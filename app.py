import csv
import hmac
import io
import os
import re
import secrets
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    current_app,
    flash,
    g,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        DATABASE=os.environ.get(
            "CONTACTS_DATABASE", str(Path(app.instance_path) / "contacts.sqlite")
        ),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "").lower()
        in {"1", "true", "yes"},
    )
    if test_config:
        app.config.update(test_config)
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("Define la variable de entorno SECRET_KEY.")

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_db(app)

    @app.before_request
    def protect_post_requests():
        if request.method == "POST":
            submitted_token = request.form.get("csrf_token", "")
            session_token = session.get("csrf_token", "")
            if not session_token or not hmac.compare_digest(
                submitted_token, session_token
            ):
                abort(400, description="Token de seguridad inválido. Recarga la página.")

    @app.context_processor
    def inject_csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return {"csrf_token": session["csrf_token"]}

    @app.get("/")
    def index():
        if g.user:
            return redirect(url_for("contacts"))
        return redirect(url_for("login"))

    @app.route("/register", methods=("GET", "POST"))
    def register():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            error = None

            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                error = "Ingresa un correo electrónico válido."
            elif len(password) < 10:
                error = "La contraseña debe tener al menos 10 caracteres."

            if error is None:
                try:
                    get_db().execute(
                        "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                        (email, generate_password_hash(password)),
                    )
                    get_db().commit()
                except sqlite3.IntegrityError:
                    error = "Ya existe una cuenta con ese correo."
                else:
                    flash("Cuenta creada. Ahora puedes iniciar sesión.", "success")
                    return redirect(url_for("login"))

            flash(error, "error")

        return render_template("register.html")

    @app.route("/login", methods=("GET", "POST"))
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = get_db().execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

            if user is None or not check_password_hash(
                user["password_hash"], password
            ):
                flash("Correo o contraseña incorrectos.", "error")
            else:
                session.clear()
                session["user_id"] = user["id"]
                return redirect(url_for("contacts"))

        return render_template("login.html")

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/contacts")
    def contacts():
        if g.user is None:
            return redirect(url_for("login"))
        search = request.args.get("q", "").strip()[:100]
        escaped_search = (
            search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        rows = get_db().execute(
            """
            SELECT id, name, email, phone, notes
            FROM contacts
            WHERE user_id = ? AND name LIKE ? ESCAPE '\\'
            ORDER BY name COLLATE NOCASE
            """,
            (g.user["id"], f"%{escaped_search}%"),
        ).fetchall()
        return render_template("contacts.html", contacts=rows, search=search)

    @app.route("/contacts/new", methods=("GET", "POST"))
    @app.route("/contacts/<int:contact_id>/edit", methods=("GET", "POST"))
    def edit_contact(contact_id=None):
        if g.user is None:
            return redirect(url_for("login"))
        contact = None
        if contact_id is not None:
            contact = get_db().execute(
                "SELECT * FROM contacts WHERE id = ? AND user_id = ?",
                (contact_id, g.user["id"]),
            ).fetchone()
            if contact is None:
                abort(404)

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            notes = request.form.get("notes", "").strip()

            if not name or len(name) > 120:
                flash("El nombre es obligatorio y no debe superar 120 caracteres.", "error")
            elif any(len(value) > limit for value, limit in (
                (email, 254), (phone, 50), (notes, 2000)
            )):
                flash("Revisa la longitud de los campos del contacto.", "error")
            else:
                if contact is None:
                    get_db().execute(
                        """INSERT INTO contacts (user_id, name, email, phone, notes)
                           VALUES (?, ?, ?, ?, ?)""",
                        (g.user["id"], name, email, phone, notes),
                    )
                    flash("Contacto guardado.", "success")
                else:
                    get_db().execute(
                        """UPDATE contacts
                           SET name = ?, email = ?, phone = ?, notes = ?
                           WHERE id = ? AND user_id = ?""",
                        (name, email, phone, notes, contact_id, g.user["id"]),
                    )
                    flash("Contacto actualizado.", "success")
                get_db().commit()
                return redirect(url_for("contacts"))

        return render_template("contact_form.html", contact=contact)

    @app.post("/contacts/<int:contact_id>/delete")
    def delete_contact(contact_id):
        if g.user is None:
            return redirect(url_for("login"))
        result = get_db().execute(
            "DELETE FROM contacts WHERE id = ? AND user_id = ?",
            (contact_id, g.user["id"]),
        )
        get_db().commit()
        if result.rowcount == 0:
            abort(404)
        flash("Contacto eliminado.", "success")
        return redirect(url_for("contacts"))

    @app.get("/contacts/export.csv")
    def export_contacts():
        if g.user is None:
            return redirect(url_for("login"))
        rows = get_db().execute(
            """SELECT name, email, phone, notes FROM contacts
               WHERE user_id = ? ORDER BY name COLLATE NOCASE""",
            (g.user["id"],),
        ).fetchall()

        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(("Nombre", "Correo", "Teléfono", "Notas"))
        for row in rows:
            writer.writerow([safe_csv_cell(value) for value in row])

        response = make_response("\ufeff" + output.getvalue())
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = 'attachment; filename="contactos.csv"'
        return response

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        g.user = (
            get_db().execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
            .fetchone()
            if user_id is not None
            else None
        )

    @app.teardown_appcontext
    def close_db(_error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    return app


def safe_csv_cell(value):
    value = value or ""
    if value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def init_db(app):
    database_path = Path(app.config["DATABASE"])
    database_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(database_path)
    try:
        with db:
            db.executescript(
                """
                PRAGMA foreign_keys = ON;
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL DEFAULT '',
                    phone TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS contacts_user_name
                    ON contacts(user_id, name);
                """
            )
    finally:
        db.close()


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
