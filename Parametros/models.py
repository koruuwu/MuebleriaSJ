from django.db import models

# Create your models here.

class Parametro(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(blank=True, null=True)  # Field name made lowercase.
    valor = models.CharField(blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'Parametros'
        verbose_name = 'Parámetro'
        verbose_name_plural = 'Parámetros'

    def __str__(self):
        return f"{self.nombre} = {self.valor}"