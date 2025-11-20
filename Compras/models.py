from django.db import models
from Sucursales.models import Sucursale
from Muebles.models import Mueble
from clientes.models import Cliente

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
     return str(self.id_mueble)

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


class Cotizacione(models.Model):
    id = models.BigAutoField(primary_key=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(db_column='Estado', default=True)  # Field name made lowercase.
    fecha_vencimiento = models.DateField(db_column='Fecha_Vencimiento')  # Field name made lowercase.
    cliente = models.ForeignKey(Cliente, models.DO_NOTHING, db_column='ID_Cliente')  # Field name made lowercase.
    def __str__(self):
        return str(self.cliente)

    class Meta:
        managed = False
        db_table = 'Cotizaciones'

class Parametro(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(db_column='Nombre', blank=True, null=True)  # Field name made lowercase.
    valor = models.CharField(db_column='Valor', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Parametros'

    def __str__(self):
        return f"{self.nombre} = {self.valor}"
    
class DetalleCotizaciones(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_cotizacion = models.ForeignKey(Cotizacione, models.DO_NOTHING, db_column='ID_Cotizacion')  # Field name made lowercase.
    id_mueble = models.ForeignKey(Mueble, models.DO_NOTHING, db_column='ID_Mueble')  # Field name made lowercase.
    cantidad = models.BigIntegerField(db_column='Cantidad')  # Field name made lowercase.
    precio_unitario = models.FloatField(db_column='Precio_Unitario')  # Field name made lowercase.
    subtotal = models.FloatField(db_column='SubTotal')  # Field name made lowercase.

    def __str__(self):
        return str(self.id_cotizacion)

    class Meta:
        managed = False
        db_table = 'Detalle_Cotizaciones'