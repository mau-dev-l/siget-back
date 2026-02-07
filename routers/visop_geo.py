from fastapi import APIRouter, HTTPException
import json
from schemas.zonas import ObraNueva
from db.connection import pg_pool2



router = APIRouter(prefix="/visop", tags=["Capas Geográficas"])




# --- ENDPOINT DASHBOARD (ACTUALIZADO 2025) ---
@router.get("/estadisticas/obras")
def get_estadisticas():
    # Inicializamos la estructura con 3 años
    resultados = {"anio_2025": [], "anio_2024": [], "anio_2023": []}
    
    try:
        with pg_pool2.getconn() as conn:
            cur = conn.cursor()
            
            # --- 2025 
            try:
                # Usamos 'tipo_proy' que es la columna que me mostraste en la imagen
                cur.execute("SELECT tipo_proy, COUNT(*) as total FROM faismun_2025 GROUP BY tipo_proy ORDER BY total DESC;")
                resultados["anio_2025"] = [{"label": row[0] or "Sin Clasificar", "value": row[1]} for row in cur.fetchall()]
            except Exception as e:
                print(f"Error Stats 2025: {e}")
                conn.rollback()
                resultados["anio_2025"] = []

            # --- 2024 ---
            try:
                cur.execute("SELECT tipo, COUNT(*) as total FROM faismun_2024_geo GROUP BY tipo ORDER BY total DESC;")
                resultados["anio_2024"] = [{"label": row[0] or "Sin Clasificar", "value": row[1]} for row in cur.fetchall()]
            except Exception as e:
                print(f"Error Stats 2024: {e}")
                conn.rollback()
                resultados["anio_2024"] = []
            
            # --- 2023 ---
            try:
                cur.execute("SELECT tipo, COUNT(*) as total FROM faismun_2023_geo GROUP BY tipo ORDER BY total DESC;")
                resultados["anio_2023"] = [{"label": row[0] or "Sin Clasificar", "value": row[1]} for row in cur.fetchall()]
            except Exception as e:
                print(f"Error Stats 2023: {e}")
                conn.rollback()
                resultados["anio_2023"] = []

        return resultados
    except Exception as e:
        print(f" Error General Stats: {e}")
        return {"anio_2025": [], "anio_2024": [], "anio_2023": []}
    

@router.post("/obras/crear")
def crear_obra(obra: ObraNueva):
    print(f" Recibiendo obra: {obra.nombre_obra}")
    sql = """
    INSERT INTO faismun_2024_geo (obra_accio, no_aprobac, colonia, geom)
    VALUES (%s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
    RETURNING id;
    """
    try:
        geojson_str = json.dumps(obra.geometry)
        with pg_pool2.getconn() as conn:
            cur = conn.cursor()
            cur.execute(sql, (obra.nombre_obra, obra.num_aprobacion, obra.colonia, geojson_str))
            nuevo_id = cur.fetchone()[0]
        return {"status": "ok", "id": nuevo_id, "mensaje": "Obra registrada correctamente"}
    except Exception as e:
        print(f" Error insertando en BD: {e}")
        raise HTTPException(status_code=500, detail=str(e))