from django.db import models
from archivos.models import *
from django.core.exceptions import ValidationError

class Cliente(models.Model):
    id = models.BigAutoField(primary_key=True)
    creado = models.DateTimeField(auto_now_add=True)
    nombre = models.CharField(max_length=100)  # Field name made lowercase.
    telefono = models.CharField(max_length=15, verbose_name="Teléfono")  # Field name made lowercase.
    direccion = models.CharField(max_length=255)  # Field name made lowercase.
    rtn = models.CharField(blank=True, null=True, max_length=16)  # Field name made lowercase.
    
    def total_pedidos(self):
        return self.ordenesventa_set.count()

    total_pedidos.short_description = "Pedidos Totales"


    def __str__(self):
        return self.nombre


    class Meta:
        managed = True
        db_table = 'Clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        permissions = [
            ("export_pdf_cliente", "Puede exportar Cliente a PDF"),
            ("export_excel_cliente", "Puede exportar Cliente a Excel"),
        ]




class DocumentosCliente(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, models.DO_NOTHING)
    id_documento = models.ForeignKey(Documento, models.DO_NOTHING)
    valor = models.CharField(max_length=100)  # Campo para almacenar el valor del documento (ejemplo: número de identificación)

    def __str__(self):
        # Mostrar "Cliente - Documento"
        return f"{self.id_cliente.nombre} - {self.id_documento.tipo_documento}: {self.valor}"

    class Meta:
        managed = True
        db_table = 'Documentos_Clientes'
        verbose_name = 'Documento del Cliente'
        verbose_name_plural = 'Documentos de los Clientes'
        permissions = [
            ("export_pdf_documentoscliente", "Puede exportar Documentos de Cliente a PDF"),
            ("export_excel_documentoscliente", "Puede exportar Documentos de Cliente a Excel"),
        ]

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
