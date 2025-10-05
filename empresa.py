import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QStackedWidget, QTableWidget, 
    QTableWidgetItem, QDialog, QMessageBox, QComboBox, QMenu, QGridLayout
)
from PyQt6.QtGui import QPixmap, QIntValidator # QIntValidator fue añadido aquí
from PyQt6.QtCore import Qt

# --- Configuración de la base de datos ---
DATABASE_NAME = "empresa.db"

def setup_database():
    """Configura las tablas iniciales de la base de datos, incluyendo migración para 'vins'."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Tabla de usuarios para el login
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT
        )
    """)

    # Tabla de asesores de venta
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advisors (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    """)

    # Tabla de Órdenes de Trabajo (OT)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ots (
            id INTEGER PRIMARY KEY,
            ot_number TEXT NOT NULL UNIQUE,
            sales_advisor TEXT,
            vin TEXT,
            status TEXT,
            request_date TEXT
        )
    """)
    
    # Tabla de Partes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY,
            part_number TEXT NOT NULL UNIQUE,
            part_name TEXT
        )
    """)
    
    # Tabla de detalles de la OT y sus partes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ot_parts (
            ot_id INTEGER,
            part_id INTEGER,
            quantity INTEGER,
            status TEXT,
            FOREIGN KEY(ot_id) REFERENCES ots(id),
            FOREIGN KEY(part_id) REFERENCES parts(id),
            PRIMARY KEY (ot_id, part_id)
        )
    """)
    
    # Tabla de información de vehículos (VIN)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vins (
            vin TEXT PRIMARY KEY,
            model TEXT,
            year INTEGER,
            insurance TEXT,
            owner_name TEXT,
            owner_email TEXT,
            owner_phone TEXT,
            sales_advisor TEXT
        )
    """)
    
    # MIGRACIÓN: Añadir columna 'sales_advisor' si la tabla ya existía sin ella
    try:
        cursor.execute("ALTER TABLE vins ADD COLUMN sales_advisor TEXT")
    except sqlite3.OperationalError as e:
        if not 'duplicate column name' in str(e):
             print(f"Error de migración inesperado: {e}")
             
    # --- Datos de prueba ---
    cursor.execute("INSERT OR IGNORE INTO users (username, password, full_name) VALUES (?, ?, ?)", 
                   ('admin', 'password', 'Administrador'))

    cursor.execute("INSERT OR IGNORE INTO advisors (name) VALUES (?)", ('Laura Gómez',))
    cursor.execute("INSERT OR IGNORE INTO advisors (name) VALUES (?)", ('Juan Pérez',))

    # El INSERT DE PRUEBA ahora utiliza la columna 'sales_advisor'
    cursor.execute("""
        INSERT OR IGNORE INTO vins (
            vin, model, year, insurance, owner_name, owner_email, owner_phone, sales_advisor
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ('VIN1234567890', 'Tesla Model 3', 2023, 'Seguros Nacionales', 'Carlos Ruíz', 'carlos@email.com', '5512345678', 'Laura Gómez'))
    
    # Añadimos otra OT para probar la búsqueda
    cursor.execute("""
        INSERT OR IGNORE INTO vins (
            vin, model, year, insurance, owner_name, owner_email, owner_phone, sales_advisor
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ('VIN0987654321', 'Honda Civic', 2022, 'GNP', 'Ana Torres', 'ana@email.com', '5598765432', 'Juan Pérez'))
    
    cursor.execute("INSERT OR IGNORE INTO ots (ot_number, sales_advisor, vin, status, request_date) VALUES (?, ?, ?, ?, ?)",
                   ('OT-001', 'Laura Gómez', 'VIN1234567890', 'Pendiente', '2025-09-10'))
                   
    cursor.execute("INSERT OR IGNORE INTO ots (ot_number, sales_advisor, vin, status, request_date) VALUES (?, ?, ?, ?, ?)",
                   ('OT-002', 'Juan Pérez', 'VIN0987654321', 'Pendiente', '2025-09-10'))
    
    cursor.execute("INSERT OR IGNORE INTO parts (part_number, part_name) VALUES (?, ?)",
                   ('NP-010-F', 'Filtro de aire'))
    cursor.execute("INSERT OR IGNORE INTO parts (part_number, part_name) VALUES (?, ?)",
                   ('NP-011-B', 'Balatas delanteras'))
    
    ot_id_result = cursor.execute("SELECT id FROM ots WHERE ot_number = 'OT-001'").fetchone()
    if ot_id_result:
        ot_id = ot_id_result[0]
        part_id_1_result = cursor.execute("SELECT id FROM parts WHERE part_number = 'NP-010-F'").fetchone()
        part_id_2_result = cursor.execute("SELECT id FROM parts WHERE part_number = 'NP-011-B'").fetchone()

        if part_id_1_result:
            part_id_1 = part_id_1_result[0]
            cursor.execute("INSERT OR IGNORE INTO ot_parts (ot_id, part_id, quantity, status) VALUES (?, ?, ?, ?)",
                           (ot_id, part_id_1, 2, 'Pedida'))
        
        if part_id_2_result:
            part_id_2 = part_id_2_result[0]
            cursor.execute("INSERT OR IGNORE INTO ot_parts (ot_id, part_id, quantity, status) VALUES (?, ?, ?, ?)",
                           (ot_id, part_id_2, 1, 'Pendiente'))

    conn.commit()
    conn.close()

# --- Carga de estilos CSS ---
def load_stylesheet(filename="styles.css"):
    """Carga los estilos CSS desde un archivo."""
    try:
        with open(filename, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Advertencia: No se encontró el archivo de estilos '{filename}'. Usando estilos por defecto.")
        return "" 

class LoginWindow(QDialog):
    # ... (código sin cambios) ...
    def __init__(self, stylesheet):
        super().__init__()
        self.setWindowTitle("Inicio de Sesión")
        self.setFixedSize(400, 300)
        self.setStyleSheet(stylesheet)
        
        self.center()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        title_label = QLabel("Bienvenido")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel("Ingresa tus credenciales")
        subtitle_label.setObjectName("subtitle_label")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuario")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.login_button = QPushButton("Entrar")
        self.login_button.clicked.connect(self.check_login)

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        
        self.setLayout(layout)

    def center(self):
        """Centra la ventana en la pantalla."""
        screen = QApplication.primaryScreen().geometry()
        self.move(int((screen.width() - self.width()) / 2), int((screen.height() - self.height()) / 2) - 100)

    def check_login(self):
        """Verifica las credenciales del usuario."""
        username = self.username_input.text()
        password = self.password_input.text()
        
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            QMessageBox.information(self, "Acceso exitoso", "¡Bienvenido, " + user[3] + "!")
            self.accept()
        else:
            QMessageBox.warning(self, "Error de acceso", "Usuario o contraseña incorrectos.")

# --- CLASES PRINCIPALES DE NAVEGACIÓN ---

class MainWindow(QMainWindow):
    # ... (código sin cambios relevantes para este cambio) ...
    def __init__(self, stylesheet):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión de Empresa")
        self.setFixedSize(1200, 800)
        self.move(int((QApplication.primaryScreen().geometry().width() - 1200) / 2), 50)
        self.setStyleSheet(stylesheet)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Cabecera con botones de navegación ---
        header_widget = QWidget()
        header_widget.setObjectName("header_buttons_container")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(0)
        
        self.nav_buttons = {}

        # Botón 1: Inicio
        home_button = QPushButton("Inicio")
        home_button.setCheckable(True)
        home_button.setChecked(True)
        home_button.clicked.connect(lambda: self.change_view("home"))
        header_layout.addWidget(home_button)
        self.nav_buttons["home"] = home_button
        
        # Botón 2: OT (Despliega menú)
        ot_button = QPushButton("Órdenes de Trabajo ▼")
        
        header_layout.addWidget(ot_button)
        self.nav_buttons["ot"] = ot_button
        
        # Botón 3: Partes (Despliega menú)
        parts_button = QPushButton("Partes ▼")
        
        header_layout.addWidget(parts_button)
        self.nav_buttons["parts"] = parts_button
        
        # Botón 4: VIN (Despliega menú)
        vin_button = QPushButton("Vehículos (VIN) ▼")
        
        header_layout.addWidget(vin_button)
        self.nav_buttons["vin"] = vin_button
        
        # NUEVO BOTÓN: Asesor de Ventas (Para filtro rápido)
        advisor_button = QPushButton("Asesor de Ventas ▼")
        
        header_layout.addWidget(advisor_button)
        self.nav_buttons["advisor_filter"] = advisor_button
        
        header_layout.addStretch()

        # --- Contenido principal con QStackedWidget ---
        self.stacked_widget = QStackedWidget()
        
        # 1. Ventana de Inicio
        self.home_widget = QWidget()
        self.setup_home_widget(self.home_widget)
        self.stacked_widget.addWidget(self.home_widget) # Índice 0
        
        # 2. CREAR WIDGETS DE VISTA PRIMERO
        
        # 2. Ventana de OT
        self.ot_widget = OTWindow(is_dialog=False, stylesheet=stylesheet) 
        self.stacked_widget.addWidget(self.ot_widget) # Índice 1
        
        # 3. Ventana de Partes
        self.parts_widget = PartsListWindow(is_dialog=False, stylesheet=stylesheet)
        self.stacked_widget.addWidget(self.parts_widget) # Índice 2
        
        # 4. Ventana de VIN
        self.vin_widget = VINLookupWindow(is_dialog=False, stylesheet=stylesheet)
        self.stacked_widget.addWidget(self.vin_widget) # Índice 3

        # 5. Ventana de Asesores 
        self.advisor_widget = AdvisorListWindow(is_dialog=False, stylesheet=stylesheet)
        self.stacked_widget.addWidget(self.advisor_widget) # Índice 4

        # 3. CREACIÓN DE MENÚS DESPUÉS DE LOS WIDGETS
        self.ot_menu = self.create_ot_menu(stylesheet) 
        self.parts_menu = self.create_parts_menu(stylesheet)
        self.vin_menu = self.create_vin_menu(stylesheet)
        self.advisor_filter_menu = self.create_advisor_filter_menu(stylesheet)
        
        # Conectar los botones a sus menús
        ot_button.clicked.connect(lambda: self.show_dropdown_menu(ot_button, self.ot_menu))
        parts_button.clicked.connect(lambda: self.show_dropdown_menu(parts_button, self.parts_menu))
        vin_button.clicked.connect(lambda: self.show_dropdown_menu(vin_button, self.vin_menu))
        advisor_button.clicked.connect(lambda: self.show_dropdown_menu(advisor_button, self.advisor_filter_menu))
        
        # Añadir todos los widgets al layout principal
        main_layout.addWidget(header_widget)
        main_layout.addWidget(self.stacked_widget)
        
        self.change_view("home")

    def show_dropdown_menu(self, button, menu):
        """Muestra el QMenu debajo del botón."""
        
        if self.nav_buttons.get("home") and self.nav_buttons["home"].isChecked():
            self.nav_buttons["home"].setChecked(False)
            
        if menu == self.advisor_filter_menu:
            self.update_advisor_filter_menu()
            
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def change_view(self, view_name):
        """Cambia la vista en el QStackedWidget y actualiza el estado del botón."""
        
        self.nav_buttons["home"].setChecked(view_name == "home")
        
        view_map = {
            "home": 0,
            "ot_list": 1,
            "parts_list": 2,
            "vin_lookup": 3,
            "advisor_list": 4
        }
        
        index = view_map.get(view_name)
        if index is not None:
            self.stacked_widget.setCurrentIndex(index)
            
            if view_name == "ot_list":
                self.ot_widget.load_ot_data()
            elif view_name == "parts_list":
                self.parts_widget.load_parts_data()
            elif view_name == "advisor_list":
                self.advisor_widget.load_advisor_data()
                
    def apply_advisor_filter(self, advisor_name=None):
        """Aplica un filtro de OTs por el nombre del asesor."""
        self.change_view("ot_list")
        self.ot_widget.load_ot_data(filter_advisor=advisor_name)
        
        if advisor_name:
             QMessageBox.information(self, "Filtro Aplicado", f"Mostrando OTs asociadas al asesor: {advisor_name}")
        else:
             QMessageBox.information(self, "Filtro Eliminado", "Mostrando todas las OTs.")


    def create_ot_menu(self, stylesheet):
        """Crea el menú desplegable para Órdenes de Trabajo."""
        menu = QMenu(self)
        menu.setStyleSheet(stylesheet)
        
        action_list = menu.addAction("Ver Todas las OTs")
        action_list.triggered.connect(lambda: self.apply_advisor_filter(None))
        
        action_add = menu.addAction("➕ Agregar Nueva OT")
        action_add.triggered.connect(self.ot_widget.add_new_ot)
        
        action_pending = menu.addAction("OTs Pendientes de Partes")
        action_pending.triggered.connect(lambda: (self.change_view("ot_list"), QMessageBox.information(self, "Filtro", "Se ha aplicado el filtro de OTs Pendientes.")))
        
        menu.addSeparator()
        
        action_add_advisor = menu.addAction("👤 Registrar Asesor")
        action_add_advisor.triggered.connect(self.add_new_advisor)
        
        action_advisors = menu.addAction("👥 Ver Listado de Asesores") 
        action_advisors.triggered.connect(lambda: self.change_view("advisor_list"))
        
        return menu

    def create_advisor_filter_menu(self, stylesheet):
        """Crea el menú dinámico para filtrar OTs por Asesor."""
        menu = QMenu(self)
        menu.setStyleSheet(stylesheet)
        
        self.update_advisor_filter_menu(menu) 
        
        return menu

    def update_advisor_filter_menu(self, menu=None):
        """Puebla el menú de filtro con la lista actual de asesores."""
        if menu is None:
            menu = self.advisor_filter_menu
            
        menu.clear()
        
        action_all = menu.addAction("Mostrar Todas las OTs")
        action_all.triggered.connect(lambda: self.apply_advisor_filter(None))
        menu.addSeparator()
        
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM advisors ORDER BY name")
        advisors = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not advisors:
            menu.addAction("No hay asesores registrados")
        else:
            for advisor in advisors:
                action = menu.addAction(advisor)
                action.triggered.connect(lambda checked, a=advisor: self.apply_advisor_filter(a))

    def create_parts_menu(self, stylesheet):
        """Crea el menú desplegable para Partes."""
        menu = QMenu(self)
        menu.setStyleSheet(stylesheet)
        
        action_list = menu.addAction("Ver Listado de Partes")
        action_list.triggered.connect(lambda: self.change_view("parts_list"))
        
        action_add = menu.addAction("➕ Agregar Nueva Parte")
        action_add.triggered.connect(self.parts_widget.add_new_part)
        
        action_search = menu.addAction("🔍 Buscar por No. de Parte")
        action_search.triggered.connect(lambda: (self.change_view("parts_list"), QMessageBox.information(self, "Búsqueda", "Lógica para abrir la barra de búsqueda rápida aquí.")))
        
        return menu

    def create_vin_menu(self, stylesheet):
        """Crea el menú desplegable para VIN/Vehículos."""
        menu = QMenu(self)
        menu.setStyleSheet(stylesheet)
        
        action_search = menu.addAction("🔍 Buscar por VIN/OT")
        action_search.triggered.connect(lambda: self.change_view("vin_lookup"))
        
        menu.addSeparator()
        
        action_add_vin = menu.addAction("🚗 Registrar Nuevo Vehículo")
        action_add_vin.triggered.connect(self.add_new_vin)
        
        return menu
    
    def setup_home_widget(self, widget):
        """Configura la vista de la ventana principal/inicio."""
        content_layout = QVBoxLayout(widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        company_logo = QLabel()
        pixmap = QPixmap('https://placehold.co/800x400/3498db/ffffff?text=Logo+de+la+Empresa') 
        company_logo.setPixmap(pixmap)
        company_logo.setScaledContents(True)
        company_logo.setFixedSize(800, 400)
        
        content_layout.addWidget(company_logo)

    def setup_placeholder_widget(self, widget, title):
        """Crea un widget de marcador de posición para nuevas vistas."""
        layout = QVBoxLayout(widget)
        title_label = QLabel(title)
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        layout.addStretch()

    def add_new_vin(self):
        """Abre la ventana para agregar un nuevo VIN."""
        add_vin_window = AddVINWindow(self.styleSheet())
        if add_vin_window.exec() == QDialog.DialogCode.Accepted:
            self.update_advisor_filter_menu()
            # Si se crea un nuevo VIN y OT, recargamos la lista de OTs
            if self.stacked_widget.currentIndex() == 1: # Índice de OTWindow
                self.ot_widget.load_ot_data()
        
    def add_new_advisor(self):
        """Abre la ventana para agregar un nuevo Asesor."""
        add_advisor_window = AddAdvisorWindow(self.styleSheet())
        if add_advisor_window.exec() == QDialog.DialogCode.Accepted:
            if self.stacked_widget.currentIndex() == 4:
                self.advisor_widget.load_advisor_data()
            self.update_advisor_filter_menu()


# --- CLASES DE VISTA Y DIÁLOGO (sin cambios relevantes) ---
class OTWindow(QWidget):
    # ... (código sin cambios relevantes para este cambio) ...
    def __init__(self, is_dialog=True, stylesheet=""):
        super().__init__()
        self.is_dialog = is_dialog
        if self.is_dialog:
            self.setWindowTitle("Órdenes de Trabajo")
            self.setGeometry(100, 50, 800, 600)
            self.setStyleSheet(stylesheet)

        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Órdenes de Trabajo por Asesor")
        self.title_label.setObjectName("title_label")
        add_ot_button = QPushButton("Agregar OT")
        add_ot_button.setObjectName("add_button")
        add_ot_button.clicked.connect(self.add_new_ot)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(add_ot_button)
        
        layout.addLayout(header_layout)
        
        self.ot_table = QTableWidget()
        self.ot_table.setColumnCount(6)
        self.ot_table.setHorizontalHeaderLabels([
            "OT", "Asesor de Ventas", "No. de Piezas", "Fecha de Pedido", "Seguro", "Estado"
        ])
        
        self.load_ot_data()
        
        layout.addWidget(self.ot_table)
        
        if self.is_dialog:
            self.setLayout(layout)

    def load_ot_data(self, filter_advisor=None):
        """Carga los datos de las OTs desde la base de datos, con opción de filtro."""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        base_query = """
        SELECT o.ot_number, o.sales_advisor, o.request_date, o.status,
               v.insurance, COUNT(op.part_id) as total_parts
        FROM ots AS o
        LEFT JOIN ot_parts AS op ON o.id = op.ot_id
        LEFT JOIN vins AS v ON o.vin = v.vin
        """
        where_clause = ""
        params = []
        
        if filter_advisor:
            where_clause = " WHERE o.sales_advisor = ?"
            params.append(filter_advisor)
            self.title_label.setText(f"Órdenes de Trabajo - Filtrado por: {filter_advisor}")
        else:
            self.title_label.setText("Órdenes de Trabajo por Asesor")

        group_by_clause = " GROUP BY o.id"
        
        cursor.execute(base_query + where_clause + group_by_clause, params)
        ots_data = cursor.fetchall()
        conn.close()
        
        self.ot_table.setRowCount(len(ots_data))
        for row_idx, row_data in enumerate(ots_data):
            self.ot_table.setItem(row_idx, 0, QTableWidgetItem(row_data[0]))
            self.ot_table.setItem(row_idx, 1, QTableWidgetItem(row_data[1]))
            self.ot_table.setItem(row_idx, 2, QTableWidgetItem(str(row_data[5])))
            self.ot_table.setItem(row_idx, 3, QTableWidgetItem(row_data[2]))
            self.ot_table.setItem(row_idx, 4, QTableWidgetItem(row_data[4] or "N/A"))
            self.ot_table.setItem(row_idx, 5, QTableWidgetItem(row_data[3]))
        
        self.ot_table.resizeColumnsToContents()
        self.ot_table.setSortingEnabled(True)

    def add_new_ot(self):
        """Abre la ventana para agregar una nueva OT."""
        stylesheet = self.styleSheet() if self.is_dialog else self.parent().styleSheet()
        add_ot_window = AddOTWindow(stylesheet)
        if add_ot_window.exec() == QDialog.DialogCode.Accepted:
            self.load_ot_data()

class PartsListWindow(QWidget):
    # ... (código sin cambios relevantes para este cambio) ...
    def __init__(self, is_dialog=True, stylesheet=""):
        super().__init__()
        self.is_dialog = is_dialog
        if self.is_dialog:
            self.setWindowTitle("Lista de Partes")
            self.setGeometry(100, 50, 600, 500)
            self.setStyleSheet(stylesheet)
        
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        title_label = QLabel("Lista de Partes")
        title_label.setObjectName("title_label")
        add_part_button = QPushButton("Agregar Parte")
        add_part_button.setObjectName("add_button")
        add_part_button.clicked.connect(self.add_new_part)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(add_part_button)
        
        layout.addLayout(header_layout)

        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(2)
        self.parts_table.setHorizontalHeaderLabels(["No. de Parte", "Nombre"])
        
        self.load_parts_data()
        
        layout.addWidget(self.parts_table)
        
        if self.is_dialog:
            self.setLayout(layout)
        
    def load_parts_data(self):
        """Carga los datos de las partes desde la base de datos."""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT part_number, part_name FROM parts")
        parts_data = cursor.fetchall()
        conn.close()
        
        self.parts_table.setRowCount(len(parts_data))
        for row_idx, row_data in enumerate(parts_data):
            self.parts_table.setItem(row_idx, 0, QTableWidgetItem(row_data[0]))
            self.parts_table.setItem(row_idx, 1, QTableWidgetItem(row_data[1]))
            
        self.parts_table.resizeColumnsToContents()

    def add_new_part(self):
        """Abre la ventana para agregar una nueva parte."""
        stylesheet = self.styleSheet() if self.is_dialog else self.parent().styleSheet()
        add_part_window = AddPartWindow(stylesheet)
        if add_part_window.exec() == QDialog.DialogCode.Accepted:
            self.load_parts_data()

class VINLookupWindow(QWidget):
    # ... (código sin cambios relevantes para este cambio) ...
    def __init__(self, is_dialog=True, stylesheet=""):
        super().__init__()
        self.is_dialog = is_dialog
        if self.is_dialog:
            self.setWindowTitle("Búsqueda por OT")
            self.setGeometry(100, 50, 700, 600)
            self.setStyleSheet(stylesheet)
        
        layout = QVBoxLayout(self)
        title_label = QLabel("Búsqueda de Información por OT")
        title_label.setObjectName("title_label")
        layout.addWidget(title_label)
        
        search_layout = QHBoxLayout()
        self.ot_input = QLineEdit()
        self.ot_input.setPlaceholderText("Ingrese el número de OT")
        self.search_button = QPushButton("Buscar")
        self.search_button.clicked.connect(self.search_ot)
        
        search_layout.addWidget(self.ot_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)
        
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_container.setVisible(False)
        
        layout.addWidget(self.results_container)

        if self.is_dialog:
            self.setLayout(layout)

    def search_ot(self):
        """Busca y muestra la información relacionada con la OT."""
        ot_number = self.ot_input.text()
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        query = """
        SELECT o.vin, v.model, v.year, v.insurance, v.owner_name, v.owner_email, v.owner_phone, o.sales_advisor
        FROM ots AS o
        LEFT JOIN vins AS v ON o.vin = v.vin
        WHERE o.ot_number = ?
        """
        cursor.execute(query, (ot_number,))
        result = cursor.fetchone()
        conn.close()
        
        # Limpiar el contenedor de resultados
        for i in reversed(range(self.results_layout.count())):
            widget = self.results_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if result:
            self.results_container.setVisible(True)
            labels_data = [
                ("VIN", result[0]),
                ("Modelo", result[1]),
                ("Año", str(result[2])),
                ("Seguro", result[3]),
                ("Propietario", result[4]),
                ("Correo", result[5]),
                ("Teléfono", result[6]),
                ("Asesor (OT)", result[7])
            ]
            
            for label_text, data in labels_data:
                info_label = QLabel(f"<span style='font-weight: bold;'>{label_text}:</span> {data}")
                info_label.setStyleSheet("font-size: 14px; margin-bottom: 5px;")
                self.results_layout.addWidget(info_label)
        else:
            self.results_container.setVisible(False)
            QMessageBox.warning(self, "No se encontró", "No se encontró ninguna OT con ese número.")

class AdvisorListWindow(QWidget):
    # ... (código sin cambios relevantes para este cambio) ...
    def __init__(self, is_dialog=True, stylesheet=""):
        super().__init__()
        self.is_dialog = is_dialog
        if self.is_dialog:
            self.setWindowTitle("Lista de Asesores de Venta")
            self.setGeometry(100, 50, 600, 500)
            self.setStyleSheet(stylesheet)
        
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        title_label = QLabel("Listado de Asesores de Venta")
        title_label.setObjectName("title_label")
        
        add_advisor_button = QPushButton("Agregar Asesor")
        add_advisor_button.setObjectName("add_button")
        add_advisor_button.clicked.connect(self.add_new_advisor_dialog)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(add_advisor_button)
        
        layout.addLayout(header_layout)

        self.advisor_table = QTableWidget()
        self.advisor_table.setColumnCount(1)
        self.advisor_table.setHorizontalHeaderLabels(["Nombre del Asesor"])
        
        self.load_advisor_data()
        
        layout.addWidget(self.advisor_table)
        
        if self.is_dialog:
            self.setLayout(layout)

    def load_advisor_data(self):
        """Carga los nombres de los asesores desde la base de datos."""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM advisors ORDER BY name")
        advisor_data = cursor.fetchall()
        conn.close()
        
        self.advisor_table.setRowCount(len(advisor_data))
        for row_idx, row_data in enumerate(advisor_data):
            self.advisor_table.setItem(row_idx, 0, QTableWidgetItem(row_data[0]))
            
        self.advisor_table.resizeColumnsToContents()
        self.advisor_table.setSortingEnabled(True)

    def add_new_advisor_dialog(self):
        """Abre la ventana para agregar un nuevo asesor."""
        stylesheet = self.styleSheet() if self.is_dialog else self.parent().styleSheet()
        add_advisor_window = AddAdvisorWindow(stylesheet)
        if add_advisor_window.exec() == QDialog.DialogCode.Accepted:
            self.load_advisor_data()
            if not self.is_dialog and isinstance(self.parent(), MainWindow):
                self.parent().update_advisor_filter_menu()
                
# --- CLASES DE DIÁLOGO (AÑADIR) ---

class AddOTWindow(QDialog):
    # ... (código sin cambios relevantes para este cambio) ...
    def __init__(self, stylesheet):
        super().__init__()
        self.setWindowTitle("Agregar Nueva OT")
        self.setGeometry(150, 150, 400, 350)
        self.setStyleSheet(stylesheet)
        
        layout = QVBoxLayout()
        title_label = QLabel("Registrar Nueva OT")
        title_label.setObjectName("title_label")
        layout.addWidget(title_label)
        
        layout.addWidget(QLabel("Número de OT:"))
        self.ot_number_input = QLineEdit()
        layout.addWidget(self.ot_number_input)
        
        layout.addWidget(QLabel("Asesor de Ventas:"))
        self.ot_advisor_input = QComboBox() 
        self.load_advisors()
        layout.addWidget(self.ot_advisor_input)
        
        layout.addWidget(QLabel("VIN:"))
        self.ot_vin_input = QLineEdit()
        layout.addWidget(self.ot_vin_input)

        layout.addWidget(QLabel("Estado:"))
        self.ot_status_input = QComboBox()
        self.ot_status_input.addItems(["Pendiente", "Pedida", "Entregada"])
        layout.addWidget(self.ot_status_input)
        
        save_button = QPushButton("Guardar OT")
        save_button.clicked.connect(self.save_ot)
        
        layout.addStretch()
        layout.addWidget(save_button)
        self.setLayout(layout)

    def load_advisors(self):
        """Carga los nombres de los asesores desde la base de datos."""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM advisors ORDER BY name")
        advisors = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not advisors:
             self.ot_advisor_input.addItem("Sin Asesores Registrados")
        else:
            self.ot_advisor_input.addItems(advisors)

    def save_ot(self):
        """Guarda la nueva OT en la base de datos."""
        ot_number = self.ot_number_input.text()
        advisor = self.ot_advisor_input.currentText()
        vin = self.ot_vin_input.text()
        status = self.ot_status_input.currentText()
        
        if advisor == "Sin Asesores Registrados":
            QMessageBox.warning(self, "Error", "Debe registrar un asesor primero.")
            return

        if not ot_number or not vin:
            QMessageBox.warning(self, "Error", "Los campos Número de OT y VIN son obligatorios.")
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT vin FROM vins WHERE vin = ?", (vin,))
            if cursor.fetchone() is None:
                QMessageBox.warning(self, "Advertencia", f"El VIN '{vin}' no existe en la base de datos de vehículos. Por favor, añádelo primero o verifica.")
                return

            cursor.execute("INSERT INTO ots (ot_number, sales_advisor, vin, status, request_date) VALUES (?, ?, ?, ?, DATE('now'))",
                           (ot_number, advisor, vin, status))
            conn.commit()
            QMessageBox.information(self, "Éxito", "OT agregada correctamente.")
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "El número de OT ya existe.")
        finally:
            conn.close()

class AddPartWindow(QDialog):
    """Ventana para agregar una nueva parte.
       MODIFICADA: Ahora incluye campo de búsqueda para la OT.
    """
    def __init__(self, stylesheet):
        super().__init__()
        self.all_ots = [] # Almacena todas las OTs cargadas
        self.ot_data = {} # Para almacenar ID y número de OT (mapeo)
        self.setWindowTitle("Agregar Parte a Orden de Trabajo")
        self.setGeometry(150, 150, 450, 450)
        self.setStyleSheet(stylesheet)
        
        layout = QVBoxLayout()
        title_label = QLabel("Registrar Nueva Parte y Asociar a OT")
        title_label.setObjectName("title_label")
        layout.addWidget(title_label)
        
        # --- Búsqueda y Selección de OT ---
        ot_selection_group = QWidget()
        ot_selection_layout = QHBoxLayout(ot_selection_group)
        ot_selection_layout.setContentsMargins(0, 0, 0, 0)
        
        # Etiqueta y campo de búsqueda
        search_label = QLabel("Buscar OT:")
        self.ot_search_input = QLineEdit()
        self.ot_search_input.setPlaceholderText("Escribe No. de OT o VIN...")
        self.ot_search_input.textChanged.connect(self.filter_ots) # Conectar al filtro

        # ComboBox para la selección final de la OT
        self.ot_combo = QComboBox()
        
        ot_selection_layout.addWidget(search_label)
        ot_selection_layout.addWidget(self.ot_search_input)
        
        layout.addWidget(QLabel("Orden de Trabajo (OT) Seleccionada:"))
        layout.addWidget(self.ot_combo)
        layout.addWidget(ot_selection_group)

        self.load_ots() # Cargar todas las OTs al inicio
        
        # --- Campos de la Parte ---
        layout.addWidget(QLabel("Número de Parte:"))
        self.part_number_input = QLineEdit()
        layout.addWidget(self.part_number_input)
        
        layout.addWidget(QLabel("Nombre de la Parte:"))
        self.part_name_input = QLineEdit()
        layout.addWidget(self.part_name_input)
        
        # --- Cantidad y Estado ---
        layout.addWidget(QLabel("Cantidad Requerida:"))
        self.quantity_input = QLineEdit("1")
        self.quantity_input.setValidator(QIntValidator())
        layout.addWidget(self.quantity_input)
        
        layout.addWidget(QLabel("Estado de la Parte (en OT):"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Pendiente", "Pedida", "Recibida"])
        layout.addWidget(self.status_combo)
        
        save_button = QPushButton("Guardar Parte y Asociar a OT")
        save_button.setObjectName("add_button")
        save_button.clicked.connect(self.save_part)
        
        layout.addStretch()
        layout.addWidget(save_button)
        self.setLayout(layout)

    def load_ots(self):
        """Carga TODAS las OTs disponibles al inicio, incluyendo el VIN para mostrar."""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        # Obtener ID, número de OT y VIN
        cursor.execute("SELECT id, ot_number, vin FROM ots ORDER BY id DESC") 
        ots = cursor.fetchall()
        conn.close()
        
        self.ot_data = {}
        self.all_ots = []
        
        for ot_id, ot_num, vin in ots:
            display_text = f"{ot_num} (VIN: {vin})"
            self.ot_data[display_text] = ot_id
            self.all_ots.append(display_text)
            
        self.filter_ots() # Rellenar el ComboBox con todas las OTs inicialmente

    def filter_ots(self):
        """Filtra los ítems del ComboBox basados en el texto de búsqueda."""
        search_text = self.ot_search_input.text().lower()
        self.ot_combo.clear()
        
        filtered_ots = [ot for ot in self.all_ots if search_text in ot.lower()]
        
        if filtered_ots:
            self.ot_combo.addItems(filtered_ots)
        else:
            self.ot_combo.addItem("No se encontraron OTs")

    def save_part(self):
        """Guarda la nueva parte y la asocia a la OT seleccionada en la tabla ot_parts."""
        part_number = self.part_number_input.text()
        part_name = self.part_name_input.text()
        quantity_text = self.quantity_input.text()
        status = self.status_combo.currentText()
        ot_display_text = self.ot_combo.currentText()
        
        # Validación de que una OT válida esté seleccionada
        if not ot_display_text or ot_display_text == "No se encontraron OTs":
            QMessageBox.warning(self, "Error", "Debe seleccionar una Orden de Trabajo válida.")
            return

        if not (part_number and part_name and quantity_text):
            QMessageBox.warning(self, "Error", "Todos los campos de la parte son obligatorios.")
            return
            
        try:
            quantity = int(quantity_text)
        except ValueError:
            QMessageBox.warning(self, "Error", "La cantidad debe ser un número entero.")
            return
            
        ot_id = self.ot_data.get(ot_display_text) # Obtener el ID de la OT
        if ot_id is None:
            QMessageBox.critical(self, "Error", "No se pudo obtener el ID de la OT seleccionada. Intente recargar.")
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        try:
            # 1. Intentar registrar la parte si no existe
            cursor.execute("SELECT id FROM parts WHERE part_number = ?", (part_number,))
            part_result = cursor.fetchone()

            if part_result:
                part_id = part_result[0]
            else:
                # La parte no existe, la insertamos
                cursor.execute("INSERT INTO parts (part_number, part_name) VALUES (?, ?)",
                               (part_number, part_name))
                part_id = cursor.lastrowid
                
            # 2. Asociar la parte a la OT en la tabla ot_parts
            # Usamos INSERT OR REPLACE para actualizar si ya se registró antes
            cursor.execute("""
                INSERT OR REPLACE INTO ot_parts (ot_id, part_id, quantity, status) 
                VALUES (?, ?, ?, ?)
            """, (ot_id, part_id, quantity, status))
            
            conn.commit()
            
            QMessageBox.information(self, "Éxito", f"Parte '{part_name}' asociada a la OT {ot_display_text} con cantidad {quantity}.")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al guardar o asociar: {e}")
            conn.rollback()
        finally:
            conn.close()

# ... (Resto de clases AddVINWindow, AddAdvisorWindow, etc., sin cambios relevantes) ...

class AddVINWindow(QDialog):
    # ... (código sin cambios relevantes para este cambio) ...
    def __init__(self, stylesheet):
        super().__init__()
        self.setWindowTitle("Registrar Nuevo Vehículo (VIN)")
        self.setGeometry(150, 150, 450, 450)
        self.setStyleSheet(stylesheet)
        
        layout = QGridLayout()
        
        title_label = QLabel("Registrar Vehículo y Propietario")
        title_label.setObjectName("title_label")
        layout.addWidget(title_label, 0, 0, 1, 2)
        
        layout.addWidget(QLabel("VIN:"), 1, 0)
        self.vin_input = QLineEdit()
        layout.addWidget(self.vin_input, 1, 1)

        layout.addWidget(QLabel("Modelo:"), 2, 0)
        self.model_input = QLineEdit()
        layout.addWidget(self.model_input, 2, 1)

        layout.addWidget(QLabel("Año:"), 3, 0)
        self.year_input = QLineEdit()
        self.year_input.setInputMask("9999")
        layout.addWidget(self.year_input, 3, 1)
        
        layout.addWidget(QLabel("Seguro:"), 4, 0)
        self.insurance_input = QLineEdit()
        layout.addWidget(self.insurance_input, 4, 1)

        layout.addWidget(QLabel("Asesor de Venta:"), 5, 0)
        self.advisor_input = QComboBox()
        self.load_advisors()
        layout.addWidget(self.advisor_input, 5, 1)

        layout.addWidget(QLabel("Propietario:"), 6, 0)
        self.owner_name_input = QLineEdit()
        layout.addWidget(self.owner_name_input, 6, 1)
        
        layout.addWidget(QLabel("Email:"), 7, 0)
        self.owner_email_input = QLineEdit()
        layout.addWidget(self.owner_email_input, 7, 1)

        layout.addWidget(QLabel("Teléfono:"), 8, 0)
        self.owner_phone_input = QLineEdit()
        layout.addWidget(self.owner_phone_input, 8, 1)
        
        save_button = QPushButton("Guardar Vehículo y Crear OT")
        save_button.clicked.connect(self.save_vin)
        save_button.setObjectName("add_button")
        
        layout.addWidget(save_button, 9, 0, 1, 2)
        
        self.setLayout(layout)

    def load_advisors(self):
        """Carga los nombres de los asesores desde la base de datos."""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM advisors ORDER BY name")
        advisors = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not advisors:
             self.advisor_input.addItem("Sin Asesores Registrados")
        else:
            self.advisor_input.addItems(advisors)

    def _generate_ot_number(self, cursor):
        """Genera un nuevo número de OT basado en el último ID de la tabla."""
        cursor.execute("SELECT MAX(id) FROM ots")
        last_id = cursor.fetchone()[0]
        new_id = (last_id or 0) + 1
        return f"OT-{new_id:04d}" # Formato OT-000X

    def save_vin(self):
        """Guarda el nuevo VIN y automáticamente crea una OT asociada."""
        vin = self.vin_input.text()
        model = self.model_input.text()
        year = self.year_input.text()
        insurance = self.insurance_input.text()
        sales_advisor = self.advisor_input.currentText()
        owner_name = self.owner_name_input.text()
        owner_email = self.owner_email_input.text()
        owner_phone = self.owner_phone_input.text()

        if sales_advisor == "Sin Asesores Registrados":
            QMessageBox.warning(self, "Error", "Debe registrar un asesor primero.")
            return

        if not (vin and model and year and owner_name):
            QMessageBox.warning(self, "Error", "Los campos VIN, Modelo, Año y Propietario son obligatorios.")
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        try:
            # 1. INTENTA GUARDAR EL VIN
            cursor.execute("INSERT INTO vins (vin, model, year, insurance, sales_advisor, owner_name, owner_email, owner_phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (vin, model, year, insurance, sales_advisor, owner_name, owner_email, owner_phone))
            
            # 2. CREAR LA OT POR DEFECTO
            ot_number = self._generate_ot_number(cursor)
            ot_status = "Pendiente" 
            
            cursor.execute("INSERT INTO ots (ot_number, sales_advisor, vin, status, request_date) VALUES (?, ?, ?, ?, DATE('now'))",
                           (ot_number, sales_advisor, vin, ot_status))
                           
            conn.commit()
            
            QMessageBox.information(self, "Éxito", f"Vehículo registrado correctamente. Se creó la Orden de Trabajo: {ot_number}")
            self.accept()
            
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "El VIN ya existe en la base de datos o hubo un error al crear la OT.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al guardar: {e}")
        finally:
            conn.close()

class AddAdvisorWindow(QDialog):
    # ... (código sin cambios relevantes para este cambio) ...
    def __init__(self, stylesheet):
        super().__init__()
        self.setWindowTitle("Registrar Nuevo Asesor")
        self.setGeometry(150, 150, 400, 200)
        self.setStyleSheet(stylesheet)
        
        layout = QVBoxLayout()
        title_label = QLabel("Registrar Asesor de Ventas")
        title_label.setObjectName("title_label")
        layout.addWidget(title_label)
        
        layout.addWidget(QLabel("Nombre Completo del Asesor:"))
        self.advisor_name_input = QLineEdit()
        layout.addWidget(self.advisor_name_input)
        
        save_button = QPushButton("Guardar Asesor")
        save_button.clicked.connect(self.save_advisor)
        
        layout.addStretch()
        layout.addWidget(save_button)
        self.setLayout(layout)

    def save_advisor(self):
        """Guarda el nuevo asesor en la base de datos."""
        advisor_name = self.advisor_name_input.text()

        if not advisor_name:
            QMessageBox.warning(self, "Error", "El nombre del asesor es obligatorio.")
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO advisors (name) VALUES (?)", (advisor_name,))
            conn.commit()
            QMessageBox.information(self, "Éxito", "Asesor agregado correctamente.")
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "El nombre del asesor ya existe.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al guardar: {e}")
        finally:
            conn.close()


# --- Punto de entrada de la aplicación ---
if __name__ == "__main__":
    setup_database()
    app = QApplication(sys.argv)
    
    STYLESHEET = load_stylesheet()
    
    login_window = LoginWindow(STYLESHEET)
    if login_window.exec() == QDialog.DialogCode.Accepted:
        main_window = MainWindow(STYLESHEET)
        main_window.show()
        sys.exit(app.exec())