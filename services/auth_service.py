from models.user_model import get_user_by_username
from core.security import verify_password, create_access_token
from fastapi import HTTPException

def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    user_id, username_db, hashed_password, role = user

    if not verify_password(password, hashed_password):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    token = create_access_token({
        "sub": str(user_id),
        "role": role
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }