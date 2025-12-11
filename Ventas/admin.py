from django.contrib import admin, messages
from .models import *
from django.forms import ModelForm
from django import forms
from django.urls import path
from django.http import JsonResponse
from Sucursales.models import Cai
from Compras.models import Parametro, InventarioMueble, DetalleCotizaciones
from Muebles.models import Mueble
from django.core.exceptions import ValidationError
from proyecto.utils.validators_inventario import ValidacionInventarioMixin
from django.db import transaction
from django.utils import timezone
# Register your models here.
from django.utils import timezone
from Sucursales.models import Cai
from Compras.models import InventarioMueble
from proyecto.utils.validators import ValidacionesBaseForm
from proyecto.utils.widgets import WidgetsRegulares

def obtener_cai_valido(sucursal):
    hoy = timezone.now().date()

    with transaction.atomic():
        cais = Cai.objects.select_for_update().filter(sucursal=sucursal)

        cais_validos = []

        for cai in cais:
            valido = True

            # Validar fecha
            if cai.fecha_vencimiento and cai.fecha_vencimiento < hoy:
                valido = False

            # Validar rango
            try:
                ultima = int(cai.ultima_secuencia or "0")
                final = int(cai.rango_final or "0")
                if ultima >= final:
                    valido = False
            except:
                valido = False

            # Apagar inválidos
            if not valido:
                if cai.activo:
                    cai.activo = False
                    cai.save(update_fields=['activo'])
            else:
                cais_validos.append(cai)

        if not cais_validos:
            return None

        # ✅ PERMITIR LOS QUE VENCEN HOY
        candidatos = [
            c for c in cais_validos
            if c.fecha_vencimiento and c.fecha_vencimiento >= hoy
        ]

        if not candidatos:
            return None

        ganador = sorted(candidatos, key=lambda x: x.fecha_vencimiento)[0]

        Cai.objects.filter(sucursal=sucursal).update(activo=False)
        ganador.activo = True
        ganador.save(update_fields=['activo'])

        return ganador


def validar_stock_mueble(mueble, cantidad, sucursal):
    """
    Retorna mensaje de error si no hay stock suficiente.
    """
    inventario = InventarioMueble.objects.filter(
        id_mueble=mueble,
        ubicación=sucursal,
        estado__id__in=[1, 2]
    ).first()
    if not inventario:
        return f"No hay inventario para {mueble.nombre} en {sucursal}"
    elif inventario.cantidad_disponible < cantidad:
        return f"Stock insuficiente para {mueble.nombre}. Disponible: {inventario.cantidad_disponible}, solicitado: {cantidad}"
    return None


def validar_rtn_cliente(usuariofinal, cliente):
    """
    Retorna mensaje de error si el cliente no cumple con RTN.
    """
    if usuariofinal:
        if cliente is None:
            return "Debe seleccionar un cliente para poder usar RTN final."
        elif not cliente.rtn:
            return "El cliente no tiene RTN configurado, debe asignarle un RTN en su ficha antes de continuar."
    return None


