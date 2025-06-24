import os

folders = [
    "api",
    "ingestion",
    "rag",
    "data/casos_anteriores",
    "ejemplos_demandas/demanda_licencia_medica",
    "ejemplos_demandas/demanda_solidaridad_laboral",
    "ejemplos_demandas/empleados_blanco",
    "ejemplos_demandas/empleados_blanco_negro",
    "ejemplos_demandas/empleados_negro",
    "static"
]

files = [
    "main.py",
    "api/endpoints.py",
    "ingestion/extract_and_convert.py",
    "ingestion/upload_to_qdrant.py",
    "rag/qa_agent.py",
    "rag/utils.py",
    "requirements.txt",
    ".env"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)

for file in files:
    with open(file, "w", encoding="utf-8") as f:
        f.write("")  # crea el archivo vacío

print("✅ Proyecto inicializado con estructura completa.")
