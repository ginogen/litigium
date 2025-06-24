# 🏛️ Legal Assistant AI

**Sistema de asistencia legal con inteligencia artificial, entrenamiento personalizado y gestión de documentos.**

---

## 🎯 **Características Principales**

- **💬 Chat Inteligente**: Conversación natural con IA especializada en derecho
- **📝 Generación de Demandas**: Creación automática de documentos legales
- **✏️ Editor Granular**: Edición por párrafos con comandos en lenguaje natural
- **🎯 Entrenamiento Personalizado**: Sistema de categorías y colecciones vectoriales por abogado
- **🎤 Transcripción de Audio**: Procesamiento de consultas de voz
- **👤 Gestión de Perfiles**: Datos profesionales personalizados

---

## 🏗️ **Arquitectura del Sistema**

### **Estructura de Directorios**
```
/
├── frontend/                  # React + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/        # Componentes UI
│   │   │   ├── Auth/          # Autenticación
│   │   │   ├── Chat/          # Sistema de chat
│   │   │   ├── Canvas/        # Editor de documentos
│   │   │   ├── Training/      # Entrenamiento personalizado
│   │   │   └── Profile/       # Gestión de perfil
│   │   ├── contexts/          # Estados globales (React Context)
│   │   └── lib/               # Utilidades y API client
│   └── package.json
│
└── backend/                   # FastAPI + Python
    ├── main.py               # Aplicación principal
    ├── routes/               # Routers organizados por funcionalidad
    │   ├── chat_routes.py     # Chat e IA
    │   ├── editor_routes.py   # Editor granular
    │   ├── document_routes.py # Gestión de documentos
    │   ├── audio_routes.py    # Procesamiento de audio
    │   ├── training_routes.py # Entrenamiento personalizado
    │   └── config_routes.py   # Configuración del sistema
    ├── core/                 # Lógica de negocio
    │   ├── document_processor.py
    │   └── category_manager.py
    ├── auth/                 # Autenticación y autorización
    ├── models/               # Modelos de datos
    └── requirements.txt
```

---

## 🚀 **Guía de Instalación**

### **1. Prerrequisitos**
- **Node.js** 18+ y npm
- **Python** 3.9+
- **Supabase** (cuenta gratuita)
- **Qdrant** (opcional, para entrenamiento avanzado)

### **2. Backend Setup**
```bash
# Navegar al directorio backend
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### **3. Frontend Setup**
```bash
# Navegar al directorio frontend
cd frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con las credenciales de Supabase
```

### **4. Configuración de Variables de Entorno**

#### **Backend (.env)**
```env
# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu_clave_anonima
SUPABASE_SERVICE_KEY=tu_clave_de_servicio

# Qdrant (opcional)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=tu_api_key

# Configuración del servidor
PORT=8000
DEBUG=true
```

#### **Frontend (.env)**
```env
VITE_SUPABASE_URL=https://tu-proyecto.supabase.co
VITE_SUPABASE_ANON_KEY=tu_clave_anonima
```

---

## 🏃‍♂️ **Ejecutar el Sistema**

### **Desarrollo**
```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend  
cd frontend
npm run dev
```

### **Producción**
```bash
# Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run build
npm run preview
```

---

## 📡 **API Endpoints**

### **🔧 Sistema y Configuración**
- `GET /api/health` - Estado del servidor
- `GET /api/v1/supabase-config` - Configuración de Supabase
- `GET /api/version` - Información de versión

### **💬 Chat e IA**
- `POST /api/chat/iniciar` - Iniciar sesión de chat
- `POST /api/chat/mensaje` - Enviar mensaje
- `POST /api/chat/generar-demanda` - Generar documento legal

### **✏️ Editor Granular**
- `POST /api/editor/inicializar` - Inicializar editor
- `POST /api/editor/procesar-comando` - Procesar comando de edición
- `GET /api/editor/parrafos/{session_id}` - Obtener párrafos

### **📄 Gestión de Documentos**
- `GET /api/documents/descargar/{session_id}` - Descargar documento
- `GET /api/documents/preview/{session_id}` - Vista previa
- `POST /api/documents/guardar-cambios` - Guardar cambios

### **🎤 Procesamiento de Audio**
- `POST /api/audio/transcribir` - Transcribir audio a texto
- `POST /api/audio/mensaje-audio` - Procesar mensaje de audio
- `GET /api/audio/formatos-soportados` - Formatos soportados

### **🎯 Entrenamiento Personalizado**
- `POST /api/training/categories` - Crear categoría
- `GET /api/training/categories` - Listar categorías
- `POST /api/training/upload` - Subir documento para entrenamiento
- `POST /api/training/search` - Búsqueda semántica

---

## 🛠️ **Stack Tecnológico**

### **Frontend**
- **React 18** - Biblioteca de UI
- **TypeScript** - Tipado estático
- **Tailwind CSS** - Framework de estilos
- **Vite** - Bundler y servidor de desarrollo
- **Zustand/Context** - Gestión de estado

### **Backend**
- **FastAPI** - Framework web moderno
- **Python 3.9+** - Lenguaje de programación
- **Supabase** - Backend como servicio (Auth + DB)
- **Qdrant** - Base de datos vectorial
- **Pydantic** - Validación de datos

### **Integraciones**
- **OpenAI/Anthropic** - Modelos de IA (próximamente)
- **Whisper** - Transcripción de audio (próximamente)
- **Vector Search** - Búsqueda semántica

---

## 🎨 **Características de la UI**

- **🌙 Tema Oscuro**: Diseño inspirado en ChatGPT
- **📱 Responsive**: Optimizado para desktop y móvil
- **⚡ Rápido**: Carga instantánea con lazy loading
- **♿ Accesible**: Cumple estándares WCAG
- **🎭 Animaciones**: Transiciones suaves

---

## 🔐 **Seguridad y Autenticación**

- **🔑 Supabase Auth**: Autenticación segura
- **👤 Perfiles Profesionales**: Datos personalizados por abogado
- **🔒 Sesiones Privadas**: Cada usuario ve solo sus datos
- **🛡️ Validación**: Validación en frontend y backend
- **📊 Logs**: Registro de actividades del sistema

---

## 🧪 **Testing y Desarrollo**

```bash
# Backend tests (próximamente)
cd backend
pytest

# Frontend tests (próximamente)
cd frontend
npm test

# Linting
npm run lint
```

---

## 📈 **Roadmap**

### **✅ Implementado**
- [x] Estructura frontend/backend
- [x] Sistema de autenticación
- [x] Entrenamiento personalizado
- [x] Gestión de categorías
- [x] Editor granular (estructura)
- [x] Procesamiento de audio (estructura)

### **🚧 En Desarrollo**
- [ ] Integración con modelos de IA
- [ ] Generación real de demandas
- [ ] Transcripción de audio real
- [ ] Búsqueda semántica avanzada

### **🔮 Próximamente**
- [ ] Plantillas de documentos
- [ ] Colaboración en tiempo real
- [ ] API pública
- [ ] Aplicación móvil

---

## 🤝 **Contribuir**

1. Fork el repositorio
2. Crear una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abrir un Pull Request

---

## 📄 **Licencia**

Este proyecto es propietario. Todos los derechos reservados.

---

## 📞 **Soporte**

Para soporte técnico o consultas:
- **Email**: soporte@legalassistant.ai
- **Documentación**: [docs.legalassistant.ai](https://docs.legalassistant.ai)
- **Issues**: [GitHub Issues](https://github.com/usuario/legal-assistant/issues)

---

**🏛️ Legal Assistant AI - Transformando el ejercicio legal con inteligencia artificial** 