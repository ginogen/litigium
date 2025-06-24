#!/usr/bin/env python3
"""
Aplicación FastAPI - Legal Assistant AI
Este archivo sirve como punto de entrada alternativo
"""

from backend.main import app

# Re-exportar para importación directa
__all__ = ['app']

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 