from django.db import models
from Parametros.models import Parametro
from Sucursales.models import Sucursale
from Muebles.models import Mueble
from clientes.models import Cliente
from Materiales.models import Materiale, Proveedore, MaterialProveedore
from django.utils import timezone
from django.db import transaction
from Sucursales.models import Sucursale
from Materiales.models import HistorialPrecio
class InventarioMueble(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_mueble = models.ForeignKey(Mueble, models.DO_NOTHING)  # Field name made lowercase.
    cantidad_disponible = models.BigIntegerField()  # Field name made lowercase.
    ubicación = models.ForeignKey(Sucursale, models.DO_NOTHING, blank=True, null=True)
    ultima_entrada = models.DateField( blank=True, null=True)  # Field renamed to remove unsuitable characters.
    ultima_salida = models.DateField( blank=True, null=True)  # Field renamed to remove unsuitable characters.
    estado = models.ForeignKey('Estados', models.DO_NOTHING, blank=False, null=False, default=1)  
    def __str__(self):
     return str(self.id_mueble)

    class Meta:
        managed = True
        db_table = 'Inventario_Muebles'
        verbose_name = 'Inventario de Mueble'
        verbose_name_plural = 'Inventarios de Muebles'
        permissions = [
            ("export_pdf_inventariomueble", "Puede exportar Inventario de Mueble a PDF"),
            ("export_excel_inventariomueble", "Puede exportar Inventario de Mueble a Excel"),
        ]

class Estados(models.Model):
    id = models.BigAutoField(primary_key=True)
    tipo = models.CharField( blank=True, null=True)  # Field name made lowercase.
    def __str__(self):
        return self.tipo


    class Meta:
        managed = True
        db_table = 'Estados_M'
        verbose_name = 'Estado de Mueble'
        verbose_name_plural = 'Estados de Muebles'
        permissions = [
            ("export_pdf_estados", "Puede exportar Estado de Mueble a PDF"),
            ("export_excel_estados", "Puede exportar Estado de Mueble a Excel"),
        ]


class Cotizacione(models.Model):
    id = models.BigAutoField(primary_key=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)  # Field name made lowercase.
    fecha_vencimiento = models.DateField()  # Field name made lowercase.
    cliente = models.ForeignKey(Cliente, models.DO_NOTHING)  # Field name made lowercase.
    subtotal = models.FloatField(null=True, blank=True)
    isv = models.FloatField(null=True, blank=True)
    total = models.FloatField(null=True, blank=True)
    def __str__(self):
        return str(self.cliente)

    class Meta:
        managed = True
        db_table = 'Cotizaciones'
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        permissions = [
            ("export_pdf_cotizacione", "Puede exportar Cotización a PDF"),
            ("export_excel_cotizacione", "Puede exportar Cotización a Excel"),
        ]

    
class DetalleCotizaciones(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_cotizacion = models.ForeignKey(Cotizacione, models.DO_NOTHING)  # Field name made lowercase.
    id_mueble = models.ForeignKey(Mueble, models.DO_NOTHING)  # Field name made lowercase.
    cantidad = models.BigIntegerField()  # Field name made lowercase.
    precio_unitario = models.FloatField()  # Field name made lowercase.
    subtotal = models.FloatField()  # Field name made lowercase.

    def __str__(self):
        return str(self.id_cotizacion)

    class Meta:
        managed = True
        db_table = 'Detalle_Cotizaciones'
        verbose_name = 'Detalle de Cotización'
        verbose_name_plural = 'Detalles de Cotizaciones'
        permissions = [
            ("export_pdf_detallecotizaciones", "Puede exportar Detalle de Cotización a PDF"),
            ("export_excel_detallecotizaciones", "Puede exportar Detalle de Cotización a Excel"),
        ]

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
    RECIBIDA='recibida'
    INCOMPLETA='incompleta'
    COMPLETA='completa'
    

    S_CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (APROBADA, 'Aprobada'),
        (RECHAZADA, 'Rechazada'),
        (INCOMPLETA, 'Incompleta'),
        (COMPLETA, 'Completa'),
        (RECIBIDA, 'Recibida'),
    ]
 

    id = models.BigAutoField(primary_key=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)  # Field name made lowercase.
    fecha_entrega = models.DateTimeField(blank=True, null=True, verbose_name="Fecha Entrega Completa")  # Field name made lowercase. 
    sucursal = models.ForeignKey(Sucursale, models.DO_NOTHING, blank=True, null=True)
    prioridad = models.CharField(choices=P_CHOICES, default=1)  # Field name made lowercase.
    estado = models.CharField(choices=S_CHOICES, default=3)  # Field name made lowercase.

   
    def save(self, *args, **kwargs):
        # Si el estado es COMPLETA y fecha_recibido está vacío, guardamos la fecha actual
        if self.estado == self.COMPLETA:
            self.fecha_entrega = timezone.now()
        else:
            # Si no está completa, dejamos el campo vacío
            self.fecha_entrega = None
        super().save(*args, **kwargs)

    class Meta:
        managed = True
        db_table = 'Lista_Compras'
        verbose_name = 'Lista de Compra'
        verbose_name_plural = 'Listas de Compras'
        permissions = [
            ("export_pdf_listacompra", "Puede exportar Lista de Compra a PDF"),
            ("export_excel_listacompra", "Puede exportar Lista de Compra a Excel"),
        ]

    def __str__(self):
        return f"Orden {self.id}"
        



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
    material = models.ForeignKey(Materiale, models.DO_NOTHING)
    proveedor= models.ForeignKey(Proveedore, models.DO_NOTHING)
    cantidad_necesaria = models.BigIntegerField()  # Field name made lowercase.
    motivo = models.CharField(choices=M_CHOICES, default=1)  # Field name made lowercase.
    prioridad = models.CharField(choices=P_CHOICES, default=3)  # Field name made lowercase.
    precio_actual = models.FloatField()
    subtotal = models.FloatField()
    id_lista = models.ForeignKey(ListaCompra, models.DO_NOTHING)  # Field name made lowercase.
      # Field name made lowercase.
    
    def save(self, *args, **kwargs):
        """
        - Garantiza que exista la relación MaterialProveedore.
        - Si cambia el precio_actual, actualiza MaterialProveedore.precio_actual
          y delega la gestión del HistorialPrecio al save() de MaterialProveedore.
        - Actualiza el subtotal a partir de cantidad_necesaria * precio_actual.
        """
        # Crear o recuperar la relación material-proveedor
        rel, created = MaterialProveedore.objects.get_or_create(
            material=self.material,
            id_proveedor=self.proveedor,
            defaults={
                'precio_actual': self.precio_actual,
                'tiempo': 1,  # valor razonable por defecto
                'unidad_tiempo': MaterialProveedore.DIAS,
            }
        )

        # Si el precio cambió, actualizar y dejar que MaterialProveedore.save maneje el historial
        if rel.precio_actual != self.precio_actual:
            rel.precio_actual = self.precio_actual
            rel.save()  # Aquí se encarga de cerrar historial anterior y crear uno nuevo

        # Asegurar que el subtotal esté consistente
        if self.cantidad_necesaria is not None and self.precio_actual is not None:
            self.subtotal = float(self.cantidad_necesaria) * float(self.precio_actual)

        super().save(*args, **kwargs)

    class Meta:
        managed = True
        db_table = 'Requerimiento_Material'
        verbose_name = 'Requerimiento de Material'
        verbose_name_plural = 'Requerimientos de Materiales'
        permissions = [
            ("export_pdf_requerimientomateriale", "Puede exportar Requerimiento de Material a PDF"),
            ("export_excel_requerimientomateriale", "Puede exportar Requerimiento de Material a Excel"),
        ]

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
    aporte = models.BigIntegerField(blank=True, null=True)  # Nuevo campo principal
    cantidad_recibida = models.BigIntegerField(blank=True, null=True)  # Se actualizará automáticamente
    estado_item = models.CharField(blank=True, null=True, choices=EI_CHOICES)

    class Meta:
        managed = True
        db_table = 'Detalle_recibido'
        verbose_name = 'Detalle Recibido'
        verbose_name_plural = 'Detalles Recibidos'
        permissions = [
            ("export_pdf_detallerecibido", "Puede exportar Detalle Recibido a PDF"),
            ("export_excel_detallerecibido", "Puede exportar Detalle Recibido a Excel"),
        ]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            aporte_actual = self.aporte or 0

            #Actualizar cantidad_recibida
            if aporte_actual > 0:
                self.cantidad_recibida = (self.cantidad_recibida or 0) + aporte_actual

            #Guardar primero
            super().save(*args, **kwargs)

            # Actualizar inventario
            if self.product and aporte_actual > 0:
                inventario, created = InventarioMateriale.objects.get_or_create(
                    id_material=self.product,
                    ubicación=self.orden.sucursal if self.orden else None,
                    defaults={
                        'cantidad_disponible': 0,
                        'ultima_entrada': timezone.now().date()
                    }
                )

                inventario.cantidad_disponible = (
                    inventario.cantidad_disponible or 0
                ) + aporte_actual

                inventario.ultima_entrada = timezone.now().date()

                inventario.estado = self.calcular_estado_automatico(
                    inventario.cantidad_disponible,
                    self.product
                )

                inventario.save()

            #RESET DEFINITIVO DEL APORTE
            self.aporte = 0
            super().save(update_fields=['aporte'])


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
    
    def calcular_estado_automatico(self, cantidad, material):
        """Calcular estado automáticamente basado en cantidad y stock mínimo"""
        if getattr(material, 'descontinuado', False):
            return Estados.objects.get(id=4)  # Descontinuado
        
        stock_minimo = getattr(material, 'stock_minimo', 10)
        
        if cantidad <= 0:
            return Estados.objects.get(id=3)  # Agotado
        elif cantidad < stock_minimo:
            return Estados.objects.get(id=2)  # Bajo Stock
        else:
            return Estados.objects.get(id=1)  # Disponible



class InventarioMateriale(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_material = models.ForeignKey(Materiale, models.DO_NOTHING)  # Field name made lowercase.
    cantidad_disponible = models.BigIntegerField()  # Field name made lowercase.
    estado = models.ForeignKey(Estados, models.DO_NOTHING, blank=True, null=True)  # Field name made lowercase.
    ubicación = models.ForeignKey(Sucursale, models.DO_NOTHING, blank=True, null=True)
    ultima_entrada = models.DateField(blank=True, null=True)  # Field renamed to remove unsuitable characters.
    ultima_salida = models.DateField(blank=True, null=True)  # Field renamed to remove unsuitable characters.
    cantidad_reservada = models.BigIntegerField(blank=True, null=True)  # Field name made lowercase.
    

    class Meta:
        managed = True
        db_table = 'Inventario_Materiales'
        verbose_name = 'Inventario de Material'
        verbose_name_plural = 'Inventarios de Materiales'
        permissions = [
            ("export_pdf_inventariomateriale", "Puede exportar Inventario de Material a PDF"),
            ("export_excel_inventariomateriale", "Puede exportar Inventario de Material a Excel"),
        ]

        