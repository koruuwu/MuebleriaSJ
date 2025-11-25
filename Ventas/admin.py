from django.contrib import admin, messages
from .models import *
from django import forms
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import PaginacionAdminMixin
from django.urls import path
from django.http import JsonResponse
from Empleados.models import Empleado
from django.utils import timezone
from Sucursales.models import Cai
from Compras.models import Parametro

# Register your models here.

class OrdenesVentaForm(forms.ModelForm):
    class Meta:
        model = OrdenesVenta
        fields = '__all__'

class DetallesOInline(admin.StackedInline):
    model = DetallesOrdene
    extra = 0
    class Media:
        js = ('js/detalle_orden.js',)
    
 

@admin.register(OrdenesVenta)
class OrdenesVentasAdmin(admin.ModelAdmin):
    form = OrdenesVentaForm
    inlines = [DetallesOInline]
    list_display=('id_factura', 'id_cliente', 'total', 'id_estado_pago', 'fecha_entrega')
    readonly_fields = ('fecha_orden',)

    class Media:
        js = ("js/filtro_cajas.js","js/factura_dinamica.js",)

    

    def obtener_precio_mueble(self, request, mueble_id):
        try:
            mueble = Mueble.objects.get(id=mueble_id)
            return JsonResponse({"precio": mueble.precio_base})
        except Mueble.DoesNotExist:
            return JsonResponse({"precio": 0})

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("filtrar_cajas/<int:empleado_id>/", self.admin_site.admin_view(self.filtrar_cajas)),
            path("obtener_precio_mueble/<int:mueble_id>/", self.admin_site.admin_view(self.obtener_precio_mueble)),
            path(
                "generar_factura/<int:empleado_id>/<int:caja_id>/",
                self.admin_site.admin_view(self.generar_factura),
            ),
        ]
        return custom + urls
    
   

    def filtrar_cajas(self, request, empleado_id):
        try:
            empleado = Empleado.objects.get(id=empleado_id)
            if not empleado.id_sucursal:
                cajas = Caja.objects.none()
            else:
                # Usar nombre correcto del campo en Caja
                cajas = Caja.objects.filter(sucursal=empleado.id_sucursal)
            data = [{"id": c.id, "nombre": c.codigo_caja} for c in cajas]
        except Empleado.DoesNotExist:
            data = []
        except Exception as e:
            print("Error en filtrar_cajas:", e)
            data = []

        return JsonResponse(data, safe=False)

    def generar_factura(self, request, empleado_id, caja_id):
        try:
            empleado = Empleado.objects.get(id=empleado_id)
            caja = Caja.objects.get(id=caja_id)
            parametro = Parametro.objects.get(id=2)

            cai = Cai.objects.filter(sucursal=empleado.id_sucursal, activo=True).first()
            if not cai:
                return JsonResponse({"error": "No hay CAI activo para esta sucursal"})

            # Solo calcular el siguiente correlativo sin guardar
            correlativo_actual = int(cai.ultima_secuencia or "0")
            siguiente_correlativo = correlativo_actual + 1
            
            # Validar rango
            rango_final = int(cai.rango_final)
            if siguiente_correlativo > rango_final:
                return JsonResponse({"error": "Se ha alcanzado el límite de numeración para este CAI"})

            numero_factura = f"{empleado.id_sucursal.codigo_sucursal}-{caja.codigo_caja}-{parametro.valor}-{str(siguiente_correlativo).zfill(8)}"

            return JsonResponse({
                "numero_factura": numero_factura,
                "correlativo": siguiente_correlativo
            })
        except Exception as e:
            return JsonResponse({"error": str(e)})

    def save_model(self, request, obj, form, change):
    # Solo actualizar CAI cuando se guarda una nueva orden
        if not change and obj.id_factura:
            # Extraer la secuencia del número de factura
            partes = obj.id_factura.split('-')
            if len(partes) >= 4:
                secuencia = partes[-1]
                
                if obj.id_empleado and obj.id_empleado.id_sucursal:
                    cai = Cai.objects.filter(
                        sucursal=obj.id_empleado.id_sucursal, 
                        activo=True
                    ).first()
                    
                    if cai:
                        secuencia_actual = int(secuencia.lstrip('0'))
                        secuencia_cai = int(cai.ultima_secuencia or "0")
                        
                        # Actualizar solo si la secuencia es mayor
                        if secuencia_actual > secuencia_cai:
                            cai.ultima_secuencia = str(secuencia_actual).zfill(8)
                            cai.save()

        super().save_model(request, obj, form, change)