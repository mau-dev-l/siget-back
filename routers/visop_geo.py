from fastapi import APIRouter, HTTPException
import json
from schemas.zonas import ObraNueva
from db.connection import execute_read_query, execute_write_query

router = APIRouter(prefix="/visop", tags=["Capas Geográficas"])

@router.get("/estadisticas/obras")
def get_estadisticas():
    """
    Obtiene el conteo de obras agrupadas por tipo para los años 2023, 2024 y 2025.
    """
    # 1. Definimos las consultas con alias claros para evitar el KeyError
    queries = {
        "anio_2025": 'SELECT tipo_proy AS label, COUNT(*) AS total FROM faismun_2025 GROUP BY tipo_proy ORDER BY total DESC;',
        "anio_2024": 'SELECT tipo AS label, COUNT(*) AS total FROM faismun_2024_geo GROUP BY tipo ORDER BY total DESC;',
        "anio_2023": 'SELECT tipo AS label, COUNT(*) AS total FROM faismun_2023_geo GROUP BY tipo ORDER BY total DESC;'
    }
    
    resultados = {}
    
    try:
        for anio, sql in queries.items():
            # 2. IMPORTANTE: use_pool2=True indica que use la base de datos de VISOP
            rows = execute_read_query(sql, use_pool2=True)
            
            # 3. Acceso por nombre de columna (soluciona el KeyError: 0)
            resultados[anio] = [
                {"label": r["label"] or "Sin Clasificar", "value": r["total"]} 
                for r in rows
            ]
            
        return resultados
    except Exception as e:
        print(f"❌ Error crítico en estadísticas: {e}")
        return {"anio_2025": [], "anio_2024": [], "anio_2023": []}

@router.post("/obras/crear")
def crear_obra(obra: ObraNueva):
    """
    Registra una nueva obra en la base de datos de VISOP (Pool 2).
    """
    sql = """
    INSERT INTO faismun_2024_geo (obra_accio, no_aprobac, colonia, geom)
    VALUES (%(nombre)s, %(num)s, %(col)s, ST_SetSRID(ST_GeomFromGeoJSON(%(geom)s), 4326))
    RETURNING id;
    """
    
    params = {
        "nombre": obra.nombre_obra,
        "num": obra.num_aprobacion,
        "col": obra.colonia,
        "geom": json.dumps(obra.geometry)
    }
    
    try:
        # execute_write_query maneja el commit y la liberación al pool 2
        nuevo_id = execute_write_query(sql, params, use_pool2=True)
        return {"status": "ok", "id": nuevo_id, "mensaje": "Obra registrada correctamente"}
    except Exception as e:
        print(f"❌ Error al insertar obra: {e}")
        raise HTTPException(status_code=500, detail="Error interno al guardar la obra")