from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection
from datetime import datetime

torneos_bp = Blueprint('torneos', __name__)

def obtener_deportes_y_profesionalismos(deporte_id=1):
    """Obtiene lista de deportes y profesionalismos del deporte especificado."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT dprt_dprt, dprt_descri FROM t_deportes ORDER BY dprt_dprt;")
    deportes = cursor.fetchall()

    cursor.execute("""
        SELECT prfm_prfm, prfm_descri
        FROM t_profesionalismo
        WHERE prfm_dprt = %s
        ORDER BY prfm_descri;
    """, (deporte_id,))
    profesionalismos = cursor.fetchall()

    cursor.close()
    conn.close()

    return deportes, profesionalismos

def validar_datos_torneo(min_eq, max_eq, min_jug, max_jug, genero, fecini, fecfin, profesionalismos, estado=None, equipos_actuales=None, jugadores_cancha=None):
    """
    Verifica las reglas de negocio según los constraints de la tabla t_Torneo.
    Devuelve una lista de mensajes de error (vacía si todo está correcto).
    """
    errores = []

    # --- Validaciones numéricas ---
    if min_jug <= 0:
        errores.append("El número mínimo de jugadores debe ser mayor que 0.")
    if max_jug < min_jug:
        errores.append("El número máximo de jugadores no puede ser menor que el mínimo.")
    if min_eq <= 0:
        errores.append("El número mínimo de equipos debe ser mayor que 0.")
    if max_eq <= min_eq:
        errores.append("El número máximo de equipos no puede ser menor o igual que el mínimo.")

    # --- Validación del género ---
    if genero not in ('M', 'F', None):
        errores.append("El género debe ser Masculino ('M'), Femenino ('F') o dejarse vacío para Mixto.")

    # --- Validación de fechas ---
    try:
        fecini_dt = datetime.strptime(fecini, '%Y-%m-%d')
        fecfin_dt = datetime.strptime(fecfin, '%Y-%m-%d')
        if fecini_dt >= fecfin_dt:
            errores.append("La fecha de inicio debe ser anterior a la fecha de finalización.")
    except ValueError:
        errores.append("Formato de fecha inválido. Use AAAA-MM-DD.")

    # --- Validación de estado (solo en actualización) ---
    if estado is not None and estado not in ('P', 'E', 'F'):
        errores.append("El estado debe ser 'P' (Programado), 'E' (En ejecución) o 'F' (Finalizado).")

    # --- Profesionalismos asociados ---
    if not profesionalismos:
        errores.append("Debe asociar al menos un profesionalismo al torneo.")
        
    if jugadores_cancha is None:
        errores.append("Debe especificar la cantidad de jugadores en cancha.")
    else:
        try:
            jugadores_cancha = int(jugadores_cancha)
            if jugadores_cancha <= 0:
                errores.append("El número de jugadores en cancha debe ser mayor que 0.")
            if jugadores_cancha > min_jug:
                errores.append("Los jugadores en cancha no pueden exceder el minimo de jugadores por equipo.")
        except:
            errores.append("Valor inválido para jugadores en cancha.")
    
    if equipos_actuales is not None:
        try:
            equipos_actuales = int(equipos_actuales)
            if equipos_actuales > max_eq:
                errores.append(
                    f"Ya hay {equipos_actuales} equipos asociados al torneo, "
                    f"no se puede reducir el número máximo de equipos."
                )
        except (ValueError, TypeError):
            errores.append("Error al verificar los equipos asociados al torneo.")   
             
    if estado == 'E' and equipos_actuales is not None:
        if equipos_actuales < min_eq:
            errores.append("No se cumple con el mínimo de equipos registrados.")
    return errores

def validar_eliminacion_torneo(cursor, id_torneo):
    """Valida si un torneo puede eliminarse, devolviendo una lista de errores."""
    errores = []

    cursor.execute("SELECT COUNT(*) FROM t_equipo_torneo WHERE eqtn_torneo = %s;", (id_torneo,))
    equipos_asociados = cursor.fetchone()[0]
    if equipos_asociados > 0:
        errores.append("Existen equipos asociados a este torneo, si requiere eliminarlo, debe desvincular los equipos.")

    return errores

@torneos_bp.route('/torneos')
def form_torneo():
    deportes, profesionalismos = obtener_deportes_y_profesionalismos()
    return render_template('form_torneo.html', deportes=deportes, profesionalismos=profesionalismos)

@torneos_bp.route('/insertar_torneo', methods=['POST'])
def insertar_torneo():
    nombre = request.form['nombre']
    min_eq = int(request.form['min_equipos'])
    max_eq = int(request.form['max_equipos'])
    min_jug = int(request.form['min_jugadores'])
    max_jug = int(request.form['max_jugadores'])
    genero = request.form['genero'] if request.form['genero'] != "NULL" else None
    fecini = request.form['fecini']
    fecfin = request.form['fecfin']
    deporte = request.form['deporte']
    jugadores_cancha = int(request.form['jugadores_cancha'])
    profesionalismos = request.form.getlist('profesionalismos')
    
    try:
        profesionalismos_selected = [int(p) for p in profesionalismos]
    except ValueError:
        profesionalismos_selected = []  # en caso de valores inesperados

    errores = validar_datos_torneo(min_eq, max_eq, min_jug, max_jug, genero, fecini, fecfin, profesionalismos, jugadores_cancha=jugadores_cancha)

    if errores:
        deportes, profesionalismos_data = obtener_deportes_y_profesionalismos()
        for err in errores:
            flash(err, "error")
        return render_template(
            'form_torneo.html',
            nombre=nombre,
            min_equipos=min_eq,
            max_equipos=max_eq,
            min_jugadores=min_jug,
            max_jugadores=max_jug,
            jugadores_cancha=jugadores_cancha,
            genero=genero,
            fecini=fecini,
            fecfin=fecfin,
            deporte=deporte,
            profesionalismos_seleccionados=profesionalismos_selected,
            deportes=deportes,
            profesionalismos=profesionalismos_data
        )


    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO t_torneo (
                trno_nombre, trno_min_equipos, trno_max_equipos,
                trno_min_jugadores, trno_max_jugadores, trno_genero,
                trno_fecini, trno_fecfin, trno_dprt, trno_estado,
                trno_jugadores_cancha
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING trno_trno;
        """, (nombre, min_eq, max_eq, min_jug, max_jug, genero,
              fecini, fecfin, deporte, 'P', jugadores_cancha))

        id_torneo = cursor.fetchone()[0]

        for prfm in profesionalismos:
            cursor.execute("""
                INSERT INTO t_profesionalismo_torneo (prtn_profesionalismo, prtn_torneo)
                VALUES (%s, %s);
            """, (prfm, id_torneo))

        conn.commit()
        flash("Torneo registrado exitosamente.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al insertar torneo: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('torneos.listar_torneos'))

@torneos_bp.route('/listar_torneos')
def listar_torneos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.trno_trno, t.trno_nombre, d.dprt_descri,
               CASE
                  WHEN t.trno_genero = 'M' THEN 'Masculino'
                  WHEN t.trno_genero = 'F' THEN 'Femenino'
                  WHEN t.trno_genero IS NULL THEN 'Mixto'
                  ELSE 'Indefinido'
               END AS genero,
               STRING_AGG(p.prfm_descri, ', ') AS profesionalismos,
               TO_CHAR(t.trno_fecini, 'YYYY-MM-DD') AS fecha_ini,
               TO_CHAR(t.trno_fecfin, 'YYYY-MM-DD') AS fecha_fin,
               CASE t.trno_estado 
                  WHEN 'P' THEN 'Programado'
                  WHEN 'E' THEN 'En ejecución'
                  WHEN 'F' THEN 'Finalizado'
                  ELSE 'Indefinido'
               END AS estado
        FROM t_torneo t
        JOIN t_deportes d ON d.dprt_dprt = t.trno_dprt
        LEFT JOIN t_profesionalismo_torneo pt ON pt.prtn_torneo = t.trno_trno
        LEFT JOIN t_profesionalismo p ON p.prfm_prfm = pt.prtn_profesionalismo
        GROUP BY t.trno_trno, t.trno_nombre, d.dprt_descri, t.trno_fecini, t.trno_fecfin, t.trno_estado
        ORDER BY t.trno_trno;
    """)
    torneos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('lista_torneos.html', torneos=torneos)

@torneos_bp.route('/editar_torneo/<int:id>')
def editar_torneo(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT trno_trno, trno_nombre, trno_min_equipos, trno_max_equipos,
               trno_min_jugadores, trno_max_jugadores, trno_genero,
               trno_fecini, trno_fecfin, trno_dprt, trno_estado, trno_jugadores_cancha
        FROM t_torneo
        WHERE trno_trno = %s;
    """, (id,))
    torneo = list(cursor.fetchone())

    # Obtener profesionalismos y deportes del deporte actual
    deportes, profesionalismos = obtener_deportes_y_profesionalismos(torneo[9])

    cursor.execute("""
        SELECT prtn_profesionalismo
        FROM t_profesionalismo_torneo
        WHERE prtn_torneo = %s;
    """, (id,))
    seleccionados = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    if torneo[7]:
        torneo[7] = torneo[7].strftime('%Y-%m-%d')
    if torneo[8]:
        torneo[8] = torneo[8].strftime('%Y-%m-%d')

    return render_template('editar_torneo.html',
                           torneo=torneo,
                           deportes=deportes,
                           profesionalismos=profesionalismos,
                           seleccionados=seleccionados)

