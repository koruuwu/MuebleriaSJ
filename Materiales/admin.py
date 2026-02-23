from urllib import request
from django.contrib import admin
from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import *
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import AdminConImagenMixin, PaginacionAdminMixin, UniqueFieldAdminMixin
from Compras.models import HistorialPrecio
from django.contrib import messages
#------------FORMULARIOS ARRIBA-SOFIA CASTRO----------------
class ImagenForm(ValidacionesBaseForm):
    archivo_temp = forms.FileField(required=False, label="Subir imagen")

    class Meta:
        model = None
        fields = "__all__"
        #exclude = ('descripcion',)#

        widgets = {
            'nombre': WidgetsRegulares.nombre("Ej: Lusiana Barrera Campos"),
        }


class MaterialeForm(ImagenForm):
    class Meta(ImagenForm.Meta):
        model = Materiale
        
        widgets = {
            'nombre': WidgetsRegulares.nombre("Ej: Madera"),
            'stock_minimo': WidgetsRegulares.numero(4, allow_zero=False, placeholder="Ej: 10"),
            'stock_maximo': WidgetsRegulares.numero(5, allow_zero=False, placeholder="Ej: 500"),            
        }

        labels = {
            'stock_minimo':"Stock Mínimo",
            'stock_maximo':"Stock Máximo",
            'categoria':"Categoría",
            'medida':"Unidad de Medida",
            }

    def clean_stock_minimo(self):
        numero = self.cleaned_data.get('stock_minimo')
        numero = self.validar_longitud(str(numero), "Stock minimo", min_len=1, max_len=4)
        return numero
    
    def clean_stock_maximo(self):
        numero = self.cleaned_data.get('stock_maximo')
        minimo = self.cleaned_data.get('stock_minimo')
        numero = self.validar_longitud(str(numero), "Stock maximo", min_len=1, max_len=5)
        if minimo in [None, ''] or numero in [None, '']:
            return numero  # Django marcará el campo como obligatorio en otro paso

        try:
            minimo = int(minimo)
            numero = int(numero)
        except ValueError:
            raise forms.ValidationError("Valores inválidos para stock.")

        if numero <= minimo:
            raise forms.ValidationError("El stock máximo debe ser mayor que el mínimo.")

        if numero > 99999:  # Ejemplo de límite máximo
            raise forms.ValidationError("Stock máximo demasiado alto.")

        return numero
    
    


class ProveForm(ValidacionesBaseForm):
    class Meta:
        model = Proveedore
        fields = "__all__"
        widgets = {
            'nombre': WidgetsRegulares.nombre("Ej: Lusiana Campos Berrillo"),
            'compañia': WidgetsRegulares.nombre("Ej: Maderas el Tropico SA"),
            'telefono': WidgetsRegulares.telefono(),
            'email': WidgetsRegulares.email(),   
        }
        labels = {
            'compañia': "Compañía",
            'telefono': "Teléfono",
        }
     
    def clean_compañia(self):
        valor = self.cleaned_data.get('compañia', '')
        return self.validar_campo_texto(valor, "La compañía", min_len=10, max_len=60)
    
class calificacionForm(ValidacionesBaseForm):
    class Meta:
        model = Calificacione
        fields = "__all__"
        widgets = {
            'comentarios':WidgetsRegulares.comentario(),
        }
        labels = {
            'comentarios': "Comentarios",
            'calificacion': "Calificación",
        }
 
class MaterialProveedorForm(ValidacionesBaseForm):
    class Meta:
        model = MaterialProveedore
        fields = "__all__"
        widgets = {
        'tiempo': WidgetsRegulares.numero(2, allow_zero=False, placeholder="Ej: 10"),
        'comentarios':WidgetsRegulares.comentario(),
        'precio_actual': WidgetsRegulares.precioWidget(7, allow_zero=False, placeholder="Ej: 150.00"),
        }
    
    def clean_tiempo(self):
        tiempo = self.cleaned_data.get('tiempo')
        return self.validar_longitud(str(tiempo), "tiempo", min_len=1, max_len=2)
    
class MedForm(ValidacionesBaseForm):
    class Meta:
        model = UnidadesMedida
        fields = "__all__"
        widgets = {
            'nombre': WidgetsRegulares.nombre("Ej: Centimetro"),
            'abreviatura': WidgetsRegulares.abreviacionMedida("Ej: Cm"),
        }
     
    def clean_abreviatura(self):#CLEAN SIEMPRE DEBE TENER EL MISMO NOMBRE QUE LOS VALORES-sofia castro
        valor = self.cleaned_data.get('abreviatura', '')
        return self.validar_campo_texto(valor, "La abreviatura", min_len=1, max_len=4)
    def clean_nombre(self):
        valor = self.cleaned_data.get('nombre', '')
        return self.validar_campo_texto(valor, "El nombre", min_len=4, max_len=10)
 
