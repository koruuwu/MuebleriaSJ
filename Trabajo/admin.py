from django.contrib import admin

from Trabajo.models import AportacionEmpleado, OrdenMensuale, OrdenMensualDetalle


class AportacionMInline(admin.StackedInline):
    model = AportacionEmpleado
    extra = 0


class DetalleOrdenMInline(admin.StackedInline):
    model = OrdenMensualDetalle
    extra = 0
    inlines=(AportacionMInline,)


# Register your models here.
@admin.register(OrdenMensuale)
class OrdenMensualeAdmin(admin.ModelAdmin):
    inlines=(DetalleOrdenMInline,)

