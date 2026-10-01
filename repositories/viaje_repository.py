class ViajeRepository:
    def __init__(self, connection):
        self.connection = connection

    def obtener_conductor_id_por_usuario(self, usuario_id):
        cursor = self.connection.cursor()
        try:
            sql = "SELECT id FROM conductor WHERE usuario_id = %s"
            cursor.execute(sql, (usuario_id,))
            fila = cursor.fetchone()
            return fila["id"] if fila else None
        finally:
            cursor.close()

    def existe_viaje_duplicado(self, conductor_id, origen, destino, fecha, hora):
        """Ejercicio 7: Verifica si existe un viaje idéntico para el mismo conductor."""
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT id FROM viaje
                WHERE conductor_id = %s
                  AND origen = %s
                  AND destino = %s
                  AND fecha = %s
                  AND hora = %s
                  AND estado != 'CANCELADO'
                LIMIT 1
            """
            cursor.execute(sql, (conductor_id, origen, destino, fecha, hora))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def crear(self, conductor_id, datos):
        cursor = self.connection.cursor()
        try:
            sql = """
                INSERT INTO viaje (
                    conductor_id, origen, destino, fecha,
                    hora, cupos, precio, estado
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'DISPONIBLE')
            """
            cursor.execute(sql, (
                conductor_id,
                datos["origen"],
                datos["destino"],
                datos["fecha"],
                datos["hora"],
                datos["cupos"],
                datos["precio"]
            ))
            return cursor.lastrowid
        finally:
            cursor.close()

    def listar(self, origen=None, destino=None, fecha=None, estado=None,
               precio_min=None, precio_max=None, solo_disponibles=False,
               desde=None, hasta=None):
        """
        Ejercicios 1, 2 y 3:
        Listado con filtros avanzados en SQL (rango de precio, solo disponibles, fechas).
        """
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT
                    v.id, v.origen, v.destino, v.fecha, v.hora,
                    v.cupos, v.precio, v.estado,
                    CONCAT(u.nombres, ' ', u.apellidos) AS conductor
                FROM viaje v
                INNER JOIN conductor c ON c.id = v.conductor_id
                INNER JOIN usuario u ON u.id = c.usuario_id
                WHERE 1 = 1
            """
            params = []

            if origen:
                sql += " AND v.origen LIKE %s"
                params.append(f"%{origen}%")
            if destino:
                sql += " AND v.destino LIKE %s"
                params.append(f"%{destino}%")
            if fecha:
                sql += " AND v.fecha = %s"
                params.append(fecha)
            if estado:
                sql += " AND v.estado = %s"
                params.append(estado)

            # Ejercicio 1: Rango de precio
            if precio_min is not None:
                sql += " AND v.precio >= %s"
                params.append(precio_min)
            if precio_max is not None:
                sql += " AND v.precio <= %s"
                params.append(precio_max)

            # Ejercicio 2: Solo viajes con cupos disponibles
            if solo_disponibles:
                sql += " AND v.estado = 'DISPONIBLE' AND v.cupos > 0"

            # Ejercicio 3: Rango de fechas (desde / hasta)
            if desde:
                sql += " AND v.fecha >= %s"
                params.append(desde)
            if hasta:
                sql += " AND v.fecha <= %s"
                params.append(hasta)

            sql += " ORDER BY v.fecha, v.hora"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()

    def listar_por_conductor(self, conductor_id, estado=None):
        """Ejercicio 4: Lista los viajes del conductor con filtro opcional de estado."""
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT
                    v.id, v.origen, v.destino, v.fecha, v.hora,
                    v.cupos, v.precio, v.estado
                FROM viaje v
                WHERE v.conductor_id = %s
            """
            params = [conductor_id]
            if estado:
                sql += " AND v.estado = %s"
                params.append(estado)

            sql += " ORDER BY v.fecha, v.hora"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()

    def obtener_por_id(self, viaje_id):
        """Ejercicio 8: Detalle enriquecido con datos del conductor mediante JOIN."""
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT
                    v.id, v.conductor_id, v.origen, v.destino,
                    v.fecha, v.hora, v.cupos, v.precio, v.estado,
                    v.fecha_registro,
                    c.usuario_id AS conductor_usuario_id,
                    c.licencia AS conductor_licencia,
                    c.calificacion AS conductor_calificacion,
                    u.nombres AS conductor_nombres,
                    u.apellidos AS conductor_apellidos,
                    CONCAT(u.nombres, ' ', u.apellidos) AS conductor
                FROM viaje v
                INNER JOIN conductor c ON c.id = v.conductor_id
                INNER JOIN usuario u ON u.id = c.usuario_id
                WHERE v.id = %s
            """
            cursor.execute(sql, (viaje_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def actualizar(self, viaje_id, datos):
        cursor = self.connection.cursor()
        try:
            sql = """
                UPDATE viaje
                SET origen = %s,
                    destino = %s,
                    fecha = %s,
                    hora = %s,
                    cupos = %s,
                    precio = %s
                WHERE id = %s
            """
            cursor.execute(sql, (
                datos["origen"],
                datos["destino"],
                datos["fecha"],
                datos["hora"],
                datos["cupos"],
                datos["precio"],
                viaje_id
            ))
            return cursor.rowcount
        finally:
            cursor.close()

    def actualizar_cupos(self, viaje_id, cupos):
        """Ejercicio 5: Actualizar únicamente los cupos de un viaje."""
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE viaje SET cupos = %s WHERE id = %s"
            cursor.execute(sql, (cupos, viaje_id))
            return cursor.rowcount
        finally:
            cursor.close()

    def cambiar_estado(self, viaje_id, nuevo_estado):
        """Ejercicio 6: Cambiar el estado del viaje."""
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE viaje SET estado = %s WHERE id = %s"
            cursor.execute(sql, (nuevo_estado, viaje_id))
            return cursor.rowcount
        finally:
            cursor.close()

    def cancelar(self, viaje_id):
        """Ejercicio 9: Cancelación lógica cambiando estado a CANCELADO."""
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE viaje SET estado = 'CANCELADO' WHERE id = %s"
            cursor.execute(sql, (viaje_id,))
            return cursor.rowcount
        finally:
            cursor.close()

    def resumen_por_estado(self, conductor_id):
        """Ejercicio 10: Agrupación en SQL mediante GROUP BY por estado."""
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT v.estado, COUNT(*) AS total
                FROM viaje v
                WHERE v.conductor_id = %s
                GROUP BY v.estado
                ORDER BY total DESC
            """
            cursor.execute(sql, (conductor_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
