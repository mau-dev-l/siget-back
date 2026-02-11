from fastapi import APIRouter, Query
import json
from db.connection import execute_read_query, execute_read_one, execute_write_query
from schemas.zonas import ZonaCreate
from services.geo_utils import rows_to_geojson

router = APIRouter(tags=["Geografía y Censo"])

@router.get("/censo/")
def get_censo_bbox(in_bbox: str = Query(None)):
    if not in_bbox: 
        return {"type": "FeatureCollection", "features": []}
    
    try:
        # Convertimos el string del bbox a una lista de floats
        bbox = list(map(float, in_bbox.split(',')))
        
        query = """
            SELECT cvegeo, pobtot, pobmas, pobfem, vivtot,
                   ST_AsGeoJSON(wkb_geometry) as geom 
            FROM cpyv_2020
            WHERE wkb_geometry && ST_MakeEnvelope(%(min_lon)s, %(min_lat)s, %(max_lon)s, %(max_lat)s, 4326)
        """
        
        params = {
            "min_lon": bbox[0], "min_lat": bbox[1], 
            "max_lon": bbox[2], "max_lat": bbox[3]
        }
        
        # Usamos nuestra función segura que libera la conexión al terminar
        rows = execute_read_query(query, params)
        return rows_to_geojson(rows)
        
    except Exception as e:
        print(f"Error en censo BBOX: {e}")
        return {"type": "FeatureCollection", "features": [], "error": str(e)}
    
@router.get("/centralidades/")
def get_poligono_zona(clave_2: str):
    # Usamos execute_read_query para mantener el pool sano y evitar el "exhausted"
    query = """
        SELECT "NAME" as nombre, "POBTOT" as pobtot, "VIVTOT" as vivtot,
               ST_AsGeoJSON(geom) as geom 
        FROM centralidad_barrial02 
        WHERE "CLAVE_2" = %(clave)s
    """
    rows = execute_read_query(query, {"clave": clave_2})
    
    # IMPORTANTE: Si no hay filas, devolvemos un GeoJSON vacío 
    # para que el JS no lance el error de 'length'
    if not rows:
        return {"type": "FeatureCollection", "features": []}
        
    return rows_to_geojson(rows)


@router.get("/lista-centralidades/")
def get_lista_zonas():
    query = 'SELECT DISTINCT "CLAVE_2" FROM centralidad_barrial02 WHERE "CLAVE_2" IS NOT NULL ORDER BY "CLAVE_2"'
    rows = execute_read_query(query)
    return [r["CLAVE_2"] for r in rows]

@router.get("/info-manzana/")
def obtener_info_manzana(lat: float, lon: float):
    query = """
        SELECT cvegeo, pobtot, vivtot, pobfem, pobmas 
        FROM cpyv_2020 
        WHERE ST_Contains(wkb_geometry, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326))
    """
    resultado = execute_read_one(query, {"lat": lat, "lon": lon})
    if not resultado: return {"mensaje": "Sin datos"}
    return {
        "clave_geo": resultado["cvegeo"],
        "poblacion_total": resultado["pobtot"],
        "viviendas": resultado["vivtot"],
        "mujeres": resultado["pobfem"],
        "hombres": resultado["pobmas"]
    }

@router.get("/colonias/")
def get_colonias():
    query = 'SELECT "NOM_ASEN" as nom_asen, "POBTOT" as pobtot, ST_AsGeoJSON(geom) as geom FROM "COLONIAS_2023_POB2020_UTM" ORDER BY "NOM_ASEN" ASC'
    return rows_to_geojson(execute_read_query(query))

@router.get("/vialidades/")
def get_vialidades(in_bbox: str = Query(None)):
    if not in_bbox: return {"type": "FeatureCollection", "features": []}
    bbox = list(map(float, in_bbox.split(',')))
    query = """SELECT "NOMVIAL" as nom_vial, ST_AsGeoJSON(geom) as geom FROM "VIALIDADES_TUXTLA_UTM" 
               WHERE geom && ST_MakeEnvelope(%(min_lon)s, %(min_lat)s, %(max_lon)s, %(max_lat)s, 4326) LIMIT 1000"""
    params = {"min_lon": bbox[0], "min_lat": bbox[1], "max_lon": bbox[2], "max_lat": bbox[3]}
    return rows_to_geojson(execute_read_query(query, params))

@router.get("/denue/")
def get_denue(in_bbox: str = Query(None)):
    if not in_bbox: return {"type": "FeatureCollection", "features": []}
    bbox = list(map(float, in_bbox.split(',')))
    query = """SELECT id, nom_estab, nombre_act, ST_AsGeoJSON(geom) as geom FROM denue_tuxtla_cb_2026 
               WHERE geom && ST_MakeEnvelope(%(min_lon)s, %(min_lat)s, %(max_lon)s, %(max_lat)s, 4326) LIMIT 50000"""
    return rows_to_geojson(execute_read_query(query, {"min_lon": bbox[0], "min_lat": bbox[1], "max_lon": bbox[2], "max_lat": bbox[3]}))


@router.get("/mis_zonas/")
def listar_mis_zonas():
    query = "SELECT id, nombre, ST_AsGeoJSON(geom) as geom FROM mis_zonas"
    return rows_to_geojson(execute_read_query(query))