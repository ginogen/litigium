#!/usr/bin/env python3
import sys
sys.path.append('.')
from rag.chat_agent import ChatAgentInteligente
import json

# Test del sistema mejorado
print("🧪 Probando sistema de extracción mejorado...")

agent = ChatAgentInteligente()
session = {
    'mensajes': [],
    'estado': 'inicio',
    'datos_cliente': {},
    'tipo_demanda': 'Empleados En Blanco',  # Ya había seleccionado este tipo
    'hechos_adicionales': '',
    'notas_abogado': ''
}

mensaje = 'Gino Gentile, Paraguay 2536, 35703591, me despidieron sin causa aparente de la empresa GEDCO'
print(f"📝 Mensaje a procesar: {mensaje}")
print(f"🎯 Tipo ya seleccionado: {session['tipo_demanda']}")

resultado = agent.procesar_mensaje(session, mensaje, 'test-123')
print('=== RESULTADO ===')
print(json.dumps(resultado, indent=2, ensure_ascii=False))

print('\n=== ESTADO DE LA SESIÓN ===')
print(f"Estado: {session.get('estado')}")
print(f"Datos cliente: {session.get('datos_cliente')}")
print(f"Hechos: {session.get('hechos_adicionales', '')[:100]}...") 