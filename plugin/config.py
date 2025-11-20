"""
Plugin Configuration
"""
from PyQt5.Qt import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                      QSpinBox, QGroupBox, QFormLayout, QPushButton,
                      QHBoxLayout)
from calibre.utils.config import JSONConfig

# Plugin preferences
prefs = JSONConfig('plugins/biblioteca_inteligente')

# Default settings
prefs.defaults['backend_host'] = '127.0.0.1'
prefs.defaults['backend_port'] = 8765
prefs.defaults['results_limit'] = 20
prefs.defaults['min_similarity'] = 0.5


class ConfigWidget(QWidget):
    """Configuration widget for the plugin"""
    
    def __init__(self):
        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Backend settings
        backend_group = QGroupBox("Backend Configuration")
        backend_layout = QFormLayout()
        
        self.host_edit = QLineEdit(prefs['backend_host'])
        backend_layout.addRow("Host:", self.host_edit)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(prefs['backend_port'])
        backend_layout.addRow("Port:", self.port_spin)
        
        backend_group.setLayout(backend_layout)
        self.layout.addWidget(backend_group)
        
        # Search settings
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout()
        
        self.results_spin = QSpinBox()
        self.results_spin.setRange(5, 100)
        self.results_spin.setValue(prefs['results_limit'])
        search_layout.addRow("Results limit:", self.results_spin)
        
        self.similarity_spin = QSpinBox()
        self.similarity_spin.setRange(0, 100)
        self.similarity_spin.setValue(int(prefs['min_similarity'] * 100))
        self.similarity_spin.setSuffix("%")
        search_layout.addRow("Min similarity:", self.similarity_spin)
        
        search_group.setLayout(search_layout)
        self.layout.addWidget(search_group)
        
        # Test connection button
        test_layout = QHBoxLayout()
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        test_layout.addWidget(self.test_button)
        test_layout.addStretch()
        self.layout.addLayout(test_layout)
        
        self.layout.addStretch()
    
    def test_connection(self):
        """Test connection to backend"""
        import requests
        from PyQt5.Qt import QMessageBox
        
        host = self.host_edit.text()
        port = self.port_spin.value()
        url = f"http://{host}:{port}/health"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                QMessageBox.information(
                    self,
                    "Connection Successful",
                    f"Connected to backend!\n\n"
                    f"Status: {data.get('status')}\n"
                    f"Indexed books: {data.get('indexed_books')}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Connection Failed",
                    f"Backend returned status code: {response.status_code}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Could not connect to backend:\n{str(e)}\n\n"
                f"Make sure the backend server is running."
            )
    
    def save_settings(self):
        """Save settings"""
        prefs['backend_host'] = self.host_edit.text()
        prefs['backend_port'] = self.port_spin.value()
        prefs['results_limit'] = self.results_spin.value()
        prefs['min_similarity'] = self.similarity_spin.value() / 100.0
