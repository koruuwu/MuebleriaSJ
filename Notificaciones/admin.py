from django.contrib import admin

from .models import Notificacione

# Register your models here.
@admin.register(Notificacione)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'mensaje', 'creado', 'leida')
    list_filter = ('tipo', 'leida','object',)
    search_fields = ('mensaje',)
    readonly_fields = ('creado',)
    
    # Permite editar 'leida' directamente desde el listado
    list_editable = ('leida',)
