from pickle import TRUE
from django.db import models

# Create your models here.
from django.db import models

class CategoriasMateriales(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(db_column='Nombre')
    descripcion = models.CharField(db_column='Descripcion')
    imagen = models.TextField()  # Ruta en Supabase
    imagen_url = models.CharField(blank=True, null=True)  # URL pública

    # Campo temporal para subir archivo desde admin
    archivo_temp = None
    

    class Meta:
        managed = False
        db_table = 'Categorias_Materiales'
