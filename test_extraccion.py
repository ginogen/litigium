#!/usr/bin/env python3
import sys
sys.path.append('.')
import asyncio
from rag.chat_agent import ChatAgentInteligente
import json

async def test_nuevo_flujo():
    """Test del flujo mejorado del chat agent"""
    print("🧪 Probando nuevo flujo mejorado...")
    
    agent = ChatAgentInteligente()
    session = {
        'mensajes': [],
        'estado': 'inicio',
        'datos_cliente': {},
        'tipo_demanda': '',
        'hechos_adicionales': '',
        'notas_abogado': ''
    }
    
    print("\n=== TEST 1: Mensaje inicial ===")
    resultado1 = await agent.procesar_mensaje(session, 'Hola', 'test-123')
    print(f"Respuesta: {resultado1['mensaje'][:200]}...")
    
    print("\n=== TEST 2: Información completa en un mensaje ===")
    mensaje_completo = 'Necesito una demanda por despido. El cliente es Pablo Andres Mariani, DNI 35703591, Paraguay 2536. Lo despidieron sin causa de la empresa GEDCO el 15 de junio.'
    
    resultado2 = await agent.procesar_mensaje(session, mensaje_completo, 'test-123')
    print(f"Completitud: {resultado2.get('progreso_completitud', 0)}%")
    print(f"Mostrar confirmación: {resultado2.get('mostrar_confirmacion', False)}")
    print(f"Respuesta: {resultado2['mensaje'][:200]}...")
    
    print("\n=== ESTADO FINAL DE LA SESIÓN ===")
    print(f"Estado: {session.get('estado')}")
    print(f"Datos cliente: {session.get('datos_cliente')}")
    print(f"Tipo demanda: {session.get('tipo_demanda')}")
    print(f"Hechos: {session.get('hechos_adicionales', '')[:100]}...")
    
    print("\n✅ Test completado!")

if __name__ == "__main__":
    asyncio.run(test_nuevo_flujo()) 