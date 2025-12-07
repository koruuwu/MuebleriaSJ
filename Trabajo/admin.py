from django.contrib import admin
import nested_admin
from Trabajo.models import AportacionEmpleado, OrdenMensuale, OrdenMensualDetalle


class AportacionMInline(nested_admin.NestedStackedInline):
    model = AportacionEmpleado
    extra = 1

class DetalleOrdenMInline(nested_admin.NestedStackedInline):
    model = OrdenMensualDetalle
    extra = 1
    inlines = [AportacionMInline]

@admin.register(OrdenMensuale)
class OrdenMensualeAdmin(nested_admin.NestedModelAdmin):
    inlines = [DetalleOrdenMInline]

