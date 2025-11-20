"""
Plugin UI Action
Main interface integration with Calibre
"""
from calibre.gui2.actions import InterfaceAction
from PyQt5.Qt import QIcon, QPixmap
import requests
import subprocess
import time


class BibliotecaInteligenteAction(InterfaceAction):
    """Main action for the plugin"""
    
    name = 'Biblioteca Inteligente'
    action_spec = ('Búsqueda Inteligente', None, 
                   'Búsqueda semántica con IA', 'Ctrl+Shift+I')
    action_type = 'current'
    
    def genesis(self):
        """Initialize the action"""
        # Create icon (using a built-in icon for now)
        icon = self.qaction.icon()
        if icon.isNull():
            icon = QIcon(I('search.png'))
        
        self.qaction.setIcon(icon)
        self.qaction.triggered.connect(self.show_search_dialog)
        
        # Check backend status
        self.backend_url = self.get_backend_url()
        self.ensure_backend_running()
    
    def get_backend_url(self):
        """Get backend URL from config"""
        from calibre_plugins.biblioteca_inteligente.config import prefs
        host = prefs.get('backend_host', '127.0.0.1')
        port = prefs.get('backend_port', 8765)
        return f"http://{host}:{port}"
    
    def ensure_backend_running(self):
        """Ensure backend server is running"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=2)
            if response.status_code == 200:
                print("✓ Backend is running")
                return True
        except:
            print("⚠ Backend not running, attempting to start...")
            # Could auto-start backend here
            return False
    
    def show_search_dialog(self):
        """Show the search dialog"""
        from calibre_plugins.biblioteca_inteligente.search_dialog import SearchDialog
        
        dialog = SearchDialog(self.gui, self.qaction.icon(), self.backend_url)
        dialog.exec_()
    
    def apply_settings(self):
        """Apply settings changes"""
        self.backend_url = self.get_backend_url()
