from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection
from datetime import datetime, timedelta

partidos_bp = Blueprint('partidos', __name__)


def validar_partido(cursor, id_torneo, local, visitante, fecha, modo="insertar", id_partido=None):
    errores = []

    # --- Validar fecha > ahora y parseo ---
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%dT%H:%M")
        if fecha_dt <= datetime.now():
            errores.append("La fecha del partido debe ser superior a la fecha y hora actuales.")
    except Exception:
        errores.append("Formato de fecha inválido. Use el selector de fecha y hora.")

    # --- Validar torneo ---
    cursor.execute("""
        SELECT trno_estado
        FROM t_torneo
        WHERE trno_trno = %s;
    """, (id_torneo,))
    torneo = cursor.fetchone()

    if not torneo:
        errores.append("El torneo no existe.")
        return errores

    estado_torneo = torneo[0]
    if estado_torneo == "F":
        errores.append("No se pueden gestionar partidos porque el torneo está finalizado.")

    # --- Validar equipos distintos ---
    if str(local) == str(visitante):
        errores.append("El equipo local y visitante no pueden ser iguales.")

    # --- Ambos equipos deben pertenecer al torneo (asociación activa) ---
    cursor.execute("""
        SELECT COUNT(*) 
        FROM t_equipo_torneo 
        WHERE eqtn_torneo = %s AND eqtn_equipo = %s AND eqtn_estado;
    """, (id_torneo, local))
    if cursor.fetchone()[0] == 0:
        errores.append("El equipo local no está asociado activamente al torneo.")

    cursor.execute("""
        SELECT COUNT(*) 
        FROM t_equipo_torneo 
        WHERE eqtn_torneo = %s AND eqtn_equipo = %s AND eqtn_estado;
    """, (id_torneo, visitante))
    if cursor.fetchone()[0] == 0:
        errores.append("El equipo visitante no está asociado activamente al torneo.")

    # --- Validación: NO permitir cambiar equipos si ya tienen jugadores registrados ---
    # t_registros contiene rgtr_torneo, rgtr_partido, rgtr_jugador
    # t_jugador_torneo contiene jgtr_jugador, jgtr_torneo, jgtr_equipo
    if modo == "actualizar" and id_partido is not None:
        cursor.execute("""
            SELECT prtd_local, prtd_visitante
            FROM t_partidos
            WHERE prtd_trno = %s AND prtd_prtd = %s;
        """, (id_torneo, id_partido))
        previo = cursor.fetchone()
        if previo:
            local_anterior, visitante_anterior = previo

            # Si cambió local → verificar registros asociados (join entre registros y jugadores en torneo)
            if str(local_anterior) != str(local):
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM t_registros r
                    JOIN t_jugador_torneo jt
                      ON jt.jgtr_jugador = r.rgtr_jugador
                     AND jt.jgtr_torneo = r.rgtr_torneo
                    WHERE r.rgtr_torneo = %s
                      AND r.rgtr_partido = %s
                      AND jt.jgtr_equipo = %s;
                """, (id_torneo, id_partido, local_anterior))
                if cursor.fetchone()[0] > 0:
                    errores.append("No se puede cambiar el equipo local porque ya tiene jugadores registrados.")

            # Si cambió visitante → verificar registros asociados
            if str(visitante_anterior) != str(visitante):
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM t_registros r
                    JOIN t_jugador_torneo jt
                      ON jt.jgtr_jugador = r.rgtr_jugador
                     AND jt.jgtr_torneo = r.rgtr_torneo
                    WHERE r.rgtr_torneo = %s
                      AND r.rgtr_partido = %s
                      AND jt.jgtr_equipo = %s;
                """, (id_torneo, id_partido, visitante_anterior))
                if cursor.fetchone()[0] > 0:
                    errores.append("No se puede cambiar el equipo visitante porque ya tiene jugadores registrados.")

    # --- Validar duplicados mismos equipos en el MISMO DÍA (ignorando hora) ---
    # Usamos rango [inicio_dia, fin_dia] para aprovechar índices.
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%dT%H:%M")
        inicio_dia = fecha_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        fin_dia = inicio_dia + timedelta(days=1) - timedelta(seconds=1)
    except Exception:
        # si el parseo falló, ya se añadió error arriba; evitamos ejecutar la consulta
        inicio_dia = None
        fin_dia = None

    if modo == "insertar" and inicio_dia is not None:
        cursor.execute("""
            SELECT COUNT(*)
            FROM t_partidos
            WHERE prtd_trno = %s
              AND prtd_local = %s
              AND prtd_visitante = %s
              AND prtd_fecha BETWEEN %s AND %s;
        """, (id_torneo, local, visitante, inicio_dia, fin_dia))
        if cursor.fetchone()[0] > 0:
            errores.append("Ya existe un partido entre estos equipos en este día.")

    if modo == "actualizar" and inicio_dia is not None:
        cursor.execute("""
            SELECT COUNT(*)
            FROM t_partidos
            WHERE prtd_trno = %s
              AND prtd_local = %s
              AND prtd_visitante = %s
              AND prtd_fecha BETWEEN %s AND %s
              AND prtd_prtd <> %s;
        """, (id_torneo, local, visitante, inicio_dia, fin_dia, id_partido))
        if cursor.fetchone()[0] > 0:
            errores.append("Ya existe otro partido entre estos equipos en este día.")

    return errores

