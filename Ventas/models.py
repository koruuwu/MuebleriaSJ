from django.db import models
from archivos.models import *
from django.core.exceptions import ValidationError
from Muebles.models import Mueble
from Sucursales.models import Caja, Sucursale
from Empleados.models import PerfilUsuario

# Tus modelos se generarán aquí con inspectdb
class OrdenesVenta(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_factura = models.CharField(db_column='ID_Factura', blank=True, null=True)  # Field name made lowercase.
    id_cotizacion = models.ForeignKey('Compras.Cotizacione', models.DO_NOTHING, db_column='ID_Cotizacion', blank=True, null=True, verbose_name="Cotizacion") 
    id_empleado = models.ForeignKey(PerfilUsuario, models.DO_NOTHING, db_column='id_empleado', blank=True, null=True) # Field name made lowercase.
    id_cliente = models.ForeignKey('clientes.Cliente', models.DO_NOTHING, db_column='ID_Cliente',verbose_name="Cliente")  # Field name made lowercase.
    descuento = models.FloatField(db_column='Descuento', null=True, blank=True)  # Field name made lowercase.
    subtotal = models.FloatField(db_column='SubTotal')  # Field name made lowercase.
    isv = models.FloatField(db_column='ISV')  # Field name made lowercase.
    total = models.FloatField(db_column='Total')  # Field name made lowercase.
    pagado = models.FloatField(blank=True, null=True)
    id_estado_pago = models.ForeignKey('EstadoPagos', models.DO_NOTHING, db_column='ID_Estado_Pago', verbose_name="Estado del pago")  # Field name made lowercase.
    id_metodo_pago = models.ForeignKey('MetodosPago', models.DO_NOTHING, db_column='ID_Metodo_Pago', verbose_name="Metodo de pago")  # Field name made lowercase.
    fecha_orden = models.DateTimeField(db_column='Fecha_Orden', auto_now_add=True )  # Field name made lowercase.
    fecha_entrega = models.DateField(db_column='Fecha_Entrega')  # Field name made lowercase

    
    
    
    

    

    class Meta:
        managed = False
        db_table = 'Ordenes_Ventas'
    

class EstadoPagos(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(db_column='Nombre')  # Field name made lowercase.
    descripcion = models.CharField(db_column='Descripcion')  # Field name made lowercase.

    def __str__(self):
        return self.nombre

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
    
class DetallesOrdene(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_orden = models.ForeignKey('OrdenesVenta', models.DO_NOTHING, db_column='ID_Orden')  # Field name made lowercase.
    id_mueble = models.ForeignKey(Mueble, models.DO_NOTHING, db_column='ID_Muebles')  # Field name made lowercase.
    precio_unitario = models.FloatField(db_column='Precio_Unitario')  # Field name made lowercase.
    cantidad = models.BigIntegerField(db_column='Cantidad')  # Field name made lowercase.
    subtotal = models.FloatField(db_column='subtotal')



    class Meta:
        managed = False
        db_table = 'Detalles_Orden'