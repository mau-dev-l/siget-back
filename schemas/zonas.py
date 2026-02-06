from pydantic import BaseModel

class ZonaCreate(BaseModel):
    nombre: str
    geom: dict