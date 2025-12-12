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
from Notificaciones.utils.notificacio_reutilizable import crear_notificacion
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from Empleados.models import PerfilUsuario




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
            'cantidad': WidgetsRegulares.numero(3, False, "Ej: 10"),
        }


@admin.register(InventarioMueble)
class InventarioMuebleAdmin(PaginacionAdminMixin,admin.ModelAdmin):
    form = InventarioForm
    list_display = ("id_mueble","cantidad_disponible", "estado", "ubicación")
    search_fields = ('id_mueble', 'ubicación')
    readonly_fields=('ultima_entrada', 'ultima_salida')
    list_filter = ('estado','ubicación')
    class Media:
        js = ("js/estados/estado_inventario_mueble.js",)

    def obtener_info_mueble(self, request, mueble_id):
        try:
            mueble = Mueble.objects.get(id=mueble_id)
            inventario = InventarioMueble.objects.get(id_mueble=mueble)
            return JsonResponse({
                'cantidad_disponible': inventario.cantidad_disponible,
                'estado': inventario.estado.id,
                'ultima_entrada': inventario.ultima_entrada,
                'ultima_salida': inventario.ultima_salida,
                'nombre_mueble': mueble.nombre,
                'stock_minimo': mueble.stock_minimo,
                'stock_maximo': mueble.stock_maximo,
            })
        except InventarioMueble.DoesNotExist:
            return JsonResponse({'error': 'Inventario no encontrado'}, status=404)
        except Mueble.DoesNotExist:
            return JsonResponse({'error': 'Mueble no encontrado'}, status=404)

    # Agregar URL custom
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "obtener_info_mueble/<int:mueble_id>/",
                self.admin_site.admin_view(self.obtener_info_mueble),
                name="inventario_obtener_info_mueble",
            ),
        ]
        return custom_urls + urls


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
    list_display = ("id_material", "cantidad_disponible","cantidad_reservada", "estado", "ubicación", "stock_minimo_info")
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
    
    def save_model(self, request, obj, form, change):
            print(">>> Entró al save_model de InventarioMaterialAdmin")

            super().save_model(request, obj, form, change)

            try:
                print(">>> Intentando generar notificación...")
                stock_minimo = obj.id_material.stock_minimo
                actual = obj.cantidad_disponible
                print("Actual:", actual, " Mínimo:", stock_minimo)
   
                stock_minimo = obj.id_material.stock_minimo
                actual = obj.cantidad_disponible

                if actual <= stock_minimo:
                    if actual == 0:
                        mensaje = (
                        f"Stock agotado para el material: {obj.id_material.nombre}. "
                        )
                    else:
                    
                        mensaje = (
                            f"Stock bajo para el material: {obj.id_material.nombre}. "
                            f"Actual: {actual} | Mínimo: {stock_minimo}"
                        )

                    # Aquí creas la notificación
                    crear_notificacion(
                        tipo="alerta",
                        mensaje=mensaje,
                        objeto=obj
                    )
            except Exception as e:
                print("ERROR generando notificación:", e)


    class Media:
        js = ("js/estado_inventario_material.js",)



class DetalleCotizacionesInline(admin.StackedInline):
    model = DetalleCotizaciones
    form=CotizacioneForm
    extra = 0

    class Media:
        js = ('js/detalle_cotizacion.js',)

    
