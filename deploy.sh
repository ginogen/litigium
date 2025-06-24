#!/bin/bash

echo "🚀 Preparando deploy para Vercel..."

# Verificar que estamos en la rama correcta
echo "📋 Verificando rama actual..."
BRANCH=$(git branch --show-current)
echo "Rama actual: $BRANCH"

# Limpiar builds anteriores
echo "🧹 Limpiando builds anteriores..."
rm -rf frontend/dist/
rm -rf frontend/build/

# Instalar dependencias del frontend
echo "📦 Instalando dependencias del frontend..."
cd frontend
npm ci

# Build del frontend
echo "🔨 Construyendo frontend..."
npm run build

# Volver al directorio raíz
cd ..

# Verificar que existe el build
if [ ! -d "frontend/dist" ]; then
    echo "❌ Error: No se pudo generar el build del frontend"
    exit 1
fi

echo "✅ Build generado exitosamente en frontend/dist/"

# Verificar archivos de configuración de Vercel
if [ ! -f "vercel.json" ]; then
    echo "❌ Error: Falta archivo vercel.json"
    exit 1
fi

if [ ! -f "package.json" ]; then
    echo "❌ Error: Falta package.json raíz"
    exit 1
fi

echo "✅ Archivos de configuración de Vercel presentes"

# Verificar variables de entorno (opcional)
echo "⚠️  Recuerda configurar las variables de entorno en Vercel:"
echo "   - SUPABASE_URL"
echo "   - SUPABASE_KEY"
echo "   - SUPABASE_SERVICE_ROLE_KEY"
echo "   - OPENAI_API_KEY"
echo "   - GOOGLE_CLIENT_ID"
echo "   - GOOGLE_CLIENT_SECRET"
echo "   - GOOGLE_TOKEN_ENCRYPTION_KEY"
echo "   - QDRANT_URL"
echo "   - QDRANT_API_KEY"
echo "   - FRONTEND_URL"

echo ""
echo "🎉 ¡Aplicación lista para deploy!"
echo ""
echo "📝 Próximos pasos:"
echo "1. Hacer push de los cambios a tu repositorio"
echo "2. Conectar el repositorio en Vercel"
echo "3. Configurar las variables de entorno en Vercel"
echo "4. Deploy automático!"
echo ""
echo "🔗 Comando Vercel CLI (opcional):"
echo "   vercel --prod" 