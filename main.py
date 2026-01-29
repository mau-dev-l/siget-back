import json
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# Importamos las nuevas funciones del database.py
from database import execute_read_query, execute_read_one, execute_write_query, pg_pool

app = FastAPI(title="API OVIE Tuxtla 2026", root_path="/api")

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
    # Como usamos RealDictCursor en database.py, 'row' se comporta igual que antes
    for row in rows:
        row_dict = dict(row) 
        # Convertir GeoJSON string a dict si viene como string desde la BD
        if geom_col in row_dict and isinstance(row_dict[geom_col], str):
            geometry = json.loads(row_dict.pop(geom_col))
        elif geom_col in row_dict:
            geometry = row_dict.pop(geom_col)
        else:
            geometry = None

        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": row_dict,
            "id": row_dict.get("id") or row_dict.get("gid")
        })
    return {"type": "FeatureCollection", "features": features}

# --- EVENTOS ---
@app.on_event("startup")
def startup():
    # El pool ya se crea al importar database, pero verificamos
    if pg_pool:
        print("✅ Sistema iniciado con Pool PostgreSQL (Psycopg2)")

@app.on_event("shutdown")
def shutdown():
    if pg_pool:
        pg_pool.closeall()
        print("🔒 Conexiones a BD cerradas")

# ================= RUTAS DEL SISTEMA =================
# NOTA: Cambiamos 'async def' a 'def' para que FastAPI maneje 
# las consultas bloqueantes de psycopg2 en un hilo separado.

# 1. INFO AL CLIC
@app.get("/info-manzana/")
def obtener_info_manzana(lat: float, lon: float):
    query = """
        SELECT cvegeo, pobtot, vivtot, pobfem, pobmas 
        FROM cpyv_2020 
        WHERE ST_Contains(wkb_geometry, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326))
    """
    # Nota el cambio de :lon a %(lon)s para psycopg2
    resultado = execute_read_one(query=query, params={"lat": lat, "lon": lon})
    
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
def get_colonias():
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
        rows = execute_read_query(query=query)
        return rows_to_geojson(rows)
    except Exception as e:
        print(f"Error Colonias: {e}")
        return {"type": "FeatureCollection", "features": []}

# 3. VIALIDADES
@app.get("/vialidades/")
def get_vialidades(in_bbox: str = Query(None)):
    if not in_bbox: return {"type": "FeatureCollection", "features": []}
    bbox = list(map(float, in_bbox.split(',')))
    
    query = """
        SELECT "NOMVIAL" as nom_vial, 
               ST_AsGeoJSON(geom) as geom
        FROM "VIALIDADES_TUXTLA_UTM"
        WHERE geom && ST_MakeEnvelope(%(min_lon)s, %(min_lat)s, %(max_lon)s, %(max_lat)s, 4326)
        LIMIT 1000
    """
    try:
        rows = execute_read_query(query=query, params={
            "min_lon": bbox[0], "min_lat": bbox[1], 
            "max_lon": bbox[2], "max_lat": bbox[3]
        })
        return rows_to_geojson(rows)
    except Exception as e:
        return {"type": "FeatureCollection", "features": []}

# 4. NEGOCIOS
@app.get("/denue/")
def get_denue(in_bbox: str = Query(None)):
    if not in_bbox: return {"type": "FeatureCollection", "features": []}
    bbox = list(map(float, in_bbox.split(',')))
    
    query = """
        SELECT id, nom_estab, codigo_act, nombre_act, 
               ST_AsGeoJSON(geom) as geom
        FROM denue_tuxtla_cb_2026 
        WHERE geom && ST_MakeEnvelope(%(min_lon)s, %(min_lat)s, %(max_lon)s, %(max_lat)s, 4326)
        LIMIT 50000
    """
    rows = execute_read_query(query=query, params={
        "min_lon": bbox[0], "min_lat": bbox[1], 
        "max_lon": bbox[2], "max_lat": bbox[3]
    })
    return rows_to_geojson(rows)

# 5. DROPDOWN DE ZONAS
@app.get("/lista-centralidades/")
def get_lista_zonas():
    query = """
        SELECT DISTINCT "CLAVE_2" 
        FROM centralidad_barrial02 
        WHERE "CLAVE_2" IS NOT NULL 
        ORDER BY "CLAVE_2"
    """
    try:
        rows = execute_read_query(query=query)
        return [r["CLAVE_2"] for r in rows]
    except Exception as e:
        print(f"Error lista zonas: {e}")
        return []

@app.get("/centralidades/")
def get_poligono_zona(clave_2: str):
    query = """
        SELECT "NAME" as nombre, 
               "POBTOT" as pobtot,
               "POBMAS" as pobmas,
               "POBFEM" as pobfem,
               "VIVTOT" as vivtot,
               ST_AsGeoJSON(geom) as geom 
        FROM centralidad_barrial02 
        WHERE "CLAVE_2" = %(clave)s
    """
    rows = execute_read_query(query=query, params={"clave": clave_2})
    return rows_to_geojson(rows)

# 6. CENSO BBOX
@app.get("/censo/")
def get_censo_bbox(in_bbox: str = Query(None)):
    if not in_bbox: return {"type": "FeatureCollection", "features": []}
    bbox = list(map(float, in_bbox.split(',')))
    
    query = """
        SELECT cvegeo, pobtot, pobmas, pobfem, vivtot,
               ST_AsGeoJSON(wkb_geometry) as geom 
        FROM cpyv_2020
        WHERE wkb_geometry && ST_MakeEnvelope(%(min_lon)s, %(min_lat)s, %(max_lon)s, %(max_lat)s, 4326)
    """
    rows = execute_read_query(query=query, params={
        "min_lon": bbox[0], "min_lat": bbox[1], 
        "max_lon": bbox[2], "max_lat": bbox[3]
    })
    return rows_to_geojson(rows)

# 7. MIS ZONAS
@app.get("/mis_zonas/")
def listar_mis_zonas():
    query = "SELECT id, nombre, fecha_creacion, ST_AsGeoJSON(geom) as geom FROM mis_zonas ORDER BY id DESC"
    rows = execute_read_query(query=query)
    return rows_to_geojson(rows)

@app.post("/mis_zonas/")
def guardar_zona(zona: ZonaCreate):
    geom_json = json.dumps(zona.geom)
    query = """
        INSERT INTO mis_zonas (nombre, geom) 
        VALUES (%(nombre)s, ST_SetSRID(ST_GeomFromGeoJSON(%(geom)s), 4326))
        RETURNING id
    """
    # execute_write_query se encarga del commit
    id_nueva = execute_write_query(query=query, params={"nombre": zona.nombre, "geom": geom_json})
    return {"mensaje": "Zona guardada", "id": id_nueva}

@app.delete("/mis_zonas/{id_zona}")
def eliminar_zona(id_zona: int):
    query = "DELETE FROM mis_zonas WHERE id = %(id)s"
    execute_write_query(query=query, params={"id": id_zona})
    return {"mensaje": "Eliminada"}

@app.get("/capa-referencia-centralidades/")
def get_todas_centralidades():
    query = """
        SELECT "CLAVE_2", ST_AsGeoJSON(geom) as geom 
        FROM centralidad_barrial02
    """
    rows = execute_read_query(query=query)
    return rows_to_geojson(rows)