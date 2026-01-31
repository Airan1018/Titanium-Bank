import mysql.connector
from mysql.connector import Error

def test_titanium_connection():
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': ''
    }
    
    print("--- COMPROBACIÓN DE SISTEMA TITANIUM ---")
    
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            print("[OK] Servidor MySQL detectado y encendido.")
            
            cursor = conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS titanium_db")
            print("[OK] Base de datos 'titanium_db' lista para usar.")
            
            cursor.execute("USE titanium_db")
            print("[OK] Conexión establecida con éxito.")
            
            conn.close()
            print("\n¡Todo listo! Ya puedes abrir tu proyecto principal.")
            
    except Error as e:
        print(f"\n[ERROR] No se pudo conectar a MySQL.")
        print(f"Causa: {e}")
        print("\nREVISA LO SIGUIENTE:")
        print("1. ¿El XAMPP está abierto?")
        print("2. ¿Le diste 'Start' a MySQL?")
        print("3. ¿El puerto es el 3306?")

if __name__ == "__main__":
    test_titanium_connection()