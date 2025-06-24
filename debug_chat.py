#!/usr/bin/env python3
import sys
import traceback
sys.path.append('.')
from rag.chat_agent import ChatAgentInteligente
import json

print("🔧 Debug del ChatAgent...")

try:
    agent = ChatAgentInteligente()
    print("✅ ChatAgent creado exitosamente")
    
    # Test 1: Inicialización básica
    session = {
        'mensajes': [],
        'estado': 'inicio',
        'datos_cliente': {},
        'tipo_demanda': None,
        'hechos_adicionales': '',
        'notas_abogado': ''
    }
    print(f"✅ Sesión inicial creada: {session}")
    
    # Test 2: Selección de tipo
    print("\n🧪 Test 2: Seleccionando tipo 'Empleados En Blanco'...")
    try:
        resultado = agent.procesar_mensaje(session, "Empleados En Blanco", "test-session")
        print(f"✅ Resultado: {resultado.get('mensaje', '')[:100]}...")
        print(f"🎯 Tipo en sesión: {session.get('tipo_demanda')}")
    except Exception as e:
        print(f"❌ Error en selección de tipo: {e}")
        traceback.print_exc()
    
    # Test 3: Procesamiento de datos
    print("\n🧪 Test 3: Enviando datos de Gino...")
    try:
        mensaje_gino = "Gino Gentile, Paraguay 2536, 35703591, me despidieron sin causa aparente de la empresa GEDCO"
        resultado = agent.procesar_mensaje(session, mensaje_gino, "test-session")
        print(f"✅ Resultado: {resultado.get('mensaje', '')[:150]}...")
        print(f"🎯 Datos en sesión: {session.get('datos_cliente', {})}")
        print(f"📝 Hechos en sesión: {session.get('hechos_adicionales', '')[:100]}...")
    except Exception as e:
        print(f"❌ Error procesando datos: {e}")
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Error crítico: {e}")
    traceback.print_exc() 