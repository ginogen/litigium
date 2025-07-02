import os
import json
import time
import re
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from rag.qa_agent import obtener_tipos_demanda_disponibles, generar_demanda, validar_datos_cliente
from datetime import datetime

load_dotenv()

class ChatAgentInteligente:
    def __init__(self, user_id: str = None):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno")
        
        self.client = OpenAI(
            api_key=api_key,
            timeout=60.0  # Timeout de 60 segundos para OpenAI
        )
        self.user_id = user_id
        # Inicializar tipos dinámicos si tenemos user_id
        if user_id:
            try:
                from rag.qa_agent import obtener_tipos_demanda_por_abogado
                self.tipos_disponibles = obtener_tipos_demanda_por_abogado(user_id)
                print(f"✅ ChatAgentInteligente inicializado con {len(self.tipos_disponibles)} tipos dinámicos para user_id: {user_id}")
            except Exception as e:
                print(f"⚠️ Error obteniendo tipos dinámicos: {e}")
                self.tipos_disponibles = self._tipos_fallback()
        else:
            # Fallback con tipos básicos si no hay user_id
            self.tipos_disponibles = self._tipos_fallback()
            print(f"✅ ChatAgentInteligente inicializado con {len(self.tipos_disponibles)} tipos básicos (sin user_id)")
        
    def _tipos_fallback(self) -> list:
        return [
            "Despido",
            "Empleados En Blanco", 
            "Empleados En Negro", 
            "Demanda Licencia Medica", 
            "Demanda Solidaridad Laboral",
            "Empleados Blanco Negro"
        ]
    
    def _extraer_datos_fallback(self, mensaje: str, session: Dict) -> Dict:
        """Método de fallback usando regex para extraer datos básicos cuando OpenAI falla."""
        print("🔧 Usando extracción de fallback con regex...")
        
        datos_extraidos = {}
        hechos_extraidos = ""
        tipo_detectado = session.get("tipo_demanda")  # Usar tipo previamente seleccionado
        
        # Patrones mejorados para formato "Nombre, Dirección, DNI"
        patron_dni = r'(?:^|,\s*)(\d{7,8})(?=\s*,?\s*$|(?:\s+me\s+|\s+despid))'  # DNI al final o antes de descripción
        
        # Patrón para nombres (buscar 2-3 palabras que empiecen con mayúscula)
        patron_nombre_formato1 = r'^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?: [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,2})'  # Al inicio
        patron_nombre_formato2 = r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?: [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)(?=\s*,)'  # Antes de coma
        
        # Patrón para direcciones (Paraguay + número, Av + nombre + número, etc.)
        patron_direccion = r'((?:Paraguay|Av\.|Avenida|Calle|Rivadavia|San Martín|Corrientes)\s+[^,]+?\s*\d+[^,]*?)(?=\s*,|\s*\d{7,8}|$)'
        
        # Intentar extraer DNI primero
        match_dni = re.search(patron_dni, mensaje, re.IGNORECASE)
        if match_dni:
            datos_extraidos["dni"] = match_dni.group(1)
            print(f"🔧 DNI encontrado: {datos_extraidos['dni']}")
            
        # Intentar extraer nombre (varios patrones)
        match_nombre = re.search(patron_nombre_formato1, mensaje) or re.search(patron_nombre_formato2, mensaje)
        if match_nombre:
            datos_extraidos["nombre_completo"] = match_nombre.group(1).strip()
            print(f"🔧 Nombre encontrado: {datos_extraidos['nombre_completo']}")
            
        # Intentar extraer dirección
        match_direccion = re.search(patron_direccion, mensaje, re.IGNORECASE)
        if match_direccion:
            datos_extraidos["domicilio"] = match_direccion.group(1).strip()
            print(f"🔧 Dirección encontrada: {datos_extraidos['domicilio']}")
            
        # Extraer hechos básicos (despido, problemas laborales)
        hechos_keywords = []
        if "despid" in mensaje.lower():
            hechos_keywords.append("despido")
        if "sin causa" in mensaje.lower():
            hechos_keywords.append("sin causa aparente")
        if "empresa" in mensaje.lower():
            # Buscar nombre de empresa después de "empresa"
            match_empresa = re.search(r'empresa\s+([A-Z][A-Z0-9]*)', mensaje, re.IGNORECASE)
            if match_empresa:
                hechos_keywords.append(f"empresa {match_empresa.group(1)}")
                
        if hechos_keywords:
            hechos_extraidos = f"Cliente reporta: {', '.join(hechos_keywords)}. Contexto completo: {mensaje}"
        
        print(f"🔧 Fallback extrajo - Nombre: {datos_extraidos.get('nombre_completo')}, DNI: {datos_extraidos.get('dni')}, Dirección: {datos_extraidos.get('domicilio')}")
        print(f"🔧 Hechos extraídos: {hechos_extraidos[:100]}...")
        
        return {
            "accion": "continuar_conversacion",
            "tipo_demanda_detectado": tipo_detectado,
            "datos_extraidos": datos_extraidos,
            "hechos_extraidos": hechos_extraidos if hechos_extraidos else None,
            "notas_extraidas": None,
            "mensaje_respuesta": "He extraído la información básica de tu mensaje. ¿Te parece correcta? Si falta algo, puedes agregarlo.",
            "listo_para_generar": bool(datos_extraidos.get("nombre_completo") and datos_extraidos.get("dni") and tipo_detectado and hechos_extraidos)
        }
        
    async def procesar_mensaje(self, session: Dict, mensaje_usuario: str, session_id: str) -> Dict:
        """Procesa un mensaje usando IA para entender la intención y extraer información."""
        
        print(f"🚨 INICIO procesar_mensaje")
        
        try:
            print(f"🚨 DENTRO del try")
            # Debug: mostrar lo que recibimos
            print(f"🔍 ChatAgent recibió:")
            print(f"   session tipo: {type(session)}")
            print(f"   session keys: {list(session.keys()) if session else 'None'}")
            print(f"   mensaje: {mensaje_usuario[:50]}...")
            print(f"   session_id: {session_id}")
            print(f"🚨 DEBUG completado")
            
            # Validar parámetros de entrada
            print(f"🔍 Validando parámetros...")
            if not session:
                raise ValueError("Sesión no puede ser None")
            if not mensaje_usuario or not mensaje_usuario.strip():
                raise ValueError("Mensaje del usuario no puede estar vacío")
            if not session_id:
                raise ValueError("Session ID no puede estar vacío")
            print(f"✅ Parámetros válidos")
                
            # Inicializar datos_cliente si no existe
            print(f"🔍 Inicializando datos_cliente...")
            print(f"   'datos_cliente' in session: {'datos_cliente' in session}")
            if 'datos_cliente' not in session:
                session['datos_cliente'] = {}
            print(f"✅ datos_cliente inicializado")
            
            # VERIFICAR SI ES EL PRIMER MENSAJE (estado = "inicio")
            # Si es el primer mensaje, mostrar siempre el mensaje inicial
            estado_actual = session.get("estado", "inicio")
            if estado_actual == "inicio":
                print(f"🎯 Primer mensaje detectado - mostrando mensaje inicial")
                
                # IMPORTANTE: Actualizar el estado antes de retornar
                session["estado"] = "conversando"
                print(f"🔄 Estado actualizado: 'inicio' → 'conversando'")
                
                # Obtener categorías disponibles para mostrar como opciones
                opciones_categorias = []
                if hasattr(self, 'tipos_disponibles') and self.tipos_disponibles:
                    opciones_categorias = [f"Quiero ayuda con {tipo}" for tipo in self.tipos_disponibles]
                
                return {
                    "session_id": session_id,
                    "mensaje": self._generar_mensaje_inicial(),
                    "tipo": "bot",
                    "timestamp": datetime.now().isoformat(),
                    "demanda_generada": False,
                    "mostrar_confirmacion": False,
                    "es_mensaje_inicial": True,
                    "opciones": opciones_categorias
                }
            
            # DETECCIÓN AUTOMÁTICA DE INFORMACIÓN DE DOCUMENTOS
            print(f"🔍 Detectando información automática de documentos...")
            cambios_automaticos = self._detectar_informacion_automatica(session, session_id)
            if cambios_automaticos:
                print(f"🤖 Cambios automáticos realizados: {cambios_automaticos}")
                
                # Si se detectó información automáticamente, mostrar inmediatamente
                mensaje_informacion = self._generar_mensaje_informacion_extraida(cambios_automaticos, session, session_id)
                if mensaje_informacion:
                    return {
                        "session_id": session_id,
                        "mensaje": mensaje_informacion,
                        "tipo": "bot",
                        "timestamp": datetime.now().isoformat(),
                        "demanda_generada": False,
                        "mostrar_confirmacion": True,
                        "informacion_extraida": True
                    }
            
            # Obtener contexto de la conversación
            print(f"🔍 Obteniendo contexto de conversación...")
            contexto = self._obtener_contexto_conversacion(session)
            print(f"✅ Contexto obtenido: {len(contexto)} chars")
            
            # Usar OpenAI para procesar el mensaje
            print(f"🔍 Llamando _procesar_con_openai...")
            # Usar tipos dinámicos del abogado o fallback
            tipos_disponibles = self.tipos_disponibles if hasattr(self, 'tipos_disponibles') else self._tipos_fallback()
            print(f"🔍 Tipos disponibles: {tipos_disponibles}")
            
            respuesta_ia = self._procesar_con_openai(mensaje_usuario, contexto, tipos_disponibles, session)
            print(f"✅ Respuesta IA obtenida")
            
            # Actualizar sesión con la información extraída
            print(f"🔍 Actualizando sesión...")
            self._actualizar_sesion(session, respuesta_ia)
            print(f"✅ Sesión actualizada")
            
            # Generar respuesta final usando la nueva lógica inteligente
            print(f"🔍 Generando respuesta inteligente...")
            mensaje_respuesta = self._generar_respuesta_inteligente(session, session_id, mensaje_usuario, respuesta_ia)
            print(f"✅ Respuesta inteligente generada")
            
            # Evaluar si está listo para generar demanda
            evaluacion = self._evaluar_informacion_completa(session, session_id)
            
            return {
                "session_id": session_id,
                "mensaje": mensaje_respuesta,
                "tipo": "bot",
                "timestamp": datetime.now().isoformat(),
                "demanda_generada": False,
                "mostrar_confirmacion": evaluacion["completo"],
                "progreso_completitud": evaluacion["porcentaje_completo"]
            }
            
        except Exception as e:
            print(f"❌ Error en procesar_mensaje: {e}")
            print(f"❌ Tipo de error: {type(e).__name__}")
            
            # Respuesta de fallback en caso de error crítico
            return {
                "session_id": session_id,
                "mensaje": f"❌ Error procesando tu mensaje: {str(e)}. Por favor, intenta reformular tu consulta.",
                "tipo": "bot",
                "timestamp": datetime.now().isoformat(),
                "demanda_generada": False
            }
    
    def _obtener_contexto_conversacion(self, session: Dict) -> str:
        """Obtiene el contexto actual de la conversación."""
        print(f"🔍 _obtener_contexto_conversacion iniciado")
        
        estado = session.get("estado", "inicio")
        tipo_demanda = session.get("tipo_demanda", "") or ""
        datos_cliente = session.get("datos_cliente", {}) or {}
        hechos = session.get("hechos_adicionales", "") or ""
        
        print(f"   estado: {estado}")
        print(f"   tipo_demanda: {tipo_demanda}")
        print(f"   datos_cliente tipo: {type(datos_cliente)}")
        print(f"   datos_cliente valor: {datos_cliente}")
        print(f"   hechos: {(hechos or '')[:50]}...")
        
        # Formato compacto - VALIDAR que datos_cliente sea dict
        datos_compactos = []
        if isinstance(datos_cliente, dict):
            for k, v in datos_cliente.items():
                if v:
                    datos_compactos.append(f"{k}:{v}")
        else:
            print(f"⚠️ datos_cliente no es dict válido: {type(datos_cliente)}")
            # Convertir a dict vacío si no es dict
            datos_cliente = {}
        
        contexto = f"""Estado:{estado}|Tipo:{tipo_demanda}|Datos:{','.join(datos_compactos)}|Hechos:{hechos[:100]}..."""
        print(f"✅ Contexto generado: {contexto[:100]}...")
        return contexto
    
    def _procesar_con_openai(self, mensaje_usuario: str, contexto: str, tipos_disponibles: List[str], session: Dict = None) -> Dict:
        """Usa OpenAI para procesar el mensaje de forma más fluida y natural."""
        
        # Protección contra tipos_disponibles None
        if not tipos_disponibles:
            print("⚠️ tipos_disponibles es None o vacío, usando fallback")
            tipos_disponibles = [
                "Empleados En Blanco", 
                "Empleados En Negro", 
                "Demanda Licencia Medica", 
                "Demanda Solidaridad Laboral",
                "Empleados Blanco Negro"
            ]
        
        prompt = f"""
Eres un asistente legal AI experto y conversacional. Tu objetivo es ayudar al ABOGADO a recopilar información sobre su CLIENTE para generar una demanda de forma NATURAL y FLUIDA.

IMPORTANTE: 
- El USUARIO que te escribe es el ABOGADO
- La información que extraes es sobre el CLIENTE del abogado
- NUNCA hables al abogado como si fuera el cliente
- Siempre dirígete al abogado profesionalmente

CONTEXTO ACTUAL: {contexto}
MENSAJE DEL ABOGADO: "{mensaje_usuario}"

TIPOS DISPONIBLES: {tipos_disponibles}

INSTRUCCIONES PRINCIPALES:
1. **Sé conversacional y profesional** - Habla al abogado, no al cliente
2. **Extrae información del CLIENTE** que el abogado proporciona
3. **Consolida información** - Evalúa todo lo disponible de una vez
4. **Prioriza eficiencia** - No pidas datos uno por uno si hay información suficiente
5. **Aprovecha documentos** - Si hay archivos procesados, úsalos inteligentemente
6. **Sé directo** - Evita confirmaciones excesivas o repetitivas

REGLAS DE EXTRACCIÓN:
- NOMBRES: 2-3 palabras que empiecen con mayúscula (ej: "Gino Gentile")
- DNI: números de 7-8 dígitos sin prefijos (ej: "35703591")
- DIRECCIONES: nombres de calles + números (ej: "Paraguay 2536")
- TELÉFONOS: números con códigos de área o más de 8 dígitos
- HECHOS: cualquier información sobre el caso laboral

MAPEO DE TIPOS (EXACTO):
- "empleados en blanco", "blanco", "trabajo en blanco" → "Empleados En Blanco"
- "empleados en negro", "negro", "trabajo en negro" → "Empleados En Negro"  
- "licencia médica", "licencia medica", "licencia" → "Demanda Licencia Medica"
- "solidaridad" → "Demanda Solidaridad Laboral"
- "blanco negro", "blanco y negro" → "Empleados Blanco Negro"

ESTRATEGIAS DE CONVERSACIÓN:
- Si es el primer mensaje: Saluda y pregunta qué tipo de demanda necesita
- Si menciona un tipo: Confirma y pide datos del cliente de forma natural
- Si da datos parciales: Agradece y pide lo que falta de forma conversacional
- Si da mucha información: Resume lo que entendiste y pregunta si está completo
- Si parece completo: Ofrece generar la demanda o preguntar si falta algo
- Si hay información de imágenes: Úsala automáticamente sin pedir confirmación

EJEMPLOS DE RESPUESTAS PROFESIONALES (ABOGADO):
- "¡Hola doctor! Veo que necesita ayuda con un caso de despido. ¿Podría contarme sobre la situación de su cliente?"
- "Perfecto, entiendo que es un caso de empleado en negro. ¿Tiene los datos del cliente disponibles?"
- "Excelente, ya tengo el nombre y DNI del cliente. ¿En qué empresa trabajaba y cuándo fue el despido?"
- "Veo que tiene toda la información necesaria. ¿Le parece que proceda a generar la demanda o desea agregar algo más?"

IMPORTANTE - MENSAJE_RESPUESTA:
El campo "mensaje_respuesta" DEBE contener una respuesta conversacional natural y útil para el usuario. NUNCA debe ser null, vacío o "N/A". Siempre debe ser una respuesta que ayude al usuario a continuar la conversación.

RESPONDE EN JSON:
{{
    "accion": "saludar|extraer_info|confirmar_datos|sugerir_generar|generar_demanda",
    "tipo_demanda_detectado": "EXACTO_DE_LISTA_O_NULL",
    "datos_extraidos": {{
        "nombre_completo": "NOMBRE_O_NULL",
        "dni": "DNI_O_NULL", 
        "domicilio": "DIRECCION_O_NULL",
        "telefono": "TELEFONO_O_NULL",
        "email": "EMAIL_O_NULL",
        "ocupacion": "TRABAJO_O_NULL"
    }},
    "hechos_extraidos": "HECHOS_DETECTADOS_O_NULL",
    "notas_extraidas": "NOTAS_O_NULL",
    "mensaje_respuesta": "RESPUESTA_CONVERSACIONAL_NATURAL_Y_UTIL",
    "listo_para_generar": false
}}

IMPORTANTE: 
- Números de 7-8 dígitos SON DNI, no teléfonos.
- El mensaje_respuesta DEBE ser una respuesta útil y conversacional.
- NUNCA devuelvas mensaje_respuesta como null, vacío o "N/A".
- NO incluyas sugerencias ni datos_faltantes en el JSON - solo el mensaje conversacional.
"""

        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un experto en extracción de datos legales. SIEMPRE responde en formato JSON válido, siendo MUY inteligente extrayendo información y manteniendo un tono conversacional natural."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Más determinista
                max_tokens=1500   # Más tokens para respuestas completas
            )
            
            elapsed_time = time.time() - start_time
            
            # Verificar que la respuesta existe
            if not response or not response.choices or len(response.choices) == 0:
                raise Exception("OpenAI no devolvió choices válidos")
            
            choice = response.choices[0]
            if not choice or not choice.message or not choice.message.content:
                raise Exception("OpenAI devolvió mensaje vacío o nulo")
            
            # Extraer y parsear la respuesta JSON
            respuesta_texto = choice.message.content.strip()
            
            if not respuesta_texto:
                raise Exception("OpenAI devolvió contenido vacío")
            
            # Limpiar la respuesta si tiene markdown
            if respuesta_texto.startswith("```json"):
                respuesta_texto = respuesta_texto.replace("```json", "").replace("```", "").strip()
            elif respuesta_texto.startswith("```"):
                respuesta_texto = respuesta_texto.replace("```", "").strip()
            
            resultado = json.loads(respuesta_texto)
            resultado["tiempo_openai"] = elapsed_time  # Para debugging
            
            # Debug: mostrar lo que extrajo
            print(f"🔍 IA extrajo: {resultado.get('datos_extraidos', {})}")
            hechos = resultado.get('hechos_extraidos', 'N/A')
            print(f"🔍 Hechos: {hechos[:100] if hechos else 'N/A'}...")
            print(f"🔍 Listo para generar: {resultado.get('listo_para_generar', False)}")
            
            return resultado
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON de OpenAI: {e}")
            try:
                respuesta_raw = response.choices[0].message.content if response and response.choices else "Sin respuesta"
                print(f"📄 Respuesta recibida: {respuesta_raw}")
            except:
                print("📄 No se pudo obtener la respuesta de OpenAI")
            # Respuesta de fallback más inteligente
            return self._extraer_datos_fallback(mensaje_usuario, session or {'tipo_demanda': None})
        except Exception as e:
            print(f"❌ Error procesando con OpenAI: {e}")
            print(f"❌ Tipo de error: {type(e).__name__}")
            # Respuesta de fallback
            return self._extraer_datos_fallback(mensaje_usuario, session or {'tipo_demanda': None})
    
    def _actualizar_sesion(self, session: Dict, respuesta_ia: Dict):
        """Actualiza la sesión con la información extraída por la IA."""
        
        # Actualizar tipo de demanda
        if respuesta_ia.get("tipo_demanda_detectado"):
            session["tipo_demanda"] = respuesta_ia["tipo_demanda_detectado"]
            print(f"🎯 Tipo de demanda detectado: {session['tipo_demanda']}")
        
        # Actualizar datos del cliente
        datos_nuevos = respuesta_ia.get("datos_extraidos", {})
        if datos_nuevos and isinstance(datos_nuevos, dict):
            for campo, valor in datos_nuevos.items():
                if valor and isinstance(valor, str) and valor.lower() not in ["null", "n/a", "no especificado", ""]:
                    if 'datos_cliente' not in session:
                        session['datos_cliente'] = {}
                    session["datos_cliente"][campo] = valor
                    print(f"📋 {campo}: {valor}")
        
        # Actualizar hechos
        if respuesta_ia.get("hechos_extraidos"):
            hechos_nuevos = respuesta_ia["hechos_extraidos"]
            if hechos_nuevos and isinstance(hechos_nuevos, str) and hechos_nuevos.lower() not in ["null", "n/a", "no especificado", ""]:
                # Combinar con hechos existentes si los hay
                hechos_existentes = session.get("hechos_adicionales", "") or ""
                if hechos_existentes:
                    session["hechos_adicionales"] = f"{hechos_existentes}. {hechos_nuevos}"
                else:
                    session["hechos_adicionales"] = hechos_nuevos
                print(f"📝 Hechos actualizados: {session['hechos_adicionales'][:100]}...")
        
        # Actualizar notas
        if respuesta_ia.get("notas_extraidas"):
            notas_nuevas = respuesta_ia["notas_extraidas"]
            if notas_nuevas and isinstance(notas_nuevas, str) and notas_nuevas.lower() not in ["null", "n/a", "no especificado", ""]:
                session["notas_abogado"] = notas_nuevas
                print(f"📝 Notas del abogado: {notas_nuevas[:50]}...")
        
        # Determinar estado basado en la información disponible (lógica mejorada)
        datos_cliente = session.get("datos_cliente", {})
        tiene_nombre = bool(datos_cliente.get("nombre_completo"))
        tiene_dni = bool(datos_cliente.get("dni"))
        tiene_domicilio = bool(datos_cliente.get("domicilio"))
        tiene_tipo = bool(session.get("tipo_demanda"))
        hechos_temp = session.get("hechos_adicionales", "") or ""
        tiene_hechos = bool(hechos_temp and len(hechos_temp.strip()) > 10)
        
        print(f"🔍 Estado actual - Nombre: {tiene_nombre}, DNI: {tiene_dni}, Domicilio: {tiene_domicilio}, Tipo: {tiene_tipo}, Hechos: {tiene_hechos}")
        
        # Si estamos en estado "inicio", cambiar a "conversando" después del primer mensaje
        if session.get("estado") == "inicio":
            session["estado"] = "conversando"
            print("🔄 Cambiando de 'inicio' a 'conversando'")
        
        # Lógica de estado más inteligente
        if respuesta_ia.get("listo_para_generar"):
            session["estado"] = "listo_generar"
            print("✅ IA dice que está listo para generar")
        elif tiene_nombre and tiene_dni and tiene_tipo and tiene_hechos:
            # Relajamos el requisito de domicilio si tenemos nombre, DNI, tipo y hechos
            session["estado"] = "listo_generar"
            print("✅ Tenemos datos suficientes (nombre + DNI + tipo + hechos)")
        elif tiene_nombre and tiene_dni and tiene_domicilio and tiene_tipo:
            # Tenemos datos básicos pero tal vez necesitamos más hechos
            if tiene_hechos:
                session["estado"] = "listo_generar"
                print("✅ Datos completos - listo para generar")
            else:
                session["estado"] = "necesita_hechos"
                print("⚠️ Necesita más detalles de los hechos")
        elif tiene_tipo and (tiene_nombre or tiene_dni):
            session["estado"] = "necesita_datos_cliente"
            print("⚠️ Necesita completar datos del cliente")
        elif tiene_tipo:
            # Si solo tenemos el tipo de demanda, necesitamos datos del cliente
            session["estado"] = "necesita_datos_cliente"
            print("✅ Tipo de demanda seleccionado, necesitamos datos del cliente")
        else:
            session["estado"] = "seleccionando_tipo"
            print("⚠️ Necesita seleccionar tipo de demanda")
        
        print(f"🎛️ Estado final: {session['estado']}")
    
    def _evaluar_informacion_completa(self, session: Dict, session_id: str) -> Dict:
        """Evalúa toda la información disponible de forma integral."""
        
        # Obtener información de documentos procesados
        info_documentos = {}
        try:
            from rag.qa_agent import obtener_informacion_documentos_sincrona
            info_documentos = obtener_informacion_documentos_sincrona(session_id)
        except Exception as e:
            print(f"⚠️ Error obteniendo documentos: {e}")
        
        datos_cliente = session.get("datos_cliente", {})
        tipo_demanda = session.get("tipo_demanda", "")
        hechos = session.get("hechos_adicionales", "")
        
        # Información disponible de documentos
        tiene_documentos = bool(info_documentos.get("transcripcion_completa"))
        personas_docs = info_documentos.get("personas_identificadas", [])
        empresas_docs = info_documentos.get("empresas_identificadas", [])
        fechas_docs = info_documentos.get("fechas_importantes", [])
        montos_docs = info_documentos.get("montos_encontrados", [])
        
        # Evaluar completitud de forma inteligente
        información_critica = {
            "cliente_identificado": bool(datos_cliente.get("nombre_completo") or personas_docs),
            "dni_disponible": bool(datos_cliente.get("dni")),
            "tipo_demanda_definido": bool(tipo_demanda),
            "contexto_caso": bool(hechos or tiene_documentos),
            "documentos_procesados": tiene_documentos,
            "empresas_identificadas": bool(empresas_docs),
            "información_temporal": bool(fechas_docs),
            "información_económica": bool(montos_docs)
        }
        
        # Calcular completitud de forma más inteligente
        elementos_criticos = ["cliente_identificado", "tipo_demanda_definido", "contexto_caso"]
        elementos_opcionales = ["dni_disponible", "documentos_procesados", "empresas_identificadas", "información_temporal", "información_económica"]
        
        criticos_completos = sum(1 for elem in elementos_criticos if información_critica[elem])
        opcionales_completos = sum(1 for elem in elementos_opcionales if información_critica[elem])
        
        # Si tiene documentos procesados, es mucho más probable que esté completo
        if tiene_documentos and criticos_completos >= 2:
            porcentaje = min(95, 60 + (criticos_completos * 15) + (opcionales_completos * 5))
        else:
            porcentaje = (criticos_completos * 25) + (opcionales_completos * 8)
        
        # Determinar qué falta realmente
        faltantes_criticos = [elem for elem in elementos_criticos if not información_critica[elem]]
        
        return {
            "completo": len(faltantes_criticos) == 0 and porcentaje >= 70,
            "porcentaje_completo": min(100, porcentaje),
            "información_critica": información_critica,
            "faltantes_criticos": faltantes_criticos,
            "tiene_documentos": tiene_documentos,
            "resumen_disponible": {
                "personas": personas_docs,
                "empresas": empresas_docs,
                "fechas": fechas_docs,
                "montos": montos_docs
            }
        }

    def _generar_respuesta_inteligente(self, session: Dict, session_id: str, mensaje_usuario: str, respuesta_ia: Dict) -> str:
        """Genera respuestas más inteligentes basadas en toda la información disponible."""
        
        evaluacion = self._evaluar_informacion_completa(session, session_id)
        datos_cliente = session.get("datos_cliente", {})
        tipo_demanda = session.get("tipo_demanda", "")
        estado = session.get("estado", "inicio")
        
        # SIEMPRE mostrar mensaje inicial cuando el estado es "inicio"
        # Esto asegura que el primer mensaje del bot sea siempre el mensaje de bienvenida
        if estado == "inicio":
            return self._generar_mensaje_inicial()
        
        # Si acabamos de detectar un tipo de demanda pero no tenemos datos del cliente
        if tipo_demanda and not datos_cliente.get("nombre_completo") and len(mensaje_usuario.strip()) < 50:
            return f"Perfecto, {tipo_demanda}. ¿Cuál es el nombre completo de su cliente? También puede subir documentos con esta información."
        
        # Si la información está completa, sugerir generar demanda
        if evaluacion["completo"]:
            return "✅ **Información completa!** Tengo todos los datos necesarios para generar la demanda. ¿Confirma que proceda a generar el documento?"
        
        # Si hay documentos procesados, hacer una evaluación integral
        if evaluacion["tiene_documentos"]:
            return self._generar_respuesta_con_documentos(session, evaluacion, mensaje_usuario)
        
        # Si no hay documentos pero tiene información básica
        if evaluacion["porcentaje_completo"] >= 40:
            return self._generar_respuesta_consolidada(session, evaluacion)
        
        # Respuesta básica para casos simples
        return self._generar_respuesta_basica(session, mensaje_usuario)

    def _generar_respuesta_con_documentos(self, session: Dict, evaluacion: Dict, mensaje_usuario: str) -> str:
        """Genera respuesta cuando hay documentos procesados - más inteligente."""
        
        datos_cliente = session.get("datos_cliente", {})
        tipo_demanda = session.get("tipo_demanda", "")
        resumen = evaluacion["resumen_disponible"]
        
        # Si la evaluación indica que está completo o casi completo
        if evaluacion["completo"] or evaluacion["porcentaje_completo"] >= 80:
            mensaje = "✅ **Excelente! He procesado la información de los documentos.**\n\n"
            
            # Mostrar información consolidada
            if resumen["personas"]:
                mensaje += f"👤 **Cliente identificado:** {resumen['personas'][0]}\n"
            if tipo_demanda:
                mensaje += f"⚖️ **Tipo de demanda:** {tipo_demanda}\n"
            if resumen["empresas"]:
                mensaje += f"🏢 **Empresas involucradas:** {', '.join(resumen['empresas'][:2])}\n"
            if resumen["fechas"]:
                mensaje += f"📅 **Fechas relevantes:** {', '.join(resumen['fechas'][:3])}\n"
            if resumen["montos"]:
                mensaje += f"💰 **Montos encontrados:** {', '.join(resumen['montos'][:2])}\n"
            
            mensaje += f"\n**¿Esta información es correcta?**\n"
            mensaje += f"✅ **Generar demanda** con esta información\n"
            mensaje += f"✏️ **Agregar/modificar** algún detalle\n"
            mensaje += f"📤 **Subir más documentos** si faltan"
            
            return mensaje
        
        # Si falta información crítica
        faltantes = evaluacion["faltantes_criticos"]
        mensaje = "📄 **He procesado los documentos subidos.**\n\n"
        
        # Mostrar lo que se encontró
        if resumen["personas"]:
            mensaje += f"✅ Cliente identificado: {resumen['personas'][0]}\n"
        if resumen["empresas"]:
            mensaje += f"✅ Empresas: {', '.join(resumen['empresas'][:2])}\n"
        if tipo_demanda:
            mensaje += f"✅ Tipo de demanda: {tipo_demanda}\n"
        
        # Indicar qué falta específicamente
        if "cliente_identificado" in faltantes:
            mensaje += f"\n❓ **¿Cuál es el nombre completo del cliente?**"
        elif "tipo_demanda_definido" in faltantes:
            mensaje += f"\n❓ **¿Qué tipo de demanda necesitas?** (despido, licencia médica, solidaridad, etc.)"
        elif "contexto_caso" in faltantes:
            mensaje += f"\n❓ **¿Puedes contarme los detalles del caso?**"
        else:
            mensaje += f"\n✅ **¿Procedo a generar la demanda?**"
        
        return mensaje

    def _generar_respuesta_consolidada(self, session: Dict, evaluacion: Dict) -> str:
        """Genera respuesta consolidada cuando hay información parcial."""
        
        datos_cliente = session.get("datos_cliente", {})
        tipo_demanda = session.get("tipo_demanda", "")
        hechos = session.get("hechos_adicionales", "")
        
        mensaje = "📋 **Información recibida:**\n\n"
        
        # Mostrar lo que se tiene
        if datos_cliente.get("nombre_completo"):
            mensaje += f"✅ Cliente: {datos_cliente['nombre_completo']}\n"
        if datos_cliente.get("dni"):
            mensaje += f"✅ DNI: {datos_cliente['dni']}\n"
        if tipo_demanda:
            mensaje += f"✅ Tipo: {tipo_demanda}\n"
        if hechos:
            mensaje += f"✅ Contexto: {hechos[:100]}...\n"
        
        # Determinar qué falta
        faltantes = evaluacion["faltantes_criticos"]
        
        if len(faltantes) == 0:
            mensaje += f"\n🎯 **¿Procedo a generar la demanda?**"
        elif len(faltantes) == 1:
            if "cliente_identificado" in faltantes:
                mensaje += f"\n❓ Solo falta el **nombre del cliente**"
            elif "tipo_demanda_definido" in faltantes:
                mensaje += f"\n❓ Solo falta definir el **tipo de demanda**"
            else:
                mensaje += f"\n❓ Solo faltan los **detalles del caso**"
        else:
            mensaje += f"\n💡 **Puedes subir documentos o contarme más detalles del caso**"
        
        return mensaje

    def _generar_respuesta_basica(self, session: Dict, mensaje_usuario: str) -> str:
        """Genera respuesta básica para casos simples."""
        
        tipo_demanda = session.get("tipo_demanda", "")
        datos_cliente = session.get("datos_cliente", {})
        
        if not tipo_demanda:
            return "¿Qué tipo de demanda necesita para su cliente? Puedo ayudarle con despidos, licencias médicas, solidaridad laboral, etc. También puede subir documentos del caso."
        
        elif not datos_cliente.get("nombre_completo"):
            return f"Perfecto, {tipo_demanda}. ¿Cuál es el nombre completo de su cliente? También puede subir documentos con esta información."
        
        else:
            return "Excelente. ¿Puede contarme los detalles del caso de su cliente o subir documentos relacionados?"

    def _generar_mensaje_inicial(self) -> str:
        """Genera un mensaje inicial explicativo para el abogado."""
        # Obtener categorías disponibles del usuario
        categorias_disponibles = []
        if hasattr(self, 'tipos_disponibles') and self.tipos_disponibles:
            categorias_disponibles = self.tipos_disponibles
        
        mensaje = """¡Hola doctor! Soy su asistente legal inteligente. 🏛️

**Para generar una demanda, puede:**

📤 **Subir archivos:** telegramas, cartas documento, recibos, anotaciones, etc.
💬 **Escribir detalles:** datos del cliente, hechos del caso, tipo de demanda
🔄 **Combinar ambos:** La información se consolidará automáticamente

¿Con qué tipo de caso necesita ayuda? Puede contarme los detalles o subir documentos directamente."""
        
        return mensaje

    async def _preparar_para_qa_agent(self, session: Dict, session_id: str) -> Dict:
        """Prepara la información para QAAgent y genera la demanda."""
        
        # Obtener información consolidada de documentos (imágenes procesadas)
        info_documentos = {}
        try:
            from rag.qa_agent import obtener_informacion_documentos_sincrona
            info_documentos = obtener_informacion_documentos_sincrona(session_id)
            print(f"📄 Información de documentos obtenida: {len(info_documentos.get('transcripcion_completa', ''))} caracteres")
        except Exception as e:
            print(f"⚠️ Error obteniendo documentos: {e}")
        
        # Crear resumen para confirmación
        resumen = self._crear_resumen_para_abogado(session, info_documentos)
        
        return {
            "session_id": session_id,
            "mensaje": resumen["mensaje"],
            "tipo": "bot",
            "timestamp": datetime.now().isoformat(),
            "demanda_generada": False,
            "mostrar_confirmacion": True,
            "resumen_datos": resumen["datos"],
            "listo_para_qa_agent": True  # Nueva bandera
        }

    def _crear_resumen_para_abogado(self, session: Dict, info_documentos: Dict) -> Dict:
        """Crea un resumen más inteligente incluyendo documentos procesados."""
        
        datos_cliente = session.get("datos_cliente", {})
        tipo_demanda = session.get("tipo_demanda", "")
        hechos = session.get("hechos_adicionales", "")
        notas = session.get("notas_abogado", "")
        
        mensaje = f"## 📋 **RESUMEN PARA GENERAR DEMANDA**\\n\\n"
        
        # Información del cliente
        if datos_cliente.get("nombre_completo"):
            mensaje += f"**👤 CLIENTE:** {datos_cliente['nombre_completo']}\\n"
            if datos_cliente.get("dni"):
                mensaje += f"**🆔 DNI:** {datos_cliente['dni']}\\n"
            if datos_cliente.get("domicilio"):
                mensaje += f"**📍 DOMICILIO:** {datos_cliente['domicilio']}\\n"
            if datos_cliente.get("telefono"):
                mensaje += f"**📞 TELÉFONO:** {datos_cliente['telefono']}\\n"
            if datos_cliente.get("email"):
                mensaje += f"**📧 EMAIL:** {datos_cliente['email']}\\n"
            if datos_cliente.get("ocupacion"):
                mensaje += f"**💼 OCUPACIÓN:** {datos_cliente['ocupacion']}\\n"
        else:
            mensaje += f"**👤 CLIENTE:** No especificado\\n"
        
        # Tipo de demanda
        if tipo_demanda:
            mensaje += f"\\n**⚖️ TIPO DE DEMANDA:** {tipo_demanda}\\n"
        else:
            mensaje += f"\\n**⚖️ TIPO DE DEMANDA:** No especificado\\n"
        
        # Documentos procesados
        if info_documentos.get("transcripcion_completa"):
            num_docs = info_documentos.get("documentos_procesados", 0)
            mensaje += f"\\n**📄 DOCUMENTOS PROCESADOS:** {num_docs} archivo(s)\\n"
            mensaje += f"• Transcripción: {len(info_documentos['transcripcion_completa'])} caracteres\\n"
            
            # Información extraída de documentos
            if info_documentos.get("personas_identificadas"):
                personas = info_documentos['personas_identificadas'][:5]  # Máximo 5
                mensaje += f"• Personas identificadas: {', '.join(personas)}{'...' if len(info_documentos['personas_identificadas']) > 5 else ''}\\n"
            
            if info_documentos.get("empresas_identificadas"):
                empresas = info_documentos['empresas_identificadas'][:3]  # Máximo 3
                mensaje += f"• Empresas identificadas: {', '.join(empresas)}{'...' if len(info_documentos['empresas_identificadas']) > 3 else ''}\\n"
            
            if info_documentos.get("fechas_importantes"):
                fechas = info_documentos['fechas_importantes'][:5]  # Máximo 5
                mensaje += f"• Fechas importantes: {', '.join(fechas)}{'...' if len(info_documentos['fechas_importantes']) > 5 else ''}\\n"
            
            if info_documentos.get("montos_encontrados"):
                montos = info_documentos['montos_encontrados'][:3]  # Máximo 3
                mensaje += f"• Montos encontrados: {', '.join(montos)}{'...' if len(info_documentos['montos_encontrados']) > 3 else ''}\\n"
        else:
            mensaje += f"\\n**📄 DOCUMENTOS PROCESADOS:** Ninguno\\n"
        
        # Hechos adicionales
        if hechos:
            mensaje += f"\\n**📝 HECHOS ADICIONALES:**\\n{hechos[:300]}{'...' if len(hechos) > 300 else ''}\\n"
        else:
            mensaje += f"\\n**📝 HECHOS ADICIONALES:** No especificados\\n"
        
        # Notas del abogado
        if notas:
            mensaje += f"\\n**📋 NOTAS DEL ABOGADO:**\\n{notas[:200]}{'...' if len(notas) > 200 else ''}\\n"
        
        mensaje += "\\n**✅ ¿CONFIRMA QUE ESTA INFORMACIÓN ES CORRECTA?**\\n\\n"
        mensaje += "**Opciones:**\\n"
        mensaje += "✅ **GENERAR DEMANDA** - Crear documento con esta información\\n"
        mensaje += "✏️ **MODIFICAR DATOS** - Agregar o cambiar información\\n"
        mensaje += "📁 **AGREGAR DOCUMENTOS** - Subir más imágenes o archivos\\n"
        mensaje += "❌ **CANCELAR** - No generar en este momento"
        
        return {
            "mensaje": mensaje,
            "datos": {
                "cliente": datos_cliente,
                "tipo_demanda": tipo_demanda,
                "hechos": hechos,
                "notas": notas,
                "documentos": info_documentos,
                "resumen_completo": {
                    "personas": info_documentos.get("personas_identificadas", []),
                    "empresas": info_documentos.get("empresas_identificadas", []),
                    "fechas": info_documentos.get("fechas_importantes", []),
                    "montos": info_documentos.get("montos_encontrados", [])
                }
            }
        }

    def _detectar_informacion_automatica(self, session: Dict, session_id: str) -> Dict:
        """Detecta automáticamente información de documentos procesados y la usa sin confirmación."""
        try:
            from rag.qa_agent import obtener_informacion_documentos_sincrona
            info_documentos = obtener_informacion_documentos_sincrona(session_id)
            
            if not info_documentos.get("transcripcion_completa"):
                return {}
            
            datos_cliente = session.get("datos_cliente", {})
            cambios_realizados = {}
            
            # Detectar nombre automáticamente si no existe
            if not datos_cliente.get("nombre_completo") and info_documentos.get("personas_identificadas"):
                personas = info_documentos["personas_identificadas"]
                if personas:
                    # Usar el primer nombre como cliente principal
                    nombre_detectado = personas[0]
                    if 'datos_cliente' not in session:
                        session['datos_cliente'] = {}
                    session['datos_cliente']['nombre_completo'] = nombre_detectado
                    cambios_realizados['nombre_completo'] = nombre_detectado
                    print(f"🤖 Nombre detectado automáticamente: {nombre_detectado}")
            
            # Detectar tipo de demanda automáticamente si no existe
            if not session.get("tipo_demanda"):
                transcripcion = info_documentos["transcripcion_completa"].lower()
                tipo_detectado = None
                
                if "negro" in transcripcion and "blanco" in transcripcion:
                    tipo_detectado = "Empleados Blanco Negro"
                elif "negro" in transcripcion:
                    tipo_detectado = "Empleados En Negro"
                elif "blanco" in transcripcion:
                    tipo_detectado = "Empleados En Blanco"
                elif "licencia" in transcripcion and ("medica" in transcripcion or "médica" in transcripcion):
                    tipo_detectado = "Demanda Licencia Medica"
                elif "solidaridad" in transcripcion:
                    tipo_detectado = "Demanda Solidaridad Laboral"
                
                if tipo_detectado:
                    session['tipo_demanda'] = tipo_detectado
                    cambios_realizados['tipo_demanda'] = tipo_detectado
                    print(f"🤖 Tipo de demanda detectado automáticamente: {tipo_detectado}")
            
            # Detectar hechos automáticamente si no existen
            if not session.get("hechos_adicionales"):
                transcripcion = info_documentos["transcripcion_completa"]
                # Extraer información relevante del documento
                hechos_detectados = self._extraer_hechos_del_documento(transcripcion)
                if hechos_detectados:
                    session['hechos_adicionales'] = hechos_detectados
                    cambios_realizados['hechos_adicionales'] = hechos_detectados
                    print(f"🤖 Hechos detectados automáticamente: {hechos_detectados[:100]}...")
            
            return cambios_realizados
            
        except Exception as e:
            print(f"⚠️ Error detectando información automática: {e}")
            return {}
    
    def _extraer_hechos_del_documento(self, transcripcion: str) -> str:
        """Extrae hechos relevantes del documento procesado."""
        hechos = []
        
        # Detectar patrones comunes en documentos legales
        if "despid" in transcripcion.lower():
            hechos.append("Despido laboral")
        
        if "sin causa" in transcripcion.lower():
            hechos.append("Despido sin causa aparente")
        
        if "negro" in transcripcion.lower():
            hechos.append("Trabajo en negro")
        
        if "blanco" in transcripcion.lower():
            hechos.append("Trabajo en blanco")
        
        if "solidaridad" in transcripcion.lower():
            hechos.append("Solidaridad laboral")
        
        if "licencia" in transcripcion.lower():
            hechos.append("Licencia médica")
        
        if "salario" in transcripcion.lower() or "sueldo" in transcripcion.lower():
            hechos.append("Problemas con salarios")
        
        if "horas extras" in transcripcion.lower() or "horas extra" in transcripcion.lower():
            hechos.append("Horas extras no pagadas")
        
        # Extraer información de empresas mencionadas
        empresas = []
        if "empresa" in transcripcion.lower():
            # Buscar nombres de empresas después de "empresa"
            import re
            matches = re.findall(r'empresa\s+([A-Z][A-Z0-9\s]+)', transcripcion, re.IGNORECASE)
            empresas.extend(matches)
        
        if empresas:
            hechos.append(f"Empresa(s) involucrada(s): {', '.join(empresas[:2])}")
        
        if hechos:
            return f"Documento indica: {', '.join(hechos)}. Contexto: {transcripcion[:200]}..."
        
        return ""

    def _generar_mensaje_informacion_extraida(self, cambios_automaticos: Dict, session: Dict, session_id: str) -> str:
        """Genera un mensaje mostrando la información extraída automáticamente de documentos."""
        
        if not cambios_automaticos:
            return ""
        
        try:
            from rag.qa_agent import obtener_informacion_documentos_sincrona
            info_documentos = obtener_informacion_documentos_sincrona(session_id)
        except:
            info_documentos = {}
        
        mensaje = "🤖 **INFORMACIÓN DETECTADA AUTOMÁTICAMENTE**\n\n"
        
        # Mostrar información del cliente detectada
        if cambios_automaticos.get('nombre_completo'):
            mensaje += f"👤 **Cliente identificado:** {cambios_automaticos['nombre_completo']}\n"
        
        # Mostrar tipo de demanda detectado
        if cambios_automaticos.get('tipo_demanda'):
            mensaje += f"⚖️ **Tipo de demanda:** {cambios_automaticos['tipo_demanda']}\n"
        
        # Mostrar hechos detectados
        if cambios_automaticos.get('hechos_adicionales'):
            hechos = cambios_automaticos['hechos_adicionales'][:200]
            mensaje += f"📝 **Hechos detectados:** {hechos}...\n"
        
        # Mostrar información adicional de documentos
        if info_documentos.get("empresas_identificadas"):
            empresas = info_documentos["empresas_identificadas"][:2]
            mensaje += f"🏢 **Empresas:** {', '.join(empresas)}\n"
        
        if info_documentos.get("fechas_importantes"):
            fechas = info_documentos["fechas_importantes"][:3]
            mensaje += f"📅 **Fechas relevantes:** {', '.join(fechas)}\n"
        
        if info_documentos.get("montos_encontrados"):
            montos = info_documentos["montos_encontrados"][:2]
            mensaje += f"💰 **Montos:** {', '.join(montos)}\n"
        
        mensaje += "\n**¿Esta información es correcta?**\n"
        mensaje += "✅ **Sí, proceder** - Generar demanda con esta información\n"
        mensaje += "✏️ **Modificar** - Agregar o cambiar datos\n"
        mensaje += "📤 **Subir más documentos** - Si falta información"
        
        return mensaje