class OrdenForm(ValidacionesBaseForm):
    aporte = forms.FloatField(initial=0, required=False, label="Aporte", widget=WidgetsRegulares.precio(10, False, "Ej: 20,000"))

    class Meta:
        model = OrdenesVenta
        fields = "__all__"
        widgets = {
            'descuento': WidgetsRegulares.numero(3, False, "Ej: 10"),
            'efectivo': WidgetsRegulares.precio(10, False, "Ej: 20,000"),
            'num_tarjeta': WidgetsRegulares.tarjeta(4, placeholder="Ej: 9876"),
        }

    def clean(self):
        cleaned_data = super().clean()
        errores = []

        perfil = PerfilUsuario.objects.filter(user=getattr(self, "current_user", None)).first()
        if not perfil or not perfil.sucursal or not perfil.caja:
            errores.append("El usuario no tiene sucursal o caja configurada.")

        # Validación RTN / Cliente
        usuariofinal = cleaned_data.get("rtn")
        cliente = cleaned_data.get("id_cliente")
        error_rtn = validar_rtn_cliente(usuariofinal, cliente)
        if error_rtn:
            errores.append(error_rtn)

        # Validación efectivo (mínimo por parámetro y que no exceda el total)
        total = cleaned_data.get("total") or 0
        efectivo = cleaned_data.get("efectivo")
        if efectivo not in (None, ""):
            # normalizar a float con manejo de errores
            try:
                efectivo_float = float(efectivo)
            except (ValueError, TypeError):
                errores.append("El valor de efectivo no es válido.")
                efectivo_float = None

            # validación mínimo (si existe parámetro)
            if efectivo_float is not None:
                try:
                    parametro_efectivo = Parametro.objects.get(id=4)
                    porcentaje_min = float(parametro_efectivo.valor)
                except Parametro.DoesNotExist:
                    porcentaje_min = None
                except (ValueError, TypeError):
                    porcentaje_min = None

                if porcentaje_min is not None and total > 0:
                    minimo_requerido = total * (porcentaje_min / 100)
                    if efectivo_float < minimo_requerido:
                        errores.append(
                            f"El efectivo ingresado ({efectivo_float}) es menor al mínimo requerido ({minimo_requerido:.2f}) según el porcentaje {porcentaje_min}%."
                        )

                # validación máximo: efectivo no puede ser mayor que el total
                if total is not None and efectivo_float > float(total):
                    errores.append(
                        f"El efectivo ingresado ({efectivo_float}) no puede exceder el total ({float(total):.2f})."
                    )


        # Validación descuento máximo
        descuento = cleaned_data.get("descuento") or 0
        try:
            parametro_des = Parametro.objects.get(id=3)
            descuento_max = float(parametro_des.valor)
        except Parametro.DoesNotExist:
            descuento_max = None

        if descuento_max is not None and float(descuento) > descuento_max:
            errores.append(f"El descuento máximo que se puede aplicar es del {descuento_max}%.")

        # Validación CAI
        if perfil:
            cai = obtener_cai_valido(perfil.sucursal)
            if not cai:
                errores.append("No hay CAI válido configurado para esta sucursal.")

        if errores:
            raise ValidationError(errores)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        aporte = self.cleaned_data.get('aporte', 0) or 0
        if aporte:
            instance.pagado = (instance.pagado or 0) + aporte

        try:
            estado_pagado = EstadoPagos.objects.get(nombre__iexact="Pagado")
            estado_pendiente = EstadoPagos.objects.get(nombre__iexact="Pendiente")
        except EstadoPagos.DoesNotExist:
            estado_pagado = estado_pendiente = None

        if instance.total and instance.pagado:
            if instance.pagado >= instance.total and estado_pagado:
                instance.id_estado_pago = estado_pagado
            elif estado_pendiente:
                instance.id_estado_pago = estado_pendiente

        if commit:
            instance.save()

        return instance






    
from django.forms import BaseInlineFormSet, ValidationError
from Compras.models import InventarioMueble
from Empleados.models import PerfilUsuario

from django.forms import BaseInlineFormSet, ValidationError
from Compras.models import InventarioMueble
from Empleados.models import PerfilUsuario

class DetallesOrdenFormSet(BaseInlineFormSet):

    

    def clean(self):
        super().clean()
        request = self.request
        perfil = PerfilUsuario.objects.filter(user=request.user).first()
        sucursal = getattr(perfil, "sucursal", None)

        if not sucursal:
            raise ValidationError("El usuario no tiene sucursal asignada.")

        errores = []

        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue

            mueble = form.cleaned_data.get("id_mueble")
            cantidad = form.cleaned_data.get("cantidad")

            if not mueble or not cantidad:
                continue

            inventario = InventarioMueble.objects.filter(
                id_mueble=mueble,
                ubicación=sucursal,
                estado__id__in=[1, 2]
            ).first()

            if not inventario:
                errores.append(f"No hay inventario para {mueble.nombre} en {sucursal}")
            elif inventario.cantidad_disponible < cantidad:
                errores.append(
                    f"Stock insuficiente para {mueble.nombre}. "
                    f"Disponible: {inventario.cantidad_disponible}, solicitado: {cantidad}"
                )

        if errores:
            raise ValidationError(errores)


