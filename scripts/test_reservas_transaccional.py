import json
from app import create_app
from database import get_connection

def main():
    app = create_app()
    client = app.test_client()

    print("==========================================================")
    print(" INICIANDO PRUEBAS DE RESERVA TRANSACCIONAL (SESIÓN 12) ")
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

    # 2. Crear dos viajes nuevos para pruebas: uno de IDA y uno de RETORNO
    viaje_ida_data = {
        "origen": "Chiclayo Centro",
        "destino": "Campus USAT",
        "fecha": "2026-12-01",
        "hora": "07:30:00",
        "cupos": 3,
        "precio": 3.00
    }
    viaje_retorno_data = {
        "origen": "Campus USAT",
        "destino": "Chiclayo Centro",
        "fecha": "2026-12-01",
        "hora": "14:00:00",
        "cupos": 2,
        "precio": 3.00
    }

    res_ida = client.post("/api/viajes", json=viaje_ida_data, headers=h_c)
    if res_ida.status_code == 201:
        id_ida = res_ida.get_json()["data"]["viaje_id"]
    else:
        # Si ya existe por test anterior, buscamos su ID
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM viaje WHERE origen='Chiclayo Centro' AND destino='Campus USAT' AND fecha='2026-12-01'")
        id_ida = c.fetchone()["id"]
        c.execute("UPDATE viaje SET cupos = 3, estado = 'DISPONIBLE' WHERE id = %s", (id_ida,))
        conn.commit()
        c.close()
        conn.close()

    res_ret = client.post("/api/viajes", json=viaje_retorno_data, headers=h_c)
    if res_ret.status_code == 201:
        id_ret = res_ret.get_json()["data"]["viaje_id"]
    else:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM viaje WHERE origen='Campus USAT' AND destino='Chiclayo Centro' AND fecha='2026-12-01'")
        id_ret = c.fetchone()["id"]
        c.execute("UPDATE viaje SET cupos = 2, estado = 'DISPONIBLE' WHERE id = %s", (id_ret,))
        conn.commit()
        c.close()
        conn.close()

    print(f"[PREPARACIÓN] Viaje IDA ID={id_ida} (cupos=3), Viaje RETORNO ID={id_ret} (cupos=2)")

    # 3. Caso 1: Reserva de IDA (1 viaje) -> 201 Created
    print("\n--- CASO 1: Reserva de 1 viaje (IDA) ---")
    body_1 = {
        "viajes": [
            {"viaje_id": id_ida, "cantidad": 1, "tipo_tramo": "IDA"}
        ]
    }
    res = client.post("/api/reservas", json=body_1, headers=h_p)
    assert res.status_code == 201, f"Error: {res.get_json()}"
    reserva_1_id = res.get_json()["data"]["reserva_id"]
    print(f"  [OK] Reserva de IDA creada con ID={reserva_1_id} (201 Created).")

    # Verificar que los cupos bajaron a 2
    res_det = client.get(f"/api/viajes/{id_ida}", headers=h_p)
    assert res_det.get_json()["data"]["cupos"] == 2
    print("  [OK] Cupos de IDA actualizados correctamente a 2.")

    # 4. Caso 2: Reserva IDA + RETORNO válida -> 201 Created
    print("\n--- CASO 2: Reserva IDA + RETORNO ---")
    body_2 = {
        "viajes": [
            {"viaje_id": id_ida, "cantidad": 1, "tipo_tramo": "IDA"},
            {"viaje_id": id_ret, "cantidad": 1, "tipo_tramo": "RETORNO"}
        ]
    }
    res = client.post("/api/reservas", json=body_2, headers=h_p)
    assert res.status_code == 201, f"Error: {res.get_json()}"
    reserva_2_id = res.get_json()["data"]["reserva_id"]
    print(f"  [OK] Reserva IDA + RETORNO creada con ID={reserva_2_id} (201 Created).")

    # 5. Caso 3: VERIFICACIÓN DIRECTA DE ATOMICIDAD (ROLLBACK POR FALTA DE CUPOS)
    print("\n--- CASO 3: Verificación de Atomicidad (ROLLBACK) ---")
    # Antes: IDA tiene cupos=1, RETORNO tiene cupos=1
    res_ida_antes = client.get(f"/api/viajes/{id_ida}", headers=h_p).get_json()["data"]["cupos"]
    res_ret_antes = client.get(f"/api/viajes/{id_ret}", headers=h_p).get_json()["data"]["cupos"]
    print(f"  [ANTES] IDA cupos={res_ida_antes}, RETORNO cupos={res_ret_antes}")

    # Intentamos reservar IDA (1 cupo) y RETORNO (pidiendo 99 cupos -> fallará por falta de cupos)
    body_fallo = {
        "viajes": [
            {"viaje_id": id_ida, "cantidad": 1, "tipo_tramo": "IDA"},
            {"viaje_id": id_ret, "cantidad": 99, "tipo_tramo": "RETORNO"}
        ]
    }
    res = client.post("/api/reservas", json=body_fallo, headers=h_p)
    assert res.status_code == 409, f"Esperado 409, recibido {res.status_code}"
    print(f"  [OK] Transacción rechazada con 409: {res.get_json()['message']}")

    # DESPUÉS: Verificar que los cupos de IDA siguen intactos (no se descontó nada)
    res_ida_despues = client.get(f"/api/viajes/{id_ida}", headers=h_p).get_json()["data"]["cupos"]
    res_ret_despues = client.get(f"/api/viajes/{id_ret}", headers=h_p).get_json()["data"]["cupos"]
    assert res_ida_despues == res_ida_antes, "¡FALLO DE ATOMICIDAD! Cupos de IDA cambiaron a pesar del error"
    assert res_ret_despues == res_ret_antes, "¡FALLO DE ATOMICIDAD! Cupos de RETORNO cambiaron"
    print(f"  [DESPUÉS] IDA cupos={res_ida_despues}, RETORNO cupos={res_ret_despues}")
    print("  [OK] ¡Atomicidad garantizada! Se ejecutó ROLLBACK completo.")

    # 6. Caso 4: Retorno anterior a la ida -> 409 Conflict
    print("\n--- CASO 4: Retorno anterior a la IDA ---")
    # Creamos un retorno antes de la ida
    viaje_retorno_ayer = {
        "origen": "Campus USAT",
        "destino": "Chiclayo Centro",
        "fecha": "2026-11-30", # Anterior al 1 de dic
        "hora": "12:00:00",
        "cupos": 2,
        "precio": 3.00
    }
    res_ret_ayer = client.post("/api/viajes", json=viaje_retorno_ayer, headers=h_c)
    if res_ret_ayer.status_code == 201:
        id_ret_ayer = res_ret_ayer.get_json()["data"]["viaje_id"]
    else:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM viaje WHERE origen='Campus USAT' AND fecha='2026-11-30'")
        id_ret_ayer = c.fetchone()["id"]
        c.close()
        conn.close()

    body_incoherente = {
        "viajes": [
            {"viaje_id": id_ida, "cantidad": 1, "tipo_tramo": "IDA"},
            {"viaje_id": id_ret_ayer, "cantidad": 1, "tipo_tramo": "RETORNO"}
        ]
    }
    res = client.post("/api/reservas", json=body_incoherente, headers=h_p)
    assert res.status_code == 409
    print(f"  [OK] Retorno anterior rechazado con 409: {res.get_json()['message']}")

    # 7. Caso 5: Viaje inexistente -> 404 Not Found
    print("\n--- CASO 5: Viaje inexistente ---")
    body_inexistente = {
        "viajes": [
            {"viaje_id": 99999, "cantidad": 1, "tipo_tramo": "IDA"}
        ]
    }
    res = client.post("/api/reservas", json=body_inexistente, headers=h_p)
    assert res.status_code == 404
    print(f"  [OK] Viaje inexistente rechazado con 404: {res.get_json()['message']}")

    # 8. Caso 6: Mismo viaje repetido -> 400 Bad Request
    print("\n--- CASO 6: Viaje repetido ---")
    body_repetido = {
        "viajes": [
            {"viaje_id": id_ida, "cantidad": 1, "tipo_tramo": "IDA"},
            {"viaje_id": id_ida, "cantidad": 1, "tipo_tramo": "RETORNO"}
        ]
    }
    res = client.post("/api/reservas", json=body_repetido, headers=h_p)
    assert res.status_code == 400
    print(f"  [OK] Viaje repetido rechazado con 400: {res.get_json()['message']}")

    # 9. Caso 7: Sin rol PASAJERO -> 403 Forbidden
    print("\n--- CASO 7: Conductor intentando reservar ---")
    res = client.post("/api/reservas", json=body_1, headers=h_c)
    assert res.status_code == 403
    print(f"  [OK] Conductor rechazado con 403: {res.get_json()['message']}")

    # 10. Caso 8: Extensión Opcional - Cancelar Reserva (restitución de cupos)
    print("\n--- CASO 8: Extensión Opcional - Cancelación Transaccional ---")
    cupos_antes_cancel = client.get(f"/api/viajes/{id_ida}", headers=h_p).get_json()["data"]["cupos"]
    res_cancel = client.delete(f"/api/reservas/{reserva_1_id}", headers=h_p)
    assert res_cancel.status_code == 200
    cupos_despues_cancel = client.get(f"/api/viajes/{id_ida}", headers=h_p).get_json()["data"]["cupos"]
    assert cupos_despues_cancel == cupos_antes_cancel + 1
    print(f"  [OK] Reserva {reserva_1_id} cancelada (200). Cupos devueltos al viaje: {cupos_antes_cancel} -> {cupos_despues_cancel}")

    print("\n==========================================================")
    print(" ¡TODAS LAS PRUEBAS DE LA SESIÓN 12 PASARON CON ÉXITO! ")
    print("==========================================================")

if __name__ == "__main__":
    main()