# Instancia global del agente - se inicializa bajo demanda
chat_agent = None

def get_chat_agent(user_id: str = None):
    """Obtiene o crea la instancia del agente de chat."""
    global chat_agent
    
    # Si se proporciona user_id, crear nueva instancia específica
    if user_id:
        try:
            print(f"🔧 Creando nueva instancia de ChatAgentInteligente para user_id: {user_id}")
            chat_agent = ChatAgentInteligente(user_id=user_id)
            print(f"✅ ChatAgentInteligente creado exitosamente con tipos dinámicos")
        except Exception as e:
            print(f"⚠️ Error inicializando ChatAgentInteligente: {e}")
            import traceback
            traceback.print_exc()
            chat_agent = None
        return chat_agent
    
    # Si no hay user_id, usar lógica existente
    if chat_agent is None:
        try:
            print(f"🔧 Creando nueva instancia de ChatAgentInteligente...")
            chat_agent = ChatAgentInteligente()
            print(f"✅ ChatAgentInteligente creado exitosamente")
        except Exception as e:
            print(f"⚠️ Error inicializando ChatAgentInteligente: {e}")
            import traceback
            traceback.print_exc()
            chat_agent = None
    else:
        print(f"🔄 Reutilizando instancia existente de ChatAgentInteligente")
    return chat_agent

def reset_chat_agent():
    """Resetea la instancia global del ChatAgent."""
    global chat_agent
    print(f"🔄 Reseteando ChatAgent...")
    chat_agent = None 