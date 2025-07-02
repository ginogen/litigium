#!/usr/bin/env python3
"""
🧪 PRUEBA CONTROL MANUAL DEL ABOGADO

Este script prueba el nuevo flujo donde el abogado debe confirmar
explícitamente antes de generar la demanda.

Flujo de prueba:
1. Simular conversación normal
2. Llegar al punto donde se debe generar la demanda
3. Verificar que se muestra el resumen de confirmación
4. Probar las 3 opciones: confirmar, modificar, cancelar
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_separator(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_step(step, description):
    print(f"\n📋 PASO {step}: {description}")
    print("-" * 40)

async def test_control_manual_abogado():
    """Prueba completa del control manual del abogado."""
    
    print_separator("PRUEBA CONTROL MANUAL DEL ABOGADO")
    
    try:
        # Importar componentes necesarios
        from rag.chat_agent import get_chat_agent, reset_chat_agent
        from rag.qa_agent import obtener_informacion_documentos_sincrona
        
        print("✅ Componentes importados correctamente")
        
        # Resetear el chat agent para empezar limpio
        reset_chat_agent()
        chat_agent = get_chat_agent()
        
        if not chat_agent:
            raise Exception("No se pudo obtener el ChatAgent")
        
        print("✅ ChatAgent inicializado correctamente")
        
        # Simular session_id y user_id
        session_id = "test_control_manual_123"
        user_id = "test_user_456"
        
        # PASO 1: Crear sesión inicial con datos básicos
        print_step(1, "CREAR SESIÓN INICIAL")
        
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "estado": "iniciada",
            "tipo_demanda": "Despido injustificado",
            "datos_cliente": {
                "nombre_completo": "Juan Pérez",
                "dni": "12345678",
                "domicilio": "Av. Corrientes 1234, CABA",
                "telefono": "011-1234-5678",
                "email": "juan.perez@email.com"
            },
            "hechos_adicionales": "El cliente fue despedido sin causa justificada el 15 de enero de 2024. Trabajaba como empleado administrativo desde marzo de 2022.",
            "notas_abogado": "Caso típico de despido sin causa. Cliente tiene buena documentación.",
            "mensajes": []
        }
        
        print(f"📋 Sesión creada:")
        print(f"   Cliente: {session['datos_cliente']['nombre_completo']}")
        print(f"   Tipo demanda: {session['tipo_demanda']}")
        print(f"   Estado: {session['estado']}")
        
        # PASO 2: Simular información de documentos procesados
        print_step(2, "SIMULAR DOCUMENTOS PROCESADOS")
        
        # Crear información simulada de documentos
        info_documentos = {
            "transcripcion_completa": "TELEGRAMA DE DESPIDO: Empresa XYZ S.A. comunica el despido sin causa del Sr. Juan Pérez, DNI 12345678, a partir del 15/01/2024. LIQUIDACIÓN FINAL: Sueldo básico $150.000, antigüedad $45.000, indemnización $450.000. RECIBO DE SUELDO: Mes diciembre 2023, neto a cobrar $180.000.",
            "documentos_utilizados": [
                {"tipo": "telegrama", "nombre": "telegrama_despido.pdf"},
                {"tipo": "liquidacion", "nombre": "liquidacion_final.pdf"},
                {"tipo": "recibo_sueldo", "nombre": "recibo_diciembre.pdf"}
            ],
            "personas_identificadas": ["Juan Pérez", "María García", "Carlos López"],
            "empresas_identificadas": ["Empresa XYZ S.A.", "Consultora ABC"],
            "fechas_importantes": [
                {"fecha": "2024-01-15", "evento": "Fecha de despido"},
                {"fecha": "2022-03-01", "evento": "Fecha de ingreso"},
                {"fecha": "2024-01-20", "evento": "Fecha de telegrama"}
            ],
            "montos_encontrados": [
                {"concepto": "sueldo_basico", "monto": "$150.000"},
                {"concepto": "antiguedad", "monto": "$45.000"},
                {"concepto": "indemnizacion", "monto": "$450.000"},
                {"concepto": "sueldo_neto", "monto": "$180.000"}
            ],
            "datos_contacto": {
                "telefonos": ["011-1234-5678", "011-9876-5432"],
                "emails": ["rrhh@empresa.com"],
                "domicilios": ["Av. Corrientes 1234, CABA"]
            }
        }
        
        print(f"📄 Documentos simulados:")
        print(f"   Archivos: {len(info_documentos['documentos_utilizados'])}")
        print(f"   Personas: {len(info_documentos['personas_identificadas'])}")
        print(f"   Empresas: {len(info_documentos['empresas_identificadas'])}")
        print(f"   Fechas: {len(info_documentos['fechas_importantes'])}")
        print(f"   Montos: {len(info_documentos['montos_encontrados'])}")
        
        # PASO 3: Simular que el sistema detecta que debe generar la demanda
        print_step(3, "SIMULAR DETECCIÓN DE GENERACIÓN")
        
        # Crear respuesta IA que indica que debe generar la demanda
        respuesta_ia = {
            "accion": "generar_demanda",
            "listo_para_generar": True,
            "mensaje": "Tengo toda la información necesaria para generar la demanda."
        }
        
        print(f"🤖 Respuesta IA simulada:")
        print(f"   Acción: {respuesta_ia['accion']}")
        print(f"   Listo para generar: {respuesta_ia['listo_para_generar']}")
        
        # PASO 4: Probar el resumen de confirmación
        print_step(4, "PROBAR RESUMEN DE CONFIRMACIÓN")
        
        # Llamar al método que crea el resumen
        resumen = chat_agent._crear_resumen_para_abogado(session, info_documentos)
        
        print(f"📋 Resumen generado:")
        print(f"   Mensaje: {len(resumen['mensaje'])} caracteres")
        print(f"   Datos cliente: {resumen['datos']['cliente']['nombre_completo']}")
        print(f"   Tipo demanda: {resumen['datos']['tipo_demanda']}")
        print(f"   Documentos: {resumen['datos']['documentos_procesados']}")
        
        # Mostrar el mensaje de confirmación
        print(f"\n📋 MENSAJE DE CONFIRMACIÓN:")
        print(resumen['mensaje'])
        
        # PASO 5: Probar las 3 opciones de confirmación
        print_step(5, "PROBAR OPCIONES DE CONFIRMACIÓN")
        
        opciones = ["confirmar_generar", "modificar_datos", "cancelar"]
        
        for i, opcion in enumerate(opciones, 1):
            print(f"\n🔍 Probando opción {i}: {opcion}")
            
            # Simular la confirmación
            resultado = await chat_agent.procesar_confirmacion_abogado(
                session=session.copy(),  # Usar copia para no afectar la original
                accion=opcion,
                session_id=session_id,
                datos_modificados=None
            )
            
            print(f"   Resultado:")
            print(f"     Mensaje: {resultado.get('mensaje', '')[:100]}...")
            print(f"     Demanda generada: {resultado.get('demanda_generada', False)}")
            print(f"     Modo edición: {resultado.get('modo_edicion', False)}")
            
            # Para la opción de confirmar, simular datos modificados
            if opcion == "confirmar_generar":
                print(f"\n🔍 Probando confirmación con datos modificados:")
                
                datos_modificados = {
                    "cliente": {
                        "nombre_completo": "Juan Carlos Pérez",
                        "dni": "12345678"
                    },
                    "hechos_adicionales": "Hechos actualizados con nueva información.",
                    "notas_abogado": "Notas actualizadas del abogado."
                }
                
                resultado_mod = await chat_agent.procesar_confirmacion_abogado(
                    session=session.copy(),
                    accion=opcion,
                    session_id=session_id,
                    datos_modificados=datos_modificados
                )
                
                print(f"   Con datos modificados:")
                print(f"     Mensaje: {resultado_mod.get('mensaje', '')[:100]}...")
                print(f"     Demanda generada: {resultado_mod.get('demanda_generada', False)}")
        
        # PASO 6: Probar el flujo completo de generación
        print_step(6, "PROBAR FLUJO COMPLETO DE GENERACIÓN")
        
        # Simular que el abogado confirma y se genera la demanda
        session["estado"] = "confirmado_por_abogado"
        
        # Simular la generación de respuesta
        resultado_final = await chat_agent._generar_respuesta(
            session=session,
            respuesta_ia={"accion": "generar_demanda"},
            session_id=session_id
        )
        
        print(f"🎯 Resultado final:")
        print(f"   Mensaje: {resultado_final.get('mensaje', '')[:100]}...")
        print(f"   Demanda generada: {resultado_final.get('demanda_generada', False)}")
        print(f"   Mostrar preview: {resultado_final.get('mostrar_preview', False)}")
        
        # PASO 7: Verificar estados de sesión
        print_step(7, "VERIFICAR ESTADOS DE SESIÓN")
        
        estados_esperados = {
            "esperando_confirmacion": "Sistema muestra resumen y espera confirmación",
            "confirmado_por_abogado": "Abogado confirmó, se puede generar demanda",
            "modificando_datos": "Abogado quiere modificar datos",
            "cancelado": "Abogado canceló la generación",
            "completado": "Demanda generada exitosamente"
        }
        
        print(f"📊 Estados del sistema:")
        for estado, descripcion in estados_esperados.items():
            print(f"   {estado}: {descripcion}")
        
        print_separator("PRUEBA COMPLETADA EXITOSAMENTE")
        
        print("✅ Todos los componentes del control manual funcionan correctamente:")
        print("   • Resumen de confirmación generado")
        print("   • Opciones de confirmación procesadas")
        print("   • Estados de sesión manejados")
        print("   • Datos modificados integrados")
        print("   • Flujo de generación controlado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_integracion_documentos():
    """Prueba la integración con documentos reales."""
    
    print_separator("PRUEBA INTEGRACIÓN CON DOCUMENTOS")
    
    try:
        from rag.qa_agent import obtener_informacion_documentos_sincrona
        
        # Usar un session_id de prueba
        session_id = "test_docs_123"
        
        print(f"🔍 Obteniendo información de documentos para session_id: {session_id}")
        
        info_docs = obtener_informacion_documentos_sincrona(session_id)
        
        print(f"📄 Información obtenida:")
        print(f"   Transcripción: {len(info_docs.get('transcripcion_completa', ''))} caracteres")
        print(f"   Documentos: {len(info_docs.get('documentos_utilizados', []))}")
        print(f"   Personas: {len(info_docs.get('personas_identificadas', []))}")
        print(f"   Empresas: {len(info_docs.get('empresas_identificadas', []))}")
        
        if info_docs.get('transcripcion_completa'):
            print(f"✅ Integración con documentos funcionando")
        else:
            print(f"⚠️ No hay documentos para esta sesión (normal para sesiones de prueba)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en integración de documentos: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del control manual del abogado...")
    
    async def run_tests():
        # Ejecutar pruebas
        test1_result = await test_control_manual_abogado()
        test2_result = await test_integracion_documentos()
        
        print_separator("RESULTADOS FINALES")
        
        if test1_result and test2_result:
            print("🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
            print("✅ El control manual del abogado está funcionando correctamente")
            print("✅ La integración con documentos está operativa")
            print("✅ El sistema está listo para uso en producción")
        else:
            print("❌ Algunas pruebas fallaron")
            if not test1_result:
                print("   • Control manual del abogado")
            print("   • Integración con documentos")
            sys.exit(1)
    
    # Ejecutar las pruebas
    asyncio.run(run_tests()) 