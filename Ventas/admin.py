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
    class Meta:
        model = OrdenesVenta
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        
        return cleaned_data
    
  

class DetallesOrdeneForm(forms.ModelForm):
    class Meta:
        model = DetallesOrdene
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        
        # Solo validar si el formulario tiene datos básicos válidos
        if not self.is_valid():
            return cleaned_data
            
        mueble = cleaned_data.get('id_mueble')
        cantidad = cleaned_data.get('cantidad')
        
        # Para nuevas órdenes, la validación se hará en save_related
        # Aquí solo validamos datos básicos del formulario
        if mueble and cantidad and cantidad <= 0:
            raise forms.ValidationError({
                'cantidad': 'La cantidad debe ser mayor a 0'
            })
        
        return cleaned_data

class DetallesOInline(admin.StackedInline):
    model = DetallesOrdene
    form = DetallesOrdeneForm
    extra = 0
    
    class Media:
        js = ('js/detalle_orden.js',)
 

@admin.register(OrdenesVenta)
class OrdenesVentasAdmin(ValidacionInventarioMixin, admin.ModelAdmin):
    form = OrdenForm
    inlines = [DetallesOInline]



    def save_related(self, request, form, formsets, change):

        orden = form.instance

        # 1. Validación general reutilizable
        errores = self.validar_inventario(request, orden, formsets)

        if errores:
            for e in errores:
                messages.error(request, e)
            return  # No guarda si hay errores

        # 2. Guardar orden + detalles
        super().save_related(request, form, formsets, change)

        # 3. Actualizar inventario reutilizable
        self.actualizar_inventario(orden, request)


    class Media:
        js = ("js/generacion_c/factura_dinamica.js",)
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("obtener_precio_mueble/<int:mueble_id>/", self.admin_site.admin_view(self.obtener_precio_mueble)),
            path("generar_factura/", 
            self.admin_site.admin_view(self.generar_factura), 
            name="generar-factura"),
            path("obtener_empleado_logeado/", 
            self.admin_site.admin_view(self.obtener_empleado_logeado),
            name="obtener-empleado-logeado"),
        ]
        return custom + urls
    
    def generar_factura(self, request):
        try:
            # Obtener el perfil del usuario logueado
            perfil = PerfilUsuario.objects.filter(user=request.user).first()

            if not perfil:
                return JsonResponse({"error": "El usuario no tiene un perfil asignado"})
            
            if not perfil.sucursal or not perfil.caja:
                return JsonResponse({"error": "El perfil del usuario no tiene sucursal o caja asignada"})

            parametro = Parametro.objects.get(id=2)

            # Obtener CAI activo para la sucursal del usuario
            cai = Cai.objects.filter(sucursal=perfil.sucursal, activo=True).first()
            if not cai:
                return JsonResponse({"error": "No hay CAI activo para esta sucursal"})

            # Obtener siguiente correlativo sin guardar
            correlativo_actual = int(cai.ultima_secuencia or "0")
            siguiente_correlativo = correlativo_actual + 1


            # Validar rango
            rango_final = int(cai.rango_final)
            if siguiente_correlativo > rango_final:
                return JsonResponse({"error": "Se ha alcanzado el límite de numeración para este CAI"})

            # Armar número de factura con sucursal y caja del perfil
            numero_factura = (
                f"{perfil.sucursal.codigo_sucursal}-"
                f"{perfil.caja.codigo_caja}-"
                f"{parametro.valor}-"
                f"{str(siguiente_correlativo).zfill(8)}"
            )

            return JsonResponse({
                "numero_factura": numero_factura,
                "correlativo": siguiente_correlativo
            })

        except Exception as e:
            return JsonResponse({"error": str(e)})

    def save_model(self, request, obj, form, change):
        perfil = PerfilUsuario.objects.filter(user=request.user).first()

        # Asignar automáticamente el empleado (PerfilUsuario) al crear
        if not change and perfil:
            obj.id_empleado = perfil

        # Solo actualizar CAI cuando se guarda una nueva orden
        if not change and obj.id_factura:
            partes = obj.id_factura.split('-')
            if len(partes) >= 4:
                secuencia = partes[-1]

                if perfil and perfil.sucursal:
                    cai = Cai.objects.filter(
                        sucursal=perfil.sucursal,
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




    '''list_display=('id_factura', 'id_cliente', 'total', 'id_estado_pago', 'fecha_entrega')
    readonly_fields = ('fecha_orden',)

    class Media:
        js = ("js/factura_dinamica.js",)

    

    def obtener_precio_mueble(self, request, mueble_id):
        try:
            mueble = Mueble.objects.get(id=mueble_id)
            return JsonResponse({"precio": mueble.precio_base})
        except Mueble.DoesNotExist:
            return JsonResponse({"precio": 0})

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("obtener_precio_mueble/<int:mueble_id>/", self.admin_site.admin_view(self.obtener_precio_mueble)),
            path(
                "generar_factura/<int:empleado_id>/<int:caja_id>/",
                self.admin_site.admin_view(self.generar_factura),
            ),
        ]
        return custom + urls
    
   

    





    def save_related(self, request, form, formsets, change):
        """
        Guarda los objetos relacionados con validación de inventario
        """
        orden = form.instance
        errores = []

        # Primero validar todo el inventario antes de guardar
        for formset in formsets:
            if formset.model == DetallesOrdene:
                for detalle_form in formset:
                    if (detalle_form.cleaned_data and 
                        not detalle_form.cleaned_data.get('DELETE', False)):
                        
                        mueble = detalle_form.cleaned_data.get('id_mueble')
                        cantidad = detalle_form.cleaned_data.get('cantidad')
                        
                        if mueble and cantidad and orden.id_empleado and orden.id_empleado.id_sucursal:
                            inventario = InventarioMueble.objects.filter(
                                id_mueble=mueble,
                                ubicación=orden.id_empleado.id_sucursal,
                                estado=True
                            ).first()

                            if not inventario:
                                errores.append(
                                    f"No hay inventario disponible para {mueble.nombre} "
                                    f"en la sucursal {orden.id_empleado.id_sucursal}"
                                )
                            elif inventario.cantidad_disponible < cantidad:
                                errores.append(
                                    f"Stock insuficiente para {mueble.nombre}. "
                                    f"Disponible: {inventario.cantidad_disponible}, "
                                    f"Solicitado: {cantidad}"
                                )
        
        if errores:
            # Mostrar errores como mensajes en el formulario
            for error in errores:
                messages.error(request, error)
            # No guardar los detalles si hay errores de inventario
            return
        
        # Si todo está bien, guardar normalmente
        super().save_related(request, form, formsets, change)
        
        # Actualizar el inventario después de guardar
        self.actualizar_inventario_despues_de_guardar(orden)

    def actualizar_inventario_despues_de_guardar(self, orden):
        """
        Actualiza el inventario después de que la orden y sus detalles han sido guardados
        """
        detalles = DetallesOrdene.objects.filter(id_orden=orden)
        
        for detalle in detalles:
            mueble = detalle.id_mueble
            cantidad_vendida = detalle.cantidad

            inventario = InventarioMueble.objects.filter(
                id_mueble=mueble,
                ubicación=orden.id_empleado.id_sucursal,
                estado=True
            ).first()

            if inventario:
                # Verificar nuevamente el stock antes de actualizar
                if inventario.cantidad_disponible >= cantidad_vendida:
                    inventario.cantidad_disponible -= cantidad_vendida
                    inventario.ultima_salida = timezone.now().date()
                    inventario.save()
                else:
                    # Esto no debería pasar si la validación anterior fue exitosa
                    print(f"Advertencia: Stock insuficiente al actualizar inventario para {mueble.nombre}")

    def response_add(self, request, obj, post_url_continue=None):
        """
        Maneja la respuesta después de agregar una nueva orden
        """
        # Verificar si hay mensajes de error
        storage = messages.get_messages(request)
        has_errors = any(message.level == messages.ERROR for message in storage)
        
        if has_errors:
            # Si hay errores, mostrar el formulario nuevamente
            return self.changeform_view(request, None, form_url='', extra_context=None)
        
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        """
        Maneja la respuesta después de cambiar una orden existente
        """
        # Verificar si hay mensajes de error
        storage = messages.get_messages(request)
        has_errors = any(message.level == messages.ERROR for message in storage)
        
        if has_errors:
            # Si hay errores, mostrar el formulario nuevamente
            return self.changeform_view(request, obj.pk, form_url='', extra_context=None)
        
        return super().response_change(request, obj)'''

