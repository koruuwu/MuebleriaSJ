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
        }

class CaiInline(admin.StackedInline):
    model = Cai
    extra = 0
    
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

        # --- TU LÓGICA AQUÍ ---
        sucursal = form.instance

        with transaction.atomic():
            hoy = timezone.now().date()
            cais = Cai.objects.select_for_update().filter(sucursal=sucursal)

            # 1) Desactivar vencidos o excedidos
            for cai in cais:
                desactivar = False

                if cai.fecha_vencimiento and cai.fecha_vencimiento < hoy:
                    cai.activo = False
                    desactivar = True
                else:
                    try:
                        ultima = int(cai.ultima_secuencia or "0")
                        final = int(cai.rango_final or "0")
                        if ultima >= final:
                            cai.activo = False
                            desactivar = True
                    except:
                        pass

                if desactivar:
                    cai.save(update_fields=['activo'])

            # 2) Releer
            activos = list(Cai.objects.filter(
                sucursal=sucursal, activo=True
            ).order_by('fecha_vencimiento'))

            # 3) Activar automático si ninguno activo
            if len(activos) == 0:
                candidato = (Cai.objects.filter(
                    sucursal=sucursal,
                    fecha_vencimiento__gte=hoy
                )
                .order_by('fecha_vencimiento')
                .first())

                if candidato:
                    candidato.activo = True
                    candidato.save(update_fields=['activo'])

                    messages.info(
                        request,
                        f"No había CAIs activos. Se activó automáticamente el CAI {candidato.codigo_cai}"
                    )

            # 4) Si hay más de uno activo
            activos = list(Cai.objects.filter(
                sucursal=sucursal, activo=True
            ).order_by('fecha_vencimiento'))

            if len(activos) > 1:
                ganador = activos[0]
                Cai.objects.filter(
                    sucursal=sucursal, activo=True
                ).exclude(pk=ganador.pk).update(activo=False)

                messages.warning(
                    request,
                    f"Se dejó activo el CAI {ganador.codigo_cai}"
                )

            elif len(activos) == 1:
                messages.success(
                    request,
                    f"CAI activo: {activos[0].codigo_cai}"
                )

            
