from attrs import fields
from django.contrib import admin
from django import forms
from .models import *
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import AdminConImagenMixin, PaginacionAdminMixin, UniqueFieldAdminMixin
# Register your models here.
class ImagenForm(ValidacionesBaseForm):
    archivo_temp = forms.FileField(required=False, label="Subir imagen")

    class Meta:
        model = None
        fields = "__all__"
        widgets = {
            'nombre': WidgetsRegulares.nombre("Ej: Clarisa sensacional"),     
            'descripcion':WidgetsRegulares.comentario("Ej: Mueble color gris, ideal para 4 personas"),
            'precio_base': WidgetsRegulares.precio(13, False, "Ej: 20,000"),   
        }
   


class MuebleForm(ValidacionesBaseForm):
    archivo_temp = forms.FileField(required=False, label="Subir imagen")

    class Meta:
        model = Mueble
        fields = "__all__"
        widgets = {
            'nombre': WidgetsRegulares.nombre("Ej: Lusiana Pérez"),     
            'descripcion': WidgetsRegulares.comentario("Ej: Mueble color gris, ideal para 4 personas"),
            'precio_base': WidgetsRegulares.precio(6, False, "Ej: 20,000"),
            'alto': WidgetsRegulares.numero(4, False, "Ej: 10"),
            'ancho': WidgetsRegulares.numero(4, False, "Ej: 5"),
            'largo': WidgetsRegulares.numero(4, False, "Ej: 20"),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        return self.validar_campo_texto(nombre, "El nombre", min_len=4, max_len=50)


class TamañoForm(ValidacionesBaseForm):
    class Meta:
        model = Tamaño
        fields = "__all__"
        widgets = {
            'nombre': WidgetsRegulares.nombre("Ej: Pequeño"),     
            'descripcion': WidgetsRegulares.comentario("Ej: tamaño reducido para 2 personas"),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        return self.validar_campo_texto(nombre, "El nombre", min_len=4, max_len=50)




@admin.register(CategoriasMueble)
class CategoriasMuebleAdmin(PaginacionAdminMixin, AdminConImagenMixin, admin.ModelAdmin):
    form = ImagenForm
    list_display = ("nombre", "descripcion", "vista_previa")
    bucket_name="muebles_cat"



@admin.register(Tamaño)
class TamanoAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    form=TamañoForm
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
class MuebleAdmin(UniqueFieldAdminMixin,PaginacionAdminMixin, AdminConImagenMixin, admin.ModelAdmin):
    form = MuebleForm
    unique_fields = ['nombre']
    list_display = ("nombre", "descripcion","alto","ancho","largo","medida", "vista_previa")
    search_fields = ('nombre', 'medida')
    list_filter = ('tamano__nombre',)


    bucket_name="muebles"
    inlines=[MuebleMaterialeInline]
    fieldsets = [
        ("Información General", {"fields": ("nombre", "descripcion","precio_base","categoria","Descontinuado","archivo_temp","imagen","imagen_url")}),
        ("Medidas", {"fields": ("medida","alto","ancho","largo","tamano")}),
    ]