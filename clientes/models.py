from django.db import models
from archivos.models import *
from django.core.exceptions import ValidationError

class Cliente(models.Model):
    id = models.BigAutoField(primary_key=True)
    creado = models.DateTimeField(auto_now_add=True)
    nombre = models.CharField(db_column='Nombre')  # Field name made lowercase.
    telefono = models.CharField(db_column='Telefono')  # Field name made lowercase.
    direccion = models.CharField(db_column='Direccion')  # Field name made lowercase.
    rtn = models.CharField(db_column='RTN', blank=True, null=True, max_length=16)  # Field name made lowercase.
    
    def total_pedidos(self):
        return self.ordenesventa_set.count()

    total_pedidos.short_description = "Pedidos Totales"


    def __str__(self):
        return self.nombre


    class Meta:
        managed = False
        db_table = 'Clientes'




class DocumentosCliente(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, models.DO_NOTHING, db_column='ID_Cliente')
    id_documento = models.ForeignKey(Documento, models.DO_NOTHING, db_column='ID_Documento')
    valor = models.CharField(db_column='Valor')

    def __str__(self):
        # Mostrar "Cliente - Documento"
        return f"{self.id_cliente.nombre} - {self.id_documento.tipo_documento}: {self.valor}"

    class Meta:
        managed = False
        db_table = 'Documentos_Clientes'

    def clean(self):
        # Evita duplicados cliente + documento + valor
        if self.id_cliente and self.id_documento:
            existe = DocumentosCliente.objects.exclude(pk=self.pk).filter(
                id_cliente=self.id_cliente,
                id_documento=self.id_documento
            ).exists()
            if existe:
                raise ValidationError(
                    f"⚠️ El usuario {self.id_cliente.nombre} ya tiene registrado el documento "
                    f"'{self.id_documento.tipo_documento}'"
                )
            

    def save(self, *args, **kwargs):
        # Asegura que la validación se ejecute también al guardar desde admin
        self.full_clean()
        super().save(*args, **kwargs)
