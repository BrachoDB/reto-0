# Proyecto
Agenda Clara permite registrar y organizar contactos privados por cuenta.
Incluye autenticación, búsqueda por nombre y exportación de contactos a CSV.
# Stack
- Framework: Flask; plantillas HTML con Jinja2 y estilos CSS.
- Base de datos: SQLite mediante `sqlite3` de la biblioteca estándar.
- Librerías principales: python-dotenv y Werkzeug; contraseña con hash.
# Comandos
- Instalar dependencias de aplicación: `python -m pip install -r requirements.txt`.
- Ejecutar: configura `SECRET_KEY` en `.env` y usa `python app.py`.
- Pruebas: `python -m pytest -v` (requiere pytest disponible).
- Estilo: `ruff check .` (requiere Ruff disponible).

# Estructura
- `app.py` — fábrica Flask, rutas, autenticación, consultas SQLite y exportación CSV.
- `.env` — configuración local privada; está ignorado por Git.
- `.env.example` — nombres y ejemplos de configuración, sin secretos reales.
- `.gitignore` — excluye entorno virtual, configuración local y datos SQLite.
- `README.md` — requisitos, inicio, funcionalidades y pruebas.
- `requirements.txt` — dependencias de ejecución de la aplicación.
- `instance/` — datos de instancia; contiene `contacts.sqlite`, creado automáticamente.
- `static/` — recursos estáticos de la interfaz.
- `static/style.css` — estilos y diseño adaptable.
- `templates/` — plantillas Jinja2 de la interfaz web.
- `templates/base.html` — estructura común y navegación.
- `templates/contact_form.html` — formulario para crear y editar contactos.
- `templates/contacts.html` — listado, búsqueda y exportación de contactos.
- `templates/login.html` — formulario de inicio de sesión.
- `templates/register.html` — formulario de registro.
- `tests/` — pruebas automatizadas.
- `tests/test_app.py` — pruebas de autenticación, privacidad, búsqueda y CSV.
- `.venv/` — entorno virtual local con dependencias instaladas.

# Qué no hacer
- No modificar las pruebas para que pasen.
- No escribir claves en el código.
- No instalar dependencias sin explicar para qué.
- No hacer commit ni push.

# Lecciones aprendidas
