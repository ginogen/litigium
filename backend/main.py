# Configurar el path para importar módulos del directorio padre
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv
from mangum import Mangum

# Importar todos los routers
from routes.training_routes import router as training_router
from routes.chat_routes import router as chat_router
from routes.editor_routes import router as editor_router
from routes.document_routes import router as document_router
from routes.audio_routes import router as audio_router
from routes.config_routes import router as config_router
from routes.folder_routes import router as folder_router
from routes.google_drive_routes import router as google_drive_router

load_dotenv()

# Crear la aplicación FastAPI
app = FastAPI(
    title="Legal Assistant AI Backend",
    description="Backend para el asistente legal con entrenamiento personalizado",
    version="1.0.0"
)

# Configurar CORS para producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173",
        "https://*.vercel.app",
        os.getenv("FRONTEND_URL", "")
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

# Handler para Vercel serverless
handler = Mangum(app)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_level="info"
    ) 