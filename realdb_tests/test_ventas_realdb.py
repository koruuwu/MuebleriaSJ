# realdb_tests/test_ventas_realdb.py
from datetime import date, timedelta

from django.test import SimpleTestCase
from django.utils import timezone
from django.contrib.auth.models import User

from Ventas.models import OrdenesVenta, DetallesOrdene, EstadoPagos, MetodosPago
from clientes.models import Cliente
from Sucursales.models import Sucursale, Caja
from Empleados.models import PerfilUsuario

from Materiales.models import UnidadesMedida
from Muebles.models import CategoriasMueble, Tamaño, Mueble


TEST_PREFIX = "test_"


class RealDBPrefixCleanupMixin:
    

    def tearDown(self):
        # 1) DetallesOrdene (depende de OrdenesVenta y Mueble)
        try:
            DetallesOrdene.objects.filter(
                id_orden__id_factura__startswith=TEST_PREFIX
            ).delete()
        except Exception:
            pass

        # 2) OrdenesVenta
        try:
            OrdenesVenta.objects.filter(
                id_factura__startswith=TEST_PREFIX
            ).delete()
        except Exception:
            pass

        # 3) Mueble y catálogos que creamos para el test
        #    (cuidado: si tus tablas de catálogos se usan globalmente, este prefijo evita dañar data real)
        try:
            Mueble.objects.filter(nombre__startswith=TEST_PREFIX).delete()
        except Exception:
            pass

        try:
            CategoriasMueble.objects.filter(nombre__startswith=TEST_PREFIX).delete()
        except Exception:
            pass

        try:
            Tamaño.objects.filter(nombre__startswith=TEST_PREFIX).delete()
        except Exception:
            pass

        try:
            UnidadesMedida.objects.filter(nombre__startswith=TEST_PREFIX).delete()
        except Exception:
            pass

        # 4) Cliente
        try:
            Cliente.objects.filter(nombre__startswith=TEST_PREFIX).delete()
        except Exception:
            pass

        # 5) PerfilUsuario / User (ojo: PerfilUsuario depende del User)
        try:
            PerfilUsuario.objects.filter(user__username__startswith=TEST_PREFIX).delete()
        except Exception:
            pass

        try:
            User.objects.filter(username__startswith=TEST_PREFIX).delete()
        except Exception:
            pass

        # 6) Caja y Sucursal
        try:
            Caja.objects.filter(codigo_caja__startswith=TEST_PREFIX).delete()
        except Exception:
            pass

        try:
            Sucursale.objects.filter(nombre__startswith=TEST_PREFIX).delete()
        except Exception:
            pass

        # 7) Catálogos Ventas
        try:
            EstadoPagos.objects.filter(nombre__startswith=TEST_PREFIX).delete()
        except Exception:
            pass

        try:
            MetodosPago.objects.filter(tipo__startswith=TEST_PREFIX).delete()
        except Exception:
            pass


class VentasCatalogosRealDBTests(RealDBPrefixCleanupMixin, SimpleTestCase):

    databases = {"default"}


    def test_01_estadopagos_crud_realdb(self):
        # CREATE
        ep = EstadoPagos.objects.create(
            nombre=f"{TEST_PREFIX}Pago_TMP",
            descripcion="tmp"
        )
        self.assertIsNotNone(ep.id)

        # READ
        ep_db = EstadoPagos.objects.get(id=ep.id)
        self.assertTrue(ep_db.nombre.startswith(TEST_PREFIX))

        # UPDATE
        ep_db.descripcion = "actualizado"
        ep_db.save(update_fields=["descripcion"])
        ep_db.refresh_from_db()
        self.assertEqual(ep_db.descripcion, "actualizado")

        # DELETE
        ep_id = ep_db.id
        ep_db.delete()
        self.assertFalse(EstadoPagos.objects.filter(id=ep_id).exists())

    def test_02_metodospago_crud_realdb(self):
        # CREATE
        mp = MetodosPago.objects.create(
            tipo=f"{TEST_PREFIX}Metodo_TMP",
            descripcion="tmp"
        )
        self.assertIsNotNone(mp.id)

        # READ
        mp_db = MetodosPago.objects.get(id=mp.id)
        self.assertTrue(mp_db.tipo.startswith(TEST_PREFIX))

        # UPDATE
        mp_db.descripcion = "actualizado"
        mp_db.save(update_fields=["descripcion"])
        mp_db.refresh_from_db()
        self.assertEqual(mp_db.descripcion, "actualizado")

        # DELETE
        mp_id = mp_db.id
        mp_db.delete()
        self.assertFalse(MetodosPago.objects.filter(id=mp_id).exists())


