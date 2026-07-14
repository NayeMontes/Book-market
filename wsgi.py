import os
import sys

print("--- DETECTIVE: LISTANDO ARCHIVOS EN LA RAÍZ ---")
try:
    print("Archivos actuales:", os.listdir('.'))
except Exception as e:
    print("No se pudo listar:", e)
print("-----------------------------------------------")

from app import create_app

app = create_app('default')

if __name__ == "__main__":
    app.run()