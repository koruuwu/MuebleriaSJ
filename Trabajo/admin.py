from django.contrib import admin
import nested_admin
from Trabajo.models import AportacionEmpleado, OrdenMensuale, OrdenMensualDetalle
from Empleados.models import PerfilUsuario
from django.forms import ModelForm
from django import forms
from django.urls import path
from django.http import JsonResponse
from Compras.models import  InventarioMateriale
from Muebles.models import MuebleMateriale

class AportacionForm(ModelForm):
    orden_selector = forms.ModelChoiceField(

        queryset=OrdenMensuale.objects.all(),
        required=False,
        label="Orden para trabajar (solo referencia)",
        help_text="Seleccione la orden; luego elija el detalle correspondiente."
    )

    cantidad_solicitada = forms.IntegerField(initial=0, required=False, label="Cantidad Solicitada")


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
    def clean(self):
        cleaned = super().clean()
        errores = []

        detalle = cleaned.get("id_orden_detalle")
        empleado = cleaned.get("id_empleado")
        cantidad_solicitada = cleaned.get("cantidad_solicitada")

        # -----------------------------
        # Validaciones básicas
        # -----------------------------
        if not detalle:
            errores.append("Debe seleccionar un detalle de orden para trabajar.")

        if not empleado:
            errores.append("No se detectó un empleado. Intente recargar la página.")

        if not cantidad_solicitada or cantidad_solicitada <= 0:
            errores.append("La cantidad solicitada debe ser mayor que 0.")

        # Si ya hay errores básicos, detenemos aquí
        if errores:
            raise forms.ValidationError(errores)

        # -----------------------------
        # Cálculo de unidades asignadas
        # -----------------------------
        from django.db.models import Sum

        asignaciones = (
            AportacionEmpleado.objects
            .filter(id_orden_detalle=detalle)
            .exclude(id=self.instance.id)
            .values("id_empleado__user__username", "cant_aprobada")
        )

        total_asignado = (
            AportacionEmpleado.objects
            .filter(id_orden_detalle=detalle)
            .exclude(id=self.instance.id)
            .aggregate(total=Sum("cant_aprobada"))["total"] or 0
        )

        planificada = detalle.cantidad_planificada or 0
        disponible = planificada - total_asignado

        # -----------------------------
        # VALIDACIÓN DE INVENTARIO DE MATERIALES
        # -----------------------------

        mueble = detalle.id_mueble

        # Materiales que usa el mueble
        materiales_mueble = MuebleMateriale.objects.filter(id_mueble=mueble)

        if not materiales_mueble.exists():
            errores.append(
                f"El mueble '{mueble.nombre}' no tiene materiales asignados. No se puede aprobar producción."
            )
        else:
            for mm in materiales_mueble:
                material = mm.id_material
                cantidad_por_mueble = mm.cantidad

                # Total de material requerido
                total_necesario = cantidad_solicitada * cantidad_por_mueble

                # Inventario del material (puedes filtrar por sucursal si aplica)
                inventario = InventarioMateriale.objects.filter(
                    id_material=material,
                    ubicación=detalle.id_orden.id_sucursal
                ).first()


                disponible_material = inventario.cantidad_disponible if inventario else 0

                if total_necesario > disponible_material:
                    errores.append(
                        f"Material insuficiente: {material.nombre}"
                    )
                    errores.append(
                        f"Necesario: {total_necesario} — Disponible: {disponible_material} Consumo por unidad: {cantidad_por_mueble}"
                    )

        # -----------------------------
        # Validación principal
        # -----------------------------
        if cantidad_solicitada > disponible:
            errores.append(
                f"No es posible asignar {cantidad_solicitada} unidades porque solo quedan {disponible} disponibles."
            )
            errores.append(
                f"Unidades planificadas: {planificada}, unidades ya asignadas: {total_asignado}"
            )

            # Detalle por empleado
            if asignaciones.exists():
                for a in asignaciones:
                    nombre = a["id_empleado__user__username"]
                    cant = a["cant_aprobada"]
                    errores.append(f"Asignaciones actuales: {nombre}: {cant} unidades")
            else:
                errores.append("Nadie ha tomado unidades aún.")

        # Si hubo errores, los lanzamos todos juntos
        if errores:
            raise forms.ValidationError(errores)

        # -----------------------------
        # Si es válido → asignar cantidad aprobada
        # -----------------------------
        cleaned["cant_aprobada"] = cantidad_solicitada

        return cleaned







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

    

