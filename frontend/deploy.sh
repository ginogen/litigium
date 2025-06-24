#!/bin/bash

# Script de deploy del frontend en Railway
# Uso: ./deploy.sh [backend-url]

set -e

echo "🚂 Deploying Frontend to Railway..."

# Verificar si estamos en el directorio correcto
if [ ! -f "package.json" ]; then
    echo "❌ Error: Este script debe ejecutarse desde el directorio frontend/"
    exit 1
fi

# Verificar si Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo "❌ Error: Railway CLI no está instalado"
    echo "Instala con: npm install -g @railway/cli"
    exit 1
fi

# URL del backend (parámetro opcional)
BACKEND_URL=${1:-""}

if [ -n "$BACKEND_URL" ]; then
    echo "🔧 Configurando URL del backend: $BACKEND_URL"
    railway variables set VITE_API_URL="$BACKEND_URL"
fi

# Instalar dependencias
echo "📦 Instalando dependencias..."
npm ci

# Build de producción
echo "🏗️  Construyendo aplicación..."
npm run build

# Verificar que el build fue exitoso
if [ -d "dist" ]; then
    echo "✅ Build completado exitosamente"
else
    echo "❌ Error: Build falló"
    exit 1
fi

# Deploy en Railway
echo "🚀 Desplegando en Railway..."
railway up

echo "✅ Deploy completado!"
echo "📍 Verifica el estado en: https://railway.app"

# Abrir la aplicación (opcional)
read -p "¿Abrir la aplicación en el navegador? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    railway open
fi 