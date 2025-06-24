#!/usr/bin/env python3
"""
Script para probar el ChatAgent después de las correcciones del error NoneType.
"""

import sys
import os
import traceback
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio raíz al path
sys.path.append('.')

def test_openai_key():
    """Verifica que la clave de OpenAI esté configurada."""
    print("🔑 Verificando clave de OpenAI...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY no está configurada")
        return False
    
    if len(api_key) < 20:
        print("❌ OPENAI_API_KEY parece estar mal configurada (muy corta)")
        return False
    
    print(f"✅ OPENAI_API_KEY configurada correctamente (longitud: {len(api_key)})")
    return True

def test_chatagent_initialization():
    """Verifica que el ChatAgent se pueda inicializar."""
    print("\n🤖 Probando inicialización del ChatAgent...")
    
    try:
        from rag.chat_agent import ChatAgentInteligente
        
        agent = ChatAgentInteligente()
        print("✅ ChatAgent inicializado exitosamente")
        print(f"📋 Tipos disponibles: {len(agent.tipos_disponibles)}")
        
        return agent
    except Exception as e:
        print(f"❌ Error inicializando ChatAgent: {e}")
        traceback.print_exc()
        return None

def test_basic_message_processing(agent):
    """Prueba el procesamiento básico de mensajes."""
    print("\n💬 Probando procesamiento de mensajes...")
    
    try:
        # Crear sesión de prueba
        session = {
            'datos_cliente': {},
            'tipo_demanda': '',
            'hechos_adicionales': '',
            'notas_abogado': '',
            'estado': 'inicio'
        }
        
        # Mensaje de prueba simple
        mensaje = "Hola, necesito ayuda con una demanda laboral"
        session_id = "test-123"
        
        print(f"📝 Enviando mensaje: {mensaje}")
        resultado = agent.procesar_mensaje(session, mensaje, session_id)
        
        if resultado and isinstance(resultado, dict):
            print("✅ Mensaje procesado exitosamente")
            print(f"📤 Respuesta: {resultado.get('mensaje', 'Sin mensaje')[:100]}...")
            return True
        else:
            print("❌ El resultado no es válido")
            return False
            
    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")
        traceback.print_exc()
        return False

def test_data_extraction(agent):
    """Prueba la extracción de datos específicos."""
    print("\n🔍 Probando extracción de datos...")
    
    try:
        # Crear sesión con tipo ya seleccionado
        session = {
            'datos_cliente': {},
            'tipo_demanda': 'Empleados En Blanco',
            'hechos_adicionales': '',
            'notas_abogado': '',
            'estado': 'conversando'
        }
        
        # Mensaje con datos específicos
        mensaje = "Gino Gentile, Paraguay 2536, 35703591, me despidieron sin causa de la empresa GEDCO"
        session_id = "test-456"
        
        print(f"📝 Enviando datos: {mensaje}")
        resultado = agent.procesar_mensaje(session, mensaje, session_id)
        
        if resultado and isinstance(resultado, dict):
            print("✅ Datos procesados exitosamente")
            print(f"📋 Datos extraídos en sesión: {session.get('datos_cliente', {})}")
            print(f"📝 Hechos: {session.get('hechos_adicionales', 'N/A')[:50]}...")
            return True
        else:
            print("❌ Error en extracción de datos")
            return False
            
    except Exception as e:
        print(f"❌ Error extrayendo datos: {e}")
        traceback.print_exc()
        return False

def main():
    """Función principal de pruebas."""
    print("🧪 PRUEBAS DEL CHATAGENT CORREGIDO")
    print("=" * 50)
    
    # Test 1: Verificar clave de OpenAI
    if not test_openai_key():
        print("\n❌ Las pruebas no pueden continuar sin la clave de OpenAI")
        return
    
    # Test 2: Inicializar ChatAgent
    agent = test_chatagent_initialization()
    if not agent:
        print("\n❌ Las pruebas no pueden continuar sin ChatAgent")
        return
    
    # Test 3: Procesamiento básico
    if not test_basic_message_processing(agent):
        print("\n❌ Error en procesamiento básico")
        return
    
    # Test 4: Extracción de datos
    if not test_data_extraction(agent):
        print("\n❌ Error en extracción de datos")
        return
    
    print("\n✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    print("🎉 El ChatAgent está funcionando correctamente")

if __name__ == "__main__":
    main() 