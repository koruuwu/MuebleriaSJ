from django.db import models

# Create your models here.
class Sucursale(models.Model):
    id = models.BigAutoField(primary_key=True)
    codigo_sucursal = models.CharField( blank=False, null=False, max_length=10)  # Field name made lowercase.
    fecha_registro = models.DateTimeField(auto_now_add=True)
    nombre = models.CharField(blank=False, null=False, max_length=100)  # Field name made lowercase.
    direccion = models.CharField(max_length=255)  # Field name made lowercase.
    telefono = models.CharField(max_length=20)  # Field name made lowercase.
    rtn = models.CharField(blank=True, null=True, max_length=20)  # Field name made lowercase.


    def __str__(self):
        return self.nombre

    class Meta:
        managed = True
        db_table = 'Sucursales'
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'


from django.utils import timezone

class Cai(models.Model):
    id = models.BigAutoField(primary_key=True)
    codigo_cai = models.CharField(max_length=37)
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()
    rango_inicial = models.CharField(max_length=8)
    rango_final = models.CharField(max_length=8)
    ultima_secuencia = models.CharField(max_length=8)
    activo = models.BooleanField()
    sucursal = models.ForeignKey('Sucursale', models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'CAI'
        verbose_name = 'CAI'
        verbose_name_plural = 'CAIs'

    def __str__(self):
        activo_str = "Activo" if self.activo else "Inactivo"
        return f"CAI: {activo_str} - Sucursal: {self.sucursal.nombre}"

    def save(self, *args, **kwargs):

        # --- Normalizar valores a 8 dígitos ---
        if self.rango_inicial:
            self.rango_inicial = str(self.rango_inicial).zfill(8)

        if self.rango_final:
            self.rango_final = str(self.rango_final).zfill(8)

        if self.ultima_secuencia:
            self.ultima_secuencia = str(self.ultima_secuencia).zfill(8)

        super().save(*args, **kwargs)




class Caja(models.Model):
    id = models.BigAutoField(primary_key=True)
    sucursal = models.ForeignKey('Sucursale', models.DO_NOTHING, blank=True, null=True)
    codigo_caja = models.CharField(blank=True, null=True, max_length=10)
    estado = models.BooleanField(blank=True, null=True)

    def __str__(self):
        return f"Caja {self.codigo_caja} - Sucursal: {self.sucursal.nombre}"

    class Meta:
        managed = True
        db_table = 'caja'
        verbose_name = 'Caja'
        verbose_name_plural = 'Cajas'