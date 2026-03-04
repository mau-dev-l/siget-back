from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Importamos los routers (ya convertidos a async)
from routers.geografia import router as geografia_router
from routers.zonas import router as zonas_router
from routers.visop_geo import router as visop_router
from routers.auth_router import router as auth_router
from routers.comment_router import router as comment_router
# Importamos los engines para monitorear el inicio
from db.connection import engine1, engine2 

app = FastAPI(title="API OVIE Tuxtla 2026", root_path="/api")

# --- CONFIGURACIÓN CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTRO DE RUTAS ---
app.include_router(geografia_router)
app.include_router(zonas_router)
app.include_router(visop_router) 
app.include_router(auth_router)
app.include_router(comment_router)

@app.on_event("startup")
async def startup():
    # En SQLAlchemy Async, los engines se inicializan al primer uso, 
    # pero podemos verificar la configuración aquí.
    print("Servidor OVIE 2026 iniciado en modo ASYNC con SQLAlchemy + asyncpg")

@app.on_event("shutdown")
async def shutdown():
    """
    Cerramos los engines asíncronos para asegurar que no queden 
    conexiones colgadas en PostgreSQL.
    """
    await engine1.dispose()
    await engine2.dispose()
    print("Motores de base de datos General y VISOP cerrados correctamente")

@app.get("/")
async def read_root():
    return {"message": "Bienvenido a la API OVIE Tuxtla 2026 (Versión Asíncrona)"}