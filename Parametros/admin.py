from django.contrib import admin
from .models import Parametro
from proyecto.utils.admin_utils import  ExportReportMixin, PaginacionAdminMixin, UniqueFieldAdminMixin
from django import forms
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares


class ParametroForm(ValidacionesBaseForm, forms.ModelForm):
    class Meta:
        model = Parametro
        fields = "__all__"
        widgets = {
            'valor': WidgetsRegulares.numero(10, allow_zero=True, placeholder="Ej: 10"),
        }

    def clean_nombre(self):
        valor = self.cleaned_data.get('nombre', '')
        return self.validar_campo_texto(valor, "El nombre", min_len=2, max_len=50)
    
    def clean_valor(self):
        valor = self.cleaned_data.get('valor', '')
        
        if not valor.isdigit():
            raise forms.ValidationError("El valor debe ser un número positivo.")
        
        valor_num = float(valor)
        if valor_num < 0:
            raise forms.ValidationError("El valor debe ser un número positivo.")
        
        return valor

@admin.register(Parametro)
class ParametroAdmin(ExportReportMixin,PaginacionAdminMixin, admin.ModelAdmin):
    form = ParametroForm
    list_display= ("id", "nombre","valor")

    export_report_name = "Reporte de Parámetros"
    export_filename_base = "Parametros"
    


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