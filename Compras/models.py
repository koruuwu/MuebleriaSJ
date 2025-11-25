from django.db import models
from Sucursales.models import Sucursale
from Muebles.models import Mueble
from clientes.models import Cliente
from Materiales.models import Materiale, Proveedore, MaterialProveedore
from django.utils import timezone
from django.db import transaction
from Sucursales.models import Sucursale
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

#-------------------COMPRAS----------------
ALTA = 'alta'
MEDIA = 'media'
BAJA = 'baja'

P_CHOICES = [
     (ALTA, 'Alta'),
    (MEDIA, 'Media'),
    (BAJA, 'Baja'),
]


class ListaCompra(models.Model):
    PENDIENTE = 'pendiente'
    APROBADA = 'aprobada'
    RECHAZADA='rechazada'
    INCOMPLETA='incompleta'
    COMPLETA='completa'
    

    S_CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (APROBADA, 'Aprobada'),
        (RECHAZADA, 'Rechazada'),
        (INCOMPLETA, 'Incompleta'),
        (COMPLETA, 'Completa'),
    ]
 

    id = models.BigAutoField(primary_key=True)
    fecha_solicitud = models.DateTimeField(db_column='Fecha_Solicitud', auto_now_add=True)  # Field name made lowercase.
    sucursal = models.ForeignKey(Sucursale, models.DO_NOTHING, db_column='sucursal', blank=True, null=True)
    prioridad = models.CharField(db_column='Prioridad', choices=P_CHOICES, default=1)  # Field name made lowercase.
    estado = models.CharField(db_column='Estado', choices=S_CHOICES, default=3)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Lista_Compras'



class RequerimientoMateriale(models.Model):
    S_BAJO = 'stock insuficiente'
    SIN_STOCK = 'sin stock'
    REPO='reposicion stock'

    M_CHOICES = [
        (REPO, 'Reposición stock'),
        (S_BAJO, 'Stock insuficiente'),
        (SIN_STOCK, 'Sin Stock'),
    ]
    id = models.BigAutoField(primary_key=True)
    material = models.ForeignKey(Materiale, models.DO_NOTHING, db_column='ID_Material')
    proveedor= models.ForeignKey(Proveedore, models.DO_NOTHING, db_column='ID_Proveedor')
    cantidad_necesaria = models.BigIntegerField(db_column='Cantidad_Necesaria')  # Field name made lowercase.
    motivo = models.CharField(db_column='Motivo', choices=M_CHOICES, default=1)  # Field name made lowercase.
    prioridad = models.CharField(db_column='Prioridad', choices=P_CHOICES, default=3)  # Field name made lowercase.
    precio_actual = models.FloatField(db_column='precio')
    subtotal = models.FloatField(db_column='subtotal')
    id_lista = models.ForeignKey(ListaCompra, models.DO_NOTHING, db_column='ID_Lista')  # Field name made lowercase.
      # Field name made lowercase.
    def save(self, *args, **kwargs):
        hoy = timezone.now().date()
        try:
            rel = MaterialProveedore.objects.get(
                material=self.material,
                id_proveedor=self.proveedor
            )
            precio_viejo = rel.precio_actual
        except MaterialProveedore.DoesNotExist:
            rel = None
            precio_viejo = None

        if precio_viejo != self.precio_actual:
            with transaction.atomic():
                # Actualizar fecha_fin del historial anterior si existe
                ultimo_historial = HistorialPrecio.objects.filter(
                    material=self.material,
                    proveedor=self.proveedor,
                    fecha_fin__isnull=True
                ).order_by('-fecha_inicio').first()
                
                if ultimo_historial:
                    ultimo_historial.fecha_fin = hoy
                    ultimo_historial.save()

                # Crear nuevo historial
                HistorialPrecio.objects.create(
                    precio=self.precio_actual,
                    fecha_inicio=hoy,
                    fecha_fin=None,
                    material=self.material,
                    proveedor=self.proveedor
                )

                # Actualizar precio en tabla principal
                if rel:
                    rel.precio_actual = self.precio_actual
                    rel.save()

        super().save(*args, **kwargs)

    class Meta:
        managed = False
        db_table = 'Requerimiento_Material'

class DetalleRecibido(models.Model):
    COMP = 'completo'
    INCOMP = 'incompleto'
    EXEDIDO ='excedido'

    EI_CHOICES = [
        (COMP, 'Completo'),
        (INCOMP, 'Incompleto'),
        (EXEDIDO, 'Exedido'),

    ]
    id = models.BigAutoField(primary_key=True)
    orden = models.ForeignKey('ListaCompra', models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey(Materiale, models.DO_NOTHING, blank=True, null=True)
    cantidad_ord = models.BigIntegerField(blank=True, null=True)
    cantidad_recibida = models.BigIntegerField(blank=True, null=True)
    estado_item = models.CharField(blank=True, null=True, choices=EI_CHOICES)

    class Meta:
        managed = False
        db_table = 'Detalle_recibido'

    def save(self, *args, **kwargs):
        # Guardamos el detalle sin tocar estado_item (lo maneja JS)
        super().save(*args, **kwargs)

        # Actualizar estado general de la lista
        if self.orden:
            detalles = DetalleRecibido.objects.filter(orden=self.orden)
            if detalles.filter(estado_item=self.INCOMP).exists():
                self.orden.estado = ListaCompra.INCOMPLETA
            elif detalles.exists() and not detalles.filter(estado_item=self.INCOMP).exists():
                self.orden.estado = ListaCompra.COMPLETA
            else:
                self.orden.estado = ListaCompra.PENDIENTE
            self.orden.save()

class HistorialPrecio(models.Model):
    id = models.BigAutoField(primary_key=True)
    precio = models.FloatField(db_column='Precio')  # Field name made lowercase.
    fecha_inicio = models.DateField(db_column='Fecha_Inicio')  # Field name made lowercase.
    fecha_fin = models.DateField(db_column='Fecha_Fin')  # Field name made lowercase.
    material = models.ForeignKey(Materiale, models.DO_NOTHING, db_column='ID_Material')  # Field name made lowercase.
    proveedor = models.ForeignKey(Proveedore, models.DO_NOTHING, db_column='ID_Proveedor')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Historial_Precios'