class VentasOrdenesYDetallesRealDBTests(RealDBPrefixCleanupMixin, SimpleTestCase):
    databases = {"default"}
    """
    (3) OrdenesVenta CRUD realdb
    (4) DetallesOrdene CRUD realdb
    """

    def _unique(self):
        return timezone.now().strftime("%Y%m%d%H%M%S%f")

    def _mk_sucursal_caja(self):
    # Formato real del sistema
        suc = Sucursale.objects.create(
            codigo_sucursal="001",  # <= 10
            nombre=f"{TEST_PREFIX}Sucursal",
            direccion="Direccion Test",
            telefono="99999999",
            rtn=None,
        )

        caja = Caja.objects.create(
            sucursal=suc,
            codigo_caja="01",  # <= 10
            estado=True,
        )

        return suc, caja

    def _mk_user_perfil(self, suc, caja):
        username = f"{TEST_PREFIX}user_{self._unique()}"
        u = User.objects.create_user(username=username, password="pass12345")

        perfil = PerfilUsuario.objects.filter(user=u).first()
        if not perfil:
            perfil = PerfilUsuario.objects.create(user=u)

        perfil.sucursal = suc
        perfil.caja = caja
        perfil.save(update_fields=["sucursal", "caja"])
        return u, perfil

    def _mk_cliente(self):
        return Cliente.objects.create(
            nombre=f"{TEST_PREFIX}Cliente_{self._unique()}",
            telefono="99999999",
            direccion="dir",
            rtn=None,
        )
    
    def _mk_unidad_medida(self):
    # Reusar la que ya existe en tu BD real (Centimetro / cm)
        um = UnidadesMedida.objects.filter(nombre__iexact="Centimetro").first()
        if um:
            return um

        # Si no existe, crear una válida para varchar(15) y (4)
        return UnidadesMedida.objects.create(
            nombre="Centimetro",   # <= 15
            abreviatura="cm",      # <= 4
        )

    def _mk_mueble(self):
        um = self._mk_unidad_medida()
        cat = CategoriasMueble.objects.create(
            nombre=f"{TEST_PREFIX}Cat_{self._unique()}",
            descripcion="desc",
            imagen="img",
            imagen_url=None,
        )
        tam = Tamaño.objects.create(
            nombre=f"{TEST_PREFIX}Tam_{self._unique()}",
            descripcion="desc",
        )

        return Mueble.objects.create(
            nombre=f"{TEST_PREFIX}Mueble_{self._unique()}",
            descripcion="desc",
            precio_base=100.0,
            categoria=cat,
            medida=um,
            alto=1.0,
            ancho=1.0,
            largo=1.0,
            imagen=None,
            imagen_url=None,
            tamano=tam,
            Descontinuado=False,
            stock_minimo=1,
            stock_maximo=100,
        )

    def _mk_catalogos_ventas(self):
        ep = EstadoPagos.objects.create(
            nombre=f"{TEST_PREFIX}Pendiente_{self._unique()}",
            descripcion="desc",
        )
        mp = MetodosPago.objects.create(
            tipo=f"{TEST_PREFIX}Efectivo_{self._unique()}",
            descripcion="desc",
        )
        return ep, mp

    def test_03_ordenesventa_crud_realdb(self):
        suc, caja = self._mk_sucursal_caja()
        _, perfil = self._mk_user_perfil(suc, caja)
        cliente = self._mk_cliente()
        ep, mp = self._mk_catalogos_ventas()

        # CREATE
        orden = OrdenesVenta.objects.create(
            cai_usado=None,
            id_factura=f"{TEST_PREFIX}FACT_{self._unique()}",
            id_cotizacion=None,
            id_empleado=perfil,
            id_cliente=cliente,
            rtn=False,
            descuento=0.0,
            subtotal=100.0,
            isv=15.0,
            total=115.0,
            cuotas=False,
            pagado=0.0,
            id_estado_pago=ep,
            id_metodo_pago=mp,
            fecha_entrega=date.today() + timedelta(days=3),
            efectivo=None,
            num_tarjeta=None,
        )
        self.assertIsNotNone(orden.id)

        # READ
        orden_db = OrdenesVenta.objects.get(id=orden.id)
        self.assertTrue(orden_db.id_factura.startswith(TEST_PREFIX))

        # UPDATE
        orden_db.total = 120.0
        orden_db.save(update_fields=["total"])
        orden_db.refresh_from_db()
        self.assertEqual(float(orden_db.total), 120.0)

        # DELETE
        oid = orden_db.id
        orden_db.delete()
        self.assertFalse(OrdenesVenta.objects.filter(id=oid).exists())

    def test_04_detallesordene_crud_realdb(self):
        suc, caja = self._mk_sucursal_caja()
        _, perfil = self._mk_user_perfil(suc, caja)
        cliente = self._mk_cliente()
        ep, mp = self._mk_catalogos_ventas()
        mueble = self._mk_mueble()

        orden = OrdenesVenta.objects.create(
            cai_usado=None,
            id_factura=f"{TEST_PREFIX}FACT_{self._unique()}",
            id_cotizacion=None,
            id_empleado=perfil,
            id_cliente=cliente,
            rtn=False,
            descuento=0.0,
            subtotal=200.0,
            isv=30.0,
            total=230.0,
            cuotas=False,
            pagado=0.0,
            id_estado_pago=ep,
            id_metodo_pago=mp,
            fecha_entrega=date.today() + timedelta(days=5),
            efectivo=None,
            num_tarjeta=None,
        )

        # CREATE
        det = DetallesOrdene.objects.create(
            id_orden=orden,
            id_mueble=mueble,
            precio_unitario=100.0,
            cantidad=2,
            subtotal=200.0,
        )
        self.assertIsNotNone(det.id)

        # READ
        det_db = DetallesOrdene.objects.get(id=det.id)
        self.assertEqual(det_db.cantidad, 2)

        # UPDATE
        det_db.cantidad = 3
        det_db.subtotal = 300.0
        det_db.save(update_fields=["cantidad", "subtotal"])
        det_db.refresh_from_db()
        self.assertEqual(det_db.cantidad, 3)
        self.assertEqual(float(det_db.subtotal), 300.0)

        # DELETE
        did = det_db.id
        det_db.delete()
        self.assertFalse(DetallesOrdene.objects.filter(id=did).exists())