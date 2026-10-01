import sys
from app import create_app
from database import get_connection
from repositories.usuario_repository import UsuarioRepository
from services.auth_service import AuthService
from services.usuario_service import UsuarioService

def test_repository():
    print("[1/5] Verificando UsuarioRepository...")
    conn = get_connection()
    try:
        repo = UsuarioRepository(conn)
        # 1. buscar_por_email existente
        u = repo.buscar_por_email("juan.perez@usat.edu.pe")
        assert u is not None, "buscar_por_email deberia encontrar al usuario"
        assert "password_hash" in u, "buscar_por_email debe incluir password_hash"
        assert u["rol"] == "PASAJERO"

        # 2. buscar_por_id
        u_id = repo.buscar_por_id(u["id"])
        assert u_id is not None, "buscar_por_id deberia encontrar al usuario"
        assert "password_hash" not in u_id, "buscar_por_id no debe exponer password_hash"
        assert "fecha_registro" in u_id, "buscar_por_id debe incluir fecha_registro"

        # 3. buscar inexistente
        assert repo.buscar_por_email("no_existe@test.com") is None
        assert repo.buscar_por_id(999999) is None
    finally:
        conn.close()
    print("      OK - UsuarioRepository cumple con todas las especificaciones.")

def test_auth_service(app):
    print("[2/5] Verificando AuthService...")
    with app.app_context():
        service = AuthService()

        # Login correcto
        data, msg, code = service.login("juan.perez@usat.edu.pe", "CampusGo#2026")
        assert code == 200, f"Esperado 200, recibido {code}"
        assert data is not None and "token" in data
        assert data["email"] == "juan.perez@usat.edu.pe"
        assert data["rol"] == "PASAJERO"

        # Clave incorrecta
        data, msg, code = service.login("juan.perez@usat.edu.pe", "ClaveErronea")
        assert code == 401, f"Esperado 401, recibido {code}"
        assert data is None

        # Email incorrecto
        data, msg, code = service.login("noexiste@usat.edu.pe", "CampusGo#2026")
        assert code == 401, f"Esperado 401, recibido {code}"
        assert data is None

        # Inactivo
        data, msg, code = service.login("inactivo@campusgo.pe", "CampusGo#2026")
        assert code == 403, f"Esperado 403, recibido {code}"
        assert data is None
    print("      OK - AuthService cumple con todas las reglas de negocio.")

def test_usuario_service(app):
    print("[3/5] Verificando UsuarioService...")
    with app.app_context():
        service = UsuarioService()

        # Perfil existente
        data, msg, code = service.obtener_perfil(1)
        assert code == 200, f"Esperado 200, recibido {code}"
        assert data["usuario_id"] == 1
        assert "password_hash" not in data
        assert "fecha_registro" in data

        # Perfil inexistente
        data, msg, code = service.obtener_perfil(999999)
        assert code == 404, f"Esperado 404, recibido {code}"
        assert data is None

        # Perfil inactivo
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM usuario WHERE estado = 'INACTIVO' LIMIT 1")
        inactivo = c.fetchone()
        c.close()
        conn.close()

        if inactivo:
            data, msg, code = service.obtener_perfil(inactivo["id"])
            assert code == 403, f"Esperado 403, recibido {code}"
            assert data is None
    print("      OK - UsuarioService cumple con las validaciones y formato de respuesta.")

def test_routes_login(client):
    print("[4/5] Verificando endpoints de Auth (/api/auth/login)...")
    # Caso 1: 200 OK
    res = client.post("/api/auth/login", json={"email": "juan.perez@usat.edu.pe", "password": "CampusGo#2026"})
    assert res.status_code == 200, f"Status: {res.status_code}"
    json_data = res.get_json()
    assert json_data["status"] is True
    assert "token" in json_data["data"]

    # Caso 2a: 400 sin JSON
    res = client.post("/api/auth/login", data="no-json", content_type="text/plain")
    assert res.status_code == 400

    # Caso 2b: 400 incompleto
    res = client.post("/api/auth/login", json={"email": "juan.perez@usat.edu.pe"})
    assert res.status_code == 400

    # Caso 3: 401 Credenciales incorrectas
    res = client.post("/api/auth/login", json={"email": "juan.perez@usat.edu.pe", "password": "bad"})
    assert res.status_code == 401
    assert res.get_json()["status"] is False

    # Caso 4: 403 Usuario inactivo
    res = client.post("/api/auth/login", json={"email": "inactivo@campusgo.pe", "password": "CampusGo#2026"})
    assert res.status_code == 403
    assert res.get_json()["status"] is False
    print("      OK - /api/auth/login responde correctamente a los 4 casos.")

