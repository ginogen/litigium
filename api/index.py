import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from main import app
    from mangum import Mangum
    
    # Crear el handler de Mangum para Vercel
    handler = Mangum(app, lifespan="off")
    
except ImportError as e:
    print(f"Error importing: {e}")
    # Fallback simple para debugging
    from fastapi import FastAPI
    
    app = FastAPI()
    
    @app.get("/")
    def read_root():
        return {"Hello": "World", "error": str(e)}
    
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")

# Exportar el handler para que Vercel lo pueda usar
__all__ = ["handler"] 