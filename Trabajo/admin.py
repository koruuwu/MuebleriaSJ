from django.contrib import admin, messages
import nested_admin
from Trabajo.models import AportacionEmpleado, OrdenMensuale, OrdenMensualDetalle
from Empleados.models import PerfilUsuario
from django.forms import ModelForm
from django import forms
from django.urls import path
from django.http import JsonResponse
from Compras.models import  InventarioMateriale
from Muebles.models import MuebleMateriale
from django.db.models import Sum
class AportacionForm(ModelForm):
    orden_selector = forms.ModelChoiceField(

        queryset=OrdenMensuale.objects.all(),
        required=False,
        label="Orden para trabajar (solo referencia)",
        help_text="Seleccione la orden; luego elija el detalle correspondiente."
    )
    Aporte = forms.IntegerField(initial=0, required=False, label="Aporte")

    cantidad_solicitada = forms.IntegerField(initial=0, required=False, label="Cantidad Solicitada")


    class Meta:
        model = AportacionEmpleado
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['id_orden_detalle'].help_text = (
            "<span id='detalle_helptext'>Seleccione un detalle para ver información.</span>"
        )

        self.fields["id_orden_detalle"].queryset = OrdenMensualDetalle.objects.none()
        aporte_field = self.fields.get('Aporte')
        if aporte_field:
            # Si el objeto es nuevo (no pk) -> no hay cant_aprobada todavía -> deshabilitar
            if not self.instance.pk:
                aporte_field.disabled = True
                aporte_field.help_text = "Se habilitará cuando exista una cantidad aprobada."
            else:
                # Si existe la instancia, verificar cant_aprobada
                if getattr(self.instance, 'cant_aprobada', None) is None:
                    aporte_field.disabled = True
                    aporte_field.help_text = "Se habilitará cuando exista una cantidad aprobada."
                else:
                    aporte_field.disabled = False

        if "orden_selector" in self.data:
            try:
                orden_id = int(self.data.get("orden_selector"))
                self.fields["id_orden_detalle"].queryset = (
                    OrdenMensualDetalle.objects.filter(id_orden_id=orden_id)
                )
            except:
                pass
        elif self.instance.pk:
            if self.instance.id_orden_detalle:
                orden = self.instance.id_orden_detalle.id_orden
                self.fields["orden_selector"].initial = orden
                self.fields["id_orden_detalle"].queryset = (
                    OrdenMensualDetalle.objects.filter(id_orden=orden)
                )

            #DESACTIVAR cantidad_solicitada SI YA EXISTE cant_aprobada
            if self.instance.cant_aprobada is not None:
                self.fields["cantidad_solicitada"].disabled = True
                self.fields["cantidad_solicitada"].required = False


            if self.instance.estado == AportacionEmpleado.COMP:
                for field_name, field in self.fields.items():
                    field.disabled = True
         
    def clean(self):
        cleaned = super().clean()
        errores = []

        detalle = cleaned.get("id_orden_detalle")
        empleado = cleaned.get("id_empleado")
        cantidad_solicitada = cleaned.get("cantidad_solicitada") or 0

        # -----------------------------
        # 1. VALIDACIONES BÁSICAS
        # -----------------------------
        if not detalle:
            errores.append("Debe seleccionar un detalle de orden para trabajar.")

        if not empleado:
            errores.append("No se detectó un empleado. Intente recargar la página.")

        # Solo validar cantidad_solicitada si AÚN NO hay cant_aprobada
        if self.instance.pk and self.instance.cant_aprobada is not None:
            pass  # Ya hay cantidad aprobada → no se vuelve a solicitar
        else:
            if not cantidad_solicitada or cantidad_solicitada <= 0:
                errores.append("La cantidad solicitada debe ser mayor que 0.")

        # Si hay errores básicos, detenemos aquí
        if errores:
            raise forms.ValidationError(errores)

        # -----------------------------
        # 2. VALIDACIÓN DE MATERIALES
        # -----------------------------
        # Solo se valida si cantidad solicitada es válida y detalle existe
        if detalle and cantidad_solicitada > 0 and (self.instance.pk is None or self.instance.cant_aprobada is None):
            # -----------------------------
            # 1. VALIDACIÓN DE CANTIDAD DISPONIBLE
            # -----------------------------
            total_asignado = (
                AportacionEmpleado.objects
                .filter(id_orden_detalle=detalle)
                .exclude(id=self.instance.id)
                .aggregate(total=Sum("cant_aprobada"))["total"] or 0
            )
            planificada = detalle.cantidad_planificada or 0
            disponible = planificada - total_asignado

            if cantidad_solicitada > disponible:
                errores.append(
                    f"No es posible asignar {cantidad_solicitada} unidades porque solo quedan {disponible} disponibles."
                )
                errores.append(
                    f"Unidades planificadas: {planificada}, unidades ya asignadas: {total_asignado}"
                )

                # Detalle por empleado
                asignaciones = (
                    AportacionEmpleado.objects
                    .filter(id_orden_detalle=detalle)
                    .exclude(id=self.instance.id)
                    .values("id_empleado__user__username", "cant_aprobada")
                )

                if asignaciones.exists():
                    for a in asignaciones:
                        nombre = a["id_empleado__user__username"]
                        cant = a["cant_aprobada"]
                        errores.append(f"Asignaciones actuales: {nombre}: {cant} unidades")
                else:
                    errores.append("Nadie ha tomado unidades aún.")

            # Si ya hay errores de cantidad, no seguimos con materiales
            if errores:
                raise forms.ValidationError(errores)

            # -----------------------------
            # 2. VALIDACIÓN DE MATERIALES
            # -----------------------------
            mueble = detalle.id_mueble
            materiales_mueble = MuebleMateriale.objects.filter(id_mueble=mueble)

            if not materiales_mueble.exists():
                errores.append(
                    f"El mueble '{mueble.nombre}' no tiene materiales asignados. No se puede aprobar producción."
                )
            else:
                for mm in materiales_mueble:
                    material = mm.id_material
                    cantidad_por_mueble = mm.cantidad or 0
                    total_necesario = cantidad_solicitada * cantidad_por_mueble

                    inventario = InventarioMateriale.objects.filter(
                        id_material=material,
                        ubicación=detalle.id_orden.id_sucursal
                    ).first()
                    disponible_material = inventario.cantidad_disponible if inventario else 0

                    if total_necesario > disponible_material:
                        errores.append(
                            f"Material insuficiente: {material.nombre} — Necesario: {total_necesario}, Disponible: {disponible_material} (Consumo por unidad: {cantidad_por_mueble})"
                        )

            if errores:
                raise forms.ValidationError(errores)

        # -----------------------------
        # 4. ASIGNAR CANTIDAD APROBADA
        # -----------------------------
        if self.instance.pk and self.instance.cant_aprobada is not None:
            cleaned["cant_aprobada"] = self.instance.cant_aprobada
        else:
            cleaned["cant_aprobada"] = cantidad_solicitada

        # Inicializar campo Aporte si no hay instancia previa
        if not self.instance.pk or getattr(self.instance, 'cant_aprobada', None) is None:
            cleaned['Aporte'] = 0

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
    list_display = ("id","estado")
    readonly_fields= ('estado',)
    # si tienes otros campos que quieres mostrar, agrégalos aquí

    class Media:
        js = ('js/filtros/filtro_orden_aportaciones.js','js/filtros/read_only_orden_aportaciones.js',)  # Archivo JS similar al de ListaCompra

    
    def save_model(self, request, obj, form, change):
        """
        - Usa el campo fantasma 'Aporte'
        - Controla que no supere lo aprobado
        - Cambia estado a:
            * 'trabajando' cuando hay avance
            * 'completo' cuando finalizada == aprobada
        """

        aporte = 0
        try:
            aporte = int(form.cleaned_data.get('Aporte') or 0)
        except Exception:
            aporte = 0

        if aporte < 0:
            aporte = 0

        finalizada_actual = obj.cantidad_finalizada or 0

        # Tope según lo aprobado
        max_remaining = None
        if obj.cant_aprobada is not None:
            max_remaining = obj.cant_aprobada - finalizada_actual
            if max_remaining < 0:
                max_remaining = 0

        # Ajuste de aporte si excede
        if max_remaining is not None and aporte > max_remaining:
            aporte_usado = max_remaining
            messages.warning(
                request,
                f"El aporte solicitado ({aporte}) excede el restante aprobado ({max_remaining}). "
                f"Se aplicará solamente {aporte_usado}."
            )
        else:
            aporte_usado = aporte

        # Actualizamos cantidad_finalizada
        nueva_finalizada = finalizada_actual + aporte_usado
        obj.cantidad_finalizada = nueva_finalizada

        # -------------------------
        # CAMBIOS DE ESTADO
        # -------------------------

        #SI YA COMPLETÓ
        if obj.cant_aprobada is not None and nueva_finalizada >= obj.cant_aprobada:
            obj.cantidad_finalizada = obj.cant_aprobada  # blindaje
            obj.estado = AportacionEmpleado.COMP
            messages.success(
                request,
                "Aportación completada al 100%. Estado cambiado a COMPLETO."
            )

        # SI SOLO ESTÁ AVANZANDO
        elif nueva_finalizada > 0 and obj.estado != AportacionEmpleado.TRAB:
            obj.estado = AportacionEmpleado.TRAB
            messages.info(
                request,
                f"Aportación marcada como 'Trabajando' porque hay {nueva_finalizada} unidades finalizadas."
            )

        # Guardamos normalmente
        super().save_model(request, obj, form, change)
          # -----------------------------------
        if obj.id_orden_detalle:
            total_finalizada = (
                AportacionEmpleado.objects
                .filter(id_orden_detalle=obj.id_orden_detalle)
                .aggregate(total=Sum("cantidad_finalizada"))["total"] or 0
            )
            detalle = obj.id_orden_detalle
            detalle.cantidad_producida = total_finalizada
            planificada = detalle.cantidad_planificada or 0

        if total_finalizada == 0:
            detalle.estado = OrdenMensualDetalle.PEND
        elif total_finalizada < planificada:
            detalle.estado = OrdenMensualDetalle.INCOMP
        else:  # total_finalizada >= planificada
            detalle.estado = OrdenMensualDetalle.COMP
        detalle.save()


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

    

