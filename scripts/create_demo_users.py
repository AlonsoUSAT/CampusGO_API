from werkzeug.security import generate_password_hash
from database import get_connection

USUARIOS = [
    ("juan.perez@usat.edu.pe", "CampusGo#2026", "Juan", "Pérez Sánchez", "PASAJERO", "ACTIVO"),
    ("carlos.mendoza@usat.edu.pe", "CampusGo#2026", "Carlos", "Mendoza Ruiz", "CONDUCTOR", "ACTIVO"),
    ("admin@campusgo.pe", "CampusGo#2026", "Administrador", "CampusGo", "ADMINISTRADOR", "ACTIVO"),
    ("inactivo@campusgo.pe", "CampusGo#2026", "Usuario", "Inactivo", "PASAJERO", "INACTIVO")
]

def main():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        sql = '''
            INSERT INTO usuario (
                email, password_hash, nombres, apellidos, rol, estado
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                password_hash = VALUES(password_hash),
                nombres = VALUES(nombres),
                apellidos = VALUES(apellidos),
                rol = VALUES(rol),
                estado = VALUES(estado)
        '''

        for email, password, nombres, apellidos, rol, estado in USUARIOS:
            cursor.execute(
                sql,
                (
                    email,
                    generate_password_hash(password),
                    nombres,
                    apellidos,
                    rol,
                    estado
                )
            )

        # Asociar perfil de pasajero a juan.perez
        cursor.execute('''
            INSERT INTO pasajero (usuario_id)
            SELECT id FROM usuario WHERE email = 'juan.perez@usat.edu.pe'
            ON DUPLICATE KEY UPDATE usuario_id = VALUES(usuario_id)
        ''')

        # Asociar perfil de conductor a carlos.mendoza
        cursor.execute('''
            INSERT INTO conductor (usuario_id, licencia, calificacion)
            SELECT id, 'Q12345678', 5.0 FROM usuario WHERE email = 'carlos.mendoza@usat.edu.pe'
            ON DUPLICATE KEY UPDATE licencia = VALUES(licencia)
        ''')

        connection.commit()
        print("Usuarios de prueba y perfiles creados/actualizados correctamente.")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main()
