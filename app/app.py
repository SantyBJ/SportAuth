from flask import Flask
from config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Importar y registrar los blueprints
    from routes.profesionalismos import profesionalismos_bp
    from routes.torneos import torneos_bp
    from routes.jugadores import jugadores_bp

    app.register_blueprint(profesionalismos_bp)
    app.register_blueprint(torneos_bp)
    app.register_blueprint(jugadores_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    #app.run(debug=True)
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
