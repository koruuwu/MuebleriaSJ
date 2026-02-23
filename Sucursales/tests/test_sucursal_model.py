from django.test import TestCase
from Sucursales.models import Sucursale, Cai, Caja



class TestModels(TestCase):

    def setUp(self):
        self.sucursal1 = Sucursale.objects.create(
            nombre="Sucursal Central",
            codigo_sucursal="001",
            )
        
    def test_sucursal_nombre(self):
        self.assertEqual(self.sucursal1.nombre, "Sucursal Central")