@partidos_bp.route('/partidos/<int:id_torneo>')
def listar_partidos(id_torneo):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.prtd_prtd, e1.eqpo_nombre AS local, e2.eqpo_nombre AS visitante, p.prtd_fecha,
               CASE p.prtd_estado 
                  WHEN 'P' THEN 'Programado'
                  WHEN 'E' THEN 'En ejecución'
                  WHEN 'F' THEN 'Finalizado'
                  ELSE 'Indefinido'
               END AS estado
        FROM t_partidos p
        JOIN t_equipos e1 ON e1.eqpo_eqpo = p.prtd_local
        JOIN t_equipos e2 ON e2.eqpo_eqpo = p.prtd_visitante
        WHERE p.prtd_trno = %s
        ORDER BY p.prtd_fecha;
    """, (id_torneo,))
    partidos = cursor.fetchall()

    # Nombre torneo
    cursor.execute("SELECT trno_nombre FROM t_torneo WHERE trno_trno = %s;", (id_torneo,))
    torneo = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('lista_partidos.html', partidos=partidos, torneo=torneo, id_torneo=id_torneo)

@partidos_bp.route('/nuevo_partido/<int:id_torneo>')
def form_partidos(id_torneo):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT eqpo_eqpo, eqpo_nombre
        FROM t_equipo_torneo 
        JOIN t_equipos ON eqpo_eqpo = eqtn_equipo
        WHERE eqtn_torneo = %s AND eqtn_estado
        ORDER BY eqpo_nombre;
    """, (id_torneo,))
    equipos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('form_partidos.html', equipos=equipos, id_torneo=id_torneo)

@partidos_bp.route('/insertar_partido/<int:id_torneo>', methods=['POST'])
def insertar_partido(id_torneo):
    local = request.form['local']
    visitante = request.form['visitante']
    fecha = request.form['fecha']

    conn = get_connection()
    cursor = conn.cursor()

    try:
        errores = validar_partido(cursor, id_torneo, local, visitante, fecha)
        if errores:
            for e in errores:
                flash(e, "error")
            return redirect(url_for('partidos.form_partidos', id_torneo=id_torneo))

        # Obtener número de partido siguiente
        cursor.execute("""
            SELECT COALESCE(MAX(prtd_prtd), 0) + 1
            FROM t_partidos 
            WHERE prtd_trno = %s;
        """, (id_torneo,))
        nuevo_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO t_partidos (prtd_trno, prtd_prtd, prtd_local, prtd_visitante, prtd_fecha)
            VALUES (%s, %s, %s, %s, %s);
        """, (id_torneo, nuevo_id, local, visitante, fecha))

        conn.commit()
        flash("Partido registrado exitosamente.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al registrar partido: {str(e)}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('partidos.listar_partidos', id_torneo=id_torneo))

@partidos_bp.route('/editar_partido/<int:id_torneo>/<int:id_partido>')
def editar_partido(id_torneo, id_partido):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT prtd_prtd, prtd_local, prtd_visitante, prtd_fecha, prtd_estado
        FROM t_partidos
        WHERE prtd_trno = %s AND prtd_prtd = %s;
    """, (id_torneo, id_partido))
    partido = cursor.fetchone()

    cursor.execute("""
        SELECT eqpo_eqpo, eqpo_nombre
        FROM t_equipo_torneo 
        JOIN t_equipos ON eqpo_eqpo = eqtn_equipo
        WHERE eqtn_torneo = %s AND eqtn_estado = TRUE
        ORDER BY eqpo_nombre;
    """, (id_torneo,))
    equipos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('editar_partido.html',
                           partido=partido, equipos=equipos,
                           id_torneo=id_torneo)

@partidos_bp.route('/actualizar_partido/<int:id_torneo>', methods=['POST'])
def actualizar_partido(id_torneo):

    id_partido = request.form['id_partido']
    local = request.form['local']
    visitante = request.form['visitante']
    fecha = request.form['fecha']

    conn = get_connection()
    cursor = conn.cursor()

    try:
        errores = validar_partido(cursor, id_torneo, local, visitante, fecha,
                                  modo="actualizar", id_partido=id_partido)
        if errores:
            for e in errores:
                flash(e, "error")
            return redirect(url_for('partidos.editar_partido',
                                    id_torneo=id_torneo,
                                    id_partido=id_partido))

        cursor.execute("""
            UPDATE t_partidos
            SET prtd_local = %s,
                prtd_visitante = %s,
                prtd_fecha = %s,
                prtd_estado = 'P',
                prtd_usua_alt = USER,
                prtd_fecalt = CURRENT_TIMESTAMP
            WHERE prtd_trno = %s AND prtd_prtd = %s;
        """, (local, visitante, fecha, id_torneo, id_partido))

        conn.commit()
        flash("Partido actualizado correctamente.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al actualizar partido: {str(e)}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('partidos.listar_partidos', id_torneo=id_torneo))

@partidos_bp.route('/eliminar_partido/<int:id_torneo>/<int:id_partido>')
def eliminar_partido(id_torneo, id_partido):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Validar registros asociados
        cursor.execute("""
            SELECT COUNT(*)
            FROM t_registros
            WHERE rgtr_torneo = %s AND rgtr_partido = %s;
        """, (id_torneo, id_partido))

        if cursor.fetchone()[0] > 0:
            flash("Si requiere eliminar este partido, debe eliminar el registro de jugadores asociados al partido.", "error")
            return redirect(url_for('partidos.listar_partidos', id_torneo=id_torneo))

        cursor.execute("""
            DELETE FROM t_partidos
            WHERE prtd_trno = %s AND prtd_prtd = %s;
        """, (id_torneo, id_partido))

        conn.commit()
        flash("Partido eliminado exitosamente.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar partido: {str(e)}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('partidos.listar_partidos', id_torneo=id_torneo))