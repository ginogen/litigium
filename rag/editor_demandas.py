from typing import Dict, List, Optional, Tuple, Any
import re
import json
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

class TipoComando(Enum):
    AGREGAR_DESPUES = "agregar_despues"
    AGREGAR_ANTES = "agregar_antes"
    MODIFICAR = "modificar"
    ELIMINAR = "eliminar"
    REEMPLAZAR = "reemplazar"
    INSERTAR_EN = "insertar_en"
    CAMBIAR_PALABRAS = "cambiar_palabras"

@dataclass
class ComandoEdicion:
    tipo: TipoComando
    referencia: str  # párrafo X, línea Y, palabra Z
    contenido: str   # texto a agregar/modificar
    posicion: Optional[int] = None
    sesion_id: str = ""
    timestamp: str = ""
    texto_original: str = ""  # Para revertir cambios

class DemandaEstructurada:
    """Representa una demanda estructurada para edición granular."""
    
    def __init__(self, texto_completo: str, sesion_id: str):
        self.sesion_id = sesion_id
        self.texto_original = texto_completo
        self.parrafos = self._estructurar_parrafos(texto_completo)
        self.historial_ediciones = []
        self.timestamp_creacion = datetime.now().isoformat()
        
    def _estructurar_parrafos(self, texto: str) -> List[Dict]:
        """Estructura el texto en párrafos numerados para edición."""
        # Separar por párrafos (doble salto de línea o líneas vacías)
        parrafos_raw = re.split(r'\n\s*\n', texto.strip())
        
        parrafos = []
        for i, parrafo in enumerate(parrafos_raw, 1):
            if parrafo.strip():
                parrafos.append({
                    'numero': i,
                    'id': f'p_{i}',
                    'contenido': parrafo.strip(),
                    'tipo': self._detectar_tipo_parrafo(parrafo),
                    'modificado': False,
                    'timestamp_modificacion': None
                })
        
        return parrafos
    
    def _detectar_tipo_parrafo(self, parrafo: str) -> str:
        """Detecta el tipo de párrafo para mejor edición."""
        texto_lower = parrafo.lower().strip()
        
        if 'sr. juez' in texto_lower or 'señor juez' in texto_lower:
            return 'encabezado'
        elif 'hechos:' in texto_lower or 'i.- hechos' in texto_lower:
            return 'hechos'
        elif 'derecho:' in texto_lower or 'ii.- derecho' in texto_lower:
            return 'derecho'
        elif 'petitorio:' in texto_lower or 'iii.- petitorio' in texto_lower:
            return 'petitorio'
        elif 'prueba:' in texto_lower or 'iv.- prueba' in texto_lower:
            return 'prueba'
        elif re.match(r'^\d+[\.\-)]', texto_lower):
            return 'numerado'
        elif len(parrafo.split()) < 10:
            return 'titulo'
        else:
            return 'normal'
    
    def obtener_parrafo_por_numero(self, numero: int) -> Optional[Dict]:
        """Obtiene un párrafo por su número."""
        for parrafo in self.parrafos:
            if parrafo['numero'] == numero:
                return parrafo
        return None
    
    def obtener_parrafo_por_contenido(self, texto_referencia: str) -> Optional[Dict]:
        """Encuentra un párrafo por contenido parcial."""
        texto_ref = texto_referencia.lower().strip()
        
        for parrafo in self.parrafos:
            if texto_ref in parrafo['contenido'].lower():
                return parrafo
        return None

