from django.test import TestCase
from Empleados.admin import UsuarioCreationForm


class UsuarioCreationFormTest(TestCase):

    def setUp(self):
        self.valid_data = {
            "username": "empleado01",
            "password1": "PasswordSeguro123",
            "password2": "PasswordSeguro123",
        }

    def test_form_valido(self):
        form = UsuarioCreationForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_username_obligatorio(self):
        data = self.valid_data.copy()
        data["username"] = ""

        form = UsuarioCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_username_minimo_5_caracteres(self):
        data = self.valid_data.copy()
        data["username"] = "abc"

        form = UsuarioCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_username_caracteres_invalidos(self):
        data = self.valid_data.copy()
        data["username"] = "empleado@01"

        form = UsuarioCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_username_solo_numeros(self):
        data = self.valid_data.copy()
        data["username"] = "123456"

        form = UsuarioCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_passwords_no_coinciden(self):
        data = self.valid_data.copy()
        data["password2"] = "PasswordDiferente123"

        form = UsuarioCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
