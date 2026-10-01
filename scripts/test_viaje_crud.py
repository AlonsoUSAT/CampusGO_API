import json
from app import create_app

def main():
    app = create_app()
    client = app.test_client()

    print("==================================================")
    print(" INICIANDO PRUEBAS DE CRUD VIAJES (SESIÓN 11)")
    print("==================================================")

    # 1. Obtener tokens
    # Conductor: Carlos Mendoza
    res = client.post("/api/auth/login", json={
        "email": "carlos.mendoza@usat.edu.pe",
        "password": "CampusGo#2026"
    })
    assert res.status_code == 200, f"Error login Carlos: {res.get_json()}"
    token_conductor = res.get_json()["data"]["token"]
    auth_conductor = {"Authorization": f"Bearer {token_conductor}"}

    # Pasajero: Juan Perez
    res = client.post("/api/auth/login", json={
        "email": "juan.perez@usat.edu.pe",
        "password": "CampusGo#2026"
    })
    assert res.status_code == 200, f"Error login Juan: {res.get_json()}"
    token_pasajero = res.get_json()["data"]["token"]
    auth_pasajero = {"Authorization": f"Bearer {token_pasajero}"}

    print("[OK] Tokens obtenidos para Conductor y Pasajero.")

    # 2. Pasajero intenta crear viaje -> 403
    trip_data = {
        "origen": "USAT",
        "destino": "Chiclayo Centro",
        "fecha": "2026-09-24",
        "hora": "18:30:00",
        "cupos": 4,
        "precio": 4.50
    }
    res = client.post("/api/viajes", json=trip_data, headers=auth_pasajero)
    assert res.status_code == 403, f"Esperado 403 para pasajero, obtenido {res.status_code}"
    print("[OK] Pasajero no puede crear viaje (403):", res.get_json()["message"])

    # 3. Conductor envía datos incompletos -> 400
    res = client.post("/api/viajes", json={"origen": "USAT"}, headers=auth_conductor)
    assert res.status_code == 400
    print("[OK] Validación datos obligatorios (400):", res.get_json()["message"])

    # 4. Conductor envía cupos inválidos -> 400
    invalid_cupos = dict(trip_data, cupos=0)
    res = client.post("/api/viajes", json=invalid_cupos, headers=auth_conductor)
    assert res.status_code == 400
    print("[OK] Validación cupos <= 0 (400):", res.get_json()["message"])

    # 5. Conductor crea viaje válido -> 201
    res = client.post("/api/viajes", json=trip_data, headers=auth_conductor)
    assert res.status_code == 201, f"Fallo al crear viaje: {res.get_json()}"
    viaje_id = res.get_json()["data"]["viaje_id"]
    print(f"[OK] Viaje creado con ID {viaje_id} (201):", res.get_json()["message"])

    # 6. Listar todos los viajes -> 200
    res = client.get("/api/viajes", headers=auth_conductor)
    assert res.status_code == 200
    viajes = res.get_json()["data"]
    assert len(viajes) > 0
    print(f"[OK] Listar todos los viajes (200): Encontrados {len(viajes)} viajes.")

    # 7. Filtrar viajes por query parameters -> 200
    res = client.get("/api/viajes?destino=Chiclayo&estado=DISPONIBLE", headers=auth_pasajero)
    assert res.status_code == 200
    filtrados = res.get_json()["data"]
    assert len(filtrados) > 0
    print(f"[OK] Filtrar viajes ?destino=Chiclayo&estado=DISPONIBLE (200): {len(filtrados)} viajes.")

    # 8. Detalle de viaje existente -> 200
    res = client.get(f"/api/viajes/{viaje_id}", headers=auth_pasajero)
    assert res.status_code == 200
    detalle = res.get_json()["data"]
    assert detalle["id"] == viaje_id
    print(f"[OK] Detalle de viaje existente (200): ID={detalle['id']}, Origen={detalle['origen']}, Destino={detalle['destino']}")

    # 9. Detalle de viaje inexistente -> 404
    res = client.get("/api/viajes/9999", headers=auth_conductor)
    assert res.status_code == 404
    print("[OK] Detalle de viaje inexistente (404):", res.get_json()["message"])

    # 10. Actualizar viaje propio -> 200
    update_data = dict(trip_data, precio=5.00, cupos=3)
    res = client.put(f"/api/viajes/{viaje_id}", json=update_data, headers=auth_conductor)
    assert res.status_code == 200
    print(f"[OK] Actualizar viaje propio (200):", res.get_json()["message"])

    # 11. Intentar actualizar sin rol CONDUCTOR -> 403
    res = client.put(f"/api/viajes/{viaje_id}", json=update_data, headers=auth_pasajero)
    assert res.status_code == 403
    print("[OK] Pasajero no puede actualizar viaje (403):", res.get_json()["message"])

    # 12. Cancelar viaje lógicamente -> 200
    res = client.delete(f"/api/viajes/{viaje_id}", headers=auth_conductor)
    assert res.status_code == 200
    print(f"[OK] Cancelar viaje (200):", res.get_json()["message"])

    # 13. Cancelar dos veces -> 409 Conflicto
    res = client.delete(f"/api/viajes/{viaje_id}", headers=auth_conductor)
    assert res.status_code == 409
    print("[OK] Cancelar viaje ya cancelado (409):", res.get_json()["message"])

    # 14. Modificar viaje cancelado -> 409 Conflicto
    res = client.put(f"/api/viajes/{viaje_id}", json=update_data, headers=auth_conductor)
    assert res.status_code == 409
    print("[OK] Modificar viaje cancelado (409):", res.get_json()["message"])

    # 15. Listar viajes propios del conductor -> 200
    res = client.get("/api/viajes/mios", headers=auth_conductor)
    assert res.status_code == 200
    print(f"[OK] Listar mis viajes (200):", len(res.get_json()["data"]), "viajes.")

    print("==================================================")
    print(" TODAS LAS PRUEBAS DE CRUD VIAJES PASARON AL 100% ")
    print("==================================================")

if __name__ == "__main__":
    main()