class EditorDemandas:
    """Manejador principal de ediciones granulares."""
    
    def __init__(self):
        self.demandas_activas = {}  # sesion_id -> DemandaEstructurada
        
    def inicializar_demanda(self, texto_completo: str, sesion_id: str) -> DemandaEstructurada:
        """Inicializa una nueva demanda para edición."""
        demanda = DemandaEstructurada(texto_completo, sesion_id)
        self.demandas_activas[sesion_id] = demanda
        return demanda
    
    def obtener_demanda(self, sesion_id: str) -> Optional[DemandaEstructurada]:
        """Obtiene una demanda activa por sesión, cargándola desde DB si es necesario."""
        demanda = self.demandas_activas.get(sesion_id)
        
        if not demanda:
            # Intentar cargar desde base de datos
            demanda = self._cargar_demanda_desde_db(sesion_id)
            if demanda:
                self.demandas_activas[sesion_id] = demanda
        
        return demanda
    
    def _cargar_demanda_desde_db(self, sesion_id: str) -> Optional[DemandaEstructurada]:
        """Carga una demanda desde la base de datos si existe."""
        try:
            from supabase_integration import supabase_admin
            
            print(f"🔍 [EDITOR] Intentando cargar demanda desde DB para sesión: {sesion_id}")
            
            # Buscar demanda en la base de datos
            response = supabase_admin.table('demandas_generadas')\
                .select('*')\
                .eq('session_id', sesion_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                demanda_data = response.data[0]  # Tomar la primera
                texto_demanda = demanda_data.get('texto_demanda')
                
                if texto_demanda:
                    print(f"✅ [EDITOR] Demanda encontrada en DB, inicializando estructura")
                    demanda = DemandaEstructurada(texto_demanda, sesion_id)
                    return demanda
            
            print(f"⚠️ [EDITOR] No se encontró demanda en DB para sesión: {sesion_id}")
            return None
            
        except Exception as e:
            print(f"❌ [EDITOR] Error cargando desde DB: {str(e)}")
            return None
    
    def procesar_comando_natural(self, comando: str, sesion_id: str) -> Dict[str, Any]:
        """Procesa comandos en lenguaje natural para editar la demanda."""
        comando_lower = comando.lower().strip()
        demanda = self.obtener_demanda(sesion_id)
        
        if not demanda:
            return {
                'exito': False,
                'error': 'No hay demanda activa para esta sesión'
            }
        
        try:
            # Detectar tipo de comando
            if 'agregar' in comando_lower and ('después' in comando_lower or 'luego' in comando_lower):
                return self._procesar_agregar_despues(comando, demanda)
            elif 'agregar' in comando_lower and ('antes' in comando_lower or 'previo' in comando_lower):
                return self._procesar_agregar_antes(comando, demanda)
            elif 'modificar' in comando_lower or 'cambiar' in comando_lower:
                return self._procesar_modificar(comando, demanda)
            elif 'eliminar' in comando_lower or 'borrar' in comando_lower:
                return self._procesar_eliminar(comando, demanda)
            elif 'reemplazar' in comando_lower:
                return self._procesar_reemplazar(comando, demanda)
            else:
                return {
                    'exito': False,
                    'error': 'Comando no reconocido. Usa: agregar, modificar, eliminar, reemplazar'
                }
                
        except Exception as e:
            return {
                'exito': False,
                'error': f'Error procesando comando: {str(e)}'
            }
    
    def _procesar_agregar_despues(self, comando: str, demanda: DemandaEstructurada) -> Dict[str, Any]:
        """Procesa comando: 'A continuación del párrafo X, agregar...'"""
        # Extraer número de párrafo
        match_numero = re.search(r'párrafo\s+(\d+)', comando)
        match_contenido = re.search(r'agregar[:\s]+(.*)', comando, re.IGNORECASE | re.DOTALL)
        
        if match_numero and match_contenido:
            numero_parrafo = int(match_numero.group(1))
            contenido_nuevo = match_contenido.group(1).strip()
            
            # Crear nuevo párrafo
            nuevo_parrafo = {
                'numero': numero_parrafo + 0.5,  # Número intermedio
                'id': f'p_{numero_parrafo}_new',
                'contenido': contenido_nuevo,
                'tipo': 'nuevo',
                'modificado': True,
                'timestamp_modificacion': datetime.now().isoformat()
            }
            
            # Insertar en la posición correcta
            for i, parrafo in enumerate(demanda.parrafos):
                if parrafo['numero'] > numero_parrafo:
                    demanda.parrafos.insert(i, nuevo_parrafo)
                    break
            else:
                demanda.parrafos.append(nuevo_parrafo)
            
            # Renumerar párrafos siguientes
            self._renumerar_parrafos(demanda, numero_parrafo + 1)
            
            # Registrar en historial
            comando_edicion = ComandoEdicion(
                tipo=TipoComando.AGREGAR_DESPUES,
                referencia=f"párrafo {numero_parrafo}",
                contenido=contenido_nuevo,
                sesion_id=demanda.sesion_id,
                timestamp=datetime.now().isoformat()
            )
            demanda.historial_ediciones.append(comando_edicion)
            
            return {
                'exito': True,
                'mensaje': f'Párrafo agregado después del párrafo {numero_parrafo}',
                'parrafos_actualizados': self._obtener_parrafos_para_vista(demanda)
            }
        
        return {
            'exito': False,
            'error': 'No se pudo extraer el número de párrafo o el contenido a agregar'
        }
    
    def _procesar_modificar(self, comando: str, demanda: DemandaEstructurada) -> Dict[str, Any]:
        """Procesa comando: 'Modificar el párrafo X con...'"""
        # Extraer número de párrafo y nuevo contenido
        match_numero = re.search(r'párrafo\s+(\d+)', comando)
        match_contenido = re.search(r'(?:con|por|a)[:\s]+(.*)', comando, re.IGNORECASE | re.DOTALL)
        
        if match_numero and match_contenido:
            numero_parrafo = int(match_numero.group(1))
            contenido_nuevo = match_contenido.group(1).strip()
            
            # Encontrar y modificar el párrafo
            parrafo = demanda.obtener_parrafo_por_numero(numero_parrafo)
            if parrafo:
                contenido_original = parrafo['contenido']
                parrafo['contenido'] = contenido_nuevo
                parrafo['modificado'] = True
                parrafo['timestamp_modificacion'] = datetime.now().isoformat()
                
                # Registrar en historial
                comando_edicion = ComandoEdicion(
                    tipo=TipoComando.MODIFICAR,
                    referencia=f"párrafo {numero_parrafo}",
                    contenido=contenido_nuevo,
                    texto_original=contenido_original,
                    sesion_id=demanda.sesion_id,
                    timestamp=datetime.now().isoformat()
                )
                demanda.historial_ediciones.append(comando_edicion)
                
                return {
                    'exito': True,
                    'mensaje': f'Párrafo {numero_parrafo} modificado exitosamente',
                    'parrafos_actualizados': self._obtener_parrafos_para_vista(demanda)
                }
            else:
                return {
                    'exito': False,
                    'error': f'No se encontró el párrafo {numero_parrafo}'
                }
        
        return {
            'exito': False,
            'error': 'No se pudo extraer el número de párrafo o el nuevo contenido'
        }
    
    def _procesar_agregar_antes(self, comando: str, demanda: DemandaEstructurada) -> Dict[str, Any]:
        """Procesa comando: 'Agregar antes del párrafo X...'"""
        match_numero = re.search(r'párrafo\s+(\d+)', comando)
        match_contenido = re.search(r'agregar[:\s]+(.*)', comando, re.IGNORECASE | re.DOTALL)
        
        if match_numero and match_contenido:
            numero_parrafo = int(match_numero.group(1))
            contenido_nuevo = match_contenido.group(1).strip()
            
            # Crear nuevo párrafo
            nuevo_parrafo = {
                'numero': numero_parrafo - 0.5,  # Número previo
                'id': f'p_{numero_parrafo}_prev',
                'contenido': contenido_nuevo,
                'tipo': 'nuevo',
                'modificado': True,
                'timestamp_modificacion': datetime.now().isoformat()
            }
            
            # Insertar en la posición correcta
            insertado = False
            for i, parrafo in enumerate(demanda.parrafos):
                if parrafo['numero'] >= numero_parrafo:
                    demanda.parrafos.insert(i, nuevo_parrafo)
                    insertado = True
                    break
            
            if not insertado:
                demanda.parrafos.append(nuevo_parrafo)
            
            # Renumerar párrafos desde este punto
            self._renumerar_parrafos(demanda, numero_parrafo)
            
            # Registrar en historial
            comando_edicion = ComandoEdicion(
                tipo=TipoComando.AGREGAR_ANTES,
                referencia=f"párrafo {numero_parrafo}",
                contenido=contenido_nuevo,
                sesion_id=demanda.sesion_id,
                timestamp=datetime.now().isoformat()
            )
            demanda.historial_ediciones.append(comando_edicion)
            
            return {
                'exito': True,
                'mensaje': f'Párrafo agregado antes del párrafo {numero_parrafo}',
                'parrafos_actualizados': self._obtener_parrafos_para_vista(demanda)
            }
        
        return {
            'exito': False,
            'error': 'No se pudo extraer el número de párrafo o el contenido a agregar'
        }

    def _procesar_reemplazar(self, comando: str, demanda: DemandaEstructurada) -> Dict[str, Any]:
        """Procesa comando: 'Reemplazar "texto viejo" por "texto nuevo" en el párrafo X'"""
        # Buscar patrón de reemplazo
        match_reemplazo = re.search(r'reemplazar\s+"([^"]+)"\s+por\s+"([^"]+)"(?:\s+en\s+el\s+párrafo\s+(\d+))?', comando, re.IGNORECASE)
        
        if match_reemplazo:
            texto_viejo = match_reemplazo.group(1)
            texto_nuevo = match_reemplazo.group(2)
            numero_parrafo = int(match_reemplazo.group(3)) if match_reemplazo.group(3) else None
            
            if numero_parrafo:
                # Reemplazar en párrafo específico
                parrafo = demanda.obtener_parrafo_por_numero(numero_parrafo)
                if parrafo and texto_viejo in parrafo['contenido']:
                    contenido_original = parrafo['contenido']
                    parrafo['contenido'] = parrafo['contenido'].replace(texto_viejo, texto_nuevo)
                    parrafo['modificado'] = True
                    parrafo['timestamp_modificacion'] = datetime.now().isoformat()
                    
                    # Registrar cambio
                    comando_edicion = ComandoEdicion(
                        tipo=TipoComando.REEMPLAZAR,
                        referencia=f"párrafo {numero_parrafo}",
                        contenido=f"'{texto_viejo}' → '{texto_nuevo}'",
                        texto_original=contenido_original,
                        sesion_id=demanda.sesion_id,
                        timestamp=datetime.now().isoformat()
                    )
                    demanda.historial_ediciones.append(comando_edicion)
                    
                    return {
                        'exito': True,
                        'mensaje': f'Texto reemplazado en párrafo {numero_parrafo}',
                        'parrafos_actualizados': self._obtener_parrafos_para_vista(demanda)
                    }
                else:
                    return {
                        'exito': False,
                        'error': f'No se encontró el texto "{texto_viejo}" en el párrafo {numero_parrafo}'
                    }
            else:
                # Reemplazar en todos los párrafos que contengan el texto
                reemplazos_realizados = 0
                for parrafo in demanda.parrafos:
                    if texto_viejo in parrafo['contenido']:
                        contenido_original = parrafo['contenido']
                        parrafo['contenido'] = parrafo['contenido'].replace(texto_viejo, texto_nuevo)
                        parrafo['modificado'] = True
                        parrafo['timestamp_modificacion'] = datetime.now().isoformat()
                        reemplazos_realizados += 1
                        
                        # Registrar cambio
                        comando_edicion = ComandoEdicion(
                            tipo=TipoComando.REEMPLAZAR,
                            referencia=f"párrafo {parrafo['numero']}",
                            contenido=f"'{texto_viejo}' → '{texto_nuevo}'",
                            texto_original=contenido_original,
                            sesion_id=demanda.sesion_id,
                            timestamp=datetime.now().isoformat()
                        )
                        demanda.historial_ediciones.append(comando_edicion)
                
                if reemplazos_realizados > 0:
                    return {
                        'exito': True,
                        'mensaje': f'Texto reemplazado en {reemplazos_realizados} párrafo(s)',
                        'parrafos_actualizados': self._obtener_parrafos_para_vista(demanda)
                    }
                else:
                    return {
                        'exito': False,
                        'error': f'No se encontró el texto "{texto_viejo}" en ningún párrafo'
                    }
        
        return {
            'exito': False,
            'error': 'Formato de comando de reemplazo incorrecto. Usa: Reemplazar "texto viejo" por "texto nuevo" [en el párrafo X]'
        }

    def _procesar_eliminar(self, comando: str, demanda: DemandaEstructurada) -> Dict[str, Any]:
        """Procesa comando: 'Eliminar el párrafo X'"""
        match_numero = re.search(r'párrafo\s+(\d+)', comando)
        
        if match_numero:
            numero_parrafo = int(match_numero.group(1))
            
            # Encontrar y eliminar el párrafo
            for i, parrafo in enumerate(demanda.parrafos):
                if parrafo['numero'] == numero_parrafo:
                    parrafo_eliminado = demanda.parrafos.pop(i)
                    
                    # Registrar en historial para poder revertir
                    comando_edicion = ComandoEdicion(
                        tipo=TipoComando.ELIMINAR,
                        referencia=f"párrafo {numero_parrafo}",
                        contenido="",
                        texto_original=parrafo_eliminado['contenido'],
                        posicion=i,
                        sesion_id=demanda.sesion_id,
                        timestamp=datetime.now().isoformat()
                    )
                    demanda.historial_ediciones.append(comando_edicion)
                    
                    # Renumerar párrafos siguientes
                    self._renumerar_parrafos(demanda, numero_parrafo)
                    
                    return {
                        'exito': True,
                        'mensaje': f'Párrafo {numero_parrafo} eliminado exitosamente',
                        'parrafos_actualizados': self._obtener_parrafos_para_vista(demanda)
                    }
            
            return {
                'exito': False,
                'error': f'No se encontró el párrafo {numero_parrafo}'
            }
        
        return {
            'exito': False,
            'error': 'No se pudo extraer el número de párrafo a eliminar'
        }
    
    def _renumerar_parrafos(self, demanda: DemandaEstructurada, desde_numero: int):
        """Renumera los párrafos desde un número específico."""
        contador = desde_numero
        for parrafo in demanda.parrafos:
            if parrafo['numero'] >= desde_numero:
                parrafo['numero'] = contador
                parrafo['id'] = f"p_{contador}"
                contador += 1
    
    def _obtener_parrafos_para_vista(self, demanda: DemandaEstructurada) -> List[Dict]:
        """Obtiene los párrafos formateados para la vista."""
        return [
            {
                'numero': p['numero'],
                'contenido': p['contenido'],
                'tipo': p['tipo'],
                'modificado': p['modificado']
            }
            for p in demanda.parrafos
        ]
    
    def obtener_texto_completo_actualizado(self, sesion_id: str) -> str:
        """Regenera el texto completo de la demanda con todas las ediciones."""
        print(f"📄 [DEBUG] Obteniendo texto completo actualizado para sesión: {sesion_id}")
        
        demanda = self.obtener_demanda(sesion_id)
        if not demanda:
            print(f"❌ [DEBUG] No se encontró demanda para sesión: {sesion_id}")
            return ""
        
        print(f"📊 [DEBUG] Demanda encontrada con {len(demanda.parrafos)} párrafos")
        
        parrafos_texto = []
        for i, parrafo in enumerate(demanda.parrafos):
            parrafos_texto.append(parrafo['contenido'])
            if i == 0:  # Log del primer párrafo para debug
                print(f"📝 [DEBUG] Primer párrafo: {parrafo['contenido'][:100]}...")
        
        texto_completo = "\n\n".join(parrafos_texto)
        print(f"✅ [DEBUG] Texto completo generado ({len(texto_completo)} chars)")
        
        return texto_completo
    
    def obtener_historial_ediciones(self, sesion_id: str) -> List[Dict]:
        """Obtiene el historial de ediciones de una demanda."""
        demanda = self.obtener_demanda(sesion_id)
        if not demanda:
            return []
        
        return [
            {
                'tipo': cmd.tipo.value,
                'referencia': cmd.referencia,
                'contenido': cmd.contenido,
                'timestamp': cmd.timestamp
            }
            for cmd in demanda.historial_ediciones
        ]

    def actualizar_documento_completo(self, sesion_id: str, texto_actualizado: str):
        """Actualiza el texto completo de una demanda con el texto editado por IA."""
        print(f"🔄 [DEBUG] Actualizando documento completo para sesión: {sesion_id}")
        print(f"📝 [DEBUG] Longitud texto nuevo: {len(texto_actualizado)} caracteres")
        
        demanda = self.obtener_demanda(sesion_id)
        if not demanda:
            print(f"❌ [DEBUG] No se encontró demanda para sesión: {sesion_id}")
            # Crear nueva demanda si no existe
            demanda = self.inicializar_demanda(texto_actualizado, sesion_id)
            print(f"✅ [DEBUG] Nueva demanda creada para sesión: {sesion_id}")
        else:
            # Actualizar demanda existente
            demanda.parrafos = demanda._estructurar_parrafos(texto_actualizado)
            print(f"📊 [DEBUG] Documento reestructurado en {len(demanda.parrafos)} párrafos")
            
            # Registrar en historial
            comando_edicion = ComandoEdicion(
                tipo=TipoComando.MODIFICAR,
                referencia="documento_completo",
                contenido="Edición completa via IA",
                sesion_id=sesion_id,
                timestamp=datetime.now().isoformat()
            )
            demanda.historial_ediciones.append(comando_edicion)
            print(f"📋 [DEBUG] Edición registrada en historial")
        
        return demanda
    
    def guardar_cambios_en_db(self, sesion_id: str) -> bool:
        """Guarda los cambios de una demanda editada de vuelta a la base de datos."""
        try:
            from supabase_integration import supabase_admin
            
            demanda = self.demandas_activas.get(sesion_id)
            if not demanda:
                print(f"❌ [EDITOR] No hay demanda activa para guardar: {sesion_id}")
                return False
            
            # Regenerar el texto completo con todos los cambios
            texto_actualizado = self.obtener_texto_completo_actualizado(sesion_id)
            
            print(f"💾 [EDITOR] Guardando cambios en DB para sesión: {sesion_id}")
            print(f"📝 [EDITOR] Longitud del texto actualizado: {len(texto_actualizado)} caracteres")
            
            # Actualizar en la base de datos
            update_data = {
                "texto_demanda": texto_actualizado,
                "updated_at": datetime.now().isoformat()
            }
            
            response = supabase_admin.table('demandas_generadas')\
                .update(update_data)\
                .eq('session_id', sesion_id)\
                .execute()
            
            if response.data:
                print(f"✅ [EDITOR] Cambios guardados exitosamente en DB")
                return True
            else:
                print(f"⚠️ [EDITOR] No se actualizó ningún registro en DB")
                return False
                
        except Exception as e:
            print(f"❌ [EDITOR] Error guardando en DB: {str(e)}")
            return False

# Configuración del sistema de edición IA-First
USAR_IA_PARA_EDICION = True  # Cambiar a False para usar solo reglas rápidas
MODELO_IA = "gpt-4o"         # Modelo principal para máxima precisión
MODELO_IA_FALLBACK = "gpt-4o-mini"  # Modelo de fallback más rápido

# Cache en memoria para ediciones comunes
_cache_ediciones = {}  # {hash(texto+instruccion): resultado}

# Instancia global del editor
editor_demandas = EditorDemandas()

# SISTEMA IA-FIRST: Funciones de cache y IA mejorada

def _verificar_cache_ediciones(texto_original: str, instruccion: str) -> str:
    """
    Verifica si existe una edición similar en el cache.
    """
    import hashlib
    
    # Crear hash de la combinación texto + instrucción
    cache_key = hashlib.md5(f"{texto_original[:100]}_{instruccion}".encode()).hexdigest()
    
    resultado = _cache_ediciones.get(cache_key, texto_original)
    if resultado != texto_original:
        print(f"💾 [CACHE] Encontrada edición similar")
    
    return resultado

def _guardar_en_cache(texto_original: str, instruccion: str, resultado: str):
    """
    Guarda una edición exitosa en el cache.
    """
    import hashlib
    
    cache_key = hashlib.md5(f"{texto_original[:100]}_{instruccion}".encode()).hexdigest()
    _cache_ediciones[cache_key] = resultado
    
    # Limitar tamaño del cache (máximo 100 entradas)
    if len(_cache_ediciones) > 100:
        # Eliminar las más antiguas (simple FIFO)
        oldest_key = next(iter(_cache_ediciones))
        del _cache_ediciones[oldest_key]
    
    print(f"💾 [CACHE] Guardada edición exitosa")

def _aplicar_edicion_con_ia_mejorada(texto_original: str, instruccion: str) -> str:
    """
    Versión mejorada de edición con IA optimizada para precisión máxima.
    """
    try:
        import openai
        import os
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Prompt especializado para ediciones legales precisas
        prompt = f"""Eres un editor experto en documentos legales argentinos. Tu tarea es aplicar EXACTAMENTE la edición solicitada con máxima precisión.

TEXTO ORIGINAL:
"{texto_original}"

INSTRUCCIÓN DE EDICIÓN:
{instruccion}

ANÁLISIS REQUERIDO:
1. Identifica QUÉ parte específica del texto debe modificarse
2. Determina si es un cambio PARCIAL (nombre, empresa, fecha) o COMPLETO
3. Para cambios PARCIALES: mantén TODO lo demás idéntico
4. Para cambios COMPLETOS: reemplaza según la instrucción

REGLAS CRÍTICAS:
- Si la instrucción menciona "cambiar", "agregar", "modificar" algo específico → SOLO cambia esa parte
- Mantén EXACTAMENTE la puntuación, mayúsculas, formato y estructura original
- Para nombres: respeta el formato "Nombre Apellido" → "Nombre Segundo Apellido"
- Para empresas: mantén el formato legal (S.A., SRL, etc.)
- Para fechas: usa formato argentino dd/mm/yyyy
- NO agregues explicaciones, notas o comentarios
- NO agregues comillas ("") al inicio o final del texto
- NO uses formato de cita o markdown

CONTEXTO LEGAL:
- Es una demanda laboral argentina
- Usa terminología jurídica apropiada
- Mantén formalidad del documento

RESPONDE ÚNICAMENTE CON EL TEXTO MODIFICADO COMPLETO:"""

        # Usar modelo principal para máxima precisión
        response = client.chat.completions.create(
            model=MODELO_IA,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.05,  # Muy baja creatividad para máxima precisión
            max_tokens=1500,
            top_p=0.1  # Muy determinista
        )
        
        texto_modificado = response.choices[0].message.content.strip()
        
        # Limpiar comillas y caracteres problemáticos
        texto_modificado = _limpiar_respuesta_ia(texto_modificado)
        
        # Validar que el resultado no esté vacío y sea diferente
        if texto_modificado and texto_modificado != texto_original:
            # Verificar que no se perdió contenido importante
            palabras_originales = len(texto_original.split())
            palabras_modificadas = len(texto_modificado.split())
            
            # Si la diferencia es muy grande, podría ser un error
            if abs(palabras_originales - palabras_modificadas) > palabras_originales * 0.8:
                print(f"⚠️ [IA] Diferencia muy grande en longitud, usando fallback...")
                return _aplicar_edicion_con_ia_fallback(texto_original, instruccion)
            
            print(f"✅ [IA] Edición precisa aplicada con {MODELO_IA}")
            return texto_modificado
        else:
            print(f"⚠️ [IA] No se detectó cambio necesario")
            return texto_original
            
    except Exception as e:
        print(f"❌ [IA] Error con modelo principal: {str(e)}")
        # Fallback a modelo más simple
        return _aplicar_edicion_con_ia_fallback(texto_original, instruccion)

def _aplicar_edicion_con_ia_fallback(texto_original: str, instruccion: str) -> str:
    """
    Fallback usando modelo más rápido si el principal falla.
    """
    try:
        import openai
        import os
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt = f"""Aplica esta edición al texto legal:

TEXTO: "{texto_original}"
INSTRUCCIÓN: {instruccion}

Reglas:
1. Solo cambia lo solicitado
2. Mantén el resto igual
3. Responde solo con el texto modificado

RESULTADO:"""

        response = client.chat.completions.create(
            model=MODELO_IA_FALLBACK,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000
        )
        
        resultado = response.choices[0].message.content.strip()
        
        # Limpiar comillas y caracteres problemáticos
        resultado = _limpiar_respuesta_ia(resultado)
        
        if resultado and resultado != texto_original:
            print(f"✅ [IA] Fallback exitoso con {MODELO_IA_FALLBACK}")
            return resultado
        else:
            print(f"⚠️ [IA] Fallback sin cambios")
            return texto_original
            
    except Exception as e:
        print(f"❌ [IA] Error en fallback: {str(e)}")
        return _fallback_edicion_simple(texto_original, instruccion)

# NUEVA FUNCIONALIDAD: Procesamiento inteligente de selecciones
def procesar_edicion_contextual(texto_seleccionado: str, instruccion: str, sesion_id: str) -> Dict[str, Any]:
    """
    Procesa una edición contextual específica con el nuevo sistema híbrido.
    Solo modifica la parte seleccionada según la instrucción del usuario.
    """
    print(f"🎯 [EDITOR] Procesando edición contextual:")
    print(f"   📝 Texto seleccionado: '{texto_seleccionado[:50]}...'")
    print(f"   💭 Instrucción: '{instruccion}'")
    print(f"   🔗 Sesión: {sesion_id}")
    
    demanda = editor_demandas.obtener_demanda(sesion_id)
    if not demanda:
        print(f"❌ [EDITOR] No hay demanda activa para sesión: {sesion_id}")
        return {
            'exito': False,
            'error': 'No hay demanda activa para esta sesión. Genera una demanda primero.'
        }
    
    # Buscar el párrafo que contiene el texto seleccionado
    parrafo_encontrado = None
    posicion_en_parrafo = -1
    
    for parrafo in demanda.parrafos:
        if texto_seleccionado in parrafo['contenido']:
            parrafo_encontrado = parrafo
            posicion_en_parrafo = parrafo['contenido'].find(texto_seleccionado)
            break
    
    if not parrafo_encontrado:
        print(f"❌ [EDITOR] Texto seleccionado no encontrado en ningún párrafo")
        return {
            'exito': False,
            'error': f'No se encontró el texto seleccionado "{texto_seleccionado}" en el documento'
        }
    
    print(f"✅ [EDITOR] Texto encontrado en párrafo {parrafo_encontrado['numero']}")
    
    # USAR EL NUEVO SISTEMA HÍBRIDO DE EDICIÓN
    try:
        # Aplicar el sistema híbrido de 3 niveles
        texto_modificado = aplicar_edicion_inteligente(texto_seleccionado, instruccion)
        
        # Verificar si hubo cambio
        if texto_modificado != texto_seleccionado:
            # Reemplazar solo la parte seleccionada
            contenido_original = parrafo_encontrado['contenido']
            nuevo_contenido = contenido_original.replace(texto_seleccionado, texto_modificado, 1)  # Solo primera ocurrencia
            
            # Actualizar el párrafo
            parrafo_encontrado['contenido'] = nuevo_contenido
            parrafo_encontrado['modificado'] = True
            parrafo_encontrado['timestamp_modificacion'] = datetime.now().isoformat()
            
            # Registrar en historial
            comando_edicion = ComandoEdicion(
                tipo=TipoComando.REEMPLAZAR,
                referencia=f"párrafo {parrafo_encontrado['numero']} (híbrido)",
                contenido=f"'{texto_seleccionado}' → '{texto_modificado}'",
                texto_original=contenido_original,
                sesion_id=sesion_id,
                timestamp=datetime.now().isoformat()
            )
            demanda.historial_ediciones.append(comando_edicion)
            
            print(f"✅ [EDITOR] Edición híbrida aplicada exitosamente")
            print(f"   🔄 '{texto_seleccionado}' → '{texto_modificado}'")
            
            # Guardar cambios automáticamente en la base de datos
            guardado_exitoso = editor_demandas.guardar_cambios_en_db(sesion_id)
            
            return {
                'exito': True,
                'mensaje': f'Texto modificado con sistema híbrido en párrafo {parrafo_encontrado["numero"]}',
                'texto_original': texto_seleccionado,
                'texto_nuevo': texto_modificado,
                'parrafo_numero': parrafo_encontrado['numero'],
                'cambio_aplicado': True,
                'guardado_en_db': guardado_exitoso,
                'metodo_usado': 'sistema_hibrido'
            }
        else:
            print(f"⚠️ [EDITOR] Sistema híbrido no pudo generar cambio para: '{instruccion}'")
            return {
                'exito': False,
                'error': f'El sistema híbrido no pudo aplicar la instrucción: "{instruccion}". Intenta ser más específico (ej: "cambiar ARCOR S.A. por MICROSOFT" o "la empresa es MICROSOFT")'
            }
            
    except Exception as e:
        print(f"❌ [EDITOR] Error en sistema híbrido: {str(e)}")
        return {
            'exito': False,
            'error': f'Error en el sistema híbrido: {str(e)}'
        }

def aplicar_edicion_inteligente(texto_original: str, instruccion: str) -> str:
    """
    Aplica una edición inteligente al texto según la instrucción del usuario.
    Enfoque IA-First: Prioriza IA para máxima precisión, con cache para velocidad.
    """
    import re
    instruccion_lower = instruccion.lower().strip()
    
    print(f"🧠 [EDITOR] Analizando instrucción (IA-First): '{instruccion}'")
    
    # PASO 1: Verificar cache de ediciones comunes primero
    resultado_cache = _verificar_cache_ediciones(texto_original, instruccion)
    if resultado_cache != texto_original:
        print(f"⚡ [EDITOR] Encontrado en cache")
        return resultado_cache
    
    # PASO 2: IA como método principal (máxima precisión)
    if USAR_IA_PARA_EDICION:
        print(f"🤖 [EDITOR] Procesando con IA (método principal)...")
        resultado_ia = _aplicar_edicion_con_ia_mejorada(texto_original, instruccion)
        
        # Guardar en cache si fue exitoso
        if resultado_ia != texto_original:
            _guardar_en_cache(texto_original, instruccion, resultado_ia)
        
        return resultado_ia
    
    # PASO 3: Fallback solo si IA está desactivada
    print(f"⚠️ [EDITOR] IA desactivada - usando reglas básicas...")
    resultado_reglas = _aplicar_reglas_rapidas(texto_original, instruccion, instruccion_lower)
    if resultado_reglas != texto_original:
        return resultado_reglas
    
    return _fallback_edicion_simple(texto_original, instruccion)

def _aplicar_reglas_rapidas(texto_original: str, instruccion: str, instruccion_lower: str) -> str:
    """
    Aplica reglas rápidas para casos comunes.
    Retorna el texto original si no se puede aplicar ninguna regla.
    """
    import re
    
    # PATRONES CONTEXTUALES - Detectar cambios específicos según el contexto
    
    # NUEVO: Patrón para cambios de nombres específicos
    # "cambiar Gino Gentile por Gino Gustavo Gentile" o "el nombre es X"
    match_cambio_nombre = re.search(r'(?:cambiar|reemplazar)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:por|a)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', instruccion, re.IGNORECASE)
    if match_cambio_nombre:
        nombre_viejo = match_cambio_nombre.group(1)
        nombre_nuevo = match_cambio_nombre.group(2)
        if nombre_viejo in texto_original:
            print(f"👤 [EDITOR] Cambiando nombre específico: '{nombre_viejo}' → '{nombre_nuevo}'")
            return texto_original.replace(nombre_viejo, nombre_nuevo)
    
    # Patrón: "el nombre es X" (buscar y reemplazar nombre existente)
    match_nombre_es = re.search(r'el nombre es\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', instruccion, re.IGNORECASE)
    if match_nombre_es:
        nombre_nuevo = match_nombre_es.group(1)
        # Buscar patrón de nombre existente en el texto (Nombre Apellido, o Nombre Segundo Apellido)
        nombres_encontrados = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?=,|\s+argentino|\s+con\s+DNI)', texto_original)
        if nombres_encontrados:
            nombre_viejo = nombres_encontrados[0]
            print(f"👤 [EDITOR] Reemplazando nombre detectado: '{nombre_viejo}' → '{nombre_nuevo}'")
            return texto_original.replace(nombre_viejo, nombre_nuevo)
    
    # Patrón genérico: "agregar X al nombre" o "incluir X en el nombre"
    match_agregar_nombre = re.search(r'(?:agregar|incluir|añadir)\s+([a-z]+)\s+(?:al|en el|en|al)\s+nombre', instruccion_lower)
    if match_agregar_nombre:
        palabra_agregar = match_agregar_nombre.group(1).title()
        # Buscar nombre existente en el texto (antes de coma o antes de "argentino")
        nombre_match = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+)(?=,|\s+argentino)', texto_original)
        if nombre_match:
            nombre_viejo = nombre_match.group(1)
            # Insertar la nueva palabra en el medio (segundo nombre)
            partes_nombre = nombre_viejo.split()
            nuevo_nombre = f"{partes_nombre[0]} {palabra_agregar} {partes_nombre[1]}"
            print(f"👤 [EDITOR] Agregando al nombre: '{nombre_viejo}' → '{nuevo_nombre}'")
            return texto_original.replace(nombre_viejo, nuevo_nombre)
    
    # Patrón: "la empresa es X" - reemplazar empresa en el texto
    match_empresa = re.search(r'la empresa es\s+([^,\.]+)', instruccion_lower)
    if match_empresa:
        nueva_empresa = match_empresa.group(1).strip().upper()
        # Buscar patrones de empresa en el texto original
        empresas_encontradas = re.findall(r'[A-Z][A-Z\s\.&]+(?:S\.A\.|SRL|LTDA?|S\.R\.L\.|INC|CORP)', texto_original)
        if empresas_encontradas:
            empresa_original = empresas_encontradas[0]
            print(f"🏢 [EDITOR] Reemplazando empresa: '{empresa_original}' → '{nueva_empresa}'")
            return texto_original.replace(empresa_original, nueva_empresa)
    
    # Patrón: "el demandado es X"
    match_demandado = re.search(r'el demandado es\s+([^,\.]+)', instruccion_lower)
    if match_demandado:
        nuevo_demandado = match_demandado.group(1).strip()
        # Buscar nombre del demandado en el texto
        demandados_encontrados = re.findall(r'contra\s+([A-Z][A-Z\s\.&]+)(?:,|\s)', texto_original)
        if demandados_encontrados:
            demandado_original = demandados_encontrados[0].strip()
            print(f"🏢 [EDITOR] Reemplazando demandado: '{demandado_original}' → '{nuevo_demandado}'")
            return texto_original.replace(demandado_original, nuevo_demandado)
    
    # Patrón: "cambiar X por Y" o "reemplazar X por Y"
    match_cambio_explicito = re.search(r'(?:cambiar|reemplazar)\s+["\']?([^"\']+?)["\']?\s+por\s+["\']?([^"\']+)["\']?', instruccion_lower)
    if match_cambio_explicito:
        texto_viejo = match_cambio_explicito.group(1).strip()
        texto_nuevo = match_cambio_explicito.group(2).strip()
        # Buscar el texto viejo en el original (case insensitive)
        pattern = re.compile(re.escape(texto_viejo), re.IGNORECASE)
        if pattern.search(texto_original):
            print(f"🏢 [EDITOR] Reemplazo explícito: '{texto_viejo}' → '{texto_nuevo}'")
            return pattern.sub(texto_nuevo, texto_original, count=1)
    
    # Cambios de género
    if 'cambiar por demandada' in instruccion_lower or 'demandada' in instruccion_lower:
        if 'demandado' in texto_original.lower():
            return texto_original.replace('demandado', 'demandada').replace('Demandado', 'Demandada')
    
    if 'cambiar por demandado' in instruccion_lower or 'demandado' in instruccion_lower:
        if 'demandada' in texto_original.lower():
            return texto_original.replace('demandada', 'demandado').replace('Demandada', 'Demandado')
    
    # Cambios de número (singular/plural)
    if 'plural' in instruccion_lower or 'pluralizar' in instruccion_lower:
        # Reglas básicas de pluralización en español
        if texto_original.endswith('o'):
            return texto_original[:-1] + 'os'
        elif texto_original.endswith('a'):
            return texto_original[:-1] + 'as'
        elif texto_original.endswith('e'):
            return texto_original + 's'
        else:
            return texto_original + 'es'
    
    if 'singular' in instruccion_lower or 'singularizar' in instruccion_lower:
        # Reglas básicas de singularización
        if texto_original.endswith('os'):
            return texto_original[:-2] + 'o'
        elif texto_original.endswith('as'):
            return texto_original[:-2] + 'a'
        elif texto_original.endswith('es'):
            return texto_original[:-2]
        elif texto_original.endswith('s'):
            return texto_original[:-1]
    
    # Cambios de tiempo verbal
    if 'pasado' in instruccion_lower or 'pretérito' in instruccion_lower:
        # Conversiones básicas a pasado
        if texto_original.endswith('r'):  # infinitivo
            if texto_original.endswith('ar'):
                return texto_original[:-2] + 'ó'
            elif texto_original.endswith('er') or texto_original.endswith('ir'):
                return texto_original[:-2] + 'ió'
    
    # Cambios directos con "cambiar por" o "reemplazar por" (sin texto específico)
    match_cambiar = re.search(r'cambiar\s+por\s+["\']?([^"\']+)["\']?', instruccion_lower)
    if match_cambiar:
        return match_cambiar.group(1).strip()
    
    match_reemplazar = re.search(r'reemplazar\s+por\s+["\']?([^"\']+)["\']?', instruccion_lower)
    if match_reemplazar:
        return match_reemplazar.group(1).strip()
    
    # Mayúsculas/minúsculas
    if 'mayúscula' in instruccion_lower or 'mayuscula' in instruccion_lower:
        return texto_original.upper()
    
    if 'minúscula' in instruccion_lower or 'minuscula' in instruccion_lower:
        return texto_original.lower()
    
    if 'capitalizar' in instruccion_lower or 'título' in instruccion_lower:
        return texto_original.title()
    
    # Agregar texto
    if 'agregar' in instruccion_lower or 'añadir' in instruccion_lower:
        match_agregar = re.search(r'(?:agregar|añadir)\s+["\']?([^"\']+)["\']?', instruccion_lower)
        if match_agregar:
            texto_a_agregar = match_agregar.group(1).strip()
            if 'al final' in instruccion_lower or 'después' in instruccion_lower:
                return texto_original + ' ' + texto_a_agregar
            elif 'al inicio' in instruccion_lower or 'antes' in instruccion_lower:
                return texto_a_agregar + ' ' + texto_original
            else:
                return texto_original + ' ' + texto_a_agregar
    
    # Si no se puede procesar con reglas simples, retornar el original
    print(f"⚠️ [EDITOR] Reglas rápidas no aplicables")
    return texto_original

