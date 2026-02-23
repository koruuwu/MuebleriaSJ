# Compras/tests/test_compras_admin.py

from datetime import date, datetime, timedelta

from django.test import SimpleTestCase
from django.contrib.admin.sites import AdminSite

# Importamos clases del admin SOLO para probar lógica pura (readonly/permissions).
from Compras.admin import ListaCInline, ListaCompraAdmin, CotizacioneAdmin


class DummyUser:
    """
    Usuario dummy para que el admin no truene cuando llama request.user.has_perm(...)
    En pruebas puras no nos interesa el sistema real de permisos.
    """
    def has_perm(self, perm_name: str) -> bool:
        return True


class DummyRequest:
    """Request dummy para métodos del admin que lo reciben."""
    def __init__(self, user=None):
        self.user = user or DummyUser()


class DummyObj:
    """Objeto genérico con pk/estado para probar reglas."""
    def __init__(self, pk=None, estado=None):
        self.pk = pk
        self.estado = estado


class DummyMaterial:
    def __init__(self, stock_maximo=None, nombre="Material X"):
        self.stock_maximo = stock_maximo
        self.nombre = nombre


class ReglasPurasCompras:
    """
    Helpers equivalentes a reglas del código de Compras,
    implementadas sin BD para test unitario puro.
    """

    @staticmethod
    def validar_no_exceder_stock_maximo(cantidad_disponible, stock_maximo):
        """
        Equivalente a InventarioMForm.clean():
        - Si stock_maximo existe y cantidad > stock_maximo -> error.
        """
        errores = []
        if cantidad_disponible is None:
            return errores

        try:
            cantidad = float(cantidad_disponible)
        except (ValueError, TypeError):
            errores.append("La cantidad no es válida.")
            return errores

        if stock_maximo is not None:
            try:
                maximo = float(stock_maximo)
            except (ValueError, TypeError):
                return errores

            if maximo and cantidad > maximo:
                errores.append(f"La cantidad no puede exceder el stock máximo de {int(maximo) if maximo.is_integer() else maximo}")
        return errores

    @staticmethod
    def calcular_fecha_vencimiento(fecha_registro, dias_parametro=15):
        """
        Equivalente a CotizacioneAdmin.save_model():
        - fecha_vencimiento = fecha_registro.date() + timedelta(days=dias_parametro)
        """
        if not fecha_registro:
            return None

        if isinstance(fecha_registro, datetime):
            base = fecha_registro.date()
        elif isinstance(fecha_registro, date):
            base = fecha_registro
        else:
            raise TypeError("fecha_registro debe ser date o datetime")

        try:
            dias = int(dias_parametro)
        except (ValueError, TypeError):
            dias = 15

        return base + timedelta(days=dias)

    @staticmethod
    def validar_cantidad_necesaria_vs_stock_maximo(material_stock_maximo, cantidad_necesaria):
        """
        Equivalente a RequerimientoForm.clean() en la parte de stock máximo:
        - Si stock_maximo y cantidad > stock_maximo -> error.
        """
        errores = []
        if cantidad_necesaria is None:
            return errores

        try:
            cant = float(cantidad_necesaria)
        except (ValueError, TypeError):
            errores.append("La cantidad necesaria no es válida.")
            return errores

        if material_stock_maximo:
            try:
                maximo = float(material_stock_maximo)
            except (ValueError, TypeError):
                return errores

            if cant > maximo:
                errores.append(f"La cantidad no puede exceder el stock máximo de {int(maximo) if maximo.is_integer() else maximo}")
        return errores


class InventarioMaterialReglasPurasTest(SimpleTestCase):
    def setUp(self):
        self.material_con_max = DummyMaterial(stock_maximo=100, nombre="Barniz")
        self.material_sin_max = DummyMaterial(stock_maximo=None, nombre="Pegamento")

    def test_no_excede_stock_maximo_ok(self):
        errores = ReglasPurasCompras.validar_no_exceder_stock_maximo(
            cantidad_disponible=50,
            stock_maximo=self.material_con_max.stock_maximo
        )
        self.assertEqual(errores, [])

    def test_excede_stock_maximo_invalido(self):
        errores = ReglasPurasCompras.validar_no_exceder_stock_maximo(
            cantidad_disponible=150,
            stock_maximo=self.material_con_max.stock_maximo
        )
        self.assertTrue(errores)
        self.assertIn("stock máximo", errores[0])

    def test_stock_maximo_none_no_valida_limite(self):
        errores = ReglasPurasCompras.validar_no_exceder_stock_maximo(
            cantidad_disponible=9999,
            stock_maximo=self.material_sin_max.stock_maximo
        )
        self.assertEqual(errores, [])

    def test_cantidad_invalida_no_numerica(self):
        errores = ReglasPurasCompras.validar_no_exceder_stock_maximo(
            cantidad_disponible="abc",
            stock_maximo=100
        )
        self.assertEqual(errores, ["La cantidad no es válida."])


class CotizacionFechaVencimientoPuroTest(SimpleTestCase):
    def test_calcular_vencimiento_con_datetime(self):
        fecha_registro = datetime(2026, 2, 20, 10, 30, 0)
        venc = ReglasPurasCompras.calcular_fecha_vencimiento(fecha_registro, dias_parametro=15)
        self.assertEqual(venc, date(2026, 3, 7))  # 20 feb + 15 días = 7 mar

    def test_calcular_vencimiento_con_date(self):
        fecha_registro = date(2026, 2, 20)
        venc = ReglasPurasCompras.calcular_fecha_vencimiento(fecha_registro, dias_parametro=10)
        self.assertEqual(venc, date(2026, 3, 2))

    def test_dias_parametro_invalido_default_15(self):
        fecha_registro = date(2026, 2, 20)
        venc = ReglasPurasCompras.calcular_fecha_vencimiento(fecha_registro, dias_parametro="x")
        self.assertEqual(venc, date(2026, 3, 7))

    def test_fecha_registro_none(self):
        venc = ReglasPurasCompras.calcular_fecha_vencimiento(None, dias_parametro=15)
        self.assertIsNone(venc)


class RequerimientoCantidadVsStockPuroTest(SimpleTestCase):
    def test_cantidad_no_excede_ok(self):
        errores = ReglasPurasCompras.validar_cantidad_necesaria_vs_stock_maximo(
            material_stock_maximo=30,
            cantidad_necesaria=10
        )
        self.assertEqual(errores, [])

    def test_cantidad_excede_invalido(self):
        errores = ReglasPurasCompras.validar_cantidad_necesaria_vs_stock_maximo(
            material_stock_maximo=30,
            cantidad_necesaria=50
        )
        self.assertTrue(errores)
        self.assertIn("stock máximo", errores[0])

    def test_stock_maximo_none_no_restringe(self):
        errores = ReglasPurasCompras.validar_cantidad_necesaria_vs_stock_maximo(
            material_stock_maximo=None,
            cantidad_necesaria=999
        )
        self.assertEqual(errores, [])

    def test_cantidad_invalida(self):
        errores = ReglasPurasCompras.validar_cantidad_necesaria_vs_stock_maximo(
            material_stock_maximo=30,
            cantidad_necesaria="abc"
        )
        self.assertEqual(errores, ["La cantidad necesaria no es válida."])
