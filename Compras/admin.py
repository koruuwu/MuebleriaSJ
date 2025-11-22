from django.contrib import admin
from .models import *
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import  PaginacionAdminMixin, UniqueFieldAdminMixin
from datetime import timedelta
from django.urls import path
from django.http import JsonResponse
from django import forms

class InventarioForm(ValidacionesBaseForm):
    class Meta:
        fields = "__all__"
        model = InventarioMueble
        widgets = {
            'cantidad_disponible': WidgetsRegulares.numero(4, allow_zero=False, placeholder="Ej: 10"),
        }
    def clean_cantidad_disponible(self):
        numero = self.cleaned_data.get('cantidad_disponible')
        numero = self.validar_longitud(str(numero), "Cantida disponible", min_len=1, max_len=4)
        return numero
    


class CotizacioneForm(ValidacionesBaseForm):
    class Meta:
        model = Cotizacione
        fields = "__all__"
        widgets = {
            
        }


@admin.register(InventarioMueble)
class InventarioMuebleAdmin(PaginacionAdminMixin,admin.ModelAdmin):
    form = InventarioForm
    list_display = ("id_mueble","cantidad_disponible", "estado", "ubicación")
    search_fields = ('id_mueble', 'ubicación')
    readonly_fields=('ultima_entrada', 'ultima_salida')
    list_filter = ('estado','ubicación')

class DetalleCotizacionesInline(admin.StackedInline):
    model = DetalleCotizaciones
    extra = 0

    class Media:
        js = ('js/detalle_cotizacion.js',)

    

@admin.register(Cotizacione)
class CotizacioneAdmin(PaginacionAdminMixin,admin.ModelAdmin):
    form = CotizacioneForm
    list_display = ("cliente", "fecha_registro", "activo", "fecha_vencimiento")
    search_fields = ('cliente',)
    readonly_fields=("fecha_registro","fecha_vencimiento")
    list_filter = ('activo',)
    inlines = [DetalleCotizacionesInline]
    
  
    def save_model(self, request, obj, form, change):
        from django.utils import timezone

        if not change:  # Solo al crear
            obj.fecha_registro = timezone.now()

        try:
            dias_parametro = int(Parametro.objects.get(nombre='dias_cotizacion').valor)
        except (Parametro.DoesNotExist, ValueError):
            dias_parametro = 15

        if obj.fecha_registro:
            obj.fecha_vencimiento = obj.fecha_registro.date() + timedelta(days=dias_parametro)

        super().save_model(request, obj, form, change)

    def obtener_precio_mueble(self, request, mueble_id):
        try:
            mueble = Mueble.objects.get(id=mueble_id)
            return JsonResponse({"precio": mueble.precio_base})  # <- aquí el nombre correcto
        except Mueble.DoesNotExist:
            return JsonResponse({"precio": 0})


    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("obtener_precio_mueble/<int:mueble_id>/", self.obtener_precio_mueble),
        ]
        return custom + urls
#------------------------------------------COMPRAS------------------------------------
class RequerimientoForm(forms.ModelForm):
    class Meta:
        model = RequerimientoMateriale
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        data = self.data or self.initial

        # Inicial: mostrar todos
        self.fields["material"].queryset = Materiale.objects.all()
        self.fields["proveedor"].queryset = Proveedore.objects.all()

        # Filtrar proveedores si hay material
        if data.get("material"):
            material_id = data.get("material")
            self.fields["proveedor"].queryset = Proveedore.objects.filter(
                materialproveedore__material=material_id
            ).distinct()

        # Filtrar materiales si hay proveedor
        elif data.get("proveedor"):
            proveedor_id = data.get("proveedor")
            self.fields["material"].queryset = Materiale.objects.filter(
                materialproveedore__id_proveedor=proveedor_id
            ).distinct()

        # Cuando se edita registro existente
        if self.instance.pk:
            self.fields["proveedor"].queryset = Proveedore.objects.filter(
                materialproveedore__material=self.instance.material
            ).distinct()
            self.fields["material"].queryset = Materiale.objects.filter(
                materialproveedore__id_proveedor=self.instance.proveedor
            ).distinct()


class ListaCInline(admin.StackedInline):
    form = RequerimientoForm
    model = RequerimientoMateriale
    extra = 0
    
    class Media:
        js = ("js/filtro_material_proveedor.js", "js/requerimiento_precio.js",)
 


@admin.register(ListaCompra)
class ListaCompraAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    list_display = ("id", "fecha_solicitud", "prioridad", "estado")
    readonly_fields = ("fecha_solicitud",)
    list_filter = ('estado','prioridad',)
    inlines = [ListaCInline]

    # Vistas para filtrar
    def get_materiales_por_proveedor(self, request, proveedor_id):
        if proveedor_id == 0:
            materiales = Materiale.objects.all().values("id", "nombre")
        else:
            materiales = Materiale.objects.filter(
                materialproveedore__id_proveedor=proveedor_id
            ).values("id", "nombre")
        return JsonResponse(list(materiales), safe=False)

    def get_proveedores_por_material(self, request, material_id):
        if material_id == 0:
            proveedores = Proveedore.objects.all().values("id", "nombre")
        else:
            proveedores = Proveedore.objects.filter(
                materialproveedore__material=material_id
            ).values("id", "nombre")
        return JsonResponse(list(proveedores), safe=False)
    
    def obtener_precio_material(self, request, material_id, proveedor_id):
        try:
            material_id = int(material_id)
            proveedor_id = int(proveedor_id)
            rel = MaterialProveedore.objects.filter(
                material_id=material_id,
                id_proveedor_id=proveedor_id
            ).first()
            precio = rel.precio_actual if rel else 0
        except Exception as e:
            import traceback; traceback.print_exc()
            precio = 0
        return JsonResponse({"precio": precio})



    # Registrar URLs custom
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "filtrar_materiales/<int:proveedor_id>/",
                self.admin_site.admin_view(self.get_materiales_por_proveedor),
                name="lista_compra_filtrar_materiales",
            ),
            path(
                "filtrar_proveedores/<int:material_id>/",
                self.admin_site.admin_view(self.get_proveedores_por_material),
                name="lista_compra_filtrar_proveedores",
            ),
            path(
                "obtener_precio_material/<int:material_id>/<int:proveedor_id>/",
                self.admin_site.admin_view(self.obtener_precio_material),
                name="obtener_precio_material",
            ),
        ]
        return custom + urls