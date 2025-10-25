from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection

profesionalismos_bp = Blueprint('profesionalismos', __name__)

@profesionalismos_bp.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT dprt_dprt, dprt_descri FROM t_deportes ORDER BY dprt_dprt;")
    deportes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('form_profesionalismo.html', deportes=deportes)

@profesionalismos_bp.route('/insertar_profesionalismo', methods=['POST'])
def insertar_profesionalismo():
    deporte_id = request.form['deporte']
    descripcion = request.form['descripcion']

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO t_profesionalismo (prfm_dprt, prfm_descri)
        VALUES (%s, %s);
    """, (deporte_id, descripcion))
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
    cursor.execute("SELECT dprt_dprt, dprt_descri FROM t_deportes ORDER BY dprt_dprt;")
    deportes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('editar_profesionalismo.html', profesionalismo=profesionalismo, deportes=deportes)

@profesionalismos_bp.route('/actualizar_profesionalismo', methods=['POST'])
def actualizar_profesionalismo():
    id_prof = request.form['id']
    deporte = request.form['deporte']
    descripcion = request.form['descripcion']

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE t_profesionalismo
        SET prfm_dprt = %s,
            prfm_descri = %s,
            prfm_usua_alt = USER,
            prfm_fecalt = CURRENT_TIMESTAMP
        WHERE prfm_prfm = %s;
    """, (deporte, descripcion, id_prof))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('profesionalismos.listar_profesionalismos'))

@profesionalismos_bp.route('/eliminar_profesionalismo/<int:id>')
def eliminar_profesionalismo(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM t_profesionalismo WHERE prfm_prfm = %s;", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('profesionalismos.listar_profesionalismos'))
