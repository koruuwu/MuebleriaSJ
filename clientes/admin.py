from django.contrib import admin, messages
from .models import *
from django import forms
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import PaginacionAdminMixin

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
        }
    
        
class DocumentosClienteInline(admin.TabularInline):
    model = DocumentosCliente
    form = DocumentosClienteForm
    extra = 0  # no muestres filas vacías adicionales 
    can_delete = False  # No permite eliminar desde el inline
    def has_add_permission(self, request, obj=None):
        return obj is not None  # Solo agregar si el cliente ya existe


@admin.register(Cliente)
class ClientesAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    form = ClienteForm
    search_fields = ('nombre','telefono')
    list_display = ('nombre','telefono','direccion')
    list_display_links = ('nombre',)
    list_filter = ('usuario_final',)
    inlines = [DocumentosClienteInline]
   



@admin.register(DocumentosCliente)
class DocumentosClientesAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    form = DocumentosClienteForm
    search_fields=('valor','id','id_cliente__nombre')#importante guion bajo para especificar que elemento de lleve foranea
    #solo en search fields y list filtrer
    list_display=('id_cliente', 'id_documento','valor')
    list_display_links=('valor',)
    list_filter=('id_documento','id_cliente')
    