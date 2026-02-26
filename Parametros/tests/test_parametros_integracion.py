from django.test import TestCase
from django.core.exceptions import ValidationError

from Parametros.models import Parametro
from Parametros.admin import ParametroForm

class ParametroCrudTests(TestCase):
    def test_crear_parametro(self):
        obj = Parametro.objects.create(nombre="ISV", valor="15")
        self.assertTrue(Parametro.objects.filter(id=obj.id).exists())

    def test_editar_parametro(self):
        obj = Parametro.objects.create(nombre="ISV", valor="15")
        obj.nombre = "ISV Actual"
        obj.valor = "18"
        obj.save()

        obj_db = Parametro.objects.get(id=obj.id)
        self.assertEqual(obj_db.nombre, "ISV Actual")
        self.assertEqual(obj_db.valor, "18")

    def test_eliminar_parametro(self):
        obj = Parametro.objects.create(nombre="Borrar", valor="1")
        obj_id = obj.id
        obj.delete()
        self.assertFalse(Parametro.objects.filter(id=obj_id).exists())