def _aplicar_edicion_con_ia(texto_original: str, instruccion: str) -> str:
    """
    Usa un LLM para interpretar y aplicar la instrucción de edición.
    Enfoque más flexible para cambios complejos.
    """
    try:
        import openai
        import os
        
        # Configurar OpenAI (usar la misma configuración del proyecto)
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt = f"""Eres un editor de texto legal especializado. Tu tarea es aplicar EXACTAMENTE la edición solicitada al texto dado.

TEXTO ORIGINAL:
"{texto_original}"

INSTRUCCIÓN DE EDICIÓN:
{instruccion}

REGLAS CRÍTICAS:
1. Si la instrucción menciona cambiar solo UNA PARTE específica del texto (como un nombre, empresa, fecha, etc.), MANTÉN todo lo demás EXACTAMENTE igual
2. NO reemplaces todo el texto si solo se solicita cambiar una parte específica
3. Identifica QUÉ específicamente debe cambiar y DÓNDE está en el texto
4. Mantén el formato, puntuación, mayúsculas y estructura original
5. Responde ÚNICAMENTE con el texto modificado completo, sin explicaciones

EJEMPLOS:
- Si dice "cambiar el nombre" → Solo cambia el nombre, mantén todo el resto
- Si dice "la empresa es X" → Solo cambia la empresa mencionada
- Si dice "agregar Gustavo al nombre" → Inserta "Gustavo" en el nombre existente

TEXTO MODIFICADO:"""

        response = client.chat.completions.create(
            model=MODELO_IA,  # Configuración global del modelo
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Baja creatividad para precisión
            max_tokens=1000
        )
        
        texto_modificado = response.choices[0].message.content.strip()
        
        # Limpiar comillas y caracteres problemáticos
        texto_modificado = _limpiar_respuesta_ia(texto_modificado)
        
        # Validar que el resultado no esté vacío y sea diferente
        if texto_modificado and texto_modificado != texto_original:
            print(f"✅ [EDITOR] IA aplicó cambio exitosamente")
            return texto_modificado
        else:
            print(f"⚠️ [EDITOR] IA no pudo aplicar cambio, manteniendo original")
            return texto_original
            
    except Exception as e:
        print(f"❌ [EDITOR] Error en edición con IA: {str(e)}")
        
        # Fallback: intentar un enfoque simple de reemplazo inteligente
        return _fallback_edicion_simple(texto_original, instruccion)

