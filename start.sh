#!/bin/bash

echo "🚀 Starting Legal Assistant AI Backend..."

# Activar entorno virtual
if [ -d "venv" ]; then
    echo "✅ Activando entorno virtual..."
    source venv/bin/activate
fi

# Verificar que uvicorn esté disponible
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn no encontrado, intentando con python -m uvicorn"
    exec python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
else
    echo "✅ uvicorn encontrado, iniciando aplicación"
    exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} 