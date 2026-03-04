from .settings import *

TEST_RUNNER = "proyecto.realdb_runner.NoDatabaseCreationRunner"

# Asegurar conexiones cortas
DATABASES["default"]["CONN_MAX_AGE"] = 0