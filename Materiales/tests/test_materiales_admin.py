from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django import forms
from Materiales.admin import *
from Materiales.models import CategoriasMateriale, UnidadesMedida


class MaterialeFormTest(TestCase):

    def setUp(self):
        self.categoria = CategoriasMateriale.objects.create(nombre="Maderas")
        self.medida = UnidadesMedida.objects.create(nombre="Unidad")
        self.image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61',
            content_type='image/jpeg'
                )


        self.valid_data = {
            "nombre": "Madera Pino",
            "stock_minimo": 10,
            "stock_maximo": 100,
            "categoria": self.categoria.id,
            "medida": self.medida.id,
            "archivo_temp": self.image,
            "imagen": self.image.name

            
            
        }

    def test_form_valido(self):
        form = MaterialeForm(data=self.valid_data, files={'imagen': self.image})
        
        self.assertTrue(form.is_valid(), form.errors)

    def test_nombre_obligatorio(self):
        data = self.valid_data.copy()
        data["nombre"] = ""

        form = MaterialeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

        form = MaterialeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_stock_minimo_obligatorio(self):
        data = self.valid_data.copy()
        data["stock_minimo"] = ""

        form = MaterialeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("stock_minimo", form.errors)

    def test_stock_maximo_obligatorio(self):
        data = self.valid_data.copy()
        data["stock_maximo"] = ""

        form = MaterialeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("stock_maximo", form.errors)

    def test_stock_maximo_menor_que_minimo(self):
        data = self.valid_data.copy()
        data["stock_minimo"] = 50
        data["stock_maximo"] = 20

        form = MaterialeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("stock_maximo", form.errors)

    def test_stock_maximo_igual_minimo(self):
        data = self.valid_data.copy()
        data["stock_minimo"] = 30
        data["stock_maximo"] = 30

        form = MaterialeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("stock_maximo", form.errors)

    def test_stock_minimo_longitud_excedida(self):
        data = self.valid_data.copy()
        data["stock_minimo"] = 12345  # 5 dígitos (máx permitido 4)

        form = MaterialeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("stock_minimo", form.errors)

    def test_stock_maximo_longitud_excedida(self):
        data = self.valid_data.copy()
        data["stock_maximo"] = 123456  # 6 dígitos (máx permitido 5)

        form = MaterialeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("stock_maximo", form.errors)




class DummyUser:
    def has_perm(self, perm_name: str) -> bool:
        return True


class DummyRequest:
    def __init__(self, user=None):
        self.user = user or DummyUser()


class DummyObj:
    def __init__(self, pk=None):
        self.pk = pk


# -------------------------
# Tests puros de FORMS
# -------------------------

class ProveFormCleanCompaniaPuroTest(SimpleTestCase):
    def test_compania_valida(self):
        form = ProveForm()
        form.cleaned_data = {"compañia": "Maderas el Tropico SA"}
        salida = form.clean_compañia()
        self.assertEqual(salida, "Maderas el Tropico SA")

    def test_compania_muy_corta_invalida(self):
        form = ProveForm()
        form.cleaned_data = {"compañia": "Maderas"}  # < 10
        with self.assertRaises(forms.ValidationError):
            form.clean_compañia()

    def test_compania_muy_larga_invalida(self):
        form = ProveForm()
        form.cleaned_data = {"compañia": "A" * 61}  # > 60
        with self.assertRaises(forms.ValidationError):
            form.clean_compañia()


class MedFormCleanNombreYAbreviaturaPuroTest(SimpleTestCase):
    def test_abreviatura_valida(self):
        form = MedForm()
        form.cleaned_data = {"abreviatura": "Cm"}
        salida = form.clean_abreviatura()
        self.assertEqual(salida, "Cm")

    def test_abreviatura_vacia_invalida(self):
        form = MedForm()
        form.cleaned_data = {"abreviatura": ""}
        with self.assertRaises(forms.ValidationError):
            form.clean_abreviatura()

    def test_abreviatura_muy_larga_invalida(self):
        form = MedForm()
        form.cleaned_data = {"abreviatura": "ABCDE"}  # > 4
        with self.assertRaises(forms.ValidationError):
            form.clean_abreviatura()

    def test_nombre_valido(self):
        form = MedForm()
        form.cleaned_data = {"nombre": "Unidad"}  # 6 letras (entre 4 y 10)
        salida = form.clean_nombre()
        self.assertEqual(salida, "Unidad")

    def test_nombre_muy_corto_invalido(self):
        form = MedForm()
        form.cleaned_data = {"nombre": "Cm"}  # < 4
        with self.assertRaises(forms.ValidationError):
            form.clean_nombre()

    def test_nombre_muy_largo_invalido(self):
        form = MedForm()
        form.cleaned_data = {"nombre": "ABCDEFGHIJKLMN"}  # 11 > 10
        with self.assertRaises(forms.ValidationError):
            form.clean_nombre()


class MaterialProveedorFormCleanTiempoPuroTest(SimpleTestCase):
    def test_tiempo_valido_1_digito(self):
        form = MaterialProveedorForm()
        form.cleaned_data = {"tiempo": 5}
        salida = form.clean_tiempo()
        self.assertIn(str(salida), ["5"]) 

    def test_tiempo_valido_2_digitos(self):
        form = MaterialProveedorForm()
        form.cleaned_data = {"tiempo": 10}
        salida = form.clean_tiempo()
        self.assertIn(str(salida), ["10"])

    def test_tiempo_muy_largo_invalido(self):
        form = MaterialProveedorForm()
        form.cleaned_data = {"tiempo": 100}  # 3 dígitos > max_len=2
        with self.assertRaises(forms.ValidationError):
            form.clean_tiempo()
