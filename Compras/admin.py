from django.contrib import admin
from .models import *
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import  PaginacionAdminMixin, UniqueFieldAdminMixin
from datetime import timedelta
from django.urls import path
from django.http import JsonResponse
from django.utils.safestring import mark_safe

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
    


class CotizacioneForm(ValidacionesBaseForm):
    class Meta:
        model = Cotizacione
        fields = "__all__"
        widgets = {
            
        }


@admin.register(InventarioMueble)
class InventarioMuebleAdmin(PaginacionAdminMixin,admin.ModelAdmin):
    form = InventarioForm
    list_display = ("id_mueble","cantidad_disponible", "estado", "ubicación")
    search_fields = ('id_mueble', 'ubicación')
    readonly_fields=('ultima_entrada', 'ultima_salida')
    list_filter = ('estado','ubicación')

class DetalleCotizacionesInline(admin.TabularInline):
    model = DetalleCotizaciones
    extra = 0

    class Media:
        js = ('js/detalle_cotizacion.js',)

    

@admin.register(Cotizacione)
class CotizacioneAdmin(PaginacionAdminMixin,admin.ModelAdmin):
    form = CotizacioneForm
    list_display = ("cliente", "fecha_registro", "activo", "fecha_vencimiento")
    search_fields = ('cliente',)
    readonly_fields=("fecha_registro","fecha_vencimiento")
    list_filter = ('activo',)
    inlines = [DetalleCotizacionesInline]
    
  
    def save_model(self, request, obj, form, change):
        from django.utils import timezone

        if not change:  # Solo al crear
            obj.fecha_registro = timezone.now()

        try:
            dias_parametro = int(Parametro.objects.get(nombre='dias_cotizacion').valor)
        except (Parametro.DoesNotExist, ValueError):
            dias_parametro = 15

        if obj.fecha_registro:
            obj.fecha_vencimiento = obj.fecha_registro.date() + timedelta(days=dias_parametro)

        super().save_model(request, obj, form, change)

    def obtener_precio_mueble(self, request, mueble_id):
        try:
            mueble = Mueble.objects.get(id=mueble_id)
            return JsonResponse({"precio": mueble.precio_base})  # <- aquí el nombre correcto
        except Mueble.DoesNotExist:
            return JsonResponse({"precio": 0})


    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("obtener_precio_mueble/<int:mueble_id>/", self.obtener_precio_mueble),
        ]
        return custom + urls

