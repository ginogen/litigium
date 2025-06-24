import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from docx import Document
from docx.shared import Inches
from datetime import datetime
import tempfile
import json
import time

load_dotenv()

# Variables de entorno
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_PREFIX = os.getenv("QDRANT_COLLECTION_PREFIX", "legalbot_")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicialización de servicios
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
llm = ChatOpenAI(
    model_name="gpt-4", 
    temperature=0.3, 
    openai_api_key=OPENAI_API_KEY,
    request_timeout=45,  # Timeout de 45 segundos
    max_retries=1  # Solo 1 reintento para no duplicar tiempo
)
embedder = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

def obtener_tipos_demanda_disponibles() -> List[str]:
    """Obtiene los tipos de demanda disponibles desde las categorías de usuario en Supabase."""
    try:
        # Importar aquí para evitar dependencias circulares
        from supabase_integration import supabase_admin
        
        # Obtener todas las categorías activas que tienen documentos procesados
        response = supabase_admin.table('categorias_demandas')\
            .select('nombre, id')\
            .eq('activo', True)\
            .execute()
        
        if not response.data:
            print("⚠️ No hay categorías en la base de datos")
            # Fallback con tipos básicos
            return ["Empleados En Blanco", "Empleados En Negro", "Demanda Licencia Medica", "Demanda Solidaridad Laboral", "Empleados Blanco Negro"]
        
        # Verificar cuáles categorías tienen documentos procesados
        categorias_con_documentos = []
        for categoria in response.data:
            docs_response = supabase_admin.table('documentos_entrenamiento')\
                .select('id')\
                .eq('categoria_id', categoria['id'])\
                .eq('estado_procesamiento', 'completado')\
                .execute()
            
            if docs_response.data and len(docs_response.data) > 0:
                categorias_con_documentos.append(categoria['nombre'])
        
        if categorias_con_documentos:
            print(f"✅ Categorías con documentos encontradas: {categorias_con_documentos}")
            return categorias_con_documentos
        else:
            print("⚠️ No hay categorías con documentos procesados")
            # Devolver nombres de categorías aunque no tengan documentos, para mostrar en la interfaz
            nombres_categorias = [cat['nombre'] for cat in response.data]
            return nombres_categorias if nombres_categorias else ["Empleados En Blanco", "Empleados En Negro"]
            
    except Exception as e:
        print(f"❌ Error obteniendo categorías desde Supabase: {e}")
        
        # Último fallback: tipos predefinidos
        return ["Empleados En Blanco", "Empleados En Negro", "Demanda Licencia Medica", "Demanda Solidaridad Laboral", "Empleados Blanco Negro"]

def mapear_nombre_carpeta(nombre_carpeta: str) -> str:
    """Mapea nombres de carpetas a nombres legibles para el usuario."""
    mapeos = {
        "empleados_blanco": "Empleados En Blanco",
        "empleados_negro": "Empleados En Negro", 
        "empleados_blanco_negro": "Empleados Blanco Negro",
        "demanda_licencia_medica": "Demanda Licencia Medica",
        "demanda_solidaridad_laboral": "Demanda Solidaridad Laboral"
    }
    
    return mapeos.get(nombre_carpeta.lower(), nombre_carpeta.replace("_", " ").title())

def mapear_tipo_a_coleccion(tipo_demanda: str) -> str:
    """Mapea tipos de demanda legibles a nombres de colección en Qdrant."""
    mapeo_inverso = {
        "Empleados En Blanco": "empleados_en_blanco",
        "Empleados En Negro": "empleados_en_negro",
        "Empleados Blanco Negro": "empleados_blanco_negro", 
        "Demanda Licencia Medica": "demanda_licencia_medica",
        "Demanda Solidaridad Laboral": "demanda_solidaridad_laboral"
    }
    
    return mapeo_inverso.get(tipo_demanda, tipo_demanda.lower().replace(" ", "_"))

