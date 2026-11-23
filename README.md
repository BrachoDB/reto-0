# Agenda Clara

Aplicación web en Python para guardar contactos de forma privada, buscarlos por nombre y exportarlos a CSV.

## Requisitos

- Python 3.10 o posterior
- Flask (`pip install -r requirements.txt`)

## Ejecutar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SECRET_KEY = "reemplaza-por-una-clave-larga-y-aleatoria"
python app.py
```

Abre http://127.0.0.1:5000, crea una cuenta y comienza a guardar contactos. La base de datos SQLite se crea automáticamente en `instance/contacts.sqlite`. Para producción, define un `SECRET_KEY` persistente y establece `COOKIE_SECURE=1` al servir la aplicación exclusivamente por HTTPS.

## Funcionalidades

- Registro e inicio de sesión con contraseñas almacenadas mediante hash.
- Contactos privados por cuenta, con nombre, correo, teléfono y notas.
- Búsqueda literal por nombre.
- Exportación de todos los contactos a CSV compatible con Excel.
- Protección CSRF en las acciones que modifican datos.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```
