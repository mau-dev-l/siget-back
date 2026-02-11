from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Importamos los routers con alias para evitar colisiones
from routers.geografia import router as geografia_router
from routers.zonas import router as zonas_router
from routers.visop_geo import router as visop_router
# Importamos AMBOS pools para cerrarlos correctamente
from db.connection import pg_pool, pg_pool2 

app = FastAPI(title="API OVIE Tuxtla 2026", root_path="/api")

# --- CONFIGURACIÓN CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTRO DE RUTAS ---
app.include_router(geografia_router)
app.include_router(zonas_router)
app.include_router(visop_router) 

@app.on_event("startup")
def startup():
    # Verificamos que ambos pools estén activos
    if pg_pool and pg_pool2: 
        print("🚀 Servidor OVIE iniciado correctamente con doble Pool de conexiones")

@app.on_event("shutdown")
def shutdown():
    """
    IMPORTANTE: Cerramos ambos pools al apagar el servicio para liberar 
    recursos en el servidor de base de datos.
    """
    if pg_pool:
        pg_pool.closeall()
    if pg_pool2:
        pg_pool2.closeall()
    print("🔒 Conexiones de ambas bases de datos cerradas exitosamente")

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API OVIE Tuxtla 2026"}