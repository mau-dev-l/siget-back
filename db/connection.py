from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from core.config import settings

# 1. Definición de las URLs de conexión (Usando asyncpg)
# Formato: postgresql+asyncpg://user:pass@host:port/dbname
DATABASE_URL_1 = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
DATABASE_URL_2 = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME_2}"

# 2. Creación de los Engines Asíncronos
# SQLAlchemy maneja internamente el pooling de conexiones (sustituye a ThreadedConnectionPool)
engine1 = create_async_engine(DATABASE_URL_1, echo=False, pool_size=5, max_overflow=10)
engine2 = create_async_engine(DATABASE_URL_2, echo=False, pool_size=5, max_overflow=10)

# 3. Creadores de Sesiones
AsyncSessionLocal1 = async_sessionmaker(bind=engine1, class_=AsyncSession, expire_on_commit=False)
AsyncSessionLocal2 = async_sessionmaker(bind=engine2, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# --- NUEVAS FUNCIONES DE GESTIÓN (Dependencias para FastAPI) ---

async def get_db():
    """Dependencia para la Base de Datos General (Pool 1)"""
    async with AsyncSessionLocal1() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_db_visop():
    """Dependencia para la Base de Datos VISOP (Pool 2)"""
    async with AsyncSessionLocal2() as session:
        try:
            yield session
        finally:
            await session.close()

# Nota: Las funciones execute_read_query y execute_write_query se vuelven obsoletas.
# Ahora la lógica de ejecución se mueve a los archivos en /services/ usando la sesión inyectada.