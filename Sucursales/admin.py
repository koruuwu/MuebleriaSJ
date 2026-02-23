from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import *
from django import forms
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import *
from proyecto.utils.admin_utils import PaginacionAdminMixin
# Register your models here.
from django.db import transaction
from django.utils import timezone
from django import forms



class SucursaleForm(ValidacionesBaseForm):
    class Meta:
        model = Sucursale
        fields = '__all__'
        widgets = {
            'codigo_sucursal' : WidgetsRegulares.codigos(),
            'nombre': WidgetsEspeciales.nombreSucursal(),
            'telefono': WidgetsRegulares.telefono(),
            'direccion': WidgetsRegulares.direccion(),
            'rtn': WidgetsRegulares.rtn(),
        }

    def clean_rtn(self):
        rtn = self.cleaned_data.get('rtn', '')

        if not rtn.isdigit():
            raise forms.ValidationError("El RTN debe contener solo números.")

        if len(rtn) != 14:
            raise forms.ValidationError("El RTN debe tener exactamente 14 dígitos.")

        return rtn

    def clean_nombre(self):
        valor = self.cleaned_data.get('nombre', '')
        return self.validar_campo_texto(valor, "El nombre de la sucursal", min_len=5, max_len=60)
    
    def clean_codigo_sucursal(self):
        valor = self.cleaned_data.get('codigo_sucursal', '')
        
        if not valor.isdigit():
            raise forms.ValidationError("El valor debe ser un número positivo.")
        
        valor_num = float(valor)
        if valor_num < 0:
            raise forms.ValidationError("El valor debe ser un número positivo.")
        
        return valor

class CAIMForm(ValidacionesBaseForm):
    class Meta:
        fields = "__all__"
        model = Cai
        widgets = {
            'rango_inicial': WidgetsRegulares.numero(8, False, "Ej: 10"),
            'rango_final': WidgetsRegulares.numero(8, False, "Ej: 10"),
            'codigo_cai': WidgetsRegulares.cai(),
        }

    def clean(self):
        cleaned_data = super().clean()

        rango_inicial = cleaned_data.get('rango_inicial')
        rango_final = cleaned_data.get('rango_final')

        if rango_inicial and rango_final:
            try:
                inicial = int(rango_inicial)
                final = int(rango_final)

                if inicial >= final:
                    raise forms.ValidationError("El rango final debe ser mayor que el rango inicial.")
            except ValueError:
                raise forms.ValidationError("Los rangos deben ser números válidos.")
            
        if fecha_emision := cleaned_data.get('fecha_emision'):
            if fecha_vencimiento := cleaned_data.get('fecha_vencimiento'):
                if fecha_vencimiento <= fecha_emision:
                    raise forms.ValidationError("La fecha de vencimiento debe ser posterior a la fecha de emisión.")

        return cleaned_data
    
    
class CajaForm(ValidacionesBaseForm, WidgetsRegulares, forms.ModelForm):
    class Meta:
        model = Caja
        fields = "__all__"
        widgets = {
            'codigo_caja': WidgetsRegulares.codigos(),
        }

class CaiInline(admin.StackedInline):
    model = Cai
    extra = 0
    form = CAIMForm
    can_delete = True

    def has_delete_permission(self, request, obj=None):
        return True


    class Media:
        js = ("js/cai_select_all.js",)
    
    '''class Media:
        js = ('js/estados/cai.js',)'''

class CajaInline(admin.StackedInline):
    model = Caja
    extra = 0
    form = CajaForm


@admin.register(Sucursale)
class SucursalesAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    form = SucursaleForm
    search_fields = ('id', 'nombre', 'direccion', 'telefono')
    list_display = ('id', 'nombre', 'direccion', 'telefono', 'fecha_registro')
    list_display_links = ('id', 'nombre')
    readonly_fields = ('fecha_registro',)
    inlines=[CaiInline, CajaInline,]
 

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for instance in instances:
            instance.save()

        for obj in formset.deleted_objects:
            obj.delete()

        formset.save_m2m()

        sucursal = form.instance

        with transaction.atomic():
            hoy = timezone.now().date()
            cais = Cai.objects.select_for_update().filter(sucursal=sucursal)

            cais_validos = []

            # 1) VALIDAR TODOS
            for cai in cais:
                valido = True

                # Validar fecha
                if cai.fecha_vencimiento and cai.fecha_vencimiento < hoy:
                    valido = False

                # Validar rango
                try:
                    ultima = int(cai.ultima_secuencia or "0")
                    final = int(cai.rango_final or "0")
                    if ultima >= final:
                        valido = False
                except:
                    valido = False

                # Si no es válido → DESACTIVAR
                if not valido:
                    if cai.activo:
                        cai.activo = False
                        cai.save(update_fields=['activo'])
                else:
                    cais_validos.append(cai)

            # 2) SI NINGUNO ES VÁLIDO → NINGUNO SE ACTIVA
            if not cais_validos:
                messages.warning(
                    request,
                    "Ningún CAI cumple las validaciones. No se activó ningún CAI."
                )
                return

            # 3) TOMAR SOLO LOS QUE NO VENCEN HOY
            candidatos = [
                cai for cai in cais_validos
                if cai.fecha_vencimiento and cai.fecha_vencimiento > hoy
            ]

            # Si todos vencen hoy, no se activa ninguno
            if not candidatos:
                messages.warning(
                    request,
                    "Todos los CAIs válidos vencen hoy. No se activó ningún CAI."
                )
                return

            # 4) GANADOR = EL DE FECHA MÁS PRÓXIMA (NO HOY)
            ganador = sorted(
                candidatos,
                key=lambda x: x.fecha_vencimiento
            )[0]

            # 5) ACTIVAR SOLO EL GANADOR
            Cai.objects.filter(
                sucursal=sucursal
            ).update(activo=False)

            ganador.activo = True
            ganador.save(update_fields=['activo'])

            if not hasattr(request, '_cai_message_sent'):
                messages.success(
                    request,
                    f"Se activó automáticamente el CAI {ganador.codigo_cai} con fecha de vencimiento más próxima {ganador.fecha_vencimiento.strftime('%d/%m/%Y')}"
                )
                request._cai_message_sent = True
            # Segundo mensaje con fecha de vencimiento

    def delete_model(self, request, obj):
        nombre = str(obj)
        obj.delete()
        self.message_user(request, f"La Sucursal '{nombre}' ha sido eliminada correctamente.", level=messages.SUCCESS)

    def delete_queryset(self, request, queryset):
        nombres = ', '.join([str(obj) for obj in queryset])
        queryset.delete()
        self.message_user(request, f'Las sucursales "{nombres}" fueron eliminadas con éxito.', level=messages.SUCCESS)

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)

        if request.method == 'POST' and obj:
            self.delete_model(request, obj)
            
            url = reverse('admin:%s_%s_changelist' % (self.model._meta.app_label, self.model._meta.model_name))
            return HttpResponseRedirect(url)

        return super().delete_view(request, object_id, extra_context)

    def response_add(self, request, obj, post_url_continue=None):
        """
        Se ejecuta después de agregar un objeto.
        Aquí podemos mostrar solo nuestro mensaje personalizado.
        """
        self.message_user(request, f'La sucursal "{obj}" ha sido creada correctamente.', level=messages.SUCCESS)
        
        # Redirigir a la página de listado
        return HttpResponseRedirect(self.get_admin_url('changelist'))

    def get_admin_url(self, action):
        """
        Helper para generar la URL del admin para esta app/modelo
        """
        return reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_{action}')
           


            
