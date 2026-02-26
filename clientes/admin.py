import re

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import *
from django import forms
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import PaginacionAdminMixin, ExportReportMixin

# PDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Excel
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter


class DocumentosClienteForm(forms.ModelForm):
    class Meta:
        model = DocumentosCliente
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        cliente = cleaned_data.get('id_cliente')
        documento = cleaned_data.get('id_documento')
        valor = cleaned_data.get('valor')

        if cliente and documento and valor:
            existe = DocumentosCliente.objects.exclude(pk=self.instance.pk).filter(
                id_cliente=cliente,
                id_documento=documento,
                valor=valor
            ).exists()
            if existe:
                raise ValidationError(
                    f"⚠️ El usuario {cliente.nombre} ya tiene registrado el documento "
                    f"'{documento.tipo_documento}' con valor {valor}."
                )
        return cleaned_data


class ClienteForm(ValidacionesBaseForm):
    class Meta:
        model = Cliente
        fields = '__all__'
        widgets = {
            'nombre': WidgetsRegulares.nombre(),
            'telefono': WidgetsRegulares.telefono(),
            'direccion': WidgetsRegulares.direccion(),
            'rtn': WidgetsRegulares.rtn(),
        }

        labels = {
            'telefono': "Teléfono",
            'direccion': "Dirección",
        }

    def clean_rtn(self):
        rtn = self.cleaned_data.get('rtn', '') or ''

        patron = r'^\d{4}-\d{4}-\d{6}$'
        if not re.match(patron, rtn):
            raise forms.ValidationError(
                "El RTN debe tener el formato 0000-0000-000000 (solo números y guiones)."
            )

        # Puedes retornar tal cual, o normalizar a solo dígitos si lo prefieres
        return rtn
    
        
class DocumentosClienteInline(admin.TabularInline):
    model = DocumentosCliente
    form = DocumentosClienteForm
    extra = 0  # no muestres filas vacías adicionales 
    can_delete = False  # No permite eliminar desde el inline
    def has_add_permission(self, request, obj=None):
        return obj is not None  # Solo agregar si el cliente ya existe


@admin.register(Cliente)
class ClientesAdmin(ExportReportMixin, PaginacionAdminMixin, admin.ModelAdmin):
    form = ClienteForm
    search_fields = ('nombre','telefono')
    list_display = ('nombre','telefono','direccion','total_pedidos')
    list_display_links = ('nombre',)
    list_filter = ()
    inlines = [DocumentosClienteInline]


    export_report_name = "Reporte de Clientes"
    export_filename_base = "clientes"
    

    

    def delete_model(self, request, obj):
        nombre = str(obj)
        obj.delete()
        self.message_user(request, f"El cliente '{nombre}' ha sido eliminado correctamente.", level=messages.SUCCESS)

    def delete_queryset(self, request, queryset):
        nombres = ', '.join([str(obj) for obj in queryset])
        queryset.delete()
        self.message_user(request, f'Clientes "{nombres}" fueron eliminados con éxito.', level=messages.SUCCESS)


    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)

        if request.method == 'POST' and obj:
            self.delete_model(request, obj)
            # Redirige a la lista de Clientes usando reverse
            url = reverse('admin:clientes_cliente_changelist')
            return HttpResponseRedirect(url)

        return super().delete_view(request, object_id, extra_context)



@admin.register(DocumentosCliente)
class DocumentosClientesAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    form = DocumentosClienteForm
    search_fields=('valor','id','id_cliente__nombre')#importante guion bajo para especificar que elemento de lleve foranea
    #solo en search fields y list filtrer
    list_display=('id_cliente', 'id_documento','valor')
    list_display_links=('valor',)
    list_filter=('id_documento','id_cliente')
    