from datetime import datetime
from database import get_connection
from repositories.viaje_repository import ViajeRepository


class ViajeService:
    def crear(self, usuario_id, datos):
        """Ejercicio 7: Crear viaje validando que no existan duplicados."""
        obligatorios = ["origen", "destino", "fecha", "hora", "cupos", "precio"]
        if any(campo not in datos for campo in obligatorios):
            return None, "Faltan datos obligatorios", 400

        try:
            cupos = int(datos["cupos"])
            if cupos <= 0:
                return None, "Los cupos deben ser mayores que cero", 400
        except (ValueError, TypeError):
            return None, "Los cupos deben ser un número entero mayor que cero", 400

        try:
            precio = float(datos["precio"])
            if precio < 0:
                return None, "El precio no puede ser negativo", 400
        except (ValueError, TypeError):
            return None, "El precio debe ser un número válido", 400

        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            conductor_id = repository.obtener_conductor_id_por_usuario(usuario_id)
            if conductor_id is None:
                return None, "El usuario no posee perfil de conductor", 403

            # Regla de negocio Ejercicio 7: Evitar duplicados
            if repository.existe_viaje_duplicado(
                conductor_id,
                datos["origen"],
                datos["destino"],
                datos["fecha"],
                datos["hora"]
            ):
                return None, "Ya existe un viaje registrado para el mismo origen, destino, fecha y hora", 409

            viaje_id = repository.crear(conductor_id, datos)
            connection.commit()
            return {"viaje_id": viaje_id}, "Viaje creado correctamente", 201
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def listar(self, filtros):
        """
        Ejercicios 1, 2 y 3: Listar con validaciones de rango de precio,
        cupos disponibles y rango de fechas.
        """
        # Validación Ejercicio 1: Rango de precio
        precio_min = filtros.get("precio_min")
        precio_max = filtros.get("precio_max")

        if precio_min is not None and str(precio_min).strip() != "":
            try:
                precio_min = float(precio_min)
                if precio_min < 0:
                    return None, "El precio mínimo no puede ser negativo", 400
            except ValueError:
                return None, "El parámetro precio_min debe ser numérico", 400
        else:
            precio_min = None

        if precio_max is not None and str(precio_max).strip() != "":
            try:
                precio_max = float(precio_max)
                if precio_max < 0:
                    return None, "El precio máximo no puede ser negativo", 400
            except ValueError:
                return None, "El parámetro precio_max debe ser numérico", 400
        else:
            precio_max = None

        if precio_min is not None and precio_max is not None:
            if precio_min > precio_max:
                return None, "precio_min debe ser menor o igual que precio_max", 400

        # Validación Ejercicio 2: Solo disponibles
        solo_disponibles_raw = str(filtros.get("solo_disponibles", "")).strip().lower()
        solo_disponibles = solo_disponibles_raw in ("true", "1", "yes")

        # Validación Ejercicio 3: Fechas (desde / hasta)
        desde = filtros.get("desde")
        hasta = filtros.get("hasta")

        if desde and str(desde).strip() != "":
            try:
                datetime.strptime(str(desde).strip(), "%Y-%m-%d")
                desde = str(desde).strip()
            except ValueError:
                return None, "El parámetro 'desde' debe tener formato YYYY-MM-DD", 400
        else:
            desde = None

        if hasta and str(hasta).strip() != "":
            try:
                datetime.strptime(str(hasta).strip(), "%Y-%m-%d")
                hasta = str(hasta).strip()
            except ValueError:
                return None, "El parámetro 'hasta' debe tener formato YYYY-MM-DD", 400
        else:
            hasta = None

        if desde and hasta and desde > hasta:
            return None, "La fecha 'desde' debe ser anterior o igual a la fecha 'hasta'", 400

        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viajes = repository.listar(
                origen=filtros.get("origen"),
                destino=filtros.get("destino"),
                fecha=filtros.get("fecha"),
                estado=filtros.get("estado"),
                precio_min=precio_min,
                precio_max=precio_max,
                solo_disponibles=solo_disponibles,
                desde=desde,
                hasta=hasta
            )
            return viajes, "Viajes obtenidos correctamente", 200
        finally:
            connection.close()

    def listar_mios(self, usuario_id, estado=None):
        """Ejercicio 4: Consultar mis viajes publicados con filtro opcional de estado."""
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            conductor_id = repository.obtener_conductor_id_por_usuario(usuario_id)
            if conductor_id is None:
                return None, "El usuario no posee perfil de conductor", 403

            viajes = repository.listar_por_conductor(conductor_id, estado=estado)
            return viajes, "Viajes del conductor obtenidos correctamente", 200
        finally:
            connection.close()

    def obtener(self, viaje_id):
        """Ejercicio 8: Detalle enriquecido de un viaje con datos de conductor."""
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)
            if viaje is None:
                return None, "Viaje no encontrado", 404
            return viaje, "Viaje obtenido correctamente", 200
        finally:
            connection.close()

    def actualizar(self, usuario_id, viaje_id, datos):
        obligatorios = ["origen", "destino", "fecha", "hora", "cupos", "precio"]
        if any(campo not in datos for campo in obligatorios):
            return None, "Faltan datos obligatorios", 400

        try:
            cupos = int(datos["cupos"])
            if cupos <= 0:
                return None, "Los cupos deben ser mayores que cero", 400
        except (ValueError, TypeError):
            return None, "Los cupos deben ser mayores que cero", 400

        try:
            precio = float(datos["precio"])
            if precio < 0:
                return None, "El precio no puede ser negativo", 400
        except (ValueError, TypeError):
            return None, "El precio no puede ser negativo", 400

        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)
            if viaje is None:
                return None, "Viaje no encontrado", 404
            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede modificar un viaje de otro conductor", 403
            if viaje["estado"] in ("FINALIZADO", "CANCELADO"):
                return None, "El estado actual no permite modificar el viaje", 409

            repository.actualizar(viaje_id, datos)
            connection.commit()
            return {"viaje_id": viaje_id}, "Viaje actualizado correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def actualizar_cupos(self, usuario_id, viaje_id, datos):
        """Ejercicio 5: Actualizar únicamente los cupos de un viaje."""
        if not isinstance(datos, dict) or "cupos" not in datos:
            return None, "Debe enviar el campo 'cupos'", 400

        try:
            nuevos_cupos = int(datos["cupos"])
            if nuevos_cupos < 0:
                return None, "Los cupos no pueden ser negativos", 400
        except (ValueError, TypeError):
            return None, "Los cupos deben ser un número entero válido", 400

        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)
            if viaje is None:
                return None, "Viaje no encontrado", 404
            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede modificar un viaje de otro conductor", 403
            if viaje["estado"] in ("FINALIZADO", "CANCELADO"):
                return None, "El estado actual no permite modificar los cupos", 409

            repository.actualizar_cupos(viaje_id, nuevos_cupos)
            connection.commit()
            return {
                "viaje_id": viaje_id,
                "cupos": nuevos_cupos
            }, "Cupos actualizados correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def cambiar_estado(self, usuario_id, viaje_id, datos):
        """Ejercicio 6: Cambiar el estado de un viaje controlando transiciones coherentes."""
        if not isinstance(datos, dict) or "estado" not in datos:
            return None, "Debe enviar el campo 'estado'", 400

        nuevo_estado = str(datos["estado"]).strip().upper()
        estados_permitidos = ["DISPONIBLE", "COMPLETO", "FINALIZADO", "CANCELADO"]
        if nuevo_estado not in estados_permitidos:
            return None, f"Estado inválido. Permitidos: {', '.join(estados_permitidos)}", 400

        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)
            if viaje is None:
                return None, "Viaje no encontrado", 404
            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede modificar el estado de un viaje ajeno", 403

            estado_actual = viaje["estado"]

            # Reglas de negocio de transiciones (409 Conflict)
            if estado_actual == nuevo_estado:
                return None, f"El viaje ya se encuentra en estado '{nuevo_estado}'", 409

            if estado_actual == "CANCELADO":
                return None, "Un viaje cancelado no puede modificar su estado", 409

            if estado_actual == "FINALIZADO":
                return None, "Un viaje finalizado no puede modificar su estado", 409

            repository.cambiar_estado(viaje_id, nuevo_estado)
            connection.commit()
            return {
                "viaje_id": viaje_id,
                "estado_anterior": estado_actual,
                "estado_nuevo": nuevo_estado
            }, "Estado actualizado correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def cancelar(self, usuario_id, viaje_id):
        """Ejercicio 9: Cancelación lógica con restricciones."""
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)
            if viaje is None:
                return None, "Viaje no encontrado", 404
            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede cancelar un viaje de otro conductor", 403
            if viaje["estado"] == "CANCELADO":
                return None, "El viaje ya se encuentra cancelado", 409
            if viaje["estado"] == "FINALIZADO":
                return None, "No se puede cancelar un viaje finalizado", 409

            repository.cancelar(viaje_id)
            connection.commit()
            return {"viaje_id": viaje_id}, "Viaje cancelado correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def resumen_por_estado(self, usuario_id):
        """Ejercicio 10: Reporte de viajes agrupados por estado en SQL."""
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            conductor_id = repository.obtener_conductor_id_por_usuario(usuario_id)
            if conductor_id is None:
                return None, "El usuario no posee perfil de conductor", 403

            filas = repository.resumen_por_estado(conductor_id)
            total_general = sum(f["total"] for f in filas)
            data = {
                "resumen": filas,
                "total_general": total_general
            }
            return data, "Resumen obtenido correctamente", 200
        finally:
            connection.close()
