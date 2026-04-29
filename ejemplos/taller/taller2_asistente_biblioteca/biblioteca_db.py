"""
Base de datos mock para el Taller 2.
No la modifiques — tus funciones operan sobre estas estructuras.
"""

# 10 libros con ID, título, autor, ejemplares disponibles
LIBROS = {
    1:  {"id": 1,  "titulo": "Clean Code",                     "autor": "Robert C. Martin",       "disponibles": 2},
    2:  {"id": 2,  "titulo": "Fluent Python",                  "autor": "Luciano Ramalho",        "disponibles": 1},
    3:  {"id": 3,  "titulo": "Design Patterns",                "autor": "Gang of Four",           "disponibles": 0},
    4:  {"id": 4,  "titulo": "Eloquent JavaScript",            "autor": "Marijn Haverbeke",       "disponibles": 3},
    5:  {"id": 5,  "titulo": "The Pragmatic Programmer",       "autor": "Hunt & Thomas",          "disponibles": 1},
    6:  {"id": 6,  "titulo": "Structure and Interpretation of Computer Programs", "autor": "Abelson & Sussman", "disponibles": 2},
    7:  {"id": 7,  "titulo": "You Don't Know JS",              "autor": "Kyle Simpson",           "disponibles": 4},
    8:  {"id": 8,  "titulo": "Effective Python",               "autor": "Brett Slatkin",          "disponibles": 1},
    9:  {"id": 9,  "titulo": "Designing Data-Intensive Applications", "autor": "Martin Kleppmann", "disponibles": 0},
    10: {"id": 10, "titulo": "The Mythical Man-Month",         "autor": "Fred Brooks",            "disponibles": 2},
}

# Reservas por estudiante: {"ana.perez": [1, 8], "juan.soto": [4], ...}
# Empieza vacío. Se llena cuando se reservan libros.
RESERVAS: dict[str, list[int]] = {}
