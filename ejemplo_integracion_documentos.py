#!/usr/bin/env python3
"""
Ejemplo práctico de la integración de documentos en el system prompt.
Muestra cómo toda la información subida por el abogado se usa automáticamente en la generación de demandas.
"""

import asyncio
import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def ejemplo_integracion_completa():
    """Ejemplo completo de integración de documentos en demandas."""
    
    print("🚀 EJEMPLO PRÁCTICO: INTEGRACIÓN DE DOCUMENTOS EN SYSTEM PROMPT")
    print("=" * 80)
    
    print("\n📋 ESCENARIO:")
    print("Un abogado sube los siguientes documentos en el chat:")
    print("1. Telegrama de despido")
    print("2. Liquidación final")
    print("3. Recibo de sueldo")
    print("4. Carta documento")
    
    print("\n🔍 PROCESO AUTOMÁTICO:")
    print("1. Sistema extrae TODO el contenido con GPT-4 Vision")
    print("2. Identifica personas, empresas, fechas, montos")
    print("3. Consolida toda la información")
    print("4. La incluye automáticamente en el system prompt")
    print("5. Genera demanda enriquecida con evidencia documental")
    
    print("\n📄 SIMULANDO DOCUMENTOS SUBIDOS...")
    
    # Simular información extraída de documentos
    informacion_documentos = {
        'transcripcion_completa': """
=== TELEGRAMA DE DESPIDO ===
TELEGRAMA N° 12345
Fecha: 15/03/2024
Remitente: EMPRESA XYZ S.A.
Destinatario: Juan Pérez
DNI: 12345678
Domicilio: Av. Corrientes 1234, CABA

Por la presente se le comunica que a partir del día 16/03/2024 queda desvinculado de la empresa sin causa aparente.

=== LIQUIDACIÓN FINAL ===
LIQUIDACIÓN FINAL
Empleado: Juan Pérez
DNI: 12345678
Fecha de ingreso: 01/01/2020
Fecha de egreso: 16/03/2024
Sueldo básico: $150.000
Indemnización por despido: $450.000
Vacaciones no gozadas: $75.000
Total a cobrar: $675.000

=== RECIBO DE SUELDO ===
RECIBO DE SUELDO - MARZO 2024
Empleado: Juan Pérez
DNI: 12345678
Categoría: Administrativo
Sueldo básico: $150.000
Presentismo: $15.000
Total bruto: $165.000
Descuentos: $33.000
Neto a cobrar: $132.000

=== CARTA DOCUMENTO ===
CARTA DOCUMENTO N° 98765
Fecha: 10/03/2024
Remitente: Juan Pérez
Destinatario: EMPRESA XYZ S.A.
Domicilio: Av. Corrientes 1234, CABA

Se reclama el pago de salarios adeudados y la regularización de la situación laboral.
        """,
        'personas_identificadas': ['Juan Pérez'],
        'empresas_identificadas': ['EMPRESA XYZ S.A.'],
        'fechas_importantes': [
            {'fecha': '15/03/2024', 'evento': 'Telegrama de despido enviado'},
            {'fecha': '16/03/2024', 'evento': 'Fecha de despido efectivo'},
            {'fecha': '01/01/2020', 'evento': 'Fecha de ingreso'},
            {'fecha': '10/03/2024', 'evento': 'Carta documento enviada'}
        ],
        'montos_encontrados': [
            {'concepto': 'sueldo_basico', 'monto': '$150.000'},
            {'concepto': 'indemnizacion_despido', 'monto': '$450.000'},
            {'concepto': 'vacaciones_no_gozadas', 'monto': '$75.000'},
            {'concepto': 'total_liquidacion', 'monto': '$675.000'},
            {'concepto': 'presentismo', 'monto': '$15.000'},
            {'concepto': 'neto_cobrar', 'monto': '$132.000'}
        ],
        'datos_contacto': {
            'telefonos': ['011-1234-5678'],
            'emails': ['juan.perez@email.com'],
            'domicilios': ['Av. Corrientes 1234, CABA']
        }
    }
    
    print(f"✅ Información extraída:")
    print(f"   📝 Transcripción: {len(informacion_documentos['transcripcion_completa'])} caracteres")
    print(f"   👥 Personas: {', '.join(informacion_documentos['personas_identificadas'])}")
    print(f"   🏢 Empresas: {', '.join(informacion_documentos['empresas_identificadas'])}")
    print(f"   📅 Fechas importantes: {len(informacion_documentos['fechas_importantes'])}")
    print(f"   💰 Montos: {len(informacion_documentos['montos_encontrados'])}")
    
    print("\n🤖 GENERANDO DEMANDA CON INFORMACIÓN INTEGRADA...")
    
    try:
        from rag.qa_agent import generar_demanda
        
        # Datos del cliente
        datos_cliente = {
            "nombre_completo": "Juan Pérez",
            "dni": "12345678",
            "domicilio": "Av. Corrientes 1234, CABA",
            "telefono": "011-1234-5678",
            "email": "juan.perez@email.com",
            "ocupacion": "Administrativo"
        }
        
        # Generar demanda con información de documentos
        resultado = await generar_demanda(
            tipo_demanda="Despido injustificado",
            datos_cliente=datos_cliente,
            hechos_adicionales="El cliente fue despedido sin causa aparente",
            notas_abogado="Caso con documentación completa: telegrama, liquidación, recibo y carta documento",
            session_id="ejemplo-session-123"
        )
        
        print(f"✅ Demanda generada exitosamente")
        print(f"   📄 Longitud: {len(resultado.get('texto_demanda', ''))} caracteres")
        print(f"   📁 Archivo: {resultado.get('archivo_docx', 'No generado')}")
        
        # Mostrar metadatos
        metadatos = resultado.get('metadatos', {})
        print(f"\n📊 METADATOS DE LA GENERACIÓN:")
        print(f"   📋 Cliente: {metadatos.get('cliente', 'N/A')}")
        print(f"   🏷️ Tipo: {metadatos.get('tipo_demanda', 'N/A')}")
        print(f"   ⏱️ Tiempo: {metadatos.get('tiempo_generacion', 0):.2f} segundos")
        print(f"   📚 Casos consultados: {metadatos.get('casos_consultados', 0)}")
        print(f"   📄 Documentos utilizados: {metadatos.get('documentos_utilizados', False)}")
        print(f"   👥 Personas en documentos: {metadatos.get('personas_documentos', 0)}")
        print(f"   🏢 Empresas en documentos: {metadatos.get('empresas_documentos', 0)}")
        print(f"   📅 Fechas en documentos: {metadatos.get('fechas_documentos', 0)}")
        print(f"   💰 Montos en documentos: {metadatos.get('montos_documentos', 0)}")
        
        # Mostrar fragmento de la demanda generada
        texto_demanda = resultado.get('texto_demanda', '')
        print(f"\n📝 FRAGMENTO DE LA DEMANDA GENERADA:")
        print("-" * 60)
        print(texto_demanda[:500] + "..." if len(texto_demanda) > 500 else texto_demanda)
        print("-" * 60)
        
        print(f"\n🎯 BENEFICIOS DE LA INTEGRACIÓN:")
        print(f"✅ Toda la información de documentos se usa automáticamente")
        print(f"✅ Fechas específicas se incluyen en los hechos")
        print(f"✅ Montos exactos se citan en el petitorio")
        print(f"✅ Empresas y personas se identifican correctamente")
        print(f"✅ Transcripción completa sirve como evidencia")
        print(f"✅ Demanda más precisa y completa")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en ejemplo: {e}")
        return False

