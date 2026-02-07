import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from core.config import settings

try:
    pg_pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=20,
        host=settings.DB_HOST,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT
    )
    print(" Pool de conexiones PostgreSQL listo.")
except Exception as e:
    print(f" Error creando el pool: {e}")
    pg_pool = None
try:
    pg_pool2 = psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=20,
        host=settings.DB_HOST,
        database=settings.DB_NAME_2,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT
    )
    print(" Pool de conexiones PostgreSQL listo.")
except Exception as e:
    print(f" Error creando el pool: {e}")
    pg_pool2 = None

def get_db_connection():
    if not pg_pool: raise Exception("Pool no inicializado")
    return pg_pool.getconn()

def release_db_connection(conn):
    if pg_pool and conn: pg_pool.putconn(conn)

def execute_read_query(query: str, params: dict = None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params or {})
        return cursor.fetchall()
    finally:
        release_db_connection(conn)

def execute_read_one(query: str, params: dict = None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params or {})
        return cursor.fetchone()
    finally:
        release_db_connection(conn)

def execute_write_query(query: str, params: dict = None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or {})
        try:
            result = cursor.fetchone()[0]
        except:
            result = cursor.rowcount
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_db_connection(conn)