def test_routes_perfil(client):
    print("[5/5] Verificando endpoints de Usuario (/api/perfil)...")
    # 1. Sin token -> 401
    res = client.get("/api/perfil")
    assert res.status_code == 401, f"Status: {res.status_code}"

    # 2. Con login previo
    login_res = client.post("/api/auth/login", json={"email": "juan.perez@usat.edu.pe", "password": "CampusGo#2026"})
    token = login_res.get_json()["data"]["token"]

    res = client.get("/api/perfil", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200, f"Status: {res.status_code}"
    body = res.get_json()
    assert body["status"] is True
    assert body["data"]["email"] == "juan.perez@usat.edu.pe"
    assert "password_hash" not in body["data"]
    assert "fecha_registro" in body["data"]

    # 3. Token malformado -> 422
    res_bad = client.get("/api/perfil", headers={"Authorization": "Bearer fake_token"})
    assert res_bad.status_code in (401, 422)
    print("      OK - /api/perfil protegido y validado correctamente.")

def test_viajes_crud(client):
    print("[6/6] Verificando endpoints de Viajes (CRUD completo Sesión 11)...")
    # Login Conductor
    res = client.post("/api/auth/login", json={"email": "carlos.mendoza@usat.edu.pe", "password": "CampusGo#2026"})
    token_c = res.get_json()["data"]["token"]
    h_c = {"Authorization": f"Bearer {token_c}"}

    # Login Pasajero
    res = client.post("/api/auth/login", json={"email": "juan.perez@usat.edu.pe", "password": "CampusGo#2026"})
    token_p = res.get_json()["data"]["token"]
    h_p = {"Authorization": f"Bearer {token_p}"}

    # 1. Pasajero intenta crear -> 403
    t_data = {"origen": "USAT", "destino": "Chiclayo Centro", "fecha": "2026-09-24", "hora": "18:30:00", "cupos": 4, "precio": 4.50}
    res = client.post("/api/viajes", json=t_data, headers=h_p)
    assert res.status_code == 403

    # 2. Conductor crea viaje -> 201
    res = client.post("/api/viajes", json=t_data, headers=h_c)
    assert res.status_code == 201
    v_id = res.get_json()["data"]["viaje_id"]

    # 3. Listar viajes -> 200
    res = client.get("/api/viajes", headers=h_p)
    assert res.status_code == 200

    # 4. Filtrar viajes -> 200
    res = client.get("/api/viajes?destino=Chiclayo&estado=DISPONIBLE", headers=h_p)
    assert res.status_code == 200

    # 5. Detalle existente -> 200
    res = client.get(f"/api/viajes/{v_id}", headers=h_p)
    assert res.status_code == 200

    # 6. Detalle inexistente -> 404
    res = client.get("/api/viajes/9999", headers=h_c)
    assert res.status_code == 404

    # 7. Actualizar viaje propio -> 200
    res = client.put(f"/api/viajes/{v_id}", json=dict(t_data, cupos=2), headers=h_c)
    assert res.status_code == 200

    # 8. Cancelar viaje -> 200
    res = client.delete(f"/api/viajes/{v_id}", headers=h_c)
    assert res.status_code == 200

    # 9. Cancelar de nuevo -> 409
    res = client.delete(f"/api/viajes/{v_id}", headers=h_c)
    assert res.status_code == 409
    print("      OK - Operaciones CRUD de Viajes cumplen todas las reglas y códigos HTTP.")

def main():
    print("==================================================")
    print(" VERIFICACION INTEGRAL DE REQUISITOS DEL LABORATORIO ")
    print("==================================================")
    app = create_app()
    client = app.test_client()

    test_repository()
    test_auth_service(app)
    test_usuario_service(app)
    test_routes_login(client)
    test_routes_perfil(client)
    test_viajes_crud(client)

    print("==================================================")
    print(" TODAS LAS COMPROBACIONES SE HAN CUMPLIDO AL 100% ")
    print("==================================================")

if __name__ == "__main__":
    main()
