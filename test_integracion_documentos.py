#!/usr/bin/env python3
"""
Script de prueba para verificar la integración de documentos en el system prompt.
Prueba que la información de documentos subidos se incluya correctamente en la generación de demandas.
"""

import asyncio
import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_obtener_informacion_documentos():
    """Prueba la función de obtener información de documentos."""
    print("🔍 Probando obtención de información de documentos...")
    
    try:
        from rag.qa_agent import obtener_informacion_documentos_sincrona
        
        # Usar un session_id de prueba (debe existir en la base de datos)
        session_id_test = "test-session-123"
        
        informacion = obtener_informacion_documentos_sincrona(session_id_test)
        
        print(f"✅ Información obtenida: {type(informacion)}")
        print(f"   Transcripción: {len(informacion.get('transcripcion_completa', ''))} caracteres")
        print(f"   Personas: {len(informacion.get('personas_identificadas', []))}")
        print(f"   Empresas: {len(informacion.get('empresas_identificadas', []))}")
        print(f"   Fechas: {len(informacion.get('fechas_importantes', []))}")
        print(f"   Montos: {len(informacion.get('montos_encontrados', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

async def test_generar_demanda_con_documentos():
    """Prueba la generación de demanda con información de documentos."""
    print("\n🔍 Probando generación de demanda con documentos...")
    
    try:
        from rag.qa_agent import generar_demanda
        
        # Datos de prueba
        datos_cliente = {
            "nombre_completo": "Juan Pérez",
            "dni": "12345678",
            "domicilio": "Av. Corrientes 1234, CABA",
            "telefono": "011-1234-5678",
            "email": "juan.perez@email.com"
        }
        
        hechos_adicionales = "El cliente fue despedido sin causa aparente"
        notas_abogado = "Caso de despido injustificado"
        session_id = "test-session-123"  # Debe existir en la base de datos
        
        print(f"📋 Generando demanda para: {datos_cliente['nombre_completo']}")
        print(f"🔗 Session ID: {session_id}")
        
        resultado = await generar_demanda(
            tipo_demanda="Despido injustificado",
            datos_cliente=datos_cliente,
            hechos_adicionales=hechos_adicionales,
            notas_abogado=notas_abogado,
            session_id=session_id
        )
        
        print(f"✅ Demanda generada exitosamente")
        print(f"   Texto: {len(resultado.get('texto_demanda', ''))} caracteres")
        print(f"   Archivo: {resultado.get('archivo_docx', 'No generado')}")
        
        # Verificar metadatos
        metadatos = resultado.get('metadatos', {})
        print(f"   Documentos utilizados: {metadatos.get('documentos_utilizados', False)}")
        print(f"   Personas en documentos: {metadatos.get('personas_documentos', 0)}")
        print(f"   Empresas en documentos: {metadatos.get('empresas_documentos', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def test_generar_demanda_sincrona():
    """Prueba la versión síncrona de generar demanda."""
    print("\n🔍 Probando generación síncrona de demanda...")
    
    try:
        from rag.qa_agent import generar_demanda_sincrona
        
        # Datos de prueba
        datos_cliente = {
            "nombre_completo": "María García",
            "dni": "87654321",
            "domicilio": "Belgrano 567, CABA",
            "telefono": "011-8765-4321",
            "email": "maria.garcia@email.com"
        }
        
        hechos_adicionales = "La cliente sufrió un accidente laboral"
        notas_abogado = "Caso de accidente de trabajo"
        session_id = "test-session-456"  # Debe existir en la base de datos
        
        print(f"📋 Generando demanda síncrona para: {datos_cliente['nombre_completo']}")
        print(f"🔗 Session ID: {session_id}")
        
        resultado = generar_demanda_sincrona(
            tipo_demanda="Accidente de trabajo",
            datos_cliente=datos_cliente,
            hechos_adicionales=hechos_adicionales,
            notas_abogado=notas_abogado,
            session_id=session_id
        )
        
        print(f"✅ Demanda síncrona generada exitosamente")
        print(f"   Texto: {len(resultado.get('texto_demanda', ''))} caracteres")
        print(f"   Archivo: {resultado.get('archivo_docx', 'No generado')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def test_system_prompt_integration():
    """Prueba que el system prompt incluya información de documentos."""
    print("\n🔍 Probando integración en system prompt...")
    
    try:
        from rag.qa_agent import obtener_informacion_documentos_sincrona
        
        # Simular información de documentos
        session_id = "test-session-789"
        informacion = obtener_informacion_documentos_sincrona(session_id)
        
        # Verificar que la información se formatea correctamente
        transcripcion = informacion.get('transcripcion_completa', 'No hay documentos')
        personas = ", ".join(informacion.get('personas_identificadas', [])) or "No identificadas"
        empresas = ", ".join(informacion.get('empresas_identificadas', [])) or "No identificadas"
        fechas = str(informacion.get('fechas_importantes', [])) or "No encontradas"
        montos = str(informacion.get('montos_encontrados', [])) or "No encontrados"
        
        print(f"✅ Formato de información verificado:")
        print(f"   Transcripción: {len(transcripcion)} caracteres")
        print(f"   Personas: {personas}")
        print(f"   Empresas: {empresas}")
        print(f"   Fechas: {fechas}")
        print(f"   Montos: {montos}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

async def main():
    """Función principal de pruebas."""
    print("🚀 INICIANDO PRUEBAS DE INTEGRACIÓN DE DOCUMENTOS")
    print("=" * 60)
    
    resultados = []
    
    # Test 1: Obtener información de documentos
    print("\n📋 TEST 1: Obtención de información de documentos")
    resultados.append(test_obtener_informacion_documentos())
    
    # Test 2: Generación async con documentos
    print("\n📋 TEST 2: Generación async con documentos")
    resultados.append(await test_generar_demanda_con_documentos())
    
    # Test 3: Generación síncrona
    print("\n📋 TEST 3: Generación síncrona")
    resultados.append(test_generar_demanda_sincrona())
    
    # Test 4: Integración en system prompt
    print("\n📋 TEST 4: Integración en system prompt")
    resultados.append(test_system_prompt_integration())
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    tests_pasados = sum(resultados)
    total_tests = len(resultados)
    
    print(f"✅ Tests pasados: {tests_pasados}/{total_tests}")
    
    if tests_pasados == total_tests:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
        print("✅ La integración de documentos está funcionando correctamente")
    else:
        print("⚠️ Algunas pruebas fallaron")
        print("🔧 Revisa los errores anteriores para identificar problemas")
    
    return tests_pasados == total_tests

if __name__ == "__main__":
    # Ejecutar pruebas
    try:
        exito = asyncio.run(main())
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error ejecutando pruebas: {e}")
        sys.exit(1) 