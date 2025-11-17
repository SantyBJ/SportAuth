from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection

jugador_torneo_bp = Blueprint('jugador_torneo', __name__)

def validar_asociacion_jugador_torneo(cursor, id_torneo, cedula, equipo, nro_camiseta, modo="insertar"):
    errores = []

    # --- Validar torneo ---
    cursor.execute("""
        SELECT trno_estado, trno_dprt, trno_genero, trno_max_jugadores, trno_max_equipos
        FROM t_torneo 
        WHERE trno_trno = %s;
    """, (id_torneo,))
    torneo_info = cursor.fetchone()
    if not torneo_info:
        errores.append("El torneo especificado no existe.")
        return errores

    trno_estado, deporte_torneo, genero_torneo, max_jugadores, max_equipos = torneo_info

    if trno_estado == 'F':
        errores.append("No se pueden asociar o modificar jugadores porque el torneo ya se encuentra finalizado.")

    # --- Validación límite máximo ---
    limite_total = max_jugadores * max_equipos

    cursor.execute("""
        SELECT COUNT(*) FROM t_jugador_torneo WHERE jgtr_torneo = %s;
    """, (id_torneo,))
    jugadores_actuales = cursor.fetchone()[0]

    if modo == "insertar" and jugadores_actuales >= limite_total:
        errores.append(
            f"Se alcanzó el límite máximo de jugadores para este torneo ({limite_total})."
        )

    cursor.execute("""
        SELECT COUNT(*) 
        FROM t_jugador_torneo 
        WHERE jgtr_torneo = %s AND jgtr_equipo = %s;
    """, (id_torneo, equipo))
    jugadores_en_equipo = cursor.fetchone()[0]

    # En actualización, excluirse a sí mismo
    if modo == "actualizar":
        cursor.execute("""
            SELECT COUNT(*) 
            FROM t_jugador_torneo
            WHERE jgtr_torneo = %s AND jgtr_equipo = %s AND jgtr_jugador <> %s;
        """, (id_torneo, equipo, cedula))
        jugadores_en_equipo = cursor.fetchone()[0]

    if jugadores_en_equipo >= max_jugadores and modo == "insertar":
        errores.append(
            f"El equipo seleccionado ya alcanzó el máximo permitido de jugadores ({max_jugadores})."
        )

    if modo == "actualizar":
        cursor.execute("""
            SELECT jgtr_equipo 
            FROM t_jugador_torneo
            WHERE jgtr_torneo = %s AND jgtr_jugador = %s;
        """, (id_torneo, cedula))
        equipo_actual = cursor.fetchone()[0]

        # Solo validar límite por equipo si está cambiando de equipo o aumentando el cupo
        if equipo_actual != equipo and jugadores_en_equipo >= max_jugadores:
            errores.append(
                f"El equipo seleccionado ya alcanzó el máximo permitido de jugadores ({max_jugadores})."
            )
    # --- Validar jugador ---
    cursor.execute("""
        SELECT jgdr_estado, jgdr_genero, jgdr_prfm,
               (SELECT prfm_dprt FROM t_profesionalismo WHERE prfm_prfm = jgdr_prfm)
        FROM t_jugadores 
        WHERE jgdr_jgdr = %s;
    """, (cedula,))
    jugador_data = cursor.fetchone()

    if not jugador_data:
        errores.append(f"No existe un jugador registrado con la cédula {cedula}.")
        return errores

    estado_jugador, genero_jugador, profesionalismo_jugador, deporte_jugador = jugador_data

    if not estado_jugador:
        errores.append("El jugador no se encuentra activo.")
    if deporte_torneo != deporte_jugador:
        errores.append("El deporte del jugador no coincide con el deporte del torneo.")

    # --- Validar profesionalismo permitido ---
    cursor.execute("""
        SELECT COUNT(*) 
        FROM t_profesionalismo_torneo
        WHERE prtn_torneo = %s AND prtn_profesionalismo = %s;
    """, (id_torneo, profesionalismo_jugador))
    permitido = cursor.fetchone()[0]
    if permitido == 0:
        errores.append("El profesionalismo del jugador no está permitido en este torneo.")

    # --- Validar género ---
    if genero_torneo is not None and genero_torneo != genero_jugador:
        errores.append("El género del jugador no coincide con el permitido por el torneo.")

    # --- Validar equipo activo ---
    cursor.execute("SELECT eqpo_estado FROM t_equipos WHERE eqpo_eqpo = %s;", (equipo,))
    eq_estado = cursor.fetchone()
    if not eq_estado or not eq_estado[0]:
        errores.append("El equipo seleccionado no se encuentra activo.")

    # --- Validar relación equipo-torneo ---
    cursor.execute("""
        SELECT eqtn_estado 
        FROM t_equipo_torneo 
        WHERE eqtn_equipo = %s AND eqtn_torneo = %s;
    """, (equipo, id_torneo))
    eq_torneo_estado = cursor.fetchone()
    if not eq_torneo_estado or not eq_torneo_estado[0]:
        errores.append("El equipo no tiene una asociación activa con este torneo.")

    # --- Validar duplicados ---
    if modo == "insertar":
        cursor.execute("""
            SELECT COUNT(*) 
            FROM t_jugador_torneo 
            WHERE jgtr_jugador = %s AND jgtr_torneo = %s;
        """, (cedula, id_torneo))
        if cursor.fetchone()[0] > 0:
            errores.append("El jugador ya está asociado a este torneo.")

    # --- Validar número de camiseta duplicado ---
    cursor.execute("""
        SELECT COUNT(*) 
        FROM t_jugador_torneo 
        WHERE jgtr_torneo = %s AND jgtr_equipo = %s AND jgtr_nro_camiseta = %s
        """ + ("" if modo == "insertar" else " AND jgtr_jugador <> %s"),
        (id_torneo, equipo, nro_camiseta) if modo == "insertar" else (id_torneo, equipo, nro_camiseta, cedula)
    )
    if cursor.fetchone()[0] > 0:
        errores.append("Ya existe un jugador con ese número de camiseta en este equipo.")

    return errores

