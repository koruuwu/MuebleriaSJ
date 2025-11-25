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
from Compras.models import Parametro, InventarioMueble
from Muebles.models import Mueble
from django.core.exceptions import ValidationError


# Register your models here.

class OrdenesVentaForm(forms.ModelForm):
    class Meta:
        model = OrdenesVenta
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        empleado = cleaned_data.get('id_empleado')
        
        if empleado and not empleado.id_sucursal:
            raise forms.ValidationError({
                'id_empleado': 'El empleado seleccionado no tiene una sucursal asignada.'
            })
            
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
        
        return super().response_change(request, obj)

