import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from core.config import settings

# --- CONFIGURACIÓN DE LOS POOLS ---
# Aumentamos maxconn a 40 para soportar más workers
try:
    pg_pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=40,
        host=settings.DB_HOST,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT
    )
    
    pg_pool2 = psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=40,
        host=settings.DB_HOST,
        database=settings.DB_NAME_2,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT
    )
    print("✅ Pools de conexiones (1 y 2) listos con mayor capacidad.")
except Exception as e:
    print(f"❌ Error creando los pools: {e}")
    pg_pool = None
    pg_pool2 = None

def get_db_connection():
    if not pg_pool: raise Exception("Pool 1 no inicializado")
    return pg_pool.getconn()

def get_db_connection2():
    if not pg_pool2: raise Exception("Pool 2 no inicializado")
    return pg_pool2.getconn()

def release_db_connection(conn):
    if pg_pool and conn:
        # El pool de psycopg2 es inteligente: sabe si la conexión 
        # pertenece al pool 1 o al pool 2 al intentar devolverla.
        try:
            pg_pool.putconn(conn)
        except:
            pg_pool2.putconn(conn)

def execute_read_query(query: str, params: dict = None):
    conn = get_db_connection()
    try:
        # Usar 'with' asegura que el cursor se cierre automáticamente
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or {})
            return cursor.fetchall()
    except Exception as e:
        print(f"Error en query: {e}")
        raise e
    finally:
        release_db_connection(conn)

def execute_read_one(query: str, params: dict = None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or {})
            return cursor.fetchone()
    finally:
        release_db_connection(conn)

def execute_write_query(query: str, params: dict = None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or {})
            # Intentamos obtener el ID si es un INSERT ... RETURNING
            try:
                result = cursor.fetchone()[0] if cursor.description else cursor.rowcount
            except:
                result = cursor.rowcount
            conn.commit() # Importante: commit antes de liberar
            return result
    except Exception as e:
        conn.rollback() # Si falla, rollback para limpiar la conexión
        raise e
    finally:
        release_db_connection(conn)