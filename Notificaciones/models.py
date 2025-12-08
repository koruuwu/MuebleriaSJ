from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
# Create your models here.
class Notificacione(models.Model):
    id = models.BigAutoField(primary_key=True)
    creado = models.DateTimeField()
    mensaje = models.CharField(db_column='Mensaje')  # Field name made lowercase.
    tipo = models.CharField(db_column='Tipo')  # Field name made lowercase.
    leida = models.BooleanField()
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    objeto = GenericForeignKey('content_type', 'object_id')

    class Meta:
        managed = True
        db_table = 'Notificaciones'