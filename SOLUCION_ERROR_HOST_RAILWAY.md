# 🚨 Solución: "This host is not allowed" en Railway

## Error encontrado
```
Blocked request. This host ("litigium-production.up.railway.app") is not allowed.
To allow this host, add "litigium-production.up.railway.app" to `preview.allowedHosts` in vite.config.js.
```

## ❌ Causa del problema
El comando `npm run preview` (Vite preview) tiene restricciones de seguridad que bloquean hosts externos como Railway.

## ✅ Solución aplicada

### 1. **Servidor de producción adecuado**
- ✅ Agregado `serve` como dependencia
- ✅ Creado script `npm run serve` para producción  
- ✅ Actualizado comando de inicio en Railway

### 2. **Archivos modificados:**

**`package.json`:**
- ➕ Agregado `"serve": "^14.2.3"` en dependencies
- ➕ Agregado `"serve": "serve -s dist -p $PORT"` en scripts
- ➕ Agregado `"start": "serve -s dist -p $PORT"` en scripts

**`railway.toml`:**
- 🔄 Cambiado `startCommand` de `npm run preview` a `npm run serve`
- ➕ Agregado `buildCommand = "npm ci && npm run build"`

**`vite.config.ts`:**
- ➕ Agregado `allowedHosts: ['all']` como respaldo

---

## 🔧 Configuración CRÍTICA en Railway Dashboard

### **Servicio Frontend:**
1. **Settings** → **Source**:
   ```
   Root Directory: frontend
   Build Command: npm ci && npm run build
   Start Command: npm run serve
   Watch Paths: frontend/**
   ```

2. **Variables de entorno** (verificar que estén configuradas):
   ```
   VITE_API_URL=https://tu-backend-xxxx.up.railway.app
   NODE_ENV=production
   VITE_NODE_ENV=production
   ```

---

## 🚀 Deploy de los cambios

```bash
# 1. Hacer commit de todos los cambios
git add .
git commit -m "fix: error host bloqueado Railway - usar serve en lugar de vite preview"
git push origin main

# 2. Verificar que Railway redeploy el frontend
# Debería ver en logs:
# ✅ Installing dependencies...
# ✅ Building with npm run build
# ✅ Starting with npm run serve
```

---

## 🎯 Diferencias entre comandos

| Comando | Uso | Ventajas | Desventajas |
|---------|-----|----------|-------------|
| `npm run preview` | Desarrollo local | Rápido, HMR | Restricciones de host |
| `npm run serve` | Producción | Sin restricciones, optimizado | Solo archivos estáticos |

---

## 🧪 Verificar que funciona

Después del redeploy, deberías ver:

1. **En Railway logs:**
   ```
   ✅ Installing dependencies
   ✅ Building application  
   ✅ Starting static server with serve
   ✅ Server running on port $PORT
   ```

2. **En el navegador:**
   - ✅ La aplicación se carga sin error de host
   - ✅ Se conecta al backend correctamente
   - ✅ Las funcionalidades funcionan

---

## 🆘 Si persiste el problema

### Verificar en Railway Dashboard:
1. **Start Command** debe ser exactamente: `npm run serve`
2. **Variables** deben incluir `VITE_API_URL` con la URL del backend
3. **Build logs** deben mostrar que `npm run build` se ejecutó exitosamente

### Comandos de diagnóstico:
```bash
# Ver logs en tiempo real
railway logs --service=frontend --tail

# Verificar variables
railway variables --service=frontend

# Forzar redeploy si es necesario
railway redeploy --service=frontend
```

---

## ✅ Resultado esperado

- 🎯 **Frontend funcionando** en la URL de Railway
- 🔗 **Conexión exitosa** con el backend
- 🚀 **Aplicación completa** lista para usar 