# backend/run_local.py
import sys
import os
from pathlib import Path

# Configurar el path correctamente
backend_dir = Path(__file__).parent
parent_dir = backend_dir.parent

# Agregar ambos directorios al path
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(backend_dir))

# Simular que estamos ejecutando como un paquete
sys.modules['backend'] = type(sys)('backend')
sys.modules['backend.routes'] = type(sys)('backend.routes')

# Ahora importar la aplicación
from main import app
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"�� Iniciando servidor en http://localhost:{port}")
    print(f"�� Documentación API: http://localhost:{port}/docs")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_level="info"
    )