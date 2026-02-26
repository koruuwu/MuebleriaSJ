from django.test import SimpleTestCase
from Sucursales.admin import SucursaleForm

class TestForms(SimpleTestCase):

    def test_sucursal_form(self):
        form_data = {
            'codigo_sucursal': '001',
            'nombre': 'Sucursal Principal',
            'direccion': 'Calle Principal #123',
            'telefono': '9555-1234',
            'rtn': '0801-1999-023999'
        }
        form = SucursaleForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_sucursal_form_invalid_codigo(self):
        form_data = {
            'codigo_sucursal': 'JA001',
            'nombre': 'Sucursal Principal',
            'direccion': 'Calle Principal #123',
            'telefono': '9555-1234',
            'rtn': '08011999023999'
        }
        form = SucursaleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('codigo_sucursal', form.errors)

    def test_sucursal_form_nombre_obligatorio(self):
        form_data = {
            'codigo_sucursal': '001',
            'nombre': '',
            'direccion': 'Calle Principal #123',
            'telefono': '9555-1234',
            'rtn': '08011999023999'
        }
        form = SucursaleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_con_caracteres_especiales(self):
        form_data = {
            'codigo_sucursal': '001',
            'nombre': '<script>alert(1)</script>',
            'direccion': 'Calle',
            'telefono': '9555-1234',
            'rtn': '08011999023999'
        }

        form = SucursaleForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_sucursal_form_codigo_obligatorio(self):
        form_data = {
            'nombre': 'Sucursal Principal',
            'direccion': 'Calle Principal #123',
            'telefono': '9555-1234',
            'rtn': '08011999023999'
        }
        form = SucursaleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('codigo_sucursal', form.errors)

    def test_sucursal_form_rtn_invalido_Letras(self):
        form_data = {
            'codigo_sucursal': '001',
            'nombre': 'Sucursal Principal',
            'direccion': 'Calle Principal #123',
            'telefono': '9555-1234',
            'rtn': '0801200512A31'
        }
        form = SucursaleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rtn', form.errors)

    def test_sucursal_form_rtn_invalido_Longitud(self):
        form_data = {
            'codigo_sucursal': '001',
            'nombre': 'Sucursal Principal',
            'direccion': 'Calle Principal #123',
            'telefono': '9555-1234',
            'rtn': '080120051231'
        }
        form = SucursaleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rtn', form.errors)    

    def test_sucursal_form_telefono_invalido(self):
        form_data = {
            'codigo_sucursal': '001',
            'nombre': 'Sucursal Principal',
            'direccion': 'Calle Principal #123',
            'telefono': 'abc123',
            'rtn': '08011999023999'
        }
        form = SucursaleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('telefono', form.errors)