def _fallback_edicion_simple(texto_original: str, instruccion: str) -> str:
    """
    Fallback cuando la IA falla. Intenta extraer cambios obvios de la instrucción.
    """
    import re
    
    print(f"🔄 [EDITOR] Aplicando fallback simple")
    
    # PATRONES ESPECÍFICOS para cambios parciales
    # "agregar Gustavo" en contexto de nombres
    if 'agregar' in instruccion.lower() and any(palabra in instruccion.lower() for palabra in ['nombre', 'gustavo', 'segundo']):
        match_agregar = re.search(r'agregar\s+([A-Za-z]+)', instruccion, re.IGNORECASE)
        if match_agregar:
            palabra_nueva = match_agregar.group(1).title()
            # Buscar nombre en el texto y agregar la palabra
            nombres_match = re.search(r'([A-Z][a-z]+)\s+([A-Z][a-z]+)', texto_original)
            if nombres_match:
                primer_nombre = nombres_match.group(1)
                apellido = nombres_match.group(2)
                nuevo_nombre = f"{primer_nombre} {palabra_nueva} {apellido}"
                resultado = texto_original.replace(nombres_match.group(0), nuevo_nombre)
                print(f"🎯 [EDITOR] Fallback agregó al nombre: '{nombres_match.group(0)}' → '{nuevo_nombre}'")
                return resultado
    
    # Buscar patrones como "cambiar a X", "debe ser X", "usar X", etc.
    # PERO solo si la instrucción parece ser para reemplazar TODO el texto
    if len(instruccion.split()) <= 4:  # Instrucciones cortas probablemente son reemplazos totales
        patrones_cambio = [
            r'cambiar\s+a\s+([^,\.]+)',
            r'debe\s+ser\s+([^,\.]+)', 
            r'usar\s+([^,\.]+)',
            r'poner\s+([^,\.]+)',
            r'escribir\s+([^,\.]+)',
            r'es\s+([^,\.]+)',
        ]
        
        for patron in patrones_cambio:
            match = re.search(patron, instruccion.lower())
            if match:
                nuevo_texto = match.group(1).strip()
                print(f"🎯 [EDITOR] Fallback detectó cambio completo a: '{nuevo_texto}'")
                return nuevo_texto
    
    # Si no encuentra nada, retornar original
    print(f"⚠️ [EDITOR] Fallback no pudo procesar: '{instruccion}'")
    return texto_original

