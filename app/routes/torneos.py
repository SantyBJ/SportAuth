from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection

torneos_bp = Blueprint('torneos', __name__)

# --- Página de formulario para crear torneos ---
@torneos_bp.route('/torneos')
def form_torneo():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT dprt_dprt, dprt_descri FROM t_deportes ORDER BY dprt_dprt;")
    deportes = cursor.fetchall()

    cursor.execute("""
        SELECT prfm_prfm, prfm_descri
        FROM t_profesionalismo
        WHERE prfm_dprt = 1
        ORDER BY prfm_descri;
    """)
    profesionalismos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('form_torneo.html', deportes=deportes, profesionalismos=profesionalismos)

# --- Insertar torneo ---
@torneos_bp.route('/insertar_torneo', methods=['POST'])
def insertar_torneo():
    nombre = request.form['nombre']
    min_eq = request.form['min_equipos']
    max_eq = request.form['max_equipos']
    min_jug = request.form['min_jugadores']
    max_jug = request.form['max_jugadores']
    genero = request.form['genero']
    fecini = request.form['fecini']
    fecfin = request.form['fecfin']
    deporte = request.form['deporte']
    profesionalismos = request.form.getlist('profesionalismos')

    if not profesionalismos:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT dprt_dprt, dprt_descri FROM t_deportes ORDER BY dprt_dprt;")
        deportes = cursor.fetchall()
        cursor.execute("""
            SELECT prfm_prfm, prfm_descri
            FROM t_profesionalismo
            WHERE prfm_dprt = 1
            ORDER BY prfm_descri;
        """)
        profesionalismos_data = cursor.fetchall()
        cursor.close()
        conn.close()

        flash("Debe asociar al menos un profesionalismo al torneo.", "error")
        return render_template(
            'form_torneo.html',
            nombre=nombre,
            min_equipos=min_eq,
            max_equipos=max_eq,
            min_jugadores=min_jug,
            max_jugadores=max_jug,
            genero=genero,
            fecini=fecini,
            fecfin=fecfin,
            deportes=deportes,
            profesionalismos=profesionalismos_data
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO t_torneo (
            trno_nombre, trno_min_equipos, trno_max_equipos,
            trno_min_jugadores, trno_max_jugadores, trno_genero,
            trno_fecini, trno_fecfin, trno_dprt
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING trno_trno;
    """, (nombre, min_eq, max_eq, min_jug, max_jug, genero, fecini, fecfin, deporte))

    id_torneo = cursor.fetchone()[0]

    for prfm in profesionalismos:
        cursor.execute("""
            INSERT INTO t_profesionalismo_torneo (prtn_profesionalismo, prtn_torneo)
            VALUES (%s, %s);
        """, (prfm, id_torneo))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('torneos.listar_torneos'))

# --- Listar torneos ---
@torneos_bp.route('/listar_torneos')
def listar_torneos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.trno_trno, t.trno_nombre, d.dprt_descri,
               STRING_AGG(p.prfm_descri, ', ') AS profesionalismos,
               TO_CHAR(t.trno_fecini, 'YYYY-MM-DD') AS fecha_ini,
               TO_CHAR(t.trno_fecfin, 'YYYY-MM-DD') AS fecha_fin,
               CASE WHEN t.trno_estado THEN 'Activo' ELSE 'Inactivo' END AS estado
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

# --- Editar torneo ---
@torneos_bp.route('/editar_torneo/<int:id>')
def editar_torneo(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT trno_trno, trno_nombre, trno_min_equipos, trno_max_equipos,
               trno_min_jugadores, trno_max_jugadores, trno_genero,
               trno_fecini, trno_fecfin, trno_dprt, trno_estado
        FROM t_torneo
        WHERE trno_trno = %s;
    """, (id,))
    torneo = list(cursor.fetchone())

    cursor.execute("""
        SELECT prfm_prfm, prfm_descri
        FROM t_profesionalismo
        WHERE prfm_dprt = %s
        ORDER BY prfm_descri;
    """, (torneo[9],))
    profesionalismos = cursor.fetchall()

    cursor.execute("""
        SELECT prtn_profesionalismo
        FROM t_profesionalismo_torneo
        WHERE prtn_torneo = %s;
    """, (id,))
    seleccionados = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT dprt_dprt, dprt_descri FROM t_deportes ORDER BY dprt_dprt;")
    deportes = cursor.fetchall()

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

# --- Actualizar torneo ---
@torneos_bp.route('/actualizar_torneo', methods=['POST'])
def actualizar_torneo():
    id_torneo = request.form['id']
    nombre = request.form['nombre']
    min_eq = request.form['min_equipos']
    max_eq = request.form['max_equipos']
    min_jug = request.form['min_jugadores']
    max_jug = request.form['max_jugadores']
    genero = request.form['genero']
    fecini = request.form['fecini']
    fecfin = request.form['fecfin']
    deporte = request.form['deporte']
    estado = request.form['estado'] == 'True'
    profesionalismos = request.form.getlist('profesionalismos')

    if not profesionalismos:
        flash("Debe asociar al menos un profesionalismo al torneo.", "error")
        return redirect(url_for("torneos.editar_torneo", id=id_torneo))

    conn = get_connection()
    cursor = conn.cursor()

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
                trno_usua_alt = USER,
                trno_fecalt = CURRENT_TIMESTAMP
            WHERE trno_trno = %s;
        """, (nombre, min_eq, max_eq, min_jug, max_jug, genero,
              fecini, fecfin, deporte, estado, id_torneo))

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

# --- Eliminar torneo ---
@torneos_bp.route('/eliminar_torneo/<int:id>')
def eliminar_torneo(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM t_profesionalismo_torneo WHERE prtn_torneo = %s;", (id,))
    cursor.execute("DELETE FROM t_torneo WHERE trno_trno = %s;", (id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('torneos.listar_torneos'))