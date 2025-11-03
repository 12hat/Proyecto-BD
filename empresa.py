import sys
import os
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QStackedWidget, QTableWidget, 
    QTableWidgetItem, QDialog, QMessageBox, QComboBox, QMenu, QGridLayout,
    QHeaderView
)
from PyQt6.QtGui import QPixmap, QIntValidator
from PyQt6.QtCore import Qt
from datetime import date 

# --- Configuración de la base de datos ---
# Base path for resources and database.
# When packaged with PyInstaller (--onefile), sys.frozen is True and
# the executable lives outside the source tree. Use the directory of
# the executable as the base path so the bundled exe is portable.
if getattr(sys, 'frozen', False):
    # Cuando está congelado por PyInstaller, sys.argv[0] apunta al ejecutable original
    # (la ubicación del .exe). Usamos eso para que la .db se cree junto al .exe.
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

DATABASE_NAME = os.path.join(base_path, "empresa.db")

def setup_database():
    """Configura las tablas iniciales de la base de datos y añade datos iniciales."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # TABLA USERS con ROLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'user' 
        )
    """)
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    except sqlite3.OperationalError:
         pass

    # Tablas restantes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advisors (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ots (
            id INTEGER PRIMARY KEY, ot_number TEXT NOT NULL UNIQUE, sales_advisor TEXT,
            vin TEXT, status TEXT, request_date TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parts (id INTEGER PRIMARY KEY, part_number TEXT NOT NULL UNIQUE, part_name TEXT)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ot_parts (
            ot_id INTEGER, part_id INTEGER, quantity INTEGER, status TEXT,
            FOREIGN KEY(ot_id) REFERENCES ots(id), FOREIGN KEY(part_id) REFERENCES parts(id),
            PRIMARY KEY (ot_id, part_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vins (
            vin TEXT PRIMARY KEY, model TEXT, year INTEGER, insurance TEXT, owner_name TEXT,
            owner_email TEXT, owner_phone TEXT, sales_advisor TEXT
        )
    """)
    try:
        cursor.execute("ALTER TABLE vins ADD COLUMN sales_advisor TEXT")
    except sqlite3.OperationalError:
         pass 
            
    # --- Datos de prueba ---
    cursor.execute("INSERT OR IGNORE INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)", 
                    ('admin', 'password', 'Administrador', 'admin'))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)", 
                    ('user1', 'pass', 'Usuario Estándar', 'user'))

    cursor.execute("INSERT OR IGNORE INTO advisors (name) VALUES (?)", ('Laura Gómez',))
    cursor.execute("INSERT OR IGNORE INTO advisors (name) VALUES (?)", ('Juan Pérez',))

    cursor.execute("""
        INSERT OR IGNORE INTO vins (vin, model, year, insurance, owner_name, owner_email, owner_phone, sales_advisor) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ('VIN1234567890', 'Tesla Model 3', 2023, 'Seguros Nacionales', 'Carlos Ruíz', 'carlos@email.com', '5512345678', 'Laura Gómez'))
    cursor.execute("""
        INSERT OR IGNORE INTO vins (vin, model, year, insurance, owner_name, owner_email, owner_phone, sales_advisor) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

# ----------------------------------------------------------------------
# --- FUNCIONES AUXILIARES ---
# ----------------------------------------------------------------------

def load_stylesheet(filename="estilo.css"):
    """Carga los estilos CSS desde un archivo dentro de la carpeta del ejecutable o del proyecto.

    Si se ejecuta como exe, busca en `base_path`. Devuelve una cadena vacía si no existe.
    """
    # si el filename es absoluto, úsalo tal cual, si no, búscalo en base_path
    path = filename if os.path.isabs(filename) else os.path.join(base_path, filename)
    try:
        with open(path, "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # Si está congelado y el archivo fue empaquetado con PyInstaller, buscar en _MEIPASS
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundled_path = os.path.join(sys._MEIPASS, os.path.basename(path))
            try:
                with open(bundled_path, "r", encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                pass

        # Retornar stylesheet embebida en el script para evitar depender de un archivo externo
        return DEFAULT_STYLESHEET

# --------- DEFAULT STYLESHEET EMBEBIDO (usado si no existe estilo.css externo) ----------
DEFAULT_STYLESHEET = """
/* =================================================================
   BASE Y FUENTES
   ================================================================= */

/* Fondo general de las ventanas */
QMainWindow, QDialog { 
    background-color: #F0F3F4; /* Gris Claro/Plata */
    font-family: Arial, sans-serif;
    font-size: 14px;
    color: #333333;
}

/* Campos de texto y entrada */
QLineEdit, QComboBox {
    padding: 8px;
    border: 1px solid #BDC3C7; /* Gris medio */
    border-radius: 4px;
    background-color: white;
    color: #333333; /* Texto negro para los campos de entrada */
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #1B365D; /* Azul Profundo al enfocar */
}


/* =================================================================
   CABECERA Y NAVEGACIÓN
   ================================================================= */

/* Contenedor de botones de navegación (La franja de arriba) */
#header_buttons_container {
    background-color: #1B365D; /* Azul Profundo/Marino */
    padding: 0;
}

/* Botones de navegación (Inicio, Ordenes, Partes, etc.) */
QPushButton { 
    background-color: #1B365D;
    color: white; 
    border: none; 
    padding: 12px 15px; /* Más padding para que sean más anchos */
    border-radius: 0px; 
    font-weight: bold;
    min-width: 120px;
    margin: 0;
}

/* Efecto al pasar el mouse por los botones de navegación */
QPushButton:hover { 
    background-color: #294D75; /* Tono de azul ligeramente más claro */
}

/* Botón activo/seleccionado (resaltado con color corporativo) */
QPushButton:checked { 
    background-color: #16A085; /* Verde azulado que contrasta con el azul */
    border-bottom: 3px solid #E74C3C; /* Línea roja de acento */
    font-weight: bold;
}


/* =================================================================
   BOTONES DE ACCIÓN ESPECIALES
   ================================================================= */

/* Botón de "Agregar" / "Guardar" / "Aceptar" (Acción Positiva) */
#add_button { 
    background-color: #27AE60; /* Verde Éxito */
    color: white;
    border-radius: 5px;
    margin: 5px;
    padding: 10px 20px;
}
#add_button:hover { 
    background-color: #1F8E4E; 
}