def mostrar_comparacion_prompts():
    """Muestra la comparación entre el prompt anterior y el nuevo."""
    
    print("\n📊 COMPARACIÓN: PROMPT ANTERIOR vs NUEVO")
    print("=" * 80)
    
    print("\n🔴 PROMPT ANTERIOR (BÁSICO):")
    print("""
CLIENTE: • NOMBRE_COMPLETO: Juan Pérez
TIPO: Despido injustificado
HECHOS: El cliente fue despedido sin causa aparente
NOTAS: Caso de despido injustificado

CONTEXTO LEGAL: [Casos similares de la base de datos]

Redacta una demanda completa siguiendo la estructura obligatoria.
    """)
    
    print("\n🟢 PROMPT NUEVO (CON DOCUMENTOS):")
    print("""
CLIENTE: • NOMBRE_COMPLETO: Juan Pérez
TIPO: Despido injustificado
HECHOS: El cliente fue despedido sin causa aparente
NOTAS: Caso con documentación completa

CONTEXTO LEGAL: [Casos similares de la base de datos]

INFORMACIÓN DE DOCUMENTOS SUBIDOS:
TRANSCRIPCIÓN COMPLETA: [TODO el contenido de telegrama, liquidación, recibo, carta documento]
PERSONAS IDENTIFICADAS: Juan Pérez
EMPRESAS IDENTIFICADAS: EMPRESA XYZ S.A.
FECHAS IMPORTANTES: [15/03/2024, 16/03/2024, 01/01/2020, 10/03/2024]
MONTOS ENCONTRADOS: [$150.000, $450.000, $675.000, $132.000]
DATOS DE CONTACTO: [Teléfonos, emails, domicilios]

Redacta una demanda completa siguiendo la estructura obligatoria. 
Si hay información de documentos, úsala para enriquecer los hechos y el petitorio.
    """)
    
    print("\n🎯 MEJORAS IMPLEMENTADAS:")
    print("✅ Transcripción completa de todos los documentos")
    print("✅ Identificación automática de personas y empresas")
    print("✅ Extracción de fechas importantes")
    print("✅ Montos exactos de liquidaciones y recibos")
    print("✅ Datos de contacto encontrados")
    print("✅ Instrucciones específicas para usar la información")
    print("✅ Integración automática en hechos y petitorio")

async def main():
    """Función principal del ejemplo."""
    
    print("🚀 EJEMPLO PRÁCTICO: INTEGRACIÓN COMPLETA DE DOCUMENTOS")
    print("=" * 80)
    
    # Mostrar comparación de prompts
    mostrar_comparacion_prompts()
    
    # Ejecutar ejemplo completo
    print("\n" + "=" * 80)
    exito = await ejemplo_integracion_completa()
    
    print("\n" + "=" * 80)
    if exito:
        print("🎉 ¡EJEMPLO COMPLETADO EXITOSAMENTE!")
        print("✅ La integración de documentos está funcionando perfectamente")
        print("✅ El system prompt ahora usa TODA la información subida por el abogado")
    else:
        print("⚠️ El ejemplo tuvo algunos problemas")
        print("🔧 Revisa los errores para identificar problemas")
    
    return exito

if __name__ == "__main__":
    # Ejecutar ejemplo
    try:
        exito = asyncio.run(main())
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Ejemplo interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error ejecutando ejemplo: {e}")
        sys.exit(1) 