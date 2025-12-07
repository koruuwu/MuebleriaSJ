from django.db import models
from  Muebles.models import Mueble
from Empleados.models import PerfilUsuario
# Create your models here.
class OrdenMensuale(models.Model):
    id = models.BigAutoField(primary_key=True)
    fecha_creacion = models.DateTimeField(db_column='Fecha_creacion')  # Field name made lowercase.
    fecha_fin = models.DateField(db_column='Fecha_fin', blank=True, null=True)  # Field name made lowercase.
    estado = models.CharField(blank=True, null=True)
    observaciones = models.CharField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Orden_Mensuales'

class OrdenMensualDetalle(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_orden = models.ForeignKey('OrdenMensuale', models.DO_NOTHING, db_column='id_orden', blank=True, null=True)
    id_mueble = models.ForeignKey(Mueble, models.DO_NOTHING, db_column='id_mueble', blank=True, null=True)
    cantidad_planificada = models.BigIntegerField(blank=True, null=True)
    cantidad_producida = models.BigIntegerField(blank=True, null=True)
    estado = models.BigIntegerField(blank=True, null=True)
    entrega_estim = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Orden_mensual_detalle'

class AportacionEmpleado(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_orden_detalle = models.ForeignKey('OrdenMensualDetalle', models.DO_NOTHING, blank=True, null=True)
    id_empleado = models.ForeignKey(PerfilUsuario, models.DO_NOTHING, blank=True, null=True) # Field name made lowercase.
    cant_aprobada = models.BigIntegerField(blank=True, null=True)
    cantidad_finalizada = models.BigIntegerField(blank=True, null=True)
    estado = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'aportacion_empleado'