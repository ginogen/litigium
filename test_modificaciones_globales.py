#!/usr/bin/env python3
"""
Script de prueba para el sistema de modificaciones globales.
Simula modificaciones globales sin usar Supabase.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from rag.editor_demandas import (
    aplicar_edicion_global_inteligente, 
    _aplicar_patrones_globales_rapidos,
    _aplicar_edicion_global_con_ia
)

def test_patrones_globales_basicos():
    """Prueba patrones globales básicos."""
    print("🧪 PRUEBA 1: Patrones Globales Básicos")
    print("=" * 60)
    
    # Documento de prueba
    documento_test = """
    DEMANDA LABORAL
    
    I. HECHOS:
    
    1. El trabajador Gino Gentile prestó servicios para ARCOR S.A. desde el 15 de marzo de 2020.
    
    2. Durante su relación laboral con ARCOR S.A., Gino Gentile desempeñó tareas como operario.
    
    3. El día 10/12/2023, ARCOR S.A. despidió al trabajador sin justa causa.
    
    II. DERECHO:
    
    El despido de Gino Gentile por parte de ARCOR S.A. configura un despido sin justa causa.
    
    III. PETITORIO:
    
    Se solicita que se condene a ARCOR S.A. al pago de la indemnización correspondiente.
    """
    
    # Prueba 1: Cambio de nombre
    print("\n📝 Prueba 1A: Cambio de nombre")
    instruccion1 = "cambiar Gino Gentile por Gino Gustavo Gentile"
    resultado1 = _aplicar_patrones_globales_rapidos(documento_test, instruccion1)
    
    if "Gino Gustavo Gentile" in resultado1 and "Gino Gentile" not in resultado1.replace("Gino Gustavo Gentile", ""):
        print("✅ ÉXITO: Nombre cambiado correctamente")
    else:
        print("❌ FALLO: Nombre no se cambió correctamente")
    
    # Prueba 2: Cambio de empresa
    print("\n📝 Prueba 1B: Cambio de empresa")
    instruccion2 = "cambiar ARCOR S.A. por MICROSOFT CORP"
    resultado2 = _aplicar_patrones_globales_rapidos(documento_test, instruccion2)
    
    if "MICROSOFT CORP" in resultado2 and "ARCOR S.A." not in resultado2:
        print("✅ ÉXITO: Empresa cambiada correctamente")
    else:
        print("❌ FALLO: Empresa no se cambió correctamente")
    
    # Prueba 3: Cambio de fechas
    print("\n📝 Prueba 1C: Cambio de fechas")
    instruccion3 = "cambiar todas las fechas por 20/01/2024"
    resultado3 = _aplicar_patrones_globales_rapidos(documento_test, instruccion3)
    
    if "20/01/2024" in resultado3 and ("15/03/2020" not in resultado3 and "10/12/2023" not in resultado3):
        print("✅ ÉXITO: Fechas cambiadas correctamente")
    else:
        print("❌ FALLO: Fechas no se cambiaron correctamente")
    
    print("\n" + "=" * 60)

def test_comando_agregar_nombre():
    """Prueba el comando de agregar al nombre."""
    print("🧪 PRUEBA 2: Agregar al Nombre")
    print("=" * 60)
    
    documento_test = """
    El trabajador Gino Gentile prestó servicios para la empresa.
    Posteriormente, Gino Gentile fue despedido injustamente.
    """
    
    instruccion = "agregar Gustavo al nombre"
    resultado = _aplicar_patrones_globales_rapidos(documento_test, instruccion)
    
    if "Gino Gustavo Gentile" in resultado:
        print("✅ ÉXITO: Segundo nombre agregado correctamente")
        print(f"📄 Resultado: {resultado}")
    else:
        print("❌ FALLO: Segundo nombre no se agregó")
        print(f"📄 Resultado: {resultado}")
    
    print("\n" + "=" * 60)

def test_comando_empresa():
    """Prueba el comando de cambio de empresa."""
    print("🧪 PRUEBA 3: Comando de Empresa")
    print("=" * 60)
    
    documento_test = """
    La empresa demandada COCA-COLA S.A. despidió al trabajador.
    Durante el tiempo que trabajó para COCA-COLA S.A., el empleado cumplió correctamente.
    """
    
    instruccion = "la empresa es PEPSI CORPORATION"
    resultado = _aplicar_patrones_globales_rapidos(documento_test, instruccion)
    
    if "PEPSI CORPORATION" in resultado and "COCA-COLA S.A." not in resultado:
        print("✅ ÉXITO: Empresa cambiada con comando 'la empresa es'")
        print(f"📄 Resultado: {resultado}")
    else:
        print("❌ FALLO: Empresa no se cambió con comando 'la empresa es'")
        print(f"📄 Resultado: {resultado}")
    
    print("\n" + "=" * 60)

def test_edicion_global_completa():
    """Prueba la función completa de edición global."""
    print("🧪 PRUEBA 4: Edición Global Completa")
    print("=" * 60)
    
    documento_test = """
    DEMANDA LABORAL
    
    El trabajador Pedro Martinez prestó servicios para IBM ARGENTINA S.A.
    desde el 01/01/2021 hasta su despido el 31/12/2023.
    
    Se solicita que IBM ARGENTINA S.A. pague las indemnizaciones correspondientes.
    """
    
    # Prueba con la función completa (sin IA por ahora)
    instrucciones = [
        "cambiar Pedro Martinez por Carlos Rodriguez",
        "reemplazar IBM ARGENTINA S.A. por GOOGLE ARGENTINA",
        "cambiar 01/01/2021 por 15/06/2022"
    ]
    
    for i, instruccion in enumerate(instrucciones, 1):
        print(f"\n📝 Ejecutando instrucción {i}: {instruccion}")
        resultado = aplicar_edicion_global_inteligente(documento_test, instruccion)
        
        if resultado != documento_test:
            print("✅ CAMBIO DETECTADO")
            documento_test = resultado  # Aplicar cambio para siguiente prueba
        else:
            print("❌ NO HAY CAMBIOS")
    
    print(f"\n📄 DOCUMENTO FINAL:\n{documento_test}")
    print("\n" + "=" * 60)

def main():
    """Función principal de pruebas."""
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA DE MODIFICACIONES GLOBALES")
    print("=" * 80)
    
    # Configurar variables de entorno de prueba
    os.environ['USAR_IA_PARA_EDICION'] = 'false'  # Desactivar IA para pruebas
    
    try:
        test_patrones_globales_basicos()
        test_comando_agregar_nombre()
        test_comando_empresa()
        test_edicion_global_completa()
        
        print("🎉 TODAS LAS PRUEBAS COMPLETADAS")
        print("💡 Para probar con IA, configura OPENAI_API_KEY y ejecuta desde la interfaz web")
        
    except Exception as e:
        print(f"❌ ERROR EN PRUEBAS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 