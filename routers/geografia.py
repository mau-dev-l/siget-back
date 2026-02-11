from fastapi import APIRouter, Query
import json
from db.connection import execute_read_query, execute_read_one, execute_write_query
from schemas.zonas import ZonaCreate
from services.geo_utils import rows_to_geojson

router = APIRouter(tags=["Geografía y Censo"])

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


@router.post("/mis_zonas/")
def guardar_zona(zona: ZonaCreate):
    geom_json = json.dumps(zona.geom)
    query = """INSERT INTO mis_zonas (nombre, geom) VALUES (%(nombre)s, ST_SetSRID(ST_GeomFromGeoJSON(%(geom)s), 4326)) RETURNING id"""
    id_nueva = execute_write_query(query, {"nombre": zona.nombre, "geom": geom_json})
    return {"mensaje": "Zona guardada", "id": id_nueva}