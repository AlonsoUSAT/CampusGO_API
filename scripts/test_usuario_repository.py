import sys
from database import get_connection
from repositories.usuario_repository import UsuarioRepository

def main():
    print("=== Probando UsuarioRepository ===")
    conn = get_connection()
    try:
        repo = UsuarioRepository(conn)
        
        # 1. Probar buscar_por_email con usuario existente
        test_email = "juan.perez@usat.edu.pe"
        print(f"\n1. Buscando usuario por email: '{test_email}'...")
        user = repo.buscar_por_email(test_email)
        if user:
            print("   [OK] Usuario encontrado:")
            for key, val in user.items():
                print(f"      - {key}: {val}")
        else:
            print("   [ERROR] No se encontro el usuario de prueba.")
            return

        # 2. Probar buscar_por_id con el id obtenido
        user_id = user["id"]
        print(f"\n2. Buscando usuario por id: {user_id}...")
        user_by_id = repo.buscar_por_id(user_id)
        if user_by_id:
            print("   [OK] Usuario encontrado por ID:")
            for key, val in user_by_id.items():
                print(f"      - {key}: {val}")
        else:
            print("   [ERROR] No se encontro el usuario por ID.")

        # 3. Probar buscar_por_email con un usuario que no existe
        non_existent_email = "inexistente@correo.com"
        print(f"\n3. Buscando email inexistente: '{non_existent_email}'...")
        user_none = repo.buscar_por_email(non_existent_email)
        if user_none is None:
            print("   [OK] Retorno None correctamente para usuario inexistente.")
        else:
            print("   [ERROR] Se esperaba None pero retorno un valor.")

    finally:
        conn.close()
        print("\n=== Fin de la prueba ===")

if __name__ == "__main__":
    main()
