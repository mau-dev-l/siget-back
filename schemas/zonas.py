from typing import Any, Dict
from pydantic import BaseModel

class ZonaCreate(BaseModel):
    nombre: str
    geom: dict


class ObraNueva(BaseModel):
    colonia: str
    nombre_obra: str
    num_aprobacion: str
    geometry: Dict[str, Any]

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class CommentCreate(BaseModel):
    feature_id: str
    content: str