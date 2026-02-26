from datetime import date, timedelta

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from django.test import TestCase, RequestFactory

from clientes.models import Cliente
from Compras.models import InventarioMueble, Estados
from Materiales.models import UnidadesMedida
from Muebles.models import CategoriasMueble, Tamaño, Mueble
from Parametros.models import Parametro
from Sucursales.models import Sucursale, Caja, Cai
from Empleados.models import PerfilUsuario

from Ventas.admin import (
    OrdenForm,
    DetallesOrdenFormSet,
    DetallesOrdeneForm,
    OrdenesVentasAdmin,
)
from Ventas.models import OrdenesVenta, EstadoPagos, MetodosPago, DetallesOrdene


class VentasBaseSetupMixin:
    """
    Setup común con datos REALES que tus forms/admin requieren:
    - Estados (Estados_M) ids 1,2,3 (por filtros estado__id__in=[1,2])
    - Parametros ids 2,3,4 (id=2 correlativo facturas, id=3 desc max, id=4 % efectivo mínimo)
    - Sucursal + Caja + PerfilUsuario (OrdenForm exige perfil con sucursal y caja)
    - CAI válido (OrdenForm/obtener_cai_valido exige CAI vigente y rango no agotado)
    - Cat/Mueble/Medida/Tamaño para poder crear Mueble e Inventario
    - EstadoPagos ("Pendiente","Pagado")
    - MetodosPago (id=4 Mixto)
    """

    def _setup_base(self):
        # --- Estados (Compras.models.Estados -> db_table Estados_M) ---
        Estados.objects.create(id=1, tipo="Disponible")
        Estados.objects.create(id=2, tipo="Bajo Stock")
        Estados.objects.create(id=3, tipo="Agotado")

        # --- Parámetros ---
        # id=2 -> prefijo/valor para factura
        Parametro.objects.create(id=2, nombre="Prefijo Factura", valor="ABC")
        # id=3 -> descuento máximo (%)
        Parametro.objects.create(id=3, nombre="Descuento Máximo", valor="10")
        # id=4 -> % mínimo de efectivo
        Parametro.objects.create(id=4, nombre="% Efectivo Mínimo", valor="30")

        # --- Sucursal y Caja ---
        self.sucursal = Sucursale.objects.create(
            codigo_sucursal="001",
            nombre="Sucursal Central",
            direccion="Col. Centro",
            telefono="9999-9999",
            rtn="0000-0000-000000",
        )
        self.caja = Caja.objects.create(
            sucursal=self.sucursal,
            codigo_caja="01",
            estado=True,
        )

        # --- Usuario + PerfilUsuario (lo crea la señal) ---
        self.user = User.objects.create_user(username="tester", password="12345")
        self.perfil = PerfilUsuario.objects.get(user=self.user)
        self.perfil.sucursal = self.sucursal
        self.perfil.caja = self.caja
        self.perfil.save()

        # --- CAI válido ---
        hoy = date.today()
        self.cai = Cai.objects.create(
            codigo_cai="CAI-TEST-0001",
            fecha_emision=hoy - timedelta(days=1),
            fecha_vencimiento=hoy + timedelta(days=30),
            rango_inicial="1",
            rango_final="10",
            ultima_secuencia="0",
            activo=True,
            sucursal=self.sucursal,
        )

        # --- Cat / Medida / Tamaño / Mueble ---
        self.medida = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="UND")
        self.tamano = Tamaño.objects.create(nombre="Mediano", descripcion="M")
        self.cat_mueble = CategoriasMueble.objects.create(
            nombre="Sillas",
            descripcion="Cat sillas",
            imagen="ruta/test.png",
            imagen_url="",
        )
        self.mueble = Mueble.objects.create(
            nombre="Silla Alpha",
            descripcion="Silla de prueba",
            precio_base=1000.0,
            categoria=self.cat_mueble,
            medida=self.medida,
            alto=1.0,
            ancho=1.0,
            largo=1.0,
            imagen="",
            imagen_url="",
            tamano=self.tamano,
            Descontinuado=False,
            stock_minimo=5,
            stock_maximo=100,
        )

        # --- Cliente ---
        self.cliente_ok = Cliente.objects.create(
            nombre="Cliente Uno",
            telefono="8888-8888",
            direccion="Barrio X",
            rtn="0801-1999-123456",  # con rtn
        )
        self.cliente_sin_rtn = Cliente.objects.create(
            nombre="Cliente Dos",
            telefono="7777-7777",
            direccion="Barrio Y",
            rtn=None,
        )

        # --- EstadoPagos ---
        self.estado_pendiente = EstadoPagos.objects.create(
            nombre="Pendiente", descripcion="Pago pendiente"
        )
        self.estado_pagado = EstadoPagos.objects.create(
            nombre="Pagado", descripcion="Pago completo"
        )

        # --- MetodosPago ---
        # Importante: el form valida mixto cuando id == 4
        self.metodo_mixto = MetodosPago.objects.create(
            id=4, tipo="Mixto", descripcion="Efectivo + Tarjeta"
        )
        self.metodo_efectivo = MetodosPago.objects.create(
            id=1, tipo="Efectivo", descripcion="Solo efectivo"
        )

        # --- Inventario de mueble en sucursal (para validar stock en formset) ---
        self.inventario = InventarioMueble.objects.create(
            id_mueble=self.mueble,
            cantidad_disponible=50,
            ubicación=self.sucursal,
            estado=Estados.objects.get(id=1),
        )


