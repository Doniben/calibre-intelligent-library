#!/usr/bin/env python3
"""
Biblioteca Inteligente - Backup System
Creates portable backups of indexed data
"""
import os
import sys
import json
import tarfile
import shutil
from pathlib import Path
from datetime import datetime


class BackupManager:
    """Manages backups of biblioteca data"""
    
    def __init__(self, calibre_path=None):
        self.home = Path.home()
        self.calibre_path = calibre_path or self.detect_calibre_library()
        
        if self.calibre_path:
            self.data_path = self.calibre_path / ".biblioteca_inteligente"
        else:
            self.data_path = None
    
    def detect_calibre_library(self):
        """Detect Calibre Library"""
        possible_paths = [
            self.home / "Calibre Library",
            self.home / "Documents" / "Calibre Library",
        ]
        
        for path in possible_paths:
            if (path / "metadata.db").exists():
                return path
        
        return None
    
    def create_backup(self, output_dir=None):
        """Create backup of biblioteca data"""
        if not self.data_path or not self.data_path.exists():
            print("✗ No se encontró instalación de Biblioteca Inteligente")
            return None
        
        # Output directory
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = self.home / "biblioteca_backups"
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"biblioteca_backup_{timestamp}.tar.gz"
        backup_file = output_path / backup_name
        
        print(f"\n📦 Creando backup...")
        print(f"   Origen: {self.data_path}")
        print(f"   Destino: {backup_file}")
        
        try:
            with tarfile.open(backup_file, "w:gz") as tar:
                # Add all files from data directory
                for item in self.data_path.iterdir():
                    if item.name not in ['.DS_Store']:
                        print(f"   + {item.name}")
                        tar.add(item, arcname=item.name)
            
            # Get backup size
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            
            print(f"\n✓ Backup creado exitosamente")
            print(f"   Archivo: {backup_file}")
            print(f"   Tamaño: {size_mb:.1f} MB")
            
            return backup_file
        
        except Exception as e:
            print(f"\n✗ Error creando backup: {e}")
            return None
    
    def restore_backup(self, backup_file):
        """Restore from backup"""
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            print(f"✗ Archivo de backup no encontrado: {backup_file}")
            return False
        
        if not self.data_path:
            print("✗ No se pudo determinar la ubicación de Calibre Library")
            return False
        
        print(f"\n📥 Restaurando backup...")
        print(f"   Origen: {backup_path}")
        print(f"   Destino: {self.data_path}")
        
        # Confirm overwrite
        if self.data_path.exists():
            print("\n⚠️ Ya existe una instalación")
            response = input("¿Deseas sobrescribir? (s/n): ").lower()
            if response != 's':
                print("Restauración cancelada")
                return False
            
            # Backup existing data
            print("   Respaldando datos actuales...")
            temp_backup = self.create_backup(self.home / "biblioteca_backups" / "pre_restore")
            if temp_backup:
                print(f"   ✓ Backup de seguridad: {temp_backup}")
        
        # Create data directory
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(self.data_path)
            
            print(f"\n✓ Backup restaurado exitosamente")
            
            # Update config with current path
            config_file = self.data_path / "config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                config['calibre_library_path'] = str(self.calibre_path)
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                print("   ✓ Configuración actualizada")
            
            return True
        
        except Exception as e:
            print(f"\n✗ Error restaurando backup: {e}")
            return False
    
    def list_backups(self, backup_dir=None):
        """List available backups"""
        if backup_dir:
            search_path = Path(backup_dir)
        else:
            search_path = self.home / "biblioteca_backups"
        
        if not search_path.exists():
            print("No se encontraron backups")
            return []
        
        backups = list(search_path.glob("biblioteca_backup_*.tar.gz"))
        
        if not backups:
            print("No se encontraron backups")
            return []
        
        print(f"\n📋 Backups disponibles en {search_path}:\n")
        
        for i, backup in enumerate(sorted(backups, reverse=True), 1):
            size_mb = backup.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"{i}. {backup.name}")
            print(f"   Tamaño: {size_mb:.1f} MB")
            print(f"   Fecha: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        
        return backups
    
    def get_info(self):
        """Get info about current installation"""
        if not self.data_path or not self.data_path.exists():
            print("No se encontró instalación")
            return None
        
        config_file = self.data_path / "config.json"
        
        if not config_file.exists():
            print("No se encontró configuración")
            return None
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print("\n📊 Información de la instalación:\n")
        print(f"Calibre Library: {config.get('calibre_library_path')}")
        print(f"Versión: {config.get('version')}")
        
        indexing = config.get('indexing', {})
        print(f"\nIndexación:")
        print(f"  Libros: {indexing.get('total_books', 0):,}")
        print(f"  Capítulos: {indexing.get('total_chapters', 0):,}")
        print(f"  Chunks: {indexing.get('total_chunks', 0):,}")
        print(f"  Última indexación: {indexing.get('last_indexed', 'Nunca')}")
        
        # Check file sizes
        print(f"\nArchivos:")
        for item in self.data_path.iterdir():
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                print(f"  {item.name}: {size_mb:.1f} MB")
        
        return config


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Biblioteca Inteligente - Backup Manager")
    parser.add_argument('action', choices=['create', 'restore', 'list', 'info'],
                       help='Action to perform')
    parser.add_argument('--file', help='Backup file (for restore)')
    parser.add_argument('--output', help='Output directory (for create)')
    parser.add_argument('--calibre-path', help='Path to Calibre Library')
    
    args = parser.parse_args()
    
    manager = BackupManager(args.calibre_path)
    
    if args.action == 'create':
        manager.create_backup(args.output)
    
    elif args.action == 'restore':
        if not args.file:
            print("Error: --file requerido para restore")
            sys.exit(1)
        manager.restore_backup(args.file)
    
    elif args.action == 'list':
        manager.list_backups(args.output)
    
    elif args.action == 'info':
        manager.get_info()


if __name__ == "__main__":
    main()
