from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection
import numpy as np
from sklearn.neural_network import MLPClassifier

rendimiento_bp = Blueprint('rendimiento', __name__, template_folder='templates')

# ------------------------------------------
# Funciones auxiliares
# ------------------------------------------

def calcular_rendimiento(goles, asist, lf, lm, lg):
    """
    Cálculo sencillo:
    - Goles valen 20 pts
    - Asistencias 10 pts
    - Faltas leves -4, medias -10, graves -20
    """
    score = (goles * 20) + (asist * 10) - (lf * 4) - (lm * 10) - (lg * 20)
    score = max(0, min(score, 100))
    return score


def calcular_reputacion(rendimiento):
    """De 0 a 5 estrellas según rendimiento."""
    return round((rendimiento / 100) * 5, 1)


def entrenar_red_neuronal(historial):
    """
    historial = lista de tuplas:
    (goles, asistencias, faltas_totales, rendimiento_category)
    rendimiento_category:
      0 = bajo, 1 = medio, 2 = alto
    """
    if len(historial) < 5:
        return None  # no hay suficientes datos

    X = np.array([[h[0], h[1], h[2]] for h in historial])
    y = np.array([h[3] for h in historial])

    model = MLPClassifier(hidden_layer_sizes=(6,),
                          activation='relu',
                          max_iter=500)

    model.fit(X, y)
    return model

# ------------------------------------------
# Página principal del módulo
# ------------------------------------------

@rendimiento_bp.route('/rendimiento_jugadores')
def rendimiento_jugadores():

    conn = get_connection()
    cursor = conn.cursor()

    # Obtener todos los registros por jugador
    cursor.execute("""
        SELECT 
              r.rgtr_jugador,
              j.jgdr_nombres || ' ' || j.jgdr_apelidos AS nombre,
              COALESCE(r.rgtr_goles,0) AS goles,
              COALESCE(r.rgtr_asistencias,0) AS asistencias,
              array_to_string(r.rgtr_faltas,'') AS faltas
          FROM t_Registros r
          JOIN t_jugadores j
            ON j.jgdr_jgdr = r.rgtr_jugador
          JOIN t_partidos p
            ON p.prtd_prtd = r.rgtr_partido
           AND p.prtd_trno = r.rgtr_torneo
          WHERE p.prtd_estado != 'P'
          ORDER BY r.rgtr_jugador, r.rgtr_fecreg;
    """)

    datos = cursor.fetchall()
    cursor.close()
    conn.close()

    jugadores = {}

    historial_entrenamiento = []

    for cedula, nombre, goles, asist, faltas_str in datos:

        lf = faltas_str.count("L") if faltas_str else 0
        lm = faltas_str.count("M") if faltas_str else 0
        lg = faltas_str.count("G") if faltas_str else 0
        faltas_totales = lf + lm + lg

        rendimiento = calcular_rendimiento(goles, asist, lf, lm, lg)

        # Categoría para entrenar NN
        if rendimiento < 40:
            cat = 0
        elif rendimiento < 70:
            cat = 1
        else:
            cat = 2

        historial_entrenamiento.append(
            (goles, asist, faltas_totales, cat)
        )

        if cedula not in jugadores:
            jugadores[cedula] = {
                'nombre': nombre,
                'historial': [],
                'rendimiento_prom': 0,
                'reputacion': 0
            }

        jugadores[cedula]['historial'].append({
            'goles': goles,
            'asistencias': asist,
            'faltas_l': lf,
            'faltas_m': lm,
            'faltas_g': lg,
            'rendimiento': rendimiento
        })

    # Calcular acumulados y rendimiento final
    for cedula, info in jugadores.items():
        total_goles = sum(h['goles'] for h in info['historial'])
        total_asist = sum(h['asistencias'] for h in info['historial'])
        total_l = sum(h['faltas_l'] for h in info['historial'])
        total_m = sum(h['faltas_m'] for h in info['historial'])
        total_g = sum(h['faltas_g'] for h in info['historial'])
        partidos = len(info['historial'])
        rendimiento_prom = (
            sum(h['rendimiento'] for h in info['historial']) / partidos
            if partidos > 0 else 0
        )

        jugadores[cedula].update({
            'total_goles': total_goles,
            'total_asist': total_asist,
            'total_l': total_l,
            'total_m': total_m,
            'total_g': total_g,
            'partidos_jugados': partidos,
            'rendimiento_prom': round(rendimiento_prom, 1),
            'reputacion': calcular_reputacion(rendimiento_prom)
        })

    # Predicciones (muy básicas)
    for cedula, info in jugadores.items():
        historial_ent = []

        # Construir historial del jugador
        for h in info['historial']:
            faltas_tot = h['faltas_l'] + h['faltas_m'] + h['faltas_g']
            rendimiento = h['rendimiento']
            # Categoría para entrenar NN
            if rendimiento < 40:
                cat = 0
            elif rendimiento < 70:
                cat = 1
            else:
                cat = 2
            historial_ent.append((h['goles'], h['asistencias'], faltas_tot, cat))
        # Entrenar solo si tiene al menos 5 partidos
        if len(historial_ent) >= 5:
            modelo = entrenar_red_neuronal(historial_ent)
            ult = info['historial'][-1]
            X_pred = np.array([[ult['goles'], ult['asistencias'],
                                ult['faltas_l'] + ult['faltas_m'] + ult['faltas_g']]])
            pred = modelo.predict(X_pred)[0]
        else:
            pred = None  # no hay suficientes datos
        
        info['prediccion'] = pred

    return render_template("rendimiento_jugadores.html", jugadores=jugadores)