def buscar_contexto_legal_enriquecido(user_id: str, query: str, tipo_demanda: str = None, top_k: int = 3) -> str:
    """Busca contexto legal enriquecido con anotaciones de experto en colección personal."""
    
    try:
        # Usar DocumentProcessor para búsqueda con anotaciones
        from backend.core.document_processor import DocumentProcessor
        
        doc_processor = DocumentProcessor()
        enhanced_context = doc_processor.get_enhanced_legal_context(
            user_id=user_id,
            query_text=query,
            tipo_demanda=tipo_demanda,
            limit=top_k
        )
        
        # Construir contexto estructurado para IA
        context_parts = []
        
        if enhanced_context.get("contexto_textual"):
            context_parts.append(f"CONTEXTO BASE: {enhanced_context['contexto_textual']}")
        
        if enhanced_context.get("estrategias_expertas"):
            estrategias_text = " | ".join(enhanced_context["estrategias_expertas"])
            context_parts.append(f"ESTRATEGIAS EXPERTAS: {estrategias_text}")
        
        if enhanced_context.get("precedentes_identificados"):
            precedentes_text = " | ".join(enhanced_context["precedentes_identificados"])
            context_parts.append(f"PRECEDENTES APLICABLES: {precedentes_text}")
        
        if enhanced_context.get("problemas_comunes"):
            problemas_text = " | ".join(enhanced_context["problemas_comunes"])
            context_parts.append(f"PROBLEMAS DETECTADOS: {problemas_text}")
        
        if enhanced_context.get("insights_adicionales"):
            insights_text = " | ".join(enhanced_context["insights_adicionales"])
            context_parts.append(f"INSIGHTS ADICIONALES: {insights_text}")
        
        # Añadir información de la fuente
        if enhanced_context.get("documentos_fuente"):
            stats_text = f"[Fuentes: {enhanced_context['documentos_fuente']} docs, {enhanced_context.get('documentos_con_anotaciones', 0)} con anotaciones expertas]"
            context_parts.append(stats_text)
        
        # Si tenemos algún contexto, devolverlo
        if context_parts:
            return " || ".join(context_parts)
        else:
            print("⚠️ Contexto enriquecido vacío, usando fallback")
            raise Exception("Contexto enriquecido vacío")
        
    except Exception as e:
        print(f"❌ Error en búsqueda enriquecida, usando fallback: {e}")
        # Usar fallback más simple
        try:
            return buscar_contexto_usuario_basico(user_id, query, tipo_demanda, top_k)
        except Exception as e2:
            print(f"❌ Error en fallback básico: {e2}")
            # Último fallback: contexto predefinido
            return obtener_contexto_predefinido(tipo_demanda or "Derecho Laboral")

def buscar_contexto_usuario_basico(user_id: str, query: str, tipo_demanda: str = None, top_k: int = 3) -> str:
    """Busca contexto en la colección personal del usuario (fallback cuando falla búsqueda enriquecida)."""
    
    try:
        # Usar DocumentProcessor para acceder a la colección personal
        from backend.core.document_processor import DocumentProcessor
        
        doc_processor = DocumentProcessor()
        collection_name = doc_processor.get_user_collection_name(user_id)
        
        print(f"🔍 Buscando en colección personal: {collection_name}")
        
        # Verificar si la colección existe
        if not doc_processor.collection_exists(collection_name):
            print(f"⚠️ Colección personal {collection_name} no existe")
            return obtener_contexto_predefinido(tipo_demanda)
        
        # Buscar documentos relevantes en la colección personal
        resultados = doc_processor.search_similar_documents(
            user_id=user_id,
            query_text=query,
            categoria_id=None,  # Buscar en todas las categorías del usuario
            limit=top_k
        )
        
        if not resultados:
            print(f"⚠️ No se encontraron documentos relevantes en colección personal")
            return obtener_contexto_predefinido(tipo_demanda)
        
        # Construir contexto desde los documentos encontrados
        contexto_parts = []
        for i, resultado in enumerate(resultados):
            documento = resultado.get('documento', {})
            payload = documento.get('payload', {})
            
            # Extraer texto relevante
            texto = resultado.get('texto_relevante', '') or payload.get('texto_completo', '')[:300]
            filename = payload.get('filename', f'Documento {i+1}')
            
            if texto:
                parte_contexto = f"DOCUMENTO {i+1} ({filename}): {texto}"
                if len(parte_contexto) > 400:  # Limitar longitud
                    parte_contexto = parte_contexto[:400] + "..."
                contexto_parts.append(parte_contexto)
        
        if contexto_parts:
            contexto_personal = " || ".join(contexto_parts)
            print(f"✅ Contexto extraído de {len(contexto_parts)} documentos personales")
            return f"CONTEXTO DE TUS DOCUMENTOS PERSONALES: {contexto_personal}"
        else:
            return obtener_contexto_predefinido(tipo_demanda)
            
    except Exception as e:
        print(f"❌ Error buscando en colección personal: {e}")
        return obtener_contexto_predefinido(tipo_demanda)