/* Botón de "Administración" y "Cerrar Sesión" (Acción Crítica o de Salida) */
#admin_button, QPushButton[text="🚪 Cerrar Sesión"] {
    background-color: #E74C3C; /* Rojo Alerta */
    font-weight: bold;
    border-radius: 0px;
}
#admin_button:hover, QPushButton[text="🚪 Cerrar Sesión"]:hover { 
    background-color: #C0392B; 
}


/* =================================================================
   TÍTULOS Y MENÚS
   ================================================================= */

/* Títulos principales de las vistas */
#title_label { 
    font-size: 24px; 
    font-weight: bold; 
    color: #1B365D; /* Títulos en Azul Profundo */
    padding: 10px 0; 
    border-bottom: 2px solid #D5DBDB; /* Línea de separación gris sutil */
    margin-bottom: 10px;
}

/* Menús desplegables (submenús de navegación) */
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #BDC3C7;
    padding: 5px;
}
QMenu::item {
    padding: 8px 25px 8px 10px;
    color: #333333;
}
QMenu::item:selected {
    background-color: #E6EEF5; /* Gris azulado suave al seleccionar */
    color: #1B365D;
}
QMenu::separator {
    height: 1px;
    background-color: #ECF0F1;
    margin: 5px 0;
}

/* =================================================================
   TABLAS (QTableWidget)
   ================================================================= */

QTableWidget {
    background-color: white; 
    border: 1px solid #BDC3C7;
    color: #333333; /* Texto negro en las tablas */
}

/* Items de las tablas */
QTableWidget::item {
    color: #333333; /* Texto negro en las celdas */
    padding: 5px;
}

/* Cabecera de la tabla (Nombres de las columnas) */
QHeaderView::section {
    background-color: #DDE1E3; /* Gris claro */
    color: #333333;
    padding: 6px;
    border: 1px solid #BDC3C7;
    font-weight: bold;
}

/* ComboBox dentro de las celdas de la tabla (Estatus) */
QTableWidget QComboBox {
    border: 1px solid #BDC3C7;
    padding: 4px;
    color: #333333; /* Texto negro en los combobox de la tabla */
}

/* =================================================================
   MENSAJES Y DIÁLOGOS (QMessageBox, QDialog)
   ================================================================= */

/* Asegurar que todos los textos en diálogos sean negros */
QMessageBox {
    background-color: white;
    color: #333333;
}

QMessageBox QLabel {
    color: #333333; /* Texto negro en los mensajes */
}

QDialog QLabel {
    color: #333333; /* Texto negro en todos los diálogos */
}

/* Placeholder text en los campos de entrada */
QLineEdit::placeholder {
    color: #7F8C8D; /* Gris para el texto de placeholder */
}
"""

def update_ot_part_status(ot_id, part_id, new_status):
    """Actualiza el estatus de una parte específica en una OT."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE ot_parts
            SET status = ?
            WHERE ot_id = ? AND part_id = ?
        """, (new_status, ot_id, part_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar estatus de parte: {e}")
        return False
    finally:
        conn.close()

# ----------------------------------------------------------------------
# --- CLASES DE DIÁLOGO (Se mantienen sin cambios) ---
# ----------------------------------------------------------------------

class LoginWindow(QDialog):
    username_logged = ""
    user_role = ""

    def __init__(self, estilo_css):
        super().__init__()
        self.setWindowTitle("Inicio de Sesión")
        self.setFixedSize(400, 300)
        self.setStyleSheet(estilo_css)
        self.center()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel("Bienvenido")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuario")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.login_button = QPushButton("Entrar")
        self.login_button.clicked.connect(self.check_login)

        layout.addWidget(title_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        
        self.setLayout(layout)

    def center(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(int((screen.width() - self.width()) / 2), int((screen.height() - self.height()) / 2) - 100)

    def check_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            LoginWindow.username_logged = user[3]
            LoginWindow.user_role = user[4]
            QMessageBox.information(self, "Acceso exitoso", f"¡Bienvenido, {LoginWindow.username_logged} (Rol: {LoginWindow.user_role})!")
            self.accept()
        else:
            QMessageBox.warning(self, "Error de acceso", "Usuario o contraseña incorrectos.")

class AddUserDialog(QDialog):
    def __init__(self, estilo_css):
        super().__init__()
        self.setWindowTitle("Crear Nuevo Usuario")
        self.setStyleSheet(estilo_css)
        self.setGeometry(150, 150, 450, 350)
        
        layout = QGridLayout(self)
        title_label = QLabel("Registrar Nuevo Usuario")
        title_label.setObjectName("title_label")
        layout.addWidget(title_label, 0, 0, 1, 2)

        self.username_input = self._add_input(layout, "Usuario (Login):", 1)
        self.password_input = self._add_input(layout, "Contraseña:", 2)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.full_name_input = self._add_input(layout, "Nombre Completo:", 3)
        
        layout.addWidget(QLabel("Rol del Usuario:"), 4, 0)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin"])
        self.role_combo.setCurrentText("user")
        layout.addWidget(self.role_combo, 4, 1)

        save_button = QPushButton("Crear Usuario")
        save_button.clicked.connect(self.save_user)
        layout.addWidget(save_button, 5, 0, 1, 2)
        
    def _add_input(self, layout, label_text, row):
        label = QLabel(label_text)
        input_field = QLineEdit()
        layout.addWidget(label, row, 0)
        layout.addWidget(input_field, row, 1)
        return input_field

    def save_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        full_name = self.full_name_input.text().strip()
        role = self.role_combo.currentText()
        
        if not all([username, password, full_name, role]):
            QMessageBox.warning(self, "Advertencia", "Todos los campos son obligatorios.")
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO users (username, password, full_name, role)
                VALUES (?, ?, ?, ?)
            """, (username, password, full_name, role))
            
            conn.commit()
            QMessageBox.information(self, "Éxito", f"Usuario '{username}' (Rol: {role}) creado exitosamente.")
            self.accept()
        
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", f"El nombre de usuario '{username}' ya existe.")
        except Exception as e:
            QMessageBox.critical(self, "Error de DB", f"Ocurrió un error al crear el usuario: {e}")
        finally:
            conn.close()

