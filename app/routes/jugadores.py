from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection

jugadores_bp = Blueprint('jugadores', __name__)

# --- Listar jugadores ---
@jugadores_bp.route('/listar_jugadores')
def listar_jugadores():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT j.jgdr_jgdr, j.jgdr_nombres, j.jgdr_apelidos,
               CASE j.jgdr_genero 
			     WHEN 'M' THEN 'Masculino'
				 WHEN 'F' THEN 'Femenino'
				 ELSE 'Indefinindo - ' || j.jgdr_genero
			   END jgdr_genero,
               p.prfm_descri, 
               CASE WHEN j.jgdr_estado THEN 'Activo' ELSE 'Inactivo' END AS estado
        FROM t_jugadores j
        JOIN t_profesionalismo p ON p.prfm_prfm = j.jgdr_prfm
        ORDER BY j.jgdr_apelidos, j.jgdr_nombres;
    """)
    jugadores = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('lista_jugadores.html', jugadores=jugadores)

# --- Formulario de creación ---
@jugadores_bp.route('/jugadores')
def form_jugador():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT prfm_prfm, prfm_descri FROM t_profesionalismo ORDER BY prfm_descri;")
    profesionalismos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('form_jugador.html', profesionalismos=profesionalismos)

# --- Insertar jugador ---
@jugadores_bp.route('/insertar_jugador', methods=['POST'])
def insertar_jugador():
    cedula = request.form['cedula']
    nombres = request.form['nombres']
    apellidos = request.form['apellidos']
    genero = request.form['genero']
    profesionalismo = request.form['profesionalismo']

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO t_jugadores (jgdr_jgdr, jgdr_nombres, jgdr_apelidos, jgdr_genero, jgdr_prfm)
            VALUES (%s, %s, %s, %s, %s);
        """, (cedula, nombres, apellidos, genero, profesionalismo))
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"Error al insertar jugador: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('jugadores.listar_jugadores'))

# --- Editar jugador ---
@jugadores_bp.route('/editar_jugador/<int:id>')
def editar_jugador(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT jgdr_jgdr, jgdr_nombres, jgdr_apelidos,
               CASE jgdr_genero 
			     WHEN 'M' THEN 'Masculino'
				 WHEN 'F' THEN 'Femenino'
				 ELSE 'Indefinindo - ' || jgdr_genero
			   END jgdr_genero, jgdr_prfm, jgdr_estado
        FROM t_jugadores
        WHERE jgdr_jgdr = %s;
    """, (id,))
    jugador = cursor.fetchone()

    cursor.execute("SELECT prfm_prfm, prfm_descri FROM t_profesionalismo ORDER BY prfm_descri;")
    profesionalismos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('editar_jugador.html', jugador=jugador, profesionalismos=profesionalismos)

# --- Actualizar jugador ---
@jugadores_bp.route('/actualizar_jugador', methods=['POST'])
def actualizar_jugador():
    cedula = request.form['cedula']
    nombres = request.form['nombres']
    apellidos = request.form['apellidos']
    genero = request.form['genero']
    profesionalismo = request.form['profesionalismo']
    estado = request.form['estado'] == 'True'

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE t_jugadores
            SET jgdr_nombres = %s,
                jgdr_apelidos = %s,
                jgdr_genero = %s,
                jgdr_prfm = %s,
                jgdr_estado = %s,
                jgdr_usua_alt = USER,
                jgdr_fecalt = CURRENT_TIMESTAMP
            WHERE jgdr_jgdr = %s;
        """, (nombres, apellidos, genero, profesionalismo, estado, cedula))
        conn.commit()
        flash("Jugador actualizado correctamente.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al actualizar jugador: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('jugadores.listar_jugadores'))

# --- Eliminar jugador ---
@jugadores_bp.route('/eliminar_jugador/<int:id>')
def eliminar_jugador(id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM t_jugadores WHERE jgdr_jgdr = %s;", (id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar jugador: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('jugadores.listar_jugadores'))