class OrdenFormTests(TestCase, VentasBaseSetupMixin):
    def setUp(self):
        self._setup_base()

    def _base_orden_data(self, **overrides):
        # NOTA: OrdenForm toma perfil desde form.current_user (set en el admin)
        base = {
            "cai_usado": "",  # se asigna en save_model del admin, puede venir vacío en el form
            "id_factura": "",
            "id_cotizacion": "",
            "id_empleado": "",  # opcional (blank=True,null=True)
            "id_cliente": self.cliente_ok.id,
            "rtn": False,
            "descuento": 0,
            "subtotal": 1000,
            "isv": 150,
            "total": 1150,
            "cuotas": False,
            "pagado": "",
            "id_estado_pago": self.estado_pendiente.id,
            "id_metodo_pago": self.metodo_efectivo.id,
            "fecha_entrega": (date.today() + timedelta(days=7)).isoformat(),
            "efectivo": 400,  # >= 30% de 1150 => 345
            "num_tarjeta": "",
            # campo fantasma del form:
            "aporte": 0,
        }
        base.update(overrides)
        return base

    def test_orden_form_valida(self):
        form = OrdenForm(data=self._base_orden_data())
        form.current_user = self.user
        self.assertTrue(form.is_valid(), form.errors)

    def test_orden_form_falla_efectivo_menor_minimo_parametro(self):
        # Parametro id=4 = 30% mínimo. Total 1150 => min 345. Pongo 100.
        form = OrdenForm(data=self._base_orden_data(efectivo=100))
        form.current_user = self.user
        self.assertFalse(form.is_valid())
        self.assertIn("menor al mínimo requerido", str(form.errors))

    def test_orden_form_falla_efectivo_mayor_total(self):
        form = OrdenForm(data=self._base_orden_data(efectivo=999999))
        form.current_user = self.user
        self.assertFalse(form.is_valid())
        self.assertIn("no puede exceder el total", str(form.errors))

    def test_orden_form_falla_descuento_supera_maximo(self):
        # Parametro id=3 = 10%
        form = OrdenForm(data=self._base_orden_data(descuento=15))
        form.current_user = self.user
        self.assertFalse(form.is_valid())
        self.assertIn("descuento máximo", str(form.errors).lower())

    def test_orden_form_mixto_requiere_efectivo_y_tarjeta(self):
        form = OrdenForm(
            data=self._base_orden_data(
                id_metodo_pago=self.metodo_mixto.id,
                efectivo=0,
                num_tarjeta="",
            )
        )
        form.current_user = self.user
        self.assertFalse(form.is_valid())
        txt = str(form.errors).lower()
        self.assertIn("método de pago es mixto", txt)
        self.assertIn("efectivo", txt)
        self.assertIn("tarjeta", txt)


