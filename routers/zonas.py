import json
from fastapi import APIRouter
from db.connection import execute_read_query, execute_write_query
from schemas.zonas import ZonaCreate
from services.geo_utils import rows_to_geojson

router = APIRouter(prefix="/zonas", tags=["Zonas Personalizadas"])

@router.get("/capa-referencia-centralidades/")
def get_capa_referencia(clave: str = None):
    """
    Obtiene la geometría de una centralidad barrial para usarla como referencia
    al dibujar una zona personalizada.
    """
    if not clave:
        return {"type": "FeatureCollection", "features": []}
        
    # Usamos comillas dobles para la columna "CLAVE_2" en PostgreSQL
    query = """
        SELECT "CLAVE_2", ST_AsGeoJSON(geom) as geom 
        FROM centralidad_barrial02 
        WHERE "CLAVE_2" = %(c)s
    """
    # use_pool2=False (por defecto) asegura que use la base de datos General
    rows = execute_read_query(query, {"c": clave}, use_pool2=False)
    return rows_to_geojson(rows)

@router.post("/mis_zonas/")
def guardar_zona(zona: ZonaCreate):
    """
    Guarda una nueva zona dibujada por el usuario en la base de datos.
    """
    geom_json = json.dumps(zona.geom)
    
    # ST_GeomFromGeoJSON convierte el JSON del frontend a geometría de PostGIS
    query = """
        INSERT INTO mis_zonas (nombre, geom) 
        VALUES (%(nombre)s, ST_SetSRID(ST_GeomFromGeoJSON(%(geom)s), 4326)) 
        RETURNING id
    """
    
    params = {
        "nombre": zona.nombre, 
        "geom": geom_json
    }
    
    # execute_write_query gestiona el commit() y libera la conexión al Pool 1
    id_nueva = execute_write_query(query, params, use_pool2=False)
    
    return {
        "mensaje": "Zona guardada exitosamente", 
        "id": id_nueva
    }