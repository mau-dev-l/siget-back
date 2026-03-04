from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.connection import get_db_visop  # Conexión a la base de datos VISOP
from schemas.zonas import CommentCreate
from services.comment_service import add_comment, list_comments

router = APIRouter(prefix="/comentarios", tags=["comentarios"])

@router.post("/")
async def create_comment_endpoint(
    data: CommentCreate, 
    db: AsyncSession = Depends(get_db_visop)
):
    """
    Crea un nuevo comentario en la base de datos VISOP.
    """
    # Pasamos la sesión db al service y usamos await
    return await add_comment(
        db=db,
        feature_id=data.feature_id,
        content=data.content
    )

@router.get("/{feature_id}")
async def get_comments(
    feature_id: str, 
    db: AsyncSession = Depends(get_db_visop)
):
    """
    Lista los comentarios asociados a un feature desde la base de datos VISOP.
    """
    # Llamada asíncrona al service
    return await list_comments(db=db, feature_id=feature_id)