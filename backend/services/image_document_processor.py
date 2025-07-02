"""
Procesador Especializado de Documentos Legales con GPT-4 Vision
Extrae TODA la información de documentos como telegramas, liquidaciones, recibos de sueldo.
Optimizado para el workflow del abogado según su prompt específico.
"""

import base64
import json
import asyncio
from typing import Dict, List, Tuple, Optional, Any
from openai import OpenAI
import os
from datetime import datetime
import re
from PIL import Image
import io
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalDocumentProcessor:
    """Procesador especializado para documentos legales con extracción completa."""
    
    def __init__(self):
        """Inicializar el procesador con configuración optimizada."""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not self.client.api_key:
            raise ValueError("OPENAI_API_KEY no configurada")
        
        # Configuración de procesamiento
        self.max_image_size = (2048, 2048)
        self.supported_formats = ['image/jpeg', 'image/png', 'image/webp']
        
        # Prompts especializados por tipo de documento
        self.prompts_especializados = {
            'telegrama': self._get_telegrama_prompt(),
            'carta_documento': self._get_carta_documento_prompt(),
            'liquidacion': self._get_liquidacion_prompt(),
            'recibo_sueldo': self._get_recibo_sueldo_prompt(),
            'imagen_general': self._get_general_prompt()
        }
    
    async def procesar_imagenes_multiples(
        self, 
        imagenes: List[Tuple[bytes, str, str]],  # [(imagen_bytes, nombre, tipo_documento)]
        session_id: str,
        abogado_id: str
    ) -> Dict[str, Any]:
        """
        Procesa múltiples imágenes de manera concurrente.
        
        Args:
            imagenes: Lista de tuplas (bytes, nombre_archivo, tipo_documento)
            session_id: ID de la sesión de chat
            abogado_id: ID del abogado
            
        Returns:
            Dict con resultados consolidados
        """
        logger.info(f"🚀 Procesando {len(imagenes)} imágenes para sesión {session_id}")
        
        # Procesar imágenes en paralelo (máximo 3 concurrentes para evitar rate limits)
        semaforo = asyncio.Semaphore(3)
        
        tareas = []
        for i, (imagen_bytes, nombre, tipo_doc) in enumerate(imagenes):
            tarea = self._procesar_imagen_individual(
                imagen_bytes, nombre, tipo_doc, session_id, abogado_id, semaforo
            )
            tareas.append(tarea)
        
        # Ejecutar todas las tareas
        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        
        # Consolidar resultados
        resultados_exitosos = []
        errores = []
        
        for i, resultado in enumerate(resultados):
            if isinstance(resultado, Exception):
                errores.append({
                    'archivo': imagenes[i][1],
                    'error': str(resultado)
                })
                logger.error(f"❌ Error procesando {imagenes[i][1]}: {resultado}")
            else:
                resultados_exitosos.append(resultado)
                logger.info(f"✅ Procesado exitosamente: {imagenes[i][1]}")
        
        # Generar resumen consolidado
        resumen_consolidado = self._consolidar_resultados(resultados_exitosos)
        
        return {
            'resultados_individuales': resultados_exitosos,
            'errores': errores,
            'resumen_consolidado': resumen_consolidado,
            'total_procesados': len(resultados_exitosos),
            'total_errores': len(errores),
            'session_id': session_id
        }
    
    async def _procesar_imagen_individual(
        self,
        imagen_bytes: bytes,
        nombre_archivo: str,
        tipo_documento: str,
        session_id: str,
        abogado_id: str,
        semaforo: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """Procesa una imagen individual con GPT-4 Vision."""
        
        async with semaforo:  # Limitar concurrencia
            try:
                logger.info(f"📄 Procesando imagen: {nombre_archivo} (tipo: {tipo_documento})")
                
                # Optimizar imagen
                imagen_optimizada = self._optimizar_imagen(imagen_bytes)
                
                # Obtener prompt especializado
                prompt = self.prompts_especializados.get(tipo_documento, self.prompts_especializados['imagen_general'])
                
                # Llamar a GPT-4 Vision
                response = self.client.chat.completions.create(
                    model="gpt-4o",  # Usar modelo más reciente con visión
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{imagen_optimizada}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=4000,
                    temperature=0.1  # Baja temperatura para mayor precisión
                )
                
                # Extraer contenido
                contenido_crudo = response.choices[0].message.content
                
                # Parsear JSON si es posible
                datos_estructurados = self._parsear_contenido_estructurado(contenido_crudo)
                
                # Extraer texto limpio
                texto_extraido = self._extraer_texto_limpio(contenido_crudo, datos_estructurados)
                
                resultado = {
                    'nombre_archivo': nombre_archivo,
                    'tipo_documento': tipo_documento,
                    'texto_extraido': texto_extraido,
                    'datos_estructurados': datos_estructurados,
                    'metadatos_procesamiento': {
                        'modelo_usado': 'gpt-4o',
                        'timestamp': datetime.now().isoformat(),
                        'tokens_utilizados': response.usage.total_tokens,
                        'tamaño_imagen_bytes': len(imagen_bytes),
                        'session_id': session_id
                    },
                    'procesado_exitosamente': True
                }
                
                logger.info(f"✅ Imagen procesada: {nombre_archivo} ({response.usage.total_tokens} tokens)")
                return resultado
                
            except Exception as e:
                logger.error(f"❌ Error procesando {nombre_archivo}: {str(e)}")
                return {
                    'nombre_archivo': nombre_archivo,
                    'tipo_documento': tipo_documento,
                    'error': str(e),
                    'procesado_exitosamente': False,
                    'timestamp': datetime.now().isoformat()
                }
    
    def _optimizar_imagen(self, imagen_bytes: bytes) -> str:
        """Optimiza la imagen para GPT-4 Vision."""
        try:
            # Abrir imagen
            imagen = Image.open(io.BytesIO(imagen_bytes))
            
            # Convertir a RGB si es necesario
            if imagen.mode in ('RGBA', 'P'):
                imagen = imagen.convert('RGB')
            
            # Redimensionar si es muy grande
            if imagen.size[0] > self.max_image_size[0] or imagen.size[1] > self.max_image_size[1]:
                imagen.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
            
            # Convertir a bytes optimizados
            buffer = io.BytesIO()
            imagen.save(buffer, format='JPEG', quality=85, optimize=True)
            imagen_optimizada = buffer.getvalue()
            
            # Convertir a base64
            return base64.b64encode(imagen_optimizada).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error optimizando imagen: {e}")
            # Fallback: usar imagen original
            return base64.b64encode(imagen_bytes).decode('utf-8')
    
    def _consolidar_resultados(self, resultados: List[Dict]) -> Dict[str, Any]:
        """Consolida la información de todos los documentos procesados."""
        
        consolidado = {
            'transcripcion_completa': '',
            'personas_identificadas': set(),
            'empresas_identificadas': set(),
            'fechas_importantes': [],
            'montos_encontrados': [],
            'datos_contacto': {},
            'resumen_cronologico': [],
            'documentos_procesados': len(resultados)
        }
        
        for resultado in resultados:
            if not resultado.get('procesado_exitosamente', False):
                continue
                
            # Agregar transcripción
            if resultado.get('texto_extraido'):
                consolidado['transcripcion_completa'] += f"\n\n=== {resultado['nombre_archivo']} ===\n"
                consolidado['transcripcion_completa'] += resultado['texto_extraido']
            
            # Consolidar datos estructurados
            datos_struct = resultado.get('datos_estructurados', {})
            
            # Personas
            if 'datos_personales' in datos_struct:
                nombres = datos_struct['datos_personales'].get('nombres_personas', [])
                consolidado['personas_identificadas'].update(nombres)
            
            # Empresas
            if 'datos_empresas' in datos_struct:
                empresas = datos_struct['datos_empresas'].get('nombres_empresas', [])
                consolidado['empresas_identificadas'].update(empresas)
            
            # Fechas
            if 'fechas_encontradas' in datos_struct:
                consolidado['fechas_importantes'].extend(datos_struct['fechas_encontradas'])
            
            # Montos
            if 'montos_encontrados' in datos_struct:
                consolidado['montos_encontrados'].extend(datos_struct['montos_encontrados'])
            
            # Cronología
            if 'fecha_documento' in datos_struct:
                consolidado['resumen_cronologico'].append({
                    'fecha': datos_struct['fecha_documento'],
                    'documento': resultado['nombre_archivo'],
                    'tipo': resultado['tipo_documento'],
                    'evento': datos_struct.get('evento_principal', 'Documento recibido')
                })
        
        # Convertir sets a listas para JSON
        consolidado['personas_identificadas'] = list(consolidado['personas_identificadas'])
        consolidado['empresas_identificadas'] = list(consolidado['empresas_identificadas'])
        
        # Ordenar cronología
        consolidado['resumen_cronologico'].sort(key=lambda x: x.get('fecha', ''))
        
        return consolidado
    
    def _parsear_contenido_estructurado(self, contenido: str) -> Dict[str, Any]:
        """Intenta extraer datos estructurados del contenido."""
        try:
            # Buscar JSON en el contenido
            patron_json = r'\{(?:[^{}]|{[^{}]*})*\}'
            matches = re.findall(patron_json, contenido, re.DOTALL)
            
            if matches:
                # Intentar parsear el JSON más grande
                json_candidato = max(matches, key=len)
                return json.loads(json_candidato)
                
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Fallback: extraer datos básicos con regex
        return self._extraer_datos_con_regex(contenido)
    
    def _extraer_datos_con_regex(self, contenido: str) -> Dict[str, Any]:
        """Extrae datos básicos usando regex como fallback."""
        datos = {
            'datos_personales': {'nombres_personas': []},
            'datos_empresas': {'nombres_empresas': []},
            'fechas_encontradas': [],
            'montos_encontrados': []
        }
        
        # Fechas (varios formatos)
        patron_fechas = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\b'
        fechas = re.findall(patron_fechas, contenido, re.IGNORECASE)
        datos['fechas_encontradas'] = fechas
        
        # Montos
        patron_montos = r'\$\s*[\d.,]+|\b\d+[.,]\d{2}\s*pesos\b'
        montos = re.findall(patron_montos, contenido, re.IGNORECASE)
        datos['montos_encontrados'] = montos
        
        return datos
    
    def _extraer_texto_limpio(self, contenido_crudo: str, datos_estructurados: Dict) -> str:
        """Extrae texto limpio removiendo marcadores JSON."""
        texto = contenido_crudo
        
        # Remover bloques JSON
        patron_json = r'\{(?:[^{}]|{[^{}]*})*\}'
        texto = re.sub(patron_json, '', texto, flags=re.DOTALL)
        
        # Limpiar texto
        texto = re.sub(r'\n+', '\n', texto)
        texto = texto.strip()
        
        return texto
    
    # PROMPTS ESPECIALIZADOS PARA CADA TIPO DE DOCUMENTO
    
    def _get_telegrama_prompt(self) -> str:
        """Prompt especializado para telegramas."""
        return """
Eres un experto en documentos legales argentinos. Analiza esta imagen de un telegrama y extrae TODA la información presente.

INSTRUCCIONES ESPECÍFICAS:
1. Transcribe TODO el texto palabra por palabra, respetando formato y estructura
2. Identifica y extrae datos específicos en formato JSON al final
3. Presta especial atención a: fechas, nombres de personas, empresas, números de telegrama, remitente, destinatario

FORMATO DE RESPUESTA:
Primero la transcripción completa del telegrama, luego datos estructurados en JSON:

TRANSCRIPCIÓN COMPLETA:
[Aquí toda la transcripción literal]

DATOS ESTRUCTURADOS:
{
  "tipo_documento": "telegrama",
  "numero_telegrama": "...",
  "fecha_envio": "...",
  "fecha_recepcion": "...", 
  "remitente": "...",
  "destinatario": "...",
  "datos_personales": {
    "nombres_personas": ["nombre1", "nombre2"],
    "dni_encontrados": ["12345678"]
  },
  "datos_empresas": {
    "nombres_empresas": ["empresa1"],
    "domicilios": ["dirección1"]
  },
  "contenido_legal": {
    "tipo_reclamo": "...",
    "plazos_mencionados": [],
    "montos_reclamados": []
  }
}

EXTRAE TODO EL CONTENIDO SIN OMITIR NADA.
"""

    def _get_carta_documento_prompt(self) -> str:
        """Prompt especializado para cartas documento."""
        return """
Eres un experto en documentos legales argentinos. Analiza esta carta documento y extrae TODA la información.

INSTRUCCIONES:
1. Transcribe TODO el contenido literal de la carta
2. Identifica datos legales relevantes
3. Extrae fechas, personas, empresas, reclamos, plazos

FORMATO DE RESPUESTA:
TRANSCRIPCIÓN COMPLETA:
[Contenido literal completo]

DATOS ESTRUCTURADOS:
{
  "tipo_documento": "carta_documento",
  "fecha_documento": "...",
  "remitente_abogado": "...",
  "destinatario": "...",
  "datos_personales": {
    "nombres_personas": [],
    "dni_encontrados": [],
    "domicilios": []
  },
  "datos_empresas": {
    "nombres_empresas": [],
    "cuit_encontrados": [],
    "domicilios_legales": []
  },
  "contenido_legal": {
    "tipo_reclamo": "...",
    "plazo_intimacion": "...",
    "consecuencias_advertidas": [],
    "montos_reclamados": [],
    "normativa_citada": []
  }
}
"""

    def _get_liquidacion_prompt(self) -> str:
        """Prompt especializado para liquidaciones."""
        return """
Eres un experto en liquidaciones laborales argentinas. Analiza esta liquidación y extrae TODOS los datos.

INSTRUCCIONES:
1. Transcribe TODOS los ítems, conceptos y montos
2. Identifica empleado, empleador, período
3. Extrae todos los conceptos: haberes, descuentos, aportes

FORMATO DE RESPUESTA:
TRANSCRIPCIÓN COMPLETA:
[Todos los conceptos y montos literales]

DATOS ESTRUCTURADOS:
{
  "tipo_documento": "liquidacion",
  "fecha_liquidacion": "...",
  "periodo_liquidado": "...",
  "empleado": {
    "nombre": "...",
    "dni": "...",
    "legajo": "..."
  },
  "empleador": {
    "razon_social": "...",
    "cuit": "...",
    "domicilio": "..."
  },
  "conceptos_haberes": [
    {"concepto": "sueldo_basico", "monto": "..."},
    {"concepto": "horas_extra", "monto": "..."}
  ],
  "conceptos_descuentos": [
    {"concepto": "jubilacion", "monto": "..."},
    {"concepto": "obra_social", "monto": "..."}
  ],
  "totales": {
    "total_haberes": "...",
    "total_descuentos": "...",
    "neto_a_cobrar": "..."
  }
}
"""

    def _get_recibo_sueldo_prompt(self) -> str:
        """Prompt especializado para recibos de sueldo."""
        return """
Eres un experto en recibos de sueldo argentinos. Analiza este recibo y extrae TODA la información.

INSTRUCCIONES:
1. Transcribe TODOS los conceptos, montos, códigos
2. Identifica trabajador, empresa, período
3. Extrae conceptos remunerativos y no remunerativos

FORMATO DE RESPUESTA:
TRANSCRIPCIÓN COMPLETA:
[Todos los datos del recibo literales]

DATOS ESTRUCTURADOS:
{
  "tipo_documento": "recibo_sueldo",
  "fecha_recibo": "...",
  "periodo": "...",
  "trabajador": {
    "nombre_completo": "...",
    "dni": "...",
    "cuil": "...",
    "legajo": "...",
    "categoria": "...",
    "fecha_ingreso": "..."
  },
  "empleador": {
    "razon_social": "...",
    "cuit": "...",
    "actividad": "..."
  },
  "conceptos_remunerativos": [],
  "conceptos_no_remunerativos": [],
  "descuentos_legales": [],
  "totales": {
    "total_remunerativo": "...",
    "total_no_remunerativo": "...",
    "total_descuentos": "...",
    "neto_pagado": "..."
  }
}
"""

    def _get_general_prompt(self) -> str:
        """Prompt general para cualquier documento legal."""
        return """
Eres un experto en documentos legales argentinos. Analiza esta imagen y extrae TODA la información visible.

INSTRUCCIONES:
1. Transcribe TODO el texto que puedas leer
2. Identifica el tipo de documento
3. Extrae datos relevantes: nombres, fechas, números, montos

FORMATO DE RESPUESTA:
TRANSCRIPCIÓN COMPLETA:
[Todo el texto visible]

DATOS ESTRUCTURADOS:
{
  "tipo_documento_detectado": "...",
  "fecha_documento": "...",
  "datos_personales": {
    "nombres_personas": [],
    "documentos_identidad": []
  },
  "datos_empresas": {
    "nombres_empresas": [],
    "identificaciones_fiscales": []
  },
  "fechas_encontradas": [],
  "montos_encontrados": [],
  "observaciones": "..."
}

EXTRAE TODO SIN OMITIR INFORMACIÓN.
""" 