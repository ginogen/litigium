#!/usr/bin/env python3
import sys
import traceback
import os
sys.path.append('.')

print("🔧 Debug detallado del ChatAgent...")

# Test 1: Verificar variables de entorno
print("\n1️⃣ Variables de entorno:")
openai_key = os.getenv('OPENAI_API_KEY')
print(f"   OPENAI_API_KEY: {'✅ Configurada' if openai_key else '❌ No configurada'}")
if openai_key:
    print(f"   Longitud: {len(openai_key)} caracteres")
    print(f"   Primeros 10 chars: {openai_key[:10]}...")

# Test 2: Importar y crear ChatAgent
print("\n2️⃣ Importación del ChatAgent:")
try:
    from rag.chat_agent import ChatAgentInteligente, get_chat_agent
    print("   ✅ Importación exitosa")
    
    # Test 3: Crear instancia directa
    print("\n3️⃣ Creación de instancia directa:")
    try:
        agent_directo = ChatAgentInteligente()
        print("   ✅ Instancia directa creada")
    except Exception as e:
        print(f"   ❌ Error creando instancia directa: {e}")
        agent_directo = None
    
    # Test 4: Usar get_chat_agent()
    print("\n4️⃣ Función get_chat_agent():")
    try:
        agent = get_chat_agent()
        print(f"   get_chat_agent() devolvió: {type(agent)}")
        if agent:
            print("   ✅ get_chat_agent() exitoso")
        else:
            print("   ❌ get_chat_agent() devolvió None")
    except Exception as e:
        print(f"   ❌ Error en get_chat_agent(): {e}")
        traceback.print_exc()
        agent = None
    
    # Test 5: Probar procesar_mensaje si tenemos agent
    if agent:
        print("\n5️⃣ Test de procesar_mensaje:")
        try:
            # Crear sesión de prueba
            session_test = {
                'datos_cliente': {},
                'tipo_demanda': '',
                'hechos_adicionales': '',
                'notas_abogado': '',
                'estado': 'inicio'
            }
            
            print("   📝 Enviando mensaje de prueba...")
            resultado = agent.procesar_mensaje(session_test, "hola, como empezamos?", "test-123")
            
            print(f"   Resultado tipo: {type(resultado)}")
            if resultado:
                print(f"   ✅ procesar_mensaje devolvió: {type(resultado)}")
                print(f"   Contiene mensaje: {'mensaje' in resultado}")
                if 'mensaje' in resultado:
                    print(f"   Mensaje: {resultado['mensaje'][:100]}...")
            else:
                print(f"   ❌ procesar_mensaje devolvió None")
                
        except Exception as e:
            print(f"   ❌ Error en procesar_mensaje: {e}")
            print(f"   Tipo de error: {type(e).__name__}")
            traceback.print_exc()
    else:
        print("\n5️⃣ No se puede probar procesar_mensaje (agent es None)")

except ImportError as e:
    print(f"   ❌ Error de importación: {e}")
except Exception as e:
    print(f"   ❌ Error inesperado: {e}")
    traceback.print_exc()

print("\n�� Debug completado") 