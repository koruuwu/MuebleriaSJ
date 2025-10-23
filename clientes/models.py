from django.db import models
from archivos.models import *
# Create your models here.
class Cliente(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    telefono = models.CharField(db_column='Telefono')  # Field name made lowercase.
    direccion = models.CharField(db_column='Direccion')  # Field name made lowercase.
    nombre = models.CharField(db_column='Nombre')  # Field name made lowercase.
    uduario_final = models.BooleanField(db_column='Uduario_Final')  # Field name made lowercase.

    def __str__(self):
        return self.nombre


    class Meta:
        managed = False
        db_table = 'Clientes'


class DocumentosCliente(models.Model):
    id = models.BigAutoField(primary_key=True)
    valor = models.CharField(db_column='Valor')  # Field name made lowercase.
    id_cliente = models.ForeignKey(Cliente, models.DO_NOTHING, db_column='ID_Cliente')  # Field name made lowercase.
    id_documento = models.ForeignKey(Documento, models.DO_NOTHING, db_column='ID_Documento')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Documentos_Clientes'