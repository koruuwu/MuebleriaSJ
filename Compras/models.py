from django.db import models
from Sucursales.models import Sucursale
from Muebles.models import Mueble

class InventarioMueble(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_mueble = models.ForeignKey(Mueble, models.DO_NOTHING, db_column='ID_Mueble')  # Field name made lowercase.
    cantidad_disponible = models.BigIntegerField(db_column='Cantidad_Disponible')  # Field name made lowercase.
    estado = models.BooleanField(db_column='Estado')  # Field name made lowercase.
    ubicación = models.ForeignKey(Sucursale, models.DO_NOTHING, db_column='ubicación', blank=True, null=True)
    ultima_entrada = models.DateField(db_column='ultima entrada', blank=True, null=True)  # Field renamed to remove unsuitable characters.
    ultima_salida = models.DateField(db_column='ultima salida', blank=True, null=True)  # Field renamed to remove unsuitable characters.
    estado = models.ForeignKey('Estados', models.DO_NOTHING, db_column='Estado', blank=False, null=False, default=1)  
    def __str__(self):
        return self.id_mueble
    class Meta:
        managed = False
        db_table = 'Inventario_Muebles'

class Estados(models.Model):
    id = models.BigAutoField(primary_key=True)
    tipo = models.CharField(db_column='Tipo', blank=True, null=True)  # Field name made lowercase.
    def __str__(self):
        return self.tipo


    class Meta:
        managed = False
        db_table = 'Estados_M'