# Trabajo/tests/test_trabajo_integracion.py

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from Trabajo.models import OrdenMensuale, OrdenMensualDetalle, AportacionEmpleado
from Trabajo.admin import AportacionForm

from Sucursales.models import Sucursale, Caja
from Empleados.models import PerfilUsuario

from Materiales.models import CategoriasMateriale, UnidadesMedida, Materiale
from Muebles.models import CategoriasMueble, Tamaño, Mueble, MuebleMateriale
from Compras.models import InventarioMateriale


class OrdenMensualeCrudTest(TestCase):
    """CRUD de OrdenMensuale y verificación básica del método actualizar_estado()."""

    def setUp(self):
        self.sucursal = Sucursale.objects.create(
            codigo_sucursal="001",
            nombre="Sucursal Central",
            direccion="Col. Centro",
            telefono="99999999",
            rtn="0000-0000-000000",
        )

        self.orden = OrdenMensuale.objects.create(
            id_sucursal=self.sucursal,
            nombre="Orden Febrero",
            observaciones="Obs",
            fecha_fin=timezone.now().date() + timedelta(days=30),
            estado=OrdenMensuale.PEND,
        )

        # Dependencias mínimas para crear un detalle válido
        self.cat_mat = CategoriasMateriale.objects.create(
            nombre="Categoria Material",
            descripcion="Descripcion Material",
            imagen="ruta/imagen.png",
            imagen_url="",
        )
        self.medida = UnidadesMedida.objects.create(nombre="UnidadMed", abreviatura="UND")

        self.cat_mueble = CategoriasMueble.objects.create(
            nombre="Categoria Mueble",
            descripcion="Descripcion",
            imagen="ruta/imagen.png",
            imagen_url="",
        )
        self.tamano = Tamaño.objects.create(nombre="Grande", descripcion="Tamano grande")

        self.mueble = Mueble.objects.create(
            nombre="Silla Oficina",
            descripcion="Silla comoda",
            precio_base=1500.0,
            categoria=self.cat_mueble,
            medida=self.medida,
            alto=10.0,
            ancho=10.0,
            largo=10.0,
            tamano=self.tamano,
            Descontinuado=False,
            stock_minimo=5,
            stock_maximo=50,
            imagen="",
            imagen_url="",
        )

    def test_crear_orden_mensual_valida(self):
        """Valida que se pueda crear una OrdenMensuale con datos mínimos válidos."""
        orden = OrdenMensuale.objects.create(
            id_sucursal=self.sucursal,
            nombre="Orden Marzo",
            observaciones="",
            fecha_fin=timezone.now().date() + timedelta(days=15),
            estado=OrdenMensuale.PEND,
        )
        self.assertEqual(OrdenMensuale.objects.count(), 2)
        self.assertEqual(orden.id_sucursal, self.sucursal)
        self.assertEqual(orden.nombre, "Orden Marzo")
        self.assertEqual(orden.estado, OrdenMensuale.PEND)

    def test_editar_orden_mensual_modifica_nombre_y_actualiza_estado(self):
        """
        Valida que editar campos básicos funcione y que actualizar_estado()
        refleje el estado según los detalles.
        """
        self.orden.nombre = "Orden Febrero Editada"
        self.orden.save()

        orden_db = OrdenMensuale.objects.get(pk=self.orden.pk)
        self.assertEqual(orden_db.nombre, "Orden Febrero Editada")

        # Crear un detalle completo y forzar actualización de estado
        OrdenMensualDetalle.objects.create(
            id_orden=self.orden,
            id_mueble=self.mueble,
            cantidad_planificada=10,
            cantidad_producida=10,
            estado=OrdenMensualDetalle.COMP,
            entrega_estim=timezone.now().date() + timedelta(days=10),
        )

        self.orden.actualizar_estado()
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.estado, OrdenMensuale.COMP)

    def test_eliminar_orden_mensual_elimina_registro(self):
        """
        Valida eliminación de la orden.
        Nota: como los FK son DO_NOTHING, borramos detalles primero para evitar violación de FK.
        """
        detalle = OrdenMensualDetalle.objects.create(
            id_orden=self.orden,
            id_mueble=self.mueble,
            cantidad_planificada=5,
            cantidad_producida=0,
            estado=OrdenMensualDetalle.PEND,
            entrega_estim=None,
        )

        detalle.delete()
        self.orden.delete()

        self.assertEqual(OrdenMensuale.objects.filter(pk=self.orden.pk).count(), 0)
        self.assertEqual(OrdenMensualDetalle.objects.filter(pk=detalle.pk).count(), 0)