@jugador_torneo_bp.route('/jugadores_torneo/<int:id_torneo>')
def jugadores_por_torneo(id_torneo):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.trno_nombre,
               jt.jgtr_jugador,
               j.jgdr_nombres || ' ' || j.jgdr_apelidos AS nombre_jugador,
               e.eqpo_nombre AS equipo,
               jt.jgtr_nro_camiseta,
               CASE WHEN jt.jgtr_estado THEN 'Activo' ELSE 'Inactivo' END AS estado
        FROM t_jugador_torneo jt
        JOIN t_jugadores j ON j.jgdr_jgdr = jt.jgtr_jugador
        JOIN t_equipos e ON e.eqpo_eqpo = jt.jgtr_equipo
        JOIN t_torneo t ON t.trno_trno = jt.jgtr_torneo
        WHERE jt.jgtr_torneo = %s
        ORDER BY e.eqpo_nombre, j.jgdr_apelidos;
    """, (id_torneo,))
    jugadores = cursor.fetchall()

    # Traer info del torneo y equipos disponibles
    cursor.execute("SELECT trno_trno, trno_nombre FROM t_torneo WHERE trno_trno = %s;", (id_torneo,))
    torneo = cursor.fetchone()
    cursor.execute("""
        SELECT eqpo_eqpo, eqpo_nombre 
        FROM t_Equipo_Torneo 
        JOIN t_Equipos ON eqpo_eqpo = eqtn_equipo
        WHERE eqtn_torneo = %s
        ORDER BY eqpo_nombre;
    """, (id_torneo,))
    equipos = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('gestion_jugadores_torneo.html', torneo=torneo, jugadores=jugadores, equipos=equipos)

@jugador_torneo_bp.route('/insertar_jugador_torneo/<int:id_torneo>', methods=['POST'])
def insertar_jugador_torneo(id_torneo):
    cedula = request.form['cedula']
    equipo = request.form['equipo']
    nro_camiseta = request.form['nro_camiseta']

    conn = get_connection()
    cursor = conn.cursor()

    try:
        errores = validar_asociacion_jugador_torneo(cursor, id_torneo, cedula, equipo, nro_camiseta, modo="insertar")
        if errores:
            for err in errores:
                flash(err, "error")
            return redirect(url_for('jugador_torneo.jugadores_por_torneo', id_torneo=id_torneo))

        cursor.execute("""
            INSERT INTO t_jugador_torneo (jgtr_jugador, jgtr_torneo, jgtr_equipo, jgtr_nro_camiseta)
            VALUES (%s, %s, %s, %s);
        """, (cedula, id_torneo, equipo, nro_camiseta))
        conn.commit()
        flash("Jugador asociado exitosamente al torneo.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al asociar jugador: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('jugador_torneo.jugadores_por_torneo', id_torneo=id_torneo))

@jugador_torneo_bp.route('/actualizar_jugador_torneo/<int:id_torneo>', methods=['POST'])
def actualizar_jugador_torneo(id_torneo):
    jugador = request.form['jugador']
    equipo = request.form['equipo']
    nro_camiseta = request.form['nro_camiseta']
    estado = True if request.form.get('estado') == '1' else False

    conn = get_connection()
    cursor = conn.cursor()
    try:
        errores = validar_asociacion_jugador_torneo(cursor, id_torneo, jugador, equipo, nro_camiseta, modo="actualizar")
        if errores:
            for err in errores:
                flash(err, "error")
            return redirect(url_for('jugador_torneo.jugadores_por_torneo', id_torneo=id_torneo))

        cursor.execute("""
            UPDATE t_jugador_torneo
            SET jgtr_equipo = %s,
                jgtr_nro_camiseta = %s,
                jgtr_estado = %s,
                jgtr_usua_alt = USER,
                jgtr_fecalt = CURRENT_TIMESTAMP
            WHERE jgtr_jugador = %s AND jgtr_torneo = %s;
        """, (equipo, nro_camiseta, estado, jugador, id_torneo))
        conn.commit()
        flash("Datos del jugador actualizados correctamente.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al actualizar jugador: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('jugador_torneo.jugadores_por_torneo', id_torneo=id_torneo))

@jugador_torneo_bp.route('/eliminar_jugador_torneo/<int:jugador>/<int:id_torneo>')
def eliminar_jugador_torneo(jugador, id_torneo):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*)
            FROM t_registros
            WHERE rgtr_torneo = %s
              AND rgtr_jugador = %s;
        """, (id_torneo, jugador))
        registros = cursor.fetchone()[0]

        if registros > 0:
            flash("Este jugador tiene registros en el torneo y no puede ser eliminado.", "error")
            return redirect(url_for('jugador_torneo.jugadores_por_torneo', id_torneo=id_torneo))
        
        cursor.execute("""
            DELETE FROM t_jugador_torneo
            WHERE jgtr_jugador = %s AND jgtr_torneo = %s;
        """, (jugador, id_torneo))
        conn.commit()
        flash("Asociación eliminada correctamente.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar asociación: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('jugador_torneo.jugadores_por_torneo', id_torneo=id_torneo))