class VentasAdminSaveModelTests(TestCase, VentasBaseSetupMixin):
    def setUp(self):
        self._setup_base()
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.modeladmin = OrdenesVentasAdmin(OrdenesVenta, self.site)

    def test_save_model_genera_id_factura_y_actualiza_cai(self):
        data = {
            "id_cliente": self.cliente_ok.id,
            "rtn": False,
            "descuento": 0,
            "subtotal": 1000,
            "isv": 150,
            "total": 1150,
            "cuotas": False,
            "pagado": "",
            "id_estado_pago": self.estado_pendiente.id,
            "id_metodo_pago": self.metodo_efectivo.id,
            "fecha_entrega": (date.today() + timedelta(days=7)).isoformat(),
            "efectivo": 400,
            "num_tarjeta": "",
            "aporte": 0,
        }
        form = OrdenForm(data=data)
        form.current_user = self.user
        self.assertTrue(form.is_valid(), form.errors)

        obj = form.save(commit=False)

        request = self.factory.post("/admin/Ventas/ordenesventa/add/", data=data)
        request.user = self.user

        # Ejecuta tu lógica REAL del admin: genera id_factura, asigna cai_usado, incrementa secuencia
        self.modeladmin.save_model(request, obj, form, change=False)

        obj.refresh_from_db()
        self.cai.refresh_from_db()

        # Parametro id=2 -> "ABC"
        esperado = f"{self.sucursal.codigo_sucursal}-{self.caja.codigo_caja}-ABC-00000001"
        self.assertEqual(obj.id_factura, esperado)
        self.assertEqual(obj.cai_usado_id, self.cai.id)
        self.assertEqual(self.cai.ultima_secuencia, "00000001")


class DetallesOrdenFormSetTests(TestCase, VentasBaseSetupMixin):
    def setUp(self):
        self._setup_base()
        self.factory = RequestFactory()

    def _build_formset(self, request, orden_instance, cantidad):
        FormSet = inlineformset_factory(
            OrdenesVenta,
            DetallesOrdene,
            form=DetallesOrdeneForm,
            formset=DetallesOrdenFormSet,
            extra=0,
            can_delete=False,
            fields="__all__",
        )

        post = {
            "detallesordene_set-TOTAL_FORMS": "1",
            "detallesordene_set-INITIAL_FORMS": "0",
            "detallesordene_set-MIN_NUM_FORMS": "0",
            "detallesordene_set-MAX_NUM_FORMS": "1000",
            "detallesordene_set-0-id": "",
            "detallesordene_set-0-id_mueble": str(self.mueble.id),
            "detallesordene_set-0-precio_unitario": "1000",
            "detallesordene_set-0-cantidad": str(cantidad),
            "detallesordene_set-0-subtotal": str(1000 * cantidad),
        }

        fs = FormSet(data=post, instance=orden_instance)
        fs.request = request  # tu clean() lo requiere
        return fs

    def test_formset_falla_stock_insuficiente(self):
        # Perfil OK (tiene sucursal), pero inventario no alcanza
        request = self.factory.post("/admin/Ventas/ordenesventa/add/")
        request.user = self.user

        orden = OrdenesVenta(
            id_cliente=self.cliente_ok,
            rtn=False,
            descuento=0,
            subtotal=1000,
            isv=150,
            total=1150,
            cuotas=False,
            pagado=None,
            id_estado_pago=self.estado_pendiente,
            id_metodo_pago=self.metodo_efectivo,
            fecha_entrega=date.today() + timedelta(days=7),
            efectivo=400,
            num_tarjeta=None,
        )  # NO guardamos: creación (pk None) => permite inlines

        fs = self._build_formset(request, orden, cantidad=9999)
        self.assertFalse(fs.is_valid())

        non_form = " ".join([str(e) for e in fs.non_form_errors()])
        self.assertIn("stock insuficiente", non_form.lower())

    def test_formset_valido_con_stock_suficiente(self):
        request = self.factory.post("/admin/Ventas/ordenesventa/add/")
        request.user = self.user

        orden = OrdenesVenta(
            id_cliente=self.cliente_ok,
            rtn=False,
            descuento=0,
            subtotal=1000,
            isv=150,
            total=1150,
            cuotas=False,
            pagado=None,
            id_estado_pago=self.estado_pendiente,
            id_metodo_pago=self.metodo_efectivo,
            fecha_entrega=date.today() + timedelta(days=7),
            efectivo=400,
            num_tarjeta=None,
        )

        fs = self._build_formset(request, orden, cantidad=2)
        self.assertTrue(fs.is_valid(), fs.errors)