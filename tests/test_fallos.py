import secrets

from app import create_app


def test_busqueda_ignora_mayusculas_en_nombres_acentuados(tmp_path):
    numero = secrets.randbelow(900_000) + 100_000
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "DATABASE": str(tmp_path / "contacts.sqlite"),
        }
    )
    cliente = app.test_client()

    cliente.get("/register")
    with cliente.session_transaction() as session:
        csrf_token = session["csrf_token"]
    correo = f"usuario{numero}@example.com"
    respuesta = cliente.post(
        "/register",
        data={
            "email": correo,
            "password": "una-clave-segura",
            "csrf_token": csrf_token,
        },
    )
    assert respuesta.status_code == 302

    cliente.get("/login")
    with cliente.session_transaction() as session:
        csrf_token = session["csrf_token"]
    respuesta = cliente.post(
        "/login",
        data={
            "email": correo,
            "password": "una-clave-segura",
            "csrf_token": csrf_token,
        },
    )
    assert respuesta.status_code == 302

    cliente.get("/contacts/new")
    with cliente.session_transaction() as session:
        csrf_token = session["csrf_token"]
    nombre = f"ángela {numero}"
    respuesta = cliente.post(
        "/contacts/new",
        data={
            "name": nombre,
            "email": "",
            "phone": "",
            "notes": "",
            "csrf_token": csrf_token,
        },
    )
    assert respuesta.status_code == 302

    respuesta = cliente.get("/contacts", query_string={"q": f"ÁNGELA {numero}"})

    assert respuesta.status_code == 200
    assert nombre.encode() in respuesta.data
