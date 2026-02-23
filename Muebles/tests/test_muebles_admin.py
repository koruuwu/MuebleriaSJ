from django.test import TestCase, SimpleTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

from Muebles.admin import MuebleForm, TamañoForm, MuebleMaterialeForm
from Muebles.models import Mueble, Tamaño


class MuebleFormTest(TestCase):
    def setUp(self):
        # Modelos relacionados (dinámico, sin asumir app)
        CategoriaMueble = Mueble._meta.get_field("categoria").related_model
        Medida = Mueble._meta.get_field("medida").related_model

        # Crear categoría (si tu modelo exige imagen/imagen_url, los seteamos)
        # Si tu modelo NO tiene esos campos, entonces bórralos aquí.
        self.categoria = CategoriaMueble.objects.create(
            nombre="Salas",
            descripcion="Categoria para salas",
            imagen="muebles_cat/test.jpg",
            imagen_url="muebles_cat/test.jpg",
        )

        # Medida: ajusta campos si tu modelo Medida tiene otra estructura
        self.medida = Medida.objects.create(nombre="cm")

        self.tamano = Tamaño.objects.create(
            nombre="Mediano",
            descripcion="Tamaño mediano para 3-4 personas"
        )

        self.valid_data = {
            "nombre": "Sofa Modelo Luna",
            "descripcion": "Mueble color gris, ideal para 4 personas",
            "precio_base": "20000.50",
            "alto": 100,
            "ancho": 200,
            "largo": 90,
            "medida": self.medida.id,
            "categoria": self.categoria.id,
            "tamano": self.tamano.id,
            "stock_minimo": 5,
            "stock_maximo": 50,
            "Descontinuado": False,
            # archivo_temp es opcional (required=False)
        }

    def test_form_valido_sin_archivo_temp(self):
        form = MuebleForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_nombre_obligatorio(self):
        data = self.valid_data.copy()
        data["nombre"] = ""
        form = MuebleForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_nombre_muy_corto(self):
        data = self.valid_data.copy()
        data["nombre"] = "abc"  # min_len=4
        form = MuebleForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_nombre_con_dobles_espacios(self):
        data = self.valid_data.copy()
        data["nombre"] = "Sofa  Luna"  # doble espacio
        form = MuebleForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_archivo_temp_extension_invalida(self):
        data = self.valid_data.copy()
        archivo = SimpleUploadedFile(
            "foto.gif",
            b"fakecontent",
            content_type="image/gif"
        )
        form = MuebleForm(data=data, files={"archivo_temp": archivo})
        self.assertFalse(form.is_valid())
        self.assertIn("archivo_temp", form.errors)

    def test_archivo_temp_mime_invalido(self):
        data = self.valid_data.copy()
        archivo = SimpleUploadedFile(
            "foto.jpg",
            b"fakecontent",
            content_type="application/pdf"  # mime inválido
        )
        form = MuebleForm(data=data, files={"archivo_temp": archivo})
        self.assertFalse(form.is_valid())
        self.assertIn("archivo_temp", form.errors)

    def test_archivo_temp_valido_jpg(self):
        data = self.valid_data.copy()
        archivo = SimpleUploadedFile(
            "foto.jpg",
            b"fakecontent",
            content_type="image/jpeg"
        )
        form = MuebleForm(data=data, files={"archivo_temp": archivo})
        self.assertTrue(form.is_valid(), form.errors)

    def test_archivo_temp_valido_png(self):
        data = self.valid_data.copy()
        archivo = SimpleUploadedFile(
            "foto.png",
            b"fakecontent",
            content_type="image/png"
        )
        form = MuebleForm(data=data, files={"archivo_temp": archivo})
        self.assertTrue(form.is_valid(), form.errors)


class TamanoFormTest(TestCase):
    def setUp(self):
        self.valid_data = {
            "nombre": "Pequeño",
            "descripcion": "Tamaño reducido para 2 personas"
        }

    def test_form_valido(self):
        form = TamañoForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_nombre_obligatorio(self):
        data = self.valid_data.copy()
        data["nombre"] = ""
        form = TamañoForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_nombre_muy_corto(self):
        data = self.valid_data.copy()
        data["nombre"] = "abc"  # min_len=4
        form = TamañoForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_nombre_con_dobles_espacios(self):
        data = self.valid_data.copy()
        data["nombre"] = "Pe  queño"
        form = TamañoForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)



class MuebleMaterialeFormTest(SimpleTestCase):

    def test_cantidad_cero_invalida(self):
        form = MuebleMaterialeForm()
        form.cleaned_data = {"cantidad": 0}
        with self.assertRaises(ValidationError):
            form.clean_cantidad()

    def test_cantidad_negativa_invalida(self):
        form = MuebleMaterialeForm()
        form.cleaned_data = {"cantidad": -5}
        with self.assertRaises(ValidationError):
            form.clean_cantidad()

    def test_cantidad_valida(self):
        form = MuebleMaterialeForm()
        form.cleaned_data = {"cantidad": 2}
        self.assertEqual(form.clean_cantidad(), 2)
