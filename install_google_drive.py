#!/usr/bin/env python3
"""
Instalador automático para la integración Google Drive
Instala dependencias, configura base de datos y valida configuración
"""

import os
import sys
import subprocess
import secrets
import base64
from pathlib import Path

def print_step(step, description):
    """Imprime paso de instalación con formato"""
    print(f"\n🔧 Paso {step}: {description}")
    print("=" * 50)

def run_command(command, description="", check=True):
    """Ejecuta comando con manejo de errores"""
    print(f"⚡ Ejecutando: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"📄 Error details: {e.stderr}")
        return None

def generate_encryption_key():
    """Genera clave de encriptación segura"""
    key = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(key).decode()

def install_backend_dependencies():
    """Instala dependencias del backend"""
    print_step(1, "Instalando dependencias del backend")
    
    backend_path = Path("backend")
    if not backend_path.exists():
        print("❌ Error: Directorio 'backend' no encontrado")
        print("   Ejecuta este script desde el directorio raíz del proyecto")
        return False
    
    os.chdir(backend_path)
    
    # Instalar dependencias
    result = run_command("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client cryptography")
    
    os.chdir("..")
    return result is not None

def setup_database():
    """Configura la base de datos"""
    print_step(2, "Configurando base de datos")
    
    if not Path("google_drive_schema.sql").exists():
        print("❌ Error: archivo google_drive_schema.sql no encontrado")
        return False
    
    print("📋 Para aplicar el schema de base de datos, ejecuta manualmente:")
    print("   psql -d tu_base_de_datos -f google_drive_schema.sql")
    print("   O usa tu cliente de base de datos preferido")
    
    return True

def setup_environment():
    """Configura variables de entorno"""
    print_step(3, "Configurando variables de entorno")
    
    env_path = Path("backend/.env")
    env_template_path = Path("backend/env_template.txt")
    
    if env_path.exists():
        print("⚠️  Archivo .env ya existe")
        overwrite = input("¿Deseas sobrescribirlo? (y/N): ").lower()
        if overwrite != 'y':
            print("📝 Por favor, agrega manualmente las variables de Google Drive al .env:")
            print_google_drive_env_vars()
            return True
    
    # Generar clave de encriptación
    encryption_key = generate_encryption_key()
    
    # Leer template si existe
    env_content = ""
    if env_template_path.exists():
        with open(env_template_path, 'r') as f:
            env_content = f.read()
    
    # Agregar variables de Google Drive
    google_drive_vars = f"""

# Google Drive Integration (agregado por install_google_drive.py)
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
TOKEN_ENCRYPTION_KEY={encryption_key}
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content + google_drive_vars)
    
    print(f"✅ Archivo .env creado/actualizado")
    print(f"🔑 Clave de encriptación generada automáticamente")
    print()
    print("⚠️  IMPORTANTE: Debes configurar manualmente:")
    print("   GOOGLE_CLIENT_ID=tu_google_oauth_client_id")
    print("   GOOGLE_CLIENT_SECRET=tu_google_oauth_client_secret")
    print()
    print("📖 Consulta GOOGLE_DRIVE_INTEGRATION_README.md para obtener estas credenciales")
    
    return True

def print_google_drive_env_vars():
    """Imprime variables de entorno necesarias"""
    encryption_key = generate_encryption_key()
    print(f"""
# Variables de Google Drive para agregar a .env:
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
TOKEN_ENCRYPTION_KEY={encryption_key}
""")

def validate_installation():
    """Valida la instalación"""
    print_step(4, "Validando instalación")
    
    validation_errors = []
    
    # Verificar archivos backend
    backend_files = [
        "backend/services/token_manager.py",
        "backend/services/google_drive_service.py", 
        "backend/routes/google_drive_routes.py",
        "backend/config.py"
    ]
    
    for file_path in backend_files:
        if not Path(file_path).exists():
            validation_errors.append(f"Archivo faltante: {file_path}")
    
    # Verificar archivos frontend
    frontend_files = [
        "frontend/src/lib/google-drive-api.ts",
        "frontend/src/components/Training/GoogleDriveConnector.tsx",
        "frontend/src/components/Training/GoogleDriveExplorer.tsx"
    ]
    
    for file_path in frontend_files:
        if not Path(file_path).exists():
            validation_errors.append(f"Archivo faltante: {file_path}")
    
    # Verificar .env
    env_path = Path("backend/.env")
    if not env_path.exists():
        validation_errors.append("Archivo backend/.env no encontrado")
    else:
        with open(env_path, 'r') as f:
            env_content = f.read()
            required_vars = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'TOKEN_ENCRYPTION_KEY']
            for var in required_vars:
                if var not in env_content:
                    validation_errors.append(f"Variable de entorno faltante: {var}")
    
    if validation_errors:
        print("❌ Errores de validación encontrados:")
        for error in validation_errors:
            print(f"   • {error}")
        return False
    else:
        print("✅ Validación exitosa - Instalación completada")
        return True

def print_next_steps():
    """Imprime pasos siguientes"""
    print_step(5, "Próximos pasos")
    
    print("""
🚀 Para completar la integración:

1. Configurar OAuth2 en Google Cloud Console:
   • Ve a https://console.cloud.google.com/
   • Crea proyecto o selecciona existente
   • Habilita Google Drive API
   • Configura OAuth consent screen
   • Crea credenciales OAuth 2.0
   • Agrega http://localhost:3000/auth/google/callback como redirect URI

2. Actualizar variables de entorno:
   • Edita backend/.env
   • Agrega tu GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET

3. Aplicar schema de base de datos:
   • psql -d tu_database -f google_drive_schema.sql

4. Instalar dependencias frontend (si es necesario):
   • cd frontend && npm install

5. Reiniciar aplicación:
   • Backend: python backend/main.py
   • Frontend: npm run dev

📖 Documentación completa: GOOGLE_DRIVE_INTEGRATION_README.md

🧪 Testing:
   • Ve a Training → Google Drive
   • Haz clic en "Conectar Google Drive"
   • Autoriza la aplicación
   • Explora y selecciona archivos
   • Importa documentos

¡Listo! 🎉
""")

def main():
    """Función principal del instalador"""
    print("🔗 Instalador de Integración Google Drive")
    print("=" * 50)
    print("Este script instalará y configurará la integración con Google Drive")
    print()
    
    proceed = input("¿Deseas continuar? (Y/n): ").lower()
    if proceed == 'n':
        print("Instalación cancelada")
        return
    
    try:
        # Ejecutar pasos de instalación
        success = True
        
        success &= install_backend_dependencies()
        success &= setup_database() 
        success &= setup_environment()
        success &= validate_installation()
        
        if success:
            print("\n🎉 ¡Instalación completada exitosamente!")
            print_next_steps()
        else:
            print("\n❌ Instalación falló con errores")
            print("   Revisa los mensajes anteriores para más detalles")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Instalación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 