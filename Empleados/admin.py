from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import admin
from django.contrib.auth.models import Group

from proyecto.utils.admin_utils import ExportReportMixin, PaginacionAdminMixin

# Quitar admin original
admin.site.unregister(Group)

from proyecto.utils.admin_utils import ExportReportMixin, PaginacionAdminMixin
from .models import PerfilUsuario
from Sucursales.models import Sucursale, Caja
from django.urls import path
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from proyecto.utils.validators import ValidacionesBaseForm
import logging

logger = logging.getLogger(__name__)

class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    max_num = 1
    verbose_name_plural = "Información de sucursal/caja"
    fk_name = "user"

    class Media:
        js = ("filtros/filtrar_cajas_por_sucursal.js",)

    def get_extra(self, request, obj=None, **kwargs):
        if obj and hasattr(obj, "perfilusuario"):  # nombre del related_name o del modelo en minúsculas
            return 0
        return 1

    # Filtrar cajas dependiendo de la sucursal seleccionada
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "caja":
            if request.user.is_superuser:
                kwargs["queryset"] = Caja.objects.all()
            else:
                # filtrar cajas según la sucursal ligada al usuario
                perfil = PerfilUsuario.objects.filter(user=request.user).first()
                if perfil and perfil.sucursal:
                    kwargs["queryset"] = Caja.objects.filter(sucursal=perfil.sucursal)
                else:
                    kwargs["queryset"] = Caja.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
from django.contrib.auth.forms import UserCreationForm

class UsuarioCreationForm(UserCreationForm, ValidacionesBaseForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def clean_username(self):
        username = super().clean_username()


        if not username:
            raise ValidationError("El nombre de usuario es obligatorio.")
        
        username = self.validar_campo_texto(username, "El nombre de usuario", min_len=4, max_len=150)

        # Ejemplo 1: mínimo de longitud
        if len(username) < 5:
            raise ValidationError("El nombre de usuario debe tener al menos 5 caracteres.")

        # Ejemplo 2: solo letras y números
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError(
                "El nombre de usuario confirma solo puede contener letras, números y guión bajo."
            )

        # Ejemplo 3: evitar usernames solo numéricos
        if username.isdigit():
            raise ValidationError(
                "El nombre de usuario no puede contener solo números."
            )
        return username

    

class UsuarioChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"

    def clean_username(self):
        username = self.cleaned_data.get("username")

        if not username:
            raise ValidationError("El nombre de usuario es obligatorio.")

        # Ejemplo 1: mínimo de longitud
        if len(username) < 5:
            raise ValidationError("El nombre de usuario debe tener al menos 5 caracteres.")

        # Ejemplo 2: solo letras y números
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError(
                "El nombre de usuario confirma solo puede contener letras, números y guión bajo."
            )

        # Ejemplo 3: evitar usernames solo numéricos
        if username.isdigit():
            raise ValidationError(
                "El nombre de usuario no puede contener solo números."
            )

        return username
    
@admin.register(Group)
class GroupAdmin(ExportReportMixin, PaginacionAdminMixin, admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    filter_horizontal = ("permissions",)   # ✅ cambia el selector

    export_report_name = "Reporte de Grupos"
    export_filename_base = "Grupos"

class UsuarioAdmin(ExportReportMixin,UserAdmin):
    form = UsuarioChangeForm
    add_form = UsuarioCreationForm
    inlines = [PerfilUsuarioInline]

    

    # EDICIÓN
    fieldsets = (
        (None, {"fields": ("username",)}),
        ("Permisos", {"fields": ("is_active", "is_superuser", "groups", "user_permissions")}),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
    )

    export_report_name = "Reporte de Usuarios"
    export_filename_base = "Usuarios"
    

    # CREACIÓN
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2"),
        }),
    
    )

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        response = super().changeform_view(request, object_id, form_url, extra_context)

        if request.method == "POST" and hasattr(response, "context_data"):
            ctx = response.context_data

            # 1) Errores del formulario principal
            adminform = ctx.get("adminform")
            if adminform and adminform.form.errors:
                print("ERRORES FORM PRINCIPAL:")
                print(adminform.form.errors.as_json())
                logger.error("Errores form usuario: %s", adminform.form.errors.as_json())

            # 2) Errores de los inlines (aquí es donde sospechamos)
            inline_admin_formsets = ctx.get("inline_admin_formsets", [])
            for inline in inline_admin_formsets:
                formset = inline.formset

                if formset.non_form_errors():
                    print("ERRORES NON-FIELD DEL FORMSET:", formset.non_form_errors())
                    logger.error("Non-form errors: %s", formset.non_form_errors())

                for form in formset.forms:
                    if form.errors:
                        print(f"ERRORES INLINE {form.prefix}:")
                        print(form.errors.as_json())
                        logger.error("Errores inline %s: %s", form.prefix, form.errors.as_json())

        return response
    



    
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "filtrar_cajas_por_sucursal/<int:sucursal_id>/",
                self.admin_site.admin_view(self.filtrar_cajas),
                name="filtrar-cajas-por-sucursal",
            ),
        ]
        return custom + urls

    def filtrar_cajas(self, request, sucursal_id):
        try:
            # Validar que la sucursal exista
            sucursal = Sucursale.objects.filter(id=sucursal_id).first()
            if not sucursal:
                return JsonResponse([], safe=False)

            # Si existe, filtrar cajas por la sucursal
            cajas = Caja.objects.filter(sucursal=sucursal)
            data = [{"id": c.id, "nombre": c.codigo_caja} for c in cajas]

        except Exception as e:
            print("Error en filtrar_cajas:", e)
            data = []

        return JsonResponse(data, safe=False)
    
    def save_model(self, request, obj, form, change):
        if not change:  # SOLO al crear
            obj.is_staff = True
        super().save_model(request, obj, form, change)



admin.site.unregister(User)
admin.site.register(User, UsuarioAdmin)
