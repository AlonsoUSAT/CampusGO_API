from flask import Flask
from flask_jwt_extended import JWTManager
from config import Config
from services.auth_service import AuthService

def main():
    print("=== Probando AuthService ===")
    app = Flask(__name__)
    app.config.from_object(Config)
    JWTManager(app)

    auth_service = AuthService()

    with app.app_context():
        # 1. Login exitoso
        email_valido = "juan.perez@usat.edu.pe"
        pass_valido = "CampusGo#2026"
        print(f"\n1. Intentando login correcto para: {email_valido}...")
        data, mensaje, status_code = auth_service.login(email_valido, pass_valido)
        print(f"   Status Code: {status_code}")
        print(f"   Mensaje: {mensaje}")
        if data and "token" in data:
            print(f"   [OK] Token JWT generado: {data['token'][:25]}...")
            print(f"   [OK] Datos retornados: id={data['usuario_id']}, rol={data['rol']}")

        # 2. Contraseña incorrecta
        print(f"\n2. Intentando login con clave erronea...")
        data, mensaje, status_code = auth_service.login(email_valido, "ClaveIncorrecta")
        print(f"   Status Code: {status_code}")
        print(f"   Mensaje: {mensaje}")
        if status_code == 401 and data is None:
            print("   [OK] Rechazado correctamente con 401.")

        # 3. Usuario inexistente
        print(f"\n3. Intentando login con correo inexistente...")
        data, mensaje, status_code = auth_service.login("noexiste@usat.edu.pe", "CampusGo#2026")
        print(f"   Status Code: {status_code}")
        print(f"   Mensaje: {mensaje}")
        if status_code == 401 and data is None:
            print("   [OK] Rechazado correctamente con 401.")

    print("\n=== Fin de la prueba ===")

if __name__ == "__main__":
    main()
