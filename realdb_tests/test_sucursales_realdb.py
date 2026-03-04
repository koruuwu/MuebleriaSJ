# realdb_tests/test_sucursales_realdb.py
from uuid import uuid4
from django.test import SimpleTestCase
from django.utils import timezone

from Sucursales.models import Sucursale, Caja, Cai


class SucursalesRealDBTests(SimpleTestCase):
    
    databases = {"default"}

    def setUp(self):
        self.tag = f"test_{uuid4().hex[:8]}"
        self.created = {
            "sucursales": [],
            "cajas": [],
            "cais": [],
        }

    def tearDown(self):
        # 1) Dependientes
        if self.created["cais"]:
            Cai.objects.filter(id__in=self.created["cais"]).delete()

        if self.created["cajas"]:
            Caja.objects.filter(id__in=self.created["cajas"]).delete()

        # 2) Padres
        if self.created["sucursales"]:
            Sucursale.objects.filter(id__in=self.created["sucursales"]).delete()

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _mk_sucursal(self):
        s = Sucursale.objects.create(
            codigo_sucursal="001",  # OJO: si tu BD tiene UNIQUE real, cambiamos a tag corto
            nombre=f"{self.tag}_sucursal",
            direccion="Direccion test",
            telefono="99999999",
            rtn=None,
        )
        self.created["sucursales"].append(s.id)
        return s

    # ---------------------------------------------------------------------
    # Tests
    # ---------------------------------------------------------------------

    def test_01_sucursal_crud_realdb(self):
        s = self._mk_sucursal()
        self.assertIsNotNone(s.id)

        s.telefono = "88888888"
        s.save(update_fields=["telefono"])
        self.assertEqual(Sucursale.objects.get(id=s.id).telefono, "88888888")

        sid = s.id
        s.delete()
        self.assertFalse(Sucursale.objects.filter(id=sid).exists())
        self.created["sucursales"] = [i for i in self.created["sucursales"] if i != sid]

    def test_02_caja_crud_realdb(self):
        s = self._mk_sucursal()

        c = Caja.objects.create(
            sucursal=s,
            codigo_caja="01",
            estado=True,
        )
        self.created["cajas"].append(c.id)
        self.assertIsNotNone(c.id)

        c.estado = False
        c.save(update_fields=["estado"])
        self.assertEqual(Caja.objects.get(id=c.id).estado, False)

        cid = c.id
        c.delete()
        self.assertFalse(Caja.objects.filter(id=cid).exists())
        self.created["cajas"] = [i for i in self.created["cajas"] if i != cid]

    def test_03_cai_normaliza_rangos_realdb(self):
        s = self._mk_sucursal()

        hoy = timezone.now().date()

        cai = Cai.objects.create(
            codigo_cai=f"{uuid4().hex[:8]}-{uuid4().hex[:6]}-{uuid4().hex[:6]}-{uuid4().hex[:6]}-{uuid4().hex[:6]}",
            fecha_emision=hoy,
            fecha_vencimiento=hoy.replace(year=hoy.year + 1),
            rango_inicial="1",
            rango_final="25",
            ultima_secuencia="7",
            activo=True,
            sucursal=s,
        )
        self.created["cais"].append(cai.id)
        self.assertIsNotNone(cai.id)

        cai_ref = Cai.objects.get(id=cai.id)
        self.assertEqual(cai_ref.rango_inicial, "00000001")
        self.assertEqual(cai_ref.rango_final, "00000025")
        self.assertEqual(cai_ref.ultima_secuencia, "00000007")

        # Update: cambiamos ultima_secuencia y verificamos normalización
        cai.ultima_secuencia = "123"
        cai.save(update_fields=["ultima_secuencia"])
        cai_ref2 = Cai.objects.get(id=cai.id)
        self.assertEqual(cai_ref2.ultima_secuencia, "00000123")

        cid = cai.id
        cai.delete()
        self.assertFalse(Cai.objects.filter(id=cid).exists())
        self.created["cais"] = [i for i in self.created["cais"] if i != cid]