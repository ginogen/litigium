#!/bin/bash

echo "🚀 Starting Legal Assistant AI Backend..."

# Verificar que uvicorn esté disponible
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn no encontrado, intentando con python -m uvicorn"
    python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
else
    echo "✅ uvicorn encontrado, iniciando normalmente"
    uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
fi 