# Actualizar la clase EditorDemandas para incluir el nuevo método
class EditorDemandasMejorado(EditorDemandas):
    """Versión mejorada con edición contextual optimizada."""
    
    def procesar_comando(self, comando: str, sesion_id: str) -> Dict[str, Any]:
        """
        Procesa comandos incluyendo ediciones contextuales.
        Método principal que decide si usar edición contextual o tradicional.
        """
        print(f"🎯 [EDITOR] Procesando comando: {comando[:100]}...")
        
        # Detectar si es una edición contextual (formato del Canvas)
        if comando.startswith('Reemplazar "') and '" según:' in comando:
            # Extraer texto a reemplazar e instrucción
            import re
            match = re.search(r'Reemplazar "([^"]+)" según: (.+)', comando)
            if match:
                texto_seleccionado = match.group(1)
                instruccion = match.group(2)
                return procesar_edicion_contextual(texto_seleccionado, instruccion, sesion_id)
        
        # Si no es contextual, usar el método tradicional
        return self.procesar_comando_natural(comando, sesion_id)

# Reemplazar la instancia global
editor_demandas = EditorDemandasMejorado()

def _limpiar_respuesta_ia(texto: str) -> str:
    """
    Limpia la respuesta de la IA removiendo comillas extra y caracteres problemáticos
    que pueden romper el formato del documento.
    """
    if not texto:
        return texto
    
    texto = texto.strip()
    
    # Remover comillas dobles al inicio y final
    if texto.startswith('"') and texto.endswith('"'):
        texto = texto[1:-1].strip()
        print(f"🧹 [LIMPIEZA] Removidas comillas dobles")
    
    # Remover comillas simples al inicio y final
    if texto.startswith("'") and texto.endswith("'"):
        texto = texto[1:-1].strip()
        print(f"🧹 [LIMPIEZA] Removidas comillas simples")
    
    # Remover comillas tipográficas
    if texto.startswith(""") and texto.endswith("""):
        texto = texto[1:-1].strip()
        print(f"🧹 [LIMPIEZA] Removidas comillas tipográficas")
    
    # Remover markdown code blocks
    if texto.startswith("```") and texto.endswith("```"):
        texto = texto[3:-3].strip()
        print(f"🧹 [LIMPIEZA] Removido markdown code block")
    
    # Remover backticks simples
    if texto.startswith("`") and texto.endswith("`"):
        texto = texto[1:-1].strip()
        print(f"🧹 [LIMPIEZA] Removidos backticks")
    
    return texto

