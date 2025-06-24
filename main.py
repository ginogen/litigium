#!/usr/bin/env python3
"""
Punto de entrada principal para Railway
Este archivo ayuda a Railway a detectar que es un proyecto Python
"""

# Re-exportar la app desde backend
from backend.main import app

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    ) 