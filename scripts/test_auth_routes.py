import json
from app import create_app

def print_response(title, response):
    print(f"\n==========================================")
    print(f"CASO: {title}")
    print(f"Status Code: {response.status_code}")
    try:
        data = response.get_json()
        print("Response JSON:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print("Raw Data:", response.data.decode("utf-8"))
    print(f"==========================================")

def main():
    app = create_app()
    client = app.test_client()

    # 1. Credenciales correctas -> 200 OK
    res_200 = client.post(
        "/api/auth/login",
        json={
            "email": "juan.perez@usat.edu.pe",
            "password": "CampusGo#2026"
        }
    )
    print_response("1. Credenciales correctas (Esperado: 200)", res_200)

    # 2. Body incompleto (sin JSON / campos vacíos) -> 400 Bad Request
    res_400_no_json = client.post(
        "/api/auth/login",
        data="esto no es json",
        content_type="text/plain"
    )
    print_response("2a. Body no es JSON (Esperado: 400)", res_400_no_json)

    res_400_empty = client.post(
        "/api/auth/login",
        json={
            "email": "juan.perez@usat.edu.pe"
            # Falta password
        }
    )
    print_response("2b. Falta el password (Esperado: 400)", res_400_empty)

    # 3. Credenciales incorrectas -> 401 Unauthorized
    res_401 = client.post(
        "/api/auth/login",
        json={
            "email": "juan.perez@usat.edu.pe",
            "password": "ClaveEquivocada"
        }
    )
    print_response("3. Credenciales incorrectas (Esperado: 401)", res_401)

    # 4. Usuario inactivo -> 403 Forbidden
    res_403 = client.post(
        "/api/auth/login",
        json={
            "email": "inactivo@campusgo.pe",
            "password": "CampusGo#2026"
        }
    )
    print_response("4. Usuario inactivo (Esperado: 403)", res_403)

if __name__ == "__main__":
    main()