class OTPartsDialog(QDialog):
    def __init__(self, ot_number, estilo_css=""):
        super().__init__()
        self.ot_number = ot_number
        self.estilo_css = estilo_css
        self.ot_id = self._get_ot_id(ot_number) 
        self.row_to_part_id = {} 

        self.setWindowTitle(f"Partes para OT: {ot_number}")
        self.setGeometry(200, 200, 750, 500) 
        self.setStyleSheet(estilo_css)
        
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        title_label = QLabel(f"Detalle de Partes para OT: {ot_number}")
        title_label.setObjectName("title_label")
        
        self.assign_button = QPushButton("➕ Asignar Parte de Inventario")
        self.assign_button.clicked.connect(self.open_assign_dialog)
        self.assign_button.setObjectName("add_button")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.assign_button)
        layout.addLayout(header_layout)
        
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(5)
        self.parts_table.setHorizontalHeaderLabels(["No. de Parte", "Nombre", "Cantidad", "Estado Actual", "Cambiar Estado"])
        self.parts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.load_ot_parts()
        
        self.parts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.parts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.parts_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.parts_table)
        
        
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def _get_ot_id(self, ot_number):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        result = cursor.execute("SELECT id FROM ots WHERE ot_number = ?", (ot_number,)).fetchone()
        conn.close()
        return result[0] if result else None

    def open_assign_dialog(self):
        if self.ot_id is None:
            QMessageBox.warning(self, "Error", "No se pudo encontrar la OT en la base de datos.")
            return

        assign_dialog = AssignPartsToOTDialog(self.ot_id, self.ot_number, self.estilo_css)
        if assign_dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_ot_parts()

    def load_ot_parts(self):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        query = """
        SELECT p.part_number, p.part_name, op.quantity, op.status, p.id
        FROM ot_parts AS op
        JOIN ots AS o ON o.id = op.ot_id
        JOIN parts AS p ON p.id = op.part_id
        WHERE o.ot_number = ?
        """
        cursor.execute(query, (self.ot_number,))
        parts_data = cursor.fetchall()
        conn.close()
        
        self.parts_table.setRowCount(len(parts_data))
        self.row_to_part_id.clear()
        
        part_statuses = ["Pendiente", "Pedida", "Entregada"]

        for row_idx, row_data in enumerate(parts_data):
            part_number, part_name, quantity, current_status, part_id = row_data
            
            self.row_to_part_id[row_idx] = part_id

            self.parts_table.setItem(row_idx, 0, QTableWidgetItem(part_number))
            self.parts_table.setItem(row_idx, 1, QTableWidgetItem(part_name))
            self.parts_table.setItem(row_idx, 2, QTableWidgetItem(str(quantity)))
            self.parts_table.setItem(row_idx, 3, QTableWidgetItem(current_status))

            status_combo = QComboBox(self)
            status_combo.addItems(part_statuses)
            status_combo.setCurrentText(current_status)
            
            status_combo.currentIndexChanged.connect(
                lambda index, r=row_idx, c=status_combo: self.handle_status_change(r, c.currentText())
            )
            
            self.parts_table.setCellWidget(row_idx, 4, status_combo)
            
        self.parts_table.resizeColumnsToContents()
        self.parts_table.setSortingEnabled(True)

    def handle_status_change(self, row_index, new_status):
        part_id = self.row_to_part_id.get(row_index)
        
        if not part_id or self.ot_id is None:
            QMessageBox.critical(self, "Error", "No se pudo identificar la Parte o la OT para actualizar.")
            self.load_ot_parts()
            return

        part_number_item = self.parts_table.item(row_index, 0)
        part_number = part_number_item.text() if part_number_item else "Desconocida"
        
        if update_ot_part_status(self.ot_id, part_id, new_status):
            self.parts_table.setItem(row_index, 3, QTableWidgetItem(new_status))
            QMessageBox.information(self, "Actualización Exitosa", 
                                    f"Estatus de la parte {part_number} actualizado a '{new_status}' para OT {self.ot_number}.")
        else:
            QMessageBox.critical(self, "Error de DB", "Fallo al actualizar el estatus en la base de datos.")
            self.load_ot_parts()

class AddOTWindow(QDialog):
    def __init__(self, estilo_css):
        super().__init__()
        self.setWindowTitle("Agregar Nueva OT")
        self.setGeometry(150, 150, 400, 400)
        self.setStyleSheet(estilo_css)
        
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

        layout.addWidget(QLabel("Fecha de Pedido (AAAA-MM-DD):"))
        self.ot_date_input = QLineEdit()
        self.ot_date_input.setText(date.today().strftime("%Y-%m-%d"))
        self.ot_date_input.setPlaceholderText("Ej: 2025-09-10")
        layout.addWidget(self.ot_date_input)
        
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
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM advisors ORDER BY name")
        advisors = [row[0] for row in cursor.fetchall()]
        conn.close()
        self.ot_advisor_input.addItems(advisors)
        
    def save_ot(self):
        ot_number = self.ot_number_input.text().strip()
        sales_advisor = self.ot_advisor_input.currentText()
        vin = self.ot_vin_input.text().strip()
        request_date = self.ot_date_input.text().strip()
        status = self.ot_status_input.currentText()

        if not ot_number or not sales_advisor or not vin or not request_date:
            QMessageBox.warning(self, "Advertencia", "Todos los campos (OT, Asesor, VIN y Fecha) son obligatorios.")
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT vin FROM vins WHERE vin = ?", (vin,))
            if not cursor.fetchone():
                QMessageBox.warning(self, "Error de Validación", "El VIN ingresado no existe en la base de datos de vehículos. Por favor, regístrelo primero.")
                conn.close()
                return

            cursor.execute("""
                INSERT INTO ots (ot_number, sales_advisor, vin, status, request_date)
                VALUES (?, ?, ?, ?, ?)
            """, (ot_number, sales_advisor, vin, status, request_date))
            
            conn.commit()
            QMessageBox.information(self, "Éxito", f"Orden de Trabajo {ot_number} guardada exitosamente.")
            self.accept()
        
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", f"El número de OT '{ot_number}' ya existe o faltan datos obligatorios.")
        except Exception as e:
            QMessageBox.critical(self, "Error de DB", f"Ocurrió un error al guardar la OT: {e}")
        finally:
            conn.close()

