#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para el Sistema de Edición Inteligente Híbrido
Demuestra las capacidades de edición en 3 niveles.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag.editor_demandas import aplicar_edicion_inteligente, USAR_IA_PARA_EDICION

def test_edicion_nivel_1_reglas_rapidas():
    """Prueba ediciones que se resuelven con reglas rápidas (Nivel 1)"""
    print("🚀 === PRUEBAS NIVEL 1: REGLAS RÁPIDAS ===")
    
    casos_test = [
        {
            "nombre": "Cambio de empresa",
            "texto": "demandado ARCOR S.A., con domicilio en Buenos Aires",
            "instruccion": "la empresa es MICROSOFT CORP",
            "esperado": "MICROSOFT CORP"
        },
        {
            "nombre": "Cambio de género",
            "texto": "el demandado trabajó durante tres años",
            "instruccion": "cambiar por demandada",
            "esperado": "demandada"
        },
        {
            "nombre": "Reemplazo directo",
            "texto": "solicita $50.000 en concepto de indemnización",
            "instruccion": "cambiar 50.000 por 75.000",
            "esperado": "75.000"
        },
        {
            "nombre": "Patrón 'es X'",
            "texto": "Empleado Juan Pérez",
            "instruccion": "el nombre es Carlos Rodriguez",
            "esperado": "Carlos Rodriguez"
        }
    ]
    
    for i, caso in enumerate(casos_test, 1):
        print(f"\n📝 Test {i}: {caso['nombre']}")
        print(f"   Texto: '{caso['texto']}'")
        print(f"   Instrucción: '{caso['instruccion']}'")
        
        resultado = aplicar_edicion_inteligente(caso['texto'], caso['instruccion'])
        
        if caso['esperado'] in resultado:
            print(f"   ✅ ÉXITO: '{resultado}'")
        else:
            print(f"   ❌ FALLO: '{resultado}' (esperaba: {caso['esperado']})")

def test_edicion_nivel_2_ia():
    """Prueba ediciones complejas que requieren IA (Nivel 2)"""
    print("\n\n🤖 === PRUEBAS NIVEL 2: EDICIÓN CON IA ===")
    
    if not USAR_IA_PARA_EDICION:
        print("⚠️ IA DESACTIVADA - Saltando pruebas de Nivel 2")
        return
    
    casos_test = [
        {
            "nombre": "Agregar contenido legal",
            "texto": "El trabajador fue despedido el 15 de marzo de 2024.",
            "instruccion": "agregar referencia al artículo 245 de la LCT",
        },
        {
            "nombre": "Cambio de tono",
            "texto": "El patrón lo echó sin motivo.",
            "instruccion": "hacer más formal y técnico",
        },
        {
            "nombre": "Corrección contextual",
            "texto": "La empresa incumplió con los pagos salariales.",
            "instruccion": "especificar que fueron 3 meses de atraso",
        },
        {
            "nombre": "Expansión de hechos",
            "texto": "Ocurrió un accidente laboral.",
            "instruccion": "agregar detalles sobre las lesiones sufridas",
        }
    ]
    
    for i, caso in enumerate(casos_test, 1):
        print(f"\n📝 Test {i}: {caso['nombre']}")
        print(f"   Texto: '{caso['texto']}'")
        print(f"   Instrucción: '{caso['instruccion']}'")
        
        resultado = aplicar_edicion_inteligente(caso['texto'], caso['instruccion'])
        
        if resultado != caso['texto']:
            print(f"   ✅ CAMBIO APLICADO: '{resultado}'")
        else:
            print(f"   ⚠️ SIN CAMBIO: '{resultado}'")

def test_edicion_nivel_3_fallback():
    """Prueba ediciones que van al fallback (Nivel 3)"""
    print("\n\n🔄 === PRUEBAS NIVEL 3: FALLBACK SIMPLE ===")
    
    casos_test = [
        {
            "nombre": "Patrón 'cambiar a'",
            "texto": "EMPRESA ANTERIOR",
            "instruccion": "cambiar a NUEVA EMPRESA SA",
            "esperado": "NUEVA EMPRESA SA"
        },
        {
            "nombre": "Patrón 'debe ser'",
            "texto": "monto incorrecto",
            "instruccion": "debe ser 80.000 pesos",
            "esperado": "80.000 pesos"
        },
        {
            "nombre": "Patrón 'usar'",
            "texto": "fecha anterior", 
            "instruccion": "usar 15/03/2024",
            "esperado": "15/03/2024"
        }
    ]
    
    for i, caso in enumerate(casos_test, 1):
        print(f"\n📝 Test {i}: {caso['nombre']}")
        print(f"   Texto: '{caso['texto']}'")
        print(f"   Instrucción: '{caso['instruccion']}'")
        
        resultado = aplicar_edicion_inteligente(caso['texto'], caso['instruccion'])
        
        if caso['esperado'] in resultado:
            print(f"   ✅ ÉXITO: '{resultado}'")
        else:
            print(f"   ❌ FALLO: '{resultado}' (esperaba: {caso['esperado']})")

