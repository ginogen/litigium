import os
import json
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import hashlib

load_dotenv()

# Variables de configuración
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_PREFIX = os.getenv("QDRANT_COLLECTION_PREFIX", "legalbot_")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializar clientes
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
embedder = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

def load_json_docs(path="data/casos_anteriores"):
    """Carga todos los documentos JSON del directorio especificado."""
    docs = []
    if not os.path.exists(path):
        print(f"⚠️ Directorio {path} no existe. Creándolo...")
        os.makedirs(path, exist_ok=True)
        return docs
    
    for fname in os.listdir(path):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(path, fname), encoding="utf-8") as f:
                    doc = json.load(f)
                    if doc.get("tipo"):  # Solo incluir documentos con tipo definido
                        docs.append(doc)
                    else:
                        print(f"⚠️ Documento {fname} no tiene tipo definido, saltando...")
            except Exception as e:
                print(f"❌ Error cargando {fname}: {e}")
    
    return docs

def get_embedding(text):
    """Genera embedding para el texto dado."""
    try:
        return embedder.embed_query(text)
    except Exception as e:
        print(f"❌ Error generando embedding: {e}")
        return None

def crear_coleccion_si_no_existe(collection_name):
    """Crea una colección en Qdrant si no existe."""
    try:
        if not client.collection_exists(collection_name=collection_name):
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
            print(f"✅ Colección '{collection_name}' creada")
        else:
            print(f"ℹ️ Colección '{collection_name}' ya existe")
    except Exception as e:
        print(f"❌ Error creando colección {collection_name}: {e}")
        raise

def upload_to_qdrant():
    """Procesa y sube documentos a Qdrant."""
    docs = load_json_docs()
    
    if not docs:
        print("⚠️ No se encontraron documentos para procesar")
        return
    
    print(f"📂 Documentos cargados: {len(docs)}")

    # Agrupar documentos por tipo
    docs_por_tipo = {}
    for doc in docs:
        tipo = doc.get("tipo", "desconocido").lower().replace(" ", "_")
        if tipo not in docs_por_tipo:
            docs_por_tipo[tipo] = []
        docs_por_tipo[tipo].append(doc)

    print(f"📊 Tipos de demanda encontrados: {list(docs_por_tipo.keys())}")

    # Procesar cada tipo de demanda
    for tipo, documentos in docs_por_tipo.items():
        collection_name = f"{COLLECTION_PREFIX}{tipo}"
        print(f"\n🔄 Procesando tipo: {tipo} ({len(documentos)} documentos)")
        
        # Crear colección
        crear_coleccion_si_no_existe(collection_name)
        
        # Procesar documentos de este tipo
        puntos_a_subir = []
        
        for doc in tqdm(documentos, desc=f"Procesando {tipo}"):
            try:
                # Crear texto completo para embedding
                texto_completo = " ".join([
                    doc.get("hechos", ""),
                    doc.get("derecho", ""),
                    doc.get("petitorio", ""),
                    doc.get("prueba", "")
                ]).strip()
                
                if not texto_completo:
                    print(f"⚠️ Documento {doc.get('id', 'sin_id')} está vacío, saltando...")
                    continue
                
                # Generar embedding
                vector = get_embedding(texto_completo)
                if vector is None:
                    continue
                
                # Crear ID único
                doc_id = doc.get("id", "unknown")
                uid = hashlib.md5(f"{collection_name}_{doc_id}".encode()).hexdigest()
                
                # Crear punto para Qdrant
                punto = PointStruct(
                    id=uid,
                    vector=vector,
                    payload={
                        **doc,
                        "texto_completo": texto_completo,
                        "fecha_procesamiento": os.path.getctime(os.path.join("data/casos_anteriores", f"{doc_id}.json")) if os.path.exists(os.path.join("data/casos_anteriores", f"{doc_id}.json")) else None
                    }
                )
                puntos_a_subir.append(punto)
                
            except Exception as e:
                print(f"❌ Error procesando documento {doc.get('id', 'sin_id')}: {e}")
                continue
        
        # Subir puntos a Qdrant
        if puntos_a_subir:
            try:
                client.upsert(collection_name=collection_name, points=puntos_a_subir)
                print(f"✅ {len(puntos_a_subir)} documentos subidos a '{collection_name}'")
            except Exception as e:
                print(f"❌ Error subiendo a Qdrant: {e}")
        else:
            print(f"⚠️ No hay documentos válidos para subir en tipo '{tipo}'")

    print("\n🎉 Proceso de carga completado")

def verificar_conexion():
    """Verifica la conexión a Qdrant y OpenAI."""
    try:
        # Verificar Qdrant
        collections = client.get_collections()
        print(f"✅ Conexión a Qdrant exitosa. Colecciones disponibles: {len(collections.collections)}")
        
        # Verificar OpenAI
        test_embedding = embedder.embed_query("test")
        print(f"✅ Conexión a OpenAI exitosa. Dimensión de embedding: {len(test_embedding)}")
        
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def mostrar_estadisticas():
    """Muestra estadísticas de las colecciones existentes."""
    try:
        collections = client.get_collections()
        print("\n📊 ESTADÍSTICAS DE COLECCIONES:")
        print("-" * 50)
        
        for collection in collections.collections:
            if collection.name.startswith(COLLECTION_PREFIX):
                info = client.get_collection(collection.name)
                tipo = collection.name.replace(COLLECTION_PREFIX, "").replace("_", " ").title()
                print(f"📁 {tipo}: {info.points_count} documentos")
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")

# Ejecución principal
if __name__ == "__main__":
    print("🚀 Iniciando carga de documentos a Qdrant...")
    
    # Verificar conexiones
    if not verificar_conexion():
        print("❌ No se pudo establecer conexión. Revisa las variables de entorno.")
        exit(1)
    
    # Ejecutar carga
    upload_to_qdrant()
    
    # Mostrar estadísticas finales
    mostrar_estadisticas()
