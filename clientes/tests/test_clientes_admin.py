from django.test import SimpleTestCase
from clientes.admin import ClienteForm


class TestClienteForm(SimpleTestCase):

    def setUp(self):
        self.valid_data = {
            'nombre': 'Alejandro Martínez López',
            'telefono': '9876-5432',
            'direccion': 'Colonia Miraflores, Tegucigalpa',
            'rtn': '08011999023999'
        }

    # ----------------------------
    # CASO VÁLIDO
    # ----------------------------

    def test_cliente_form_valido(self):
        form = ClienteForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), form.errors)

    # ----------------------------
    # NOMBRE
    # ----------------------------

    def test_nombre_obligatorio(self):
        data = self.valid_data.copy()
        data['nombre'] = ''
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_muy_corto(self):
        data = self.valid_data.copy()
        data['nombre'] = 'Juan'
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_con_dobles_espacios(self):
        data = self.valid_data.copy()
        data['nombre'] = 'Alejandro  Martinez'
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_con_letras_repetidas(self):
        data = self.valid_data.copy()
        data['nombre'] = 'Alejannndro Martinez'
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_con_vocabulario_soez(self):
        data = self.valid_data.copy()
        data['nombre'] = 'Cliente puta ejemplo'
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    # ----------------------------
    # TELÉFONO
    # ----------------------------

    def test_telefono_invalido_letras(self):
        data = self.valid_data.copy()
        data['telefono'] = 'abcd-1234'
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('telefono', form.errors)

    def test_telefono_longitud_invalida(self):
        data = self.valid_data.copy()
        data['telefono'] = '1234'
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('telefono', form.errors)

    def test_telefono_inicio_invalido(self):
        data = self.valid_data.copy()
        data['telefono'] = '1123-4567'  # no inicia con 2,3,7,8,9
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('telefono', form.errors)

    # ----------------------------
    # DIRECCIÓN
    # ----------------------------

    def test_direccion_muy_corta(self):
        data = self.valid_data.copy()
        data['direccion'] = 'Colonia'
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('direccion', form.errors)

    def test_direccion_dobles_espacios(self):
        data = self.valid_data.copy()
        data['direccion'] = 'Colonia  Miraflores'
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('direccion', form.errors)

    # ----------------------------
    # RTN
    # ----------------------------

    def test_rtn_con_letras(self):
        data = self.valid_data.copy()
        data['rtn'] = '0801A999023999'
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('rtn', form.errors)

    def test_rtn_longitud_invalida(self):
        data = self.valid_data.copy()
        data['rtn'] = '08011999023'
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('rtn', form.errors)
