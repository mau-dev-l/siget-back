from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def create_comment(db: AsyncSession, feature_id: str, content: str):
    # Cambiamos la sintaxis de %(var)s a :var (estándar de SQLAlchemy)
    query = text("""
        INSERT INTO comments (feature_id, content)
        VALUES (:feature_id, :content)
        RETURNING id;
    """)

    result = await db.execute(query, {
        "feature_id": feature_id,
        "content": content
    })
    
    # Confirmamos los cambios en la DB
    await db.commit()
    
    # Obtenemos el ID retornado
    return result.scalar()

async def get_comments_by_feature(db: AsyncSession, feature_id: str):
    query = text("""
        SELECT id, content, created_at
        FROM comments
        WHERE feature_id = :feature_id
        ORDER BY created_at DESC;
    """)

    result = await db.execute(query, {"feature_id": feature_id})
    
    # .mappings().all() emula el comportamiento de RealDictCursor (lista de dicts)
    return result.mappings().all()