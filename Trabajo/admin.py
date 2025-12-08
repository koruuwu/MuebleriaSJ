from django.contrib import admin
import nested_admin
from Trabajo.models import AportacionEmpleado, OrdenMensuale, OrdenMensualDetalle
from Empleados.models import PerfilUsuario
from django.forms import ModelForm
from django import forms
from django.urls import path
from django.http import JsonResponse
class AportacionForm(ModelForm):
    orden_selector = forms.ModelChoiceField(
        queryset=OrdenMensuale.objects.all(),
        required=False,
        label="Orden para trabajar (solo referencia)",
        help_text="Seleccione la orden; luego elija el detalle correspondiente."
    )

    class Meta:
        model = AportacionEmpleado
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_orden_detalle'].help_text = (
            "<span id='detalle_helptext'>Seleccione un detalle para ver información.</span>"
        )

        # Inicia el campo de detalle vacío
        self.fields["id_orden_detalle"].queryset = OrdenMensualDetalle.objects.none()

        # Cuando el usuario selecciona una orden en una edición ya cargada
        if "orden_selector" in self.data:
            try:
                orden_id = int(self.data.get("orden_selector"))
                self.fields["id_orden_detalle"].queryset = (
                    OrdenMensualDetalle.objects.filter(id_orden_id=orden_id)
                )
            except:
                pass
        elif self.instance.pk:
            # Si se está editando una aportación ya existente
            if self.instance.id_orden_detalle:
                orden = self.instance.id_orden_detalle.id_orden
                self.fields["orden_selector"].initial = orden
                self.fields["id_orden_detalle"].queryset = (
                    OrdenMensualDetalle.objects.filter(id_orden=orden)
                )




class AportacionMInline(nested_admin.NestedStackedInline):
    model = AportacionEmpleado
    extra = 0

class DetalleOrdenMInline(nested_admin.NestedStackedInline):
    model = OrdenMensualDetalle
    extra = 0
    min_num = 0  # Cambia a 1 para forzar al menos un detalle
  
    inlines = [AportacionMInline]
    

@admin.register(OrdenMensuale)
class OrdenMensualeAdmin(nested_admin.NestedModelAdmin):
    inlines = [DetalleOrdenMInline]

@admin.register(AportacionEmpleado)
class AportacionAdmin(admin.ModelAdmin):
    form = AportacionForm
    list_display = ("id",)

    class Media:
        js = ('js/filtros/filtro_orden_aportaciones.js',)  # Archivo JS similar al de ListaCompra

    def get_urls(self):
        urls = super().get_urls()

        custom = [
            path(
                "filtrar_detalles/<int:orden_id>/",
                self.admin_site.admin_view(self.filtrar_detalles_por_orden),
                name="filtrar_detalles_orden",
            ),
            path(
                "obtener_empleado_logeado/",
                self.admin_site.admin_view(self.obtener_empleado_logeado),
                name="obtener-empleado-logeado-aportacion",
            )
        ]
        return custom + urls

    # --- Vista AJAX ---
    
    def filtrar_detalles_por_orden(self, request, orden_id):
        detalles = OrdenMensualDetalle.objects.filter(id_orden_id=orden_id)

        data = []
        for d in detalles:
            texto = f"{d.id} - {d.id_mueble.nombre} (Plan: {d.cantidad_planificada})"
            data.append({
                "id": d.id,
                "texto": texto,
                "mueble": d.id_mueble.nombre,
                "plan": d.cantidad_planificada
            })

        return JsonResponse(data, safe=False)
    
    def obtener_empleado_logeado(self, request):
        perfil = PerfilUsuario.objects.filter(user=request.user).first()
        return JsonResponse({
            "id_empleado": perfil.id if perfil else None
        })

    

