
from django.db import models
from django.db import models


class Materiale(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(db_column='Nombre')  # Field name made lowercase.
    imagen = models.TextField()
    stock_minimo = models.BigIntegerField(db_column='Stock_Minimo')  # Field name made lowercase.
    stock_maximo = models.BigIntegerField(db_column='Stock_Maximo')  # Field name made lowercase.
    id_categoria = models.ForeignKey('CategoriasMateriale', models.DO_NOTHING, db_column='ID_Categoria')  # Field name made lowercase.
    imagen_url = models.CharField(blank=True, null=True)
    id_medida = models.ForeignKey('UnidadesMedida', models.DO_NOTHING, db_column='id_medida', blank=True, null=True)

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
    nombre = models.CharField(db_column='Nombre', max_length=50)  # Field name made lowercase.
    abreviatura = models.CharField(db_column='Abreviatura', max_length=10)  # Field name made lowercase.
    def __str__(self):
        return self.nombre

    class Meta:
        managed = False
        db_table = 'Unidades_Medida'