class CateForm(ValidacionesBaseForm):
    archivo_temp = forms.FileField(required=False, label="Subir imagen")
    class Meta:
        model = CategoriasMateriale
        fields = "__all__"
        widgets = {
            'nombre': WidgetsRegulares.nombre("Ej: Madera"),     
            'descripcion': WidgetsRegulares.comentario("Ej: Material base para un mueble"),
        }


#----------------ADMINS---------------------
    
@admin.register(Materiale)
class MaterialeAdmin(UniqueFieldAdminMixin,PaginacionAdminMixin, AdminConImagenMixin, admin.ModelAdmin):
    unique_fields = ['nombre']#Validador de valores repetidos
    form = MaterialeForm
    exclude = ('imagen','imagen_url',)
    list_display = ("nombre","categoria", "stock_minimo","stock_maximo", "vista_previa")
    list_filter = ('categoria','medida',)
    bucket_name="materiales"

    def delete_model(self, request, obj):
        nombre = str(obj)
        obj.delete()
        self.message_user(request, f"El material '{nombre}' ha sido eliminado correctamente.", level=messages.SUCCESS)

    def delete_queryset(self, request, queryset):
        nombres = ', '.join([str(obj) for obj in queryset])
        queryset.delete()
        self.message_user(request, f'Materiales "{nombres}" fueron eliminados con éxito.', level=messages.SUCCESS)

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)

        if request.method == 'POST' and obj:
            self.delete_model(request, obj)
            # Redirige a la lista de Materiales usando reverse
            url = reverse('admin:Materiales_materiale_changelist')
            return HttpResponseRedirect(url)

        return super().delete_view(request, object_id, extra_context)

    


@admin.register(CategoriasMateriale)
class CategoriasMaterialeAdmin(PaginacionAdminMixin, AdminConImagenMixin, admin.ModelAdmin):
    form = CateForm
    list_display = ("nombre", "descripcion", "vista_previa")
    bucket_name="materiales_cat"



@admin.register(UnidadesMedida)
class UnidadesMedidaAdmin(UniqueFieldAdminMixin,PaginacionAdminMixin,admin.ModelAdmin):
    form=MedForm
    unique_fields = ['nombre']
    list_display = ("nombre", "abreviatura")

class MaterialProveedorInline(admin.StackedInline):
    model = MaterialProveedore
    form=MaterialProveedorForm
    extra = 0  
    def has_add_permission(self, request, obj=None):
        return obj is not None  
    
class HistorialPInline(admin.TabularInline):
    model = HistorialPrecio
    extra = 0  
    def has_add_permission(self, request, obj=None):
        return False
    def has_change_permission(self, request, obj = ...):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


class CalificacionInline(admin.StackedInline):
    form = calificacionForm
    model = Calificacione
    extra = 0 
    can_delete = True

    def has_delete_permission(self, request, obj=None):
        return True
     
    def has_add_permission(self, request, obj=None):
        return obj is not None  
    
    class Media:
        js = ("js/calificacion_select_all.js",)


@admin.register(Proveedore)
class ProveedoreAdmin(PaginacionAdminMixin,admin.ModelAdmin):
    form= ProveForm
    list_display = ("compañia","nombre", "telefono", "estado")
    search_fields = ('nombre', 'compañia')
    list_filter = ('estado__tipo','materialproveedore__material')
    inlines=[MaterialProveedorInline, HistorialPInline, CalificacionInline]
    '''fieldsets = [
        ("Información General", {"fields": ("nombre", "telefono")}),
        ("Estado", {"fields": ("estado",)}),
    ]'''

    def delete_model(self, request, obj):
        nombre = str(obj)
        obj.delete()
        self.message_user(request, f"El proveedor '{nombre}' ha sido eliminado correctamente.", level=messages.SUCCESS)

    def delete_queryset(self, request, queryset):
        nombres = ', '.join([str(obj) for obj in queryset])
        queryset.delete()
        self.message_user(request, f'Los proveedores "{nombres}" fueron eliminados con éxito.', level=messages.SUCCESS)

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)

        if request.method == 'POST' and obj:
            self.delete_model(request, obj)
            
            url = reverse('admin:%s_%s_changelist' % (self.model._meta.app_label, self.model._meta.model_name))
            return HttpResponseRedirect(url)

        return super().delete_view(request, object_id, extra_context)
    
   




    