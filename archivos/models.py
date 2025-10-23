from django.db import models

  
class Documento(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    tipo_documento = models.CharField(db_column='Tipo_Documento')  # Field name made lowercase.
    descripcion = models.CharField(db_column='Descripcion')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Documentos'
    def __str__(self):
        return self.tipo_documento