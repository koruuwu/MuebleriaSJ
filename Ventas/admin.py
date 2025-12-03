from django.contrib import admin, messages
from .models import *
from django.forms import ModelForm
from django import forms
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import PaginacionAdminMixin
from django.urls import path
from django.http import JsonResponse
from Empleados.models import Empleado
from django.utils import timezone
from Sucursales.models import Cai
from Compras.models import Parametro, InventarioMueble
from Muebles.models import Mueble
from django.core.exceptions import ValidationError
from proyecto.utils.validators_inventario import ValidacionInventarioMixin


# Register your models here.


class OrdenForm(ModelForm):
    aporte = forms.FloatField(initial=0, required=False, label="Aporte")

    class Meta:
        model = OrdenesVenta
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        # VALIDACIÓN CAI (MOVIDA DESDE save_model)
        perfil = PerfilUsuario.objects.filter(user=self.current_user).first()

        if not perfil or not perfil.sucursal or not perfil.caja:
            raise ValidationError("El usuario no tiene sucursal o caja configurada.")

        cai = Cai.objects.filter(sucursal=perfil.sucursal, activo=True).first()
        if not cai:
            raise ValidationError("No hay CAI activo para esta sucursal.")

        siguiente = int(cai.ultima_secuencia or "0") + 1
        if siguiente > int(cai.rango_final):
            raise ValidationError("Se alcanzó el rango final del CAI.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        aporte = self.cleaned_data.get('aporte', 0) or 0

        # Sumar aporte
        if aporte:
            instance.pagado = (instance.pagado or 0) + aporte

        # Actualizar estado de pago
        try:
            estado_pagado = EstadoPagos.objects.get(nombre__iexact="Pagado")
            estado_pendiente = EstadoPagos.objects.get(nombre__iexact="Pendiente")
        except EstadoPagos.DoesNotExist:
            estado_pagado = estado_pendiente = None

        if instance.total and instance.pagado:
            if instance.pagado >= instance.total and estado_pagado:
                instance.id_estado_pago = estado_pagado
            elif estado_pendiente:
                instance.id_estado_pago = estado_pendiente

        if commit:
            instance.save()

        return instance

    
from django.forms import BaseInlineFormSet, ValidationError
from Compras.models import InventarioMueble
from Empleados.models import PerfilUsuario

from django.forms import BaseInlineFormSet, ValidationError
from Compras.models import InventarioMueble
from Empleados.models import PerfilUsuario

class DetallesOrdenFormSet(BaseInlineFormSet):

    def clean(self):
        super().clean()
        request = self.request
        perfil = PerfilUsuario.objects.filter(user=request.user).first()
        sucursal = getattr(perfil, "sucursal", None)

        if not sucursal:
            raise ValidationError("El usuario no tiene sucursal asignada.")

        errores = []

        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue

            mueble = form.cleaned_data.get("id_mueble")
            cantidad = form.cleaned_data.get("cantidad")

            if not mueble or not cantidad:
                continue

            inventario = InventarioMueble.objects.filter(
                id_mueble=mueble,
                ubicación=sucursal,
                estado=True
            ).first()

            if not inventario:
                errores.append(f"No hay inventario para {mueble.nombre} en {sucursal}")
            elif inventario.cantidad_disponible < cantidad:
                errores.append(
                    f"Stock insuficiente para {mueble.nombre}. "
                    f"Disponible: {inventario.cantidad_disponible}, solicitado: {cantidad}"
                )

        if errores:
            raise ValidationError(errores)


class DetallesOrdeneForm(forms.ModelForm):
    class Meta:
        model = DetallesOrdene
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad')

        if cantidad is not None and cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a 0.'})

        return cleaned_data


class DetallesOInline(admin.StackedInline):
    model = DetallesOrdene
    form = DetallesOrdeneForm
    extra = 0
    formset = DetallesOrdenFormSet

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.request = request
        return formset

    
    class Media:
        js = ('js/detalle_orden.js',)
 

@admin.register(OrdenesVenta)
class OrdenesVentasAdmin(ValidacionInventarioMixin, admin.ModelAdmin):
    form = OrdenForm
    inlines = [DetallesOInline]
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['aporte'].initial = 0
        form.current_user = request.user   # PASO CRÍTICO PARA EL CAI
        return form

    def get_changeform_initial_data(self, request):
        data = super().get_changeform_initial_data(request)
        data['aporte'] = 0
        return data



    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        self.actualizar_inventario(form.instance, request)



    class Media:
        js = ("js/ordenes_venta_aporte.js","js/generacion_c/factura_dinamica.js",)
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("obtener_precio_mueble/<int:mueble_id>/", self.admin_site.admin_view(self.obtener_precio_mueble)),
            path("obtener_empleado_logeado/", 
            self.admin_site.admin_view(self.obtener_empleado_logeado),
            name="obtener-empleado-logeado"),
        ]
        return custom + urls
    
 

    def save_model(self, request, obj, form, change):

        # La validación del CAI YA ESTÁ EN EL FORM

        if not change:
            perfil = PerfilUsuario.objects.filter(user=request.user).first()
            parametro = Parametro.objects.get(id=2)
            cai = Cai.objects.filter(sucursal=perfil.sucursal, activo=True).first()

            siguiente = int(cai.ultima_secuencia or "0") + 1

            numero_factura = (
                f"{perfil.sucursal.codigo_sucursal}-"
                f"{perfil.caja.codigo_caja}-"
                f"{parametro.valor}-"
                f"{str(siguiente).zfill(8)}"
            )

            obj.id_factura = numero_factura

        super().save_model(request, obj, form, change)

        # Actualizar CAI solo cuando la orden se ha guardado
        if not change:
            cai.ultima_secuencia = str(siguiente).zfill(8)
            cai.save()





    def obtener_empleado_logeado(self, request):
        perfil = PerfilUsuario.objects.filter(user=request.user).first()
        return JsonResponse({
            "id_empleado": perfil.id if perfil else None
        })
    
    def obtener_precio_mueble(self, request, mueble_id):
        try:
            mueble = Mueble.objects.get(id=mueble_id)
            return JsonResponse({"precio": mueble.precio_base})
        except Mueble.DoesNotExist:
            return JsonResponse({"precio": 0})




''' list_display=('id_factura', 'id_cliente', 'total', 'id_estado_pago', 'fecha_entrega')
    readonly_fields = ('fecha_orden',)'''


    
   

    




