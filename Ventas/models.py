from django.db import models
from archivos.models import *
from django.core.exceptions import ValidationError

# Tus modelos se generarán aquí con inspectdb
class OrdenesVenta(models.Model):
    id = models.BigAutoField(primary_key=True)
    fecha_orden = models.DateTimeField(db_column='Fecha_Orden')  # Field name made lowercase.
    fecha_entrega = models.DateField(db_column='Fecha_Entrega')  # Field name made lowercase.
    isv = models.FloatField(db_column='ISV')  # Field name made lowercase.
    id_factura = models.BigIntegerField(db_column='ID_Factura')  # Field name made lowercase.
    subtotal = models.FloatField(db_column='SubTotal')  # Field name made lowercase.
    total = models.FloatField(db_column='Total')  # Field name made lowercase.
    descuento = models.FloatField(db_column='Descuento')  # Field name made lowercase.
    id_empleado = models.ForeignKey('Empleados.Empleado', models.DO_NOTHING, db_column='ID_Empleado', verbose_name="Empleado")  # Field name made lowercase.
    id_cliente = models.ForeignKey('clientes.Cliente', models.DO_NOTHING, db_column='ID_Cliente',verbose_name="Cliente")  # Field name made lowercase.
    id_cotizacion = models.ForeignKey('Compras.Cotizacione', models.DO_NOTHING, db_column='ID_Cotizacion', blank=True, null=True, verbose_name="Cotizacion")  # Field name made lowercase.
    id_estado_pago = models.ForeignKey('EstadoPagos', models.DO_NOTHING, db_column='ID_Estado_Pago', verbose_name="Estado del pago")  # Field name made lowercase.
    id_metodo_pago = models.ForeignKey('MetodosPago', models.DO_NOTHING, db_column='ID_Metodo_Pago', verbose_name="Metodo de pago")  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Ordenes_Ventas'
    

class EstadoPagos(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(db_column='Nombre')  # Field name made lowercase.
    descripcion = models.CharField(db_column='Descripcion')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Estado_Pagos'

class MetodosPago(models.Model):
    id = models.BigAutoField(primary_key=True)
    tipo = models.CharField(db_column='Tipo')  # Field name made lowercase.
    descripcion = models.CharField(db_column='Descripcion')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Metodos_Pago'

    def __str__(self):
        return self.tipo