import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db.connection import get_db  # Usamos la base de datos General (Pool 1)
from schemas.zonas import ZonaCreate
from services.geo_utils import rows_to_geojson

router = APIRouter(prefix="/zonas", tags=["Zonas Personalizadas"])

@router.get("/capa-referencia-centralidades/")
async def get_capa_referencia(clave: str = None, db: AsyncSession = Depends(get_db)):
    """
    Obtiene la geometría de una centralidad barrial de forma asíncrona.
    """
    if not clave:
        return {"type": "FeatureCollection", "features": []}
        
    # Cambiamos %(c)s por :c y usamos text()
    query = text("""
        SELECT "CLAVE_2", ST_AsGeoJSON(geom) as geom 
        FROM centralidad_barrial02 
        WHERE "CLAVE_2" = :c
    """)
    
    try:
        result = await db.execute(query, {"c": clave})
        rows = result.mappings().all()
        return rows_to_geojson(rows)
    except Exception as e:
        print(f"Error al obtener capa de referencia: {e}")
        return {"type": "FeatureCollection", "features": [], "error": str(e)}

@router.post("/mis_zonas/")
async def guardar_zona(zona: ZonaCreate, db: AsyncSession = Depends(get_db)):
    """
    Guarda una nueva zona dibujada por el usuario usando SQLAlchemy Async.
    """
    geom_json = json.dumps(zona.geom)
    
    # Cambiamos placeholders a formato :name
    query = text("""
        INSERT INTO mis_zonas (nombre, geom) 
        VALUES (:nombre, ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)) 
        RETURNING id
    """)
    
    params = {
        "nombre": zona.nombre, 
        "geom": geom_json
    }
    
    try:
        # Ejecutamos la inserción
        result = await db.execute(query, params)
        id_nueva = result.scalar()
        
        # IMPORTANTE: Confirmar la transacción en la base de datos General
        await db.commit()
        
        return {
            "mensaje": "Zona guardada exitosamente", 
            "id": id_nueva
        }
    except Exception as e:
        # Revertimos en caso de error para mantener la integridad
        await db.rollback()
        print(f"Error al guardar zona personalizada: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno al guardar la zona personalizada"
        )