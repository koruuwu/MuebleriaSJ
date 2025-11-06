# proyecto/admin_utils.py
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
