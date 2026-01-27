import os
import time
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 1. Cargar variables
load_dotenv()

# 2. Configuración de conexión (usando variables separadas es más seguro)
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")

# 3. Crear el Pool de Conexiones
# Usamos ThreadedConnectionPool porque FastAPI usará hilos para estas consultas
try:
    pg_pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=20,
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    print("✅ Pool de conexiones PostgreSQL creado exitosamente.")
except Exception as e:
    print(f"❌ Error creando el pool de conexiones: {e}")
    pg_pool = None

def get_db_connection():
    """Obtiene una conexión del pool."""
    if not pg_pool:
        raise Exception("El pool de conexiones no está inicializado.")
    return pg_pool.getconn()

def release_db_connection(conn):
    """Devuelve la conexión al pool."""
    if pg_pool and conn:
        pg_pool.putconn(conn)

# --- FUNCIONES AUXILIARES PARA REEMPLAZAR databases.fetch_all ---

def execute_read_query(query: str, params: dict = None):
    """
    Ejecuta un SELECT y devuelve una lista de diccionarios (como fetch_all).
    """
    conn = get_db_connection()
    try:
        # RealDictCursor es CLAVE: permite acceder a las columnas por nombre (row['id'])
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params or {})
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except Exception as e:
        print(f"Error SQL (Lectura): {e}")
        return []
    finally:
        release_db_connection(conn)

def execute_read_one(query: str, params: dict = None):
    """
    Ejecuta un SELECT y devuelve un solo resultado (como fetch_one).
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params or {})
        row = cursor.fetchone()
        cursor.close()
        return row
    except Exception as e:
        print(f"Error SQL (Lectura Uno): {e}")
        return None
    finally:
        release_db_connection(conn)

def execute_write_query(query: str, params: dict = None):
    """
    Ejecuta INSERT/UPDATE/DELETE y devuelve el ID generado o filas afectadas.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or {})
        
        # Intentar obtener ID si es un INSERT con RETURNING
        try:
            result = cursor.fetchone()[0]
        except:
            result = cursor.rowcount
            
        conn.commit()
        cursor.close()
        return result
    except Exception as e:
        conn.rollback()
        print(f"Error SQL (Escritura): {e}")
        raise e
    finally:
        release_db_connection(conn)