class AddVINWindow(QDialog):
    def __init__(self, estilo_css):
        super().__init__()
        self.setWindowTitle("Registrar Nuevo Vehículo (VIN)")
        self.setStyleSheet(estilo_css)
        self.setGeometry(150, 150, 500, 450)
        
        layout = QGridLayout(self)
        title_label = QLabel("Registrar Nuevo Vehículo")
        title_label.setObjectName("title_label")
        layout.addWidget(title_label, 0, 0, 1, 2)

        self.vin_input = self._add_input(layout, "VIN:", 1)
        self.model_input = self._add_input(layout, "Modelo:", 2)
        self.year_input = self._add_input(layout, "Año:", 3)
        self.year_input.setValidator(QIntValidator(1900, 2100))
        self.insurance_input = self._add_input(layout, "Aseguradora:", 4)
        self.owner_name_input = self._add_input(layout, "Propietario:", 5)
        self.owner_email_input = self._add_input(layout, "Email:", 6)
        self.owner_phone_input = self._add_input(layout, "Teléfono:", 7)
        
        layout.addWidget(QLabel("Asesor de Venta:"), 8, 0)
        self.advisor_combo = QComboBox()
        self._load_advisors_combo()
        layout.addWidget(self.advisor_combo, 8, 1)

        save_button = QPushButton("Guardar Vehículo")
        save_button.clicked.connect(self.save_vin)
        layout.addWidget(save_button, 9, 0, 1, 2)
        
    def _add_input(self, layout, label_text, row):
        label = QLabel(label_text)
        input_field = QLineEdit()
        layout.addWidget(label, row, 0)
        layout.addWidget(input_field, row, 1)
        return input_field
        
    def _load_advisors_combo(self):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM advisors ORDER BY name")
        advisors = [row[0] for row in cursor.fetchall()]
        conn.close()
        self.advisor_combo.addItems(advisors)

    def save_vin(self):
        vin = self.vin_input.text().strip().upper()
        model = self.model_input.text().strip()
        year = self.year_input.text().strip()
        insurance = self.insurance_input.text().strip()
        owner_name = self.owner_name_input.text().strip()
        owner_email = self.owner_email_input.text().strip()
        owner_phone = self.owner_phone_input.text().strip()
        sales_advisor = self.advisor_combo.currentText()

        if not all([vin, model, year, owner_name, sales_advisor]):
            QMessageBox.warning(self, "Advertencia", "Los campos VIN, Modelo, Año, Propietario y Asesor son obligatorios.")
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO vins (vin, model, year, insurance, owner_name, owner_email, owner_phone, sales_advisor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (vin, model, year, insurance, owner_name, owner_email, owner_phone, sales_advisor))
            
            conn.commit()
            QMessageBox.information(self, "Éxito", f"Vehículo {vin} registrado exitosamente.")
            self.accept()
        
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", f"El VIN '{vin}' ya existe.")
        except Exception as e:
            QMessageBox.critical(self, "Error de DB", f"Ocurrió un error al guardar el VIN: {e}")
        finally:
            conn.close()

class AddPartWindow(QDialog):
    def __init__(self, estilo_css):
        super().__init__()
        self.setWindowTitle("Agregar Nueva Parte al Inventario") 
        self.setStyleSheet(estilo_css)
        self.setGeometry(150, 150, 400, 250)
        
        layout = QVBoxLayout(self)
        title_label = QLabel("Registrar Nueva Parte al Inventario")
        title_label.setObjectName("title_label")
        layout.addWidget(title_label)
        
        layout.addWidget(QLabel("Número de Parte (NP):"))
        self.part_number_input = QLineEdit()
        layout.addWidget(self.part_number_input)
        
        layout.addWidget(QLabel("Nombre de la Parte:"))
        self.part_name_input = QLineEdit()
        layout.addWidget(self.part_name_input)
        
        save_button = QPushButton("Guardar Parte en Inventario")
        save_button.clicked.connect(self.save_part)
        
        layout.addWidget(save_button)

    def save_part(self):
        part_number = self.part_number_input.text().strip().upper()
        part_name = self.part_name_input.text().strip()
        
        if not part_number or not part_name:
            QMessageBox.warning(self, "Advertencia", "Ambos campos son obligatorios.")
            return
            
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO parts (part_number, part_name)
                VALUES (?, ?)
            """, (part_number, part_name))
            
            conn.commit()
            QMessageBox.information(self, "Éxito", f"Parte '{part_number}' registrada exitosamente en el inventario.")
            self.accept()
        
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", f"El número de parte '{part_number}' ya existe.")
        except Exception as e:
            QMessageBox.critical(self, "Error de DB", f"Ocurrió un error al guardar la parte: {e}")
        finally:
            conn.close()

class AssignPartsToOTDialog(QDialog):
    def __init__(self, ot_id, ot_number, estilo_css):
        super().__init__()
        self.ot_id = ot_id
        self.ot_number = ot_number
        self.setStyleSheet(estilo_css)
        self.setWindowTitle(f"Asignar Partes a OT: {ot_number}")
        self.setGeometry(200, 200, 500, 300)
        
        layout = QGridLayout(self)
        title_label = QLabel(f"Asignar Partes para {ot_number}")
        title_label.setObjectName("title_label")
        layout.addWidget(title_label, 0, 0, 1, 2)

        layout.addWidget(QLabel("Seleccionar Parte:"), 1, 0)
        self.part_combo = QComboBox()
        self._load_available_parts()
        layout.addWidget(self.part_combo, 1, 1)

        layout.addWidget(QLabel("Cantidad Requerida:"), 2, 0)
        self.quantity_input = QLineEdit("1")
        self.quantity_input.setValidator(QIntValidator(1, 999))
        layout.addWidget(self.quantity_input, 2, 1)
        
        layout.addWidget(QLabel("Estado Inicial:"), 3, 0)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Pendiente", "Pedida", "Entregada"])
        self.status_combo.setCurrentText("Pendiente")
        layout.addWidget(self.status_combo, 3, 1)

        save_button = QPushButton(f"Asignar a {ot_number}")
        save_button.clicked.connect(self.assign_part)
        layout.addWidget(save_button, 4, 0, 1, 2)
        
    def _load_available_parts(self):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT part_number, part_name, id FROM parts ORDER BY part_number")
        parts = cursor.fetchall()
        conn.close()
        
        self.part_map = {} 
        if not parts:
            self.part_combo.addItem("No hay partes en inventario")
            return
            
        for number, name, part_id in parts:
            display_text = f"{number} - {name}"
            self.part_combo.addItem(display_text)
            self.part_map[display_text] = part_id

    def assign_part(self):
        selected_text = self.part_combo.currentText()
        quantity_text = self.quantity_input.text()
        status = self.status_combo.currentText()
        
        if selected_text == "No hay partes en inventario" or not quantity_text:
            QMessageBox.warning(self, "Error", "Selecciona una parte y una cantidad válida.")
            return

        try:
            part_id = self.part_map[selected_text]
            quantity = int(quantity_text)
        except (KeyError, ValueError):
            QMessageBox.critical(self, "Error", "Error al obtener ID de parte o cantidad inválida.")
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO ot_parts (ot_id, part_id, quantity, status)
                VALUES (?, ?, ?, ?)
            """, (self.ot_id, part_id, quantity, status))
            
            conn.commit()
            QMessageBox.information(self, "Éxito", f"Parte asignada a OT {self.ot_number} con éxito.")
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error de DB", f"Ocurrió un error al asignar la parte: {e}")
        finally:
            conn.close()

