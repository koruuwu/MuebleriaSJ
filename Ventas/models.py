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
    
    id_cliente = models.ForeignKey('clientes.Cliente', models.DO_NOTHING, db_column='ID_Cliente')  # Field name made lowercase.
    

    class Meta:
        managed = False
        db_table = 'Ordenes_Ventas'