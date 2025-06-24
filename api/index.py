import sys
import os

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Importar la aplicación FastAPI
from main import handler

# Vercel buscará la función 'handler' por defecto
def handler_func(request):
    return handler(request, {})

# También exportar como app para compatibilidad
from main import app 