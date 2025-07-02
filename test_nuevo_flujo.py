#!/usr/bin/env python3
"""
Script de prueba para verificar el nuevo flujo sin mensaje inicial automático.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from rag.chat_agent import ChatAgentInteligente
import asyncio

async def test_nuevo_flujo():
    """Prueba el nuevo flujo sin mensaje inicial automático."""
    
    print("🧪 INICIANDO PRUEBA DEL NUEVO FLUJO")
    print("=" * 60)
    
    # Crear agente con user_id de prueba
    user_id = "test-user-123"
    agent = ChatAgentInteligente(user_id)
    
    # Simular sesión nueva (estado = "inicio")
    session = {
        "estado": "inicio",
        "datos_cliente": {},
        "tipo_demanda": "",
        "hechos_adicionales": "",
        "notas_abogado": "",
        "user_id": user_id
    }
    
    session_id = "test-session-123"
    
    print("\n📝 PRUEBA 1: Primer mensaje sin mensaje inicial automático")
    print("Mensaje: 'Necesito ayuda con Despido'")
    
    mensaje1 = "Necesito ayuda con Despido"
    resultado1 = await agent.procesar_mensaje(session.copy(), mensaje1, session_id)
    
    print(f"✅ Respuesta obtenida: {len(resultado1['mensaje'])} caracteres")
    print(f"📄 Respuesta: {resultado1['mensaje']}")
    print(f"🎛️ Estado final: {session.get('estado', 'N/A')}")
    
    # Verificar que NO muestra el mensaje inicial
    if "¡Hola doctor!" in resultado1['mensaje']:
        print("❌ MENSAJE INICIAL SE MOSTRÓ (NO DEBERÍA)")
    else:
        print("✅ MENSAJE INICIAL NO SE MOSTRÓ (CORRECTO)")
    
    # Verificar que detectó el tipo de demanda
    if "Despido" in resultado1['mensaje']:
        print("✅ TIPO DE DEMANDA DETECTADO CORRECTAMENTE")
    else:
        print("❌ TIPO DE DEMANDA NO DETECTADO")
    
    print("\n" + "=" * 60)
    print("📝 PRUEBA 2: Mensaje con datos del cliente")
    print("Mensaje: 'El cliente se llama Juan Pérez, DNI 12345678'")
    
    # Simular que ya tiene tipo de demanda
    session2 = {
        "estado": "necesita_datos_cliente",
        "datos_cliente": {},
        "tipo_demanda": "Despido",
        "hechos_adicionales": "",
        "notas_abogado": "",
        "user_id": user_id
    }
    
    mensaje2 = "El cliente se llama Juan Pérez, DNI 12345678"
    resultado2 = await agent.procesar_mensaje(session2, mensaje2, session_id)
    
    print(f"✅ Respuesta obtenida: {len(resultado2['mensaje'])} caracteres")
    print(f"📄 Respuesta: {resultado2['mensaje']}")
    print(f"🎛️ Estado final: {session2.get('estado', 'N/A')}")
    
    # Verificar que detectó los datos del cliente
    if "Juan Pérez" in resultado2['mensaje'] or "12345678" in resultado2['mensaje']:
        print("✅ DATOS DEL CLIENTE DETECTADOS CORRECTAMENTE")
    else:
        print("❌ DATOS DEL CLIENTE NO DETECTADOS")
    
    print("\n" + "=" * 60)
    print("📝 PRUEBA 3: Mensaje libre sin categoría específica")
    print("Mensaje: 'Tengo un problema laboral'")
    
    session3 = {
        "estado": "inicio",
        "datos_cliente": {},
        "tipo_demanda": "",
        "hechos_adicionales": "",
        "notas_abogado": "",
        "user_id": user_id
    }
    
    mensaje3 = "Tengo un problema laboral"
    resultado3 = await agent.procesar_mensaje(session3, mensaje3, session_id)
    
    print(f"✅ Respuesta obtenida: {len(resultado3['mensaje'])} caracteres")
    print(f"📄 Respuesta: {resultado3['mensaje']}")
    print(f"🎛️ Estado final: {session3.get('estado', 'N/A')}")
    
    # Verificar que procesa el mensaje libre
    if "problema laboral" in resultado3['mensaje'].lower() or "laboral" in resultado3['mensaje'].lower():
        print("✅ MENSAJE LIBRE PROCESADO CORRECTAMENTE")
    else:
        print("❌ MENSAJE LIBRE NO PROCESADO")
    
    print("\n" + "=" * 60)
    print("✅ PRUEBA DEL NUEVO FLUJO COMPLETADA")

if __name__ == "__main__":
    asyncio.run(test_nuevo_flujo()) 