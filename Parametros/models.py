from django.db import models

# Create your models here.

class Parametro(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(db_column='Nombre', blank=True, null=True)  # Field name made lowercase.
    valor = models.CharField(db_column='Valor', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Parametros'

    def __str__(self):
        return f"{self.nombre} = {self.valor}"