from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.geografia import router as geografia_router
from routers.zonas import router as zonas_router
from routers.visop_geo import router as visop_router
from db.connection import pg_pool

app = FastAPI(title="API OVIE Tuxtla 2026", root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
#Tu primer commit en GitHub
# Incluimos los módulos de rutas
app.include_router(geografia_router)
app.include_router(zonas_router)
app.include_router(visop_router)  # Asegúrate de importar este módulo correctamente

@app.on_event("startup")
def startup():
    if pg_pool: print(" Servidor OVIE iniciado correctamente")

@app.on_event("shutdown")
def shutdown():
    if pg_pool:
        pg_pool.closeall()
        print("Conexiones cerradas")

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API OVIE Tuxtla 2026"}
