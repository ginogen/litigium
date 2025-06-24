#!/usr/bin/env python3
import requests
import json
import time

print("🧪 Probando comunicación Frontend -> Backend...")
print("⚠️  NOTA: Algunas rutas requieren autenticación de Supabase")
print("📋 Si hay errores 403, asegúrate de estar logueado en el frontend primero")

BASE_URL = "http://localhost:8000"

# 1. Test de inicialización de chat
print("\n1️⃣ Probando inicialización de chat...")
try:
    response = requests.post(f"{BASE_URL}/api/chat/iniciar", timeout=10)
    if response.status_code == 200:
        data = response.json()
        session_id = data.get("session_id")
        print(f"✅ Chat iniciado - Session ID: {session_id}")
        print(f"📝 Mensaje de bienvenida: {data.get('respuesta', '')[:100]}...")
        print(f"🎯 Opciones disponibles: {data.get('opciones', [])}")
    else:
        print(f"❌ Error iniciando chat: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    exit(1)

# 2. Test de selección de tipo
print("\n2️⃣ Probando selección de tipo 'Empleados En Blanco'...")
try:
    response = requests.post(f"{BASE_URL}/api/chat/mensaje", 
                           json={"mensaje": "Empleados En Blanco", "session_id": session_id},
                           timeout=30)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Tipo seleccionado correctamente")
        print(f"📝 Respuesta: {data.get('respuesta', '')[:150]}...")
        print(f"🎯 Opciones: {data.get('opciones', [])}")
        print(f"📋 Requiere datos: {data.get('requiere_datos', False)}")
    else:
        print(f"❌ Error seleccionando tipo: {response.status_code}")
        print(f"📄 Respuesta: {response.text}")
except Exception as e:
    print(f"❌ Error enviando mensaje: {e}")

# 3. Test de envío de datos completos (como el caso de Gino)
print("\n3️⃣ Probando envío de datos completos...")
mensaje_gino = "Gino Gentile, Paraguay 2536, 35703591, me despidieron sin causa aparente de la empresa GEDCO"
try:
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/api/chat/mensaje", 
                           json={"mensaje": mensaje_gino, "session_id": session_id},
                           timeout=60)  # Timeout más largo para generación
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Datos procesados en {elapsed:.1f} segundos")
        print(f"📝 Respuesta: {data.get('respuesta', '')[:200]}...")
        print(f"🎯 Demanda generada: {data.get('demanda_generada', False)}")
        print(f"👁️ Mostrar preview: {data.get('mostrar_preview', False)}")
        print(f"📥 Mostrar descarga: {data.get('mostrar_descarga', False)}")
    else:
        print(f"❌ Error procesando datos: {response.status_code}")
        print(f"📄 Respuesta: {response.text}")
except Exception as e:
    print(f"❌ Error procesando datos completos: {e}")

print("\n�� Test completado.") 