from app import create_app

# Esto manda a llamar a la función que creaste para inicializar tu sitio
app = create_app()

if __name__ == "__main__":
    app.run()