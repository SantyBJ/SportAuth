from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection

registros_bp = Blueprint('registros', __name__, template_folder='templates')

# -------------------------
# Validaciones
# -------------------------

def validar_registro(cursor, id_torneo, id_partido, cedula, equipo, modo="insertar"):
    """
    Validaciones antes de insertar/actualizar un registro en t_Registros.
    - jugador debe existir y estar activo
    - jugador debe estar asociado al torneo (t_jugador_torneo) y pertenecer al equipo indicado
    - equipo debe ser local o visitante del partido y tener asociacion activa con torneo
    - no duplicar pk (rgtr_torneo, rgtr_partido, rgtr_jugador) en modo insertar
    - no permitir inserts/updates si partido no está en estado 'P' (programado) para cambios de registro
    """
    errores = []

    # --- Validar partido y su estado + equipos ---
    cursor.execute("""
        SELECT prtd_local, prtd_visitante, prtd_estado
        FROM t_partidos
        WHERE prtd_trno = %s AND prtd_prtd = %s;
    """, (id_torneo, id_partido))
    partido = cursor.fetchone()
    if not partido:
        errores.append("Partido no encontrado.")
        return errores

    prtd_local, prtd_visitante, prtd_estado = partido

    # Only allow insert/update of registrations if partido is Programado ('P')
    if prtd_estado != 'P':
        errores.append("No se pueden modificar registros: el partido ya inició o está finalizado.")

    # equipo debe ser local o visitante
    if equipo not in (prtd_local, prtd_visitante):
        errores.append("El jugador ingresado no se encuentra en el equipo local ni visitante del partido.")

    # validar jugador existente y activo
    cursor.execute("""
        SELECT jgdr_estado, jgdr_genero, jgdr_prfm, jgdr_nombres || ' ' || jgdr_apelidos
        FROM t_jugadores
        WHERE jgdr_jgdr = %s;
    """, (cedula,))
    jugador = cursor.fetchone()
    if not jugador:
        errores.append(f"No existe jugador con cédula {cedula}.")
        return errores
    estado_jugador, genero_jugador, prfm_jugador, nombre_jugador = jugador
    if not estado_jugador:
        errores.append("El jugador no está activo.")

    # validar que jugador esté asociado al torneo y al equipo (t_jugador_torneo)
    cursor.execute("""
        SELECT jgtr_equipo, jgtr_estado
        FROM t_jugador_torneo
        WHERE jgtr_jugador = %s AND jgtr_torneo = %s;
    """, (cedula, id_torneo))
    assoc = cursor.fetchone()
    if not assoc:
        errores.append("El jugador no está asociado a este torneo.")
    else:
        jgtr_equipo, jgtr_estado = assoc
        if jgtr_equipo != equipo:
            errores.append("El jugador no pertenece al equipo seleccionado en este torneo.")
        if not jgtr_estado:
            errores.append("La asociación del jugador con el torneo está inactiva.")

    # validar equipo activo y asociado al torneo
    cursor.execute("SELECT eqpo_estado FROM t_equipos WHERE eqpo_eqpo = %s;", (equipo,))
    eq_estado = cursor.fetchone()
    if not eq_estado or not eq_estado[0]:
        errores.append("El equipo no se encuentra activo.")
    cursor.execute("""
        SELECT eqtn_estado
        FROM t_equipo_torneo
        WHERE eqtn_equipo = %s AND eqtn_torneo = %s;
    """, (equipo, id_torneo))
    eqtn = cursor.fetchone()
    if not eqtn or not eqtn[0]:
        errores.append("El equipo no está asociado activamente al torneo.")

    # validar duplicado PK en modo insertar
    if modo == "insertar":
        cursor.execute("""
            SELECT COUNT(*) FROM t_Registros
            WHERE rgtr_torneo = %s AND rgtr_partido = %s AND rgtr_jugador = %s;
        """, (id_torneo, id_partido, cedula))
        if cursor.fetchone()[0] > 0:
            errores.append("El jugador ya está registrado para este partido.")
        
    return errores

