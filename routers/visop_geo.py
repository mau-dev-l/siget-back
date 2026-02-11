from fastapi import APIRouter, HTTPException
import json
from schemas.zonas import ObraNueva
from db.connection import execute_read_query, execute_write_query # Usamos las funciones de ayuda

router = APIRouter(prefix="/visop", tags=["Capas Geográficas"])

@router.get("/estadisticas/obras")
def get_estadisticas():
    # Definimos las consultas para cada año
    queries = {
        "anio_2025": "SELECT tipo_proy, COUNT(*) FROM faismun_2025 GROUP BY tipo_proy ORDER BY COUNT(*) DESC;",
        "anio_2024": "SELECT tipo, COUNT(*) FROM faismun_2024_geo GROUP BY tipo ORDER BY COUNT(*) DESC;",
        "anio_2023": "SELECT tipo, COUNT(*) FROM faismun_2023_geo GROUP BY tipo ORDER BY COUNT(*) DESC;"
    }
    
    resultados = {}
    
    for anio, sql in queries.items():
        # IMPORTANTE: use_pool2=True asegura que use la base de VISOP y libere bien la conexión
        rows = execute_read_query(sql, use_pool2=True)
        # Formateamos los datos para el frontend
        resultados[anio] = [{"label": r[0] or "Sin Clasificar", "value": r[1]} for r in rows]
        
    return resultados

@router.post("/obras/crear")
def crear_obra(obra: ObraNueva):
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
        # execute_write_query ya maneja el commit, el rollback y la liberación del pool
        nuevo_id = execute_write_query(sql, params, use_pool2=True)
        return {"status": "ok", "id": nuevo_id, "mensaje": "Obra registrada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar: {str(e)}")