from django.db import models
from Sucursales.models import *

# Create your models here.
class User(models.Model):
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
    id_empleado = models.ForeignKey('Empleado', models.DO_NOTHING, blank=True, null=True)  # Field name made lowercase.


    def __str__(self):
        return self.username

    class Meta:
        managed = True
        db_table = 'user'
        permissions = [
            ("export_pdf_user", "Puede exportar Usuarios a PDF"),
            ("export_excel_user", "Puede exportar Usuarios a Excel"),
        ]


class Empleado(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField()  # Field name made lowercase.
    fecha_nacimiento = models.DateField()  # Field name made lowercase.
    telefono = models.CharField()  # Field name made lowercase.
    area = models.CharField()  # Field name made lowercase.
    estado = models.BooleanField()  # Field name made lowercase.
    email = models.CharField()  # Field name made lowercase.
    id_usuario = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)  # Field name made lowercase.
    id_sucursal = models.ForeignKey('Sucursales.Sucursale', models.DO_NOTHING, blank=True, null=True,verbose_name='Sucursal')  # Field name made lowercase.

    def __str__(self):
        return self.nombre

    class Meta:
        managed = True
        db_table = 'Empleados'
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        permissions = [
            ("export_pdf_empleado", "Puede exportar Empleados a PDF"),
            ("export_excel_empleado", "Puede exportar Empleados a Excel"),
        ]


from django.contrib.auth.models import User, Group, Permission
from django.db import models
from Sucursales.models import Sucursale, Caja
from django.db.models.signals import post_save
from django.dispatch import receiver

class PerfilUsuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sucursal = models.ForeignKey(Sucursale, models.DO_NOTHING, blank=True, null=True)
    caja = models.ForeignKey(Caja, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'PerfilUsuario'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'
        permissions = [
            ("export_pdf_perfilusuario", "Puede exportar Perfiles de Usuario a PDF"),
            ("export_excel_perfilusuario", "Puede exportar Perfiles de Usuario a Excel"),
        ]

    def __str__(self):
        return f"Perfil de {self.user.username}"
    
class GroupProxy(Group):
    class Meta:
        proxy = True
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"
        permissions = [
            ("export_pdf_groupproxy", "Puede exportar Grupos a PDF"),
            ("export_excel_groupproxy", "Puede exportar Grupos a Excel"),
        ]

class UserProxy(User):
    class Meta:
        proxy = True
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        permissions = [
            ("export_pdf_userproxy", "Puede exportar Usuarios a PDF"),
            ("export_excel_userproxy", "Puede exportar Usuarios a Excel"),
        ]