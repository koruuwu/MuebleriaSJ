# proyecto/admin_utils.py
from math import ceil
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

from django import forms
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.utils.html import format_html
from proyecto.supabase_client import subir_archivo

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.urls import path
from django.http import HttpResponse
from django.utils import timezone

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

class ExportReportMixin:
    """
    Mixin genérico para exportar PDF/Excel desde cualquier ModelAdmin.
    Usa list_display por defecto. Se puede personalizar con:

    - export_report_name      -> título del reporte
    - export_filename_base    -> prefijo del archivo
    - export_columns          -> tupla/lista de nombres de campos a usar
    - export_exclude_fields   -> campos de list_display a excluir
    - export_rows_per_page    -> filas por página en PDF
    """

    export_report_name = "Reporte"
    export_filename_base = "reporte"
    export_rows_per_page = 35
    export_exclude_fields = ("vista_previa",)  # ejemplo, se puede override
    export_pdf_column_widths = None

    change_list_template = "admin/change_list_export.html"

    def get_urls(self):
        """
        Añade las URLs /export/pdf/ y /export/excel/ para este ModelAdmin.
        """
        urls = super().get_urls()
        # app_label y model_name para no repetir nombres
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name

        custom = [
            path(
                "export/pdf/",
                self.admin_site.admin_view(self.export_pdf),
                name=f"{app_label}_{model_name}_export_pdf",
            ),
            path(
                "export/excel/",
                self.admin_site.admin_view(self.export_excel),
                name=f"{app_label}_{model_name}_export_excel",
            ),
        ]
        return custom + urls

    # ---------- Helpers comunes ----------
    def _get_changelist_queryset(self, request):
        """
        Devuelve el queryset tal como aparece en el changelist:
        respeta búsqueda, filtros, orden, etc.
        """
        cl = self.get_changelist_instance(request)
        return cl.get_queryset(request)
    
    def _get_export_columns(self):
        """
        Devuelve la lista de 'column keys' que usaremos para el reporte.
        Prioridad:
        1) self.export_fields (si existe)
        2) self.list_display
        3) todos los campos del modelo
        Aplicando export_exclude_fields.
        """
        # 1) export_fields explícitos en el admin (si los defines)
        if hasattr(self, "export_fields") and self.export_fields:
            cols = list(self.export_fields)
        # 2) list_display del admin
        elif getattr(self, "list_display", None):
            cols = [c for c in self.list_display if c != "action_checkbox"]
        # 3) todos los campos del modelo
        else:
            cols = [f.name for f in self.model._meta.fields]

        excl = getattr(self, "export_exclude_fields", ())
        cols = [c for c in cols if c not in excl]
        return cols

    def _export_get_value(self, obj, field_name):
        """
        Obtiene el valor de una 'columna' para un objeto:
        - Si el admin tiene un método con ese nombre -> lo llama con obj.
        - Si el modelo tiene atributo/propiedad -> lo usa (si es callable, lo llama).
        """
        # método definido en el ModelAdmin (por ejemplo total_pedidos, vista_previa, etc.)
        if hasattr(self, field_name):
            admin_attr = getattr(self, field_name)
            if callable(admin_attr):
                return admin_attr(obj)

        # atributo / propiedad del modelo
        attr = getattr(obj, field_name, "")
        if callable(attr):
            return attr()
        return attr

    def _wrap_text(self, text, max_width, font_name="Helvetica", font_size=10):
        """
        Divide 'text' en varias líneas para que cada línea no sobrepase max_width.
        Devuelve una lista de líneas.
        """
        if text is None:
            return [""]

        text = str(text)
        words = text.split()
        if not words:
            return [""]

        lines = []
        current = ""

        for word in words:
            candidate = word if not current else current + " " + word
            if stringWidth(candidate, font_name, font_size) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                # Si la palabra sola ya es muy ancha, la partimos “a lo bruto”.
                if stringWidth(word, font_name, font_size) <= max_width:
                    current = word
                else:
                    fragment = ""
                    for ch in word:
                        cand = fragment + ch
                        if stringWidth(cand, font_name, font_size) <= max_width:
                            fragment = cand
                        else:
                            if fragment:
                                lines.append(fragment)
                            fragment = ch
                    current = fragment

        if current:
            lines.append(current)

        return lines or [""]

    def get_export_queryset(self, request):
        # Usa el mismo queryset que ve el usuario en el changelist
        cl = self.get_changelist_instance(request)
        return cl.get_queryset(request)

    def get_export_columns(self, request):
        """
        Devuelve la lista de nombres de campos / métodos a exportar.
        Por defecto: list_display sin 'action_checkbox' ni los de export_exclude_fields.
        Si el admin define export_columns, se usa eso.
        """
        if hasattr(self, "export_columns"):
            return list(self.export_columns)

        cols = []
        for name in self.get_list_display(request):
            if name == "action_checkbox":
                continue
            if name in getattr(self, "export_exclude_fields", ()):
                continue
            cols.append(name)
        return cols

    def get_export_headers(self, request, columns):
        """
        Devuelve los encabezados "bonitos" para cada columna.
        Intenta usar verbose_name o short_description.
        """
        headers = []
        for name in columns:
            # 1. Campo de modelo
            try:
                field = self.model._meta.get_field(name)
                headers.append(str(field.verbose_name).title())
                continue
            except Exception:
                pass

            # 2. Método en el admin o en el modelo con short_description
            attr = getattr(self, name, None) or getattr(self.model, name, None)
            label = getattr(attr, "short_description", None) if attr else None
            if label:
                headers.append(str(label))
            else:
                # 3. Fallback
                headers.append(name.replace("_", " ").title())
        return headers

    def get_export_row(self, obj, columns):
        """
        Devuelve una lista con los valores de cada columna para un registro.
        """
        data = []
        for name in columns:
            value = getattr(obj, name, "")
            if callable(value):
                try:
                    value = value()
                except TypeError:
                    # por si requiere argumentos, ignoramos
                    pass
            if value is None:
                value = ""
            data.append(str(value))
        return data

    # ---------- PDF ----------

        
    def export_pdf(self, request):
        qs = self._get_changelist_queryset(request)

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{self.export_filename_base}.pdf"'

        c = canvas.Canvas(response, pagesize=letter)
        page_width, page_height = letter

        empresa = "Mueblería San José"
        reporte = getattr(self, "export_report_name", "Reporte")
        usuario = request.user.get_username()
        ahora = timezone.localtime()

        # Márgenes y layout
        left_margin = 40
        right_margin = 40
        bottom_margin = 60
        table_header_height = 15
        top_header_y = page_height - 50
        table_top_y = page_height - 110
        bottom_limit_y = bottom_margin + 20
        line_height = 14

        total_width = page_width - left_margin - right_margin

        # ----- Columnas -----
        columns = self._get_export_columns()
        num_cols = len(columns)

        if self.export_pdf_column_widths and len(self.export_pdf_column_widths) == num_cols:
            col_widths = self.export_pdf_column_widths
        else:
            col_width = total_width / max(num_cols, 1)
            col_widths = [col_width] * num_cols

        col_x = [left_margin]
        for w_col in col_widths[:-1]:
            col_x.append(col_x[-1] + w_col)

        # ----- Encabezado y pie -----
        def header():
            c.setFont("Helvetica-Bold", 14)
            c.drawString(left_margin, top_header_y, empresa)

            c.setFont("Helvetica", 12)
            c.drawString(left_margin, top_header_y - 20, reporte)

            c.line(left_margin, table_top_y - 5, page_width - right_margin, table_top_y - 5)

        def footer(page_num, total_pages):
            c.line(left_margin, 60, page_width - right_margin, 60)
            c.setFont("Helvetica", 9)
            c.drawString(left_margin, 45, f"Usuario: {usuario}")
            c.drawString(left_margin + 160, 45, f"Fecha y hora: {ahora.strftime('%Y-%m-%d %H:%M:%S')}")
            texto_pagina = f"Página {page_num} de {total_pages or 1}"
            c.drawRightString(page_width - right_margin, 45, texto_pagina)

        # Y de inicio de datos (parte superior de la primera fila)
        data_top_y = table_top_y - table_header_height

        # ---------- 1) SIMULACIÓN para saber cuántas páginas habrá ----------
        page_count = 1
        y_sim = data_top_y

        for obj in qs:
            max_lines = 1
            for idx, field_name in enumerate(columns):
                value = self._export_get_value(obj, field_name)
                lines = self._wrap_text(
                    value,
                    max_width=col_widths[idx] - 4,
                    font_name="Helvetica",
                    font_size=10,
                )
                max_lines = max(max_lines, len(lines))

            row_height = max_lines * line_height
            if y_sim - row_height < bottom_limit_y:
                page_count += 1
                y_sim = data_top_y

            y_sim -= row_height

        total_pages = max(page_count, 1)

        # ---------- 2) DIBUJO real ----------
        page_num = 1
        header()

        # Encabezado de columnas
        c.setFont("Helvetica-Bold", 10)
        header_y = table_top_y
        for i, col in enumerate(columns):
            titulo = col.replace("_", " ").title()
            c.drawString(col_x[i], header_y, titulo)
        c.setFont("Helvetica", 10)

        y = data_top_y  # parte superior de la primera fila
        row_index = 0   # para zebra

        for obj in qs:
            # Valores de la fila según columnas
            values = self.get_export_row(obj, columns)

            # Envolver texto por columna
            col_lines = []
            max_lines_in_row = 1
            for value, max_w in zip(values, col_widths):
                text = "" if value is None else str(value)
                lines = self._wrap_text(text, max_w - 4)
                if not lines:
                    lines = [""]
                col_lines.append(lines)
                max_lines_in_row = max(max_lines_in_row, len(lines))

            row_height = max_lines_in_row * line_height

            # ¿Cabe la fila completa? Si no, salto de página
            if y - row_height < bottom_limit_y:
                footer(page_num, total_pages)
                c.showPage()
                page_num += 1
                header()

                # reimprimir encabezado de columnas en la nueva página
                c.setFont("Helvetica-Bold", 10)
                header_y = table_top_y
                for i, col in enumerate(columns):
                    titulo = col.replace("_", " ").title()
                    c.drawString(col_x[i], header_y, titulo)
                c.setFont("Helvetica", 10)

                y = data_top_y  # reset parte superior de filas

            row_top = y
            row_bottom = y - row_height

            # Fondo “zebra” para la fila completa
            if row_index % 2 == 0:
                c.setFillColor(colors.whitesmoke)
                c.rect(
                    left_margin,
                    row_bottom,
                    total_width,
                    row_height,
                    stroke=0,
                    fill=1,
                )
                c.setFillColor(colors.black)

            # Texto de la fila, línea por línea
            for line_idx in range(max_lines_in_row):
                text_y = row_top - (line_idx + 1) * line_height + 3  # +3 = pequeño padding
                for col_idx, lines in enumerate(col_lines):
                    if line_idx < len(lines):
                        c.drawString(
                            col_x[col_idx],
                            text_y,
                            lines[line_idx],
                        )

            y = row_bottom
            row_index += 1

        footer(page_num, total_pages)
        c.save()
        return response

    # ---------- Export Excel ----------

    def export_excel(self, request):
        qs = self._get_changelist_queryset(request)
        columns = self._get_export_columns()
        headers = self.get_export_headers(request, columns)

        wb = Workbook()
        ws = wb.active
        ws.title = str(self.export_report_name)[:31]

        empresa = getattr(self, "export_company_name", "Mueblería San José")
        reporte = getattr(self, "export_report_name", "Reporte")
        usuario = request.user.get_username()
        ahora = timezone.localtime().strftime("%Y-%m-%d %H:%M:%S")

        ws["A1"] = empresa
        ws["A2"] = reporte
        ws["A3"] = f"Usuario: {usuario}"
        ws["A4"] = f"Fecha y hora: {ahora}"

        start_row = 6
        for col, h in enumerate(headers, start=1):
            ws.cell(row=start_row, column=col, value=h)

        row = start_row + 1
        for obj in qs:
            values = self.get_export_row(obj, columns)
            for col, val in enumerate(values, start=1):
                ws.cell(row=row, column=col, value=val)
            row += 1

        for i in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(i)].width = 22

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename_base = getattr(self, "export_filename_base", "reporte")
        filename = f"{filename_base}_reporte.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

