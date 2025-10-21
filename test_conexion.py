import os
import django
from django.db import connections
from django.db.utils import OperationalError

# Apunta a tus settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')

django.setup()

db_conn = connections['default']
try:
    c = db_conn.cursor()
    print("¡Conexión exitosa a la base de datos!")
except OperationalError as e:
    print("Error de conexión:", e)

#TEST CONEXION A SUPABASE NO TOCAR