def buscar_contexto_legal_basico(tipo: str, query: str, top_k: int = 2) -> str:
    """Búsqueda básica en colecciones públicas (fallback)."""
    # Mapear el tipo legible al nombre de colección
    nombre_coleccion = mapear_tipo_a_coleccion(tipo)
    collection = f"{COLLECTION_PREFIX}{nombre_coleccion}"
    
    try:
        emb = embedder.embed_query(query)
        search = qdrant.search(
            collection_name=collection, 
            query_vector=emb, 
            limit=top_k, 
            with_payload=True
        )
        
        contexto_parts = []
        for i, resultado in enumerate(search):
            payload = resultado.payload
            # Solo incluir partes clave y resumidas
            hechos = payload.get('hechos', '')[:300] + "..." if len(payload.get('hechos', '')) > 300 else payload.get('hechos', '')
            derecho = payload.get('derecho', '')[:200] + "..." if len(payload.get('derecho', '')) > 200 else payload.get('derecho', '')
            
            parte_contexto = f"CASO {i+1}: HECHOS: {hechos} | DERECHO: {derecho}"
            contexto_parts.append(parte_contexto)
        
        return " | ".join(contexto_parts) if contexto_parts else obtener_contexto_predefinido(tipo)
    except Exception as e:
        print(f"Error buscando contexto para tipo '{tipo}' (colección: {collection}): {e}")
        return obtener_contexto_predefinido(tipo)

def obtener_contexto_predefinido(tipo_demanda: str) -> str:
    """Proporciona contexto legal predefinido cuando no hay casos en la base de datos."""
    
    contextos_predefinidos = {
        "Derecho Laboral": """
        CONTEXTO LEGAL PREDEFINIDO - DERECHO LABORAL:
        
        HECHOS TÍPICOS: Despido injustificado de empleado en relación de dependencia. Trabajador con antigüedad que fue desvinculado sin causa justa invocada por el empleador.
        
        DERECHO APLICABLE: 
        - Ley de Contrato de Trabajo 20.744 - Art. 245: Indemnización por despido sin justa causa
        - LCT Art. 232: Preaviso 
        - LCT Art. 233: Integración del mes de despido
        - LCT Art. 258: Indemnización por antigüedad
        
        JURISPRUDENCIA: "El despido sin causa es una facultad del empleador que debe indemnizar según los arts. 232, 233 y 245 de la LCT" (CNAT).
        
        PETITORIO TÍPICO: Indemnización por despido (Art. 245), preaviso (Art. 232), integración del mes de despido (Art. 233), diferencias salariales si las hubiere.
        
        PRUEBAS HABITUALES: Recibos de sueldo, telegrama de despido, certificado de servicios, testimonios de compañeros de trabajo.
        """,
        
        "Empleados En Blanco": """
        CONTEXTO LEGAL PREDEFINIDO - EMPLEADOS EN BLANCO:
        
        HECHOS TÍPICOS: Trabajador registrado que sufrió despido sin causa. Relación laboral documentada con aportes y contribuciones al día.
        
        DERECHO APLICABLE:
        - LCT Art. 245: Indemnización por despido sin justa causa equivalente a un mes de sueldo por año de antigüedad
        - LCT Art. 232/233: Preaviso e integración
        - Ley 25.323: Incremento indemnizatorio por falta de pago en término
        
        MONTO INDEMNIZATORIO: Un mes de sueldo por año de antigüedad o fracción mayor a 3 meses.
        """,
        
        "Empleados En Negro": """
        CONTEXTO LEGAL PREDEFINIDO - TRABAJADORES NO REGISTRADOS:
        
        HECHOS TÍPICOS: Trabajador no registrado o parcialmente registrado. Prestación de servicios sin alta tempestiva en AFIP.
        
        DERECHO APLICABLE:
        - Ley 24.013 Art. 8, 9 y 10: Indemnizaciones por falta de registración
        - Ley 25.323: Incrementos indemnizatorios
        - LCT Art. 245: Indemnización común por despido
        
        INDEMNIZACIONES ESPECIALES: Doble indemnización del Art. 245, plus del 25% del Art. 9, indemnización sustitutiva del preaviso incrementada.
        """
    }
    
    # Buscar contexto específico o usar genérico
    contexto = contextos_predefinidos.get(tipo_demanda)
    if contexto:
        return contexto.strip()
    
    # Contexto genérico para cualquier tipo
    return """
    CONTEXTO LEGAL GENÉRICO - DERECHO LABORAL:
    
    PRINCIPIOS FUNDAMENTALES:
    - Principio protectorio del trabajador (Art. 9 LCT)
    - Indubio pro operario en caso de duda
    - Primacía de la realidad sobre las formas
    
    BASE LEGAL COMÚN:
    - Ley de Contrato de Trabajo 20.744
    - Ley Nacional de Empleo 24.013  
    - Ley de Riesgos del Trabajo 24.557
    - Código Civil y Comercial (subsidiario)
    
    ESTRUCTURA DE DEMANDA:
    1. Hechos cronológicos y precisos
    2. Derecho aplicable con citas normativas
    3. Petitorio claro y fundado
    4. Ofrecimiento de prueba específico
    """

