from docx import Document
import json
import os
import re
from glob import glob

def extract_sections(text):
    """Extrae las secciones principales de una demanda."""
    sections = {"hechos": "", "derecho": "", "petitorio": "", "prueba": ""}
    current = None
    
    for line in text.split("\n"):
        line_lower = line.strip().lower()
        if any(word in line_lower for word in ["hechos", "i.-", "i)", "1.-", "1)"]):
            current = "hechos"
        elif any(word in line_lower for word in ["derecho", "ii.-", "ii)", "2.-", "2)"]):
            current = "derecho"
        elif any(word in line_lower for word in ["petitorio", "solicito", "iii.-", "iii)", "3.-", "3)"]):
            current = "petitorio"
        elif any(word in line_lower for word in ["prueba", "ofrezco", "iv.-", "iv)", "4.-", "4)"]):
            current = "prueba"
        elif current and line.strip():
            sections[current] += line.strip() + " "
    
    return sections

def inferir_tipo_por_carpeta(filepath):
    """Infiere el tipo de demanda basado en la carpeta donde está el archivo."""
    carpeta = os.path.basename(os.path.dirname(filepath)).lower()
    
    tipos_mapeados = {
        "despido": "Despido Injustificado",
        "discriminatorio": "Despido Discriminatorio", 
        "accidente": "Accidente Laboral",
        "licencia": "Licencia Médica",
        "solidaridad": "Solidaridad Laboral",
        "blanco": "Empleados en Blanco",
        "negro": "Empleados en Negro"
    }
    
    for key, tipo in tipos_mapeados.items():
        if key in carpeta:
            return tipo
    
    return carpeta.replace("_", " ").title()

def docx_to_json(filepath, output_folder="data/casos_anteriores"):
    """Convierte un archivo Word a JSON estructurado."""
    try:
        doc = Document(filepath)
        full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        
        if not full_text.strip():
            print(f"⚠️ Archivo vacío: {filepath}")
            return False

        sections = extract_sections(full_text)
        
        # Inferir tipo por carpeta
        tipo_inferido = inferir_tipo_por_carpeta(filepath)
        
        json_data = {
            "id": os.path.splitext(os.path.basename(filepath))[0],
            "tipo": tipo_inferido,
            "jurisdiccion": "Argentina",
            "empresa": "",
            "fecha": "",
            **sections,
            "archivo_origen": filepath
        }

        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, json_data["id"] + ".json")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Convertido: {os.path.basename(filepath)} → {json_data['tipo']}")
        return True
        
    except Exception as e:
        print(f"❌ Error procesando {filepath}: {e}")
        return False

def procesar_todos_los_archivos():
    """Procesa todos los archivos Word en la carpeta ejemplos_demandas."""
    print("🔄 Buscando archivos Word en ejemplos_demandas/...")
    
    archivos_word = []
    for root, dirs, files in os.walk("ejemplos_demandas"):
        for file in files:
            if file.endswith(('.docx', '.doc')):
                archivos_word.append(os.path.join(root, file))
    
    if not archivos_word:
        print("⚠️ No se encontraron archivos Word en ejemplos_demandas/")
        return
    
    print(f"📂 Encontrados {len(archivos_word)} archivos Word")
    
    exitosos = 0
    for archivo in archivos_word:
        if docx_to_json(archivo):
            exitosos += 1
    
    print(f"\n🎉 Procesamiento completado: {exitosos}/{len(archivos_word)} archivos convertidos")
    print(f"📁 Los archivos JSON están en: data/casos_anteriores/")

if __name__ == "__main__":
    procesar_todos_los_archivos()