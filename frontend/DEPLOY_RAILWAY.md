# 🚂 Deploy del Frontend en Railway

## Pasos para deployar el frontend

### 1. Crear nuevo servicio en Railway
1. Ve a [railway.app](https://railway.app)
2. Entra a tu proyecto existente
3. Haz click en "Add Service" → "GitHub Repository"
4. Selecciona el repositorio y configura:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm ci && npm run build`
   - **Start Command**: `npm run preview -- --host 0.0.0.0 --port $PORT`

### 2. Configurar variables de entorno

En el dashboard de Railway, ve a la sección "Variables" y agrega:

```bash
# URL del backend (reemplaza con tu URL real)
VITE_API_URL=https://tu-backend.up.railway.app

# Supabase (si usas autenticación)
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here

# Environment
VITE_NODE_ENV=production
NODE_ENV=production
```

### 3. Obtener URL del backend

Para obtener la URL de tu backend:
1. Ve al servicio del backend en Railway
2. En la pestaña "Settings", copia la URL del dominio público
3. Úsala como valor para `VITE_API_URL`

### 4. Deploy

Una vez configuradas las variables:
1. Haz push de tus cambios
2. Railway automáticamente detectará el cambio y hará el deploy
3. El proceso tardará unos minutos

### 5. Verificar el deploy

1. Ve a la URL de tu frontend en Railway
2. Verifica que se conecte correctamente al backend
3. Prueba la funcionalidad de login/registro

## Comandos útiles de Railway CLI

```bash
# Ver logs del frontend
railway logs --service=frontend

# Abrir el frontend en el navegador
railway open --service=frontend

# Ver variables de entorno
railway variables --service=frontend

# Conectar a la instancia
railway shell --service=frontend
```

## Solución de problemas

### Error de CORS
Si ves errores de CORS, verifica que:
1. El backend tenga configurado el dominio del frontend en CORS
2. Las URLs en `VITE_API_URL` sean correctas

### Error 404 en rutas
Si las rutas del SPA no funcionan:
1. Verifica que existe el archivo `public/_redirects`
2. El contenido debe ser: `/* /index.html 200`

### Error de conexión a la API
1. Verifica que `VITE_API_URL` apunte al backend correcto
2. Asegúrate que el backend esté funcionando
3. Revisa los logs de ambos servicios

## Arquitectura final

```
┌─────────────────┐     HTTPS     ┌─────────────────┐
│   Frontend      │ ────────────► │    Backend      │
│   (React/Vite)  │               │   (FastAPI)     │
│                 │               │                 │
│ Railway Service │               │ Railway Service │
└─────────────────┘               └─────────────────┘
        │                                 │
        │                                 │
        ▼                                 ▼
┌─────────────────┐               ┌─────────────────┐
│   Supabase      │               │    Qdrant       │
│ (Auth + Data)   │               │   (Vector DB)   │
└─────────────────┘               └─────────────────┘
``` 