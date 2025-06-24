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
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno")
        
        self.client = OpenAI(
            api_key=api_key,
            timeout=60.0  # Timeout de 60 segundos para OpenAI
        )
        
        # Inicializar tipos con fallback
        try:
            self.tipos_disponibles = obtener_tipos_demanda_disponibles()
            if not self.tipos_disponibles:
                raise ValueError("obtener_tipos_demanda_disponibles devolvió lista vacía")
            print(f"✅ ChatAgentInteligente inicializado con {len(self.tipos_disponibles)} tipos de demanda")
        except Exception as e:
            print(f"⚠️ Error obteniendo tipos de demanda: {e}")
            # Fallback con tipos básicos
            self.tipos_disponibles = [
                "Empleados En Blanco", 
                "Empleados En Negro", 
                "Demanda Licencia Medica", 
                "Demanda Solidaridad Laboral",
                "Empleados Blanco Negro"
            ]
            print(f"✅ ChatAgentInteligente inicializado con {len(self.tipos_disponibles)} tipos de demanda (fallback)")
        
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
        
    def procesar_mensaje(self, session: Dict, mensaje_usuario: str, session_id: str) -> Dict:
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
            
            # Obtener contexto de la conversación
            print(f"🔍 Obteniendo contexto de conversación...")
            contexto = self._obtener_contexto_conversacion(session)
            print(f"✅ Contexto obtenido: {len(contexto)} chars")
            
            # Usar OpenAI para procesar el mensaje
            print(f"🔍 Llamando _procesar_con_openai...")
            print(f"   tipos_disponibles: {self.tipos_disponibles}")
            print(f"   tipos_disponibles tipo: {type(self.tipos_disponibles)}")
            respuesta_ia = self._procesar_con_openai(
                mensaje_usuario=mensaje_usuario,
                contexto=contexto,
                tipos_disponibles=self.tipos_disponibles,
                session=session
            )
            
            print(f"🔍 _procesar_con_openai devolvió: {type(respuesta_ia)}")
            if respuesta_ia:
                print(f"   Keys: {list(respuesta_ia.keys())}")
            else:
                print(f"   Valor: {respuesta_ia}")
            
            # Validar respuesta de IA
            if not respuesta_ia:
                raise ValueError("La IA no devolvió una respuesta válida")
            
            # Actualizar la sesión con la información extraída
            print(f"🔍 Llamando _actualizar_sesion...")
            self._actualizar_sesion(session, respuesta_ia)
            print(f"✅ _actualizar_sesion completado")
            
            # Generar respuesta apropiada
            print(f"🔍 Llamando _generar_respuesta...")
            resultado_final = self._generar_respuesta(session, respuesta_ia, session_id)
            print(f"🔍 _generar_respuesta devolvió: {type(resultado_final)}")
            if resultado_final:
                print(f"   Keys: {list(resultado_final.keys())}")
            return resultado_final
            
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
        """Usa OpenAI para procesar el mensaje y determinar la acción apropiada."""
        
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
Eres un asistente legal AI experto que DEBE extraer TODA la información disponible del mensaje del usuario.

CONTEXTO ACTUAL: {contexto}
MENSAJE DEL USUARIO: "{mensaje_usuario}"

TIPOS DISPONIBLES: {tipos_disponibles}

MAPEO DE TIPOS (EXACTO):
- "empleados en blanco", "blanco", "trabajo en blanco" → "Empleados En Blanco"
- "empleados en negro", "negro", "trabajo en negro" → "Empleados En Negro"  
- "licencia médica", "licencia medica", "licencia" → "Demanda Licencia Medica"
- "solidaridad" → "Demanda Solidaridad Laboral"
- "blanco negro", "blanco y negro" → "Empleados Blanco Negro"

INSTRUCCIONES CRÍTICAS:
1. EXTRAE TODOS los datos personales que encuentres (nombres, direcciones, DNI, etc.)
2. Si detectas formato "Nombre + Dirección + DNI", sepáralos correctamente
3. Cualquier mención de despido, problema laboral = agregar a hechos
4. Si hay tipo + datos básicos + hechos → GENERAR INMEDIATAMENTE
5. Mapea tipos al nombre EXACTO de la lista disponible

