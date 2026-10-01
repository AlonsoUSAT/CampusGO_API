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

    print("=== Probando Flujo Completo y /api/perfil ===")

    # 1. Intentar acceder a /api/perfil sin token (Esperado: 401)
    res_no_token = client.get("/api/perfil")
    print_response("1. Acceso a /api/perfil sin token (Esperado: 401)", res_no_token)

    # 2. Iniciar sesión para obtener el token JWT
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "juan.perez@usat.edu.pe",
            "password": "CampusGo#2026"
        }
    )
    login_data = login_res.get_json()
    token = login_data["data"]["token"]
    print(f"\n[OK] Login realizado con exito. Token obtenido: {token[:30]}...")

    # 3. Acceder a /api/perfil con Bearer Token (Esperado: 200)
    res_con_token = client.get(
        "/api/perfil",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    print_response("2. Acceso a /api/perfil con Bearer Token (Esperado: 200)", res_con_token)

    # 4. Acceder con token invalido / corrupto (Esperado: 422 o 401)
    res_token_invalido = client.get(
        "/api/perfil",
        headers={
            "Authorization": "Bearer token_invalido_xyz"
        }
    )
    print_response("3. Acceso con token invalido (Esperado: 422 o 401)", res_token_invalido)

    print("\n=== Pruebas de Perfil finalizadas ===")

if __name__ == "__main__":
    main()
