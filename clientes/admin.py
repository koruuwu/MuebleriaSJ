from django.contrib import admin, messages
from .models import *
from django import forms
from proyecto.validators import ValidacionesBaseForm
from proyecto.widgets import WidgetsRegulares
from proyecto.admin_utils import PaginacionAdminMixin

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
    def full_clean(self):
        """
        Sobrescribe full_clean para manejar el mensaje genérico en español
        """
        try:
            return super().full_clean()
        except ValidationError as e:
            # Si es un error de formulario completo, personalizar el mensaje
            if not hasattr(e, 'error_dict') and hasattr(e, 'message'):
                if e.message == "Please correct the errors below.":
                    raise ValidationError("Por favor, corrija los errores a continuación.")
            raise e
        
class DocumentosClienteInline(admin.TabularInline):
    model = DocumentosCliente
    form = DocumentosClienteForm
    extra = 0  # no muestres filas vacías adicionales 
    can_delete = False  # opcionalÑ
    
    def has_add_permission(self, request, obj=None):
        # Solo permite agregar si el cliente ya está guardado
        return obj is not None

    def has_change_permission(self, request, obj=None):
        # Solo permite editar si el cliente ya está guardado
        return obj is not None

    def has_delete_permission(self, request, obj=None):
        # Solo permite eliminar si el cliente ya está guardado
        return obj is not None


@admin.register(Cliente)
class ClientesAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    form = ClienteForm
    search_fields = ('nombre','telefono')
    list_display = ('id','nombre','telefono','direccion')
    list_display_links = ('nombre',)
    list_filter = ('usuario_final',)
    inlines = []
   



@admin.register(DocumentosCliente)
class DocumentosClientesAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    form = DocumentosClienteForm
    search_fields=('valor','id','id_cliente__nombre')#importante guion bajo para especificar que elemento de lleve foranea
    list_display=('id_cliente', 'id_documento','valor')
    list_display_links=('valor',)
    list_filter=('id_documento','id_cliente')
    