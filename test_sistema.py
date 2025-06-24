#!/usr/bin/env python3
"""
Script de prueba para el Sistema Legal AI
Verifica que todas las funcionalidades estén operativas
"""

import asyncio
import os
import requests
import json
from pathlib import Path

def verificar_archivos():
    """Verifica que todos los archivos necesarios existan."""
    archivos_requeridos = [
        "main.py",
        "config.py", 
        "requirements.txt",
        "rag/qa_agent.py",
        "rag/audio_service.py",
        "templates/chat.html",
        "templates/preview_demanda.html",
        "ingestion/upload_to_qdrant.py",
        "data/casos_anteriores/ejemplo_despido_discriminatorio.json",
        "data/casos_anteriores/ejemplo_accidente_laboral.json"
    ]
    
    print("🔍 Verificando archivos del sistema...")
    archivos_faltantes = []
    
    for archivo in archivos_requeridos:
        if not Path(archivo).exists():
            archivos_faltantes.append(archivo)
        else:
            print(f"✅ {archivo}")
    
    if archivos_faltantes:
        print("\n❌ Archivos faltantes:")
        for archivo in archivos_faltantes:
            print(f"   - {archivo}")
        return False
    
    print("\n✅ Todos los archivos necesarios están presentes")
    return True

def verificar_dependencias():
    """Verifica que las dependencias estén instaladas."""
    print("\n🔍 Verificando dependencias...")
    
    dependencias = [
        "fastapi",
        "uvicorn", 
        "openai",
        "langchain",
        "qdrant_client",
        "python_docx",
        "pydub"
    ]
    
    dependencias_faltantes = []
    
    for dep in dependencias:
        try:
            __import__(dep.replace("-", "_"))
            print(f"✅ {dep}")
        except ImportError:
            dependencias_faltantes.append(dep)
            print(f"❌ {dep}")
    
    if dependencias_faltantes:
        print(f"\n❌ Instala las dependencias faltantes:")
        print(f"pip install {' '.join(dependencias_faltantes)}")
        return False
    
    print("\n✅ Todas las dependencias están instaladas")
    return True

def verificar_variables_entorno():
    """Verifica las variables de entorno necesarias."""
    print("\n🔍 Verificando variables de entorno...")
    
    variables_requeridas = [
        "OPENAI_API_KEY",
        "QDRANT_URL"
    ]
    
    variables_faltantes = []
    
    for var in variables_requeridas:
        if not os.getenv(var):
            variables_faltantes.append(var)
            print(f"❌ {var}")
        else:
            print(f"✅ {var}")
    
    if variables_faltantes:
        print(f"\n❌ Configura las variables de entorno faltantes en el archivo .env:")
        for var in variables_faltantes:
            print(f"   {var}=tu_valor_aqui")
        return False
    
    print("\n✅ Variables de entorno configuradas")
    return True

def test_importaciones():
    """Prueba las importaciones del sistema."""
    print("\n🔍 Probando importaciones...")
    
    try:
        from config import validar_configuracion
        print("✅ config.py importado correctamente")
        
        from rag.qa_agent import generar_demanda
        print("✅ rag.qa_agent importado correctamente")
        
        from rag.audio_service import get_audio_service
        print("✅ rag.audio_service importado correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en importaciones: {e}")
        return False

def test_configuracion():
    """Prueba la validación de configuración."""
    print("\n🔍 Probando configuración...")
    
    try:
        from config import validar_configuracion
        validar_configuracion()
        print("✅ Configuración válida")
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False

def mostrar_instrucciones():
    """Muestra instrucciones para usar el sistema."""
    print("\n" + "="*60)
    print("🚀 SISTEMA LEGAL AI - INSTRUCCIONES DE USO")
    print("="*60)
    
    print("\n1️⃣ CONFIGURAR VARIABLES DE ENTORNO:")
    print("   Crea un archivo .env con:")
    print("   OPENAI_API_KEY=tu_api_key_de_openai")
    print("   QDRANT_URL=tu_url_de_qdrant")
    print("   QDRANT_API_KEY=tu_api_key_de_qdrant")
    
    print("\n2️⃣ INSTALAR DEPENDENCIAS:")
    print("   pip install -r requirements.txt")
    
    print("\n3️⃣ CARGAR DATOS DE EJEMPLO:")
    print("   python ingestion/upload_to_qdrant.py")
    
    print("\n4️⃣ INICIAR SERVIDOR:")
    print("   python main.py")
    print("   O: uvicorn main:app --reload")
    
    print("\n5️⃣ ACCEDER AL SISTEMA:")
    print("   http://localhost:8000")
    
    print("\n🎯 FUNCIONALIDADES DISPONIBLES:")
    print("   • 💬 Chat inteligente para recopilar información")
    print("   • 🎤 Transcripción de audio con Whisper AI")
    print("   • 📄 Vista previa y edición de demandas")
    print("   • 📥 Descarga de documentos Word")
    print("   • 🔄 Regeneración automática con IA")
    
    print("\n📱 FLUJO DE USO:")
    print("   1. Hacer clic en 'Comenzar Nueva Demanda'")
    print("   2. Seleccionar tipo de demanda")
    print("   3. Proporcionar datos del cliente (texto o audio)")
    print("   4. Describir hechos del caso")
    print("   5. Agregar notas adicionales")
    print("   6. Ver vista previa y editar si es necesario")
    print("   7. Descargar demanda en formato Word")

def main():
    """Función principal de prueba."""
    print("🏛️ SISTEMA LEGAL AI - VERIFICACIÓN DE INSTALACIÓN")
    print("=" * 60)
    
    todas_las_pruebas_pasaron = True
    
    # Verificar archivos
    if not verificar_archivos():
        todas_las_pruebas_pasaron = False
    
    # Verificar dependencias
    if not verificar_dependencias():
        todas_las_pruebas_pasaron = False
    
    # Verificar variables de entorno
    if not verificar_variables_entorno():
        todas_las_pruebas_pasaron = False
    
    # Test importaciones
    if not test_importaciones():
        todas_las_pruebas_pasaron = False
    
    # Test configuración
    if not test_configuracion():
        todas_las_pruebas_pasaron = False
    
    print("\n" + "="*60)
    
    if todas_las_pruebas_pasaron:
        print("🎉 ¡SISTEMA LISTO PARA USAR!")
        print("✅ Todas las verificaciones pasaron correctamente")
        mostrar_instrucciones()
    else:
        print("❌ CONFIGURACIÓN INCOMPLETA")
        print("   Corrige los errores anteriores antes de continuar")
        print("\n💡 Revisa el README.md para instrucciones detalladas")

if __name__ == "__main__":
    main() 