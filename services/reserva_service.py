from datetime import datetime, timedelta, time
from database import get_connection
from repositories.reserva_repository import ReservaRepository


def _combinar_fecha_hora(fecha, hora):
    """
    Convierte de forma segura fecha y hora (timedelta o time de MySQL)
    a un objeto datetime.datetime para validar el orden cronológico.
    """
    if isinstance(hora, timedelta):
        return datetime.combine(fecha, time.min) + hora
    elif isinstance(hora, time):
        return datetime.combine(fecha, hora)
    elif isinstance(hora, str):
        t = datetime.strptime(hora, "%H:%M:%S").time()
        return datetime.combine(fecha, t)
    return datetime.combine(fecha, time.min)


class ReservaService:
    def crear(self, usuario_id, datos):
        """
        Registra una reserva atómica con 1 o 2 viajes (ida y opcional retorno).
        Garantiza consistencia mediante SELECT ... FOR UPDATE y transacciones (BEGIN/COMMIT/ROLLBACK).
        """
        viajes = datos.get("viajes", [])
        if not isinstance(viajes, list) or len(viajes) not in (1, 2):
            return None, "Debe seleccionar uno o dos viajes", 400

        ids = [v.get("viaje_id") for v in viajes if isinstance(v, dict)]
        if None in ids or len(ids) != len(viajes) or len(ids) != len(set(ids)):
            return None, "Los viajes son inválidos o están repetidos", 400

        connection = get_connection()
        try:
            connection.begin()
            repository = ReservaRepository(connection)

            pasajero_id = repository.obtener_pasajero_id_por_usuario(usuario_id)
            if pasajero_id is None:
                connection.rollback()
                return None, "El usuario no posee perfil de pasajero", 403

            viajes_bd = []
            for item in viajes:
                try:
                    cantidad = int(item.get("cantidad", 0))
                except (ValueError, TypeError):
                    connection.rollback()
                    return None, "Datos de tramo inválidos", 400

                tipo = item.get("tipo_tramo")
                if cantidad <= 0 or tipo not in ("IDA", "RETORNO"):
                    connection.rollback()
                    return None, "Datos de tramo inválidos", 400

                # Bloqueo atómico con SELECT ... FOR UPDATE
                viaje = repository.obtener_viaje_para_actualizar(item["viaje_id"])

                if viaje is None:
                    connection.rollback()
                    return None, "Uno de los viajes no existe", 404

                if viaje["estado"] != "DISPONIBLE":
                    connection.rollback()
                    return None, "Uno de los viajes no está disponible", 409

                if viaje["cupos"] < cantidad:
                    connection.rollback()
                    return None, "No existen cupos suficientes", 409

                if str(viaje["conductor_usuario_id"]) == str(usuario_id):
                    connection.rollback()
                    return None, "No puede reservar su propio viaje", 409

                viajes_bd.append((item, viaje))

            # Validación de orden ida -> retorno
            if len(viajes_bd) == 2:
                tipos = {item["tipo_tramo"] for item, _ in viajes_bd}
                if tipos != {"IDA", "RETORNO"}:
                    connection.rollback()
                    return None, "Debe seleccionar IDA y RETORNO", 400

                ida = next(
                    (item, v) for item, v in viajes_bd
                    if item["tipo_tramo"] == "IDA"
                )
                retorno = next(
                    (item, v) for item, v in viajes_bd
                    if item["tipo_tramo"] == "RETORNO"
                )

                fecha_ida = _combinar_fecha_hora(
                    ida[1]["fecha"],
                    ida[1]["hora"]
                )
                fecha_retorno = _combinar_fecha_hora(
                    retorno[1]["fecha"],
                    retorno[1]["hora"]
                )

                if fecha_retorno <= fecha_ida:
                    connection.rollback()
                    return None, "El retorno debe ser posterior a la ida", 409

            # 1. Crear cabecera de reserva
            reserva_id = repository.crear_reserva(pasajero_id)

            # 2. Crear detalles y descontar cupos atómicamente
            orden = 1
            for item, viaje in viajes_bd:
                repository.crear_detalle(
                    reserva_id,
                    item["viaje_id"],
                    int(item["cantidad"]),
                    item["tipo_tramo"],
                    orden
                )
                repository.descontar_cupos(
                    item["viaje_id"],
                    int(item["cantidad"])
                )
                orden += 1

            connection.commit()
            return {
                "reserva_id": reserva_id
            }, "Reserva registrada correctamente", 201

        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def cancelar(self, usuario_id, reserva_id):
        """
        Extensión opcional - Cancelación transaccional:
        DELETE /api/reservas/{id}

        BEGIN
          bloquear reserva y detalles
          UPDATE reserva -> CANCELADA
          UPDATE reserva_viaje -> CANCELADA
          devolver cupos a viaje IDA
          devolver cupos a viaje RETORNO
        COMMIT

        si algo falla:
          ROLLBACK
        """
        connection = get_connection()
        try:
            # BEGIN
            connection.begin()
            repository = ReservaRepository(connection)

            # 1. Bloquear y validar la reserva
            reserva = repository.obtener_reserva_para_actualizar(reserva_id)
            if reserva is None:
                connection.rollback()
                return None, "Reserva no encontrada", 404

            if str(reserva["pasajero_usuario_id"]) != str(usuario_id):
                connection.rollback()
                return None, "No puede cancelar una reserva ajena", 403

            if reserva["estado"] == "CANCELADA":
                connection.rollback()
                return None, "La reserva ya se encuentra cancelada", 409

            # 2. Bloquear detalles de la reserva (SELECT ... FOR UPDATE)
            detalles = repository.obtener_detalles_reserva(reserva_id)

            # 3. Bloquear filas de los viajes involucrados (IDA y RETORNO)
            for d in detalles:
                repository.obtener_viaje_para_actualizar(d["viaje_id"])

            # 4. UPDATE reserva -> CANCELADA
            repository.cancelar_reserva(reserva_id)

            # 5. UPDATE reserva_viaje -> CANCELADA
            repository.cancelar_detalles_reserva(reserva_id)

            # 6. Devolver cupos a viaje IDA y viaje RETORNO
            for d in detalles:
                if d["estado"] != "CANCELADA":
                    repository.devolver_cupos(d["viaje_id"], d["cantidad"])

            # COMMIT
            connection.commit()
            return {
                "reserva_id": reserva_id
            }, "Reserva cancelada correctamente y cupos devueltos a los viajes", 200

        except Exception:
            # Si algo falla: ROLLBACK
            connection.rollback()
            raise
        finally:
            connection.close()
