
from django.db import models
from django.utils import timezone
from django.db import transaction

class Materiale(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(db_column='Nombre')  # Field name made lowercase.
    imagen = models.TextField()
    stock_minimo = models.BigIntegerField(db_column='Stock_Minimo')  # Field name made lowercase.
    stock_maximo = models.BigIntegerField(db_column='Stock_Maximo')  # Field name made lowercase.
    categoria = models.ForeignKey('CategoriasMateriale', models.DO_NOTHING, db_column='ID_Categoria')  # Field name made lowercase.
    imagen_url = models.CharField(blank=True, null=True)
    medida = models.ForeignKey('UnidadesMedida', models.DO_NOTHING, db_column='id_medida', blank=False, null=False)

    archivo_temp = None
    def __str__(self):
        return self.nombre


    class Meta:
        managed = False
        db_table = 'Materiales'

class CategoriasMateriale(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(db_column='Nombre')
    descripcion = models.CharField(db_column='Descripcion')
    imagen = models.TextField()  # Ruta en Supabase
    imagen_url = models.CharField(blank=True, null=True)  # URL pública

    # Campo temporal para subir archivo desde admin
    archivo_temp = None
    def __str__(self):
        return self.nombre


    class Meta:
        managed = False
        db_table = 'Categorias_Materiales'


    


class UnidadesMedida(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(db_column='Nombre', max_length=15)  # Field name made lowercase.
    abreviatura = models.CharField(db_column='Abreviatura', max_length=4)  # Field name made lowercase.
    def __str__(self):
        return self.nombre

    class Meta:
        managed = False
        db_table = 'Unidades_Medida'


class Proveedore(models.Model):
    id = models.BigAutoField(primary_key=True)
    compañia= models.CharField(db_column='Compañia', help_text="Aquí se ingresará el nombre de la compañía proveedora.")
    nombre = models.CharField(db_column='Nombre')  # Field name made lowercase.
    telefono = models.CharField(db_column='Telefono')  # Field name made lowercase.
    email = models.CharField(db_column='email', max_length=50)
    estado = models.ForeignKey('EstadosPersonas', models.DO_NOTHING, db_column='Estado', blank=False, null=False, default=1)  
    #ForeignKey, el valor de default debe ser la clave primaria (ID) de la fila a la que quieres referenciar, no el texto-sofia castro
    def __str__(self):
        return self.compañia

    class Meta:
        managed = False
        db_table = 'Proveedores'


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



class Calificacione(models.Model):
    PUNTUALIDAD = 'puntualidad'
    CALIDAD = 'calidad material'
    COMUNICACIÓN='comunicacion'
    PRECIO='Precio'
    UN=1
    DO=2
    TRE=3
    CUA=4
    CIN=5

    M_CHOICES = [
        (PUNTUALIDAD, 'Puntualidad'),
        (CALIDAD, 'Calidad Material'),
        (COMUNICACIÓN ,'Comunicación'),
        (PRECIO ,'Precio'),
    ]

    C_CHOICES = [
        (UN,1),
        (DO,2),
        (TRE,3),
        (CUA,4),
        (CIN,5),
    ]

    id = models.BigAutoField(primary_key=True)
    criterio = models.CharField(db_column='Criterio', choices=M_CHOICES, default=1)  # Field name made lowercase.
    calificacion = models.BigIntegerField(db_column='Calificacion', choices=C_CHOICES, default=1)  # Field name made lowercase.
    comentario = models.CharField(db_column='Comentario')  # Field name made lowercase.
    id_prov = models.ForeignKey(Proveedore, models.DO_NOTHING, db_column='ID_Prov', blank=True, null=True, verbose_name="Proveedor")  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Calificaciones'


class EstadosPersonas(models.Model):
    id = models.BigAutoField(primary_key=True)
    tipo = models.CharField(db_column='Tipo', blank=True, null=True)  # Field name made lowercase.
    def __str__(self):
        return self.tipo


    class Meta:
        managed = False
        db_table = 'Estados_personas'

class MaterialProveedore(models.Model):
    DIAS = 'dias'
    SEMANAS = 'semanas'
    MESES = 'meses'

    TIEMPO_CHOICES = [
        (DIAS, 'Días'),
        (SEMANAS, 'Semanas'),
        (MESES, 'Meses'),
    ]

    id = models.BigAutoField(primary_key=True)
    creado = models.DateTimeField(auto_now_add=True)
    material = models.ForeignKey('Materiale', models.DO_NOTHING, db_column='id_material', blank=False, null=False)
    id_proveedor = models.ForeignKey('Proveedore', models.DO_NOTHING, db_column='id_proveedor', blank=False, null=False)
    precio_actual = models.FloatField(db_column='precio')
    tiempo = models.BigIntegerField(db_column='Tiempo', blank=False, null=False)
    unidad_tiempo = models.CharField(
        db_column='Unidad tiempo',
        max_length=10,
        choices=TIEMPO_CHOICES,
        blank=False,
        null=False,
        default=DIAS
    )
    comentarios = models.TextField(blank=True, null=True, max_length=150)
    def __str__(self):
         return self.material.nombre
    
    def save(self, *args, **kwargs):
        hoy = timezone.now().date()

        # Detectar si es edición o creación
        if self.pk:
            rel_anterior = MaterialProveedore.objects.filter(pk=self.pk).first()
            precio_viejo = rel_anterior.precio_actual if rel_anterior else None
        else:
            rel_anterior = None
            precio_viejo = None

        # Guardar primero el registro principal sin historial (pero sin override)
        super().save(*args, **kwargs)

        # Si el precio no cambió → no hacer historial
        if precio_viejo == self.precio_actual:
            return

        with transaction.atomic():

            # Cerrar historial anterior
            ultimo = HistorialPrecio.objects.filter(
                material=self.material,
                proveedor=self.id_proveedor,
                fecha_fin__isnull=True
            ).order_by('-fecha_inicio').first()

            if ultimo:
                ultimo.fecha_fin = hoy
                ultimo.save()

            # Crear historial nuevo
            HistorialPrecio.objects.create(
                precio=self.precio_actual,
                fecha_inicio=hoy,
                fecha_fin=None,
                material=self.material,
                proveedor=self.id_proveedor
            )

        
            


    class Meta:
        managed = False
        db_table = 'Material_proveedor'