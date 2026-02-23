from django.test import TestCase
from django.urls import reverse
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test.client import Client as DjangoClient
from django.db.models.signals import post_save

from clientes.admin import ClienteForm, DocumentosClienteForm, DocumentosClienteInline
from clientes.models import Cliente, DocumentosCliente

# Documento viene de archivos.models
from archivos.models import Documento


def _dummy_value_for_field(field):
    """
    Genera valores dummy para crear instancias sin conocer el schema exacto.
    Esto hace los tests más resistentes si tu modelo Documento tiene más campos obligatorios.
    """
    from django.db import models

    # Si tiene choices, usa el primero
    if getattr(field, "choices", None):
        try:
            return list(field.choices)[0][0]
        except Exception:
            pass

    # Tipos comunes
    if isinstance(field, (models.CharField, models.TextField, models.SlugField, models.EmailField, models.URLField)):
        max_len = getattr(field, "max_length", None) or 50
        base = f"test_{field.name}"
        return (base[: max_len]).ljust(min(max_len, 10), "x")

    if isinstance(field, (models.IntegerField, models.BigIntegerField, models.SmallIntegerField, models.PositiveIntegerField)):
        return 1

    if isinstance(field, (models.FloatField,)):
        return 1.0

    if isinstance(field, (models.DecimalField,)):
        # decimal simple dentro de max_digits/decimal_places
        return 1

    if isinstance(field, (models.BooleanField,)):
        return True

    if isinstance(field, (models.DateField,)):
        from datetime import date
        return date.today()

    if isinstance(field, (models.DateTimeField,)):
        from django.utils import timezone
        return timezone.now()

    if isinstance(field, (models.TimeField,)):
        from datetime import time
        return time(12, 0)

    # ForeignKey: debe resolverse fuera de aquí
    return None


def create_minimal_instance(model_class, **overrides):
    """
    Crea y guarda una instancia con los mínimos campos obligatorios,
    rellenando con valores dummy cualquier campo requerido.

    - Soporta FK creando dependencias si hace falta.
    - Ignora M2M (no suelen ser obligatorios para guardar).
    """
    from django.db import models

    kwargs = {}

    for field in model_class._meta.fields:
        # Saltar PK autogenerada
        if field.primary_key:
            continue

        # Si viene override, úsalo
        if field.name in overrides:
            kwargs[field.name] = overrides[field.name]
            continue

        # Si permite null/blank o tiene default, no es obligatorio
        has_default = field.has_default() or field.default is not models.NOT_PROVIDED
        if field.null or getattr(field, "blank", False) or has_default:
            # si tiene default, no hace falta asignar
            continue

        # FK obligatoria
        if isinstance(field, models.ForeignKey):
            rel_model = field.remote_field.model
            # Evitar recursión rara
            if rel_model == model_class:
                continue
            kwargs[field.name] = create_minimal_instance(rel_model)
            continue

        # Campo normal obligatorio
        dummy = _dummy_value_for_field(field)
        if dummy is not None:
            kwargs[field.name] = dummy

    # aplicar overrides que no eran fields directos (por si acaso)
    kwargs.update(overrides)

    obj = model_class.objects.create(**kwargs)
    return obj