class OrdenMensualDetalleCrudTest(TestCase):
    """CRUD de OrdenMensualDetalle."""

    def setUp(self):
        self.sucursal = Sucursale.objects.create(
            codigo_sucursal="001",
            nombre="Sucursal Central",
            direccion="Col. Centro",
            telefono="99999999",
            rtn="0000-0000-000000",
        )

        self.orden = OrdenMensuale.objects.create(
            id_sucursal=self.sucursal,
            nombre="Orden Mensual",
            observaciones="",
            fecha_fin=timezone.now().date() + timedelta(days=30),
            estado=OrdenMensuale.PEND,
        )

        self.cat_mat = CategoriasMateriale.objects.create(
            nombre="Categoria Material",
            descripcion="Descripcion Material",
            imagen="ruta/imagen.png",
            imagen_url="",
        )
        self.medida = UnidadesMedida.objects.create(nombre="UnidadMed", abreviatura="UND")

        self.cat_mueble = CategoriasMueble.objects.create(
            nombre="Categoria Mueble",
            descripcion="Descripcion",
            imagen="ruta/imagen.png",
            imagen_url="",
        )
        self.tamano = Tamaño.objects.create(nombre="Grande", descripcion="Tamano grande")

        self.mueble = Mueble.objects.create(
            nombre="Mesa Comedor",
            descripcion="Mesa grande",
            precio_base=2500.0,
            categoria=self.cat_mueble,
            medida=self.medida,
            alto=100.0,
            ancho=80.0,
            largo=150.0,
            tamano=self.tamano,
            Descontinuado=False,
            stock_minimo=3,
            stock_maximo=30,
            imagen="",
            imagen_url="",
        )

        self.detalle = OrdenMensualDetalle.objects.create(
            id_orden=self.orden,
            id_mueble=self.mueble,
            cantidad_planificada=10,
            cantidad_producida=0,
            estado=OrdenMensualDetalle.PEND,
            entrega_estim=timezone.now().date() + timedelta(days=15),
        )

    def test_crear_detalle_orden_mensual_valido(self):
        """Valida que se pueda crear un detalle de orden mensual válido."""
        detalle2 = OrdenMensualDetalle.objects.create(
            id_orden=self.orden,
            id_mueble=self.mueble,
            cantidad_planificada=5,
            cantidad_producida=0,
            estado=OrdenMensualDetalle.PEND,
            entrega_estim=None,
        )
        self.assertEqual(OrdenMensualDetalle.objects.count(), 2)
        self.assertEqual(detalle2.id_orden, self.orden)
        self.assertEqual(detalle2.id_mueble, self.mueble)
        self.assertEqual(detalle2.cantidad_planificada, 5)

    def test_editar_detalle_modifica_cantidad_planificada(self):
        """Valida que se pueda editar la cantidad planificada de un detalle."""
        self.detalle.cantidad_planificada = 25
        self.detalle.save()

        detalle_db = OrdenMensualDetalle.objects.get(pk=self.detalle.pk)
        self.assertEqual(detalle_db.cantidad_planificada, 25)

    def test_eliminar_detalle_elimina_registro(self):
        """Valida que se elimine el detalle de forma correcta."""
        detalle_id = self.detalle.id
        self.detalle.delete()
        self.assertFalse(OrdenMensualDetalle.objects.filter(id=detalle_id).exists())


