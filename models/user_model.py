from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_by_username(db: AsyncSession, username: str):
    query = text("""
        SELECT id, username, password, role
        FROM users
        WHERE username = :username
        LIMIT 1
    """)
    
    result = await db.execute(query, {"username": username})
    
    # .mappings().first() devuelve un diccionario o None si no existe
    return result.mappings().first()