# Proyecto-BD — Sistema de Gestión (PyQt6 + SQLite)

Resumen breve
-------------
Aplicación de escritorio escrita en Python usando PyQt6 como GUI y SQLite como almacén local. Este README recoge instrucciones técnicas para instalar y ejecutar la aplicación en Windows desde cero (PowerShell).

Requisitos mínimos
------------------
- Windows 10/11
- Python 3.8+ instalado (preferible 3.10 o 3.11)
- Conexión a Internet para instalar dependencias
- Opcional: privilegios para cambiar la ExecutionPolicy de PowerShell

Instalación paso a paso (PowerShell)
-----------------------------------
1. Abrir PowerShell como usuario normal (no admin) y navegar al directorio del proyecto:

```powershell
cd "Ruta donde desees instalar el proyecto"
```

2. (Opcional) Comprobar Python disponible:

```powershell
python --version
```

3. Crear entorno virtual (recomendado):

```powershell
python -m venv .venv
```

4. Activar el entorno en PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si recibes un error por políticas de ejecución, ejecutar (si estás de acuerdo):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

5. Actualizar pip e instalar dependencias básicas:

```powershell
python -m pip install --upgrade pip
python -m pip install PyQt6
```

Credenciales por defecto
------------------------
Durante la primera ejecución `setup_database()` crea un usuario por defecto:

- Usuario: `admin`
- Contraseña: `password`

Solución de problemas comunes
----------------------------
- Error al activar el venv por políticas de PowerShell: usar `Set-ExecutionPolicy` con `RemoteSigned` o activar con `activate.bat` desde cmd.exe:

```powershell
.venv\Scripts\activate.bat
```

- `pip` no encuentra PyQt6: asegúrate de usar `python -m pip install PyQt6` y que `python --version` es 3.8+.
- Error `Failed to load platform plugin 'windows'`: puede indicar conflictos entre versiones de Qt o la necesidad del Visual C++ Redistributable. Instalar el paquete redistributable de Microsoft (versión 2015-2022).
- Si la app no aplica estilos: renombrar `estilo.css` a `styles.css` o editar `empresa.py` para que busque ambos nombres.

Opciones avanzadas
------------------
- Empaquetado: usar PyInstaller para generar `.exe` y distribuir.