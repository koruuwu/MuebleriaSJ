from django.test.runner import DiscoverRunner

class NoDatabaseCreationRunner(DiscoverRunner):
    """
    Test runner que NO crea ni destruye base de datos.
    Usa la base real tal cual.
    """

    def setup_databases(self, **kwargs):
        # No crear base de datos de test
        return None

    def teardown_databases(self, old_config, **kwargs):
        # No destruir base de datos
        pass