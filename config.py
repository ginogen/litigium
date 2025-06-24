"""
Configuración del Sistema Legal AI
Generador de Demandas Profesionales
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# === CONFIGURACIÓN DE SERVICIOS EXTERNOS ===
class OpenAIConfig:
    API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL = "gpt-4"
    TEMPERATURE = 0.3
    MAX_TOKENS = 4000
    EMBEDDING_MODEL = "text-embedding-ada-002"

class QdrantConfig:
    URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    API_KEY = os.getenv("QDRANT_API_KEY")
    COLLECTION_PREFIX = os.getenv("QDRANT_COLLECTION_PREFIX", "legalbot_")
    VECTOR_SIZE = 1536
    DISTANCE_METRIC = "COSINE"

class GoogleDocsConfig:
    CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    FOLDER_ID = os.getenv("GOOGLE_FOLDER_ID")

# === CONFIGURACIÓN DEL SERVIDOR ===
class ServerConfig:
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    RELOAD = DEBUG

# === CONFIGURACIÓN DE PATHS ===
class PathConfig:
    DATA_DIR = "data"
    CASOS_ANTERIORES = "data/casos_anteriores"
    EJEMPLOS_DEMANDAS = "ejemplos_demandas"
    TEMPLATES_DIR = "templates"
    STATIC_DIR = "static"
    TEMP_DIR = "temp"

# === CONFIGURACIÓN DE TIPOS DE DEMANDA ===
TIPOS_DEMANDA_DISPONIBLES = [
    "Despido Sin Justa Causa",
    "Despido Discriminatorio", 
    "Accidente Laboral",
    "Diferencias Salariales",
    "Acoso Laboral",
    "Horas Extras",
    "Vacaciones No Gozadas",
    "Licencia Médica",
    "Solidaridad Laboral",
    "Trabajo No Registrado"
]

# === CONFIGURACIÓN DE CHAT ===
class ChatConfig:
    MAX_SESSIONS = 1000
    SESSION_TIMEOUT_HOURS = 24
    MAX_MESSAGE_LENGTH = 5000
    TYPING_DELAY_SECONDS = 2

# === MENSAJES DEL SISTEMA ===
class Messages:
    WELCOME = "¡Hola! Soy tu asistente legal AI. Te ayudaré a generar una demanda profesional."
    ERROR_GENERIC = "Ha ocurrido un error. Por favor, inténtalo nuevamente."
    ERROR_SESSION_NOT_FOUND = "Sesión no encontrada. Por favor, inicia una nueva conversación."
    ERROR_MISSING_DATA = "Faltan datos obligatorios. Por favor, completa la información requerida."
    SUCCESS_GENERATED = "¡Tu demanda ha sido generada exitosamente!"

# === VALIDACIÓN DE CONFIGURACIÓN ===
def validar_configuracion():
    """Valida que todas las configuraciones necesarias estén presentes."""
    errores = []
    
    if not OpenAIConfig.API_KEY:
        errores.append("OPENAI_API_KEY no configurada")
    
    if not QdrantConfig.URL:
        errores.append("QDRANT_URL no configurada")
    
    # Crear directorios necesarios
    for path in [PathConfig.DATA_DIR, PathConfig.CASOS_ANTERIORES, PathConfig.TEMP_DIR]:
        os.makedirs(path, exist_ok=True)
    
    if errores:
        raise ValueError(f"Errores de configuración: {', '.join(errores)}")
    
    return True

# === CONFIGURACIÓN DE LOGGING ===
import logging

def configurar_logging():
    """Configura el sistema de logging."""
    logging.basicConfig(
        level=logging.INFO if ServerConfig.DEBUG else logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('sistema_legal.log'),
            logging.StreamHandler()
        ]
    )
    
    # Configurar logger específico para el sistema
    logger = logging.getLogger('sistema_legal')
    return logger

# Crear logger global
logger = configurar_logging()

# === CONFIGURACIÓN DE PROMPTS ===
class Prompts:
    SYSTEM_PROMPT = """Eres un abogado especialista en derecho laboral argentino. 
    Tu tarea es redactar una demanda profesional, completa y técnicamente correcta.
    
    INSTRUCCIONES CRÍTICAS:
    1. Usa lenguaje jurídico formal y preciso
    2. Cita artículos específicos de la LCT (Ley de Contrato de Trabajo)
    3. Estructura la demanda según el código procesal argentino
    4. Incluye jurisprudencia cuando sea relevante
    5. Calcula montos en pesos argentinos actuales
    6. Usa formato profesional de escritos judiciales
    
    ESTRUCTURA OBLIGATORIA:
    - ENCABEZADO (Tribunal, Expediente, Caratula)
    - HECHOS (numerados y detallados)
    - DERECHO (base legal con citas específicas)
    - PETITORIO (solicitudes concretas al tribunal)
    - OFRECIMIENTO DE PRUEBA (detallado y específico)
    - FIRMA Y DATOS DEL LETRADO"""
    
    HUMAN_PROMPT_TEMPLATE = """DATOS DEL CLIENTE:
{datos_cliente}

TIPO DE DEMANDA: {tipo_demanda}

HECHOS ADICIONALES:
{hechos_adicionales}

NOTAS DEL ABOGADO:
{notas_abogado}

CONTEXTO LEGAL DE CASOS SIMILARES:
{contexto_legal}

Por favor, redacta una demanda completa y profesional siguiendo la estructura obligatoria mencionada."""

# === CONFIGURACIÓN DE CAMPOS REQUERIDOS ===
CAMPOS_CLIENTE_OBLIGATORIOS = [
    "nombre_completo",
    "dni", 
    "domicilio"
]

CAMPOS_CLIENTE_OPCIONALES = [
    "telefono",
    "email",
    "fecha_nacimiento",
    "estado_civil",
    "ocupacion",
    "motivo_demanda"
]

# Validar configuración al importar
if __name__ == "__main__":
    try:
        validar_configuracion()
        print("✅ Configuración válida")
    except ValueError as e:
        print(f"❌ {e}")
else:
    validar_configuracion() 