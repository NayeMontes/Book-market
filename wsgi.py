import os
import sys

# Forzar a Python a buscar módulos en la raíz del proyecto en producción
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app

# Inicializar la aplicación con la configuración por defecto
app = create_app('default')

if __name__ == "__main__":
    app.run()