from attrs import fields
from django.contrib import admin
from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from .models import *
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import AdminConImagenMixin, PaginacionAdminMixin, UniqueFieldAdminMixin, ExportReportMixin
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
   
class HistorialPInline(admin.TabularInline):
    model = HistorialPreciosMueble
    extra = 0  
    def has_add_permission(self, request, obj=None):
        return False
    def has_change_permission(self, request, obj = ...):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    

class MuebleForm(ValidacionesBaseForm):
    archivo_temp = forms.FileField(required=False, label="Subir imagen")

    class Meta:
        model = Mueble
        fields = "__all__"
        widgets = {
            'nombre': WidgetsRegulares.nombre("Ej: Lusiana Pérez"),     
            'descripcion': WidgetsRegulares.comentario("Ej: Mueble color gris, ideal para 4 personas"),
            'precio_base': WidgetsRegulares.precio_decimal(6, False, "Ej: 20,000"),
            'alto': WidgetsRegulares.numero(4, False, "Ej: 10"),
            'ancho': WidgetsRegulares.numero(4, False, "Ej: 5"),
            'largo': WidgetsRegulares.numero(4, False, "Ej: 20"),
        }

        labels = {
            'stock_minimo':"Stock Mínimo",
            'stock_maximo':"Stock Máximo",
            }
        
        
    
    def clean_archivo_temp(self):
        archivo = self.cleaned_data.get('archivo_temp')

        if archivo:
            # Extensión
            ext = archivo.name.lower().split('.')[-1]

            # Tipo MIME
            mime = archivo.content_type

            extensiones_permitidas = ['jpg', 'jpeg', 'png']
            mime_permitidos = ['image/jpeg', 'image/png']

            if ext not in extensiones_permitidas:
                raise forms.ValidationError(
                    "La imagen debe ser JPG, JPEG o PNG."
                )

            if mime not in mime_permitidos:
                raise forms.ValidationError(
                    "El archivo no es una imagen válida."
                )

        return archivo
        

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
    
class MuebleMaterialeForm(forms.ModelForm):
    class Meta:
        model = MuebleMateriale
        fields = "__all__"

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get("cantidad")
        if cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor a 0.")
        return cantidad




@admin.register(CategoriasMueble)
class CategoriasMuebleAdmin(ExportReportMixin,PaginacionAdminMixin, AdminConImagenMixin, admin.ModelAdmin):
    form = ImagenForm
    list_display = ("nombre", "descripcion", "vista_previa")
    bucket_name="muebles_cat"

    export_report_name = "Reporte de Categorías de Muebles"
    export_filename_base = "Categorias_de_Muebles"
    export_exclude_fields = ("vista_previa",)



@admin.register(Tamaño)
class TamanoAdmin(ExportReportMixin,PaginacionAdminMixin, admin.ModelAdmin):
    form=TamañoForm
    list_display = ("nombre", "descripcion")

    export_report_name = "Reporte de Tamaños"
    export_filename_base = "Tamaños"
    

    def delete_model(self, request, obj):
        nombre = str(obj)
        obj.delete()
        self.message_user(request, f"El tamaño '{nombre}' ha sido eliminado correctamente.", level=messages.SUCCESS)

    def delete_queryset(self, request, queryset):
        nombres = ', '.join([str(obj) for obj in queryset])
        queryset.delete()
        self.message_user(request, f'Los tamaños "{nombres}" fueron eliminados con éxito.', level=messages.SUCCESS)

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)

        if request.method == 'POST' and obj:
            self.delete_model(request, obj)
            
            url = reverse('admin:%s_%s_changelist' % (self.model._meta.app_label, self.model._meta.model_name))
            return HttpResponseRedirect(url)

        return super().delete_view(request, object_id, extra_context)

@admin.register(MuebleMateriale)
class MuebleMaterialAdmin(ExportReportMixin,PaginacionAdminMixin, admin.ModelAdmin):
    form = MuebleMaterialeForm
    list_display = ("id_mueble", "id_material", "cantidad")
    search_fields = ('id_mueble__nombre', 'id_material__nombre')

    export_report_name = "Reporte de Materiales de Muebles"
    export_filename_base = "Materiales_de_Muebles"

    export_report_name = "Reporte de Muebles-Materiales"
    export_filename_base = "Muebles-Materiales"
    

class MuebleMaterialeInline(admin.TabularInline):
    model = MuebleMateriale
    extra = 0  # no muestres filas vacías adicionales 
    can_delete = False  # No permite eliminar desde el inline
    def has_add_permission(self, request, obj=None):
        return obj is not None  # Solo agregar si el cliente ya exist
    
@admin.register(Mueble)
class MuebleAdmin(UniqueFieldAdminMixin,PaginacionAdminMixin, AdminConImagenMixin, ExportReportMixin, admin.ModelAdmin):
    form = MuebleForm
    unique_fields = ['nombre']
    list_display = ("nombre", "descripcion","alto","ancho","largo","medida", "vista_previa")
    search_fields = ('nombre', 'descripcion')
    list_filter = ('tamano__nombre',)


    bucket_name="muebles"
    inlines=[MuebleMaterialeInline, HistorialPInline]
    fieldsets = [
        ("Información General", {"fields": ("nombre", "descripcion","precio_base","categoria","Descontinuado","archivo_temp","imagen","imagen_url")}),
        ("Medidas", {"fields": ("medida","alto","ancho","largo","tamano")}),
        ("Stock", {"fields": ("stock_maximo","stock_minimo")}),
    ]

    export_report_name = "Reporte de Muebles"
    export_filename_base = "muebles"
    export_exclude_fields = ("vista_previa",)

#Nuevos admin para reportes

@admin.register(HistorialPreciosMueble)
class HistorialPreciosMuebleAdmin(ExportReportMixin, PaginacionAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "id_mueble",
        "precio",
        "fecha_inicio",
        "fecha_fin",
    )
    search_fields = (
        "id_mueble__nombre",
    )
    list_filter = (
        "fecha_inicio",
        "fecha_fin",
        "id_mueble",
    )

    export_report_name = "Reporte de Historial de Precios de Muebles"
    export_filename_base = "Historial_Precios_Muebles"