def procesar_edicion_global(instruccion: str, sesion_id: str) -> Dict[str, Any]:
    """
    Procesa una modificación global en todo el documento usando el sistema IA-FIRST.
    Aplica la instrucción a TODO el documento, no solo a una selección.
    
    Ejemplos:
    - "cambiar Gino Gentile por Gino Gustavo Gentile"
    - "reemplazar todas las fechas por 15/03/2024"
    - "cambiar ARCOR S.A. por MICROSOFT"
    """
    print(f"🌍 [EDITOR] Procesando edición GLOBAL:")
    print(f"   💭 Instrucción: '{instruccion}'")
    print(f"   🔗 Sesión: {sesion_id}")
    
    demanda = editor_demandas.obtener_demanda(sesion_id)
    if not demanda:
        print(f"❌ [EDITOR] No hay demanda activa para sesión: {sesion_id}")
        return {
            'exito': False,
            'error': 'No hay demanda activa para esta sesión. Genera una demanda primero.'
        }
    
    # Obtener el texto completo del documento
    documento_completo = "\n\n".join([p['contenido'] for p in demanda.parrafos])
    
    if not documento_completo.strip():
        return {
            'exito': False,
            'error': 'El documento está vacío. No hay contenido para modificar.'
        }
    
    print(f"📄 [EDITOR] Documento completo: {len(documento_completo)} caracteres")
    
    try:
        # USAR EL SISTEMA IA-FIRST PARA MODIFICACIÓN GLOBAL
        documento_modificado = aplicar_edicion_global_inteligente(documento_completo, instruccion)
        
        # Verificar si hubo cambios
        if documento_modificado != documento_completo:
            # Dividir el documento modificado en párrafos
            parrafos_modificados = documento_modificado.split('\n\n')
            
            # Actualizar cada párrafo
            cambios_realizados = 0
            for i, parrafo_nuevo in enumerate(parrafos_modificados):
                if i < len(demanda.parrafos):
                    parrafo_actual = demanda.parrafos[i]
                    if parrafo_actual['contenido'].strip() != parrafo_nuevo.strip():
                        contenido_original = parrafo_actual['contenido']
                        parrafo_actual['contenido'] = parrafo_nuevo.strip()
                        parrafo_actual['modificado'] = True
                        parrafo_actual['timestamp_modificacion'] = datetime.now().isoformat()
                        cambios_realizados += 1
                        
                        # Registrar cambio en historial
                        comando_edicion = ComandoEdicion(
                            tipo=TipoComando.REEMPLAZAR,
                            referencia=f"párrafo {parrafo_actual['numero']} (global)",
                            contenido=f"Modificación global: '{instruccion}'",
                            texto_original=contenido_original,
                            sesion_id=sesion_id,
                            timestamp=datetime.now().isoformat()
                        )
                        demanda.historial_ediciones.append(comando_edicion)
            
            # Guardar cambios automáticamente
            guardado_exitoso = editor_demandas.guardar_cambios_en_db(sesion_id)
            
            print(f"✅ [EDITOR] Modificación global aplicada: {cambios_realizados} párrafos modificados")
            
            return {
                'exito': True,
                'mensaje': f'Modificación global aplicada exitosamente. {cambios_realizados} párrafos modificados.',
                'parrafos_modificados': cambios_realizados,
                'cambio_aplicado': True,
                'guardado_en_db': guardado_exitoso,
                'metodo_usado': 'edicion_global_ia'
            }
        else:
            print(f"⚠️ [EDITOR] No se detectaron cambios necesarios")
            return {
                'exito': False,
                'error': f'No se detectaron cambios necesarios para la instrucción: "{instruccion}". Verifica que el texto a modificar existe en el documento.'
            }
            
    except Exception as e:
        print(f"❌ [EDITOR] Error en edición global: {str(e)}")
        return {
            'exito': False,
            'error': f'Error procesando la modificación global: {str(e)}'
        }

