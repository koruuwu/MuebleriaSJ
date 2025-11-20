from django.contrib import admin
from .models import *
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import  PaginacionAdminMixin, UniqueFieldAdminMixin


class InventarioForm(ValidacionesBaseForm):
    class Meta:
        fields = "__all__"
        model = InventarioMueble
        widgets = {
            'cantidad_disponible': WidgetsRegulares.numero(4, allow_zero=False, placeholder="Ej: 10"),
        }
    def clean_cantidad_disponible(self):
        numero = self.cleaned_data.get('cantidad_disponible')
        numero = self.validar_longitud(str(numero), "Cantida disponible", min_len=1, max_len=4)
        return numero
    


@admin.register(InventarioMueble)
class InventarioMuebleAdmin(PaginacionAdminMixin,admin.ModelAdmin):
    form = InventarioForm
    list_display = ("id_mueble","cantidad_disponible", "estado", "ubicación")
    search_fields = ('id_mueble', 'ubicación')
    readonly_fields=('ultima_entrada', 'ultima_salida')
    list_filter = ('estado',)


