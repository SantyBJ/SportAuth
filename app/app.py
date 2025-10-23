from flask import Flask, render_template, request, redirect, url_for
import psycopg2

app = Flask(__name__)

# --- Configuración conexión PostgreSQL ---
def get_connection():
    return psycopg2.connect(
    dbname="SportAuth",
    user="postgres",
    password="S@ntiago21",
    port="5432"
    )

# --- Página principal: formulario con lista de deportes ---
@app.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT dprt_dprt, dprt_descri FROM t_deportes ORDER BY dprt_dprt;")  # Ajusta nombres según tu tabla real
    deportes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('form_profesionalismo.html', deportes=deportes)

# --- Insertar profesionalismo ---
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
        FROM t_profesionalismo p
        JOIN t_deportes ON dprt_dprt = prfm_dprt
        ORDER BY prfm_prfm;
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('lista_profesionalismos.html', profesionalismos=data)

if __name__ == '__main__':
    app.run(debug=True)