def aplicar_edicion_global_inteligente(documento_completo: str, instruccion: str) -> str:
    """
    Aplica una modificación global al documento completo usando el sistema IA-FIRST.
    Optimizado para cambios repetitivos en todo el documento.
    """
    print(f"🧠 [EDITOR] Aplicando edición global IA-FIRST: '{instruccion}'")
    
    # PASO 1: Verificar cache de ediciones globales
    resultado_cache = _verificar_cache_ediciones(documento_completo[:200], f"GLOBAL:{instruccion}")
    if resultado_cache != documento_completo[:200]:
        print(f"⚡ [EDITOR] Encontrada edición global similar en cache")
        # Aplicar el patrón cacheado al documento completo
        return _aplicar_patron_cacheado(documento_completo, instruccion, resultado_cache)
    
    # PASO 2: Detectar patrones de edición global comunes
    resultado_patrones = _aplicar_patrones_globales_rapidos(documento_completo, instruccion)
    if resultado_patrones != documento_completo:
        print(f"⚡ [EDITOR] Aplicado patrón global rápido")
        _guardar_en_cache(documento_completo[:200], f"GLOBAL:{instruccion}", resultado_patrones[:200])
        return resultado_patrones
    
    # PASO 3: IA para modificaciones globales complejas
    if USAR_IA_PARA_EDICION:
        print(f"🤖 [EDITOR] Procesando edición global con IA...")
        resultado_ia = _aplicar_edicion_global_con_ia(documento_completo, instruccion)
        
        if resultado_ia != documento_completo:
            _guardar_en_cache(documento_completo[:200], f"GLOBAL:{instruccion}", resultado_ia[:200])
            return resultado_ia
    
    print(f"⚠️ [EDITOR] No se pudo aplicar modificación global")
    return documento_completo

