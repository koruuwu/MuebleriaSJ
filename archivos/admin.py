from django.contrib import admin, messages
from .models import Documento
from django import forms

class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = '__all__'
        widgets = {
            'tipo_documento': forms.TextInput(attrs={
                'onkeypress': "return /[a-zA-Z\s]/.test(event.key);",
                'placeholder': 'Solo letras (sin números)'
            })
        }



@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    form = DocumentoForm
    search_fields = ('id', 'tipo_documento')
    list_display = ('id', 'tipo_documento', 'descripcion')
    list_display_links = ('tipo_documento',)
    readonly_fields = ('fecha_registro',)

    def save_model(self, request, obj, form, change):
        # Verifica duplicado antes de guardar
        if Documento.objects.exclude(pk=obj.pk).filter(tipo_documento=obj.tipo_documento).exists():
            messages.warning(request, f'⚠️ El tipo de documento "{obj.tipo_documento}" ya existe.')
        else:
            super().save_model(request, obj, form, change)
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