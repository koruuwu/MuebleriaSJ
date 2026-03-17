
from django.db import models
from django.utils import timezone
from django.db import transaction

class Materiale(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField()  # Field name made lowercase.
    imagen = models.TextField()
    stock_minimo = models.BigIntegerField()  # Field name made lowercase.
    stock_maximo = models.BigIntegerField()  # Field name made lowercase.
    categoria = models.ForeignKey('CategoriasMateriale', models.DO_NOTHING)  # Field name made lowercase.
    imagen_url = models.CharField(blank=True, null=True)
    medida = models.ForeignKey('UnidadesMedida', models.DO_NOTHING, blank=False, null=False)

    archivo_temp = None
    def __str__(self):
        return self.nombre


    class Meta:
        managed = True
        db_table = 'Materiales'
        verbose_name = 'Material'
        verbose_name_plural = 'Materiales'
        permissions = [
            ("export_pdf_materiale", "Puede exportar Materiales a PDF"),
            ("export_excel_materiale", "Puede exportar Materiales a Excel"),
        ]

class CategoriasMateriale(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255)
    imagen = models.TextField()  # Ruta en Supabase
    imagen_url = models.CharField(blank=True, null=True)  # URL pública

    # Campo temporal para subir archivo desde admin
    archivo_temp = None
    def __str__(self):
        return self.nombre


    class Meta:
        managed = True
        db_table = 'Categorias_Materiales'
        verbose_name = 'Categoría de Material'
        verbose_name_plural = 'Categorías de Materiales'
        permissions = [
            ("export_pdf_categoriasmateriale", "Puede exportar Categorías de Materiales a PDF"),
            ("export_excel_categoriasmateriale", "Puede exportar Categorías de Materiales a Excel"),
        ]


    


class UnidadesMedida(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField( max_length=15)  # Field name made lowercase.
    abreviatura = models.CharField( max_length=4)  # Field name made lowercase.
    def __str__(self):
        return self.nombre

    class Meta:
        managed = True
        db_table = 'Unidades_Medida'
        verbose_name = 'Unidad de Medida'
        verbose_name_plural = 'Unidades de Medida'
        permissions = [
            ("export_pdf_unidadesmedida", "Puede exportar Unidades de Medida a PDF"),
            ("export_excel_unidadesmedida", "Puede exportar Unidades de Medida a Excel"),
        ]


class Proveedore(models.Model):
    id = models.BigAutoField(primary_key=True)
    compañia= models.CharField(max_length=100, help_text="Aquí se ingresará el nombre de la compañía proveedora.")
    nombre = models.CharField(max_length=100)  # Field name made lowercase.
    telefono = models.CharField(max_length=20)  # Field name made lowercase.
    email = models.CharField(max_length=100)
    estado = models.ForeignKey('EstadosPersonas', models.DO_NOTHING, blank=False, null=False, default=1)  
    #ForeignKey, el valor de default debe ser la clave primaria (ID) de la fila a la que quieres referenciar, no el texto-sofia castro
    def __str__(self):
        return self.compañia

    class Meta:
        managed = True
        db_table = 'Proveedores'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        permissions = [
            ("export_pdf_proveedore", "Puede exportar Proveedores a PDF"),
            ("export_excel_proveedore", "Puede exportar Proveedores a Excel"),
        ]


class HistorialPrecio(models.Model):
    id = models.BigAutoField(primary_key=True)
    precio = models.FloatField()  # Field name made lowercase.
    fecha_inicio = models.DateField()  # Field name made lowercase.
    fecha_fin = models.DateField(blank=True, null=True)  # Field name made lowercase.
    material = models.ForeignKey(Materiale, models.DO_NOTHING)  # Field name made lowercase.
    proveedor = models.ForeignKey(Proveedore, models.DO_NOTHING)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'Historial_Precios'
        verbose_name = 'Historial de Precio'
        verbose_name_plural = 'Historiales de Precios'
        permissions = [
            ("export_pdf_historialprecio", "Puede exportar Historiales de Precios a PDF"),
            ("export_excel_historialprecio", "Puede exportar Historiales de Precios a Excel"),
        ]



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
    criterio = models.CharField(choices=M_CHOICES, default=1)  # Field name made lowercase.
    calificacion = models.BigIntegerField(choices=C_CHOICES, default=1)  # Field name made lowercase.
    comentario = models.CharField(max_length=255)  # Field name made lowercase.
    id_prov = models.ForeignKey(Proveedore, models.DO_NOTHING, blank=True, null=True, verbose_name="Proveedor")  # Field name made lowercase.

    def __str__(self):
        return f"{self.criterio} - {self.calificacion}/5"

    class Meta:
        managed = True
        db_table = 'Calificaciones'
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        permissions = [
            ("export_pdf_calificacione", "Puede exportar Calificaciones a PDF"),
            ("export_excel_calificacione", "Puede exportar Calificaciones a Excel"),
        ]


class EstadosPersonas(models.Model):
    id = models.BigAutoField(primary_key=True)
    tipo = models.CharField( blank=True, null=True)  # Field name made lowercase.
    def __str__(self):
        return self.tipo


    class Meta:
        managed = True
        db_table = 'Estados_personas'
        verbose_name = 'Estado de Persona'
        verbose_name_plural = 'Estados de Personas'
        permissions = [
            ("export_pdf_estadospersonas", "Puede exportar Estados de Personas a PDF"),
            ("export_excel_estadospersonas", "Puede exportar Estados de Personas a Excel"),
        ]

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
    material = models.ForeignKey('Materiale', models.DO_NOTHING, blank=False, null=False)
    id_proveedor = models.ForeignKey('Proveedore', models.DO_NOTHING, blank=False, null=False)
    precio_actual = models.FloatField()
    tiempo = models.BigIntegerField(blank=False, null=False)
    unidad_tiempo = models.CharField(
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
        managed = True
        db_table = 'Material_proveedor'
        verbose_name = 'Material Proveedor'
        verbose_name_plural = 'Materiales Proveedores'
        permissions = [
            ("export_pdf_materialproveedore", "Puede exportar Materiales Proveedores a PDF"),
            ("export_excel_materialproveedore", "Puede exportar Materiales Proveedores a Excel"),
        ]