# realdb_tests/test_trabajo_realdb.py
from uuid import uuid4
from datetime import timedelta

from django.test import SimpleTestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from Trabajo.models import OrdenMensuale, OrdenMensualDetalle, AportacionEmpleado
from Empleados.models import PerfilUsuario
from Sucursales.models import Sucursale
from Muebles.models import CategoriasMueble, Tamaño, Mueble
from Materiales.models import UnidadesMedida


class TrabajoRealDBTests(SimpleTestCase):
    
    databases = {"default"}

    def setUp(self):
        self.tag = f"test_{uuid4().hex[:8]}"
        self.UserModel = get_user_model()

        self.created = {
            "aportaciones": [],
            "detalles": [],
            "ordenes": [],
            # deps
            "auth_users": [],
            "perfiles": [],
            "sucursales": [],
            "muebles": [],
            "cats_mueble": [],
            "tamano": [],
            "unidades_medida": [],
        }

    def tearDown(self):
        # 1) Dependientes
        if self.created["aportaciones"]:
            AportacionEmpleado.objects.filter(id__in=self.created["aportaciones"]).delete()

        if self.created["detalles"]:
            OrdenMensualDetalle.objects.filter(id__in=self.created["detalles"]).delete()

        if self.created["ordenes"]:
            OrdenMensuale.objects.filter(id__in=self.created["ordenes"]).delete()

        # 2) Dependencias: perfil/auth_user
        if self.created["perfiles"]:
            PerfilUsuario.objects.filter(id__in=self.created["perfiles"]).delete()

        if self.created["auth_users"]:
            self.UserModel.objects.filter(id__in=self.created["auth_users"]).delete()

        # 3) Dependencias: muebles
        if self.created["muebles"]:
            # Mueble.save crea historial automáticamente: borramos el historial por FK antes de borrar muebles
            from Muebles.models import HistorialPreciosMueble
            HistorialPreciosMueble.objects.filter(id_mueble_id__in=self.created["muebles"]).delete()
            Mueble.objects.filter(id__in=self.created["muebles"]).delete()

        if self.created["tamano"]:
            Tamaño.objects.filter(id__in=self.created["tamano"]).delete()

        if self.created["cats_mueble"]:
            CategoriasMueble.objects.filter(id__in=self.created["cats_mueble"]).delete()

        # 4) Dependencias: sucursal
        if self.created["sucursales"]:
            Sucursale.objects.filter(id__in=self.created["sucursales"]).delete()

        # 5) Unidad medida (solo si la creamos)
        if self.created["unidades_medida"]:
            UnidadesMedida.objects.filter(id__in=self.created["unidades_medida"]).delete()

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _mk_um(self):
        um = UnidadesMedida.objects.first()
        if um:
            return um
        um = UnidadesMedida.objects.create(nombre=f"{self.tag[:10]}_um", abreviatura="un")
        self.created["unidades_medida"].append(um.id)
        return um

    def _mk_sucursal(self):
        # Evitar colisiones: codigo max_length=10
        cod = f"{self.tag[-3:]}"
        s = Sucursale.objects.create(
            codigo_sucursal=cod,
            nombre=f"{self.tag}_sucursal",
            direccion="Direccion test",
            telefono="99999999",
            rtn=None,
        )
        self.created["sucursales"].append(s.id)
        return s

    def _mk_auth_user_y_perfil(self):
        u = self.UserModel.objects.create_user(
            username=f"{self.tag}_auth",
            email=f"{self.tag}@test.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User",
        )
        self.created["auth_users"].append(u.id)

        perfil = PerfilUsuario.objects.filter(user=u).first()
        # La señal debería crear el perfil automáticamente
        if perfil:
            self.created["perfiles"].append(perfil.id)
        return u, perfil

    def _mk_mueble(self):
        um = self._mk_um()
        cat = CategoriasMueble.objects.create(
            nombre=f"{self.tag}_cat_mueble",
            descripcion="cat mueble test",
            imagen="x",
            imagen_url=None,
        )
        self.created["cats_mueble"].append(cat.id)

        tam = Tamaño.objects.create(
            nombre=f"{self.tag}_tam",
            descripcion="tam test",
        )
        self.created["tamano"].append(tam.id)

        m = Mueble.objects.create(
            nombre=f"{self.tag}_mueble",
            descripcion="mueble test",
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
            stock_maximo=10,
        )
        self.created["muebles"].append(m.id)
        return m

    def _mk_orden(self):
        suc = self._mk_sucursal()
        fin = (timezone.now().date() + timedelta(days=30))
        o = OrdenMensuale.objects.create(
            id_sucursal=suc,
            nombre=f"{self.tag}_orden",
            observaciones="obs test",
            fecha_fin=fin,
            estado=OrdenMensuale.PEND,
        )
        self.created["ordenes"].append(o.id)
        return o, suc

    # ---------------------------------------------------------------------
    # Tests
    # ---------------------------------------------------------------------

    def test_01_orden_mensual_crud_realdb(self):
        orden, _ = self._mk_orden()
        self.assertIsNotNone(orden.id)

        orden.observaciones = "obs edit"
        orden.save(update_fields=["observaciones"])
        self.assertEqual(OrdenMensuale.objects.get(id=orden.id).observaciones, "obs edit")

        oid = orden.id
        orden.delete()
        self.assertFalse(OrdenMensuale.objects.filter(id=oid).exists())
        self.created["ordenes"] = [i for i in self.created["ordenes"] if i != oid]

    def test_02_detalle_crud_realdb(self):
        orden, _ = self._mk_orden()
        mueble = self._mk_mueble()

        det = OrdenMensualDetalle.objects.create(
            id_orden=orden,
            id_mueble=mueble,
            cantidad_planificada=10,
            cantidad_producida=0,
            estado=OrdenMensualDetalle.PEND,
            entrega_estim=None,
        )
        self.created["detalles"].append(det.id)
        self.assertIsNotNone(det.id)

        det.estado = OrdenMensualDetalle.COMP
        det.cantidad_producida = 10
        det.save(update_fields=["estado", "cantidad_producida"])

        det_ref = OrdenMensualDetalle.objects.get(id=det.id)
        self.assertEqual(det_ref.estado, OrdenMensualDetalle.COMP)
        self.assertEqual(det_ref.cantidad_producida, 10)

        did = det.id
        det.delete()
        self.assertFalse(OrdenMensualDetalle.objects.filter(id=did).exists())
        self.created["detalles"] = [i for i in self.created["detalles"] if i != did]

    def test_03_actualizar_estado_orden_realdb(self):
        orden, _ = self._mk_orden()
        m1 = self._mk_mueble()
        m2 = self._mk_mueble()  # crea otro (tag único por test)

        # sin detalles -> PEND
        orden.actualizar_estado()
        self.assertEqual(OrdenMensuale.objects.get(id=orden.id).estado, OrdenMensuale.PEND)

        d1 = OrdenMensualDetalle.objects.create(
            id_orden=orden,
            id_mueble=m1,
            cantidad_planificada=5,
            cantidad_producida=0,
            estado=OrdenMensualDetalle.PEND,
        )
        d2 = OrdenMensualDetalle.objects.create(
            id_orden=orden,
            id_mueble=m2,
            cantidad_planificada=5,
            cantidad_producida=0,
            estado=OrdenMensualDetalle.PEND,
        )
        self.created["detalles"].extend([d1.id, d2.id])

        # 0 completos -> PEND
        orden.actualizar_estado()
        self.assertEqual(OrdenMensuale.objects.get(id=orden.id).estado, OrdenMensuale.PEND)

        # 1 completo de 2 -> INCOMP
        d1.estado = OrdenMensualDetalle.COMP
        d1.cantidad_producida = 5
        d1.save(update_fields=["estado", "cantidad_producida"])
        orden.actualizar_estado()
        self.assertEqual(OrdenMensuale.objects.get(id=orden.id).estado, OrdenMensuale.INCOMP)

        # 2 completos -> COMP
        d2.estado = OrdenMensualDetalle.COMP
        d2.cantidad_producida = 5
        d2.save(update_fields=["estado", "cantidad_producida"])
        orden.actualizar_estado()
        self.assertEqual(OrdenMensuale.objects.get(id=orden.id).estado, OrdenMensuale.COMP)

    def test_04_aportacion_empleado_crud_realdb(self):
        orden, _ = self._mk_orden()
        mueble = self._mk_mueble()

        det = OrdenMensualDetalle.objects.create(
            id_orden=orden,
            id_mueble=mueble,
            cantidad_planificada=10,
            cantidad_producida=0,
            estado=OrdenMensualDetalle.PEND,
        )
        self.created["detalles"].append(det.id)

        _, perfil = self._mk_auth_user_y_perfil()
        self.assertIsNotNone(perfil, "Debe existir PerfilUsuario (creado por señal al crear auth_user).")

        ap = AportacionEmpleado.objects.create(
            id_orden_detalle=det,
            id_empleado=perfil,
            cant_aprobada=5,
            cantidad_finalizada=0,
            estado=AportacionEmpleado.PEND,
            materiales_reservados={"madera": 2},
        )
        self.created["aportaciones"].append(ap.id)
        self.assertIsNotNone(ap.id)

        ap.estado = AportacionEmpleado.TRAB
        ap.cantidad_finalizada = 3
        ap.save(update_fields=["estado", "cantidad_finalizada"])

        ap_ref = AportacionEmpleado.objects.get(id=ap.id)
        self.assertEqual(ap_ref.estado, AportacionEmpleado.TRAB)
        self.assertEqual(ap_ref.cantidad_finalizada, 3)

        aid = ap.id
        ap.delete()
        self.assertFalse(AportacionEmpleado.objects.filter(id=aid).exists())
        self.created["aportaciones"] = [i for i in self.created["aportaciones"] if i != aid]