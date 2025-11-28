from django.db import models
from Sucursales.models import *

# Create your models here.
class Auth_User(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    id_empleado = models.ForeignKey('Empleado', models.DO_NOTHING, db_column='Id_empleado', blank=True, null=True)  # Field name made lowercase.


    def __str__(self):
        return self.username

    class Meta:
        managed = False
        db_table = 'auth_user'


class Empleado(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(db_column='Nombre')  # Field name made lowercase.
    fecha_nacimiento = models.DateField(db_column='Fecha_Nacimiento')  # Field name made lowercase.
    telefono = models.CharField(db_column='Telefono')  # Field name made lowercase.
    area = models.CharField(db_column='Area')  # Field name made lowercase.
    estado = models.BooleanField(db_column='Estado')  # Field name made lowercase.
    email = models.CharField(db_column='email')  # Field name made lowercase.
    id_usuario = models.ForeignKey('Auth_User', models.DO_NOTHING, db_column='ID_Usuario', verbose_name='Usuario')  # Field name made lowercase.
    id_sucursal = models.ForeignKey('Sucursales.Sucursale', models.DO_NOTHING, db_column='ID_Sucursal',verbose_name='Sucursal')  # Field name made lowercase.

    def __str__(self):
        return self.nombre

    class Meta:
        managed = False
        db_table = 'Empleados'


from django.contrib.auth.models import User
from django.db import models
from Sucursales.models import Sucursale, Caja
from django.db.models.signals import post_save
from django.dispatch import receiver

class PerfilUsuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column="user")
    sucursal = models.ForeignKey(Sucursale, models.DO_NOTHING, db_column='sucursal', blank=True, null=True)
    caja = models.ForeignKey(Caja, models.DO_NOTHING, db_column='caja', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'PerfilUsuario'

    def __str__(self):
        return f"Perfil de {self.user.username}"
    
    @receiver(post_save, sender=User)
    def crear_perfil_usuario(sender, instance, created, **kwargs):
        if created:
            PerfilUsuario.objects.create(user=instance)