class DetallesOrdeneForm(forms.ModelForm):
    class Meta:
        model = DetallesOrdene
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad')

        if cantidad is not None and cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a 0.'})

        return cleaned_data


class DetallesOInline(admin.StackedInline):
    model = DetallesOrdene
    form = DetallesOrdeneForm
    extra = 0
    formset = DetallesOrdenFormSet

    def has_add_permission(self, request, obj):
        if obj:  # Si la orden ya existe, no permitir agregar
            return False
        return super().has_add_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        if obj:  # Si la orden ya existe, no permitir borrar detalles
            return False
        return super().has_delete_permission(request, obj)
    
    def has_change_permission(self, request, obj=None):
        if obj:  # Si la orden ya existe, no permitir borrar detalles
            return False
        return super().has_change_permission(request, obj)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.request = request
        return formset
    
    

    
    class Media:
        js = ('js/detalle_orden.js',)
 

@admin.register(OrdenesVenta)
class OrdenesVentasAdmin(ValidacionInventarioMixin, admin.ModelAdmin):
    form = OrdenForm
    inlines = [DetallesOInline]
    change_form_template = "admin/orden_venta_change_form.html"


    def get_readonly_fields(self, request, obj=None):
        # Si el objeto ya existe (está guardado), hacer todos los campos readonly
        if obj:  # obj existe cuando se está editando, no cuando se está creando
            return [field.name for field in obj._meta.fields]
        return self.readonly_fields
    

    def _process_inline_errors(self, request, formsets):
        """
        Toma los errores de los formsets e imprime mensajes arriba del form.
        """
        for formset in formsets:
            if hasattr(formset, "non_form_errors"):
                for err in formset.non_form_errors():
                    messages.error(request, err)

            # Errores por formulario (línea) dentro del inline
            for form in formset.forms:
                if form.errors:
                    for field, errors in form.errors.items():
                        for err in errors:
                            messages.error(
                                request,
                                f"Error en Detalle de Orden ({field}): {err}"
                            )

    def add_view(self, request, form_url='', extra_context=None):
        response = super().add_view(request, form_url, extra_context)

        if request.method == "POST" and hasattr(response, "context_data"):
            formsets = response.context_data.get("inline_admin_formsets", [])
            self._process_inline_errors(request, [fs.formset for fs in formsets])

        return response

    def change_view(self, request, object_id, form_url='', extra_context=None):
        response = super().change_view(request, object_id, form_url, extra_context)

        if request.method == "POST" and hasattr(response, "context_data"):
            formsets = response.context_data.get("inline_admin_formsets", [])
            self._process_inline_errors(request, [fs.formset for fs in formsets])

        return response


    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.current_user = request.user

        if 'aporte' in form.base_fields:
            form.base_fields['aporte'].initial = 0

        if 'descuento' in form.base_fields:
            try:
                parametro_des = Parametro.objects.get(id=3)
                form.base_fields['descuento'].help_text = (
                    f"El descuento máximo actual es de {parametro_des.valor}%."
                )
            except Parametro.DoesNotExist:
                form.base_fields['descuento'].help_text = "No se encontró el parámetro de descuento."

        return form


    def get_changeform_initial_data(self, request):
        data = super().get_changeform_initial_data(request)

        # Valor por defecto que ya tenías
        data['aporte'] = 0

        # Precargar desde cotización si viene desde el botón
        cotizacion_id = request.GET.get('cotizacion_id')
        if cotizacion_id:
            from Compras.models import Cotizacione

            try:
                cot = Cotizacione.objects.get(pk=cotizacion_id)
            except Cotizacione.DoesNotExist:
                return data

            data.update({
                'id_cotizacion': cot,
                'id_cliente': cot.cliente,
                'subtotal': cot.subtotal,
                'isv': cot.isv,
                'total': cot.total,
            })

        return data

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        self.actualizar_inventario(form.instance, request)



    class Media:
        js = ("js/ordenes_venta_aporte.js","js/generacion_c/factura_dinamica.js","js/generacion_c/orden_desde_cotizacion.js")
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("obtener_precio_mueble/<int:mueble_id>/", self.admin_site.admin_view(self.obtener_precio_mueble)),
            path("obtener_empleado_logeado/", 
            self.admin_site.admin_view(self.obtener_empleado_logeado),
            name="obtener-empleado-logeado"),
            path(
                "<int:orden_id>/imprimir/",
                self.admin_site.admin_view(self.imprimir_factura),
                name="imprimir_factura"
            ),
            path(
                'detalles-cotizacion/<int:cotizacion_id>/',
                self.admin_site.admin_view(self.detalles_cotizacion_json),
                name='detalles-cotizacion-json'
            ),
            
        ]
        return custom + urls
    
    
    def detalles_cotizacion_json(self, request, cotizacion_id):
            detalles = DetalleCotizaciones.objects.filter(id_cotizacion_id=cotizacion_id)
            data = [
                {
                    'mueble': d.id_mueble_id,
                    'precio': d.precio_unitario,
                    'cantidad': d.cantidad,
                    'subtotal': d.subtotal,
                }
                for d in detalles
            ]
            return JsonResponse(data, safe=False)

    def save_model(self, request, obj, form, change):
        perfil = PerfilUsuario.objects.filter(user=request.user).first()

        with transaction.atomic():

            if not change:
                parametro = Parametro.objects.get(id=2)
                cai = obtener_cai_valido(perfil.sucursal)

                if not cai:
                    raise ValidationError("No hay CAI activo válido para esta sucursal.")

                siguiente = int(cai.ultima_secuencia or "0") + 1

                obj.id_factura = (
                    f"{perfil.sucursal.codigo_sucursal}-"
                    f"{perfil.caja.codigo_caja}-"
                    f"{parametro.valor}-"
                    f"{str(siguiente).zfill(8)}"
                )

                obj.cai_usado = cai

                cai.ultima_secuencia = str(siguiente).zfill(8)

                # ✅ GUARDAR SIEMPRE LA ORDEN ANTES DE TOCAR INLINES
                super().save_model(request, obj, form, change)

                # ✅ AHORA ya existe el id_orden y es seguro guardar detalles
                if siguiente >= int(cai.rango_final):
                    cai.activo = False
                    cai.save(update_fields=['ultima_secuencia', 'activo'])

                    messages.warning(
                        request,
                        f"El CAI {cai.codigo_cai} alcanzó su rango final y fue desactivado."
                    )

                    nuevo_cai = obtener_cai_valido(perfil.sucursal)

                    if nuevo_cai:
                        messages.success(
                            request,
                            f"Nuevo CAI activado automáticamente: {nuevo_cai.codigo_cai}"
                        )
                    else:
                        messages.error(
                            request,
                            "No hay un nuevo CAI disponible para activar."
                        )

                else:
                    cai.save(update_fields=['ultima_secuencia'])

            else:
                # Si es edición normal
                super().save_model(request, obj, form, change)






    def obtener_empleado_logeado(self, request):
        perfil = PerfilUsuario.objects.filter(user=request.user).first()
        return JsonResponse({
            "id_empleado": perfil.id if perfil else None
        })
    
    def obtener_precio_mueble(self, request, mueble_id):
        try:
            mueble = Mueble.objects.get(id=mueble_id)
            return JsonResponse({"precio": mueble.precio_base})
        except Mueble.DoesNotExist:
            return JsonResponse({"precio": 0})





    def imprimir_factura(self, request, orden_id):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle,
            Paragraph, Spacer, PageTemplate, Frame
        )
        from reportlab.lib.units import inch
        from django.http import HttpResponse
        from datetime import datetime
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        # ----------------------------
        # OBTENCIÓN DE DATOS
        # ----------------------------
        orden = OrdenesVenta.objects.select_related(
            "id_cliente", "id_empleado"
        ).get(id=orden_id)

        detalles = (
            DetallesOrdene.objects.filter(id_orden=orden)
            .select_related("id_mueble")
        )

        perfil = PerfilUsuario.objects.filter(user=request.user).first()
        cai = orden.cai_usado
        sucursal = None
        if perfil and hasattr(perfil, 'sucursal'):
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
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            f'inline; filename="Factura_{orden.id_factura}.pdf"'
        )

        # Crear el documento
        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
        )

        styles = getSampleStyleSheet()

        # Estilos profesionales en B/N (mantener igual)
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
        # ENCABEZADO PROFESIONAL (mantener igual)
        # -----------------------------------------------------------
        story.append(Paragraph("MUEBLERIA SAN JOSE", title_style))
        story.append(Spacer(1, 0.05 * inch))
        story.append(Paragraph("Factura", company_style))
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
        # NÚMERO DE FACTURA DESTACADO (mantener igual)
        # -----------------------------------------------------------
        tabla_factura = Table(
            [[Paragraph("<b>FACTURA No.</b>", label_style), 
            Paragraph(f"<b>{orden.id_factura}</b>", label_style)]],
            colWidths=[1.5 * inch, 6 * inch]
        )
        tabla_factura.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 11)
        ]))
        story.append(tabla_factura)
        story.append(Spacer(1, 0.2 * inch))

        # -----------------------------------------------------------
        # INFORMACIÓN SAR (mantener igual)
        # -----------------------------------------------------------
        info_sar = [
            [Paragraph("<b>CAI Autorizado:</b>", label_style), 
            Paragraph(cai.codigo_cai, data_style)],
            [Paragraph("<b>Rango Autorizado:</b>", label_style), 
            Paragraph(f"{cai.rango_inicial} - {cai.rango_final}", data_style)],
            [Paragraph("<b>Emisión CAI:</b>", label_style), 
            Paragraph(cai.fecha_emision.strftime("%d/%m/%Y"), data_style)],
            [Paragraph("<b>Vencimiento:</b>", label_style), 
            Paragraph(cai.fecha_vencimiento.strftime("%d/%m/%Y"), data_style)],
            [Paragraph("<b>Fecha de Factura:</b>", label_style), 
            Paragraph(orden.fecha_orden.strftime("%d/%m/%Y %H:%M"), data_style)],
        ]

        tabla_sar = Table(info_sar, colWidths=[2 * inch, 5.5 * inch])
        tabla_sar.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.9)),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(tabla_sar)
        story.append(Spacer(1, 0.25 * inch))

        # -----------------------------------------------------------
        # INFORMACIÓN DEL CLIENTE Y VENTA (mantener igual)
        # -----------------------------------------------------------
        cliente = orden.id_cliente
        efectivo = orden.efectivo or 0
        total = orden.total or 0
        metodo = orden.id_metodo_pago
        
        if metodo and (metodo != 2 and metodo != 4):
            tarjeta = 0
        else:
            tarjeta = (total - efectivo)

        usuariofinal=orden.rtn
        if usuariofinal == True:
            eretene=cliente.rtn
        else:
            eretene="CF"

        datos_cliente = [
            [Paragraph("<b>DATOS DEL CLIENTE</b>", label_style), ""],
            [Paragraph("<b>Nombre:</b>", label_style), 
            Paragraph(cliente.nombre, data_style)],
            [Paragraph("<b>RTN:</b>", label_style), 
            Paragraph(eretene or "No registrado", data_style)],
            [Paragraph("<b>Teléfono:</b>", label_style), 
            Paragraph(cliente.telefono or "No registrado", data_style)],
            [Paragraph("<b>Dirección:</b>", label_style), 
            Paragraph(cliente.direccion or "No registrada", data_style)],
        ]

        datos_venta = [
            [Paragraph("<b>DATOS DE VENTA</b>", label_style), ""],
            [Paragraph("<b>Método de Pago:</b>", label_style), 
            Paragraph(str(orden.id_metodo_pago), data_style)],
            [Paragraph("<b>Efectivo:</b>", label_style), 
            Paragraph(f"L. {efectivo:,.2f}", data_style)],
            [Paragraph("<b>Tarjeta:</b>", label_style), 
            Paragraph(f"L. {tarjeta:,.2f}", data_style)],
            [Paragraph("<b>Últimos 4 dígitos:</b>", label_style), 
            Paragraph(orden.num_tarjeta or "----", data_style)],
            [Paragraph("<b>Atendido por:</b>", label_style), 
            Paragraph(str(orden.id_empleado) if orden.id_empleado else "No registrado", data_style)],
        ]

        tabla_cliente = Table(datos_cliente, colWidths=[1.3 * inch, 2.4 * inch])
        tabla_cliente.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('SPAN', (0, 0), (1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        tabla_venta = Table(datos_venta, colWidths=[1.5 * inch, 2.1 * inch])
        tabla_venta.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('SPAN', (0, 0), (1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        contenedor_doble = Table(
            [[tabla_cliente, tabla_venta]],
            colWidths=[3.8 * inch, 3.7 * inch]
        )
        contenedor_doble.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
            ('RIGHTPADDING', (1, 0), (1, -1), 0),
        ]))

        story.append(contenedor_doble)
        story.append(Spacer(1, 0.25 * inch))

        # -----------------------------------------------------------
        # TABLA DE PRODUCTOS (mantener igual)
        # -----------------------------------------------------------
        filas = [
            [Paragraph("<b>Cant.</b>", label_style),
            Paragraph("<b>Descripción</b>", label_style),
            Paragraph("<b>Precio Unit.</b>", label_style),
            Paragraph("<b>Subtotal</b>", label_style)]
        ]

        for det in detalles:
            subtotal = det.cantidad * det.precio_unitario
            filas.append([
                Paragraph(str(det.cantidad), data_style),
                Paragraph(f"{det.id_mueble.nombre}", data_style),
                Paragraph(f"L. {det.precio_unitario:,.2f}", data_style),
                Paragraph(f"L. {subtotal:,.2f}", data_style)
            ])

        tabla_prod = Table(
            filas, colWidths=[0.8 * inch, 3.5 * inch, 1.6 * inch, 1.6 * inch]
        )
        tabla_prod.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
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
        # TOTALES (mantener igual)
        # -----------------------------------------------------------
        totales = [
            [Paragraph("<b>Subtotal:</b>", label_style), 
            Paragraph(f"L. {(orden.subtotal or 0):,.2f}", data_style)],
            [Paragraph("<b>ISV 15%:</b>", label_style), 
            Paragraph(f"L. {(orden.isv or 0):,.2f}", data_style)],
            [Paragraph("<b>Descuento:</b>", label_style), 
            Paragraph(f"L. {(orden.descuento or 0):,.2f}", data_style)],
            [Paragraph("<b>TOTAL A PAGAR:</b>", label_style), 
            Paragraph(f"<b>L. {(orden.total or 0):,.2f}</b>", label_style)],
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
        # PIE DE PÁGINA (mantener igual)
        # -----------------------------------------------------------
        story.append(Spacer(1, 0.1 * inch))
        
        pie_texto = """
        <b>CONDICIONES GENERALES:</b><br/>
        • Este documento es válido según normativa SAR de Honduras.<br/>
        • No se aceptan devoluciones sin factura original.<br/>
        • Revisar mercancía antes de retirarla.<br/>
        • Gracias por su compra.
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
        # FUNCIÓN PARA NUMERACIÓN DE PÁGINAS
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



    list_display=('id_factura', 'id_cliente', 'total', 'id_estado_pago', 'fecha_entrega')
    readonly_fields = ('fecha_orden','id_factura','cai_usado',)
    fieldsets = [
        ("General", {"fields": ("id_factura", "id_cotizacion","id_empleado","id_cliente","rtn","descuento","subtotal","isv","total","fecha_entrega","fecha_orden")}),
        ("Pago", {"fields": ("cuotas","aporte", "pagado","id_estado_pago","id_metodo_pago","efectivo","num_tarjeta")}),
    ]

    from reportlab.pdfgen.canvas import Canvas




        
    

    




