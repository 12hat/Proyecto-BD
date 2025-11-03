"""
check_build_deps.py
Comprueba si las dependencias necesarias para generar el exe están instaladas:
- PyInstaller
- PyQt6

Salida:
- Código 0 si todo está ok
- Código 1 si faltan dependencias (lista en stdout)
"""
import importlib
import sys

required = [
    ("PyInstaller", "PyInstaller"),
    ("PyQt6", "PyQt6")
]
missing = []

for name, module in required:
    try:
        importlib.import_module(module)
    except Exception:
        missing.append(name)

if missing:
    print("Faltan las siguientes dependencias necesarias para el build:")
    for m in missing:
        print(f" - {m}")
    print("\nInstálalas con: pip install pyinstaller PyQt6")
    sys.exit(1)

print("Todas las dependencias necesarias están instaladas: {}".format(', '.join([n for n,_ in required])))
sys.exit(0)
