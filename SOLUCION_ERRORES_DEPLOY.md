# 🚨 Solución de Errores de Deploy

## Errores encontrados y solucionados

### ❌ Error 1: Frontend - Nixpacks "npm not defined"

**Error:**
```
error: undefined variable 'npm'
```

**Causa:** 
El archivo `nixpacks.toml` estaba especificando `npm` como paquete, pero Nix no lo reconoce como tal.

**Solución aplicada:**
1. ✅ Simplificado `nixpacks.toml` - solo especifica el comando de inicio
2. ✅ Eliminado dependencias innecesarias 
3. ✅ Railway ahora detecta automáticamente que es un proyecto Node.js

**Archivos modificados:**
- `frontend/nixpacks.toml` (simplificado)
- `frontend/railway.toml` (limpiado)

---

### ❌ Error 2: Backend - Conflicto de dependencias gotrue

**Error:**
```
The conflict is caused by:
    The user requested gotrue==2.8.1
    supabase 2.9.1 depends on gotrue<3.0.0 and >=2.9.0
```

**Causa:** 
Versiones incompatibles entre `supabase` y `gotrue` en `requirements.txt`.

**Solución aplicada:**
1. ✅ Especificado `supabase==2.8.0` (versión estable)
2. ✅ Especificado `gotrue==2.9.1` (compatible con supabase 2.8.0)
3. ✅ Eliminado rangos de versiones problemáticos

**Archivos modificados:**
- `requirements.txt` - versiones específicas de Supabase

---

## 🔄 Próximos pasos

### Para el Frontend:
1. **Railway detectará automáticamente** que es un proyecto Node.js
2. **Configurar en Railway Dashboard:**
   - Root Directory: `frontend`
   - Build Command: (automático)
   - Start Command: `npm run preview -- --host 0.0.0.0 --port $PORT`

### Para el Backend:
1. **Las dependencias se resolverán** sin conflictos
2. **Verificar que las variables estén configuradas:**
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `OPENAI_API_KEY`

---

## ✅ Archivos finales

### Frontend simplificado:
- `railway.toml` - configuración mínima
- `package.json` - sin cambios
- Railway detecta automáticamente Node.js

### Backend corregido:
- `requirements.txt` - dependencias compatibles
- `railway.toml` - sin cambios

---

## 🧪 Para verificar que funcione:

```bash
# 1. Hacer commit de los cambios
git add .
git commit -m "fix: errores de deploy frontend y backend"
git push

# 2. Monitorear logs en Railway
railway logs --service=frontend
railway logs --service=backend
```

## 🎯 Resultado esperado:

- ✅ **Frontend**: Debe detectar Node.js y hacer build exitoso
- ✅ **Backend**: Debe instalar dependencias sin conflictos
- ✅ **Ambos servicios**: Deploy exitoso

## 🆘 Si persisten errores:

### Frontend:
- Verificar que Root Directory = `frontend` en Railway
- Verificar variables de entorno (VITE_API_URL, etc.)

### Backend:
- Verificar variables de entorno de Supabase
- Revisar logs de instalación de dependencias 