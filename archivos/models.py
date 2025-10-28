from django.db import models
from django.core.exceptions import ValidationError

class Documento(models.Model):
    id = models.BigAutoField(primary_key=True)
    fecha_registro = models.DateTimeField()
    tipo_documento = models.CharField(db_column='Tipo_Documento', max_length=100)
    descripcion = models.CharField(db_column='Descripcion', max_length=255)

    def clean(self):
        # Validar duplicado antes de guardar
        if Documento.objects.exclude(pk=self.pk).filter(tipo_documento=self.tipo_documento).exists():
            raise ValidationError({'tipo_documento': '⚠️ Este tipo de documento ya existe.'})

    class Meta:
        managed = False  # Ya existe en la base de datos
        db_table = 'Documentos'

    def __str__(self):
        return self.tipo_documento
