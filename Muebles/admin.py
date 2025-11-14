from django.contrib import admin
from django import forms
from .models import *
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import AdminConImagenMixin, PaginacionAdminMixin
# Register your models here.
class ImagenForm(ValidacionesBaseForm):
    archivo_temp = forms.FileField(required=False, label="Subir imagen")

    class Meta:
        model = CategoriasMueble
        fields = "__all__"
        widgets = {
            'nombre': WidgetsRegulares.nombre("Ej: Lusiana Pérez"),        
        }
    

@admin.register(CategoriasMueble)
class CategoriasMuebleAdmin(PaginacionAdminMixin, AdminConImagenMixin, admin.ModelAdmin):
    form = ImagenForm
    list_display = ("nombre", "descripcion", "vista_previa")
    bucket_name="muebles_cat"



@admin.register(Tamaño)
class TamanoAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    list_display = ("nombre", "descripcion")

@admin.register(MuebleMateriale)
class MuebleMaterialAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    list_display = ("id_mueble", "id_material")

class MuebleMaterialeInline(admin.TabularInline):
    model = MuebleMateriale
    extra = 0  # no muestres filas vacías adicionales 
    can_delete = False  # No permite eliminar desde el inline
    def has_add_permission(self, request, obj=None):
        return obj is not None  # Solo agregar si el cliente ya exist
    
@admin.register(Mueble)
class MuebleAdmin(PaginacionAdminMixin, AdminConImagenMixin, admin.ModelAdmin):
    form = ImagenForm
    list_display = ("nombre", "descripcion","alto","ancho","largo","medida", "vista_previa")
    bucket_name="muebles"
    inlines=[MuebleMaterialeInline]