from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import geografia, zonas
from db.connection import pg_pool

app = FastAPI(title="API OVIE Tuxtla 2026", root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluimos los módulos de rutas
app.include_router(geografia.router)
app.include_router(zonas.router)

@app.on_event("startup")
def startup():
    if pg_pool: print(" Servidor OVIE iniciado correctamente")

@app.on_event("shutdown")
def shutdown():
    if pg_pool:
        pg_pool.closeall()
        print("Conexiones cerradas")