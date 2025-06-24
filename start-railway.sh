#!/bin/bash

echo "🚀 Starting Legal Assistant AI Backend on Railway..."

# Verificar versiones disponibles de Python
echo "🔍 Checking Python versions..."
python3 --version 2>/dev/null && echo "✅ python3 available" || echo "❌ python3 not found"
python --version 2>/dev/null && echo "✅ python available" || echo "❌ python not found"

# Intentar con python3 primero
if command -v python3 &> /dev/null; then
    echo "✅ Using python3"
    python3 -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
elif command -v python &> /dev/null; then
    echo "✅ Using python"
    python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
else
    echo "❌ No Python interpreter found!"
    exit 1
fi 