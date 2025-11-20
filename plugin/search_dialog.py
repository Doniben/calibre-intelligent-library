"""
Search Dialog
Main search interface
"""
from PyQt5.Qt import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                      QPushButton, QTableWidget, QTableWidgetItem, QTextEdit,
                      QSplitter, QWidget, Qt, QHeaderView, QMessageBox)
import requests


class SearchDialog(QDialog):
    """Main search dialog"""
    
    def __init__(self, gui, icon, backend_url):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.backend_url = backend_url
        self.current_session = None
        
        self.setWindowTitle("Biblioteca Inteligente - Búsqueda Semántica")
        self.setWindowIcon(icon)
        self.resize(1000, 700)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Search input
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ej: libros sobre inteligencia artificial")
        self.search_input.returnPressed.connect(self.do_search)
        search_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("Buscar")
        self.search_button.clicked.connect(self.do_search)
        search_layout.addWidget(self.search_button)
        
        layout.addLayout(search_layout)
        
        # Main splitter (results + chat)
        splitter = QSplitter(Qt.Horizontal)
        
        # Results table
        results_widget = QWidget()
        results_layout = QVBoxLayout()
        results_widget.setLayout(results_layout)
        
        results_layout.addWidget(QLabel("Resultados:"))
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Título", "Autor", "Capítulo", "Similitud"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.itemDoubleClicked.connect(self.open_book)
        results_layout.addWidget(self.results_table)
        
        # Buttons for results
        results_buttons = QHBoxLayout()
        self.open_button = QPushButton("Abrir Libro")
        self.open_button.clicked.connect(self.open_selected_book)
        results_buttons.addWidget(self.open_button)
        
        self.ask_button = QPushButton("Preguntar a Kiro")
        self.ask_button.clicked.connect(self.ask_about_selected)
        results_buttons.addWidget(self.ask_button)
        
        results_buttons.addStretch()
        results_layout.addLayout(results_buttons)
        
        splitter.addWidget(results_widget)
        
        # Chat panel
        chat_widget = QWidget()
        chat_layout = QVBoxLayout()
        chat_widget.setLayout(chat_layout)
        
        chat_layout.addWidget(QLabel("💬 Asistente Kiro:"))
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        chat_layout.addWidget(self.chat_history)
        
        # Chat input
        chat_input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Pregunta sobre los resultados...")
        self.chat_input.returnPressed.connect(self.send_message)
        chat_input_layout.addWidget(self.chat_input)
        
        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_message)
        chat_input_layout.addWidget(self.send_button)
        
        chat_layout.addLayout(chat_input_layout)
        
        splitter.addWidget(chat_widget)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel("Listo")
        layout.addWidget(self.status_label)
    
    def do_search(self):
        """Perform search"""
        query = self.search_input.text().strip()
        if not query:
            return
        
        self.status_label.setText("Buscando...")
        self.search_button.setEnabled(False)
        
        try:
            response = requests.post(
                f"{self.backend_url}/search",
                json={"query": query, "limit": 20},
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                self.display_results(results)
                self.status_label.setText(f"Encontrados {len(results)} resultados")
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Error en la búsqueda: {response.status_code}"
                )
                self.status_label.setText("Error en búsqueda")
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de Conexión",
                f"No se pudo conectar al backend:\n{str(e)}"
            )
            self.status_label.setText("Error de conexión")
        
        finally:
            self.search_button.setEnabled(True)
    
    def display_results(self, results):
        """Display search results in table"""
        self.results_table.setRowCount(len(results))
        self.results = results  # Store for later use
        
        for i, result in enumerate(results):
            # Title
            self.results_table.setItem(i, 0, QTableWidgetItem(result.get('title', '')))
            
            # Author
            self.results_table.setItem(i, 1, QTableWidgetItem(result.get('author', '')))
            
            # Chapter
            chapter = result.get('chapter_title', 'N/A')
            self.results_table.setItem(i, 2, QTableWidgetItem(chapter))
            
            # Similarity
            similarity = result.get('similarity', 0)
            self.results_table.setItem(i, 3, QTableWidgetItem(f"{similarity:.1%}"))
    
    def open_book(self, item):
        """Open book in Calibre"""
        row = item.row()
        if row < len(self.results):
            book_id = self.results[row].get('calibre_id')
            if book_id:
                # Open book in Calibre
                self.gui.iactions['View'].view_book(self.gui.library_view.model().db, book_id)
    
    def open_selected_book(self):
        """Open selected book"""
        selected = self.results_table.selectedItems()
        if selected:
            self.open_book(selected[0])
    
    def ask_about_selected(self):
        """Ask Kiro about selected books"""
        selected_rows = set(item.row() for item in self.results_table.selectedItems())
        
        if not selected_rows:
            QMessageBox.information(self, "Selección", "Selecciona uno o más libros primero")
            return
        
        # Get selected book IDs
        book_ids = [self.results[row].get('calibre_id') for row in selected_rows]
        
        # Create session if needed
        if not self.current_session:
            try:
                response = requests.post(f"{self.backend_url}/session/new")
                if response.status_code == 200:
                    self.current_session = response.json()['session_id']
                    self.chat_history.append("🤖 <b>Sesión iniciada con Kiro</b>\n")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear sesión: {e}")
                return
        
        # Prompt user for question
        from PyQt5.Qt import QInputDialog
        question, ok = QInputDialog.getText(
            self,
            "Pregunta a Kiro",
            "¿Qué quieres saber sobre los libros seleccionados?"
        )
        
        if ok and question:
            self.ask_kiro(question, book_ids)
    
    def send_message(self):
        """Send message to Kiro"""
        message = self.chat_input.text().strip()
        if not message:
            return
        
        # Create session if needed
        if not self.current_session:
            try:
                response = requests.post(f"{self.backend_url}/session/new")
                if response.status_code == 200:
                    self.current_session = response.json()['session_id']
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear sesión: {e}")
                return
        
        self.ask_kiro(message)
    
    def ask_kiro(self, question, context_books=None):
        """Ask Kiro a question"""
        self.chat_history.append(f"\n<b>Tú:</b> {question}\n")
        self.chat_input.clear()
        self.send_button.setEnabled(False)
        
        try:
            payload = {"question": question}
            if context_books:
                payload["context_books"] = context_books
            
            response = requests.post(
                f"{self.backend_url}/session/{self.current_session}/ask",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('response', '')
                self.chat_history.append(f"<b>🤖 Kiro:</b> {answer}\n")
            else:
                self.chat_history.append(f"<i>Error: {response.status_code}</i>\n")
        
        except Exception as e:
            self.chat_history.append(f"<i>Error: {str(e)}</i>\n")
        
        finally:
            self.send_button.setEnabled(True)
