from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection

equipos_torneo_bp = Blueprint('equipo_torneo', __name__)

def existe_equipo_en_torneo(id_equipo, id_torneo):
    """
    Retorna True si el equipo ya está registrado en el torneo.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) 
        FROM t_Equipo_Torneo
        WHERE eqtn_equipo = %s AND eqtn_torneo = %s;
    """, (id_equipo, id_torneo))
    existe = cursor.fetchone()[0] > 0
    cursor.close()
    conn.close()
    return existe

@equipos_torneo_bp.route('/equipo_torneo/<int:id_torneo>')
def listar_equipos_torneo(id_torneo):
    conn = get_connection()
    cursor = conn.cursor()

    # Información del torneo
    cursor.execute("""
        SELECT trno_trno, trno_nombre, trno_min_equipos, trno_max_equipos,
               CASE trno_estado 
                  WHEN 'P' THEN 'Programado'
                  WHEN 'E' THEN 'En ejecución'
                  WHEN 'F' THEN 'Finalizado'
                  ELSE 'Indefinido'
               END AS estado
        FROM t_Torneo 
        WHERE trno_trno = %s;
    """, (id_torneo,))
    torneo = cursor.fetchone()

    cursor.execute("""
        SELECT et.eqtn_equipo, e.eqpo_nombre, et.eqtn_estado
        FROM t_Equipo_Torneo et
        JOIN t_Equipos e ON e.eqpo_eqpo = et.eqtn_equipo
        WHERE et.eqtn_torneo = %s
        ORDER BY e.eqpo_nombre;
    """, (id_torneo,))
    equipos = cursor.fetchall()

    cursor.execute("""
        SELECT eqpo_eqpo, eqpo_nombre
        FROM t_Equipos
        WHERE eqpo_eqpo NOT IN (
            SELECT eqtn_equipo 
            FROM t_Equipo_Torneo 
            WHERE eqtn_torneo = %s
        )
        AND eqpo_estado
        ORDER BY eqpo_nombre;
    """, (id_torneo,))
    disponibles = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('gestion_equipos_torneo.html',
                           torneo=torneo,
                           equipos=equipos,
                           disponibles=disponibles)

