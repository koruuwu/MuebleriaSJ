from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(Cliente)
class ClientesAdmin(admin.ModelAdmin):
    search_fields=('nombre','telefono')
    list_display=('id', 'nombre','telefono','direccion')
    list_display_links=('nombre',)

@admin.register(DocumentosCliente)
class DocumentosClientesAdmin(admin.ModelAdmin):
    search_fields=('valor','id','id_cliente__nombre')#importante guion bajo para especificar que elemento de lleve foranea
    list_display=('id_cliente', 'id_documento','valor')
    list_display_links=('valor',)
    list_filter=('id_documento','id_cliente')
