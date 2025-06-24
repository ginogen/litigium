# 🚀 Guía de Deploy en Vercel

Esta guía te llevará paso a paso para deployar tu aplicación Legal Assistant AI en Vercel.

## 📋 Prerrequisitos

1. **Cuenta en Vercel**: Crea una cuenta gratuita en [vercel.com](https://vercel.com)
2. **Repositorio Git**: Tu código debe estar en GitHub, GitLab o Bitbucket
3. **Variables de entorno configuradas**: Todas las keys y configuraciones necesarias

## 🔧 Preparación Previa

### 1. Verificar Configuración Local

```bash
# Ejecutar el script de preparación
chmod +x deploy.sh
./deploy.sh
```

### 2. Variables de Entorno Requeridas

Necesitarás configurar estas variables en Vercel:

#### Supabase (Base de datos)
- `SUPABASE_URL`: URL de tu proyecto Supabase
- `SUPABASE_KEY`: Clave anónima de Supabase
- `SUPABASE_SERVICE_ROLE_KEY`: Clave de servicio de Supabase

#### OpenAI (Inteligencia Artificial)
- `OPENAI_API_KEY`: Tu API key de OpenAI
- `MODELO_IA`: `gpt-4o` (recomendado)
- `MODELO_IA_FALLBACK`: `gpt-4o-mini` (backup)

#### Google Drive (Integración)
- `GOOGLE_CLIENT_ID`: Client ID de Google Cloud Console
- `GOOGLE_CLIENT_SECRET`: Client Secret de Google Cloud Console
- `GOOGLE_TOKEN_ENCRYPTION_KEY`: Clave de 32 caracteres para encriptar tokens

#### Qdrant (Base de datos vectorial)
- `QDRANT_URL`: URL de tu instancia Qdrant
- `QDRANT_API_KEY`: API key de Qdrant

#### Configuración de producción
- `FRONTEND_URL`: `https://tu-app.vercel.app` (se configurará después del primer deploy)
- `NODE_ENV`: `production`
- `PYTHON_ENV`: `production`

## 🚀 Deploy en Vercel

### Opción 1: Deploy desde GitHub (Recomendado)

1. **Push tu código a GitHub**:
   ```bash
   git add .
   git commit -m "🚀 Preparado para deploy en Vercel"
   git push origin main
   ```

2. **Conectar en Vercel**:
   - Ve a [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click en "New Project"
   - Importa tu repositorio
   - Selecciona el framework: **Other**
   - Configura:
     - Build Command: `cd frontend && npm ci && npm run build`
     - Output Directory: `frontend/dist`
     - Install Command: `cd frontend && npm ci`

3. **Configurar Variables de Entorno**:
   - En el dashboard del proyecto → Settings → Environment Variables
   - Agrega todas las variables listadas arriba
   - Marca las variables sensibles como "Encrypted"

4. **Deploy**:
   - Click en "Deploy"
   - Espera 2-3 minutos
   - ¡Tu aplicación estará lista!

### Opción 2: Deploy con Vercel CLI

1. **Instalar Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Login en Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   vercel --prod
   ```

## ⚙️ Configuración Post-Deploy

### 1. Actualizar FRONTEND_URL
Después del primer deploy:
1. Copia la URL de tu aplicación (ej: `https://tu-app.vercel.app`)
2. Ve a Settings → Environment Variables
3. Actualiza `FRONTEND_URL` con tu URL real
4. Redeploy la aplicación

### 2. Configurar Google OAuth
Si usas Google Drive:
1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. En tu proyecto → APIs & Services → Credentials
3. Edita tu OAuth 2.0 Client ID
4. Agrega en "Authorized redirect URIs":
   - `https://tu-app.vercel.app/auth/google/callback`

### 3. Configurar CORS en Supabase
1. Ve a tu proyecto Supabase → Settings → API
2. En "CORS Origins" agrega:
   - `https://tu-app.vercel.app`

## 🔄 Actualizaciones Automáticas

Vercel realizará deploy automático cada vez que hagas push a la rama principal:

```bash
# Hacer cambios
git add .
git commit -m "✨ Nuevas funcionalidades"
git push origin main
# Deploy automático activado
```

## 🐛 Solución de Problemas

### Error: "Build failed"
- Verifica que todas las dependencias estén `package.json`
- Revisa los logs de build en Vercel
- Asegúrate de que el frontend se compile localmente

### Error: "Function timeout"
- Las serverless functions de Vercel tienen límite de 10s (gratis) / 60s (pro)
- Optimiza operaciones largas o considera upgrade a plan Pro

### Error: "Environment variables not found"
- Verifica que todas las variables estén configuradas en Vercel
- Los nombres deben coincidir exactamente
- Variables sensibles deben marcarse como "Encrypted"

### Error 404 en rutas del frontend
- Verifica que `vercel.json` tenga las rutas correctas
- El archivo está configurado para manejar SPA routing

## 📊 Monitoreo

### Logs en Tiempo Real
```bash
vercel logs tu-app.vercel.app
```

### Metrics Dashboard
- Ve a tu dashboard de Vercel
- Revisa métricas de performance
- Monitorea errores y usage

## 💰 Costos Estimados

### Plan Hobby (Gratis)
- ✅ 100GB bandwidth
- ✅ Deploys ilimitados
- ⚠️ Serverless functions: 10s timeout
- ⚠️ 12 deploys por hora

### Plan Pro ($20/mes)
- ✅ 1TB bandwidth
- ✅ 60s timeout functions
- ✅ Deploy hooks
- ✅ Soporte prioritario

## 🎉 ¡Deploy Exitoso!

Tu aplicación Legal Assistant AI debería estar corriendo en:
`https://tu-app.vercel.app`

### Funcionalidades Verificadas ✅
- ✅ Frontend React cargando
- ✅ API Backend respondiendo
- ✅ Autenticación con Supabase
- ✅ Base de datos funcionando
- ✅ Integración con OpenAI
- ✅ Google Drive (si configurado)
- ✅ Vectorización con Qdrant

---

## 🆘 Soporte

Si tienes problemas:
1. Revisa los logs en Vercel Dashboard
2. Verifica variables de entorno
3. Consulta esta documentación
4. Revisa la [documentación oficial de Vercel](https://vercel.com/docs) 