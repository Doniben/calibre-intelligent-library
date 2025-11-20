"""
Calibre Intelligent Library Plugin
Main plugin entry point
"""
from calibre.customize import InterfaceActionBase


class BibliotecaInteligentePlugin(InterfaceActionBase):
    """
    Plugin for semantic search and AI assistant in Calibre
    """
    
    name = 'Biblioteca Inteligente'
    description = 'Búsqueda semántica y asistente IA para tu biblioteca'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Doniben'
    version = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)
    
    # This is the actual plugin class that will be instantiated
    actual_plugin = 'calibre_plugins.biblioteca_inteligente.ui:BibliotecaInteligenteAction'
    
    def is_customizable(self):
        """Plugin can be customized"""
        return True
    
    def config_widget(self):
        """Return configuration widget"""
        from calibre_plugins.biblioteca_inteligente.config import ConfigWidget
        return ConfigWidget()
    
    def save_settings(self, config_widget):
        """Save settings from config widget"""
        config_widget.save_settings()
