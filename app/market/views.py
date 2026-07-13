import requests
from flask import render_template, request, jsonify
from concurrent.futures import ThreadPoolExecutor  # Para llamadas en paralelo

from . import market
from models.model import Books

# Configuramos cabeceras profesionales para evitar bloqueos por Rate Limit
HEADERS = {
    'User-Agent': 'MiAplicacionLibros/1.0 (contacto: tu-correo@ejemplo.com)'
}

# ==========================================
# GOOGLE BOOKS (Complementary Information)
# ==========================================
def get_google_book(title, author):
    """
    Search Google Books using title + author
    and return additional information.
    """
    try:
        query = f"{title} {author}"
        url = "https://www.googleapis.com/books/v1/volumes"
        params = {"q": query, "maxResults": 1}

        # Bajamos el timeout a 3 segundos. Si Google Books tarda más, 
        # pasamos olímpicamente de él para no retrasar la web.
        response = requests.get(url, params=params, headers=HEADERS, timeout=3)
        response.raise_for_status()

        data = response.json()
        if "items" not in data:
            return None

        info = data["items"][0]["volumeInfo"]
        images = info.get("imageLinks", {})

        return {
            "description": info.get("description", ""),
            "pages": info.get("pageCount", "N/A"),
            "language": info.get("language", "N/A"),
            "publisher": info.get("publisher", "Unknown"),
            "categories": ", ".join(info.get("categories", [])),
            "cover": images.get("thumbnail") or images.get("smallThumbnail"),
            "google_link": info.get("infoLink")
        }
    except Exception:
        # Si Google Books falla o da timeout, devolvemos None sin romper nada
        return None

# ==========================================
# MARKET PAGE
# ==========================================
@market.route("/market", methods=["GET"])
def market_home():
    return render_template("pages/market.html")

# ==========================================
# AJAX API
# ==========================================
@market.route("/api/books", methods=["GET"])
def api_books():
    query = request.args.get("search", "").strip()
    books = []

    try:
        # ======================================
        # SEARCH USING OPENLIBRARY
        # ======================================
        if query:
            url = f"https://openlibrary.org/search.json?q={query}"
            
            # Subimos el timeout a 12 segundos por si Open Library está saturado
            response = requests.get(url, headers=HEADERS, timeout=12)
            response.raise_for_status()
            
            data = response.json()
            docs = data.get("docs", [])[:12] # Limitamos a 12 resultados

            # --- OPTIMIZACIÓN EN PARALELO ---
            # En lugar de consultar Google Books uno por uno (12 veces consecutivas),
            # usamos hilos para consultar los 12 libros casi al mismo tiempo.
            with ThreadPoolExecutor(max_workers=6) as executor:
                # Preparamos las tareas
                futures = [
                    executor.submit(
                        get_google_book, 
                        doc.get("title", "No title"), 
                        ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "Unknown"
                    )
                    for doc in docs
                ]
                
                # Recolectamos las respuestas de Google Books
                google_results = [future.result() for future in futures]

            # Procesamos y cruzamos los datos obtenidos
            for doc, google in zip(docs, google_results):
                title = doc.get("title", "No title")
                author = ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "Unknown"
                cover_id = doc.get("cover_i")

                books.append({
                    "title": title,
                    "author": author,
                    "year": doc.get("first_publish_year", "N/A"),
                    "category": google["categories"] if google and google.get("categories") else (
                        doc.get("subject", ["General"])[0] if doc.get("subject") else "General"
                    ),
                    "description": google["description"] if google else "",
                    "pages": google["pages"] if google else "N/A",
                    "language": google["language"] if google else "N/A",
                    "publisher": google["publisher"] if google else "Unknown",
                    "cover": google["cover"] if google and google.get("cover") else (
                        f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None
                    ),
                    "link": google["google_link"] if google else f"https://openlibrary.org{doc.get('key')}"
                })

        # ======================================
        # LOCAL DATABASE
        # ======================================
        else:
            db_books = Books.query.limit(20).all()
            for book in db_books:
                books.append({
                    "title": book.title,
                    "author": book.author,
                    "year": book.year,
                    "category": book.category,
                    "description": "",
                    "pages": "N/A",
                    "language": "N/A",
                    "publisher": "Unknown",
                    "cover": None,
                    "link": book.link
                })

        return jsonify(books)

    except requests.exceptions.Timeout:
        print("Error: Open Library timed out.")
        return jsonify({"error": "The external API is running very slow, please try again."}), 504

    except Exception as e:
        print("API error general:", e)
        return jsonify({"error": "Ocurrió un error al cargar los libros"}), 500