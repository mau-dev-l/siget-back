from pydantic_settings import BaseSettings
from pathlib import Path
#install pydantic-settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# pydantic nos permite gestionar la configuración de la aplicación de manera sencilla y segura.

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_NAME_2: str
    DB_USER: str
    DB_PASSWORD: str

    class Config:
        env_file = ".env"

settings = Settings()
