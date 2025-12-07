from django.db import models

# Create your models here.
class Sucursale(models.Model):
    id = models.BigAutoField(primary_key=True)
    codigo_sucursal = models.CharField(db_column='codigo_sucursal', blank=False, null=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    nombre = models.CharField(db_column='Nombre', blank=False, null=False)  # Field name made lowercase.
    direccion = models.CharField(db_column='Direccion')  # Field name made lowercase.
    telefono = models.CharField(db_column='Telefono')  # Field name made lowercase.
    rtn = models.CharField(db_column='RTN', blank=True, null=True)  # Field name made lowercase.


    def __str__(self):
        return self.nombre

    class Meta:
        managed = False
        db_table = 'Sucursales'


from django.utils import timezone

class Cai(models.Model):
    id = models.BigAutoField(primary_key=True)
    codigo_cai = models.CharField(db_column='Codigo_Cai')
    fecha_emision = models.DateField(db_column='Fecha_Emision')
    fecha_vencimiento = models.DateField(db_column='Fecha_Vencimiento')
    rango_inicial = models.CharField(db_column='Rango_Inicial')
    rango_final = models.CharField(db_column='Rango_Final')
    ultima_secuencia = models.CharField(db_column='Ultima_Secuencia')
    activo = models.BooleanField(db_column='Activo')
    sucursal = models.ForeignKey('Sucursale', models.DO_NOTHING, db_column='ID_Sucursal')

    class Meta:
        managed = False
        db_table = 'CAI'




class Caja(models.Model):
    id = models.BigAutoField(primary_key=True)
    sucursal = models.ForeignKey('Sucursale', models.DO_NOTHING, blank=True, null=True)
    codigo_caja = models.CharField(blank=True, null=True)
    estado = models.BooleanField(blank=True, null=True)

    def __str__(self):
        return self.codigo_caja

    class Meta:
        managed = False
        db_table = 'caja'