class AddAdvisorWindow(QDialog):
    def __init__(self, estilo_css):
        super().__init__()
        self.setWindowTitle("Registrar Nuevo Asesor")
        self.setStyleSheet(estilo_css)
        self.setGeometry(150, 150, 400, 200)
        
        layout = QVBoxLayout(self)
        title_label = QLabel("Registrar Nuevo Asesor de Venta")
        title_label.setObjectName("title_label")
        layout.addWidget(title_label)
        
        layout.addWidget(QLabel("Nombre del Asesor:"))
        self.advisor_name_input = QLineEdit()
        layout.addWidget(self.advisor_name_input)
        
        save_button = QPushButton("Guardar Asesor")
        save_button.clicked.connect(self.save_advisor)
        
        layout.addWidget(save_button)

    def save_advisor(self):
        advisor_name = self.advisor_name_input.text().strip()
        
        if not advisor_name:
            QMessageBox.warning(self, "Advertencia", "El nombre del asesor es obligatorio.")
            return
            
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO advisors (name)
                VALUES (?)
            """, (advisor_name,))
            
            conn.commit()
            QMessageBox.information(self, "Éxito", f"Asesor '{advisor_name}' registrado exitosamente.")
            self.accept()
        
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", f"El asesor '{advisor_name}' ya existe.")
        except Exception as e:
            QMessageBox.critical(self, "Error de DB", f"Ocurrió un error al guardar el asesor: {e}")
        finally:
            conn.close()


# ----------------------------------------------------------------------
# --- CLASES DE VISTA PRINCIPALES (Botón Volver a Inicio eliminado) ---
# ----------------------------------------------------------------------

class OTWindow(QWidget):
    # ⭐️ Eliminado 'main_window' del constructor ⭐️
    def __init__(self, estilo_css=""):
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        
        # ❌ ELIMINADO: self.back_button = QPushButton("⬅️ Volver a Inicio") ❌
        # ❌ ELIMINADO: self.back_button.clicked.connect(self.go_back_to_home) ❌
        # ❌ ELIMINADO: header_layout.addWidget(self.back_button) ❌
        
        header_layout.addSpacing(20)
        
        self.title_label = QLabel("Órdenes de Trabajo por Asesor")
        self.title_label.setObjectName("title_label")
        add_ot_button = QPushButton("Agregar OT")
        add_ot_button.setObjectName("add_button")
        # Nota: La conexión se realiza a un método interno, que llama al diálogo
        add_ot_button.clicked.connect(self.add_new_ot) 
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(add_ot_button)
        
        layout.addLayout(header_layout)
        
        # Nueva sección de búsqueda
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por OT, asesor, fecha, seguro o estado...")
        self.search_input.textChanged.connect(self.search_ots)
        search_button = QPushButton("🔍 Buscar")
        search_button.clicked.connect(self.search_ots)
        clear_button = QPushButton("Limpiar")
        clear_button.clicked.connect(self.clear_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        search_layout.addWidget(clear_button)
        search_layout.addStretch()
        
        layout.addLayout(search_layout)
        
        self.ot_table = QTableWidget()
        self.ot_table.setColumnCount(6)
        self.ot_table.setHorizontalHeaderLabels([
            "OT", "Asesor de Ventas", "No. de Piezas", "Fecha de Pedido", "Seguro", "Estado"
        ])
        
        self.current_filter_advisor = None  # Para mantener el filtro de asesor activo
        self.load_ot_data()
        
        self.ot_table.cellDoubleClicked.connect(self.show_ot_parts)
        
        layout.addWidget(self.ot_table)
        
    # ❌ ELIMINADO: go_back_to_home() ❌

    def show_ot_parts(self, row, column):
        ot_number_item = self.ot_table.item(row, 0)
        if ot_number_item is None:
            return
            
        ot_number = ot_number_item.text()
        
        # Obtiene el estilo de la app o de la ventana principal
        estilo_css = self.parent().styleSheet() if self.parent() else self.styleSheet()
        parts_dialog = OTPartsDialog(ot_number, estilo_css=estilo_css)
        parts_dialog.exec()

    def load_ot_data(self, filter_advisor=None, search_term=None):
        self.current_filter_advisor = filter_advisor  # Guardar el filtro actual
        
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        base_query = """
        SELECT o.ot_number, o.sales_advisor, o.request_date, o.status,
               v.insurance, COUNT(op.part_id) as total_parts
        FROM ots AS o
        LEFT JOIN ot_parts AS op ON o.id = op.ot_id
        LEFT JOIN vins AS v ON o.vin = v.vin
        """
        where_clauses = []
        params = []
        
        # Filtro por asesor
        if filter_advisor:
            where_clauses.append("o.sales_advisor = ?")
            params.append(filter_advisor)
            self.title_label.setText(f"Órdenes de Trabajo - Filtrado por: {filter_advisor}")
        else:
            self.title_label.setText("Órdenes de Trabajo por Asesor")
        
        # Filtro de búsqueda
        if search_term:
            search_condition = """(
                o.ot_number LIKE ? OR 
                o.sales_advisor LIKE ? OR 
                o.request_date LIKE ? OR 
                o.status LIKE ? OR 
                v.insurance LIKE ?
            )"""
            where_clauses.append(search_condition)
            search_param = f'%{search_term}%'
            params.extend([search_param] * 5)
        
        # Construir WHERE clause
        where_clause = ""
        if where_clauses:
            where_clause = " WHERE " + " AND ".join(where_clauses)

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
        
        # Mostrar mensaje si no hay resultados de búsqueda
        if search_term and len(ots_data) == 0:
            QMessageBox.information(self, "Sin resultados", 
                                   f"No se encontraron órdenes de trabajo que coincidan con '{search_term}'.")
    
    def search_ots(self):
        """Busca órdenes de trabajo por cualquier atributo"""
        search_term = self.search_input.text().strip()
        self.load_ot_data(
            filter_advisor=self.current_filter_advisor,
            search_term=search_term if search_term else None
        )
    
    def clear_search(self):
        """Limpia la búsqueda y muestra todas las OT (manteniendo filtro de asesor si existe)"""
        self.search_input.clear()
        self.load_ot_data(filter_advisor=self.current_filter_advisor)

    def add_new_ot(self):
        # Asume que el estilo está en la aplicación o lo pasa directamente
        estilo_css = QApplication.instance().styleSheet() 
        add_ot_window = AddOTWindow(estilo_css)
        if add_ot_window.exec() == QDialog.DialogCode.Accepted:
            self.load_ot_data()

class PartsListWindow(QWidget):
    def __init__(self, estilo_css=""):
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        
        # ❌ ELIMINADO: Botón Volver a Inicio ❌
        
        header_layout.addSpacing(20)

        title_label = QLabel("Lista de Partes (Inventario)")
        title_label.setObjectName("title_label")
        add_part_button = QPushButton("Agregar Parte al Inventario")
        add_part_button.setObjectName("add_button")
        add_part_button.clicked.connect(self.add_new_part)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(add_part_button)
        
        layout.addLayout(header_layout)

        # Nueva sección de búsqueda
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ingrese número de parte o nombre...")
        self.search_input.textChanged.connect(self.search_parts)
        search_button = QPushButton("🔍 Buscar")
        search_button.clicked.connect(self.search_parts)
        clear_button = QPushButton("Limpiar")
        clear_button.clicked.connect(self.clear_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        search_layout.addWidget(clear_button)
        search_layout.addStretch()
        
        layout.addLayout(search_layout)

        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(2)
        self.parts_table.setHorizontalHeaderLabels(["No. de Parte", "Nombre"])
        
        self.load_parts_data()
        
        layout.addWidget(self.parts_table)
        
    # ❌ ELIMINADO: go_back_to_home() ❌
            
    def load_parts_data(self, search_term=None):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        if search_term:
            # Buscar por número de parte o nombre
            cursor.execute("""
                SELECT part_number, part_name 
                FROM parts 
                WHERE part_number LIKE ? OR part_name LIKE ?
                ORDER BY part_number
            """, (f'%{search_term}%', f'%{search_term}%'))
        else:
            cursor.execute("SELECT part_number, part_name FROM parts ORDER BY part_number")
            
        parts_data = cursor.fetchall()
        conn.close()
        
        self.parts_table.setRowCount(len(parts_data))
        for row_idx, row_data in enumerate(parts_data):
            self.parts_table.setItem(row_idx, 0, QTableWidgetItem(row_data[0]))
            self.parts_table.setItem(row_idx, 1, QTableWidgetItem(row_data[1]))
            
        self.parts_table.resizeColumnsToContents()
        
        # Mostrar mensaje si no hay resultados
        if search_term and len(parts_data) == 0:
            QMessageBox.information(self, "Sin resultados", 
                                   f"No se encontraron partes que coincidan con '{search_term}'.")

    def search_parts(self):
        """Busca partes por número o nombre"""
        search_term = self.search_input.text().strip()
        self.load_parts_data(search_term if search_term else None)
    
    def clear_search(self):
        """Limpia la búsqueda y muestra todas las partes"""
        self.search_input.clear()
        self.load_parts_data()

    def add_new_part(self):
        estilo_css = QApplication.instance().styleSheet()
        add_part_window = AddPartWindow(estilo_css)
        if add_part_window.exec() == QDialog.DialogCode.Accepted:
            self.load_parts_data()

class VINLookupWindow(QWidget):
    def __init__(self, estilo_css=""):
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        # ⭐️ CABECERA SIN BOTÓN VOLVER A INICIO ⭐️
        header_layout = QHBoxLayout()
        
        # ❌ ELIMINADO: Botón Volver a Inicio ❌
        
        header_layout.addSpacing(20)
        
        title_label = QLabel("Búsqueda de Información por OT")
        title_label.setObjectName("title_label")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # ⭐️ BUSCADOR - Aseguramos la visibilidad ⭐️
        search_layout = QHBoxLayout()
        self.ot_input = QLineEdit()
        self.ot_input.setPlaceholderText("Ingrese el número de OT")
        self.search_button = QPushButton("Buscar")
        self.search_button.clicked.connect(self.search_ot)
        
        search_layout.addWidget(self.ot_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout) # <-- Esta línea es vital
        
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_container.setVisible(False)
        
        layout.addWidget(self.results_container)

    # ❌ ELIMINADO: go_back_to_home() ❌

    def search_ot(self):
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
    def __init__(self, estilo_css=""):
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        
        # ❌ ELIMINADO: Botón Volver a Inicio ❌
        
        header_layout.addSpacing(20)

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

    # ❌ ELIMINADO: go_back_to_home() ❌
            
    def load_advisor_data(self):
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
        estilo_css = QApplication.instance().styleSheet()
        add_advisor_window = AddAdvisorWindow(estilo_css)
        if add_advisor_window.exec() == QDialog.DialogCode.Accepted:
            self.load_advisor_data()
            # Asume que el parent (MainWindow) tiene el método, aunque la vista no lo necesite
            if isinstance(self.parent(), MainWindow):
                self.parent().update_advisor_filter_menu()

# ----------------------------------------------------------------------
# --- CLASE PRINCIPAL (MAIN WINDOW) ---
# ----------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self, estilo_css):
        super().__init__()
        self.user_role = LoginWindow.user_role
        self.user_full_name = LoginWindow.username_logged
        
        self.setWindowTitle(f"Sistema de Gestión - Usuario: {self.user_full_name} ({self.user_role.upper()})")
        
        # ⭐️ MODIFICACIÓN: Pantalla más compacta ⭐️
        self.setFixedSize(1000, 600) 
        self.move(int((QApplication.primaryScreen().geometry().width() - 1000) / 2), 
                  int((QApplication.primaryScreen().geometry().height() - 600) / 2)) 
        
        self.setStyleSheet(estilo_css)
        
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

        # Botones de navegación principales (Izquierda)
        # Botones de navegación principales (Izquierda)
        home_button = QPushButton("Inicio")
        home_button.setCheckable(True)
        home_button.setChecked(True)
        home_button.clicked.connect(lambda: self.change_view("home"))
        header_layout.addWidget(home_button)
        self.nav_buttons["home"] = home_button
        
        ot_button = QPushButton("Órdenes de Trabajo ▼")
        ot_button.setCheckable(True) # ⭐️ AGREGAR
        ot_button.setChecked(False)  # ⭐️ AGREGAR
        header_layout.addWidget(ot_button)
        self.nav_buttons["ot"] = ot_button
        
        parts_button = QPushButton("Partes ▼")
        parts_button.setCheckable(True) # ⭐️ AGREGAR
        parts_button.setChecked(False) # ⭐️ AGREGAR
        header_layout.addWidget(parts_button)
        self.nav_buttons["parts"] = parts_button
        
        vin_button = QPushButton("Vehículos (VIN) ▼")
        vin_button.setCheckable(True) # ⭐️ AGREGAR
        vin_button.setChecked(False)  # ⭐️ AGREGAR
        header_layout.addWidget(vin_button)
        self.nav_buttons["vin"] = vin_button
        
        advisor_button = QPushButton("Asesor de Ventas ▼")
        advisor_button.setCheckable(True) # ⭐️ AGREGAR
        advisor_button.setChecked(False) # ⭐️ AGREGAR
        header_layout.addWidget(advisor_button)
        self.nav_buttons["advisor_filter"] = advisor_button
        
        header_layout.addStretch()

        # Botón ADMIN (Solo visible si es admin)
        if self.user_role == 'admin':
            admin_button = QPushButton("🛠️ Administración ▼") 
            admin_button.setObjectName("admin_button") 
            header_layout.addWidget(admin_button)
            self.nav_buttons["admin"] = admin_button
            
            self.admin_menu = self.create_admin_menu(estilo_css)
            admin_button.clicked.connect(lambda: self.show_dropdown_menu(admin_button, self.admin_menu))
        
        # Botón CERRAR SESIÓN
        logout_button = QPushButton("🚪 Cerrar Sesión")
        # ⭐️ Conexión al método logout, que debe existir ⭐️
        logout_button.clicked.connect(self.logout) 
        header_layout.addWidget(logout_button)
        
        # --- Contenido principal (Stacked Widget) ---
        self.stacked_widget = QStackedWidget()
        
        self.home_widget = QWidget()
        self.setup_home_widget(self.home_widget)
        self.stacked_widget.addWidget(self.home_widget) 
        
        # ⭐️ Vistas sin el argumento 'main_window' ⭐️
        self.ot_widget = OTWindow(estilo_css=estilo_css)
        self.stacked_widget.addWidget(self.ot_widget) 
        
        self.parts_widget = PartsListWindow(estilo_css=estilo_css)
        self.stacked_widget.addWidget(self.parts_widget) 
        
        self.vin_widget = VINLookupWindow(estilo_css=estilo_css)
        self.stacked_widget.addWidget(self.vin_widget) 

        self.advisor_widget = AdvisorListWindow(estilo_css=estilo_css)
        self.stacked_widget.addWidget(self.advisor_widget) 

        self.ot_menu = self.create_ot_menu(estilo_css)
        self.parts_menu = self.create_parts_menu(estilo_css)
        self.vin_menu = self.create_vin_menu(estilo_css)
        self.advisor_filter_menu = self.create_advisor_filter_menu(estilo_css)
        
        ot_button.clicked.connect(lambda: self.show_dropdown_menu(ot_button, self.ot_menu))
        parts_button.clicked.connect(lambda: self.show_dropdown_menu(parts_button, self.parts_menu))
        vin_button.clicked.connect(lambda: self.show_dropdown_menu(vin_button, self.vin_menu))
        advisor_button.clicked.connect(lambda: self.show_dropdown_menu(advisor_button, self.advisor_filter_menu))
        
        main_layout.addWidget(header_widget)
        main_layout.addWidget(self.stacked_widget)
        
        self.change_view("home")

    # ------------------
    # MÉTODOS DE ADMIN Y UTILIDAD
    # ------------------
    
    def create_admin_menu(self, estilo_css):
        menu = QMenu(self)
        menu.setStyleSheet(estilo_css)
        
        action_add_user = menu.addAction("➕ Crear Nuevo Usuario")
        action_add_user.triggered.connect(self.add_new_user)
        
        menu.addSeparator()
        
        action_logout = menu.addAction("🚪 Cerrar Sesión")
        action_logout.triggered.connect(self.logout)
        
        return menu

    def add_new_user(self):
        add_user_dialog = AddUserDialog(self.styleSheet())
        add_user_dialog.exec()
        
    def logout(self):
        """Cierra la ventana principal para volver a la pantalla de login (manejado en __main__)."""
        self.close()

    def show_dropdown_menu(self, button, menu):
        if self.nav_buttons.get("home") and self.nav_buttons["home"].isChecked():
            self.nav_buttons["home"].setChecked(False)
            
        if menu == self.advisor_filter_menu:
            self.update_advisor_filter_menu()
            
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def change_view(self, view_name):
     # MODIFICACIÓN DE LÓGICA DE CHEQUEO 
        # Desactivar el 'checked' de TODOS los botones
        for name, button in self.nav_buttons.items():
            if button.isCheckable():
                # Desmarca todos
                button.setChecked(False)
     # Activar el 'checked' del botón actual
        # Esta parte marca el botón seleccionado después de desmarcar los demás
        view_map = {
            "home": 0, "ot_list": 1, "parts_list": 2, "vin_lookup": 3, "advisor_list": 4
        }
        
        # Aquí debes mapear el nombre de la vista al nombre del botón
        button_name_map = {
            "home": "home", "ot_list": "ot", "parts_list": "parts", "vin_lookup": "vin", "advisor_list": "advisor_filter"
        }
        
        if view_name in button_name_map:
            button_key = button_name_map[view_name]
            if button_key in self.nav_buttons:
                self.nav_buttons[button_key].setChecked(True)
        # FIN MODIFICACIÓN DE LÓGICA DE CHEQUEO 
        
        index = view_map.get(view_name)
        if index is not None:
            self.stacked_widget.setCurrentIndex(index)
            # Recargar datos si es necesario al cambiar de vista
            if view_name == "ot_list":
                self.ot_widget.load_ot_data()
            elif view_name == "parts_list":
                self.parts_widget.load_parts_data()
            elif view_name == "advisor_list":
                self.advisor_widget.load_advisor_data()
                
    def apply_advisor_filter(self, advisor_name=None):
        self.change_view("ot_list")
        self.ot_widget.load_ot_data(filter_advisor=advisor_name)
        
        if advisor_name:
             QMessageBox.information(self, "Filtro Aplicado", f"Mostrando OTs asociadas al asesor: {advisor_name}")
        else:
             QMessageBox.information(self, "Filtro Eliminado", "Mostrando todas las OTs.")

    def create_ot_menu(self, estilo_css):
        menu = QMenu(self)
        menu.setStyleSheet(estilo_css)
        
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

    def create_advisor_filter_menu(self, estilo_css):
        menu = QMenu(self)
        menu.setStyleSheet(estilo_css)
        self.update_advisor_filter_menu(menu) 
        return menu

    def update_advisor_filter_menu(self, menu=None):
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

    def create_parts_menu(self, estilo_css):
        menu = QMenu(self)
        menu.setStyleSheet(estilo_css)
        
        action_list = menu.addAction("Ver Listado de Partes (Inventario)")
        action_list.triggered.connect(lambda: self.change_view("parts_list"))
        action_add = menu.addAction("➕ Agregar Nueva Parte a Inventario")
        action_add.triggered.connect(self.parts_widget.add_new_part)
        action_search = menu.addAction("🔍 Buscar por No. de Parte")
        action_search.triggered.connect(lambda: (self.change_view("parts_list"), QMessageBox.information(self, "Búsqueda", "Lógica para abrir la barra de búsqueda rápida aquí.")))
        
        return menu

    def create_vin_menu(self, estilo_css):
        menu = QMenu(self)
        menu.setStyleSheet(estilo_css)
        
        action_search = menu.addAction("🔍 Buscar por VIN/OT")
        action_search.triggered.connect(lambda: self.change_view("vin_lookup"))
        menu.addSeparator()
        action_add_vin = menu.addAction("🚗 Registrar Nuevo Vehículo")
        action_add_vin.triggered.connect(self.add_new_vin)
        
        return menu
    
    def setup_home_widget(self, widget):
        content_layout = QVBoxLayout(widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        company_logo = QLabel()
        
        # Intentar cargar imagen desde la carpeta del ejecutable/proyecto
        image_path = os.path.join(base_path, 'image.jpeg')
        pixmap = QPixmap(image_path)
        # Si no existe en la carpeta del exe, intentar en el bundle temporal (PyInstaller _MEIPASS)
        if pixmap.isNull() and getattr(sys, 'frozen', False):
            try:
                bundled_image = os.path.join(sys._MEIPASS, 'image.jpeg')
                pixmap = QPixmap(bundled_image)
            except Exception:
                pass

        if pixmap.isNull():
            company_logo = QLabel(f"Sistema de Gestión de Empresa\nUsuario: {self.user_full_name}")
            company_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            company_logo.setObjectName("title_label")
        else:
            company_logo.setPixmap(pixmap)
            company_logo.setScaledContents(True)
            company_logo.setFixedSize(600, 400) 
        
        content_layout.addWidget(company_logo)
        
        if self.user_role == 'admin':
            admin_actions_layout = QHBoxLayout()
            admin_actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            
        content_layout.addStretch()

    def add_new_vin(self):
        add_vin_window = AddVINWindow(self.styleSheet())
        if add_vin_window.exec() == QDialog.DialogCode.Accepted:
            self.update_advisor_filter_menu()
            if self.stacked_widget.currentIndex() == 1: 
                self.ot_widget.load_ot_data()
        
    def add_new_advisor(self):
        add_advisor_window = AddAdvisorWindow(self.styleSheet())
        if add_advisor_window.exec() == QDialog.DialogCode.Accepted:
            if self.stacked_widget.currentIndex() == 4:
                self.advisor_widget.load_advisor_data()
            self.update_advisor_filter_menu()


# ----------------------------------------------------------------------
# --- PUNTO DE ENTRADA (MAIN) ---
# ----------------------------------------------------------------------

if __name__ == "__main__":
    setup_database()
    app = QApplication(sys.argv)
    
    # Cargar estilos: preferir archivo externo si existe, sino usar estilos embebidos
    estilo_css = load_stylesheet()
    
    # 1. Mostrar Login
    login_dialog = LoginWindow(estilo_css) 
    
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        # 2. Si es exitoso, mostrar la ventana principal
        main_window = MainWindow(estilo_css) 
        main_window.show()
        sys.exit(app.exec())