@rendimiento_bp.route('/auto_registrar_jugadores/<int:partido>/<int:torneo>', methods=['POST'])
def auto_registrar_jugadores(partido, torneo):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # ░░ 1. Reglas del torneo ░░
        cursor.execute("""
            SELECT trno_min_jugadores, trno_max_jugadores, trno_jugadores_cancha
            FROM t_Torneo
            WHERE trno_trno = %s
        """, (torneo,))
        t_rules = cursor.fetchone()

        if not t_rules:
            flash("Torneo no encontrado.", "danger")
            return redirect(url_for("registros.gestion_jugadores_partido",
                                    id_torneo=torneo, id_partido=partido))

        min_por_equipo, max_por_equipo, jugadores_cancha = map(int, t_rules)

        # ░░ 2. Equipos del partido ░░
        cursor.execute("""
            SELECT prtd_local, prtd_visitante
            FROM t_partidos
            WHERE prtd_prtd = %s AND prtd_trno = %s
        """, (partido, torneo))
        row = cursor.fetchone()

        if not row:
            flash("Partido no válido.", "danger")
            return redirect(url_for("registros.gestion_jugadores_partido",
                                    id_torneo=torneo, id_partido=partido))

        equipo_local, equipo_visitante = row

        equipos = [
            ("Local", equipo_local),
            ("Visitante", equipo_visitante)
        ]

        total_registrados = 0
        avisos = []

        # ░░ 3. Procesar cada equipo ░░
        for etiqueta, equipo_id in equipos:

            # Jugadores activos en el torneo
            cursor.execute("""
                SELECT jgtr_jugador, jgtr_nro_camiseta
                FROM t_Jugador_Torneo
                WHERE jgtr_torneo = %s
                  AND jgtr_equipo = %s
                  AND jgtr_estado = TRUE
            """, (torneo, equipo_id))

            jugadores = cursor.fetchall()

            if not jugadores or len(jugadores) < min_por_equipo:
                avisos.append(
                    f"Equipo {etiqueta}: {len(jugadores)} jugadores activos (mínimo {min_por_equipo})."
                )
                continue

            candidatos = []

            # ░░ 4. Historial global REAL ░░
            for (jug_id, nro_cami) in jugadores:

                cursor.execute("""
                    SELECT 
                        COALESCE(rgtr_goles, 0),
                        COALESCE(rgtr_asistencias, 0),
                        array_to_string(rgtr_faltas, '')
                    FROM t_Registros
                    WHERE rgtr_jugador = %s
                    ORDER BY rgtr_fecreg
                """, (jug_id,))

                registros = cursor.fetchall()

                historial = []
                rendimientos = []

                for goles, asist, faltas_str in registros:
                    faltas_str = faltas_str or ""
                    lf = faltas_str.count("L")
                    lm = faltas_str.count("M")
                    lg = faltas_str.count("G")
                    faltas_tot = lf + lm + lg

                    rend = calcular_rendimiento(goles, asist, lf, lm, lg)
                    historial.append((goles, asist, faltas_tot, rend))
                    rendimientos.append(rend)

                partidos_jugados = len(historial)
                promedio = round(sum(rendimientos) / partidos_jugados, 1) if partidos_jugados else 0

                # ░░ 5. Predicción opcional ░░
                entrenamiento = []
                for g, a, f, rend in historial:
                    if rend < 40: cat = 0
                    elif rend < 70: cat = 1
                    else: cat = 2
                    entrenamiento.append((g, a, f, cat))

                pred = None
                if len(entrenamiento) >= 5:
                    modelo = entrenar_red_neuronal(entrenamiento)
                    if modelo:
                        ult = entrenamiento[-1]
                        Xp = np.array([[ult[0], ult[1], ult[2]]])
                        try:
                            pred = int(modelo.predict(Xp)[0])
                        except: pred = None

                candidatos.append({
                    "jugador": jug_id,
                    "nro": nro_cami,
                    "rend_prom": promedio,
                    "partidos": partidos_jugados,
                    "pred": pred
                })

            # ░░ 6. ORDENAMIENTO FINAL (CORRECTO) ░░
            def sort_key(c):
                pred_val = c["pred"] if c["pred"] is not None else -1
                return (
                    c["rend_prom"],  # primero rendimiento
                    pred_val,        # luego predicción
                    c["partidos"]    # luego experiencia
                )

            candidatos_sorted = sorted(candidatos, key=sort_key, reverse=True)

            # ░░ 7. Selección de titulares y banca ░░
            titulares_count = min(jugadores_cancha, len(candidatos_sorted))
            total_squad = min(max_por_equipo, len(candidatos_sorted))

            seleccionados = candidatos_sorted[:total_squad]

            registrados_por_equipo = 0

            for idx, c in enumerate(seleccionados):
                estado = 'J' if idx < titulares_count else 'B'

                cursor.execute("""
                    INSERT INTO t_Registros (rgtr_torneo, rgtr_partido, rgtr_jugador, rgtr_estado, rgtr_fecreg)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (rgtr_torneo, rgtr_partido, rgtr_jugador)
                    DO UPDATE SET rgtr_estado = EXCLUDED.rgtr_estado
                """, (torneo, partido, c["jugador"], estado))

                if cursor.rowcount > 0:
                    registrados_por_equipo += cursor.rowcount

            total_registrados += registrados_por_equipo
            avisos.append(
                f"{etiqueta}: {registrados_por_equipo} jugadores asignados ({titulares_count} titulares)."
            )

        conn.commit()

        flash(f"Automatización finalizada. Total: {total_registrados}", "success")
        for a in avisos:
            flash(a, "info")

    except Exception as e:
        conn.rollback()
        flash(f"Error: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("registros.gestion_jugadores_partido",
                            id_torneo=torneo,
                            id_partido=partido))
