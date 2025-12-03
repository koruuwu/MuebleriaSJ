from django.contrib import admin, messages
from .models import *
from django import forms
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import *
from proyecto.utils.admin_utils import PaginacionAdminMixin
# Register your models here.

class SucursaleForm(ValidacionesBaseForm):
    class Meta:
        model = Sucursale
        fields = '__all__'
        widgets = {
            'nombre': WidgetsEspeciales.nombreSucursal(),
            'telefono': WidgetsRegulares.telefono(),
            'direccion': WidgetsRegulares.direccion(),
        }

class CaiInline(admin.StackedInline):
    model = Cai
    extra = 0
    class Media:
        js = ('js/estados/cai.js',)

class CajaInline(admin.StackedInline):
    model = Caja
    extra = 0


@admin.register(Sucursale)
class SucursalesAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    form = SucursaleForm
    search_fields = ('id', 'nombre', 'direccion', 'telefono')
    list_display = ('id', 'nombre', 'direccion', 'telefono', 'fecha_registro')
    list_display_links = ('id', 'nombre')
    readonly_fields = ('fecha_registro',)
    inlines=[CaiInline, CajaInline,]