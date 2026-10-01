import json
from app import create_app

def main():
    app = create_app()
    client = app.test_client()

    print("==========================================================")
    print(" INICIANDO PRUEBAS DEL BANCO DE EJERCICIOS (SESIÓN 11) ")
    print("==========================================================")

    # 1. Login Conductor y Pasajero
    res = client.post("/api/auth/login", json={"email": "carlos.mendoza@usat.edu.pe", "password": "CampusGo#2026"})
    assert res.status_code == 200
    token_c = res.get_json()["data"]["token"]
    h_c = {"Authorization": f"Bearer {token_c}"}

    res = client.post("/api/auth/login", json={"email": "juan.perez@usat.edu.pe", "password": "CampusGo#2026"})
    assert res.status_code == 200
    token_p = res.get_json()["data"]["token"]
    h_p = {"Authorization": f"Bearer {token_p}"}

    # Crear un viaje base para las pruebas con hora única
    viaje_base = {
        "origen": "Terminal Chiclayo",
        "destino": "Campus USAT",
        "fecha": "2026-10-15",
        "hora": "07:15:00",
        "cupos": 4,
        "precio": 3.50
    }
    res = client.post("/api/viajes", json=viaje_base, headers=h_c)
    if res.status_code == 201:
        v_id = res.get_json()["data"]["viaje_id"]
    else:
        # Si ya existía, obtenemos uno existente
        res_list = client.get("/api/viajes/mios?estado=DISPONIBLE", headers=h_c)
        viajes = res_list.get_json()["data"]
        v_id = viajes[0]["id"] if viajes else 1

    print(f"[PREPARACIÓN] Viaje activo para pruebas ID: {v_id}")

    # ========================================================
    # EJERCICIO 1: Filtrar por rango de precio
    # ========================================================
    print("\n--- EJERCICIO 1: Rango de precio ---")
    # Caso correcto
    res = client.get("/api/viajes?precio_min=1.00&precio_max=10.00", headers=h_c)
    assert res.status_code == 200
    print("  [OK] Caso correcto (200): Filtrado por precio_min y precio_max.")

    # Caso error 1: No numérico
    res = client.get("/api/viajes?precio_min=caro", headers=h_c)
    assert res.status_code == 400
    print("  [OK] Caso error (400): Parámetro no numérico rechazado.")

    # Caso error 2: min > max
    res = client.get("/api/viajes?precio_min=10.00&precio_max=2.00", headers=h_c)
    assert res.status_code == 400
    print("  [OK] Caso error (400): precio_min > precio_max rechazado.")

    # ========================================================
    # EJERCICIO 2: Mostrar únicamente viajes con cupos disponibles
    # ========================================================
    print("\n--- EJERCICIO 2: solo_disponibles=true ---")
    res = client.get("/api/viajes?solo_disponibles=true", headers=h_c)
    assert res.status_code == 200
    for v in res.get_json()["data"]:
        assert v["cupos"] > 0
        assert v["estado"] == "DISPONIBLE"
    print("  [OK] Caso correcto (200): Solo devuelve viajes con cupos > 0 y estado DISPONIBLE.")

    # ========================================================
    # EJERCICIO 3: Consultar viajes por fecha mínima / rango
    # ========================================================
    print("\n--- EJERCICIO 3: Fechas desde / hasta ---")
    # Caso correcto
    res = client.get("/api/viajes?desde=2026-01-01&hasta=2026-12-31", headers=h_c)
    assert res.status_code == 200
    print("  [OK] Caso correcto (200): Filtrado por rango desde y hasta.")

    # Caso error: Formato inválido
    res = client.get("/api/viajes?desde=15-10-2026", headers=h_c)
    assert res.status_code == 400
    print("  [OK] Caso error (400): Formato inválido de fecha rechazado.")

    # ========================================================
    # EJERCICIO 4: Consultar mis viajes con filtro opcional de estado
    # ========================================================
    print("\n--- EJERCICIO 4: GET /api/viajes/mios ---")
    res = client.get("/api/viajes/mios?estado=DISPONIBLE", headers=h_c)
    assert res.status_code == 200
    print("  [OK] Caso correcto (200): Mis viajes filtrados por estado DISPONIBLE.")

    res = client.get("/api/viajes/mios", headers=h_p)
    assert res.status_code == 403
    print("  [OK] Caso error (403): Pasajero no puede consultar mis viajes de conductor.")

    # ========================================================
    # EJERCICIO 5: Actualizar solamente los cupos
    # ========================================================
    print("\n--- EJERCICIO 5: PATCH /api/viajes/{id}/cupos ---")
    # Caso correcto
    res = client.patch(f"/api/viajes/{v_id}/cupos", json={"cupos": 2}, headers=h_c)
    assert res.status_code == 200
    assert res.get_json()["data"]["cupos"] == 2
    print("  [OK] Caso correcto (200): Cupos actualizados a 2.")

    # Caso error: Cupos negativos
    res = client.patch(f"/api/viajes/{v_id}/cupos", json={"cupos": -1}, headers=h_c)
    assert res.status_code == 400
    print("  [OK] Caso error (400): Cupos negativos rechazados.")

    # ========================================================
    # EJERCICIO 6: Cambiar el estado de un viaje
    # ========================================================
    print("\n--- EJERCICIO 6: PATCH /api/viajes/{id}/estado ---")
    # Caso correcto
    res = client.patch(f"/api/viajes/{v_id}/estado", json={"estado": "COMPLETO"}, headers=h_c)
    assert res.status_code == 200
    print("  [OK] Caso correcto (200): Estado cambiado a COMPLETO.")

    # Caso error 1: Estado inválido
    res = client.patch(f"/api/viajes/{v_id}/estado", json={"estado": "INEXISTENTE"}, headers=h_c)
    assert res.status_code == 400
    print("  [OK] Caso error (400): Estado no permitido rechazado.")

    # Caso error 2: Conflicto mismo estado (409)
    res = client.patch(f"/api/viajes/{v_id}/estado", json={"estado": "COMPLETO"}, headers=h_c)
    assert res.status_code == 409
    print("  [OK] Caso error (409): Transición al mismo estado rechazada con 409.")

    # ========================================================
    # EJERCICIO 7: Evitar viajes duplicados
    # ========================================================
    print("\n--- EJERCICIO 7: Evitar viajes duplicados ---")
    duplicado_data = {
        "origen": "Lambayeque Centro",
        "destino": "USAT Chiclayo",
        "fecha": "2026-11-20",
        "hora": "08:00:00",
        "cupos": 3,
        "precio": 4.00
    }
    # 1era vez: Debe crearse (201) o ya existir
    res1 = client.post("/api/viajes", json=duplicado_data, headers=h_c)
    # 2da vez: Mismos datos -> Debe responder 409 Conflict
    res2 = client.post("/api/viajes", json=duplicado_data, headers=h_c)
    assert res2.status_code == 409
    print("  [OK] Caso conflicto (409): Viaje duplicado rechazado correctamente.")

    # ========================================================
    # EJERCICIO 8: Detalle enriquecido con JOIN
    # ========================================================
    print("\n--- EJERCICIO 8: GET /api/viajes/{id} con JOIN enriquecido ---")
    res = client.get(f"/api/viajes/{v_id}", headers=h_p)
    assert res.status_code == 200
    det = res.get_json()["data"]
    assert "conductor" in det
    assert "conductor_calificacion" in det
    assert "conductor_licencia" in det
    print(f"  [OK] Caso correcto (200): Detalle incluye Conductor: '{det['conductor']}', Licencia: '{det['conductor_licencia']}'.")

    # ========================================================
    # EJERCICIO 9: Cancelar un viaje con restricciones
    # ========================================================
    print("\n--- EJERCICIO 9: DELETE /api/viajes/{id} con restricciones ---")
    res = client.delete(f"/api/viajes/{v_id}", headers=h_c)
    assert res.status_code == 200
    print("  [OK] Caso correcto (200): Cancelación lógica exitosa.")

    # Cancelar de nuevo -> 409
    res = client.delete(f"/api/viajes/{v_id}", headers=h_c)
    assert res.status_code == 409
    print("  [OK] Caso conflicto (409): Viaje ya cancelado rechazado con 409.")

    # ========================================================
    # EJERCICIO 10: Reporte de viajes agrupados por estado (GROUP BY)
    # ========================================================
    print("\n--- EJERCICIO 10: GET /api/viajes/resumen (GROUP BY) ---")
    res = client.get("/api/viajes/resumen", headers=h_c)
    assert res.status_code == 200
    rep = res.get_json()["data"]
    assert "resumen" in rep
    assert "total_general" in rep
    print(f"  [OK] Caso correcto (200): Reporte generado con {len(rep['resumen'])} estados. Total: {rep['total_general']}.")

    print("\n==========================================================")
    print(" ¡LOS 10 EJERCICIOS DEL BANCO HAN SIDO PROBADOS Y APROBADOS! ")
    print("==========================================================")

if __name__ == "__main__":
    main()
