# Solución: App se Queda Cargando al Cambiar de Sección

## 🔍 **Problemas Identificados y Solucionados**

### 1. **Reintentos Infinitos en Plantillas**
**Problema:** La función `loadTemplates()` tenía un sistema de reintentos automáticos que podía crear loops infinitos si había problemas de conectividad.

**Solución Implementada:**
- ✅ Agregado timeout de 10 segundos para requests de plantillas
- ✅ Limitado reintentos a solo 1 vez
- ✅ Aumentado intervalo de reintento a 5 segundos
- ✅ AbortController para cancelar requests al desmontar componente

### 2. **Estados de Loading sin Reset**
**Problema:** Los estados de `isLoading`, `isUploading`, `isSearching` etc. podían quedarse en `true` al cambiar de tab.

**Solución Implementada:**
- ✅ Función `resetLoadingStates()` que resetea todos los estados
- ✅ useEffect que resetea loading al cambiar de `activeTab`
- ✅ Cleanup functions en useEffect para anotaciones

### 3. **Requests sin Timeout**
**Problema:** Las llamadas a API podían quedarse "colgadas" indefinidamente.

**Solución Implementada:**
- ✅ Timeout de 15 segundos para cargar categorías
- ✅ Timeout de 20 segundos para búsquedas
- ✅ Timeout de 10 segundos para plantillas
- ✅ Manejo específico de errores de timeout

### 4. **Memory Leaks en Componentes**
**Problema:** Componentes no limpiaban resources al desmontarse.

**Solución Implementada:**
- ✅ Cleanup functions en useEffect
- ✅ AbortController para cancelar requests pendientes
- ✅ Reset de estados al cambiar de documento

## 🛠 **Código Mejorado**

### Estados de Loading Resetea Automáticamente:
```typescript
// Función para resetear estados de loading al cambiar de tab
const resetLoadingStates = useCallback(() => {
  setIsLoading(false);
  setIsUploading(false);
  setIsSearching(false);
  setIsLoadingAnnotations(false);
  setIsLoadingTemplates(false);
}, []);

// Resetear estados de loading al cambiar de tab para evitar UI colgada
useEffect(() => {
  resetLoadingStates();
}, [activeTab, resetLoadingStates]);
```

### Requests con Timeout:
```typescript
// Agregar timeout para evitar requests colgados
const response = await Promise.race([
  categoryAPI.obtenerCategorias(),
  new Promise((_, reject) => 
    setTimeout(() => reject(new Error('Request timeout')), 15000)
  )
]) as any;
```

### Cleanup de Recursos:
```typescript
// Cargar anotaciones cuando se selecciona un documento
useEffect(() => {
  if (selectedDocument?.id) {
    loadAnnotations(selectedDocument.id);
  }
  
  // Cleanup al cambiar de documento
  return () => {
    setIsLoadingAnnotations(false);
  };
}, [selectedDocument?.id]);
```

## 🚀 **Recomendaciones Adicionales**

### Para el Usuario:

1. **Si sigue ocurriendo el problema:**
   - Abre las DevTools del navegador (F12)
   - Ve a la pestaña "Console"
   - Busca errores en rojo o warnings
   - Comparte esa información para diagnosis más específica

2. **Indicadores de problemas:**
   - Si ves muchos `console.warn` sobre templates
   - Si aparecen errores 500 o 404 repetidos
   - Si los timeouts son muy frecuentes

3. **Limpieza preventiva:**
   - Cierra pestañas extra del navegador
   - Limpia caché del navegador ocasionalmente
   - Si tienes conexión lenta, espera a que termine una acción antes de cambiar de sección

### Para el Desarrollador:

1. **Monitoreo adicional:**
   ```typescript
   // Agregar logging de performance
   console.time('loadCategories');
   const response = await categoryAPI.obtenerCategorias();
   console.timeEnd('loadCategories');
   ```

2. **Circuit breaker pattern:**
   ```typescript
   // Implementar circuit breaker para APIs problemáticas
   const circuitBreaker = {
     failures: 0,
     isOpen: false,
     attempt: async (fn) => {
       if (this.isOpen) throw new Error('Circuit breaker open');
       try {
         const result = await fn();
         this.failures = 0;
         return result;
       } catch (error) {
         this.failures++;
         if (this.failures >= 3) this.isOpen = true;
         throw error;
       }
     }
   };
   ```

3. **Estados de error más granulares:**
   ```typescript
   const [error, setError] = useState<{
     type: 'network' | 'timeout' | 'server' | 'unknown';
     message: string;
     retry?: () => void;
   } | null>(null);
   ```

## 📋 **Testing**

Para verificar que la solución funciona:

1. **Test de cambio rápido de tabs:**
   - Cambiar rápidamente entre "Subir Documentos" → "Categorías" → "Búsqueda"
   - No debería quedarse ningún spinner activo

2. **Test de timeout:**
   - Con DevTools → Network → "Slow 3G"
   - Intentar cargar plantillas o categorías
   - Debería mostrar mensaje de timeout después del tiempo especificado

3. **Test de memory leaks:**
   - Abrir/cerrar DocumentViewer varias veces
   - Cambiar entre documentos rápidamente
   - La app debería mantener responsividad

## ⚡ **Optimizaciones Futuras**

1. **Lazy loading de componentes:**
   ```typescript
   const DocumentViewer = lazy(() => import('./DocumentViewer'));
   ```

2. **Cache de resultados:**
   ```typescript
   const [categoriesCache, setCategoriesCache] = useState<{
     data: Category[];
     timestamp: number;
   } | null>(null);
   ```

3. **Debounce en búsquedas:**
   ```typescript
   const debouncedSearch = useMemo(
     () => debounce(handleSearch, 500),
     [handleSearch]
   );
   ```

## ✅ **Resultado Esperado**

Después de estos cambios:
- ✅ La app no se debería quedar "colgada" al cambiar entre secciones
- ✅ Los estados de loading se resetean automáticamente
- ✅ Los requests tienen timeouts apropiados
- ✅ Mejor manejo de errores con mensajes específicos
- ✅ Limpieza automática de recursos para prevenir memory leaks

La aplicación debería ser mucho más estable y responsiva al navegar entre diferentes secciones. 