def _aplicar_patrones_globales_rapidos(documento: str, instruccion: str) -> str:
    """
    Aplica patrones de edición global comunes de forma rápida.
    """
    import re
    instruccion_lower = instruccion.lower()
    
    print(f"🔍 [EDITOR] Buscando patrones globales rápidos...")
    
    # PATRÓN 1: "cambiar X por Y" o "reemplazar X por Y"
    match_cambio = re.search(r'(?:cambiar|reemplazar)\s+(.+?)\s+por\s+(.+)', instruccion, re.IGNORECASE)
    if match_cambio:
        texto_viejo = match_cambio.group(1).strip()
        texto_nuevo = match_cambio.group(2).strip()
        
        # Limpiar comillas si las hay
        texto_viejo = texto_viejo.strip('"\'')
        texto_nuevo = texto_nuevo.strip('"\'')
        
        if texto_viejo in documento:
            print(f"🏢 [EDITOR] Patrón global - Reemplazando '{texto_viejo}' por '{texto_nuevo}'")
            return documento.replace(texto_viejo, texto_nuevo)
    
    # PATRÓN 2: "el nombre es X" (cambiar nombre en todo el documento)
    match_nombre = re.search(r'el nombre es\s+(.+)', instruccion, re.IGNORECASE)
    if match_nombre:
        nombre_nuevo = match_nombre.group(1).strip()
        # Buscar patrones de nombre completo en el documento
        nombres_encontrados = re.findall(r'[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', documento)
        if nombres_encontrados:
            # Reemplazar el primer nombre encontrado en todo el documento
            nombre_viejo = nombres_encontrados[0]
            print(f"👤 [EDITOR] Patrón global - Cambiando nombre '{nombre_viejo}' por '{nombre_nuevo}'")
            return documento.replace(nombre_viejo, nombre_nuevo)
    
    # PATRÓN 3: "agregar X al nombre" (en todo el documento)
    match_agregar = re.search(r'agregar\s+(.+?)\s+al nombre', instruccion, re.IGNORECASE)
    if match_agregar:
        palabra_nueva = match_agregar.group(1).strip().title()
        # Buscar y modificar nombres en todo el documento
        def reemplazar_nombre(match):
            nombre_completo = match.group(0)
            partes = nombre_completo.split()
            if len(partes) >= 2:
                # Insertar la palabra nueva entre el primer nombre y apellido
                return f"{partes[0]} {palabra_nueva} {' '.join(partes[1:])}"
            return nombre_completo
        
        resultado = re.sub(r'[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', reemplazar_nombre, documento)
        if resultado != documento:
            print(f"👤 [EDITOR] Patrón global - Agregando '{palabra_nueva}' a nombres")
            return resultado
    
    # PATRÓN 4: "cambiar todas las fechas por X"
    match_fechas = re.search(r'(?:cambiar|reemplazar)\s+(?:todas las )?fechas?\s+por\s+(.+)', instruccion, re.IGNORECASE)
    if match_fechas:
        fecha_nueva = match_fechas.group(1).strip()
        # Buscar y reemplazar patrones de fecha
        patron_fecha = r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}'
        if re.search(patron_fecha, documento):
            print(f"📅 [EDITOR] Patrón global - Cambiando fechas por '{fecha_nueva}'")
            return re.sub(patron_fecha, fecha_nueva, documento)
    
    # PATRÓN 5: "cambiar empresa por X" o "la empresa es X"
    match_empresa = re.search(r'(?:cambiar empresa|la empresa es)\s+(.+)', instruccion, re.IGNORECASE)
    if match_empresa:
        empresa_nueva = match_empresa.group(1).strip()
        # Buscar patrones de empresa (terminaciones S.A., SRL, etc.)
        patron_empresa = r'[A-Z][A-Z\s]+(?:S\.A\.|SRL|S\.R\.L\.|SOCIEDAD ANÓNIMA|LIMITADA)'
        empresas_encontradas = re.findall(patron_empresa, documento)
        if empresas_encontradas:
            empresa_vieja = empresas_encontradas[0]
            print(f"🏢 [EDITOR] Patrón global - Cambiando empresa '{empresa_vieja}' por '{empresa_nueva}'")
            return documento.replace(empresa_vieja, empresa_nueva)
    
    return documento

def _aplicar_edicion_global_con_ia(documento: str, instruccion: str) -> str:
    """
    Usa IA para modificaciones globales complejas en todo el documento.
    """
    try:
        import openai
        import os
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt = f"""Eres un editor experto en documentos legales argentinos. Tu tarea es aplicar una MODIFICACIÓN GLOBAL a TODO el documento.

DOCUMENTO COMPLETO:
{documento}

INSTRUCCIÓN GLOBAL:
{instruccion}

ANÁLISIS REQUERIDO:
1. Identifica TODOS los lugares donde se debe aplicar el cambio
2. Aplica la modificación de forma CONSISTENTE en todo el documento
3. Mantén el formato, estructura y estilo legal original
4. Asegúrate de que el cambio sea COHERENTE en todo el documento

REGLAS CRÍTICAS:
- Aplica el cambio EN TODAS las ocurrencias relevantes
- Mantén la estructura de párrafos EXACTAMENTE igual
- Conserva toda la puntuación, mayúsculas y formato original
- NO agregues explicaciones o notas
- NO uses comillas ("") al inicio o final
- Mantén el lenguaje jurídico formal

CONTEXTO LEGAL:
- Es una demanda laboral argentina
- Mantén terminología jurídica apropiada
- Respeta el formato legal estándar

RESPONDE ÚNICAMENTE CON EL DOCUMENTO MODIFICADO COMPLETO:"""

        response = client.chat.completions.create(
            model=MODELO_IA,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.05,  # Muy baja para precisión
            max_tokens=2000,
            top_p=0.1
        )
        
        documento_modificado = response.choices[0].message.content.strip()
        documento_modificado = _limpiar_respuesta_ia(documento_modificado)
        
        if documento_modificado and documento_modificado != documento:
            print(f"✅ [IA] Modificación global aplicada exitosamente")
            return documento_modificado
        else:
            print(f"⚠️ [IA] No se detectaron cambios necesarios")
            return documento
            
    except Exception as e:
        print(f"❌ [IA] Error en modificación global: {str(e)}")
        return documento

def _aplicar_patron_cacheado(documento: str, instruccion: str, patron_cache: str) -> str:
    """
    Aplica un patrón encontrado en cache al documento completo.
    """
    # Implementación simple - en producción sería más sofisticada
    # Por ahora, aplicar la instrucción usando patrones rápidos
    return _aplicar_patrones_globales_rapidos(documento, instruccion)