from django.contrib import admin, messages
from .models import *
from django import forms
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import *
from proyecto.utils.admin_utils import PaginacionAdminMixin
# Register your models here.

class EmpleadosForm(ValidacionesBaseForm):
    class Meta:
        model = Empleado
        fields = '__all__'
        widgets = {
            'nombre': WidgetsRegulares.nombre(),
            'telefono': WidgetsRegulares.telefono(),
            'email': WidgetsRegulares.email(),
        }

    
        
        
class Auth_UserForm(ValidacionesBaseForm):
    class Meta:
        model = Auth_User
        fields = '__all__'
        widgets = {
            'username': WidgetsRegulares.nombre(),
            'first_name': WidgetsRegulares.nombre(),
            'last_name': WidgetsRegulares.nombre(),
            'email': WidgetsRegulares.email(),
        }

class Auth_UserInLine(admin.TabularInline):
    model = Auth_User
    form = Auth_UserForm
    extra = 0  # no muestres filas vacías adicionales 
    can_delete = False  # No permite eliminar desde el inline

@admin.register(Empleado)
class EmpleadosAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    form = EmpleadosForm
    search_fields = ('id', 'nombre', 'telefono', 'area')
    list_display = ('id', 'nombre', 'telefono', 'email', 'area', 'estado', 'id_sucursal')
    list_display_links = ('id', 'nombre')
    readonly_fields = ()