# Configurar el path para importar módulos del directorio padre
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv

# Import condicional de Mangum (solo para Vercel/Lambda)
try:
    from mangum import Mangum
    MANGUM_AVAILABLE = True
except ImportError:
    MANGUM_AVAILABLE = False
    print("ℹ️  Mangum no disponible - OK para Railway/local deployment")

# Importar todos los routers
from .routes.training_routes import router as training_router
from .routes.chat_routes import router as chat_router
from .routes.editor_routes import router as editor_router
from .routes.document_routes import router as document_router
from .routes.audio_routes import router as audio_router
from .routes.config_routes import router as config_router
from .routes.folder_routes import router as folder_router
from .routes.google_drive_routes import router as google_drive_router

load_dotenv()

# Crear la aplicación FastAPI
app = FastAPI(
    title="Legal Assistant AI Backend",
    description="Backend para el asistente legal con entrenamiento personalizado",
    version="1.0.0"
)

# Configurar CORS para Railway
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173",
        "https://*.vercel.app",
        "https://*.railway.app",
        "https://*.up.railway.app",
        os.getenv("FRONTEND_URL", ""),
        os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar todos los routers
app.include_router(config_router)      # Configuración y sistema
app.include_router(chat_router)        # Chat e IA  
app.include_router(editor_router)      # Editor granular
app.include_router(document_router)    # Gestión de documentos
app.include_router(audio_router)       # Procesamiento de audio
app.include_router(training_router)    # Entrenamiento personalizado
app.include_router(folder_router)      # Gestión de carpetas
app.include_router(google_drive_router)  # Integración Google Drive

# Configuración para servir el frontend estático (Railway)
frontend_dist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

# Solo montar archivos estáticos si el directorio existe (en producción)
if os.path.exists(frontend_dist_path):
    # Servir archivos estáticos del frontend
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="assets")
    
    # Ruta catch-all para servir el frontend SPA
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        # Si es una ruta de API, no interceptar
        if path.startswith("api/") or path.startswith("health"):
            return JSONResponse({"error": "API route not found"}, status_code=404)
        
        # Intentar servir archivo específico primero
        file_path = os.path.join(frontend_dist_path, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Si no existe, servir index.html (SPA routing)
        return FileResponse(os.path.join(frontend_dist_path, "index.html"))

# Ruta de salud
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Legal Assistant AI Backend is running"}

# Manejador de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error interno del servidor: {str(exc)}"}
    )

# Handler para Vercel serverless (solo si Mangum está disponible)
if MANGUM_AVAILABLE:
    handler = Mangum(app)
    print("✅ Mangum handler creado para Vercel/Lambda")
else:
    print("ℹ️  Sin Mangum handler - deployment para Railway/uvicorn")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_level="info"
    ) 