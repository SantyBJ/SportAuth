from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection

profesionalismos_bp = Blueprint('profesionalismos', __name__)

@profesionalismos_bp.route('/profesionalismos')
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.close()
    conn.close()
    return render_template('form_profesionalismo.html')

@profesionalismos_bp.route('/insertar_profesionalismo', methods=['POST'])
def insertar_profesionalismo():
    descripcion = request.form['descripcion']

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO t_profesionalismo (prfm_dprt, prfm_descri)
        VALUES (1, %s);
    """, (descripcion,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('profesionalismos.listar_profesionalismos'))

@profesionalismos_bp.route('/listar_profesionalismos')
def listar_profesionalismos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT prfm_prfm, dprt_descri, prfm_descri
        FROM t_profesionalismo
        JOIN t_deportes ON dprt_dprt = prfm_dprt
        ORDER BY prfm_prfm;
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('lista_profesionalismos.html', profesionalismos=data)

@profesionalismos_bp.route('/editar_profesionalismos/<int:id>')
def editar_profesionalismos(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT prfm_prfm, prfm_descri, prfm_dprt
        FROM t_profesionalismo WHERE prfm_prfm = %s;
    """, (id,))
    profesionalismo = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('editar_profesionalismo.html', profesionalismo=profesionalismo)

@profesionalismos_bp.route('/actualizar_profesionalismo', methods=['POST'])
def actualizar_profesionalismo():
    id_prof = request.form['id']
    descripcion = request.form['descripcion']

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE t_profesionalismo
        SET prfm_descri = %s,
            prfm_usua_alt = USER,
            prfm_fecalt = CURRENT_TIMESTAMP
        WHERE prfm_prfm = %s;
    """, (descripcion, id_prof))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('profesionalismos.listar_profesionalismos'))

@profesionalismos_bp.route('/eliminar_profesionalismo/<int:id>')
def eliminar_profesionalismo(id):
    conn = get_connection()
    cursor = conn.cursor()
    # --- Verificar si hay jugadores asociados ---
    cursor.execute("""
        SELECT COUNT(*) FROM t_jugadores
        WHERE jgdr_prfm = %s;
    """, (id,))
    jugadores_count = cursor.fetchone()[0]

    # --- Verificar si hay torneos asociados ---
    cursor.execute("""
        SELECT COUNT(*) FROM t_profesionalismo_torneo
        WHERE prtn_profesionalismo = %s;
    """, (id,))
    torneos_count = cursor.fetchone()[0]

    if jugadores_count > 0 or torneos_count > 0:
        cursor.close()
        conn.close()
        if torneos_count > 0:
            flash("No se puede eliminar el profesionalismo porque tiene torneos asociados.", "error")
        else:
            flash("No se puede eliminar el profesionalismo porque tiene jugadores asociados.", "error")
        return redirect(url_for('profesionalismos.listar_profesionalismos'))
    
    cursor.execute("DELETE FROM t_profesionalismo WHERE prfm_prfm = %s;", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('profesionalismos.listar_profesionalismos'))
