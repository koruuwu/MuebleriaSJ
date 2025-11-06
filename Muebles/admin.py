from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import CategoriasMateriales
from proyecto.supabase_client import subir_archivo
from proyecto.utils.admin_utils import AdminConImagenMixin

# Formulario con campo de carga temporal
class CategoriasMaterialesForm(forms.ModelForm):
    archivo_temp = forms.FileField(required=False, label="Subir imagen")

    class Meta:
        model = CategoriasMateriales
        fields = "__all__"


@admin.register(CategoriasMateriales)
class CategoriasMaterialesAdmin( AdminConImagenMixin, admin.ModelAdmin):
    form = CategoriasMaterialesForm
    list_display = ("nombre", "descripcion", "vista_previa")
    bucket_name="materiales_cat"

