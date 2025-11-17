from django.db import models

# Create your models here.
class Sucursale(models.Model):
    id = models.BigAutoField(primary_key=True)
    fecha_registro = models.DateTimeField()
    nombre = models.CharField(db_column='Nombre')  # Field name made lowercase.
    direccion = models.CharField(db_column='Direccion')  # Field name made lowercase.
    telefono = models.CharField(db_column='Telefono')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Sucursales'