class ClientesIntegracionTest(TestCase):
    """
    Integración real:
    - valida forms
    - valida model.clean / full_clean al guardar
    - valida admin urls (delete / changelist / add)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # --- Defensivo: desconectar signal que crea PerfilUsuario si existe ---
        # Esto evita el error que tuviste: column "user" of relation "PerfilUsuario" does not exist
        try:
            from Empleados.models import crear_perfil_usuario  # según tu traceback anterior
            User = get_user_model()
            post_save.disconnect(crear_perfil_usuario, sender=User)
        except Exception:
            # Si no existe ese signal o ese import, no pasa nada
            pass

    def setUp(self):
        # Crear superuser para probar Admin con client
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(
            username="admin_test",
            password="admin12345",
            email="admin@test.com"
        )
        self.client = DjangoClient()
        self.client.force_login(self.admin_user)

        # Crear datos base para Cliente y Documento
        self.cliente = create_minimal_instance(
            Cliente,
            nombre="Cliente Prueba",
            telefono="99999999",
            direccion="Direccion X",
            rtn="08011999123456"[:14],  # 14 dígitos
        )

        # Documento puede tener más campos obligatorios; el helper los rellena
        # Solo forzamos tipo_documento si existe.
        try:
            self.documento = create_minimal_instance(Documento, tipo_documento="RTN")
        except TypeError:
            # Si Documento no tiene tipo_documento, lo creamos sin ese override
            self.documento = create_minimal_instance(Documento)

    # -------------------------
    # 1) Integración: ClienteForm
    # -------------------------
    def test_cliente_form_rtn_valido(self):
        data = {
            "nombre": "Juan Perez",
            "telefono": "99999999",
            "direccion": "Calle 1",
            "rtn": "08011999123456",  # 14 dígitos, solo números
        }
        form = ClienteForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_cliente_form_rtn_no_numerico_invalido(self):
        data = {
            "nombre": "Juan Perez",
            "telefono": "99999999",
            "direccion": "Calle 1",
            "rtn": "0801ABC9123456",  # contiene letras
        }
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("rtn", form.errors)

    def test_cliente_form_rtn_longitud_invalida(self):
        data = {
            "nombre": "Juan Perez",
            "telefono": "99999999",
            "direccion": "Calle 1",
            "rtn": "123",  # no tiene 14
        }
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("rtn", form.errors)

    # -----------------------------------
    # 2) Integración: DocumentosClienteForm (admin form)
    #    Valida duplicado cliente+documento+valor
    # -----------------------------------
    def test_documentos_cliente_form_no_permite_duplicado_mismo_cliente_doc_valor(self):
        # Crear uno existente
        existente = DocumentosCliente.objects.create(
            id_cliente=self.cliente,
            id_documento=self.documento,
            valor="ABC-123"
        )

        data = {
            "id_cliente": self.cliente.id,
            "id_documento": self.documento.id,
            "valor": "ABC-123"
        }
        form = DocumentosClienteForm(data=data)
        self.assertFalse(form.is_valid())
        # El error puede venir como non_field_errors por ValidationError en clean()
        self.assertTrue(form.errors, "Se esperaba error de validación por duplicado")

    def test_documentos_cliente_form_permita_mismo_cliente_doc_distinto_valor(self):
        DocumentosCliente.objects.create(
            id_cliente=self.cliente,
            id_documento=self.documento,
            valor="ABC-123"
        )

        data = {
            "id_cliente": self.cliente.id,
            "id_documento": self.documento.id,
            "valor": "XYZ-999"
        }
        form = DocumentosClienteForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    # -----------------------------------
    # 3) Integración: Model clean/save (full_clean)
    #    OJO: tu model.clean evita duplicado cliente+documento (sin valorar "valor")
    # -----------------------------------
    def test_model_no_permite_duplicado_mismo_cliente_doc_aunque_valor_diferente(self):
        DocumentosCliente.objects.create(
            id_cliente=self.cliente,
            id_documento=self.documento,
            valor="ABC-123"
        )

        obj = DocumentosCliente(
            id_cliente=self.cliente,
            id_documento=self.documento,
            valor="DIF-456"
        )

        # Como tu save() llama full_clean(), debe explotar por duplicado cliente+documento
        with self.assertRaises(ValidationError):
            obj.save()

    # -----------------------------------
    # 4) Integración: Inline permiso add
    # -----------------------------------
    def test_inline_has_add_permission_solo_si_obj_existe(self):
        inline = DocumentosClienteInline(parent_model=Cliente, admin_site=admin.site)

        class DummyReq:
            user = None

        request = DummyReq()

        # obj None => False
        self.assertFalse(inline.has_add_permission(request, obj=None))
        # obj existe => True
        self.assertTrue(inline.has_add_permission(request, obj=self.cliente))

    # -----------------------------------
    # 5) Integración real con Admin URLs
    # -----------------------------------
    def test_admin_changelist_clientes_responde_200(self):
        url = reverse("admin:clientes_cliente_changelist")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_admin_add_documentos_cliente_responde_200(self):
        url = reverse("admin:clientes_documentoscliente_add")
        resp = self.client.get(url)
        # Puede ser 200 o 302 si tu admin redirige por permisos, pero con superuser debe ser 200
        self.assertEqual(resp.status_code, 200)

    def test_admin_delete_cliente_post_elimina_y_redirige(self):
        url = reverse("admin:clientes_cliente_delete", args=[self.cliente.id])

        # GET muestra confirmación
        resp_get = self.client.get(url)
        self.assertEqual(resp_get.status_code, 200)

        # POST confirma delete
        resp_post = self.client.post(url, data={"post": "yes"})
        self.assertEqual(resp_post.status_code, 302)

        # Validar que ya no existe
        self.assertFalse(Cliente.objects.filter(id=self.cliente.id).exists())