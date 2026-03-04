from django.test import SimpleTestCase
from django.db import connections
from django.db.utils import OperationalError

class RealDBConnectionTests(SimpleTestCase):
    databases = {"default"}  # habilita acceso a DB en SimpleTestCase

    def test_db_is_reachable(self):
        try:
            connections["default"].cursor()
        except OperationalError as e:
            self.fail(f"No se pudo conectar a la BD real (default). Detalle: {e}")