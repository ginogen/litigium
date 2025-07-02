#!/usr/bin/env python3
"""
Script de prueba para verificar que el mensaje inicial se muestra correctamente
en nuevas conversaciones, independientemente del contenido del mensaje del usuario.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from rag.chat_agent import ChatAgentInteligente
import asyncio

async def test_mensaje_inicial():
    """Prueba que el mensaje inicial se muestre en conversaciones nuevas."""
    
    print("🧪 INICIANDO PRUEBA DE MENSAJE INICIAL")
    print("=" * 50)
    
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
    
    # Caso 1: Mensaje corto sin tipo de demanda
    print("\n📝 CASO 1: Mensaje corto sin tipo de demanda")
    print("Mensaje: 'Hola'")
    
    mensaje1 = "Hola"
    resultado1 = await agent.procesar_mensaje(session.copy(), mensaje1, session_id)
    
    print(f"Respuesta: {resultado1['mensaje'][:100]}...")
    print(f"Estado final: {session.get('estado', 'N/A')}")
    
    # Caso 2: Mensaje con tipo de demanda
    print("\n📝 CASO 2: Mensaje con tipo de demanda")
    print("Mensaje: 'Quiero ayuda con Despido'")
    
    session2 = {
        "estado": "inicio",
        "datos_cliente": {},
        "tipo_demanda": "",
        "hechos_adicionales": "",
        "notas_abogado": "",
        "user_id": user_id
    }
    
    mensaje2 = "Quiero ayuda con Despido"
    resultado2 = await agent.procesar_mensaje(session2, mensaje2, session_id)
    
    print(f"Respuesta: {resultado2['mensaje'][:100]}...")
    print(f"Estado final: {session2.get('estado', 'N/A')}")
    
    # Caso 3: Mensaje largo con información completa
    print("\n📝 CASO 3: Mensaje largo con información completa")
    print("Mensaje: 'Necesito una demanda de despido para Juan Pérez, DNI 12345678, trabajaba en blanco y negro'")
    
    session3 = {
        "estado": "inicio",
        "datos_cliente": {},
        "tipo_demanda": "",
        "hechos_adicionales": "",
        "notas_abogado": "",
        "user_id": user_id
    }
    
    mensaje3 = "Necesito una demanda de despido para Juan Pérez, DNI 12345678, trabajaba en blanco y negro"
    resultado3 = await agent.procesar_mensaje(session3, mensaje3, session_id)
    
    print(f"Respuesta: {resultado3['mensaje'][:100]}...")
    print(f"Estado final: {session3.get('estado', 'N/A')}")
    
    print("\n✅ PRUEBA COMPLETADA")

if __name__ == "__main__":
    asyncio.run(test_mensaje_inicial()) 