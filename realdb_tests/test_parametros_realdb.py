from django.test import TestCase
from Parametros.models import Parametro

class ParametroRealDBCrudTests(TestCase):
    
    databases = {"default"}

    def setUp(self):
        self.test_prefix = "TEST_PARAM_"
        # Limpieza previa por si quedaron basuras de una corrida anterior
        Parametro.objects.filter(nombre__startswith=self.test_prefix).delete()

    def tearDown(self):
        # Limpieza final
        Parametro.objects.filter(nombre__startswith=self.test_prefix).delete()

    def test_insert_parametro_realdb(self):
        p = Parametro.objects.create(nombre=f"{self.test_prefix}INSERT", valor="10")
        self.assertIsNotNone(p.id)

        # Verificar que realmente está en la BD
        self.assertTrue(Parametro.objects.filter(id=p.id).exists())

    def test_update_parametro_realdb(self):
        p = Parametro.objects.create(nombre=f"{self.test_prefix}UPDATE", valor="10")
        p.valor = "25"
        p.save(update_fields=["valor"])

        p2 = Parametro.objects.get(id=p.id)
        self.assertEqual(p2.valor, "25")

    def test_delete_parametro_realdb(self):
        p = Parametro.objects.create(nombre=f"{self.test_prefix}DELETE", valor="10")
        pid = p.id
        p.delete()

        self.assertFalse(Parametro.objects.filter(id=pid).exists())