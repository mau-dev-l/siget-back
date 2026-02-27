from fastapi import APIRouter
from pydantic import BaseModel
from services.auth_service import authenticate_user

router = APIRouter(prefix="/api", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(data: LoginRequest):
    return authenticate_user(data.username, data.password)