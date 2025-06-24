# 🚂 Configuración de Servicios Separados en Railway

## Problema resuelto
Evitar que Railway redepliegue servicios innecesariamente cuando cambias archivos de otros servicios.

## ✅ Configuración del Servicio Backend

### En Railway Dashboard:
1. Ve a tu servicio **Backend**
2. **Settings** → **Source**
3. Configura:
   - **Root Directory**: (vacío o `backend`)
   - **Watch Paths**: `backend/** *.py requirements.txt main.py rag/** railway.toml`

### Archivos creados:
- `backend/.railwayignore` ✅ (ignora frontend)
- `railway.toml` actualizado con `watchPaths` ✅

## ✅ Configuración del Servicio Frontend

### En Railway Dashboard:
1. Ve a tu servicio **Frontend** 
2. **Settings** → **Source**
3. Configura:
   - **Root Directory**: `frontend`
   - **Watch Paths**: `frontend/**`

### Archivos creados:
- `frontend/.railwayignore` ✅ (ignora backend)
- `frontend/railway.toml` con `watchPaths` ✅

## 🎯 Resultado esperado

| Cambio en | Backend redeploy | Frontend redeploy |
|-----------|------------------|-------------------|
| `backend/` | SÍ ✅ | NO ❌ |
| `frontend/` | NO ❌ | SÍ ✅ |
| `requirements.txt` | SÍ ✅ | NO ❌ |
| `frontend/package.json` | NO ❌ | SÍ ✅ |

## 🧪 Cómo probar

1. Haz un cambio pequeño solo en el frontend:
   ```bash
   # Cambiar un comentario en frontend/src/App.tsx
   git add frontend/
   git commit -m "test: cambio solo frontend"
   git push
   ```

2. Verifica en Railway:
   - Solo el servicio **Frontend** debe mostrar "Deploying"
   - El servicio **Backend** debe permanecer sin cambios

## 🔧 Comandos útiles

```bash
# Ver logs solo del servicio que se está deployando
railway logs --service=frontend
railway logs --service=backend

# Forzar redeploy si es necesario
railway redeploy --service=frontend
railway redeploy --service=backend
```

## 📊 Ventajas de esta configuración

- ⚡ **Deploys más rápidos**: Solo el servicio que cambió se redeploy
- 💰 **Menos uso de recursos**: No malgastas build minutes
- 🔒 **Más estabilidad**: El backend no se reinicia por cambios de frontend
- 🎯 **Mejor experiencia**: Deploys más predecibles

## ⚠️ Notas importantes

- Los archivos `.railwayignore` funcionan como `.gitignore` pero para Railway
- `watchPaths` en `railway.toml` define exactamente qué cambios activan un redeploy
- Si necesitas que ambos servicios se redeplieguen, puedes tocar un archivo común como `README.md`

## 🆘 Solución de problemas

### Si el backend se redeploy cuando no debería:
1. Verifica que `frontend/` esté en `backend/.railwayignore`
2. Confirma que `watchPaths` esté configurado en `railway.toml`
3. Revisa que **Watch Paths** esté configurado en Railway Dashboard

### Si el frontend no se redeploy cuando debería:
1. Verifica que el cambio esté en `frontend/`
2. Confirma que `watchPaths = ["frontend/**"]` esté en `frontend/railway.toml`
3. Revisa la configuración de **Root Directory** en Railway Dashboard 