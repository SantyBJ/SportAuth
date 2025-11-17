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
    - Goles valen 5 pts
    - Asistencias 3 pts
    - Faltas leves -1, medias -2, graves -3
    """
    score = (goles * 5) + (asist * 3) - (lf * 1) - (lm * 2) - (lg * 3)
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
        if rendimiento < 35:
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
        rendimiento_prom = sum(h['rendimiento'] for h in info['historial']) / partidos

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
            if rendimiento < 35:
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
