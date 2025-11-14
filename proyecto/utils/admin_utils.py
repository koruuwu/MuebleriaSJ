# proyecto/admin_utils.py
from django import forms
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.utils.html import format_html
from proyecto.supabase_client import subir_archivo

class PaginacionAdminMixin:

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

    def changelist_view(self, request, extra_context=None):
        if 'per_page' in request.session:
            self.list_per_page = request.session['per_page']
        else:
            self.list_per_page = 10
        return super().changelist_view(request, extra_context=extra_context)





class AdminConImagenMixin:
    readonly_fields = ("vista_previa", "imagen_url", "imagen")
    bucket_name = "default"  # Cada admin puede sobrescribir este valor

    def save_model(self, request, obj, form, change):
        archivo = form.cleaned_data.get("archivo_temp")
        if archivo:
            ruta, url = subir_archivo(archivo, self.bucket_name)
            obj.imagen = ruta
            obj.imagen_url = url
        super().save_model(request, obj, form, change)

    def vista_previa(self, obj):
        if getattr(obj, "imagen_url", None):
            return format_html(
                '<img src="{}" style="max-height:100px;border-radius:8px;" />',
                obj.imagen_url,
            )
        return "Sin imagen"
    vista_previa.short_description = "Vista previa"



from django.contrib import admin
from django.core.exceptions import ValidationError

class UniqueFieldAdminMixin:
    """
    Mixin para ModelAdmin que valida campos únicos antes de guardar,
    sin necesidad de definir un ModelForm.
    """
    
    # Campo único o lista de campos únicos a validar
    unique_fields = []  # ['tipo_documento'] o ['campo1', 'campo2']

    def get_form(self, request, obj=None, **kwargs):
        """
        Inyecta dinámicamente la validación de duplicados en el form que genera el admin.
        """
        form = super().get_form(request, obj, **kwargs)

        unique_fields = self.unique_fields  # lista de campos a validar

        class _FormWithUniqueValidation(form):
            def clean(self_inner):
                cleaned_data = super(_FormWithUniqueValidation, self_inner).clean()
                for field in unique_fields:
                    valor = cleaned_data.get(field)
                    if valor is None:
                        continue
                    qs = self_inner._meta.model.objects.exclude(pk=self_inner.instance.pk)
                    if qs.filter(**{field: valor}).exists():
                        raise ValidationError({field: f'⚠️ El valor "{valor}" ya existe.'})
                return cleaned_data

        return _FormWithUniqueValidation