from django.urls import reverse
from django.utils.html import format_html
@admin.register(Cotizacione)
class CotizacioneAdmin(PaginacionAdminMixin,admin.ModelAdmin):
    form = CotizacioneForm
    list_display = ("cliente", "fecha_registro", "activo", "fecha_vencimiento", "convertir_a_orden")
    search_fields = ('cliente',)
    readonly_fields=("fecha_registro","fecha_vencimiento")
    list_filter = ('activo',)
    change_form_template = "admin/cotizacion_change_form.html"
    inlines = [DetalleCotizacionesInline]

    
    def convertir_a_orden(self, obj):
        url = (
            reverse('admin:Ventas_ordenesventa_add')
            + f'?cotizacion_id={obj.id}'
        )
        return format_html(
            '<a class="button" href="{}">Convertir a Orden</a>',
            url
        )

    convertir_a_orden.short_description = "Orden de Venta"
  
    
  
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
            path(
                "<int:cotizacion_id>/imprimir-cotizacion/",
                self.admin_site.admin_view(self.imprimir_cotizacion),
                name="imprimir_cotizacion"
            ),
        ]
        return custom + urls
    
    def imprimir_cotizacion(self, request, cotizacion_id):
        # imports locales
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
        from django.shortcuts import get_object_or_404
        from django.http import HttpResponse

        # ----------------------------
        # OBTENCIÓN DE DATOS
        # ----------------------------
        cotizacion = get_object_or_404(
            Cotizacione.objects.select_related("cliente"),
            id=cotizacion_id
        )

        detalles = DetalleCotizaciones.objects.filter(id_cotizacion=cotizacion).select_related("id_mueble")

        perfil = PerfilUsuario.objects.filter(user=request.user).first()
        sucursal = None
        if perfil and hasattr(perfil, "sucursal"):
            sucursal = perfil.sucursal

        sucursal_info = ""
        if sucursal:
            sucursal_info = (
                f"R.T.N. No {sucursal.rtn}<br/>"
                f"{sucursal.nombre}<br/>"
                f"{sucursal.direccion}<br/>"
                f"Tel. (504) {sucursal.telefono or 'No registrado'}"
            )
        else:
            sucursal_info = "Sucursal no registrada"

        # ----------------------------
        # PDF RESPONSE
        # ----------------------------
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="Cotizacion_{cotizacion.id}.pdf"'

        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
        )

        styles = getSampleStyleSheet()

        # Estilos profesionales en B/N (mismo estilo que factura)
        title_style = ParagraphStyle(
            'title_style',
            parent=styles['Heading1'],
            alignment=1,
            fontSize=20,
            textColor=colors.black,
            spaceAfter=4,
            fontName='Helvetica-Bold',
            letterSpacing=2
        )

        company_style = ParagraphStyle(
            'company_style',
            parent=styles['Normal'],
            alignment=1,
            fontSize=14,
            textColor=colors.black,
            spaceAfter=2,
            fontName='Helvetica-Bold'
        )

        info_style = ParagraphStyle(
            'info_style',
            parent=styles['Normal'],
            alignment=1,
            fontSize=9,
            textColor=colors.black,
            leading=11
        )

        label_style = ParagraphStyle(
            'label_style',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )

        data_style = ParagraphStyle(
            'data_style',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black
        )

        small_style = ParagraphStyle(
            'small_style',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.black,
            leading=10
        )

        story = []

        # -----------------------------------------------------------
        # ENCABEZADO PROFESIONAL
        # -----------------------------------------------------------
        story.append(Paragraph("COTIZACIÓN", title_style))
        story.append(Spacer(1, 0.05 * inch))
        story.append(Paragraph("Mueblería San José", company_style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(sucursal_info, info_style))
        
        story.append(Spacer(1, 0.15 * inch))
        
        # Línea separadora
        linea = Table([[""]], colWidths=[7.5 * inch])
        linea.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.black),
        ]))
        story.append(linea)
        story.append(Spacer(1, 0.15 * inch))

        # -----------------------------------------------------------
        # NÚMERO DE COTIZACIÓN DESTACADO
        # -----------------------------------------------------------
        tabla_num = Table(
            [[Paragraph("<b>COTIZACIÓN No.</b>", label_style), 
            Paragraph(f"<b>{cotizacion.id}</b>", label_style)]],
            colWidths=[1.5 * inch, 6 * inch]
        )
        tabla_num.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 11)
        ]))
        story.append(tabla_num)
        story.append(Spacer(1, 0.2 * inch))

        # -----------------------------------------------------------
        # INFORMACIÓN DE FECHAS
        # -----------------------------------------------------------
        info_dates = [
            [Paragraph("<b>Fecha de Cotización:</b>", label_style), 
            Paragraph(cotizacion.fecha_registro.strftime("%d/%m/%Y %H:%M"), data_style)],
            [Paragraph("<b>Fecha de Vencimiento:</b>", label_style), 
            Paragraph(cotizacion.fecha_vencimiento.strftime("%d/%m/%Y") if cotizacion.fecha_vencimiento else "No aplica", data_style)],
        ]

        tabla_dates = Table(info_dates, colWidths=[2 * inch, 5.5 * inch])
        tabla_dates.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.9)),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(tabla_dates)
        story.append(Spacer(1, 0.25 * inch))

        # -----------------------------------------------------------
        # INFORMACIÓN DEL CLIENTE
        # -----------------------------------------------------------
        cliente = cotizacion.cliente
        
        datos_cliente = [
            [Paragraph("<b>DATOS DEL CLIENTE</b>", label_style), ""],
            [Paragraph("<b>Nombre:</b>", label_style), 
            Paragraph(cliente.nombre if cliente else "No registrado", data_style)],
            [Paragraph("<b>RTN:</b>", label_style), 
            Paragraph(cliente.rtn or "No registrado", data_style)],
            [Paragraph("<b>Teléfono:</b>", label_style), 
            Paragraph(cliente.telefono or "No registrado", data_style)],
            [Paragraph("<b>Dirección:</b>", label_style), 
            Paragraph(cliente.direccion or "No registrada", data_style)],
        ]

        tabla_cliente = Table(datos_cliente, colWidths=[1.3 * inch, 6.2 * inch])
        tabla_cliente.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('SPAN', (0, 0), (1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(tabla_cliente)
        story.append(Spacer(1, 0.25 * inch))

        # -----------------------------------------------------------
        # TABLA DE PRODUCTOS
        # -----------------------------------------------------------
        filas = [
            [Paragraph("<b>Cant.</b>", label_style),
            Paragraph("<b>Descripción</b>", label_style),
            Paragraph("<b>Precio Unit.</b>", label_style),
            Paragraph("<b>Subtotal</b>", label_style)]
        ]

        for det in detalles:
            try:
                subtotal = float(det.subtotal)
            except Exception:
                subtotal = (det.cantidad or 0) * (det.precio_unitario or 0)

            filas.append([
                Paragraph(str(det.cantidad), data_style),
                Paragraph(f"{det.id_mueble.nombre if det.id_mueble else 'Sin descripción'}", data_style),
                Paragraph(f"L. {float(det.precio_unitario or 0):,.2f}", data_style),
                Paragraph(f"L. {subtotal:,.2f}", data_style)
            ])

        tabla_prod = Table(
            filas, colWidths=[0.8 * inch, 3.5 * inch, 1.6 * inch, 1.6 * inch]
        )
        tabla_prod.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
        ]))

        story.append(tabla_prod)
        story.append(Spacer(1, 0.25 * inch))

        # -----------------------------------------------------------
        # TOTALES
        # -----------------------------------------------------------
        totales = [
            [Paragraph("<b>Subtotal:</b>", label_style), 
            Paragraph(f"L. {(cotizacion.subtotal or 0):,.2f}", data_style)],
            [Paragraph("<b>ISV 15%:</b>", label_style), 
            Paragraph(f"L. {(cotizacion.isv or 0):,.2f}", data_style)],
            [Paragraph("<b>TOTAL:</b>", label_style), 
            Paragraph(f"<b>L. {(cotizacion.total or 0):,.2f}</b>", label_style)],
        ]

        tabla_tot = Table(totales, colWidths=[5.5 * inch, 2 * inch])
        tabla_tot.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
            ('INNERGRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.black),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('FONTSIZE', (0, -1), (-1, -1), 11)
        ]))

        story.append(tabla_tot)
        story.append(Spacer(1, 0.3 * inch))

        # -----------------------------------------------------------
        # PIE DE PÁGINA
        # -----------------------------------------------------------
        story.append(Spacer(1, 0.1 * inch))
        
        pie_texto = """
        <b>CONDICIONES GENERALES:</b><br/>
        • Esta cotización es válida por el periodo indicado.<br/>
        • Revisar mercancía antes de retirarla.<br/>
        • Gracias por su preferencia.
        """
        
        story.append(Paragraph(pie_texto, small_style))
        
        # Línea final
        story.append(Spacer(1, 0.15 * inch))
        linea_final = Table([[""]], colWidths=[7.5 * inch])
        linea_final.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
        ]))
        story.append(linea_final)

        # -----------------------------------------------------------
        # NUMERACIÓN Y LOGO EN PIE
        # -----------------------------------------------------------
        class PageNumCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                canvas.Canvas.__init__(self, *args, **kwargs)
                self.pages = []

            def showPage(self):
                self.pages.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                page_count = len(self.pages)
                for page in self.pages:
                    self.__dict__.update(page)
                    self.draw_page_number(page_count)
                    canvas.Canvas.showPage(self)
                canvas.Canvas.save(self)

            def draw_page_number(self, page_count):
                page = f"Página {self._pageNumber} de {page_count}"
                self.setFont("Helvetica", 9)
                self.drawRightString(7.8 * inch, 0.4 * inch, page)

                # logo en esquina inferior izquierda
                try:
                    from reportlab.lib.utils import ImageReader
                    logo_path = "static/img/logo.png"
                    width = 90
                    height = 90
                    x = 0.5 * inch
                    y = 0.2 * inch
                    self.saveState()
                    try:
                        self.setFillAlpha(0.50)
                        self.setStrokeAlpha(0.20)
                    except Exception:
                        pass
                    self.drawImage(
                        ImageReader(logo_path),
                        x, y,
                        width=width,
                        height=height,
                        preserveAspectRatio=True,
                        mask="auto"
                    )
                    self.restoreState()
                except Exception as e:
                    print("Error cargando logo:", e)

        # Construir documento con numeración
        doc.build(story, canvasmaker=PageNumCanvas)
        return response



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
    
    def clean(self):
        cleaned_data = super().clean()
        material = cleaned_data.get('material')
        proveedor = cleaned_data.get('proveedor')
        cantidad = cleaned_data.get('cantidad_necesaria')  # o como lo llames

        if material and proveedor and cantidad:
            rel = MaterialProveedore.objects.filter(
                material=material,
                id_proveedor=proveedor
            ).first()
            precio = rel.precio_actual if rel else 0

            # Validación de cantidad, stock, etc.
            stock_maximo = material.stock_maximo
            if stock_maximo and cantidad > stock_maximo:
                self.add_error('cantidad_necesaria',
                            f'La cantidad no puede exceder el stock máximo de {stock_maximo}')

            # Guardar precio en el cleaned_data si quieres usarlo después
            cleaned_data['precio_actual'] = precio

        return cleaned_data
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
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import inch
        from django.http import HttpResponse
        from datetime import datetime
        
        lista = self.get_object(request, lista_id)
        requerimientos = RequerimientoMateriale.objects.filter(id_lista=lista).select_related('material', 'proveedor')
        
        # ----------------------------
        # PDF RESPONSE
        # ----------------------------
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Lista_Compra_{lista.id}_{datetime.now().strftime("%Y%m%d")}.pdf"'
        
        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
        )
        
        styles = getSampleStyleSheet()
        
        # Estilos profesionales en B/N (mismo estilo que factura)
        title_style = ParagraphStyle(
            'title_style',
            parent=styles['Heading1'],
            alignment=1,
            fontSize=20,
            textColor=colors.black,
            spaceAfter=4,
            fontName='Helvetica-Bold',
            letterSpacing=2
        )
        
        company_style = ParagraphStyle(
            'company_style',
            parent=styles['Normal'],
            alignment=1,
            fontSize=14,
            textColor=colors.black,
            spaceAfter=2,
            fontName='Helvetica-Bold'
        )
        
        info_style = ParagraphStyle(
            'info_style',
            parent=styles['Normal'],
            alignment=1,
            fontSize=9,
            textColor=colors.black,
            leading=11
        )
        
        label_style = ParagraphStyle(
            'label_style',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        data_style = ParagraphStyle(
            'data_style',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black
        )
        
        small_style = ParagraphStyle(
            'small_style',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.black,
            leading=10
        )
        
        story = []
        
        # -----------------------------------------------------------
        # ENCABEZADO PROFESIONAL
        # -----------------------------------------------------------
        story.append(Paragraph("LISTA DE COMPRA", title_style))
        story.append(Spacer(1, 0.05 * inch))
        story.append(Paragraph("Mueblería San José", company_style))
        story.append(Spacer(1, 0.15 * inch))
        
        # Línea separadora
        linea = Table([[""]], colWidths=[7.5 * inch])
        linea.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.black),
        ]))
        story.append(linea)
        story.append(Spacer(1, 0.15 * inch))
        
        # -----------------------------------------------------------
        # NÚMERO DE LISTA DESTACADO
        # -----------------------------------------------------------
        tabla_num = Table(
            [[Paragraph("<b>LISTA DE COMPRA No.</b>", label_style), 
            Paragraph(f"<b>{lista.id}</b>", label_style)]],
            colWidths=[2 * inch, 5.5 * inch]
        )
        tabla_num.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 11)
        ]))
        story.append(tabla_num)
        story.append(Spacer(1, 0.2 * inch))
        
        # -----------------------------------------------------------
        # INFORMACIÓN DE LA LISTA
        # -----------------------------------------------------------
        info_data = [
            [Paragraph("<b>Fecha Solicitud:</b>", label_style), 
            Paragraph(lista.fecha_solicitud.strftime("%d/%m/%Y"), data_style)],
            [Paragraph("<b>Fecha Entrega:</b>", label_style), 
            Paragraph(lista.fecha_entrega.strftime("%d/%m/%Y") if lista.fecha_entrega else "No especificada", data_style)],
            [Paragraph("<b>Prioridad:</b>", label_style), 
            Paragraph(lista.get_prioridad_display(), data_style)],
            [Paragraph("<b>Estado:</b>", label_style), 
            Paragraph(lista.get_estado_display(), data_style)],
            [Paragraph("<b>Fecha de Generación:</b>", label_style), 
            Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), data_style)],
        ]
        
        tabla_info = Table(info_data, colWidths=[2 * inch, 5.5 * inch])
        tabla_info.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.9)),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(tabla_info)
        story.append(Spacer(1, 0.25 * inch))
        
        # -----------------------------------------------------------
        # TABLA DE MATERIALES
        # -----------------------------------------------------------
        if requerimientos:
            filas = [
                [Paragraph("<b>Material</b>", label_style),
                Paragraph("<b>Proveedor</b>", label_style),
                Paragraph("<b>Cantidad</b>", label_style),
                Paragraph("<b>Precio Unit.</b>", label_style),
                Paragraph("<b>Subtotal</b>", label_style)]
            ]
            
            for req in requerimientos:
                subtotal = req.precio_actual * req.cantidad_necesaria
                filas.append([
                    Paragraph(req.material.nombre, data_style),
                    Paragraph(req.proveedor.compañia, data_style),
                    Paragraph(f"{req.cantidad_necesaria:,.2f}", data_style),
                    Paragraph(f"L. {req.precio_actual:,.2f}", data_style),
                    Paragraph(f"L. {subtotal:,.2f}", data_style)
                ])
            
            materiales_table = Table(
                filas, colWidths=[2.2 * inch, 2 * inch, 1 * inch, 1.3 * inch, 1 * inch]
            )
            materiales_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ]))
            
            story.append(materiales_table)
            story.append(Spacer(1, 0.25 * inch))
            
            # -----------------------------------------------------------
            # TOTALES
            # -----------------------------------------------------------
            total_cantidad = sum(req.cantidad_necesaria for req in requerimientos)
            total_general = sum(req.precio_actual * req.cantidad_necesaria for req in requerimientos)
            
            totales = [
                [Paragraph("<b>Total Cantidad:</b>", label_style), 
                Paragraph(f"{total_cantidad:,.2f}", data_style)],
                [Paragraph("<b>TOTAL GENERAL:</b>", label_style), 
                Paragraph(f"<b>L. {total_general:,.2f}</b>", label_style)],
            ]
            
            tabla_tot = Table(totales, colWidths=[5.5 * inch, 2 * inch])
            tabla_tot.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
                ('INNERGRID', (0, 0), (-1, -2), 0.5, colors.grey),
                ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.black),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('FONTSIZE', (0, -1), (-1, -1), 11)
            ]))
            
            story.append(tabla_tot)
        else:
            story.append(Paragraph("<b>No hay materiales en esta lista de compra</b>", data_style))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # -----------------------------------------------------------
        # PIE DE PÁGINA
        # -----------------------------------------------------------
        story.append(Spacer(1, 0.1 * inch))
        
        pie_texto = """
        <b>NOTAS IMPORTANTES:</b><br/>
        • Verificar disponibilidad con proveedores antes de realizar pedidos.<br/>
        • Confirmar precios actualizados al momento de la compra.<br/>
        • Revisar calidad y especificaciones de los materiales.<br/>
        • Conservar este documento como respaldo de la solicitud.
        """
        
        story.append(Paragraph(pie_texto, small_style))
        
        # Línea final
        story.append(Spacer(1, 0.15 * inch))
        linea_final = Table([[""]], colWidths=[7.5 * inch])
        linea_final.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
        ]))
        story.append(linea_final)
        class PageNumCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                canvas.Canvas.__init__(self, *args, **kwargs)
                self.pages = []
                
            def showPage(self):
                self.pages.append(dict(self.__dict__))
                self._startPage()
                
            def save(self):
                page_count = len(self.pages)
                
                for page in self.pages:
                    self.__dict__.update(page)
                    self.draw_page_number(page_count)
                    canvas.Canvas.showPage(self)
                    
                canvas.Canvas.save(self)
            
            def draw_page_number(self, page_count):
                page = f"Página {self._pageNumber} de {page_count}"

                # Número de página en esquina inferior derecha
                self.setFont("Helvetica", 9)
                self.drawRightString(
                    7.8 * inch,
                    0.4 * inch,
                    page
                )

                # ---------------------------------------------
                #   LOGO EN ESQUINA INFERIOR IZQUIERDA
                # ---------------------------------------------
                try:
                    from reportlab.lib.utils import ImageReader

                    logo_path = "static/img/logo.png"  # <--- CAMBIA ESTA RUTA

                    # Tamaño pequeño (ajusta a gusto)
                    width = 90
                    height = 90

                    # Posición (muy abajo, esquina izquierda)
                    x = 0.5 * inch
                    y = 0.2 * inch

                    # Guardar estado gráfico
                    self.saveState()

                    # Opacidad (0.0 = invisible, 1.0 = normal)
                    self.setFillAlpha(0.50)
                    self.setStrokeAlpha(0.20)

                    # Dibujar imagen
                    self.drawImage(
                        ImageReader(logo_path),
                        x, y,
                        width=width,
                        height=height,
                        preserveAspectRatio=True,
                        mask='auto'
                    )

                    # Restaurar estado
                    self.restoreState()

                except Exception as e:
                    print("Error cargando logo:", e)


        # Construir PDF con numeración de páginas
        doc.build(
            story,
            canvasmaker=PageNumCanvas  # Usar nuestro canvas personalizado
        )
        
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