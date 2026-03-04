from fastapi import APIRouter, HTTPException, Depends
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db.connection import get_db_visop  # Conexión a la base VISOP
from schemas.zonas import ObraNueva

router = APIRouter(prefix="/visop", tags=["Capas Geográficas"])

@router.get("/estadisticas/obras")
async def get_estadisticas(db: AsyncSession = Depends(get_db_visop)):
    """
    Obtiene el conteo de obras agrupadas por tipo para los años 2023, 2024 y 2025 de forma asíncrona.
    """
    queries = {
        "anio_2025": 'SELECT tipo_proy AS label, COUNT(*) AS total FROM faismun_2025 GROUP BY tipo_proy ORDER BY total DESC;',
        "anio_2024": 'SELECT tipo AS label, COUNT(*) AS total FROM faismun_2024_geo GROUP BY tipo ORDER BY total DESC;',
        "anio_2023": 'SELECT tipo AS label, COUNT(*) AS total FROM faismun_2023_geo GROUP BY tipo ORDER BY total DESC;'
    }
    
    resultados = {}
    
    try:
        for anio, sql in queries.items():
            # Ejecución asíncrona de cada consulta
            result = await db.execute(text(sql))
            rows = result.mappings().all()
            
            # Mapeo de resultados compatible con tu lógica anterior
            resultados[anio] = [
                {"label": r["label"] or "Sin Clasificar", "value": r["total"]} 
                for r in rows
            ]
            
        return resultados
    except Exception as e:
        print(f"Error crítico en estadísticas: {e}")
        return {"anio_2025": [], "anio_2024": [], "anio_2023": []}

@router.post("/obras/crear")
async def crear_obra(obra: ObraNueva, db: AsyncSession = Depends(get_db_visop)):
    """
    Registra una nueva obra en la base de datos de VISOP usando SQLAlchemy Async.
    """
    # Cambiamos placeholders %(nombre)s por :nombre
    sql = text("""
        INSERT INTO faismun_2024_geo (obra_accio, no_aprobac, colonia, geom)
        VALUES (:nombre, :num, :col, ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326))
        RETURNING id;
    """)
    
    params = {
        "nombre": obra.nombre_obra,
        "num": obra.num_aprobacion,
        "col": obra.colonia,
        "geom": json.dumps(obra.geometry)
    }
    
    try:
        # Ejecución y obtención del ID retornado
        result = await db.execute(sql, params)
        nuevo_id = result.scalar()
        
        # IMPORTANTE: En SQLAlchemy Async debemos hacer commit explícito
        await db.commit()
        
        return {"status": "ok", "id": nuevo_id, "mensaje": "Obra registrada correctamente"}
    except Exception as e:
        # En caso de error, hacemos rollback para limpiar la transacción
        await db.rollback()
        print(f"Error al insertar obra: {e}")
        raise HTTPException(status_code=500, detail="Error interno al guardar la obra")