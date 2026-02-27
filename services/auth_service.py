from models.user_model import get_user_by_username
from core.security import verify_password, create_access_token
from fastapi import HTTPException


def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)

    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

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