from pickle import FALSE
from django.db import models
from Materiales.models import *

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
    id_categoria = models.ForeignKey('CategoriasMueble', models.DO_NOTHING, db_column='ID_Categoria', blank=True, null=True)  # Field name made lowercase.
    medida = models.ForeignKey(UnidadesMedida, models.DO_NOTHING, db_column='id_unidadesm', blank=True, null=True)
    alto = models.FloatField(db_column='Alto', blank=True, null=True)  # Field name made lowercase.
    ancho = models.FloatField(db_column='Ancho', blank=True, null=True)  # Field name made lowercase.
    largo = models.FloatField(db_column='Largo', blank=True, null=True)  # Field name made lowercase.
    imagen = models.TextField(blank=True, null=True)
    imagen_url = models.CharField(blank=True, null=True)
    tamano = models.ForeignKey('Tamaño', models.DO_NOTHING, db_column='id_tamano', blank=True, null=True)
    Descontinuado = models.BooleanField(db_column='Estado')  # Field name made lowercase.
    archivo_temp = None
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
