# 🚂 Deployment en Railway

Esta guía te ayudará a deployar tu aplicación Legal Assistant AI en Railway.

## ¿Por qué Railway?

- ✅ **Fullstack nativo**: Maneja FastAPI + React sin configuraciones complejas
- ✅ **PostgreSQL incluido**: Base de datos integrada
- ✅ **Variables de entorno fáciles**: Configuración intuitiva
- ✅ **Logs en tiempo real**: Debugging más sencillo
- ✅ **Deploy automático**: Git push = deploy automático

## 🚀 Pasos para Deploy

### 1. Instalar Railway CLI

```bash
# Instalar Railway CLI globalmente
npm install -g @railway/cli

# O con curl
curl -fsSL https://railway.app/install.sh | sh
```

### 2. Login en Railway

```bash
railway login
```

### 3. Crear nuevo proyecto

```bash
# En el directorio raíz de tu proyecto
railway init

# Seleccionar "Empty Project"
# Nombrar tu proyecto (ej: "legal-assistant-ai")
```

### 4. Configurar variables de entorno

#### Opción A: CLI (recomendado)
```bash
# Variables requeridas
railway variables set OPENAI_API_KEY="tu_api_key_aqui"
railway variables set SUPABASE_URL="tu_supabase_url"
railway variables set SUPABASE_ANON_KEY="tu_supabase_anon_key"
railway variables set SUPABASE_SERVICE_ROLE_KEY="tu_service_role_key"

# Variables opcionales
railway variables set QDRANT_URL="tu_qdrant_url"
railway variables set QDRANT_API_KEY="tu_qdrant_api_key"
railway variables set GOOGLE_CLIENT_ID="tu_google_client_id"
railway variables set GOOGLE_CLIENT_SECRET="tu_google_client_secret"

# Variables del sistema
railway variables set NODE_ENV="production"
railway variables set PYTHONPATH="."
```

#### Opción B: Dashboard web
1. Ve a tu proyecto en [railway.app](https://railway.app)
2. Ve a la pestaña "Variables"
3. Agrega las variables una por una

### 5. Configurar base de datos (opcional)

Si necesitas PostgreSQL:

```bash
# Agregar PostgreSQL a tu proyecto
railway add postgresql

# Railway automáticamente creará DATABASE_URL
```

### 6. Deploy

```bash
# Deploy inicial
railway up

# O conectar a repo existente
railway link
git push origin main  # Deploy automático en cada push
```

## 📝 Variables de Entorno Requeridas

Copia las variables de `railway.env.example` y configúralas en Railway:

### Obligatorias:
- `OPENAI_API_KEY`: Tu API key de OpenAI
- `SUPABASE_URL`: URL de tu proyecto Supabase
- `SUPABASE_ANON_KEY`: Clave anónima de Supabase
- `SUPABASE_SERVICE_ROLE_KEY`: Clave de service role de Supabase

### Opcionales:
- `QDRANT_URL`: Para búsqueda vectorial
- `QDRANT_API_KEY`: API key de Qdrant
- `GOOGLE_CLIENT_ID`: Para integración con Google Drive
- `GOOGLE_CLIENT_SECRET`: Secret de Google Drive

## 🔧 Comandos Útiles

```bash
# Ver logs en tiempo real
railway logs

# Ver estado del deploy
railway status

# Abrir la aplicación en el navegador
railway open

# Ver todas las variables
railway variables

# Conectar a la base de datos
railway connect postgresql

# Ejecutar comandos en el servidor
railway run python manage.py migrate
```

## 🌐 URL de la aplicación

Después del deploy, tu aplicación estará disponible en:
- `https://tu-proyecto.up.railway.app`

Railway asigna automáticamente un dominio. También puedes:
- Configurar un dominio personalizado
- Ver la URL en el dashboard de Railway

## 🔍 Debugging

### Ver logs:
```bash
railway logs --tail
```

### Verificar build:
1. Ve al dashboard de Railway
2. Pestaña "Deployments"
3. Click en el deployment más reciente
4. Ver logs de build y runtime

### Problemas comunes:

#### Build falla:
- Verificar que `requirements.txt` esté actualizado
- Verificar que `package.json` del frontend esté correcto

#### App no inicia:
- Verificar variables de entorno
- Verificar logs con `railway logs`

#### 502/503 errors:
- La app debe escuchar en `0.0.0.0:$PORT`
- Verificar que el proceso no se cierre

## 💰 Costos

- **Plan gratuito**: $5 USD de crédito mensual
- **Plan Pro**: $20/mes + $20 de crédito de uso
- **Facturación**: Solo pagas por uso (CPU, RAM, transferencia)

## 🔄 Deployment Automático

Una vez configurado:

1. Haces cambios en tu código
2. `git push origin main`
3. Railway detecta el push y redeploya automáticamente
4. Tu app se actualiza sin downtime

## 📞 Soporte

- [Documentación oficial](https://docs.railway.app)
- [Discord de Railway](https://discord.gg/railway)
- [Ejemplos de Railway](https://github.com/railwayapp/examples)

## ✅ Checklist de Deploy

- [ ] Railway CLI instalado
- [ ] Proyecto creado en Railway
- [ ] Variables de entorno configuradas
- [ ] Primer deploy exitoso (`railway up`)
- [ ] App funcionando en la URL proporcionada
- [ ] Base de datos conectada (si aplica)
- [ ] Deploy automático configurado (git push)

¡Tu Legal Assistant AI está listo para producción! 🎉 