REGLAS DE IDENTIFICACIÓN DE DATOS:
- NOMBRES: 2-3 palabras que empiecen con mayúscula (ej: "Gino Gentile")
- DNI: números de 7-8 dígitos sin prefijos internacionales (ej: "35703591" = DNI, NO teléfono)
- DIRECCIONES: nombres de calles + números (ej: "Paraguay 2536")
- TELÉFONOS: números con códigos de área o más de 8 dígitos (ej: "011-1234-5678")

EJEMPLOS DE EXTRACCIÓN CORRECTA:
- "Juan Pérez, Rivadavia 123, 12345678" → nombre_completo: "Juan Pérez", domicilio: "Rivadavia 123", dni: "12345678"
- "Gino Gentile, Paraguay 2536, 35703591" → nombre_completo: "Gino Gentile", domicilio: "Paraguay 2536", dni: "35703591"
- "me despidieron" → hechos: descripción del despido
- "empresa XYZ" → agregar a hechos con contexto

RESPONDE EN JSON:
{{
    "accion": "seleccionar_tipo|generar_demanda|solicitar_info_critica|continuar_conversacion",
    "tipo_demanda_detectado": "EXACTO_DE_LISTA_O_NULL",
    "datos_extraidos": {{
        "nombre_completo": "NOMBRE_COMPLETO_O_NULL",
        "dni": "SOLO_NUMEROS_7_8_DIGITOS_O_NULL", 
        "domicilio": "DIRECCION_COMPLETA_O_NULL",
        "telefono": "TELEFONO_CON_CODIGO_AREA_O_NULL",
        "email": "EMAIL_O_NULL",
        "ocupacion": "TRABAJO_O_NULL"
    }},
    "hechos_extraidos": "TODOS_LOS_HECHOS_LABORALES_DETECTADOS",
    "notas_extraidas": "NOTAS_ADICIONALES_O_NULL",
    "mensaje_respuesta": "RESPUESTA_PROFESIONAL",
    "listo_para_generar": true_si_tienes_nombre_dni_tipo_hechos
}}

