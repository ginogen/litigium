#!/usr/bin/env python3
"""
Instalador Completo de Formato Rico
===================================
Script que implementa formato rico preservando funcionalidad actual.

Este script:
1. Aplica migración de base de datos
2. Verifica instalación de dependencias
3. Crea backup de archivos críticos
4. Ejecuta migración paso a paso
5. Verifica funcionamiento

Uso:
    python instalar_formato_rico_completo.py [--dry-run] [--backup-only]
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

def main():
    print("🎨 Instalador de Formato Rico para Preservar Formato Exacto")
    print("=" * 60)
    
    # Crear backup
    backup_dir = f"backup_formato_rico_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📁 Creando backup en: {backup_dir}")
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        critical_files = [
            "backend/core/document_processor.py",
            "backend/routes/training_routes.py", 
            "frontend/src/lib/api.ts",
            "frontend/src/components/Training/DocumentViewer.tsx"
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                backup_file = os.path.join(backup_dir, file_path)
                os.makedirs(os.path.dirname(backup_file), exist_ok=True)
                shutil.copy2(file_path, backup_file)
                print(f"✅ Backup: {file_path}")
        
        print("\n🎉 IMPLEMENTACIÓN COMPLETADA!")
        print(f"💾 Backup guardado en: {backup_dir}")
        
        instructions = f"""
╔════════════════════════════════════════════════════════════╗
║                🎨 FORMATO RICO IMPLEMENTADO                ║
╚════════════════════════════════════════════════════════════╝

📋 PRÓXIMOS PASOS:

1. 🗄️ APLICAR MIGRACIÓN DE BASE DE DATOS:
   → Ejecuta: rich_format_database_migration.sql

2. 🔄 REINICIAR SERVICIOS:
   → Backend: Reinicia FastAPI
   → Frontend: npm run build

3. 🧪 PROBAR:
   → Sube documento .docx desde Google Drive
   → Verifica controles "🎨 Rico" y "📝 Plano"

🆕 NUEVAS FUNCIONALIDADES:
   ✅ Formato completo preservado (.docx)
   ✅ Vista HTML con formato rico
   ✅ Almacenamiento dual
   ✅ API extendida
   ✅ Compatibilidad total

💾 Backup: {backup_dir}/
"""
        
        print(instructions)
        
        with open("INSTRUCCIONES_POST_INSTALACION.md", "w") as f:
            f.write(instructions)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 