from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.connection import get_db_visop  # Importamos la conexión a la DB VISOP
from schemas.zonas import LoginRequest, TokenResponse
from services.auth_service import authenticate_user

router = APIRouter(tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest, 
    db: AsyncSession = Depends(get_db_visop) # Inyectamos la sesión asíncrona
):
    """
    Endpoint de autenticación asíncrono. 
    Pasa la sesión de la DB al servicio para consultar el usuario.
    """
    # Agregamos 'await' y pasamos 'db' como primer argumento
    return await authenticate_user(db, data.username, data.password)