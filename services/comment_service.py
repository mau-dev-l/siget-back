from models.comment_model import create_comment, get_comments_by_feature
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

async def add_comment(db: AsyncSession, feature_id: str, content: str):
    if not content.strip():
        raise HTTPException(status_code=400, detail="Comentario vacío")

    # El modelo ahora debe ser asíncrono
    comment_id = await create_comment(db, feature_id, content)

    return {
        "message": "Comentario guardado",
        "comment_id": comment_id
    }

async def list_comments(db: AsyncSession, feature_id: str):
    # Retornamos los comentarios de forma asíncrona
    return await get_comments_by_feature(db, feature_id)