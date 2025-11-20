#!/usr/bin/env python3
"""
Biblioteca Inteligente - Installer
Detects existing installations and sets up the system
"""
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path


class BibliotecaInstaller:
    """Intelligent installer for Biblioteca Inteligente"""
    
    def __init__(self):
        self.home = Path.home()
        self.calibre_path = None
        self.data_path = None
        self.project_root = Path(__file__).parent
    
    def detect_calibre_library(self):
        """Detect Calibre Library location"""
        print("\n🔍 Buscando Calibre Library...")
        
        possible_paths = [
            self.home / "Calibre Library",
            self.home / "Documents" / "Calibre Library",
            self.home / "calibre" / "Calibre Library",
        ]
        
        for path in possible_paths:
            if (path / "metadata.db").exists():
                self.calibre_path = path
                self.data_path = path / ".biblioteca_inteligente"
                print(f"✓ Calibre Library encontrada: {path}")
                return True
        
        print("✗ No se encontró Calibre Library automáticamente")
        return False
    
    def prompt_calibre_path(self):
        """Prompt user for Calibre Library path"""
        print("\nIngresa la ruta a tu Calibre Library:")
        path_str = input("> ").strip()
        
        path = Path(path_str).expanduser()
        if (path / "metadata.db").exists():
            self.calibre_path = path
            self.data_path = path / ".biblioteca_inteligente"
            print(f"✓ Calibre Library configurada: {path}")
            return True
        else:
            print("✗ No se encontró metadata.db en esa ruta")
            return False
    
    def check_existing_installation(self):
        """Check for existing installation"""
        if not self.data_path:
            return "NEW"
        
        if self.data_path.exists():
            config_file = self.data_path / "config.json"
            if config_file.exists():
                print(f"\n✓ Instalación existente encontrada")
                return "EXISTING"
        
        return "NEW"
    
    def check_python_version(self):
        """Check Python version"""
        print("\n🐍 Verificando Python...")
        version = sys.version_info
        
        if version.major == 3 and version.minor >= 9:
            print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            print(f"✗ Python 3.9+ requerido (tienes {version.major}.{version.minor})")
            return False
    
    def check_venv(self):
        """Check if virtual environment exists"""
        venv_path = self.project_root / "venv"
        
        if venv_path.exists():
            print("✓ Entorno virtual encontrado")
            return True
        else:
            print("⚠ Entorno virtual no encontrado")
            return False
    
    def create_venv(self):
        """Create virtual environment"""
        print("\n📦 Creando entorno virtual...")
        venv_path = self.project_root / "venv"
        
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                check=True
            )
            print("✓ Entorno virtual creado")
            return True
        except Exception as e:
            print(f"✗ Error creando entorno virtual: {e}")
            return False
    
    def install_dependencies(self):
        """Install Python dependencies"""
        print("\n📚 Instalando dependencias...")
        
        venv_python = self.project_root / "venv" / "bin" / "python"
        if not venv_python.exists():
            venv_python = self.project_root / "venv" / "Scripts" / "python.exe"
        
        requirements = self.project_root / "backend" / "requirements.txt"
        
        try:
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", "-r", str(requirements)],
                check=True,
                capture_output=True
            )
            print("✓ Dependencias instaladas")
            return True
        except Exception as e:
            print(f"✗ Error instalando dependencias: {e}")
            return False
    
    def create_data_directory(self):
        """Create data directory"""
        print(f"\n📁 Creando directorio de datos...")
        
        try:
            self.data_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Directorio creado: {self.data_path}")
            return True
        except Exception as e:
            print(f"✗ Error creando directorio: {e}")
            return False
    
    def create_config(self):
        """Create configuration file"""
        print("\n⚙️ Creando configuración...")
        
        config = {
            "version": "1.0.0",
            "calibre_library_path": str(self.calibre_path),
            "backend": {
                "host": "127.0.0.1",
                "port": 8765
            },
            "indexing": {
                "last_indexed": None,
                "total_books": 0,
                "total_chapters": 0,
                "total_chunks": 0,
                "embedding_model": "all-MiniLM-L6-v2",
                "chunk_size": 500,
                "chunk_overlap": 50
            },
            "search": {
                "results_per_page": 20,
                "min_similarity": 0.5,
                "context_window": 3
            },
            "kiro": {
                "command": "kiro-cli",
                "timeout": 60,
                "max_context_tokens": 4000
            }
        }
        
        config_file = self.data_path / "config.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✓ Configuración creada: {config_file}")
            return True
        except Exception as e:
            print(f"✗ Error creando configuración: {e}")
            return False
    
    def create_startup_script(self):
        """Create startup script"""
        print("\n🚀 Creando script de inicio...")
        
        script_content = f"""#!/bin/bash
# Biblioteca Inteligente - Startup Script

cd "{self.project_root}"
source venv/bin/activate
python backend/server.py
"""
        
        script_path = self.project_root / "start_backend.sh"
        
        try:
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            script_path.chmod(0o755)
            print(f"✓ Script creado: {script_path}")
            return True
        except Exception as e:
            print(f"✗ Error creando script: {e}")
            return False
    
    def show_next_steps(self):
        """Show next steps to user"""
        print("\n" + "="*60)
        print("✅ INSTALACIÓN COMPLETADA")
        print("="*60)
        
        print("\n📋 Próximos pasos:\n")
        
        print("1. Iniciar el backend:")
        print(f"   cd {self.project_root}")
        print("   ./start_backend.sh")
        print("   (o manualmente: source venv/bin/activate && python backend/server.py)")
        
        print("\n2. Instalar el plugin en Calibre:")
        print("   - Abre Calibre")
        print("   - Preferencias → Plugins → Cargar plugin desde archivo")
        print(f"   - Selecciona: {self.project_root}/plugin/biblioteca-inteligente.zip")
        print("   - Reinicia Calibre")
        
        print("\n3. Indexar tu biblioteca (primera vez):")
        print("   - Esto tomará 12-14 horas")
        print("   - Se ejecutará en background")
        print("   - Puedes seguir usando Calibre normalmente")
        
        print("\n4. Usar el sistema:")
        print("   - Click en 'Búsqueda Inteligente' en Calibre")
        print("   - O usa Ctrl+Shift+I")
        
        print("\n📚 Documentación:")
        print(f"   {self.project_root}/README.md")
        print(f"   {self.project_root}/docs/")
        
        print("\n" + "="*60)
    
    def run(self):
        """Run the installer"""
        print("="*60)
        print("  BIBLIOTECA INTELIGENTE - INSTALADOR")
        print("="*60)
        
        # Check Python version
        if not self.check_python_version():
            return False
        
        # Detect Calibre Library
        if not self.detect_calibre_library():
            if not self.prompt_calibre_path():
                print("\n✗ No se pudo configurar Calibre Library")
                return False
        
        # Check existing installation
        status = self.check_existing_installation()
        
        if status == "EXISTING":
            print("\n⚠️ Ya existe una instalación")
            response = input("¿Deseas reinstalar? (s/n): ").lower()
            if response != 's':
                print("Instalación cancelada")
                return False
        
        # Check/create venv
        if not self.check_venv():
            if not self.create_venv():
                return False
        
        # Install dependencies
        print("\n⏳ Esto puede tomar varios minutos...")
        if not self.install_dependencies():
            return False
        
        # Create data directory
        if not self.create_data_directory():
            return False
        
        # Create config
        if not self.create_config():
            return False
        
        # Create startup script
        if not self.create_startup_script():
            return False
        
        # Show next steps
        self.show_next_steps()
        
        return True


if __name__ == "__main__":
    installer = BibliotecaInstaller()
    success = installer.run()
    sys.exit(0 if success else 1)
