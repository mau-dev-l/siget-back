import sys
import asyncio
import json
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import database

# ==========================================
# 🚑 FIX WINDOWS (Evita desconexiones)
# ==========================================
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI(title="API OVIE Tuxtla 2026")

# --- CONFIGURACIÓN CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS ---
class ZonaCreate(BaseModel):
    nombre: str
    geom: dict

# --- UTILERÍA ---
def rows_to_geojson(rows, geom_col="geom"):
    features = []
    for row in rows:
        row_dict = dict(row)
        geometry = json.loads(row_dict.pop(geom_col))
        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": row_dict,
            "id": row_dict.get("id") or row_dict.get("gid")
        })
    return {"type": "FeatureCollection", "features": features}

# --- EVENTOS ---
@app.on_event("startup")
async def startup():
    await database.connect()
    print("✅ Conectado a PostgreSQL Remoto (Modo Selector Windows)")

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# ================= RUTAS DEL SISTEMA =================

# 1. INFO AL CLIC
@app.get("/info-manzana/")
async def obtener_info_manzana(lat: float, lon: float):
    query = """
        SELECT cvegeo, pobtot, vivtot, pobfem, pobmas 
        FROM cpyv_2020 
        WHERE ST_Contains(wkb_geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
    """
    resultado = await database.fetch_one(query=query, values={"lat": lat, "lon": lon})
    if not resultado: return {"mensaje": "Sin datos"}
    return {
        "clave_geo": resultado["cvegeo"],
        "poblacion_total": resultado["pobtot"],
        "viviendas": resultado["vivtot"],
        "mujeres": resultado["pobfem"],
        "hombres": resultado["pobmas"]
    }

# 2. BUSCADOR DE COLONIAS
@app.get("/colonias/")
async def get_colonias():
    query = """
        SELECT "NOM_ASEN" as nom_asen, 
               "POBTOT" as pobtot,
               "POBFEM" as pobfem,
               "POBMAS" as pobmas,
               "VIVTOT" as vivtot,
               ST_AsGeoJSON(geom) as geom 
        FROM "COLONIAS_2023_POB2020_UTM"
        ORDER BY "NOM_ASEN" ASC
    """
    try:
        rows = await database.fetch_all(query=query)
        return rows_to_geojson(rows)
    except Exception as e:
        print(f"Error Colonias: {e}")
        return {"type": "FeatureCollection", "features": []}

# 3. VIALIDADES
@app.get("/vialidades/")
async def get_vialidades(in_bbox: str = Query(None)):
    if not in_bbox: return {"type": "FeatureCollection", "features": []}
    bbox = list(map(float, in_bbox.split(',')))
    
    query = """
        SELECT "NOMVIAL" as nom_vial, 
               ST_AsGeoJSON(geom) as geom
        FROM "VIALIDADES_TUXTLA_UTM"
        WHERE geom && ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
        LIMIT 1000
    """
    try:
        rows = await database.fetch_all(query=query, values={
            "min_lon": bbox[0], "min_lat": bbox[1], 
            "max_lon": bbox[2], "max_lat": bbox[3]
        })
        return rows_to_geojson(rows)
    except Exception as e:
        return {"type": "FeatureCollection", "features": []}

# 4. NEGOCIOS (AQUÍ ESTABA EL FRENO DE MANO) 🛑 -> 🟢
@app.get("/denue/")
async def get_denue(in_bbox: str = Query(None)):
    if not in_bbox: return {"type": "FeatureCollection", "features": []}
    bbox = list(map(float, in_bbox.split(',')))
    
    # HE SUBIDO EL LÍMITE DE 2000 A 50000 PARA TRAER TODO EL DENUE DE LA ZONA
    query = """
        SELECT id, nom_estab, codigo_act, nombre_act, 
               ST_AsGeoJSON(geom) as geom
        FROM denue_tuxtla_cb_2026 
        WHERE geom && ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
        LIMIT 50000
    """
    rows = await database.fetch_all(query=query, values={
        "min_lon": bbox[0], "min_lat": bbox[1], 
        "max_lon": bbox[2], "max_lat": bbox[3]
    })
    return rows_to_geojson(rows)

# 5. DROPDOWN DE ZONAS (SOLO TEXTO PLANO)
@app.get("/lista-centralidades/")
async def get_lista_zonas():
    # Solo pedimos CLAVE_2
    query = """
        SELECT DISTINCT "CLAVE_2" 
        FROM centralidad_barrial02 
        WHERE "CLAVE_2" IS NOT NULL 
        ORDER BY "CLAVE_2"
    """
    try:
        rows = await database.fetch_all(query=query)
        # Retornamos lista simple de strings
        return [r["CLAVE_2"] for r in rows]
    except Exception as e:
        print(f"Error lista zonas: {e}")
        return []

@app.get("/centralidades/")
async def get_poligono_zona(clave_2: str):
    query = """
        SELECT "NAME" as nombre, 
               "POBTOT" as pobtot,
               "POBMAS" as pobmas,
               "POBFEM" as pobfem,
               "VIVTOT" as vivtot,
               ST_AsGeoJSON(geom) as geom 
        FROM centralidad_barrial02 
        WHERE "CLAVE_2" = :clave
    """
    rows = await database.fetch_all(query=query, values={"clave": clave_2})
    return rows_to_geojson(rows)

# 6. CENSO BBOX
@app.get("/censo/")
async def get_censo_bbox(in_bbox: str = Query(None)):
    if not in_bbox: return {"type": "FeatureCollection", "features": []}
    bbox = list(map(float, in_bbox.split(',')))
    
    query = """
        SELECT cvegeo, pobtot, pobmas, pobfem, vivtot,
               ST_AsGeoJSON(wkb_geometry) as geom 
        FROM cpyv_2020
        WHERE wkb_geometry && ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
    """
    rows = await database.fetch_all(query=query, values={
        "min_lon": bbox[0], "min_lat": bbox[1], 
        "max_lon": bbox[2], "max_lat": bbox[3]
    })
    return rows_to_geojson(rows)

# 7. MIS ZONAS
@app.get("/mis_zonas/")
async def listar_mis_zonas():
    query = "SELECT id, nombre, fecha_creacion, ST_AsGeoJSON(geom) as geom FROM mis_zonas ORDER BY id DESC"
    rows = await database.fetch_all(query=query)
    return rows_to_geojson(rows)

@app.post("/mis_zonas/")
async def guardar_zona(zona: ZonaCreate):
    geom_json = json.dumps(zona.geom)
    query = """
        INSERT INTO mis_zonas (nombre, geom) 
        VALUES (:nombre, ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326))
        RETURNING id
    """
    id_nueva = await database.execute(query=query, values={"nombre": zona.nombre, "geom": geom_json})
    return {"mensaje": "Zona guardada", "id": id_nueva}

@app.delete("/mis_zonas/{id_zona}")
async def eliminar_zona(id_zona: int):
    query = "DELETE FROM mis_zonas WHERE id = :id"
    await database.execute(query=query, values={"id": id_zona})
    return {"mensaje": "Eliminada"}