@equipos_torneo_bp.route('/insertar_equipo_torneo', methods=['POST'])
def insertar_equipo_torneo():
    id_torneo = request.form['id_torneo']
    id_equipo = request.form['id_equipo']

    if existe_equipo_en_torneo(id_equipo, id_torneo):
        flash("El equipo ya está registrado en este torneo.", "error")
        return redirect(url_for('equipo_torneo.listar_equipos_torneo', id_torneo=id_torneo))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT trno_estado FROM t_Torneo WHERE trno_trno = %s;", (id_torneo,))
    estado_torneo = cursor.fetchone()

    if not estado_torneo:
        flash("Torneo no encontrado.", "error")
        cursor.close()
        conn.close()
        return redirect(url_for('equipo_torneo.listar_equipos_torneo', id_torneo=id_torneo))

    if estado_torneo[0] == 'F':
        flash("No se pueden asociar equipos a un torneo ya finalizado.", "error")
        cursor.close()
        conn.close()
        return redirect(url_for('equipo_torneo.listar_equipos_torneo', id_torneo=id_torneo))

    if existe_equipo_en_torneo(id_equipo, id_torneo):
        flash("El equipo ya está registrado en este torneo.", "error")
        cursor.close()
        conn.close()
        return redirect(url_for('equipo_torneo.listar_equipos_torneo', id_torneo=id_torneo))

    cursor.execute("""
        SELECT COUNT(*) FROM t_Equipo_Torneo WHERE eqtn_torneo = %s
    """, (id_torneo,))
    total_actual = cursor.fetchone()[0]

    cursor.execute("""
        SELECT trno_max_jugadores FROM t_Torneo WHERE trno_trno = %s
    """, (id_torneo,))
    max_permitido = cursor.fetchone()[0]

    if total_actual > max_permitido:
        cursor.close()
        conn.close()
        flash("Se ha alcanzado el número máximo de equipos permitidos para este torneo", "error")
        return redirect(url_for('equipo_torneo.listar_equipos_torneo', id_torneo=id_torneo))

    try:
        cursor.execute("""
            INSERT INTO t_Equipo_Torneo (eqtn_equipo, eqtn_torneo, eqtn_estado, eqtn_usua, eqtn_feccre)
            VALUES (%s, %s, TRUE, USER, CURRENT_TIMESTAMP);
        """, (id_equipo, id_torneo))
        conn.commit()
        flash("Equipo registrado correctamente en el torneo.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al registrar el equipo: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('equipo_torneo.listar_equipos_torneo', id_torneo=id_torneo))

@equipos_torneo_bp.route('/cambiar_estado_equipo_torneo/<int:id_torneo>/<int:id_equipo>')
def cambiar_estado_equipo_torneo(id_torneo, id_equipo):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT eqtn_estado
            FROM t_Equipo_Torneo
            WHERE eqtn_torneo = %s AND eqtn_equipo = %s;
        """, (id_torneo, id_equipo))
        estado_actual = cursor.fetchone()

        if not estado_actual:
            flash("No se encontró el equipo en este torneo.", "error")
            return redirect(url_for('equipo_torneo.listar_equipos_torneo', id_torneo=id_torneo))

        estado_actual = estado_actual[0]

        if not estado_actual:
            cursor.execute("""
                SELECT eqpo_estado
                FROM t_Equipos
                WHERE eqpo_eqpo = %s;
            """, (id_equipo,))
            estado_equipo = cursor.fetchone()

            if not estado_equipo or not estado_equipo[0]:
                flash("El equipo no se encuentra activo.", "error")
                cursor.close()
                conn.close()
                return redirect(url_for('equipo_torneo.listar_equipos_torneo', id_torneo=id_torneo))

        cursor.execute("""
            UPDATE t_Equipo_Torneo
            SET eqtn_estado = NOT eqtn_estado
               ,eqtn_usua_alt = USER
               ,eqtn_fecalt   = CURRENT_TIMESTAMP
            WHERE eqtn_torneo = %s AND eqtn_equipo = %s;
        """, (id_torneo, id_equipo))
        conn.commit()
        flash("Estado del equipo actualizado correctamente.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al cambiar el estado: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('equipo_torneo.listar_equipos_torneo', id_torneo=id_torneo))

@equipos_torneo_bp.route('/eliminar_equipo_torneo/<int:id_torneo>/<int:id_equipo>')
def eliminar_equipo_torneo(id_torneo, id_equipo):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # --- Validar jugadores asociados ---
        cursor.execute("""
            SELECT COUNT(*) 
            FROM t_Jugador_Torneo
            WHERE jgtr_torneo = %s AND jgtr_equipo = %s;
        """, (id_torneo, id_equipo))
        jugadores_asociados = cursor.fetchone()[0]

        if jugadores_asociados > 0:
            flash("No se puede desvincular el equipo ya que tiene jugadores registrados.", "error")
            cursor.close()
            conn.close()
            return redirect(url_for('equipo_torneo.listar_equipos_torneo', id_torneo=id_torneo))

        # --- Validar partidos asociados ---
        cursor.execute("""
            SELECT COUNT(*)
            FROM t_Partidos
            WHERE prtd_trno = %s
              AND (prtd_local = %s OR prtd_visitante = %s);
        """, (id_torneo, id_equipo, id_equipo))
        partidos_asociados = cursor.fetchone()[0]

        if partidos_asociados > 0:
            flash("El equipo que trató de eliminar tiene partidos asociados.", "error")
            cursor.close()
            conn.close()
            return redirect(url_for('equipo_torneo.listar_equipos_torneo', id_torneo=id_torneo))

        # --- Eliminar equipo del torneo ---
        cursor.execute("""
            DELETE FROM t_Equipo_Torneo
            WHERE eqtn_torneo = %s AND eqtn_equipo = %s;
        """, (id_torneo, id_equipo))

        conn.commit()
        flash("Equipo eliminado del torneo correctamente.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar el equipo del torneo: {e}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('equipo_torneo.listar_equipos_torneo', id_torneo=id_torneo))