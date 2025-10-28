from django.contrib import admin, messages
from .models import *
from django import forms


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


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={
                'onkeypress': "return /[a-zA-Z\\s]/.test(event.key);",
                'placeholder': 'Ej: Lusiana Pérez',
            }),
            'telefono': forms.TextInput(attrs={
                'onkeypress': "return /[0-9\\+\\-\\s]/.test(event.key);",
                'placeholder': 'Ej: 9876-5432',
                'oninput': """
                    this.value = this.value.replace(/[^0-9]/g, '');
                    if (this.value.length > 4) {
                        this.value = this.value.substring(0,4) + '-' + this.value.substring(4,8);
                    }
                """
            }),
            'direccion': forms.TextInput(attrs={
                'placeholder': 'Ej: Col. Miraflores, Tegucigalpa, Bloque A, 2032',
            }),
        }

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').replace('-', '')
        if len(telefono) < 8:
            raise ValidationError("⚠️ El número de teléfono debe tener al menos 8 dígitos.")
        return telefono
        
    


@admin.register(Cliente)
class ClientesAdmin(admin.ModelAdmin):
    form = ClienteForm
    search_fields=('nombre','telefono')
    list_display=('id', 'nombre','telefono','direccion')
    list_display_links=('nombre',)
    list_per_page =1  # valor por defecto
    readonly_fields = ('creado',)
    list_filter=('usuario_final',)
    actions = ["set_pagination_1", "set_pagination_10", "set_pagination_25", "set_pagination_50", "set_pagination_100"]


    def set_pagination_1(self, request, queryset):
        request.session['per_page'] = 1
        self.message_user(request, "Mostrando 1 elementos por página.")
    set_pagination_1.short_description = "Mostrar 1 por página"

    def set_pagination_10(self, request, queryset):
        request.session['per_page'] = 10
        self.message_user(request, "Mostrando 10 elementos por página.")
    set_pagination_10.short_description = "Mostrar 10 por página"

    def set_pagination_25(self, request, queryset):
        request.session['per_page'] = 25
        self.message_user(request, "Mostrando 25 elementos por página.")
    set_pagination_25.short_description = "Mostrar 25 por página"

    def set_pagination_50(self, request, queryset):
        request.session['per_page'] = 50
        self.message_user(request, "Mostrando 50 elementos por página.")
    set_pagination_50.short_description = "Mostrar 50 por página"

    def set_pagination_100(self, request, queryset):
        request.session['per_page'] = 100
        self.message_user(request, "Mostrando 100 elementos por página.")
    set_pagination_100.short_description = "Mostrar 100 por página"

    # --- Lógica que aplica el cambio ---
    def changelist_view(self, request, extra_context=None):
        if 'per_page' in request.session:
            self.list_per_page = request.session['per_page']
        else:
            self.list_per_page = 10  # Valor por defecto

        return super().changelist_view(request, extra_context=extra_context)
   



@admin.register(DocumentosCliente)
class DocumentosClientesAdmin(admin.ModelAdmin):
    form = DocumentosClienteForm
    search_fields=('valor','id','id_cliente__nombre')#importante guion bajo para especificar que elemento de lleve foranea
    list_display=('id_cliente', 'id_documento','valor')
    list_display_links=('valor',)
    list_filter=('id_documento','id_cliente')
    actions = ["set_pagination_1", "set_pagination_10", "set_pagination_25", "set_pagination_50", "set_pagination_100"]

    def set_pagination_1(self, request, queryset):
        request.session['per_page'] = 1
        self.message_user(request, "Mostrando 1 elementos por página.")
    set_pagination_1.short_description = "Mostrar 1 por página"

    def set_pagination_10(self, request, queryset):
        request.session['per_page'] = 10
        self.message_user(request, "Mostrando 10 elementos por página.")
    set_pagination_10.short_description = "Mostrar 10 por página"

    def set_pagination_25(self, request, queryset):
        request.session['per_page'] = 25
        self.message_user(request, "Mostrando 25 elementos por página.")
    set_pagination_25.short_description = "Mostrar 25 por página"

    def set_pagination_50(self, request, queryset):
        request.session['per_page'] = 50
        self.message_user(request, "Mostrando 50 elementos por página.")
    set_pagination_50.short_description = "Mostrar 50 por página"

    def set_pagination_100(self, request, queryset):
        request.session['per_page'] = 100
        self.message_user(request, "Mostrando 100 elementos por página.")
    set_pagination_100.short_description = "Mostrar 100 por página"

    # --- Lógica que aplica el cambio ---
    def changelist_view(self, request, extra_context=None):
        if 'per_page' in request.session:
            self.list_per_page = request.session['per_page']
        else:
            self.list_per_page = 10  # Valor por defecto

        return super().changelist_view(request, extra_context=extra_context)