# -------------------------
# Rutas principales
# -------------------------

@registros_bp.route('/gestion_jugadores_partido/<int:id_torneo>/<int:id_partido>')
def gestion_jugadores_partido(id_torneo, id_partido):
    conn = get_connection()
    cursor = conn.cursor()

    # Traer info del partido
    cursor.execute("""
        SELECT prtd_local, prtd_visitante, prtd_fecha, prtd_estado
        FROM t_partidos
        WHERE prtd_trno = %s AND prtd_prtd = %s;
    """, (id_torneo, id_partido))
    partido = cursor.fetchone()
    if not partido:
        cursor.close()
        conn.close()
        flash("Partido no encontrado.", "error")
        return redirect(url_for('partidos.listar_partidos', id_torneo=id_torneo))

    prtd_local, prtd_visitante, prtd_fecha, prtd_estado = partido

    # Traer nombres de equipos
    cursor.execute("SELECT eqpo_nombre FROM t_equipos WHERE eqpo_eqpo = %s;", (prtd_local,))
    local_nombre = cursor.fetchone()[0]
    cursor.execute("SELECT eqpo_nombre FROM t_equipos WHERE eqpo_eqpo = %s;", (prtd_visitante,))
    visitante_nombre = cursor.fetchone()[0]

    # Traer jugadores disponibles por equipo (asociados al torneo y activos)
    cursor.execute("""
        SELECT jt.jgtr_jugador, j.jgdr_nombres || ' ' || j.jgdr_apelidos AS nombre, jt.jgtr_nro_camiseta
        FROM t_jugador_torneo jt
        JOIN t_jugadores j ON j.jgdr_jgdr = jt.jgtr_jugador
        WHERE jt.jgtr_torneo = %s AND jt.jgtr_equipo = %s AND jt.jgtr_estado = TRUE
        ORDER BY j.jgdr_apelidos;
    """, (id_torneo, prtd_local))
    jugadores_local = cursor.fetchall()

    cursor.execute("""
        SELECT jt.jgtr_jugador, j.jgdr_nombres || ' ' || j.jgdr_apelidos AS nombre, jt.jgtr_nro_camiseta
        FROM t_jugador_torneo jt
        JOIN t_jugadores j ON j.jgdr_jgdr = jt.jgtr_jugador
        WHERE jt.jgtr_torneo = %s AND jt.jgtr_equipo = %s AND jt.jgtr_estado = TRUE
        ORDER BY j.jgdr_apelidos;
    """, (id_torneo, prtd_visitante))
    jugadores_visitante = cursor.fetchall()

    # Traer registros ya guardados para el partido -> con info de equipo (desde t_jugador_torneo)
    cursor.execute("""
        SELECT r.rgtr_jugador,
               j.jgdr_nombres || ' ' || j.jgdr_apelidos AS nombre,
               jt.jgtr_equipo,
               jt.jgtr_nro_camiseta AS nro_camiseta_torneo,
               CASE r.rgtr_estado
                 WHEN 'J' THEN 'Jugando'
                 WHEN 'B' THEN 'Banca'
                 WHEN 'L' THEN 'Lesionado'
                 WHEN 'E' THEN 'Expulsado'
                 ELSE 'Indefinido'
               END estado,
               COALESCE(r.rgtr_goles,0) AS goles,
               COALESCE(r.rgtr_asistencias,0) AS asistencias,
               COALESCE(array_to_string(r.rgtr_faltas, ''), '') AS faltas,
               r.rgtr_fecreg
        FROM t_Registros r
        JOIN t_jugadores j ON j.jgdr_jgdr = r.rgtr_jugador
        JOIN t_jugador_torneo jt ON jt.jgtr_jugador = r.rgtr_jugador AND jt.jgtr_torneo = r.rgtr_torneo
        WHERE r.rgtr_torneo = %s AND r.rgtr_partido = %s
        ORDER BY jt.jgtr_equipo, j.jgdr_apelidos;
    """, (id_torneo, id_partido))
    raw_registros = cursor.fetchall()

    registros = []
    for r in raw_registros:
        faltas_str = r[7] or ""
        leves = faltas_str.count('L')
        medias = faltas_str.count('M')
        graves = faltas_str.count('G')

        registros.append({
            'jugador': r[0],
            'nombre': r[1],
            'equipo': r[2],
            'camiseta': r[3],
            'estado': r[4],
            'goles': r[5],
            'asistencias': r[6],
            'faltas_leves': leves,
            'faltas_medias': medias,
            'faltas_graves': graves,
            'fecreg': r[8]
        })

    # Calcular goles actuales por equipo (útil al mostrar)
    cursor.execute("""
        SELECT jt.jgtr_equipo, SUM(COALESCE(r.rgtr_goles,0)) AS goles
        FROM t_Registros r
        JOIN t_jugador_torneo jt ON jt.jgtr_jugador = r.rgtr_jugador AND jt.jgtr_torneo = r.rgtr_torneo
        WHERE r.rgtr_torneo = %s AND r.rgtr_partido = %s
        GROUP BY jt.jgtr_equipo;
    """, (id_torneo, id_partido))
    goles_por_equipo = {row[0]: int(row[1]) for row in cursor.fetchall()}

    # Resultado por equipos
    goles_local = goles_por_equipo.get(prtd_local, 0)
    goles_visitante = goles_por_equipo.get(prtd_visitante, 0)

    cursor.close()
    conn.close()

    return render_template('gestion_jugadores_partido.html',
                           id_torneo=id_torneo,
                           id_partido=id_partido,
                           partido=partido,
                           local={'id': prtd_local, 'nombre': local_nombre},
                           visitante={'id': prtd_visitante, 'nombre': visitante_nombre},
                           jugadores_local=jugadores_local,
                           jugadores_visitante=jugadores_visitante,
                           registros=registros,
                           prtd_estado=prtd_estado,
                           goles_local=goles_local,
                           goles_visitante=goles_visitante)

