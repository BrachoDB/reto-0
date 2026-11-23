import csv
import io
import tempfile
import unittest
from pathlib import Path

from app import create_app


class ContactsAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-key",
                "DATABASE": str(Path(self.temp_dir.name) / "test.sqlite"),
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def csrf_token(self):
        response = self.client.get("/register")
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as session:
            return session["csrf_token"]

    def post(self, url, data):
        return self.client.post(url, data={**data, "csrf_token": self.csrf_token()})

    def register_and_login(self, email="ana@example.com"):
        response = self.post(
            "/register", {"email": email, "password": "una-clave-segura"}
        )
        self.assertEqual(response.status_code, 302)
        return self.post(
            "/login", {"email": email, "password": "una-clave-segura"}
        )

    def test_registration_login_contact_search_and_csv_export(self):
        self.register_and_login()
        self.post(
            "/contacts/new",
            {
                "name": "María López",
                "email": "maria@example.com",
                "phone": "555-0101",
                "notes": "Amiga",
            },
        )
        self.post(
            "/contacts/new",
            {"name": "Carlos Díaz", "email": "", "phone": "", "notes": ""},
        )

        response = self.client.get("/contacts?q=maría")
        self.assertEqual(response.status_code, 200)
        self.assertIn("María López".encode(), response.data)
        self.assertNotIn("Carlos Díaz".encode(), response.data)

        response = self.client.get("/contacts/export.csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.content_type)
        rows = list(csv.reader(io.StringIO(response.get_data(as_text=True).lstrip("\ufeff"))))
        self.assertEqual(rows[0], ["Nombre", "Correo", "Teléfono", "Notas"])
        self.assertEqual(rows[1], ["Carlos Díaz", "", "", ""])
        self.assertEqual(rows[2], ["María López", "maria@example.com", "555-0101", "Amiga"])

    def test_contacts_are_private_and_csrf_is_required(self):
        self.register_and_login()
        response = self.client.post(
            "/contacts/new",
            data={"name": "Privado", "email": "", "phone": "", "notes": ""},
        )
        self.assertEqual(response.status_code, 400)
        self.post(
            "/contacts/new",
            {"name": "Privado", "email": "", "phone": "", "notes": ""},
        )
        self.post("/logout", {})
        self.register_and_login("otra@example.com")
        self.assertNotIn("Privado".encode(), self.client.get("/contacts").data)
        response = self.client.get("/contacts/export.csv")
        rows = list(csv.reader(io.StringIO(response.get_data(as_text=True).lstrip("\ufeff"))))
        self.assertEqual(rows, [["Nombre", "Correo", "Teléfono", "Notas"]])

    def test_registration_rejects_short_password(self):
        response = self.post(
            "/register", {"email": "corta@example.com", "password": "123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("al menos 10 caracteres".encode(), response.data)


if __name__ == "__main__":
    unittest.main()