REGLA ESPECIAL: Si encuentras nombre + DNI + dirección + tipo + situación laboral → listo_para_generar: true
IMPORTANTE: Números de 7-8 dígitos SON DNI, no teléfonos.
"""

        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un experto en extracción de datos legales. SIEMPRE responde en formato JSON válido, siendo MUY inteligente extrayendo información."},
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
        else:
            session["estado"] = "seleccionando_tipo"
            print("⚠️ Necesita seleccionar tipo de demanda")
        
        print(f"🎛️ Estado final: {session['estado']}")
    
    def _generar_respuesta(self, session: Dict, respuesta_ia: Dict, session_id: str) -> Dict:
        """Genera la respuesta final para el abogado."""
        
        # Verificar si debe generar la demanda automáticamente
        estado = session.get("estado", "")
        debe_generar = (
            respuesta_ia.get("listo_para_generar") or 
            respuesta_ia.get("accion") == "generar_demanda" or
            estado == "listo_generar"
        )
        
        if debe_generar:
            try:
                # Verificar que tenemos la información mínima
                datos_cliente = session.get("datos_cliente", {})
                if not (datos_cliente.get("nombre_completo") and datos_cliente.get("dni")):
                    raise ValueError("Faltan datos básicos del cliente (nombre y DNI)")
                
                # Mostrar progreso al usuario
                print(f"🔄 Iniciando generación de demanda para {datos_cliente.get('nombre_completo')}")
                
                # Generar la demanda con timeout mejorado y contexto enriquecido
                start_time = time.time()
                
                # NUEVO: Obtener user_id del contexto de sesión si está disponible
                user_id = session.get("user_id")  # El user_id debe pasarse desde el endpoint
                
                resultado = generar_demanda(
                    tipo_demanda=session["tipo_demanda"],
                    datos_cliente=datos_cliente,
                    hechos_adicionales=session.get("hechos_adicionales", "") or "",
                    notas_abogado=session.get("notas_abogado", "") or "",
                    user_id=user_id  # NUEVO: Pasar user_id para contexto enriquecido
                )
                elapsed_time = time.time() - start_time
                
                # NUEVO: Guardar la demanda en la base de datos
                try:
                    from supabase_integration import supabase_admin
                    
                    # Obtener abogado_id desde user_id
                    abogado_id = None
                    if user_id:
                        try:
                            abogado_response = supabase_admin.table('abogados')\
                                .select('id')\
                                .eq('user_id', user_id)\
                                .single()\
                                .execute()
                            
                            if abogado_response.data:
                                abogado_id = abogado_response.data['id']
                                print(f"✅ abogado_id obtenido: {abogado_id}")
                            else:
                                print(f"⚠️ No se encontró abogado para user_id: {user_id}")
                        except Exception as e:
                            print(f"⚠️ Error obteniendo abogado_id: {e}")
                    
                    # NUEVO: Subir archivo al bucket de Supabase Storage
                    archivo_url = None
                    if resultado.get("archivo_docx"):
                        try:
                            archivo_path = resultado["archivo_docx"]
                            if os.path.exists(archivo_path):
                                # Crear nombre único para el archivo
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                cliente_nombre = datos_cliente.get("nombre_completo", "Cliente").replace(" ", "_")
                                nombre_archivo = f"{user_id}/demanda_{cliente_nombre}_{timestamp}.docx"
                                
                                # Leer archivo y verificar que sea válido
                                with open(archivo_path, 'rb') as file:
                                    archivo_bytes = file.read()
                                
                                # Verificar que el archivo no esté vacío
                                if len(archivo_bytes) == 0:
                                    raise Exception("El archivo generado está vacío")
                                
                                print(f"📄 Archivo a subir: {len(archivo_bytes)} bytes")
                                
                                # Intentar subida con diferentes métodos
                                storage_response = None
                                
                                # Método 1: Con content-type específico
                                try:
                                    storage_response = supabase_admin.storage.from_('demandas-generadas').upload(
                                        nombre_archivo, 
                                        archivo_bytes,
                                        file_options={
                                            "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                            "upsert": "true"
                                        }
                                    )
                                    print(f"✅ Subida exitosa con content-type específico")
                                except Exception as e1:
                                    print(f"⚠️ Método 1 falló: {e1}")
                                    
                                    # Método 2: Sin content-type explícito
                                    try:
                                        storage_response = supabase_admin.storage.from_('demandas-generadas').upload(
                                            nombre_archivo, 
                                            archivo_bytes,
                                            file_options={"upsert": "true"}
                                        )
                                        print(f"✅ Subida exitosa sin content-type")
                                    except Exception as e2:
                                        print(f"⚠️ Método 2 falló: {e2}")
                                        
                                        # Método 3: Solo el archivo, sin opciones
                                        try:
                                            storage_response = supabase_admin.storage.from_('demandas-generadas').upload(
                                                nombre_archivo, 
                                                archivo_bytes
                                            )
                                            print(f"✅ Subida exitosa sin opciones")
                                        except Exception as e3:
                                            print(f"⚠️ Método 3 falló: {e3}")
                                            raise Exception(f"Todos los métodos de subida fallaron: {e1}, {e2}, {e3}")
                                
                                if storage_response:
                                    # Generar URL pública
                                    archivo_url = supabase_admin.storage.from_('demandas-generadas').get_public_url(nombre_archivo)
                                    print(f"✅ Archivo subido a Storage: {nombre_archivo}")
                                    print(f"🔗 URL pública: {archivo_url}")
                                else:
                                    print(f"⚠️ Error: storage_response es None")
                            else:
                                print(f"⚠️ Archivo no encontrado: {archivo_path}")
                        except Exception as storage_error:
                            print(f"⚠️ Error subiendo a Storage: {storage_error}")
                            # Continuar sin archivo en Storage
                    
                    # Preparar datos para guardar
                    demanda_data = {
                        "session_id": session_id,  # Nueva columna
                        "sesion_id": None,  # Mantener NULL por ahora
                        "abogado_id": abogado_id,
                        "user_id": user_id,
                        "tipo_demanda": session["tipo_demanda"],
                        "datos_cliente": datos_cliente,
                        "hechos_adicionales": session.get("hechos_adicionales", ""),
                        "notas_abogado": session.get("notas_abogado", ""),
                        "texto_demanda": resultado.get("texto_demanda", ""),
                        "metadatos": resultado.get("metadatos", {}),
                        "archivo_docx": resultado.get("archivo_docx", ""),
                        "archivo_docx_url": archivo_url,  # URL de Supabase Storage
                        "estado": "completado",
                        "fecha_generacion": datetime.now().isoformat()
                    }
                    
                    print(f"💾 Guardando demanda en base de datos")
                    print(f"   session_id: {session_id}")
                    print(f"   user_id: {user_id}")
                    print(f"   abogado_id: {abogado_id}")
                    print(f"   archivo_url: {archivo_url}")
                    
                    # Buscar si ya existe una demanda para esta sesión
                    existing_response = supabase_admin.table('demandas_generadas')\
                        .select('id')\
                        .eq('session_id', session_id)\
                        .execute()
                    
                    if existing_response.data:
                        # Actualizar demanda existente
                        update_response = supabase_admin.table('demandas_generadas')\
                            .update(demanda_data)\
                            .eq('session_id', session_id)\
                            .execute()
                        print(f"✅ Demanda actualizada en base de datos")
                    else:
                        # Crear nueva demanda
                        insert_response = supabase_admin.table('demandas_generadas')\
                            .insert(demanda_data)\
                            .execute()
                        print(f"✅ Nueva demanda guardada en base de datos")
                        
                except Exception as db_error:
                    print(f"⚠️ Error guardando en base de datos: {db_error}")
                    # Continuar aunque falle el guardado en DB
                
                session["estado"] = "completado"
                session["resultado"] = resultado
                
                print(f"✅ Demanda generada en {elapsed_time:.1f} segundos")
                
                return {
                    "session_id": session_id,
                    "mensaje": "✅ **Demanda generada exitosamente**\\n\\nHe creado la demanda profesional basándome en los casos similares de la base de datos. El documento incluye:\\n\\n• Hechos estructurados según jurisprudencia\\n• Base legal con artículos específicos de la LCT\\n• Petitorio adaptado al tipo de caso\\n• Ofrecimiento de prueba detallado\\n\\n**Opciones disponibles:**\\n🔍 **Previsualizar** - Ver la demanda antes de descargar\\n📄 **Descargar** - Obtener el archivo Word\\n🔄 **Regenerar** - Crear una nueva versión",
                    "tipo": "bot",
                    "timestamp": datetime.now().isoformat(),
                    "demanda_generada": True,
                    "mostrar_preview": True
                }
                
            except Exception as e:
                print(f"❌ Error generando demanda: {e}")
                return {
                    "session_id": session_id,
                    "mensaje": f"❌ Error al generar la demanda: {str(e)}\\n\\nPor favor, verifica que hayas proporcionado:\\n• Tipo de demanda\\n• Nombre completo del cliente\\n• DNI del cliente\\n• Hechos básicos del caso",
                    "tipo": "bot",
                    "timestamp": datetime.now().isoformat(),
                    "demanda_generada": False
                }
        
        # Respuesta normal de conversación
        mensaje = respuesta_ia.get("mensaje_respuesta", "¿En qué puedo ayudarte con la demanda?")
        
        # Agregar opciones si hay tipos disponibles y no se ha seleccionado
        opciones = None
        if not session.get("tipo_demanda") and respuesta_ia.get("accion") == "seleccionar_tipo":
            opciones = self.tipos_disponibles
        
        return {
            "session_id": session_id,
            "mensaje": mensaje,
            "tipo": "bot", 
            "timestamp": datetime.now().isoformat(),
            "opciones": opciones,
            "requiere_datos": respuesta_ia.get("accion") == "solicitar_info_critica",
            "demanda_generada": False
        }

# Instancia global del agente - se inicializa bajo demanda
chat_agent = None

def get_chat_agent():
    """Obtiene o crea la instancia del agente de chat."""
    global chat_agent
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