# -------------------------
# Insertar registro (agregar jugador al partido)
# -------------------------
@registros_bp.route('/insertar_registro/<int:id_torneo>/<int:id_partido>', methods=['POST'])
def insertar_registro(id_torneo, id_partido):
    cedula = request.form['cedula']

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Obtener equipo del jugador en el torneo
        cursor.execute("""
            SELECT jgtr_equipo
            FROM t_jugador_torneo
            WHERE jgtr_torneo = %s AND jgtr_jugador = %s;
        """, (id_torneo, cedula))
        row = cursor.fetchone()

        if not row:
            flash("El jugador no está asociado al torneo.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        equipo = row[0]

        errores = validar_registro(cursor, id_torneo, id_partido, cedula, equipo, modo="insertar")
        if errores:
            for e in errores:
                flash(e, "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        # Insertar jugador en el partido
        cursor.execute("""
            INSERT INTO t_Registros (
                rgtr_torneo, rgtr_partido, rgtr_jugador,
                rgtr_estado, rgtr_usua, rgtr_fecreg
            )
            VALUES (%s, %s, %s, 'J', USER, CURRENT_TIMESTAMP)
        """, (id_torneo, id_partido, cedula))

        conn.commit()
        flash("Jugador registrado correctamente.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al registrar jugador: {str(e)}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('registros.gestion_jugadores_partido',
                            id_torneo=id_torneo, id_partido=id_partido))

# -------------------------
# Actualizar registro (estado, camiseta)
# -------------------------
@registros_bp.route('/actualizar_registro/<int:id_torneo>/<int:id_partido>', methods=['POST'])
def actualizar_registro(id_torneo, id_partido):
    jugador = request.form['jugador']
    nuevo_estado = request.form.get('estado')

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Validar estado enviado
        if nuevo_estado not in ('J', 'B'):
            flash("Solo se permite cambiar entre estados J y B.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        # Obtener estado actual
        cursor.execute("""
            SELECT rgtr_estado
            FROM t_Registros
            WHERE rgtr_torneo = %s AND rgtr_partido = %s AND rgtr_jugador = %s;
        """, (id_torneo, id_partido, jugador))

        row = cursor.fetchone()
        if not row:
            flash("Registro no encontrado.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        estado_actual = row[0]

        if estado_actual not in ('J', 'B'):
            flash("No se puede cambiar el estado: solo J o B son válidos en esta etapa.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        # Evitar cambios innecesarios
        if estado_actual == nuevo_estado:
            flash("El estado ya es el seleccionado.", "info")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        # Obtener equipo para validar
        cursor.execute("""
            SELECT jgtr_equipo
            FROM t_jugador_torneo
            WHERE jgtr_jugador = %s AND jgtr_torneo = %s;
        """, (jugador, id_torneo))
        row = cursor.fetchone()

        if not row:
            flash("Jugador no asociado al torneo.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        equipo = row[0]

        # Validación general
        errores = validar_registro(cursor, id_torneo, id_partido, jugador, equipo, modo="actualizar")
        if errores:
            for e in errores:
                flash(e, "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        cursor.execute("""
            UPDATE t_Registros
            SET rgtr_estado = %s,
                rgtr_usua_alt = USER,
                rgtr_fecalt = CURRENT_TIMESTAMP
            WHERE rgtr_torneo = %s AND rgtr_partido = %s AND rgtr_jugador = %s;
        """, (nuevo_estado, id_torneo, id_partido, jugador))

        conn.commit()
        flash("Estado actualizado correctamente.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al actualizar registro: {str(e)}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('registros.gestion_jugadores_partido',
                            id_torneo=id_torneo, id_partido=id_partido))

# -------------------------
# Eliminar registro
# -------------------------
@registros_bp.route('/eliminar_registro/<int:id_torneo>/<int:id_partido>/<int:jugador>')
def eliminar_registro(id_torneo, id_partido, jugador):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # verificar estado del partido (solo permitir si 'P')
        cursor.execute("SELECT prtd_estado FROM t_partidos WHERE prtd_trno = %s AND prtd_prtd = %s;", (id_torneo, id_partido))
        estado = cursor.fetchone()
        if not estado:
            flash("Partido no encontrado.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))
        if estado[0] != 'P':
            flash("No es posible eliminar registros: el partido ya inició o finalizó.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))

        cursor.execute("""
            DELETE FROM t_Registros
            WHERE rgtr_torneo = %s AND rgtr_partido = %s AND rgtr_jugador = %s;
        """, (id_torneo, id_partido, jugador))
        conn.commit()
        flash("Registro eliminado correctamente.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar registro: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))

# -------------------------
# Iniciar partido
# -------------------------
@registros_bp.route('/iniciar_partido/<int:id_torneo>/<int:id_partido>')
def iniciar_partido(id_torneo, id_partido):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # obtener estado y fecha del partido
        cursor.execute("""
            SELECT prtd_estado, prtd_fecha
            FROM t_partidos
            WHERE prtd_trno = %s AND prtd_prtd = %s;
        """, (id_torneo, id_partido))
        
        row = cursor.fetchone()
        if not row:
            flash("Partido no encontrado.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        prtd_estado, prtd_fecha = row

        # validar estado = Programado
        if prtd_estado != 'P':
            flash("El partido no está en estado Programado.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        # Verificar que la fecha programada NO sea mayor a la actual
                # obtener fecha/hora actual del servidor y volverla naive para evitar errores
        cursor.execute("SELECT CURRENT_TIMESTAMP;")
        now = cursor.fetchone()[0].replace(tzinfo=None)

        # asegurar que también prtd_fecha sea naive
        prtd_fecha = prtd_fecha.replace(tzinfo=None) if prtd_fecha.tzinfo else prtd_fecha

        if prtd_fecha > now:
            flash("No se puede iniciar el partido: la fecha programada es mayor a la fecha y hora actuales.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))
        
        # obtener info del torneo
        cursor.execute("""
            SELECT trno_estado,
                   trno_min_jugadores,
                   trno_jugadores_cancha
            FROM t_torneo
            WHERE trno_trno = %s;
        """, (id_torneo,))
        torneo = cursor.fetchone()

        if not torneo:
            flash("No se encontró información del torneo.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        trno_estado, trno_min_jugadores, trno_jug_cancha = torneo

        # validar estado del torneo
        if trno_estado != 'E':
            flash("El torneo no está en estado En ejecución.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))
        
        cursor.execute("""
            SELECT prtd_local, prtd_visitante
            FROM t_partidos
            WHERE prtd_trno = %s AND prtd_prtd = %s;
        """, (id_torneo, id_partido))
        prtd_local, prtd_visitante = cursor.fetchone()
        
        cursor.execute("""
            SELECT jt.jgtr_equipo, COUNT(*)
            FROM t_registros r
            JOIN t_jugador_torneo jt 
              ON jt.jgtr_jugador = r.rgtr_jugador
             AND jt.jgtr_torneo = r.rgtr_torneo
           WHERE r.rgtr_torneo = %s
             AND r.rgtr_partido = %s
            GROUP BY jt.jgtr_equipo;
        """, (id_torneo, id_partido))

        conteo_registrados = {fila[0]: fila[1] for fila in cursor.fetchall()}

        local_reg = conteo_registrados.get(prtd_local, 0)
        visit_reg = conteo_registrados.get(prtd_visitante, 0)

        if local_reg < trno_min_jugadores:
            flash(
                f"El equipo LOCAL debe tener al menos {trno_min_jugadores} jugadores "
                f"registrados. Actualmente tiene {local_reg}.",
                "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        if visit_reg < trno_min_jugadores:
            flash(
                f"El equipo VISITANTE debe tener al menos {trno_min_jugadores} jugadores "
                f"registrados. Actualmente tiene {visit_reg}.",
                "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))
        # ---------------------------------------
        # VALIDACIÓN DE JUGADORES EN CANCHA
        # ---------------------------------------
        cursor.execute("""
            SELECT jt.jgtr_equipo, COUNT(*)
            FROM t_registros r
            JOIN t_jugador_torneo jt ON jt.jgtr_jugador = r.rgtr_jugador
                                     AND jt.jgtr_torneo = r.rgtr_torneo
            WHERE r.rgtr_torneo = %s
              AND r.rgtr_partido = %s
              AND r.rgtr_estado = 'J'
            GROUP BY jt.jgtr_equipo;
        """, (id_torneo, id_partido))

        jugadores_cancha = {fila[0]: fila[1] for fila in cursor.fetchall()}

        cursor.execute("""
            SELECT prtd_local, prtd_visitante
            FROM t_partidos
            WHERE prtd_trno = %s AND prtd_prtd = %s;
        """, (id_torneo, id_partido))
        prtd_local, prtd_visitante = cursor.fetchone()

        cant_local = jugadores_cancha.get(prtd_local, 0)
        cant_visitante = jugadores_cancha.get(prtd_visitante, 0)

        if cant_local != trno_jug_cancha:
            flash(
                f"El equipo local debe tener exactamente "
        f"{trno_jug_cancha} jugadores en cancha. Actual: {cant_local}.",
                "error"
            )
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        if cant_visitante != trno_jug_cancha:
            flash(
                f"El equipo visitante debe tener exactamente "
                f"{trno_jug_cancha} jugadores en cancha. Actual: {cant_visitante}.",
                "error"
            )
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))



        # iniciar partido
        cursor.execute("""
            UPDATE t_partidos
            SET prtd_estado = 'E',
                prtd_usua_alt = USER,
                prtd_fecalt = CURRENT_TIMESTAMP
            WHERE prtd_trno = %s AND prtd_prtd = %s;
        """, (id_torneo, id_partido))

        conn.commit()
        flash("Partido iniciado. Ahora puede registrar eventos.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al iniciar partido: {str(e)}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('registros.gestion_jugadores_partido',
                            id_torneo=id_torneo, id_partido=id_partido))


# -------------------------
# Finalizar partido
# -------------------------
@registros_bp.route('/finalizar_partido/<int:id_torneo>/<int:id_partido>')
def finalizar_partido(id_torneo, id_partido):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT prtd_estado, prtd_local, prtd_visitante FROM t_partidos WHERE prtd_trno = %s AND prtd_prtd = %s;", (id_torneo, id_partido))
        row = cursor.fetchone()
        if not row:
            flash("Partido no encontrado.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))

        prtd_estado, prtd_local, prtd_visitante = row
        if prtd_estado != 'E':
            flash("Solo se puede finalizar un partido que esté En ejecución.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))

        # Calcular goles finales por equipo
        cursor.execute("""
            SELECT jt.jgtr_equipo, SUM(COALESCE(r.rgtr_goles,0)) AS goles
            FROM t_Registros r
            JOIN t_jugador_torneo jt ON jt.jgtr_jugador = r.rgtr_jugador AND jt.jgtr_torneo = r.rgtr_torneo
            WHERE r.rgtr_torneo = %s AND r.rgtr_partido = %s
            GROUP BY jt.jgtr_equipo;
        """, (id_torneo, id_partido))
        rows = cursor.fetchall()
        goles = {row[0]: int(row[1]) for row in rows}
        goles_local = goles.get(prtd_local, 0)
        goles_visitante = goles.get(prtd_visitante, 0)

        # actualizar estado del partido
        cursor.execute("""
            UPDATE t_partidos
            SET prtd_estado = 'F',
                prtd_usua_alt = USER,
                prtd_fecalt = CURRENT_TIMESTAMP
            WHERE prtd_trno = %s AND prtd_prtd = %s;
        """, (id_torneo, id_partido))

        conn.commit()
        flash(f"Partido finalizado. Resultado: {goles_local} - {goles_visitante}", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al finalizar partido: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))

# -------------------------
# Eventos durante el partido (solo si estado = 'E')
# - agregar_gol, agregar_asistencia, agregar_falta, marcar_lesion, marcar_expulsion, sustituir
# -------------------------
def partido_en_ejecucion(cursor, id_torneo, id_partido):
    cursor.execute("SELECT prtd_estado FROM t_partidos WHERE prtd_trno = %s AND prtd_prtd = %s;", (id_torneo, id_partido))
    row = cursor.fetchone()
    return bool(row and row[0] == 'E')

@registros_bp.route('/evento_gol/<int:id_torneo>/<int:id_partido>', methods=['POST'])
def evento_gol(id_torneo, id_partido):
    jugador = request.form['jugador']
    registro = int(request.form['registro'])
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if not partido_en_ejecucion(cursor, id_torneo, id_partido):
            flash("No se pueden registrar goles si el partido no está en ejecución.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))

        # verificar que jugador está registrado en el partido y en estado J (jugando)
        cursor.execute("""
            SELECT rgtr_estado FROM t_Registros
            WHERE rgtr_torneo = %s AND rgtr_partido = %s AND rgtr_jugador = %s;
        """, (id_torneo, id_partido, jugador))
        row = cursor.fetchone()
        if not row:
            flash("Jugador no registrado en el partido.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))
        if row[0] != 'J':
            flash("Solo jugadores en campo pueden marcar goles.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))

        cursor.execute("""
            UPDATE t_Registros
            SET rgtr_goles = CASE WHEN COALESCE(rgtr_goles, 0) + (%s) <= 0 THEN NULL ELSE COALESCE(rgtr_goles, 0) + (%s) END,
                rgtr_usua_alt = USER,
                rgtr_fecalt = CURRENT_TIMESTAMP
            WHERE rgtr_torneo = %s AND rgtr_partido = %s AND rgtr_jugador = %s;
        """, (registro, registro, id_torneo, id_partido, jugador))
        conn.commit()
        flash("Evento registrado.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al registrar gol: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))

@registros_bp.route('/evento_asistencia/<int:id_torneo>/<int:id_partido>', methods=['POST'])
def evento_asistencia(id_torneo, id_partido):
    jugador = request.form['jugador']
    registro = int(request.form['registro'])
    print(registro)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if not partido_en_ejecucion(cursor, id_torneo, id_partido):
            flash("No se pueden registrar asistencias si el partido no está en ejecución.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))
        
        cursor.execute("""
            SELECT rgtr_estado FROM t_Registros
            WHERE rgtr_torneo = %s AND rgtr_partido = %s AND rgtr_jugador = %s;
        """, (id_torneo, id_partido, jugador))
        row = cursor.fetchone()
        if not row:
            flash("Jugador no registrado en el partido.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))
        if row[0] != 'J':
            flash("Solo jugadores en campo pueden marcar goles.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))

        cursor.execute("""
            UPDATE t_Registros
            SET rgtr_asistencias = CASE WHEN COALESCE(rgtr_asistencias, 0) + (%s) <= 0 THEN NULL ELSE COALESCE(rgtr_asistencias, 0) + (%s) END,
                rgtr_usua_alt = USER,
                rgtr_fecalt = CURRENT_TIMESTAMP
            WHERE rgtr_torneo = %s AND rgtr_partido = %s AND rgtr_jugador = %s;
        """, (registro, registro, id_torneo, id_partido, jugador))
        if cursor.rowcount == 0:
            flash("Jugador no registrado en el partido.", "error")
            conn.rollback()
            return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))
        conn.commit()
        flash("Evento registrado.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al registrar asistencia: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('registros.gestion_jugadores_partido', id_torneo=id_torneo, id_partido=id_partido))

@registros_bp.route('/evento_falta/<int:id_torneo>/<int:id_partido>', methods=['POST'])
def evento_falta(id_torneo, id_partido):
    jugador = request.form['jugador']
    tipo = request.form['tipo']  # 'L', 'M', 'G'

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Validar tipo
        if tipo not in ('L', 'M', 'G'):
            flash("Tipo de falta inválido.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        # Verificar estado del partido
        if not partido_en_ejecucion(cursor, id_torneo, id_partido):
            flash("Solo se pueden registrar faltas si el partido está en ejecución.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        # Obtener faltas previas
        cursor.execute("""
            SELECT COALESCE(array_to_string(rgtr_faltas, ''), '') AS faltas,
                   rgtr_estado
            FROM t_Registros
            WHERE rgtr_torneo = %s AND rgtr_partido = %s AND rgtr_jugador = %s;
        """, (id_torneo, id_partido, jugador))

        row = cursor.fetchone()
        if not row:
            flash("Jugador no registrado en el partido.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        faltas_prev, estado_prev = row
        nuevas_faltas = (faltas_prev or "") + tipo

        # Convertir FAIL string a ARRAY "{L,M,G}"
        array_faltas = "{" + ",".join(nuevas_faltas) + "}"

        # Contar faltas medias
        medias = nuevas_faltas.count("M")

        # Estado por defecto
        nuevo_estado = estado_prev

        # Falta grave
        if tipo == "G":
            nuevo_estado = "E"
            flash("Jugador expulsado por falta grave.", "warning")

        # Dos faltas medias
        if medias >= 2:
            nuevo_estado = "E"
            flash("Jugador expulsado por acumular 2 faltas medias.", "warning")

        # Update FINAL en un solo UPDATE
        cursor.execute("""
            UPDATE t_Registros
            SET 
                rgtr_faltas = %s::text[],
                rgtr_estado = %s,
                rgtr_usua_alt = USER,
                rgtr_fecalt = CURRENT_TIMESTAMP
            WHERE rgtr_torneo = %s AND rgtr_partido = %s AND rgtr_jugador = %s;
        """, (array_faltas, nuevo_estado, id_torneo, id_partido, jugador))

        conn.commit()

    except Exception as e:
        conn.rollback()
        flash(f"Error al registrar falta: {str(e)}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('registros.gestion_jugadores_partido',
                            id_torneo=id_torneo, id_partido=id_partido))

@registros_bp.route('/evento_lesion/<int:id_torneo>/<int:id_partido>', methods=['POST'])
def evento_lesion(id_torneo, id_partido):
    jugador = request.form['jugador']
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if not partido_en_ejecucion(cursor, id_torneo, id_partido):
            flash("Solo se pueden registrar lesiones con el partido en ejecución.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        # cambiar estado a lesionado
        cursor.execute("""
            UPDATE t_Registros
            SET rgtr_estado = 'L',
                rgtr_usua_alt = USER,
                rgtr_fecalt = CURRENT_TIMESTAMP
            WHERE rgtr_torneo = %s AND rgtr_partido = %s AND rgtr_jugador = %s;
        """, (id_torneo, id_partido, jugador))

        # inactivar en el torneo
        cursor.execute("""
            UPDATE t_jugador_torneo
            SET jgtr_estado = FALSE
            WHERE jgtr_torneo = %s AND jgtr_jugador = %s;
        """, (id_torneo, jugador))

        conn.commit()
        flash("Jugador lesionado e inactivado del torneo.", "warning")

    except Exception as e:
        conn.rollback()
        flash(f"Error al registrar lesión: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('registros.gestion_jugadores_partido',
                            id_torneo=id_torneo, id_partido=id_partido))

@registros_bp.route('/evento_sustitucion/<int:id_torneo>/<int:id_partido>', methods=['POST'])
def evento_sustitucion(id_torneo, id_partido):
    jugador_sale = request.form['jugador_sale']
    jugador_entra = request.form['jugador_entra']

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if not partido_en_ejecucion(cursor, id_torneo, id_partido):
            flash("No se pueden realizar sustituciones si el partido no está en ejecución.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        cursor.execute("""
            SELECT rgtr_estado
            FROM t_Registros
            WHERE rgtr_torneo=%s AND rgtr_partido=%s AND rgtr_jugador=%s;
        """, (id_torneo, id_partido, jugador_sale))
        row_sale = cursor.fetchone()

        cursor.execute("""
            SELECT rgtr_estado
            FROM t_Registros
            WHERE rgtr_torneo=%s AND rgtr_partido=%s AND rgtr_jugador=%s;
        """, (id_torneo, id_partido, jugador_entra))
        row_entra = cursor.fetchone()

        if not row_sale or not row_entra:
            flash("Ambos jugadores deben estar registrados en el partido.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        if row_sale[0] != 'J':
            flash("El jugador que sale debe estar en estado 'Jugando'.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        if row_entra[0] != 'B':
            flash("El jugador que entra debe estar en estado 'Banca'.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        cursor.execute("""
            SELECT jgtr_equipo 
            FROM t_jugador_torneo 
            WHERE jgtr_jugador = %s AND jgtr_torneo = %s;
        """, (jugador_sale, id_torneo))
        equipo_sale = cursor.fetchone()

        cursor.execute("""
            SELECT jgtr_equipo 
            FROM t_jugador_torneo 
            WHERE jgtr_jugador = %s AND jgtr_torneo = %s;
        """, (jugador_entra, id_torneo))
        equipo_entra = cursor.fetchone()

        if not equipo_sale or not equipo_entra or equipo_sale[0] != equipo_entra[0]:
            flash("La sustitución no es válida: ambos jugadores deben pertenecer al mismo equipo.", "error")
            return redirect(url_for('registros.gestion_jugadores_partido',
                                    id_torneo=id_torneo, id_partido=id_partido))

        cursor.execute("""
            UPDATE t_Registros
            SET rgtr_estado = 'B',
                rgtr_usua_alt = USER,
                rgtr_fecalt = CURRENT_TIMESTAMP
            WHERE rgtr_torneo=%s AND rgtr_partido=%s AND rgtr_jugador=%s;
        """, (id_torneo, id_partido, jugador_sale))

        cursor.execute("""
            UPDATE t_Registros
            SET rgtr_estado = 'J',
                rgtr_usua_alt = USER,
                rgtr_fecalt = CURRENT_TIMESTAMP
            WHERE rgtr_torneo=%s AND rgtr_partido=%s AND rgtr_jugador=%s;
        """, (id_torneo, id_partido, jugador_entra))

        conn.commit()
        flash("Sustitución realizada correctamente.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error en la sustitución: {str(e)}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('registros.gestion_jugadores_partido',
                            id_torneo=id_torneo, id_partido=id_partido))