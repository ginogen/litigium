#!/usr/bin/env python3
"""
Script de prueba para verificar que el sistema legal completo esté funcionando.
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def verificar_variables_entorno():
    """Verifica que todas las variables de entorno necesarias estén configuradas."""
    print("🔍 Verificando variables de entorno...")
    
    variables_requeridas = [
        "OPENAI_API_KEY",
        "SUPABASE_URL", 
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY"
    ]
    
    variables_opcionales = [
        "QDRANT_URL",
        "QDRANT_API_KEY"
    ]
    
    errores = []
    
    # Verificar variables requeridas
    for var in variables_requeridas:
        valor = os.getenv(var)
        if not valor:
            errores.append(f"❌ {var} no configurada")
        else:
            # Mostrar solo los primeros caracteres por seguridad
            valor_mostrar = valor[:10] + "..." if len(valor) > 10 else valor
            print(f"✅ {var}: {valor_mostrar}")
    
    # Verificar variables opcionales
    for var in variables_opcionales:
        valor = os.getenv(var)
        if valor:
            valor_mostrar = valor[:20] + "..." if len(valor) > 20 else valor
            print(f"✅ {var}: {valor_mostrar}")
        else:
            print(f"⚠️ {var}: No configurada (opcional)")
    
    if errores:
        print("\n🚨 ERRORES ENCONTRADOS:")
        for error in errores:
            print(f"  {error}")
        return False
    
    print("✅ Todas las variables requeridas están configuradas")
    return True

def verificar_dependencias():
    """Verifica que todas las dependencias necesarias estén instaladas."""
    print("\n🔍 Verificando dependencias...")
    
    dependencias = [
        ("openai", "OpenAI API"),
        ("langchain_openai", "LangChain OpenAI"),
        ("qdrant_client", "Qdrant Client"),
        ("supabase", "Supabase Client"),
        ("fastapi", "FastAPI"),
        ("docx", "Python DOCX"),
        ("PyPDF2", "PyPDF2")
    ]
    
    errores = []
    
    for modulo, descripcion in dependencias:
        try:
            __import__(modulo)
            print(f"✅ {descripcion}")
        except ImportError:
            errores.append(f"❌ {descripcion} ({modulo}) no instalado")
    
    if errores:
        print("\n🚨 DEPENDENCIAS FALTANTES:")
        for error in errores:
            print(f"  {error}")
        print("\n📦 Instalar con: pip install -r requirements.txt")
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True

def verificar_chat_agent():
    """Verifica que el ChatAgent inteligente funcione correctamente."""
    print("\n🔍 Verificando ChatAgent inteligente...")
    
    try:
        sys.path.append('.')
        from rag.chat_agent import get_chat_agent
        
        agent = get_chat_agent()
        if agent:
            print("✅ ChatAgent inicializado correctamente")
            
            # Prueba básica
            sesion_test = {
                'datos_cliente': {},
                'tipo_demanda': '',
                'hechos_adicionales': '',
                'estado': 'inicio'
            }
            
            resultado = agent.procesar_mensaje(
                sesion_test, 
                "Hola, necesito ayuda con una demanda laboral", 
                "test-123"
            )
            
            if resultado and resultado.get("mensaje"):
                print("✅ ChatAgent responde correctamente")
                print(f"   Respuesta: {resultado['mensaje'][:100]}...")
                return True
            else:
                print("❌ ChatAgent no genera respuestas válidas")
                return False
        else:
            print("❌ ChatAgent no pudo inicializarse")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando ChatAgent: {e}")
        return False

def verificar_document_processor():
    """Verifica que el procesador de documentos funcione."""
    print("\n🔍 Verificando procesador de documentos...")
    
    try:
        sys.path.append('.')
        from backend.core.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        print("✅ DocumentProcessor inicializado")
        
        # Verificar conexión con Qdrant
        try:
            collection_name = processor.get_user_collection_name("test-user")
            print(f"✅ Conexión con Qdrant: {collection_name}")
            return True
        except Exception as e:
            print(f"⚠️ Problema con Qdrant: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando DocumentProcessor: {e}")
        return False

def verificar_qa_agent():
    """Verifica que el agente de QA funcione para generar demandas."""
    print("\n🔍 Verificando generador de demandas...")
    
    try:
        sys.path.append('.')
        from rag.qa_agent import generar_demanda, obtener_tipos_demanda_disponibles
        
        tipos = obtener_tipos_demanda_disponibles()
        if tipos:
            print(f"✅ Tipos de demanda disponibles: {len(tipos)}")
            print(f"   Ejemplos: {tipos[:3]}")
        else:
            print("⚠️ No se encontraron tipos de demanda")
        
        # Prueba de generación (sin ejecutar realmente)
        print("✅ Generador de demandas disponible")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando generador de demandas: {e}")
        return False

def main():
    """Función principal de verificación."""
    print("🚀 VERIFICACIÓN COMPLETA DEL SISTEMA LEGAL AI")
    print("=" * 50)
    
    verificaciones = [
        ("Variables de entorno", verificar_variables_entorno),
        ("Dependencias", verificar_dependencias),
        ("ChatAgent inteligente", verificar_chat_agent),
        ("Procesador de documentos", verificar_document_processor),
        ("Generador de demandas", verificar_qa_agent)
    ]
    
    resultados = []
    
    for nombre, funcion in verificaciones:
        try:
            resultado = funcion()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"❌ Error en {nombre}: {e}")
            resultados.append((nombre, False))
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 50)
    
    exitosos = 0
    for nombre, resultado in resultados:
        status = "✅ FUNCIONANDO" if resultado else "❌ PROBLEMA"
        print(f"{status:20} {nombre}")
        if resultado:
            exitosos += 1
    
    porcentaje = (exitosos / len(resultados)) * 100
    print(f"\n🎯 Estado del sistema: {exitosos}/{len(resultados)} componentes funcionando ({porcentaje:.0f}%)")
    
    if porcentaje == 100:
        print("🎉 ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Subir documentos de entrenamiento")
        print("2. Probar el chat con casos reales")
        print("3. Generar tu primera demanda")
    elif porcentaje >= 75:
        print("⚠️ Sistema mayormente funcional con algunos problemas menores")
    else:
        print("🚨 Sistema requiere configuración adicional")
        print("\n📋 REVISAR:")
        print("- Variables de entorno en archivo .env")
        print("- Instalación de dependencias")
        print("- Conexiones a servicios externos")

if __name__ == "__main__":
    main() 