class PaginacionAdminMixin:

    actions = ["set_pagination_1", "set_pagination_10", "set_pagination_25", "set_pagination_50", "set_pagination_100"]

    def set_pagination_1(self, request, queryset):
        request.session['per_page'] = 1
        self.message_user(request, "Mostrando 1 elementos por página.")
    set_pagination_1.short_description = "Mostrar 1 por página"

    def set_pagination_10(self, request, queryset):
        request.session['per_page'] = 10
        self.message_user(request, "Mostrando 10 elementos por página.")
    set_pagination_10.short_description = "Mostrar 10 por página"

    def set_pagination_25(self, request, queryset):
        request.session['per_page'] = 25
        self.message_user(request, "Mostrando 25 elementos por página.")
    set_pagination_25.short_description = "Mostrar 25 por página"

    def set_pagination_50(self, request, queryset):
        request.session['per_page'] = 50
        self.message_user(request, "Mostrando 50 elementos por página.")
    set_pagination_50.short_description = "Mostrar 50 por página"

    def set_pagination_100(self, request, queryset):
        request.session['per_page'] = 100
        self.message_user(request, "Mostrando 100 elementos por página.")
    set_pagination_100.short_description = "Mostrar 100 por página"

    def changelist_view(self, request, extra_context=None):
        if 'per_page' in request.session:
            self.list_per_page = request.session['per_page']
        else:
            self.list_per_page = 10
        return super().changelist_view(request, extra_context=extra_context)





