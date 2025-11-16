from django.contrib import admin, messages
from .models import *
from django import forms
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import PaginacionAdminMixin
# Register your models here.

class OrdenesVentaForm(forms.ModelForm):
    class Meta:
        model = OrdenesVenta
        fields = '__all__'

@admin.register(OrdenesVenta)
class OrdenesVentasAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    form = OrdenesVentaForm
    search_fields = ('id', 'id_cliente__nombre_cliente', 'id_factura')
    list_display = ('id', 'fecha_orden', 'fecha_entrega', 'id_cliente', 'subtotal', 'isv', 'descuento', 'total')
    list_display_links = ('id', 'id_cliente')
    readonly_fields = ()