import sys
import os

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Importar la aplicación FastAPI
from main import app
from mangum import Mangum

# Crear el handler de Mangum para Vercel
handler = Mangum(app, lifespan="off")

# Exportar el handler para que Vercel lo pueda usar
__all__ = ["handler"] 