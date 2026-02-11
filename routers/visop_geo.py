from fastapi import APIRouter, HTTPException
import json
from schemas.zonas import ObraNueva
# Importamos también la función de liberación
from db.connection import pg_pool2, release_db_connection 

router = APIRouter(prefix="/visop", tags=["Capas Geográficas"])

@router.get("/estadisticas/obras")
def get_estadisticas():
    resultados = {"anio_2025": [], "anio_2024": [], "anio_2023": []}
    
    # 1. Obtenemos la conexión
    conn = pg_pool2.getconn()
    try:
        # 2. Usamos 'with' para el cursor (esto sí cierra el cursor automáticamente)
        with conn.cursor() as cur:
            # --- 2025 ---
            try:
                cur.execute("SELECT tipo_proy, COUNT(*) as total FROM faismun_2025 GROUP BY tipo_proy ORDER BY total DESC;")
                resultados["anio_2025"] = [{"label": row[0] or "Sin Clasificar", "value": row[1]} for row in cur.fetchall()]
            except Exception as e:
                print(f"Error Stats 2025: {e}")
                conn.rollback()

            # --- 2024 ---
            try:
                cur.execute("SELECT tipo, COUNT(*) as total FROM faismun_2024_geo GROUP BY tipo ORDER BY total DESC;")
                resultados["anio_2024"] = [{"label": row[0] or "Sin Clasificar", "value": row[1]} for row in cur.fetchall()]
            except Exception as e:
                print(f"Error Stats 2024: {e}")
                conn.rollback()
            
            # --- 2023 ---
            try:
                cur.execute("SELECT tipo, COUNT(*) as total FROM faismun_2023_geo GROUP BY tipo ORDER BY total DESC;")
                resultados["anio_2023"] = [{"label": row[0] or "Sin Clasificar", "value": row[1]} for row in cur.fetchall()]
            except Exception as e:
                print(f"Error Stats 2023: {e}")
                conn.rollback()

        return resultados
    except Exception as e:
        print(f" Error General Stats: {e}")
        return {"anio_2025": [], "anio_2024": [], "anio_2023": []}
    finally:
        # 3. ¡ESTO ES LO MÁS IMPORTANTE! Devolver la conexión al pool
        release_db_connection(conn)

@router.post("/obras/crear")
def crear_obra(obra: ObraNueva):
    sql = """
    INSERT INTO faismun_2024_geo (obra_accio, no_aprobac, colonia, geom)
    VALUES (%s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
    RETURNING id;
    """
    conn = pg_pool2.getconn()
    try:
        geojson_str = json.dumps(obra.geometry)
        with conn.cursor() as cur:
            cur.execute(sql, (obra.nombre_obra, obra.num_aprobacion, obra.colonia, geojson_str))
            nuevo_id = cur.fetchone()[0]
            conn.commit() # Aseguramos el guardado
        return {"status": "ok", "id": nuevo_id, "mensaje": "Obra registrada correctamente"}
    except Exception as e:
        conn.rollback()
        print(f" Error insertando en BD: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Liberamos conexión
        release_db_connection(conn)