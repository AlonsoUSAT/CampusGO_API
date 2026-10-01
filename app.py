import datetime
import decimal
from flask import Flask
from flask.json.provider import DefaultJSONProvider
from flask_jwt_extended import JWTManager
from config import Config
from routes.auth_routes import auth_bp
from routes.usuario_routes import usuario_bp
from routes.viaje_routes import viaje_bp
from routes.reserva_routes import reserva_bp


class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, (datetime.time, datetime.timedelta)):
            return str(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


def create_app():
    app = Flask(__name__)
    app.json = CustomJSONProvider(app)
    app.config.from_object(Config)
    JWTManager(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(viaje_bp)
    app.register_blueprint(reserva_bp)

    @app.get("/")
    def inicio():
        return {
            "data": {
                "app": "CampusGo API REST"
            },
            "message": "API disponible",
            "status": True
        }, 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
