import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from core.config import settings

# --- CONFIGURACIÓN DE LOS POOLS ---
# Aumentamos la capacidad para soportar múltiples peticiones simultáneas
try:
    # Pool 1: Base de datos General (Censo, DENUE, Geografía)
    pg_pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=40,
        host=settings.DB_HOST,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT
    )
    
    # Pool 2: Base de datos VISOP (Obras, Faismun)
    pg_pool2 = psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=40,
        host=settings.DB_HOST,
        database=settings.DB_NAME_2,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT
    )
    print("✅ Pools de conexiones (1 y 2) listos con capacidad de 40 c/u.")
except Exception as e:
    print(f"❌ Error creando los pools: {e}")
    pg_pool = None
    pg_pool2 = None

# --- FUNCIONES DE GESTIÓN DE CONEXIÓN ---

def get_db_connection(use_pool2: bool = False):
    """Obtiene una conexión del Pool 1 o del Pool 2 según se requiera."""
    target_pool = pg_pool2 if use_pool2 else pg_pool
    if not target_pool:
        raise Exception(f"Pool {'2 (VISOP)' if use_pool2 else '1 (General)'} no está inicializado.")
    return target_pool.getconn()

def release_db_connection(conn, use_pool2: bool = False):
    """Devuelve la conexión al pool correspondiente."""
    target_pool = pg_pool2 if use_pool2 else pg_pool
    if target_pool and conn:
        target_pool.putconn(conn)

# --- FUNCIONES DE EJECUCIÓN (READ/WRITE) ---

def execute_read_query(query: str, params: dict = None, use_pool2: bool = False):
    """Ejecuta un SELECT y devuelve una lista de diccionarios."""
    conn = get_db_connection(use_pool2)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or {})
            return cursor.fetchall()
    except Exception as e:
        print(f"Error SQL (Lectura): {e}")
        return []
    finally:
        release_db_connection(conn, use_pool2)

def execute_read_one(query: str, params: dict = None, use_pool2: bool = False):
    """Ejecuta un SELECT y devuelve un solo resultado."""
    conn = get_db_connection(use_pool2)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or {})
            return cursor.fetchone()
    except Exception as e:
        print(f"Error SQL (Lectura Uno): {e}")
        return None
    finally:
        release_db_connection(conn, use_pool2)

def execute_write_query(query: str, params: dict = None, use_pool2: bool = False):
    """Ejecuta INSERT, UPDATE o DELETE y maneja la transacción."""
    conn = get_db_connection(use_pool2)
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or {})
            # Si la consulta tiene RETURNING id, obtenemos el valor
            try:
                result = cursor.fetchone()[0] if cursor.description else cursor.rowcount
            except:
                result = cursor.rowcount
            conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        print(f"Error SQL (Escritura): {e}")
        raise e
    finally:
        release_db_connection(conn, use_pool2)