# Mantener función original para compatibilidad
def buscar_contexto_legal(tipo: str, query: str, top_k: int = 2) -> str:
    """Busca contexto legal relevante en la base de datos vectorial (función legacy)."""
    return buscar_contexto_legal_basico(tipo, query, top_k)

def generar_demanda(tipo_demanda: str, datos_cliente: Dict, hechos_adicionales: str = "", notas_abogado: str = "", user_id: str = None) -> Dict:
    """Genera una demanda completa basada en el contexto legal enriquecido con anotaciones."""
    
    # Construir query de búsqueda
    query_busqueda = f"{hechos_adicionales} {datos_cliente.get('motivo_demanda', '')} {notas_abogado}"
    
    # NUEVO: Usar contexto enriquecido con anotaciones si se proporciona user_id
    if user_id:
        print(f"🔍 Usando contexto enriquecido con anotaciones para user {user_id}")
        contexto_legal = buscar_contexto_legal_enriquecido(user_id, query_busqueda, tipo_demanda)
    else:
        print(f"🔍 Usando contexto básico (sin user_id)")
        contexto_legal = obtener_contexto_predefinido(tipo_demanda)
    
    # Prompt mejorado para generar demanda profesional
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un abogado especialista en derecho laboral argentino. 
        Redacta una demanda profesional, completa y técnicamente correcta.
        
        ESTRUCTURA OBLIGATORIA:
        1. ENCABEZADO (Tribunal, Expediente, Caratula)
        2. HECHOS (numerados y claros)
        3. DERECHO (LCT artículos específicos)
        4. PETITORIO (solicitudes concretas)
        5. OFRECIMIENTO DE PRUEBA
        6. FIRMA DEL LETRADO
        
        Usa lenguaje jurídico formal, cita artículos LCT específicos, y estructura según código procesal argentino."""),
        
        ("human", """CLIENTE: {datos_cliente}
TIPO: {tipo_demanda}
HECHOS: {hechos_adicionales}
NOTAS: {notas_abogado}

CONTEXTO LEGAL: {contexto_legal}

