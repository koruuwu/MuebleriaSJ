# Sucursales/tests/test_sucursales_integracion.py

from django.test import TestCase
from django.utils import timezone

from Sucursales.admin import SucursaleForm, CAIMForm, CajaForm
from Sucursales.models import Sucursale, Cai, Caja


class SucursaleFormCrudTest(TestCase):
    def setUp(self):
        self.data = {
            "codigo_sucursal": "001",
            "nombre": "Sucursal Centro",
            "telefono": "99998888",
            "direccion": "Barrio Centro, Calle Principal",
            "rtn": "0801-2000-000001",
        }

    def test_crear_sucursal_valida(self):
        """Valida que SucursaleForm permita crear una sucursal con RTN válido."""
        form = SucursaleForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        sucursal = form.save()
        self.assertEqual(Sucursale.objects.count(), 1)
        self.assertEqual(sucursal.codigo_sucursal, "001")
        self.assertEqual(sucursal.nombre, "Sucursal Centro")
        self.assertEqual(sucursal.rtn, "0801-2000-000001")

    def test_editar_sucursal_modifica_nombre(self):
        """Valida que editar el nombre se refleje en base de datos."""
        sucursal = Sucursale.objects.create(
            codigo_sucursal="001",
            nombre="Sucursal Centro",
            telefono="99998888",
            direccion="Barrio Centro",
            rtn="0801-2000-000001",
        )

        sucursal.nombre = "Sucursal Centro Actualizada"
        sucursal.save()

        sucursal_ref = Sucursale.objects.get(pk=sucursal.pk)
        self.assertEqual(sucursal_ref.nombre, "Sucursal Centro Actualizada")

    def test_eliminar_sucursal_elimina_registro(self):
        """Valida que se elimine la sucursal."""
        sucursal = Sucursale.objects.create(
            codigo_sucursal="001",
            nombre="Sucursal Centro",
            telefono="99998888",
            direccion="Barrio Centro",
            rtn="0801-2000-000001",
        )

        sucursal.delete()
        self.assertEqual(Sucursale.objects.count(), 0)


class CaiFormCrudTest(TestCase):
    def setUp(self):
        self.sucursal = Sucursale.objects.create(
            codigo_sucursal="001",
            nombre="Sucursal Centro",
            telefono="99998888",
            direccion="Barrio Centro",
            rtn="0801-2000-000001",
        )
        hoy = timezone.now().date()

        self.data = {
            "codigo_cai": "CAI-TEST-0001",
            "fecha_emision": hoy,
            "fecha_vencimiento": hoy.replace(year=hoy.year + 1),
            "rango_inicial": "1",          # el save() lo normaliza a 8 dígitos
            "rango_final": "99",           # el save() lo normaliza a 8 dígitos
            "ultima_secuencia": "0",       # el save() lo normaliza a 8 dígitos
            "activo": True,
            "sucursal": self.sucursal.id,
        }

    def test_crear_cai_valido_y_normaliza_campos(self):
        """Valida que CAIMForm cree un CAI válido y que el modelo normalice a 8 dígitos."""
        form = CAIMForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        cai = form.save()
        self.assertEqual(Cai.objects.count(), 1)

        cai_ref = Cai.objects.get(pk=cai.pk)
        self.assertEqual(cai_ref.rango_inicial, "00000001")
        self.assertEqual(cai_ref.rango_final, "00000099")
        self.assertEqual(cai_ref.ultima_secuencia, "00000000")
        self.assertTrue(cai_ref.activo)
        self.assertEqual(cai_ref.sucursal_id, self.sucursal.id)

    def test_editar_cai_modifica_activo(self):
        """Valida que editar el estado activo se refleje en base de datos."""
        hoy = timezone.now().date()
        cai = Cai.objects.create(
            codigo_cai="CAI-TEST-0001",
            fecha_emision=hoy,
            fecha_vencimiento=hoy.replace(year=hoy.year + 1),
            rango_inicial="00000001",
            rango_final="00000099",
            ultima_secuencia="00000000",
            activo=True,
            sucursal=self.sucursal,
        )

        cai.activo = False
        cai.save()

        cai_ref = Cai.objects.get(pk=cai.pk)
        self.assertFalse(cai_ref.activo)

    def test_eliminar_cai_elimina_registro(self):
        """Valida que se elimine el CAI."""
        hoy = timezone.now().date()
        cai = Cai.objects.create(
            codigo_cai="CAI-TEST-0001",
            fecha_emision=hoy,
            fecha_vencimiento=hoy.replace(year=hoy.year + 1),
            rango_inicial="00000001",
            rango_final="00000099",
            ultima_secuencia="00000000",
            activo=True,
            sucursal=self.sucursal,
        )

        cai.delete()
        self.assertEqual(Cai.objects.count(), 0)


class CajaFormCrudTest(TestCase):
    def setUp(self):
        self.sucursal = Sucursale.objects.create(
            codigo_sucursal="001",
            nombre="Sucursal Centro",
            telefono="99998888",
            direccion="Barrio Centro",
            rtn="0801-2000-000001",
        )

        self.data = {
            "sucursal": self.sucursal.id,
            "codigo_caja": "01",
            "estado": True,
        }

    def test_crear_caja_valida(self):
        """Valida que CajaForm permita crear una caja."""
        form = CajaForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        caja = form.save()
        self.assertEqual(Caja.objects.count(), 1)
        self.assertEqual(caja.sucursal_id, self.sucursal.id)
        self.assertEqual(caja.codigo_caja, "01")
        self.assertTrue(caja.estado)

    def test_editar_caja_modifica_estado(self):
        """Valida que editar el estado se refleje en base de datos."""
        caja = Caja.objects.create(
            sucursal=self.sucursal,
            codigo_caja="01",
            estado=True,
        )

        caja.estado = False
        caja.save()

        caja_ref = Caja.objects.get(pk=caja.pk)
        self.assertFalse(caja_ref.estado)

    def test_eliminar_caja_elimina_registro(self):
        """Valida que se elimine la caja."""
        caja = Caja.objects.create(
            sucursal=self.sucursal,
            codigo_caja="01",
            estado=True,
        )

        caja.delete()
        self.assertEqual(Caja.objects.count(), 0)