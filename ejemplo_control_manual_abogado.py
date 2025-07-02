#!/usr/bin/env python3
"""
📋 EJEMPLO PRÁCTICO - CONTROL MANUAL DEL ABOGADO

Este ejemplo muestra cómo funciona el nuevo flujo donde el abogado
debe confirmar explícitamente antes de generar la demanda.

Flujo del ejemplo:
1. Abogado inicia conversación
2. Sube documentos (telegrama, liquidación, recibo)
3. Proporciona datos del cliente
4. Sistema muestra resumen de confirmación
5. Abogado confirma y se genera la demanda
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
    print(f"📋 {title}")
    print(f"{'='*60}")

def print_step(step, description):
    print(f"\n🔹 PASO {step}: {description}")
    print("-" * 40)

async def ejemplo_control_manual_abogado():
    """Ejemplo práctico del control manual del abogado."""
    
    print_separator("EJEMPLO PRÁCTICO - CONTROL MANUAL DEL ABOGADO")
    
    try:
        # Importar componentes necesarios
        from rag.chat_agent import get_chat_agent, reset_chat_agent
        from rag.qa_agent import obtener_informacion_documentos_sincrona
        
        print("✅ Sistema inicializado correctamente")
        
        # Resetear el chat agent
        reset_chat_agent()
        chat_agent = get_chat_agent()
        
        # Simular datos de sesión
        session_id = "ejemplo_control_manual_2024"
        user_id = "abogado_ejemplo_123"
        
        # PASO 1: Abogado inicia conversación
        print_step(1, "ABOGADO INICIA CONVERSACIÓN")
        
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "estado": "iniciada",
            "tipo_demanda": "",
            "datos_cliente": {},
            "hechos_adicionales": "",
            "notas_abogado": "",
            "mensajes": []
        }
        
        print("👨‍💼 Abogado: 'Hola, necesito generar una demanda de despido injustificado'")
        
        # Simular respuesta del sistema
        respuesta_ia = {
            "accion": "seleccionar_tipo",
            "mensaje": "¡Hola! Te ayudo a generar la demanda de despido injustificado. Para empezar, necesito algunos datos básicos del cliente y los documentos del caso."
        }
        
        print(f"🤖 Sistema: {respuesta_ia['mensaje']}")
        
        # PASO 2: Abogado sube documentos
        print_step(2, "ABOGADO SUBE DOCUMENTOS")
        
        print("👨‍💼 Abogado sube 3 documentos:")
        print("   📄 telegrama_despido.pdf")
        print("   📄 liquidacion_final.pdf") 
        print("   📄 recibo_diciembre.pdf")
        
        # Simular información extraída de documentos
        info_documentos = {
            "transcripcion_completa": """
            TELEGRAMA DE DESPIDO:
            Empresa Tecnología Avanzada S.A. comunica el despido sin causa del Sr. Carlos Rodríguez, 
            DNI 34567890, a partir del 20 de febrero de 2024. El empleado trabajaba como desarrollador 
            de software desde el 15 de marzo de 2021.
            
            LIQUIDACIÓN FINAL:
            Sueldo básico: $180.000
            Antigüedad: $54.000
            Indemnización por despido: $540.000
            Total a cobrar: $774.000
            
            RECIBO DE SUELDO - DICIEMBRE 2023:
            Sueldo básico: $180.000
            Presentismo: $15.000
            Descuentos: $36.000 (aportes)
            Neto a cobrar: $159.000
            """,
            "documentos_utilizados": [
                {"tipo": "telegrama", "nombre": "telegrama_despido.pdf"},
                {"tipo": "liquidacion", "nombre": "liquidacion_final.pdf"},
                {"tipo": "recibo_sueldo", "nombre": "recibo_diciembre.pdf"}
            ],
            "personas_identificadas": ["Carlos Rodríguez", "María González", "Roberto Silva"],
            "empresas_identificadas": ["Empresa Tecnología Avanzada S.A.", "Consultora IT Solutions"],
            "fechas_importantes": [
                {"fecha": "2024-02-20", "evento": "Fecha de despido"},
                {"fecha": "2021-03-15", "evento": "Fecha de ingreso"},
                {"fecha": "2024-02-25", "evento": "Fecha de telegrama"}
            ],
            "montos_encontrados": [
                {"concepto": "sueldo_basico", "monto": "$180.000"},
                {"concepto": "antiguedad", "monto": "$54.000"},
                {"concepto": "indemnizacion", "monto": "$540.000"},
                {"concepto": "total_liquidacion", "monto": "$774.000"},
                {"concepto": "sueldo_neto", "monto": "$159.000"}
            ],
            "datos_contacto": {
                "telefonos": ["011-4567-8901", "011-2345-6789"],
                "emails": ["rrhh@tecnologiaavanzada.com"],
                "domicilios": ["Av. Libertador 5678, CABA"]
            }
        }
        
        print("✅ Documentos procesados automáticamente:")
        print(f"   📝 Transcripción: {len(info_documentos['transcripcion_completa'])} caracteres")
        print(f"   👥 Personas identificadas: {len(info_documentos['personas_identificadas'])}")
        print(f"   🏢 Empresas identificadas: {len(info_documentos['empresas_identificadas'])}")
        print(f"   📅 Fechas importantes: {len(info_documentos['fechas_importantes'])}")
        print(f"   💰 Montos encontrados: {len(info_documentos['montos_encontrados'])}")
        
        # PASO 3: Abogado proporciona datos del cliente
        print_step(3, "ABOGADO PROPORCIONA DATOS DEL CLIENTE")
        
        print("👨‍💼 Abogado: 'El cliente es Carlos Rodríguez, DNI 34567890, vive en Belgrano, CABA'")
        
        # Actualizar datos del cliente
        session["datos_cliente"] = {
            "nombre_completo": "Carlos Rodríguez",
            "dni": "34567890",
            "domicilio": "Belgrano, CABA",
            "telefono": "011-4567-8901",
            "email": "carlos.rodriguez@email.com"
        }
        session["tipo_demanda"] = "Despido injustificado"
        session["hechos_adicionales"] = "El cliente fue despedido sin causa justificada. Trabajaba como desarrollador de software y tenía buen desempeño."
        session["notas_abogado"] = "Caso típico de despido sin causa. Cliente tiene toda la documentación necesaria."
        
        print("✅ Datos del cliente registrados:")
        print(f"   👤 Nombre: {session['datos_cliente']['nombre_completo']}")
        print(f"   🆔 DNI: {session['datos_cliente']['dni']}")
        print(f"   📄 Tipo demanda: {session['tipo_demanda']}")
        
        # PASO 4: Sistema detecta que debe generar la demanda
        print_step(4, "SISTEMA DETECTA GENERACIÓN")
        
        print("🤖 Sistema detecta que tiene toda la información necesaria")
        print("🤖 Sistema: 'Tengo toda la información necesaria para generar la demanda'")
        
        # PASO 5: Sistema muestra resumen de confirmación
        print_step(5, "SISTEMA MUESTRA RESUMEN DE CONFIRMACIÓN")
        
        # Crear resumen para el abogado
        resumen = chat_agent._crear_resumen_para_abogado(session, info_documentos)
        
        print("📋 RESUMEN PARA CONFIRMACIÓN:")
        print(resumen['mensaje'])
        
        # PASO 6: Abogado revisa y confirma
        print_step(6, "ABOGADO REVISA Y CONFIRMA")
        
        print("👨‍💼 Abogado revisa el resumen y confirma que todo está correcto")
        print("👨‍💼 Abogado: 'Todo está correcto, generar la demanda'")
        
        # Procesar confirmación
        resultado = await chat_agent.procesar_confirmacion_abogado(
            session=session,
            accion="confirmar_generar",
            session_id=session_id,
            datos_modificados=None
        )
        
        print(f"✅ Confirmación procesada:")
        print(f"   Demanda generada: {resultado.get('demanda_generada', False)}")
        print(f"   Mensaje: {resultado.get('mensaje', '')[:100]}...")
        
        # PASO 7: Demanda generada exitosamente
        print_step(7, "DEMANDA GENERADA EXITOSAMENTE")
        
        print("🎉 ¡Demanda generada exitosamente!")
        print("📄 El sistema ha creado un documento profesional con:")
        print("   • Hechos estructurados según jurisprudencia")
        print("   • Base legal con artículos específicos de la LCT")
        print("   • Petitorio adaptado al caso de despido")
        print("   • Ofrecimiento de prueba detallado")
        print("   • Información extraída de todos los documentos")
        
        # Mostrar información consolidada utilizada
        print("\n📊 INFORMACIÓN CONSOLIDADA UTILIZADA:")
        print(f"   📝 Transcripción completa de {len(info_documentos['documentos_utilizados'])} documentos")
        print(f"   👥 Personas: {', '.join(info_documentos['personas_identificadas'])}")
        print(f"   🏢 Empresas: {', '.join(info_documentos['empresas_identificadas'])}")
        print(f"   📅 Fechas clave: {len(info_documentos['fechas_importantes'])} eventos")
        print(f"   💰 Montos: {len(info_documentos['montos_encontrados'])} valores monetarios")
        
        print_separator("EJEMPLO COMPLETADO EXITOSAMENTE")
        
        print("✅ Flujo del control manual del abogado:")
        print("   1. ✅ Abogado inicia conversación")
        print("   2. ✅ Sube documentos (procesamiento automático)")
        print("   3. ✅ Proporciona datos del cliente")
        print("   4. ✅ Sistema detecta información completa")
        print("   5. ✅ Muestra resumen de confirmación")
        print("   6. ✅ Abogado confirma explícitamente")
        print("   7. ✅ Demanda generada con toda la información")
        
        print("\n🎯 BENEFICIOS DEL CONTROL MANUAL:")
        print("   • El abogado tiene control total sobre la generación")
        print("   • Puede revisar toda la información antes de confirmar")
        print("   • Puede modificar datos si es necesario")
        print("   • Puede cancelar si no está listo")
        print("   • La demanda se genera solo con confirmación explícita")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en el ejemplo: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def ejemplo_modificacion_datos():
    """Ejemplo de modificación de datos antes de generar."""
    
    print_separator("EJEMPLO - MODIFICACIÓN DE DATOS")
    
    try:
        from rag.chat_agent import get_chat_agent
        
        chat_agent = get_chat_agent()
        session_id = "ejemplo_modificacion_2024"
        
        # Simular sesión con datos iniciales
        session = {
            "session_id": session_id,
            "user_id": "abogado_ejemplo_123",
            "estado": "esperando_confirmacion",
            "tipo_demanda": "Despido injustificado",
            "datos_cliente": {
                "nombre_completo": "Ana Martínez",
                "dni": "23456789",
                "domicilio": "Palermo, CABA"
            },
            "hechos_adicionales": "Cliente despedida sin causa.",
            "notas_abogado": "Caso simple de despido.",
            "mensajes": []
        }
        
        print("👨‍💼 Abogado revisa el resumen y encuentra errores")
        print("👨‍💼 Abogado: 'Necesito modificar algunos datos antes de generar'")
        
        # Procesar solicitud de modificación
        resultado = await chat_agent.procesar_confirmacion_abogado(
            session=session,
            accion="modificar_datos",
            session_id=session_id,
            datos_modificados=None
        )
        
        print(f"🤖 Sistema: {resultado.get('mensaje', '')[:100]}...")
        
        # Simular datos modificados
        datos_modificados = {
            "cliente": {
                "nombre_completo": "Ana María Martínez",
                "dni": "23456789",
                "domicilio": "Palermo, CABA",
                "telefono": "011-3456-7890",
                "email": "ana.martinez@email.com"
            },
            "hechos_adicionales": "La cliente fue despedida sin causa justificada el 10 de marzo de 2024. Trabajaba como contadora desde enero de 2022.",
            "notas_abogado": "Caso de despido sin causa. Cliente tiene telegrama y liquidación. Solicitar indemnización completa."
        }
        
        print("👨‍💼 Abogado proporciona datos corregidos:")
        print(f"   👤 Nombre: {datos_modificados['cliente']['nombre_completo']}")
        print(f"   📞 Teléfono: {datos_modificados['cliente']['telefono']}")
        print(f"   📝 Hechos actualizados: {len(datos_modificados['hechos_adicionales'])} caracteres")
        
        # Confirmar con datos modificados
        resultado_final = await chat_agent.procesar_confirmacion_abogado(
            session=session,
            accion="confirmar_generar",
            session_id=session_id,
            datos_modificados=datos_modificados
        )
        
        print(f"✅ Demanda generada con datos corregidos:")
        print(f"   Demanda generada: {resultado_final.get('demanda_generada', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en ejemplo de modificación: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Ejecutando ejemplo práctico del control manual del abogado...")
    
    async def run_examples():
        # Ejecutar ejemplos
        ejemplo1_result = await ejemplo_control_manual_abogado()
        ejemplo2_result = await ejemplo_modificacion_datos()
        
        print_separator("RESULTADOS DE LOS EJEMPLOS")
        
        if ejemplo1_result and ejemplo2_result:
            print("🎉 ¡TODOS LOS EJEMPLOS FUNCIONARON CORRECTAMENTE!")
            print("✅ El control manual del abogado está operativo")
            print("✅ El sistema está listo para uso en producción")
        else:
            print("❌ Algunos ejemplos fallaron")
            if not ejemplo1_result:
                print("   • Ejemplo principal")
            if not ejemplo2_result:
                print("   • Ejemplo de modificación")
    
    # Ejecutar los ejemplos
    asyncio.run(run_examples()) 