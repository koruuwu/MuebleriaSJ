from django.contrib import admin
from .models import *
from django.template.loader import render_to_string
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares
from proyecto.utils.admin_utils import  PaginacionAdminMixin, UniqueFieldAdminMixin
from datetime import timedelta
from django.urls import path
from django.http import JsonResponse
from django import forms
from django.utils import timezone
from Materiales.models import Materiale
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse

class InventarioForm(ValidacionesBaseForm):
    class Meta:
        fields = "__all__"
        model = InventarioMueble
        widgets = {
            'cantidad_disponible': WidgetsRegulares.numero(4, allow_zero=True, placeholder="Ej: 10"),
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


class InventarioMForm(ValidacionesBaseForm):
    class Meta:
        fields = "__all__"
        model = InventarioMateriale
        
    
    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad_disponible')
        material = cleaned_data.get('id_material')
        
        if cantidad is not None and material:
            # Validar que no exceda stock máximo si es necesario
            stock_maximo = material.stock_maximo
            if stock_maximo and cantidad > stock_maximo:
                self.add_error('cantidad_disponible', 
                             f'La cantidad no puede exceder el stock máximo de {stock_maximo}')
        
        return cleaned_data


@admin.register(InventarioMateriale)
class InventarioMaterialAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    form = InventarioMForm
    list_display = ("id_material", "cantidad_disponible", "estado", "ubicación", "stock_minimo_info")
    search_fields = ('id_material__nombre', 'ubicación__nombre')
    readonly_fields = ('ultima_entrada', 'ultima_salida')
    list_filter = ('estado', 'ubicación')
    
    def stock_minimo_info(self, obj):
        return f"Mín: {obj.id_material.stock_minimo}"
    stock_minimo_info.short_description = "Stock Mínimo"

    def obtener_info_material(self, request, material_id):
        try:
            material = Materiale.objects.get(id=material_id)
            return JsonResponse({
                'stock_minimo': material.stock_minimo,
                'stock_maximo': material.stock_maximo,
                'descontinuado': getattr(material, 'descontinuado', False),
                'nombre': material.nombre
            })
        except Materiale.DoesNotExist:
            return JsonResponse({'error': 'Material no encontrado'}, status=404)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "obtener_info_material/<int:material_id>/",
                self.admin_site.admin_view(self.obtener_info_material),
                name="inventario_obtener_info_material",
            ),
        ]
        return custom_urls + urls
    
    class Media:
        js = ("js/estado_inventario_material.js",)



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

        # Solo modificar si existen los campos
        if "material" in self.fields:
            self.fields["material"].queryset = Materiale.objects.all()
        if "proveedor" in self.fields:
            self.fields["proveedor"].queryset = Proveedore.objects.all()

        if data.get("material") and "proveedor" in self.fields:
            material_id = data.get("material")
            self.fields["proveedor"].queryset = Proveedore.objects.filter(
                materialproveedore__material=material_id
            ).distinct()

        elif data.get("proveedor") and "material" in self.fields:
            proveedor_id = data.get("proveedor")
            self.fields["material"].queryset = Materiale.objects.filter(
                materialproveedore__id_proveedor=proveedor_id
            ).distinct()

        # Cuando se edita registro existente
        if self.instance.pk:
            if "proveedor" in self.fields:
                self.fields["proveedor"].queryset = Proveedore.objects.filter(
                    materialproveedore__material=self.instance.material
                ).distinct()
            if "material" in self.fields:
                self.fields["material"].queryset = Materiale.objects.filter(
                    materialproveedore__id_proveedor=self.instance.proveedor
                ).distinct()

class ListaCInline(admin.StackedInline):
    form = RequerimientoForm
    model = RequerimientoMateriale
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        """
        Si la orden está completa, recibida o incompleta
        todos los campos del inline se vuelven de solo lectura.
        """
        if obj and obj.pk and obj.estado in ['completa', 'recibida', 'incompleta']:
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

    def has_add_permission(self, request, obj=None):
        """
        No permitir agregar nuevos materiales si la orden está
        completa, recibida o incompleta.
        """
        if obj and obj.pk and obj.estado in ['completa', 'recibida', 'incompleta']:
            return False
        return super().has_add_permission(request, obj)

    class Media:
        js = ("js/filtro_material_proveedor.js", "js/requerimiento_precio.js",)

    

 
class DetalleRecibCInline(admin.StackedInline):
    model = DetalleRecibido
    extra = 0
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['aporte'].initial = 0  # Siempre iniciar en 0
        return form

    def get_changeform_initial_data(self, request):
        data = super().get_changeform_initial_data(request)
        data['aporte'] = 0  # Forzar aporte = 0 después de guardar
        return data


    
    def has_add_permission(self, request, obj=None):
        # Solo permitir agregar si la orden existe y está marcada como 'recibida'
        if obj and obj.pk:
            return obj.estado == 'recibida'
        return False

    def get_readonly_fields(self, request, obj=None):
        # Si la orden está completa, todo es readonly
        if obj and obj.pk and obj.estado == 'completa':
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)
    
    class Media:
        js = (
            "js/filtrar_productos_por_orden.js",
            "js/estado_inventario_material.js",  # AGREGAR ESTE JS
        )

