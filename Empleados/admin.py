from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import PerfilUsuario
from Sucursales.models import Sucursale, Caja
from django.urls import path
from django.http import JsonResponse

class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = "Información de sucursal/caja"
    fk_name = "user"
    class Media:
        js = ("filtros/filtrar_cajas_por_sucursal.js",)

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

class UsuarioAdmin(UserAdmin):
    inlines = (PerfilUsuarioInline,)
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


admin.site.unregister(User)
admin.site.register(User, UsuarioAdmin)
