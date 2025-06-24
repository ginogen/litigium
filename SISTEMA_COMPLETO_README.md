# 🏛️ Sistema Legal AI - Generador de Demandas Inteligente

## 🎯 **Sistema Completo y Funcional**

Este sistema legal AI incluye todas las funcionalidades necesarias para:
- **Chat inteligente** con extracción automática de datos
- **Generación de demandas** usando GPT-4 y RAG
- **Sistema de entrenamiento** con documentos personalizados
- **Búsqueda semántica** en base de conocimientos legal

---

## 🚀 **Configuración Rápida**

### **1. Variables de Entorno**

Crea un archivo `.env` en la raíz del proyecto:

```bash
# OpenAI (REQUERIDO para IA)
OPENAI_API_KEY=sk-tu-clave-openai-aqui

# Supabase (REQUERIDO para base de datos)
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu-anon-key
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key

# Qdrant (OPCIONAL para vectores avanzados)
QDRANT_URL=https://tu-qdrant-cluster.qdrant.io
QDRANT_API_KEY=tu-qdrant-api-key
```

### **2. Instalación**

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend  
cd frontend
npm install
```

### **3. Verificación del Sistema**

```bash
# Ejecutar verificación completa
python test_sistema_completo.py
```

### **4. Iniciar Servicios**

```bash
# Backend (Terminal 1)
cd backend
uvicorn main:app --reload --port 8000

# Frontend (Terminal 2) 
cd frontend
npm run dev
```

---

## 🧠 **Funcionalidades Inteligentes Activadas**

### **Chat con IA GPT-4**
- ✅ Extracción automática de datos (nombre, DNI, dirección)
- ✅ Comprensión contextual de mensajes complejos
- ✅ Detección automática de tipos de demanda
- ✅ Seguimiento de conversación inteligente

### **Generación de Demandas con RAG**
- ✅ Búsqueda en documentos similares
- ✅ Generación usando jurisprudencia actual
- ✅ Plantillas profesionales optimizadas
- ✅ Descarga en formato Word

### **Sistema de Entrenamiento**
- ✅ Subida drag & drop de documentos
- ✅ Extracción automática de texto (PDF, DOCX)
- ✅ Vectorización con OpenAI embeddings
- ✅ Categorización personalizada

### **Búsqueda Semántica**
- ✅ Búsqueda por similitud en lenguaje natural
- ✅ Filtros por categoría y tipo
- ✅ Resultados con score de relevancia

---

## 💬 **Ejemplos de Uso del Chat**

### **Caso Simple**
```
Usuario: "Necesito una demanda por despido injustificado"
IA: "Te ayudo con la demanda. Necesito algunos datos del cliente..."
```

### **Caso Complejo (Todo en un mensaje)**
```
Usuario: "Juan Pérez, DNI 35703591, Paraguay 2536, me despidieron sin causa de la empresa ACME"
IA: "✅ Información completa recibida
     Cliente: Juan Pérez
     DNI: 35703591
     Tipo: Despido injustificado
     ¿Procedo a generar la demanda?"
```

### **Con Documentos Contextuales**
```
Usuario: "Caso similar al de empleado en blanco despedido"
IA: [Busca en documentos similares]
     "He encontrado 3 casos similares en tu base de datos.
     Basándome en ellos, te recomiendo enfocar la demanda en..."
```

---

## 📊 **Flujo de Trabajo Completo**

### **1. Subir Documentos de Entrenamiento**
1. Ve a **Training Section**
2. Crea categorías (ej: "Despidos", "Accidentes")
3. Sube documentos PDF/DOCX con casos anteriores
4. El sistema los procesa automáticamente

### **2. Chat Inteligente**
1. Inicia nueva sesión de chat
2. Describe el caso en lenguaje natural
3. La IA extrae datos automáticamente
4. Confirma información y genera demanda

### **3. Generación y Descarga**
1. La IA busca casos similares
2. Genera demanda profesional
3. Previsualiza el documento
4. Descarga en formato Word

---

## 🔧 **Arquitectura del Sistema**

```
Frontend (React + TypeScript)
├── Chat inteligente con UI moderna
├── Sistema de subida drag & drop
├── Previsualización de demandas
└── Gestión de categorías

Backend (FastAPI + Python)
├── ChatAgent con GPT-4
├── DocumentProcessor con embeddings
├── RAG con búsqueda semántica
└── Generador de demandas profesionales

Datos
├── Supabase (sesiones + metadatos)
├── Qdrant (vectores para búsqueda)
└── Storage (documentos originales)
```

---

## 🎛️ **Configuración Avanzada**

### **Personalizar Tipos de Demanda**
Edita `rag/qa_agent.py`:
```python
TIPOS_DEMANDA = [
    "Tu Tipo Personalizado",
    "Otro Tipo Específico",
    # ... más tipos
]
```

### **Ajustar Prompts de IA**
Modifica `rag/chat_agent.py` para personalizar el comportamiento:
```python
prompt = f"""
Eres un asistente legal especializado en [TU JURISDICCIÓN]
que debe seguir [TUS REGLAS ESPECÍFICAS]...
"""
```

### **Configurar Qdrant Local**
```bash
# Docker
docker run -p 6333:6333 qdrant/qdrant:latest

# En .env
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Dejar vacío para local
```

---

## 🚨 **Troubleshooting**

### **Chat no responde inteligentemente**
- ✅ Verifica `OPENAI_API_KEY` en `.env`
- ✅ Ejecuta `python test_sistema_completo.py`
- ✅ Revisa logs del backend

### **Documentos no se procesan**
- ✅ Verifica conexión con Qdrant
- ✅ Asegúrate que el archivo sea PDF/DOCX válido
- ✅ Revisa permisos de Supabase Storage

### **Demandas no se generan**
- ✅ Verifica que tengas documentos de entrenamiento
- ✅ Asegúrate que los datos del cliente estén completos
- ✅ Revisa quota de OpenAI

---

## 📈 **Métricas del Sistema**

El sistema incluye tracking automático de:
- Sesiones de chat por usuario
- Documentos procesados exitosamente  
- Demandas generadas
- Búsquedas realizadas
- Tiempo de respuesta de IA

---

## 🎉 **¡Ya tienes un sistema legal AI completo!**

### **Próximos pasos:**
1. ⚡ Ejecuta `python test_sistema_completo.py`
2. 📄 Sube tus primeros documentos de casos
3. 💬 Prueba el chat con un caso real
4. 🎯 Genera tu primera demanda automatizada

### **Soporte:**
- 📚 Documentación completa en `/docs`
- 🐛 Reportar issues en el repositorio
- 💡 Sugerencias de mejoras bienvenidas

---

**¡Tu asistente legal AI está listo para revolucionar tu práctica profesional!** 🚀⚖️ 