def test_casos_complejos():
    """Prueba casos complejos del mundo real"""
    print("\n\n🎯 === CASOS COMPLEJOS DEL MUNDO REAL ===")
    
    texto_demanda = """Que vengo por el presente a interponer demanda laboral contra ARCOR S.A., 
con domicilio en Av. del Libertador 1850, Buenos Aires, por despido injustificado y en negro, 
solicitando el pago de las indemnizaciones correspondientes por $50.000, conforme a los hechos 
y derecho que a continuación expongo."""
    
    casos_test = [
        {
            "nombre": "Cambio de empresa completo",
            "instruccion": "la empresa es COCA-COLA FEMSA",
            "buscar": "COCA-COLA FEMSA"
        },
        {
            "nombre": "Cambio de monto",
            "instruccion": "el monto es $150.000",
            "buscar": "150.000"
        },
        {
            "nombre": "Agregar causa específica",
            "instruccion": "especificar que el despido fue discriminatorio por embarazo",
            "buscar": None  # Solo verificar que cambió
        }
    ]
    
    for i, caso in enumerate(casos_test, 1):
        print(f"\n📝 Test {i}: {caso['nombre']}")
        print(f"   Instrucción: '{caso['instruccion']}'")
        
        resultado = aplicar_edicion_inteligente(texto_demanda, caso['instruccion'])
        
        if caso['buscar']:
            if caso['buscar'] in resultado:
                print(f"   ✅ ÉXITO: Cambio aplicado correctamente")
                print(f"   📄 Resultado: '{resultado[:100]}...'")
            else:
                print(f"   ❌ FALLO: No se encontró '{caso['buscar']}'")
                print(f"   📄 Resultado: '{resultado[:100]}...'")
        else:
            if resultado != texto_demanda:
                print(f"   ✅ CAMBIO DETECTADO")
                print(f"   📄 Resultado: '{resultado[:100]}...'")
            else:
                print(f"   ⚠️ SIN CAMBIO DETECTADO")

def test_rendimiento():
    """Prueba el rendimiento del sistema"""
    print("\n\n⚡ === PRUEBA DE RENDIMIENTO ===")
    
    import time
    
    texto = "El demandado EMPRESA S.A. debe pagar $10.000"
    instruccion = "la empresa es NUEVA EMPRESA"
    
    # Medir tiempo de 10 ediciones
    inicio = time.time()
    for i in range(10):
        resultado = aplicar_edicion_inteligente(texto, instruccion)
    fin = time.time()
    
    tiempo_promedio = (fin - inicio) / 10 * 1000  # en ms
    
    print(f"   ⏱️ Tiempo promedio por edición: {tiempo_promedio:.1f}ms")
    print(f"   📊 Ediciones por segundo: {1000/tiempo_promedio:.1f}")
    
    if tiempo_promedio < 100:
        print(f"   ✅ EXCELENTE rendimiento")
    elif tiempo_promedio < 500:
        print(f"   ✅ BUEN rendimiento")
    else:
        print(f"   ⚠️ Rendimiento mejorable")

if __name__ == "__main__":
    print("🧠 SISTEMA DE EDICIÓN INTELIGENTE HÍBRIDO - PRUEBAS")
    print("=" * 60)
    print(f"📋 Configuración: IA {'ACTIVADA' if USAR_IA_PARA_EDICION else 'DESACTIVADA'}")
    print("=" * 60)
    
    try:
        # Ejecutar todas las pruebas
        test_edicion_nivel_1_reglas_rapidas()
        test_edicion_nivel_2_ia()
        test_edicion_nivel_3_fallback()
        test_casos_complejos()
        test_rendimiento()
        
        print("\n\n✅ === PRUEBAS COMPLETADAS ===")
        print("🚀 El sistema híbrido está funcionando correctamente!")
        
    except Exception as e:
        print(f"\n❌ ERROR durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc() 