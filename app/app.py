from flask import Flask, render_template, request, redirect, url_for # type: ignore
import psycopg2
import os
from dotenv import load_dotenv # type: ignore

load_dotenv()  # Carga las variables del archivo .env

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )


# --- Página principal (formulario para agregar) ---
@app.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT dprt_dprt, dprt_descri FROM t_deportes ORDER BY dprt_dprt;")
    deportes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('form_profesionalismo.html', deportes=deportes)

# --- Crear profesionalismo ---
@app.route('/insertar', methods=['POST'])
def insertar():
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

    return redirect(url_for('listar'))

# --- Listar profesionalismos ---
@app.route('/listar')
def listar():
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

# --- Formulario de edición ---
@app.route('/editar/<int:id>')
def editar(id):
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

# --- Actualizar profesionalismo ---
@app.route('/actualizar', methods=['POST'])
def actualizar():
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

    return redirect(url_for('listar'))

# --- Eliminar profesionalismo ---
@app.route('/eliminar/<int:id>')
def eliminar(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM t_profesionalismo WHERE prfm_prfm = %s;", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('listar'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)