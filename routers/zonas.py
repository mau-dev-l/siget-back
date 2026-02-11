import json
from fastapi import APIRouter
from db.connection import execute_read_query, execute_write_query
from schemas.zonas import ZonaCreate
from services.geo_utils import rows_to_geojson

router = APIRouter(prefix="/zonas", tags=["Zonas Personalizadas"])

@router.get("/lista-centralidades/")
def get_lista_zonas():
    query = 'SELECT DISTINCT "CLAVE_2" FROM centralidad_barrial02 WHERE "CLAVE_2" IS NOT NULL ORDER BY "CLAVE_2"'
    rows = execute_read_query(query)
    return [r["CLAVE_2"] for r in rows]

# --- OBTENER POLÍGONOS DE REFERENCIA ---
@router.get("/capa-referencia-centralidades/")
def get_capa_referencia(clave: str):
    query = """SELECT "CLAVE_2", ST_AsGeoJSON(geom) as geom 
               FROM centralidad_barrial02 
               WHERE "CLAVE_2" = %(clave)s"""
    rows = execute_read_query(query, {"clave": clave})
    return rows_to_geojson(rows)

# --- GUARDAR MI ZONA ---
@router.post("/mis_zonas/")
def guardar_zona(zona: ZonaCreate):
    geom_json = json.dumps(zona.geom)
    query = """INSERT INTO mis_zonas (nombre, geom) 
               VALUES (%(nombre)s, ST_SetSRID(ST_GeomFromGeoJSON(%(geom)s), 4326)) 
               RETURNING id"""
    id_nueva = execute_write_query(query, {"nombre": zona.nombre, "geom": geom_json})
    return {"mensaje": "Zona guardada", "id": id_nueva}
# ... (Aquí agregarías el resto de DELETE y GET de zonas)