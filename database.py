import os
from databases import Database
from dotenv import load_dotenv

# 1. Cargar las variables del archivo .env
load_dotenv()

# 2. Leer la dirección de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")

# 3. Crear la instancia de conexión
database = Database(DATABASE_URL)