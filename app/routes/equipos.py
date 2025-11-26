from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection

equipos_bp = Blueprint('equipos', __name__)

def existe_equipo(nombre, id_excluir=None):
    """
    Retorna True si ya existe un equipo con el mismo nombre (ignorando mayúsculas).
    Si id_excluir se proporciona, lo excluye de la búsqueda (útil al actualizar).
    """
    conn = get_connection()
    cursor = conn.cursor()

    if id_excluir:
        cursor.execute("""
            SELECT COUNT(*) FROM t_Equipos
            WHERE LOWER(eqpo_nombre) = LOWER(%s)
              AND eqpo_eqpo <> %s;
        """, (nombre, id_excluir))
    else:
        cursor.execute("""
            SELECT COUNT(*) FROM t_Equipos
            WHERE LOWER(eqpo_nombre) = LOWER(%s);
        """, (nombre,))
    
    existe = cursor.fetchone()[0] > 0
    cursor.close()
    conn.close()
    return existe

@equipos_bp.route('/equipos')
def equipos():
    return render_template('form_equipo.html')

# --- Insertar nuevo equipo ---
@equipos_bp.route('/insertar_equipo', methods=['POST'])
def insertar_equipo():
    nombre = request.form['nombre']

    if existe_equipo(nombre):
        flash(f"Ya existe un equipo con el nombre '{nombre}'.", "error")
        return redirect(url_for('equipos.equipos'))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO t_Equipos (eqpo_nombre, eqpo_estado)
        VALUES (%s, TRUE);
    """, (nombre,))
    
    conn.commit()
    cursor.close()
    conn.close()

    flash("Equipo registrado correctamente.", "success")
    return redirect(url_for('equipos.listar_equipos'))

# --- Listar equipos ---
@equipos_bp.route('/listar_equipos')
def listar_equipos():
    conn = get_connection()
    cursor = conn.cursor()

    # Obtener equipos
    cursor.execute("""
        SELECT eqpo_eqpo, eqpo_nombre, eqpo_estado
        FROM t_Equipos
        ORDER BY eqpo_eqpo;
    """)
    equipos_raw = cursor.fetchall()

    equipos = []

    for id_equipo, nombre, estado in equipos_raw:

        # --- 1. Obtener partidos del equipo ---
        cursor.execute("""
            SELECT prtd_prtd, prtd_local, prtd_visitante
            FROM t_partidos
            WHERE prtd_local = %s OR prtd_visitante = %s;
        """, (id_equipo, id_equipo))
        partidos = cursor.fetchall()

        partidos_jugados = len(partidos)
        ganados = empatados = perdidos = 0
        goles_favor = goles_contra = 0

        for prtd_id, loc, vis in partidos:

            # --- 2. Goles a favor ---
            cursor.execute("""
                SELECT SUM(COALESCE(r.rgtr_goles,0))
                FROM t_registros r
                JOIN t_jugador_torneo jt 
                    ON jt.jgtr_jugador = r.rgtr_jugador 
                   AND jt.jgtr_torneo = r.rgtr_torneo
                WHERE r.rgtr_partido = %s
                  AND jt.jgtr_equipo = %s;
            """, (prtd_id, id_equipo))
            gf = cursor.fetchone()[0] or 0

            # --- 3. Goles en contra (sumar goles del rival) ---
            rival = vis if id_equipo == loc else loc

            cursor.execute("""
                SELECT SUM(COALESCE(r.rgtr_goles,0))
                FROM t_registros r
                JOIN t_jugador_torneo jt 
                    ON jt.jgtr_jugador = r.rgtr_jugador 
                   AND jt.jgtr_torneo = r.rgtr_torneo
                WHERE r.rgtr_partido = %s
                  AND jt.jgtr_equipo = %s;
            """, (prtd_id, rival))
            gc = cursor.fetchone()[0] or 0

            goles_favor += gf
            goles_contra += gc

            # --- 4. Determinar resultado ---
            if gf > gc:
                ganados += 1
            elif gf == gc:
                empatados += 1
            else:
                perdidos += 1

        # --- 5. Calcular rendimiento ---
        puntos = (ganados * 3) + (empatados * 1)
        rendimiento = 0
        if partidos_jugados > 0:
            rendimiento = round((puntos / (partidos_jugados * 3)) * 100, 1)

        equipos.append({
            'id': id_equipo,
            'nombre': nombre,
            'estado': estado,
            'pj': partidos_jugados,
            'pg': ganados,
            'pe': empatados,
            'pp': perdidos,
            'gf': goles_favor,
            'gc': goles_contra,
            'dg': goles_favor - goles_contra,
            'rend': rendimiento
        })

    cursor.close()
    conn.close()

    return render_template('lista_equipos.html', equipos=equipos)

# --- Editar equipo ---
@equipos_bp.route('/editar_equipo/<int:id>')
def editar_equipo(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT eqpo_eqpo, eqpo_nombre, eqpo_estado
        FROM t_Equipos
        WHERE eqpo_eqpo = %s;
    """, (id,))
    equipo = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('editar_equipo.html', equipo=equipo)

# --- Actualizar equipo ---
@equipos_bp.route('/actualizar_equipo', methods=['POST'])
def actualizar_equipo():
    id_equipo = request.form['id']
    nombre = request.form['nombre']
    estado = request.form.get('estado') == 'on'

    if existe_equipo(nombre, id_excluir=id_equipo):
        flash(f"No se puede actualizar: ya existe un equipo con el nombre '{nombre}'.", "error")
        return redirect(url_for('equipos.editar_equipo', id=id_equipo))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE t_Equipos
        SET eqpo_nombre = %s,
            eqpo_estado = %s,
            eqpo_usua_alt = USER,
            eqpo_fecalt = CURRENT_TIMESTAMP
        WHERE eqpo_eqpo = %s;
    """, (nombre, estado, id_equipo))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('equipos.listar_equipos'))

@equipos_bp.route('/eliminar_equipo/<int:id>')
def eliminar_equipo(id):
    conn = get_connection()
    cursor = conn.cursor()

    # 🔹 Validar si el equipo está asociado a torneos
    cursor.execute("""
        SELECT COUNT(*) 
        FROM t_Equipo_Torneo 
        WHERE eqtn_equipo = %s;
    """, (id,))
    asociados = cursor.fetchone()[0]

    if asociados > 0:
        flash("Si requiere eliminar este equipo, desvincúlelo de torneos asociados.", "error")
        cursor.close()
        conn.close()
        return redirect(url_for('equipos.listar_equipos'))

    cursor.execute("DELETE FROM t_Equipos WHERE eqpo_eqpo = %s;", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("✅ Equipo eliminado correctamente.", "success")
    return redirect(url_for('equipos.listar_equipos'))
