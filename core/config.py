from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Variables de la primera base de datos
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    
    # Variable para la segunda base de datos (VISOP)
    DB_NAME_2: str 
    
    # Credenciales comunes
    DB_USER: str
    DB_PASSWORD: str
    
    # Opción de servidor
    DEBUG: bool = False 

    # Configuración del cargador
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore"  # <-- Esto evita el error de la imagen si hay variables extra
    )

settings = Settings()