class AdminConImagenMixin:
    readonly_fields = ("vista_previa", "imagen_url", "imagen")
    bucket_name = "default"  # Cada admin puede sobrescribir este valor

    def save_model(self, request, obj, form, change):
        archivo = form.cleaned_data.get("archivo_temp")
        if archivo:
            ruta, url = subir_archivo(archivo, self.bucket_name)
            obj.imagen = ruta
            obj.imagen_url = url
        super().save_model(request, obj, form, change)

    def vista_previa(self, obj):
        if getattr(obj, "imagen_url", None):
            return format_html(
                '<img src="{}" style="max-height:100px;border-radius:8px;" />',
                obj.imagen_url,
            )
        return "Sin imagen"
    vista_previa.short_description = "Vista previa"



from django.contrib import admin
from django.core.exceptions import ValidationError

class UniqueFieldAdminMixin:
    """
    Mixin para ModelAdmin que valida campos únicos antes de guardar,
    sin necesidad de definir un ModelForm.
    """
    
    # Campo único o lista de campos únicos a validar
    unique_fields = []  # ['tipo_documento'] o ['campo1', 'campo2']

    def get_form(self, request, obj=None, **kwargs):
        """
        Inyecta dinámicamente la validación de duplicados en el form que genera el admin.
        """
        form = super().get_form(request, obj, **kwargs)

        unique_fields = self.unique_fields  # lista de campos a validar

        class _FormWithUniqueValidation(form):
            def clean(self_inner):
                cleaned_data = super(_FormWithUniqueValidation, self_inner).clean()
                for field in unique_fields:
                    valor = cleaned_data.get(field)
                    if valor is None:
                        continue
                    qs = self_inner._meta.model.objects.exclude(pk=self_inner.instance.pk)
                    if qs.filter(**{field: valor}).exists():
                        raise ValidationError({field: f'⚠️ El valor "{valor}" ya existe.'})
                return cleaned_data

        return _FormWithUniqueValidation


