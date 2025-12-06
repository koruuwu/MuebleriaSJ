from django.contrib import admin
from .models import Parametro
from proyecto.utils.admin_utils import  PaginacionAdminMixin, UniqueFieldAdminMixin
@admin.register(Parametro)
class ParametroAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    list_display= ("id", "nombre","valor")


    '''list_display = ("id", "fecha_solicitud","fecha_entrega", "prioridad", "estado")
    readonly_fields = ("fecha_solicitud","fecha_entrega",)
    list_filter = ('estado','prioridad',)
    inlines = [ListaCInline, DetalleRecibCInline]
    change_form_template = "admin/lista_compra_change_form.html"

    def get_readonly_fields(self, request, obj=None):
        # Si la orden está completa, todos los campos del admin son readonly
        if obj and obj.pk and obj.estado not in ['pendiente', 'rechazada','aprobada' ]:
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)'''