class AportacionEmpleadoFormCrudTest(TestCase):
    """CRUD/validaciones clave de AportacionEmpleado usando AportacionForm del admin."""

    def setUp(self):
        # Sucursal y caja para el perfil (no es requisito del AportacionForm, pero es parte real del sistema)
        self.sucursal = Sucursale.objects.create(
            codigo_sucursal="001",
            nombre="Sucursal Central",
            direccion="Col. Centro",
            telefono="99999999",
            rtn="0000-0000-000000",
        )
        self.caja = Caja.objects.create(sucursal=self.sucursal, codigo_caja="01", estado=True)

        # Usuario y perfil (se crea automático por signal)
        self.user = User.objects.create_user(username="empleado1", password="test12345")
        self.perfil = PerfilUsuario.objects.get(user=self.user)
        self.perfil.sucursal = self.sucursal
        self.perfil.caja = self.caja
        self.perfil.save()

        # Catálogos para mueble/material
        self.cat_mat = CategoriasMateriale.objects.create(
            nombre="Categoria Material",
            descripcion="Descripcion Material",
            imagen="ruta/imagen.png",
            imagen_url="",
        )
        self.medida = UnidadesMedida.objects.create(nombre="UnidadMed", abreviatura="UND")

        self.material = Materiale.objects.create(
            nombre="Madera Pino",
            imagen="ruta/imagen.png",
            stock_minimo=10,
            stock_maximo=500,
            categoria=self.cat_mat,
            imagen_url="",
            medida=self.medida,
        )

        self.cat_mueble = CategoriasMueble.objects.create(
            nombre="Categoria Mueble",
            descripcion="Descripcion",
            imagen="ruta/imagen.png",
            imagen_url="",
        )
        self.tamano = Tamaño.objects.create(nombre="Grande", descripcion="Tamano grande")

        self.mueble = Mueble.objects.create(
            nombre="Silla Oficina",
            descripcion="Silla comoda",
            precio_base=1500.0,
            categoria=self.cat_mueble,
            medida=self.medida,
            alto=10.0,
            ancho=10.0,
            largo=10.0,
            tamano=self.tamano,
            Descontinuado=False,
            stock_minimo=5,
            stock_maximo=50,
            imagen="",
            imagen_url="",
        )

        # Materiales por mueble (consumo)
        self.mm = MuebleMateriale.objects.create(
            id_material=self.material,
            id_mueble=self.mueble,
            cantidad=2,  # 2 unidades de material por mueble
        )

        # Orden y detalle
        self.orden = OrdenMensuale.objects.create(
            id_sucursal=self.sucursal,
            nombre="Orden Febrero",
            observaciones="",
            fecha_fin=timezone.now().date() + timedelta(days=30),
            estado=OrdenMensuale.PEND,
        )
        self.detalle = OrdenMensualDetalle.objects.create(
            id_orden=self.orden,
            id_mueble=self.mueble,
            cantidad_planificada=10,
            cantidad_producida=0,
            estado=OrdenMensualDetalle.PEND,
            entrega_estim=timezone.now().date() + timedelta(days=15),
        )

        # Inventario suficiente para pasar validación de materiales
        InventarioMateriale.objects.create(
            id_material=self.material,
            ubicación=self.sucursal,
            cantidad_disponible=999,
            cantidad_reservada=0,
            ultima_entrada=timezone.now().date(),
            ultima_salida=None,
            estado=None,
        )

    def test_crear_aportacion_valida_asigna_cant_aprobada(self):
        """Valida que AportacionForm permita crear aportación y asigne cant_aprobada = cantidad_solicitada."""
        data = {
            "orden_selector": self.orden.id,              # importante para que __init__ cargue queryset de detalles
            "id_orden_detalle": self.detalle.id,
            "id_empleado": self.perfil.id,
            "cantidad_solicitada": 4,
            "estado": AportacionEmpleado.PEND,
            # campos del modelo que pueden ir vacíos
            "cant_aprobada": "",
            "cantidad_finalizada": "",
            "materiales_reservados": "{}",
            "Aporte": 0,  # aunque esté disabled en UI, aquí lo mandamos en 0
        }

        form = AportacionForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

        aport = form.save()
        self.assertEqual(AportacionEmpleado.objects.count(), 1)
        self.assertEqual(aport.id_orden_detalle, self.detalle)
        self.assertEqual(aport.id_empleado, self.perfil)
        self.assertEqual(aport.cant_aprobada, 4)

    def test_crear_aportacion_falla_si_excede_disponible_planificado(self):
        """Valida que no permita solicitar más de lo disponible (planificada - asignado)."""
        # Ya hay 8 aprobadas sobre planificada 10 -> quedan 2
        AportacionEmpleado.objects.create(
            id_orden_detalle=self.detalle,
            id_empleado=self.perfil,
            cant_aprobada=8,
            cantidad_finalizada=0,
            estado=AportacionEmpleado.PEND,
            materiales_reservados={},
        )

        data = {
            "orden_selector": self.orden.id,
            "id_orden_detalle": self.detalle.id,
            "id_empleado": self.perfil.id,
            "cantidad_solicitada": 5,  # excede (solo quedan 2)
            "estado": AportacionEmpleado.PEND,
            "cant_aprobada": "",
            "cantidad_finalizada": "",
            "materiales_reservados": "{}",
            "Aporte": 0,
        }

        form = AportacionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())

    def test_crear_aportacion_falla_si_material_insuficiente_en_inventario(self):
        """Valida que falle si el inventario de materiales no cubre el consumo requerido."""
        # Ajustar inventario a un valor bajo
        invent = InventarioMateriale.objects.get(id_material=self.material, ubicación=self.sucursal)
        invent.cantidad_disponible = 5
        invent.save()

        # consumo = cantidad_solicitada(4) * mm.cantidad(2) = 8 > 5
        data = {
            "orden_selector": self.orden.id,
            "id_orden_detalle": self.detalle.id,
            "id_empleado": self.perfil.id,
            "cantidad_solicitada": 4,
            "estado": AportacionEmpleado.PEND,
            "cant_aprobada": "",
            "cantidad_finalizada": "",
            "materiales_reservados": "{}",
            "Aporte": 0,
        }

        form = AportacionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())