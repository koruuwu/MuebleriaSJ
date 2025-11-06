from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import *
from proyecto.supabase_client import subir_archivo
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import AdminConImagenMixin, PaginacionAdminMixin

# Formulario con campo de carga temporal
class ImagenForm(ValidacionesBaseForm):
    archivo_temp = forms.FileField(required=False, label="Subir imagen")

    class Meta:
        model = CategoriasMateriale
        fields = "__all__"
        widgets = {
            'nombre': WidgetsRegulares.nombre(),
            'stock_minimo': WidgetsRegulares.numero(4,allow_zero=False),
            'stock_maximo': WidgetsRegulares.numero(5, allow_zero=False),  
            
        }
    def clean_stock_minimo(self):
        numero = self.cleaned_data.get('stock_minimo')
        numero = self.validar_longitud(str(numero), "Stock minimo", min_len=1, max_len=4)
        return numero
    
    def clean_stock_maximo(self):
        numero = self.cleaned_data.get('stock_maximo')
        numero = self.validar_longitud(str(numero), "Stock maximo", min_len=1, max_len=5)
        return numero
    


    
@admin.register(Materiale)
class MaterialeAdmin(PaginacionAdminMixin, AdminConImagenMixin, admin.ModelAdmin):
    form = ImagenForm
    list_display = ("nombre","id_categoria", "stock_minimo","stock_maximo", "vista_previa")
    bucket_name="materiales"

@admin.register(CategoriasMateriale)
class CategoriasMaterialeAdmin(PaginacionAdminMixin, AdminConImagenMixin, admin.ModelAdmin):
    form = ImagenForm
    list_display = ("nombre", "descripcion", "vista_previa")
    bucket_name="materiales_cat"



@admin.register(UnidadesMedida)
class UnidadesMedidaAdmin(PaginacionAdminMixin,admin.ModelAdmin):
    list_display = ("nombre", "abreviatura")
    bucket_name="materiales"