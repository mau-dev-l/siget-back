from fastapi import APIRouter
from pydantic import BaseModel
from services.auth_service import authenticate_user

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    return authenticate_user(data.username, data.password)