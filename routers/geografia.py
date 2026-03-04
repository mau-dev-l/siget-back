from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db.connection import get_db
from services.geo_utils import rows_to_geojson

router = APIRouter(tags=["Geografía y Censo"])

@router.get("/censo/")
async def get_censo_bbox(in_bbox: str = Query(None), db: AsyncSession = Depends(get_db)):
    if not in_bbox: 
        return {"type": "FeatureCollection", "features": []}
    
    try:
        bbox = list(map(float, in_bbox.split(',')))
        query = text("""
            SELECT cvegeo, pobtot, pobmas, pobfem, vivtot,
                   ST_AsGeoJSON(wkb_geometry) as geom 
            FROM cpyv_2020
            WHERE wkb_geometry && ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
        """)
        
        params = {
            "min_lon": bbox[0], "min_lat": bbox[1], 
            "max_lon": bbox[2], "max_lat": bbox[3]
        }
        
        result = await db.execute(query, params)
        return rows_to_geojson(result.mappings().all())
        
    except Exception as e:
        return {"type": "FeatureCollection", "features": [], "error": str(e)}

@router.get("/centralidades/")
async def get_poligono_zona(clave_2: str, db: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT "NAME" as nombre, "POBTOT" as pobtot, "VIVTOT" as vivtot,
               "POBFEM" as pobfem, "POBMAS" as pobmas,
               ST_AsGeoJSON(geom) as geom 
        FROM centralidad_barrial02 
        WHERE "CLAVE_2" = :clave
    """)
    result = await db.execute(query, {"clave": clave_2})
    return rows_to_geojson(result.mappings().all())

@router.get("/lista-centralidades/")
async def get_lista_zonas(db: AsyncSession = Depends(get_db)):
    query = text('SELECT DISTINCT "CLAVE_2" FROM centralidad_barrial02 WHERE "CLAVE_2" IS NOT NULL ORDER BY "CLAVE_2"')
    result = await db.execute(query)
    # Extraemos solo el valor de la columna
    return [r["CLAVE_2"] for r in result.mappings().all()]

@router.get("/info-manzana/")
async def obtener_info_manzana(lat: float, lon: float, db: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT cvegeo, pobtot, vivtot, pobfem, pobmas 
        FROM cpyv_2020 
        WHERE ST_Contains(wkb_geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
    """)
    result = await db.execute(query, {"lat": lat, "lon": lon})
    resultado = result.mappings().first()
    
    if not resultado: 
        return {"mensaje": "Sin datos"}
    
    return {
        "clave_geo": resultado["cvegeo"],
        "poblacion_total": resultado["pobtot"],
        "viviendas": resultado["vivtot"],
        "mujeres": resultado["pobfem"],
        "hombres": resultado["pobmas"]
    }

@router.get("/colonias/")
async def get_colonias(db: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT "NOM_ASEN" as nom_asen, "POBTOT" as pobtot, ST_AsGeoJSON(geom) as geom 
        FROM "COLONIAS_2023_POB2020_UTM" 
        ORDER BY "NOM_ASEN" ASC
    """)
    result = await db.execute(query)
    return rows_to_geojson(result.mappings().all())

@router.get("/denue/")
async def get_denue(in_bbox: str = Query(None), db: AsyncSession = Depends(get_db)):
    if not in_bbox: 
        return {"type": "FeatureCollection", "features": []}
    
    try:
        bbox = list(map(float, in_bbox.split(',')))
        query = text("""
            SELECT id, nom_estab, codigo_act, nombre_act, 
                   ST_AsGeoJSON(geom) as geom
            FROM denue_tuxtla_cb_2026 
            WHERE geom && ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
            LIMIT 10000
        """)
        
        params = {
            "min_lon": bbox[0], "min_lat": bbox[1], 
            "max_lon": bbox[2], "max_lat": bbox[3]
        }
        
        result = await db.execute(query, params)
        return rows_to_geojson(result.mappings().all())

    except Exception as e:
        return {"type": "FeatureCollection", "features": [], "error": str(e)}

@router.get("/mis_zonas/")
async def listar_mis_zonas(db: AsyncSession = Depends(get_db)):
    query = text("SELECT id, nombre, ST_AsGeoJSON(geom) as geom FROM mis_zonas")
    result = await db.execute(query)
    return rows_to_geojson(result.mappings().all())