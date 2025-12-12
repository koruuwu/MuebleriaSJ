
from django.db import models
from  Muebles.models import Mueble
from Empleados.models import PerfilUsuario
from Sucursales.models import Sucursale
# Create your models here.
class OrdenMensuale(models.Model):
    PEND = 'pendiente'
    APROB='aprobada'
    COMP = 'completo'
    INCOMP = 'incompleto'

    EI_CHOICES = [
        (PEND, 'Pendiente'),
        (APROB, 'Aprobada'),
        (INCOMP, 'Incompleto'),
        (COMP, 'Completo'),
    ]
    

    id = models.BigAutoField(primary_key=True)
    id_sucursal = models.ForeignKey(Sucursale, models.DO_NOTHING, db_column='id_sucursal', blank=False, null=False, verbose_name="sucursal")
    nombre = models.CharField(db_column='Nombre', blank=False, null=False)  # Field name made lowercase.
    fecha_creacion = models.DateTimeField(db_column='Fecha_creacion', auto_now_add=True )  # Field name made lowercase.
    observaciones = models.CharField(blank=True, null=True)
    fecha_fin = models.DateField(db_column='Fecha_fin', blank=False, null=False)  # Field name made lowercase.
    estado = models.CharField(blank=False, null=True, choices=EI_CHOICES, default=PEND) 

    def __str__(self):
        if self.nombre:
            return self.nombre
        return f"Orden #{self.id} (Sin nombre)"
    
    def actualizar_estado(self):
        detalles = self.ordenmensualdetalle_set.all()
        if not detalles.exists():
            self.estado = self.PEND
        else:
            total_detalles = detalles.count()
            completos = detalles.filter(estado=OrdenMensualDetalle.COMP).count()

            if completos == 0:
                self.estado = self.PEND
            elif completos < total_detalles:
                self.estado = self.INCOMP
            else:
                self.estado = self.COMP
        super().save(update_fields=['estado'])

    class Meta:
        managed = False
        db_table = 'Orden_Mensuales'



    


class OrdenMensualDetalle(models.Model):
    PEND = 'pendiente'
    INCOMP = 'incompleto'
    COMP = 'completo'
        

    EU_CHOICES = [
        (PEND, 'Pendiente'),
        (INCOMP, 'Incompleto'),
        (COMP, 'Completo'),
    ]
    id = models.BigAutoField(primary_key=True)
    id_orden = models.ForeignKey('OrdenMensuale', models.DO_NOTHING, db_column='id_orden', blank=True, null=True)
    id_mueble = models.ForeignKey(Mueble, models.DO_NOTHING, db_column='id_mueble', blank=True, null=True)
    cantidad_planificada = models.BigIntegerField(blank=True, null=True)
    cantidad_producida = models.BigIntegerField(blank=True, null=True)
    estado = models.CharField(blank=False, null=False, choices=EU_CHOICES, default=1)
    entrega_estim = models.DateField(blank=True, null=True)

    def __str__(self):
        return str(self.id_mueble)


    class Meta:
        managed = False
        db_table = 'Orden_mensual_detalle'

class AportacionEmpleado(models.Model):
    PEND = 'pendiente'
    TRAB = 'trabajando'
    COMP = 'completo'        

    EA_CHOICES = [
        (PEND, 'Pendiente'),
        (TRAB, 'Trabajando'),
        (COMP, 'Completo'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    id_orden_detalle = models.ForeignKey('OrdenMensualDetalle', models.DO_NOTHING, db_column='id_orden_detalle', blank=True, null=True)
    id_empleado = models.ForeignKey(PerfilUsuario, models.DO_NOTHING, db_column='id_empleado', blank=True, null=True) # Field name made lowercase.
    cant_aprobada = models.BigIntegerField(blank=True, null=True)
    cantidad_finalizada = models.BigIntegerField(blank=True, null=True)
    estado = models.CharField(blank=False, null=False, choices=EA_CHOICES, default=PEND)
    materiales_reservados = models.JSONField(default=dict, blank=True)

    class Meta:
        managed = False
        db_table = 'aportacion_empleado'