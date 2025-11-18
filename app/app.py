from flask import Flask
from config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Importar y registrar los blueprints
    from routes.home                  import home_bp
    from routes.profesionalismos      import profesionalismos_bp
    from routes.torneos               import torneos_bp
    from routes.jugadores             import jugadores_bp
    from routes.rendimiento_jugadores import rendimiento_bp
    from routes.equipos               import equipos_bp
    from routes.equipo_torneo         import equipos_torneo_bp
    from routes.jugador_torneo        import jugador_torneo_bp
    from routes.partidos              import partidos_bp
    from routes.registros             import registros_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(profesionalismos_bp)
    app.register_blueprint(torneos_bp)
    app.register_blueprint(jugadores_bp)
    app.register_blueprint(rendimiento_bp)
    app.register_blueprint(equipos_bp)
    app.register_blueprint(equipos_torneo_bp)
    app.register_blueprint(jugador_torneo_bp)
    app.register_blueprint(partidos_bp)
    app.register_blueprint(registros_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