@admin.register(ListaCompra)
class ListaCompraAdmin(PaginacionAdminMixin, admin.ModelAdmin):
    list_display = ("id", "fecha_solicitud","fecha_entrega", "prioridad", "estado")
    readonly_fields = ("fecha_solicitud","fecha_entrega",)
    list_filter = ('estado','prioridad',)
    inlines = [ListaCInline, DetalleRecibCInline]
    change_form_template = "admin/lista_compra_change_form.html"

    def get_readonly_fields(self, request, obj=None):
        # Si la orden está completa, todos los campos del admin son readonly
        if obj and obj.pk and obj.estado not in ['pendiente', 'rechazada','aprobada' ]:
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)
    


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
            proveedores = Proveedore.objects.all().values("id", "compañia")
        else:
            proveedores = Proveedore.objects.filter(
                materialproveedore__material=material_id
            ).values("id", "compañia")
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
    
    def obtener_productos_por_lista(self, request, lista_id):
        """Obtener productos filtrados por lista de compra con cantidad necesaria"""
        try:
            # Obtener requerimientos con información de cantidad
            requerimientos = RequerimientoMateriale.objects.filter(
                id_lista_id=lista_id
            ).select_related('material')
            
            productos_data = []
            for req in requerimientos:
                productos_data.append({
                    'id': req.material.id,
                    'nombre': req.material.nombre,
                    'cantidad_necesaria': req.cantidad_necesaria,
                    'requerimiento_id': req.id  # Por si lo necesitas después
                })
            
            return JsonResponse(productos_data, safe=False)
        except Exception as e:
            print(f"Error en obtener_productos_por_lista: {e}")
            return JsonResponse([], safe=False)
    
 
    def imprimir_lista_compra(self, request, lista_id):
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import inch
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from datetime import datetime
        import os
        
        lista = self.get_object(request, lista_id)
        requerimientos = RequerimientoMateriale.objects.filter(id_lista=lista).select_related('material','proveedor')
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Lista_Compra_{lista.id}_{datetime.now().strftime("%Y%m%d")}.pdf"'
        
        # Crear el documento
        doc = SimpleDocTemplate(response, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            alignment=1  # Centrado
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.white,
            alignment=1
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#2c3e50'),
            alignment=0  # Izquierda
        )
        
        # Contenido
        story = []
        
        # Encabezado
        story.append(Paragraph("MUEBLERÍA SAN JOSÉ", title_style))
        story.append(Paragraph("LISTA DE COMPRA", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Información de la lista
        info_data = [
            [Paragraph("<b>N° Lista:</b>", normal_style), Paragraph(str(lista.id), normal_style),
            Paragraph("<b>Fecha Solicitud:</b>", normal_style), Paragraph(lista.fecha_solicitud.strftime("%d/%m/%Y"), normal_style)],
            [Paragraph("<b>Fecha Entrega:</b>", normal_style), Paragraph(lista.fecha_entrega.strftime("%d/%m/%Y") if lista.fecha_entrega else "No especificada", normal_style),
            Paragraph("<b>Prioridad:</b>", normal_style), Paragraph(lista.get_prioridad_display(), normal_style)],
            [Paragraph("<b>Estado:</b>", normal_style), Paragraph(lista.get_estado_display(), normal_style),
            Paragraph("<b>Generado:</b>", normal_style), Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), normal_style)]
        ]
        
        info_table = Table(info_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1.5*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecf0f1')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Tabla de materiales
        if requerimientos:
            # Encabezados de la tabla
            headers = ['Material', 'Proveedor', 'Cantidad', 'Precio', 'Subtotal']
            
            # Datos de la tabla
            table_data = [headers]
            
            for req in requerimientos:
                subtotal = req.precio_actual * req.cantidad_necesaria
                row = [
                    Paragraph(req.material.nombre, normal_style),
                    Paragraph(req.proveedor.compañia, normal_style),
                    Paragraph(f"L. {req.cantidad_necesaria:,.2f}", normal_style),
                    Paragraph(f"L. {req.precio_actual:,.2f}", normal_style),
                    Paragraph(f"L. {subtotal:,.2f}", normal_style)
                   
                ]
                table_data.append(row)
            

            total_cantidad = sum(req.cantidad_necesaria for req in requerimientos)
            total_general = sum(req.precio_actual * req.cantidad_necesaria for req in requerimientos)
            
            table_data.append([
                Paragraph("<b>TOTAL GENERAL</b>", normal_style),
                Paragraph("", normal_style),
                Paragraph(f"<b>{total_cantidad}</b>", normal_style),
                Paragraph("", normal_style),
                Paragraph(f"<b>L. {total_general:,.2f}</b>", normal_style)
            ])
            
            # Crear tabla
            materiales_table = Table(table_data, colWidths=[2*inch, 2*inch, 1*inch, 1*inch,2*inch])
            materiales_table.setStyle(TableStyle([
                # Estilo encabezados
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                
                # Estilo filas
                ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#f8f9fa')),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e9ecef')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Centrar cantidad
                ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Centrar unidad
                
                # Bordes
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#34495e')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                
                # Estilo total
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d4edda')),
                
                # Alineación y padding
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(materiales_table)
        else:
            story.append(Paragraph("<b>No hay materiales en esta lista de compra</b>", normal_style))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Notas
        notas = [
            "• Verificar disponibilidad con proveedores antes de realizar pedidos",
        ]
        
        for nota in notas:
            story.append(Paragraph(nota, ParagraphStyle(
                'NotaStyle',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#7f8c8d'),
                leftIndent=10
            )))
        
        # Generar PDF
        doc.build(story)
        
        return response


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
            path(
                "obtener_productos_por_lista/<int:lista_id>/",
                self.admin_site.admin_view(self.obtener_productos_por_lista),
                name="obtener_productos_por_lista",
            ),
            path(
                "obtener_productos_por_lista/<int:lista_id>/",
                self.admin_site.admin_view(self.obtener_productos_por_lista),
                name="obtener_productos_por_lista",
            ),
            path(
                '<int:lista_id>/imprimir/',
                self.admin_site.admin_view(self.imprimir_lista_compra),
                name='imprimir_lista_compra'
            ),
        ]
        return custom + urls