@torneos_bp.route('/actualizar_torneo', methods=['POST'])
def actualizar_torneo():
    id_torneo = request.form['id']
    nombre = request.form['nombre']
    min_eq = int(request.form['min_equipos'])
    max_eq = int(request.form['max_equipos'])
    min_jug = int(request.form['min_jugadores'])
    max_jug = int(request.form['max_jugadores'])
    genero = request.form['genero'] if request.form['genero'] != "NULL" else None
    fecini = request.form['fecini']
    fecfin = request.form['fecfin']
    deporte = request.form['deporte']
    estado = request.form['estado']
    jugadores_cancha = int(request.form['jugadores_cancha'])
    profesionalismos = request.form.getlist('profesionalismos')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM t_equipo_torneo WHERE eqtn_torneo = %s", (id_torneo,))
    equipos_actuales = cursor.fetchone()[0]
    errores = validar_datos_torneo(min_eq, max_eq, min_jug, max_jug, genero, fecini, fecfin, profesionalismos, estado, equipos_actuales, jugadores_cancha)

    if errores:
        cursor.close()
        conn.close()
        for err in errores:
            flash(err, "error")
        return redirect(url_for("torneos.editar_torneo", id=id_torneo))

    cursor.execute("""
        SELECT 
            eq.eqpo_nombre AS equipo_nombre,
            COUNT(*) AS cantidad_jugadores
        FROM t_Registros r
        JOIN t_Jugador_Torneo jt 
            ON jt.jgtr_jugador = r.rgtr_jugador 
            AND jt.jgtr_torneo = r.rgtr_torneo
        JOIN t_Equipos eq
            ON eq.eqpo_eqpo = jt.jgtr_equipo
        WHERE r.rgtr_torneo = %s
        GROUP BY r.rgtr_partido, eq.eqpo_eqpo, eq.eqpo_nombre;
    """, (id_torneo,))
    
    jugadores_por_equipo = cursor.fetchall()  
    cursor.execute("""
        SELECT trno_min_jugadores, trno_max_jugadores
        FROM t_torneo
        WHERE trno_trno = %s;
    """, (id_torneo,))
    min_jug_actual, max_jug_actual = cursor.fetchone()
    
    if min_jug > min_jug_actual:
        for equipo_nombre, cant in jugadores_por_equipo:
            if cant < min_jug:
                flash(
                    f"No puede aumentar el mínimo de jugadores. "
                    f"El equipo '{equipo_nombre}' tiene solo {cant} jugadores registrados.",
                    "error"
                )
                cursor.close()
                conn.close()
                return redirect(url_for("torneos.editar_torneo", id=id_torneo))
            
    if max_jug < max_jug_actual:
        for equipo_nombre, cant in jugadores_por_equipo:
            if cant > max_jug:
                flash(
                    f"No puede reducir el máximo de jugadores. "
                    f"El equipo '{equipo_nombre}' tiene {cant} jugadores registrados.",
                    "error"
                )
                cursor.close()
                conn.close()
                return redirect(url_for("torneos.editar_torneo", id=id_torneo))
    
    try:
        cursor.execute("""
            UPDATE t_torneo
            SET trno_nombre = %s,
                trno_min_equipos = %s,
                trno_max_equipos = %s,
                trno_min_jugadores = %s,
                trno_max_jugadores = %s,
                trno_genero = %s,
                trno_fecini = %s,
                trno_fecfin = %s,
                trno_dprt = %s,
                trno_estado = %s,
                trno_jugadores_cancha = %s,
                trno_usua_alt = USER,
                trno_fecalt = CURRENT_TIMESTAMP
            WHERE trno_trno = %s;
        """, (nombre, min_eq, max_eq, min_jug, max_jug, genero,
              fecini, fecfin, deporte, estado, jugadores_cancha, id_torneo))

        cursor.execute("DELETE FROM t_profesionalismo_torneo WHERE prtn_torneo = %s;", (id_torneo,))
        for prfm in profesionalismos:
            cursor.execute("""
                INSERT INTO t_profesionalismo_torneo (prtn_profesionalismo, prtn_torneo)
                VALUES (%s, %s);
            """, (prfm, id_torneo))

        conn.commit()

    except Exception as e:
        conn.rollback()
        flash(f"Error al actualizar torneo: {str(e)}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('torneos.listar_torneos'))

@torneos_bp.route('/eliminar_torneo/<int:id>')
def eliminar_torneo(id):
    conn = get_connection()
    cursor = conn.cursor()

    # Validaciones
    errores = validar_eliminacion_torneo(cursor, id)

    if errores:
        for error in errores:
            flash(error, 'error')
        cursor.close()
        conn.close()
        return redirect(url_for('torneos.listar_torneos'))

    # Si pasa las validaciones, eliminar
    cursor.execute("DELETE FROM t_profesionalismo_torneo WHERE prtn_torneo = %s;", (id,))
    cursor.execute("DELETE FROM t_torneo WHERE trno_trno = %s;", (id,))
    conn.commit()

    cursor.close()
    conn.close()

    flash("Torneo eliminado exitosamente.", "success")
    return redirect(url_for('torneos.listar_torneos'))