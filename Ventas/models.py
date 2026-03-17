from django.db import models
from archivos.models import *
from django.core.exceptions import ValidationError
from Muebles.models import Mueble
from Sucursales.models import Caja, Sucursale, Cai
from Empleados.models import PerfilUsuario

# Tus modelos se generarán aquí con inspectdb
class OrdenesVenta(models.Model):
    id = models.BigAutoField(primary_key=True)
    cai_usado = models.ForeignKey(Cai, models.DO_NOTHING, blank=True, null=True)
    id_factura = models.CharField(blank=True, null=True)  # Field name made lowercase.
    id_cotizacion = models.ForeignKey('Compras.Cotizacione', models.DO_NOTHING, blank=True, null=True, verbose_name="Cotizacion") 
    id_empleado = models.ForeignKey(PerfilUsuario, models.DO_NOTHING, blank=True, null=True, verbose_name="Empleado") # Field name made lowercase.
    id_cliente = models.ForeignKey('clientes.Cliente', models.DO_NOTHING, verbose_name="Cliente")  # Field name made lowercase.
    rtn = models.BooleanField(blank=False, null=False)  # Field name made lowercase.
    descuento = models.FloatField(null=True, blank=True)  # Field name made lowercase.
    subtotal = models.FloatField()  # Field name made lowercase.
    isv = models.FloatField()  # Field name made lowercase.
    total = models.FloatField()  # Field name made lowercase.
    cuotas = models.BooleanField(blank=False, null=False)
    pagado = models.FloatField(blank=True, null=True)
    id_estado_pago = models.ForeignKey('EstadoPagos', models.DO_NOTHING, verbose_name="Estado del pago")  # Field name made lowercase.
    id_metodo_pago = models.ForeignKey('MetodosPago', models.DO_NOTHING, verbose_name="Metodo de pago")  # Field name made lowercase.
    fecha_orden = models.DateTimeField( auto_now_add=True )  # Field name made lowercase.
    fecha_entrega = models.DateField()  # Field name made lowercase
    efectivo = models.FloatField(blank=True, null=True)
    num_tarjeta = models.CharField(blank=True, null=True, max_length=4, verbose_name="Numero de Tarjeta")

    def __str__(self):
        if self.id_factura:
            return self.id_factura
        return f"Orden #{self.id} (Sin factura)"  

    class Meta:
        managed = True
        db_table = 'Ordenes_Ventas'
        verbose_name = 'Orden de Venta'
        verbose_name_plural = 'Ordenes de Ventas'
        permissions = [
            ("export_pdf_ordenesventa", "Puede exportar Órdenes de Venta a PDF"),
            ("export_excel_ordenesventa", "Puede exportar Órdenes de Venta a Excel"),
        ]
    

class EstadoPagos(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100)  # Field name made lowercase.
    descripcion = models.CharField(max_length=255)  # Field name made lowercase.

    def __str__(self):
        return self.nombre

    class Meta:
        managed = True
        db_table = 'Estado_Pagos'
        verbose_name = 'Estado de Pago'
        verbose_name_plural = 'Estados de Pago'
        permissions = [
            ("export_pdf_estadopagos", "Puede exportar Estados de Pago a PDF"),
            ("export_excel_estadopagos", "Puede exportar Estados de Pago a Excel"),
        ]

class MetodosPago(models.Model):
    id = models.BigAutoField(primary_key=True)
    tipo = models.CharField(max_length=100)  # Field name made lowercase.
    descripcion = models.CharField(max_length=255)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'Metodos_Pago'
        verbose_name = 'Método de Pago'
        verbose_name_plural = 'Métodos de Pago'
        permissions = [
            ("export_pdf_metodospago", "Puede exportar Métodos de Pago a PDF"),
            ("export_excel_metodospago", "Puede exportar Métodos de Pago a Excel"),
        ]

    def __str__(self):
        return self.tipo
    
class DetallesOrdene(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_orden = models.ForeignKey('OrdenesVenta', models.DO_NOTHING, verbose_name="Orden")  # Field name made lowercase.
    id_mueble = models.ForeignKey(Mueble, models.DO_NOTHING, verbose_name="Mueble")  # Field name made lowercase.
    precio_unitario = models.FloatField(verbose_name="Precio Unitario")  # Field name made lowercase.
    cantidad = models.BigIntegerField(verbose_name="Cantidad")  # Field name made lowercase.
    subtotal = models.FloatField(verbose_name="Subtotal")



    class Meta:
        managed = True
        db_table = 'Detalles_Orden'
        verbose_name = 'Detalle de Orden'
        verbose_name_plural = 'Detalles de Ordenes'
        permissions = [
            ("export_pdf_detallesordene", "Puede exportar Detalles de Orden a PDF"),
            ("export_excel_detallesordene", "Puede exportar Detalles de Orden a Excel"),
        ]