Redacta una demanda completa siguiendo la estructura obligatoria.""")
    ])
    
    try:
        # Formatear datos del cliente de manera legible
        datos_formateados = "\n".join([f"• {k.upper()}: {v}" for k, v in datos_cliente.items() if v])
        
        # Generar la demanda con timeout específico
        messages = prompt.format_messages(
            datos_cliente=datos_formateados,
            tipo_demanda=tipo_demanda,
            hechos_adicionales=hechos_adicionales,
            notas_abogado=notas_abogado,
            contexto_legal=contexto_legal
        )
        
        # Configurar timeout para la operación de IA
        start_time = time.time()
        
        try:
            respuesta = llm.invoke(messages)
            texto_demanda = respuesta.content
        except Exception as llm_error:
            elapsed_time = time.time() - start_time
            if elapsed_time > 60:  # Si tardó más de 1 minuto
                raise TimeoutError(f"La generación de la demanda tardó demasiado ({elapsed_time:.1f}s)")
            else:
                raise llm_error
        
        # Crear documento Word
        archivo_docx = crear_documento_word(texto_demanda, datos_cliente, tipo_demanda)
        
        return {
            "texto_demanda": texto_demanda,
            "archivo_docx": archivo_docx,
            "metadatos": {
                "tipo_demanda": tipo_demanda,
                "fecha_generacion": datetime.now().isoformat(),
                "cliente": datos_cliente.get("nombre_completo", "No especificado"),
                "casos_consultados": len(contexto_legal.split("--- CASO PRECEDENTE ---")) - 1,
                "tiempo_generacion": time.time() - start_time
            }
        }
        
    except TimeoutError as e:
        raise Exception(f"Timeout en generación: {str(e)}")
    except Exception as e:
        raise Exception(f"Error generando demanda: {str(e)}")

def crear_documento_word(texto_demanda: str, datos_cliente: Dict, tipo_demanda: str) -> str:
    """Crea un documento Word con la demanda generada - tipografía completamente en negro."""
    try:
        from docx.shared import RGBColor
        from docx.enum.text import WD_COLOR_INDEX
        
        # Crear documento
        doc = Document()
        
        # Configurar título en negro
        titulo = doc.add_heading(f'DEMANDA - {tipo_demanda.upper()}', 0)
        titulo.alignment = 1  # Centrado
        # Asegurar color negro en título
        for run in titulo.runs:
            run.font.color.rgb = RGBColor(0, 0, 0)  # Negro
        
        # Agregar información del cliente
        encabezado_cliente = doc.add_heading('DATOS DEL CLIENTE', level=1)
        # Asegurar color negro en encabezado
        for run in encabezado_cliente.runs:
            run.font.color.rgb = RGBColor(0, 0, 0)
        
        tabla_cliente = doc.add_table(rows=0, cols=2)
        tabla_cliente.style = 'Table Grid'
        
        for campo, valor in datos_cliente.items():
            if valor:
                row = tabla_cliente.add_row()
                # Configurar texto en negro para la tabla
                cell_campo = row.cells[0]
                cell_valor = row.cells[1]
                
                cell_campo.text = campo.replace('_', ' ').title()
                cell_valor.text = str(valor)
                
                # Asegurar color negro en celdas
                for paragraph in cell_campo.paragraphs:
                    for run in paragraph.runs:
                        run.font.color.rgb = RGBColor(0, 0, 0)
                for paragraph in cell_valor.paragraphs:
                    for run in paragraph.runs:
                        run.font.color.rgb = RGBColor(0, 0, 0)
        
        # Agregar salto de página
        doc.add_page_break()
        
        # Agregar texto de la demanda
        encabezado_demanda = doc.add_heading('DEMANDA', level=1)
        # Asegurar color negro en encabezado
        for run in encabezado_demanda.runs:
            run.font.color.rgb = RGBColor(0, 0, 0)
        
        # Dividir el texto en párrafos y procesar
        paragrafos = texto_demanda.split('\n\n')
        for parrafo in paragrafos:
            if parrafo.strip():
                # Verificar si es un encabezado de sección
                es_encabezado = any(keyword in parrafo.upper() for keyword in ['HECHOS', 'DERECHO', 'PETITORIO', 'PRUEBA'])
                
                if es_encabezado:
                    # Crear como encabezado pero en negro
                    p = doc.add_heading(parrafo.strip(), level=2)
                    for run in p.runs:
                        run.font.color.rgb = RGBColor(0, 0, 0)
                else:
                    # Crear como párrafo normal en negro
                    p = doc.add_paragraph(parrafo.strip())
                    for run in p.runs:
                        run.font.color.rgb = RGBColor(0, 0, 0)
        
        # Guardar en archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        doc.save(temp_file.name)
        
        return temp_file.name
        
    except Exception as e:
        raise Exception(f"Error creando documento Word: {str(e)}")

def validar_datos_cliente(datos: Dict) -> Dict:
    """Valida y formatea los datos del cliente."""
    campos_requeridos = ['nombre_completo', 'dni', 'domicilio']
    campos_faltantes = [campo for campo in campos_requeridos if not datos.get(campo)]
    
    if campos_faltantes:
        raise ValueError(f"Faltan campos obligatorios: {', '.join(campos_faltantes)}")
    
    return datos

# Ejemplo de uso:
if __name__ == "__main__":
    datos = {
        "nombre": "Romina Gabriela Ruth Vaca",
        "dni": "32501402",
        "domicilio": "Itaqui 2099, CABA",
        "fecha_nacimiento": "27/10/1986",
        "email": "v.romina7529@gmail.com",
        "estado_civil": "Soltera",
        "motivo": "despido mientras estaba con licencia médica"
    }
    resultado = generar_demanda("Demanda con licencia medica", datos)
    print(resultado)