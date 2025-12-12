from django.contrib import admin, messages
from .models import *
from django import forms
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import *
from proyecto.utils.admin_utils import PaginacionAdminMixin
# Register your models here.
from django.db import transaction
from django.utils import timezone
class SucursaleForm(ValidacionesBaseForm):
    class Meta:
        model = Sucursale
        fields = '__all__'
        widgets = {
            'nombre': WidgetsEspeciales.nombreSucursal(),
            'telefono': WidgetsRegulares.telefono(),
            'direccion': WidgetsRegulares.direccion(),
            'rtn': WidgetsRegulares.rtn(),
        }

class CAIMForm(ValidacionesBaseForm):
    class Meta:
        fields = "__all__"
        model = Cai
        widgets = {
            'rango_inicial': WidgetsRegulares.numero(8, False, "Ej: 10"),
            'rango_final': WidgetsRegulares.numero(8, False, "Ej: 10"),
            'codigo_cai': WidgetsRegulares.cai(),
        }
    
    


class CaiInline(admin.StackedInline):
    model = Cai
    extra = 0
    form = CAIMForm
    
    '''class Media:
        js = ('js/estados/cai.js',)'''

class CajaInline(admin.StackedInline):
    model = Caja
    extra = 0


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
           


            
