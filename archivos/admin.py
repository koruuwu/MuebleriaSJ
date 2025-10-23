
from django.contrib import admin
from .models import *

@admin.register(Documento)
class DocumentosAdmin(admin.ModelAdmin):
    search_fields=('id', 'tipo_documento')
    list_display=('id', 'tipo_documento','descripcion')
    list_display_links=('tipo_documento',)
# Register your models here.
