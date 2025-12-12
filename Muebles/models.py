from pickle import FALSE
from django.db import models
from Materiales.models import UnidadesMedida, Materiale
from django.utils import timezone
from django.db import transaction
class CategoriasMueble(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(db_column='Nombre')  # Field name made lowercase.
    descripcion = models.CharField(db_column='Descripcion')  # Field name made lowercase.
    imagen = models.TextField()
    imagen_url = models.CharField(blank=True, null=True)
    
    archivo_temp = None
    def __str__(self):
        return self.nombre


    class Meta:
        managed = False
        db_table = 'Categorias_Muebles'

class Mueble(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(db_column='Nombre')  # Field name made lowercase.
    descripcion = models.TextField(db_column='Descripcion', max_length=250)  # Field name made lowercase.
    precio_base = models.FloatField(db_column='Precio_Base')  # Field name made lowercase.
    categoria = models.ForeignKey('CategoriasMueble', models.DO_NOTHING, db_column='ID_Categoria', blank=False, null=False)  # Field name made lowercase.
    medida = models.ForeignKey(UnidadesMedida, models.DO_NOTHING, db_column='id_unidadesm', blank=False, null=False)
    alto = models.FloatField(db_column='Alto', blank=False, null=False)  # Field name made lowercase.
    ancho = models.FloatField(db_column='Ancho', blank=False, null=False)  # Field name made lowercase.
    largo = models.FloatField(db_column='Largo', blank=False, null=False)  # Field name made lowercase.
    imagen = models.TextField(blank=True, null=True)
    imagen_url = models.CharField(blank=True, null=True)
    tamano = models.ForeignKey('Tamaño', models.DO_NOTHING, db_column='id_tamano', blank=False, null=False)
    Descontinuado = models.BooleanField(db_column='Estado')  # Field name made lowercase.
    archivo_temp = None
    stock_minimo = models.BigIntegerField(db_column='Stock_Minimo')  # Field name made lowercase.
    stock_maximo = models.BigIntegerField(db_column='Stock_Maximo') 

    def save(self, *args, **kwargs):
        hoy = timezone.now().date()

        # Detectar si es edición
        if self.pk:
            mueble_anterior = Mueble.objects.filter(pk=self.pk).first()
            precio_viejo = mueble_anterior.precio_base if mueble_anterior else None
        else:
            precio_viejo = None

        # Guardar primero el registro principal
        super().save(*args, **kwargs)

        # Si el precio no cambió → no crear historial
        if precio_viejo == self.precio_base:
            return

        with transaction.atomic():
            # Cerrar historial anterior
            ultimo = HistorialPreciosMueble.objects.filter(
                id_mueble=self,
                fecha_fin__isnull=True
            ).order_by('-fecha_inicio').first()

            if ultimo:
                ultimo.fecha_fin = hoy
                ultimo.save()

            # Crear historial nuevo
            HistorialPreciosMueble.objects.create(
                precio=self.precio_base,
                fecha_inicio=hoy,
                fecha_fin=None,
                id_mueble=self
            )

    def __str__(self):
        return self.nombre
    
    


    class Meta:
        managed = False
        db_table = 'Muebles'

class Tamaño(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(db_column='Nombre', blank=True, null=True)  # Field name made lowercase.
    descripcion = models.CharField(db_column='Descripcion', blank=True, null=True, max_length=50)  # Field name made lowercase.
    def __str__(self):
        return self.nombre


    class Meta:
        managed = False
        db_table = 'Tamano'


class MuebleMateriale(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_material = models.ForeignKey(Materiale, models.DO_NOTHING, db_column='id_material', blank=False, null=False)
    id_mueble = models.ForeignKey(Mueble, models.DO_NOTHING, db_column='id_mueble', blank=False, null=False)
    cantidad = models.BigIntegerField(db_column='Cantidad', blank=False, null=False)  # Field name made lowercase.
    
    def __str__(self):
        # Mostrar "Cliente - Documento"
        return f"{self.id_material.nombre} - {self.id_mueble.nombre}: {self.cantidad}"

    class Meta:
        managed = False
        db_table = 'Mueble_Material'
    


class HistorialPreciosMueble(models.Model):
    id = models.BigAutoField(primary_key=True)
    precio = models.FloatField(db_column='Precio')  # Field name made lowercase.
    fecha_inicio = models.DateField(db_column='Fecha_Inicio')  # Field name made lowercase.
    fecha_fin = models.DateField(db_column='Fecha_Fin', blank=True, null=True)  # Field name made lowercase.
    id_mueble = models.ForeignKey(Mueble, models.DO_NOTHING, db_column='ID_Mueble')  # Field name made lowercase.
    
    class Meta:
        managed = False
        db_table = 'Historial_Precios_muebles'

    