from models.user_model import get_user_by_username
from core.security import verify_password, create_access_token
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

async def authenticate_user(db: AsyncSession, username: str, password: str):
    # Ahora invocamos la función del modelo con await
    user = await get_user_by_username(db, username)

    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Si usabas RealDictCursor, SQLAlchemy devuelve objetos similares a diccionarios (mappings)
    if not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = create_access_token({
        "sub": str(user["id"]),
        "role": user["role"]
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }