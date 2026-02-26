from datetime import date

from django.test import TestCase

from Compras.models import *
from Compras.admin import *
from Sucursales.models import Sucursale
from Muebles.models import CategoriasMueble, Mueble, Tamaño
from clientes.models import Cliente
from Materiales.models import *
from django.utils import timezone
from django.db import transaction
from Sucursales.models import Sucursale
from Materiales.models import HistorialPrecio

class InventarioMueblesCrudTest(TestCase):
    def setUp(self):
        self.estado_disponible = Estados.objects.create(tipo='Disponible')

        self.categoria = CategoriasMueble.objects.create(nombre='Sillas', descripcion='Sillas de diferentes tipos')

        self.medida = UnidadesMedida.objects.create(nombre='Unidad', abreviatura='ud')

        self.tamano = Tamaño.objects.create(nombre='Mediano', descripcion='Tamaño mediano para muebles')
        
        self.mueble = Mueble.objects.create(
            nombre='Silla de Madera',
            descripcion='Silla de madera maciza con diseño clásico.',
            precio_base=150.00,
            categoria=self.categoria,
            medida=self.medida,
            alto=10.0,
            ancho=10.0,
            largo=10.0,
            tamano=self.tamano,
            Descontinuado=False,
            stock_minimo=1,
            stock_maximo=100,
        )

        self.ubicación = Sucursale.objects.create(
            codigo_sucursal='001',
            nombre='Sucursal Central',
            direccion='Avenida Principal 123',
            telefono='98761234',
        )
    

        self.inventario_inicial = InventarioMueble.objects.create(
            id_mueble=self.mueble,
            cantidad_disponible=20,
            estado=self.estado_disponible,
            ubicación=self.ubicación
            )
        
    def test_crear_inventario_mueble_valido(self):
        form_vacio = InventarioForm()
        estado_campo = form_vacio.fields['estado']
        estado_valido = estado_campo.queryset.first()
        form_data = {
            'id_mueble': self.mueble.id,
            'cantidad_disponible': 50,
            'estado': estado_valido.id,
            'ubicación': self.ubicación.id,
        }

        form = InventarioForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

        inventario = form.save()

        self.assertEqual(InventarioMueble.objects.count(), 2)
        self.assertEqual(inventario.id_mueble, self.mueble)
        self.assertEqual(inventario.cantidad_disponible, 50)
        self.assertEqual(inventario.estado, estado_valido)
        self.assertEqual(inventario.ubicación, self.ubicación)

    def test_editar_inventario_mueble_valido(self):
        estado_bajo = Estados.objects.create(tipo='Bajo Stock')

        form_data = {
            'id_mueble': self.mueble.id,
            'cantidad_disponible': 5,
            'estado': estado_bajo.id,
            'ubicación': self.ubicación.id,
        }

        form = InventarioForm(data=form_data, instance=self.inventario_inicial)
        self.assertTrue(form.is_valid(), form.errors)

        inventario_editado = form.save()

        self.assertEqual(InventarioMueble.objects.count(), 1)
        self.assertEqual(inventario_editado.id_mueble, self.mueble)
        self.assertEqual(inventario_editado.cantidad_disponible, 5)
        self.assertEqual(inventario_editado.estado, estado_bajo)
        self.assertEqual(inventario_editado.ubicación, self.ubicación)

    def test_eliminar_inventario_mueble(self):
        self.assertEqual(InventarioMueble.objects.count(), 1)

        self.inventario_inicial.delete()

        self.assertEqual(InventarioMueble.objects.count(), 0)

from django.test import TestCase
from Compras.models import Estados


class EstadosCrudTest(TestCase):

    def setUp(self):
        # Estado inicial para pruebas de edición y eliminación
        self.estado = Estados.objects.create(tipo='Disponible')

    def test_crear_estado_valido(self):
        
        self.assertEqual(Estados.objects.count(), 1)

        estado = self.estado
        self.assertEqual(estado.tipo, 'Disponible')
        self.assertEqual(str(estado), 'Disponible')

    def test_editar_estado(self):
        
        self.estado.tipo = 'Bajo stock'
        self.estado.save()

        estado_editado = Estados.objects.get(pk=self.estado.pk)

        self.assertEqual(estado_editado.tipo, 'Bajo stock')
        self.assertEqual(str(estado_editado), 'Bajo stock')

    def test_eliminar_estado(self):
        
        self.assertEqual(Estados.objects.count(), 1)

        self.estado.delete()

        self.assertEqual(Estados.objects.count(), 0)

class CotizacionesCrudTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre="Cliente de Prueba",
            rtn="0801199900000",
            telefono="98765432",
            direccion="Col. Centro"
        )

        self.cotizacion = Cotizacione.objects.create(
            cliente=self.cliente,
            fecha_vencimiento=date.today() + timedelta(days=15),
            subtotal=1000.0,
            isv=150.0,
            total=1150.0,
        )

    def test_crear_cotizacion_valida(self):
        
        self.assertEqual(Cotizacione.objects.count(), 1)

        cot = self.cotizacion
        self.assertEqual(cot.cliente, self.cliente)
        self.assertTrue(cot.activo)
        self.assertEqual(cot.subtotal, 1000.0)
        self.assertEqual(cot.isv, 150.0)
        self.assertEqual(cot.total, 1150.0)

        
        self.assertEqual(str(cot), str(self.cliente))

    def test_editar_cotizacion(self):
        
        nueva_fecha = date.today() + timedelta(days=20)

        self.cotizacion.activo = False
        self.cotizacion.subtotal = 2000.0
        self.cotizacion.isv = 300.0
        self.cotizacion.total = 2300.0
        self.cotizacion.fecha_vencimiento = nueva_fecha
        self.cotizacion.save()

        cot_refrescada = Cotizacione.objects.get(pk=self.cotizacion.id)

        self.assertFalse(cot_refrescada.activo)
        self.assertEqual(cot_refrescada.subtotal, 2000.0)
        self.assertEqual(cot_refrescada.isv, 300.0)
        self.assertEqual(cot_refrescada.total, 2300.0)
        self.assertEqual(cot_refrescada.fecha_vencimiento, nueva_fecha)

    def test_eliminar_cotizacion(self):
        
        self.assertEqual(Cotizacione.objects.count(), 1)

        self.cotizacion.delete()

        self.assertEqual(Cotizacione.objects.count(), 0)

class DetalleCotizacionesCrudTest(TestCase):
    def setUp(self):
        # ----- Cliente base -----
        self.cliente = Cliente.objects.create(
            nombre="Cliente Detalle Test",
            rtn="0801199900001",
            telefono="99998888",
            direccion="Col. Detalle"
        )

        # ----- Cotización base -----
        self.cotizacion = Cotizacione.objects.create(
            cliente=self.cliente,
            fecha_vencimiento=date.today() + timedelta(days=10),
            subtotal=0.0,
            isv=0.0,
            total=0.0,
        )

        # ----- Datos base para un Mueble -----
        self.categoria = CategoriasMueble.objects.create(
            nombre='Sillas',
            descripcion='Sillas varias',
            imagen='',
            imagen_url=''
        )

        self.medida = UnidadesMedida.objects.create(
            nombre='Unidad',
            abreviatura='ud'
        )

        self.tamano = Tamaño.objects.create(
            nombre='Mediano',
            descripcion='Mueble mediano'
        )

        self.mueble = Mueble.objects.create(
            nombre='Silla Estándar',
            descripcion='Silla estándar para comedor',
            precio_base=500.0,
            categoria=self.categoria,
            medida=self.medida,
            alto=1.0,
            ancho=1.0,
            largo=1.0,
            tamano=self.tamano,
            Descontinuado=False,
            stock_minimo=1,
            stock_maximo=100,
        )

        # ----- Detalle de cotización base -----
        self.detalle = DetalleCotizaciones.objects.create(
            id_cotizacion=self.cotizacion,
            id_mueble=self.mueble,
            cantidad=2,
            precio_unitario=500.0,
            subtotal=1000.0,
        )

    def test_crear_detalle_cotizacion_valido(self):

        self.assertEqual(DetalleCotizaciones.objects.count(), 1)

        det = self.detalle
        self.assertEqual(det.id_cotizacion, self.cotizacion)
        self.assertEqual(det.id_mueble, self.mueble)
        self.assertEqual(det.cantidad, 2)
        self.assertEqual(det.precio_unitario, 500.0)
        self.assertEqual(det.subtotal, 1000.0)

        self.assertEqual(str(det), str(self.cotizacion))

    def test_editar_detalle_cotizacion(self):
        """
        Probar actualización de cantidad, precio y subtotal
        de un detalle de cotización.
        """
        self.detalle.cantidad = 3
        self.detalle.precio_unitario = 450.0
        self.detalle.subtotal = 1350.0  # 3 * 450
        self.detalle.save()

        det_refrescado = DetalleCotizaciones.objects.get(pk=self.detalle.pk)

        self.assertEqual(det_refrescado.cantidad, 3)
        self.assertEqual(det_refrescado.precio_unitario, 450.0)
        self.assertEqual(det_refrescado.subtotal, 1350.0)

    def test_eliminar_detalle_cotizacion(self):
        """
        Probar que el detalle se elimina correctamente
        sin eliminar la cotización padre.
        """
        self.assertEqual(DetalleCotizaciones.objects.count(), 1)
        self.assertEqual(Cotizacione.objects.count(), 1)

        self.detalle.delete()

        self.assertEqual(DetalleCotizaciones.objects.count(), 0)
        # La cotización debe seguir existiendo
        self.assertEqual(Cotizacione.objects.count(), 1)

class ListaCompraCrudTest(TestCase):
    def setUp(self):
        # Crear una sucursal base para asociar a la lista
        self.sucursal = Sucursale.objects.create(
            codigo_sucursal="001",
            nombre="Sucursal Central",
            direccion="Avenida Principal 123",
            telefono="98761234",
        )

        # Crear una lista de compra inicial (estado pendiente, sin fecha_entrega)
        self.lista = ListaCompra.objects.create(
            sucursal=self.sucursal,
            prioridad=ALTA,  # usa la constante definida en Compras.models
            estado=ListaCompra.PENDIENTE,
        )

    def test_crear_lista_compra_valida(self):
        """Verifica que la lista de compra inicial se creó correctamente."""
        self.assertEqual(ListaCompra.objects.count(), 1)

        lista = self.lista

        # Sucursal asociada correctamente
        self.assertEqual(lista.sucursal, self.sucursal)

        # Prioridad y estado correctos
        self.assertEqual(lista.prioridad, ALTA)
        self.assertEqual(lista.estado, ListaCompra.PENDIENTE)

        # fecha_solicitud se asigna por auto_now_add
        self.assertIsNotNone(lista.fecha_solicitud)

        # Como no está COMPLETA, no debe tener fecha_entrega
        self.assertIsNone(lista.fecha_entrega)

        # __str__ debe devolver "Orden <id>"
        self.assertEqual(str(lista), f"Orden {lista.id}")

    def test_editar_lista_compra_cambiar_estado_y_fecha_entrega(self):
        """
        Si el estado pasa a COMPLETA, se debe llenar fecha_entrega.
        Si luego vuelve a un estado diferente, se debe limpiar fecha_entrega.
        """
        # Cambiar a COMPLETA
        self.lista.estado = ListaCompra.COMPLETA
        self.lista.save()

        lista_refrescada = ListaCompra.objects.get(pk=self.lista.id)

        self.assertEqual(lista_refrescada.estado, ListaCompra.COMPLETA)
        self.assertIsNotNone(lista_refrescada.fecha_entrega)

        # Guardar la fecha para asegurarnos que luego cambie
        fecha_entrega_inicial = lista_refrescada.fecha_entrega

        # Cambiar a PENDIENTE de nuevo
        lista_refrescada.estado = ListaCompra.PENDIENTE
        lista_refrescada.save()
        lista_refrescada.refresh_from_db()

        self.assertEqual(lista_refrescada.estado, ListaCompra.PENDIENTE)
        # Por la lógica de save, fecha_entrega debe volver a None
        self.assertIsNone(lista_refrescada.fecha_entrega)

        # Aseguramos que realmente cambió (no se quedó con la fecha anterior)
        self.assertNotEqual(fecha_entrega_inicial, lista_refrescada.fecha_entrega)

    def test_eliminar_lista_compra(self):
        """Probar que la lista de compra se elimina correctamente."""
        self.assertEqual(ListaCompra.objects.count(), 1)

        self.lista.delete()

        self.assertEqual(ListaCompra.objects.count(), 0)


class RequerimientoMaterialeCrudTest(TestCase):
    def setUp(self):
        # --------- Catálogo de Materiales ---------
        self.categoria = CategoriasMateriale.objects.create(
            nombre="Maderas",
            descripcion="Materiales de madera",
            imagen="categorias/maderas.png",
            imagen_url="http://testserver/media/categorias/maderas.png",
        )

        self.unidad = UnidadesMedida.objects.create(
            nombre="Unidad",
            abreviatura="ud",
        )

        self.material = Materiale.objects.create(
            nombre="Madera Pino",
            imagen="materiales/madera_pino.png",
            stock_minimo=10,
            stock_maximo=100,
            categoria=self.categoria,
            imagen_url="http://testserver/media/materiales/madera_pino.png",
            medida=self.unidad,
        )

        # --------- Estado de personas / Proveedor ---------
        self.estado_persona_activo = EstadosPersonas.objects.create(
            tipo="Activo"
        )

        self.proveedor = Proveedore.objects.create(
            compañia="Proveedor Demo",
            nombre="Juan Proveedor",
            telefono="98761234",
            email="proveedor@demo.com",
            estado=self.estado_persona_activo,
        )

        # --------- Lista de compra base ---------
        self.lista = ListaCompra.objects.create(
            sucursal=None,
            prioridad=ALTA,
            estado=ListaCompra.PENDIENTE,
        )

        # --------- Relación Material–Proveedor (para evitar errores en get_or_create) ---------
        self.relacion_mp = MaterialProveedore.objects.create(
            material=self.material,
            id_proveedor=self.proveedor,
            precio_actual=50.0,
            tiempo=7,
            unidad_tiempo=MaterialProveedore.DIAS,
            comentarios="Relación inicial de prueba",
        )

        # --------- Requerimiento inicial ---------
        self.requerimiento = RequerimientoMateriale.objects.create(
            material=self.material,
            proveedor=self.proveedor,
            cantidad_necesaria=20,
            motivo=RequerimientoMateriale.REPO,
            prioridad=ALTA,
            precio_actual=50.0,
            subtotal=1000.0,
            id_lista=self.lista,
        )

    # ----------------------------------------------------------------------
    def test_crear_requerimiento_materiale_valido(self):
        """Debe crearse correctamente el requerimiento y mantenerse la relación material–proveedor."""
        self.assertEqual(RequerimientoMateriale.objects.count(), 1)

        req = self.requerimiento
        self.assertEqual(req.material, self.material)
        self.assertEqual(req.proveedor, self.proveedor)
        self.assertEqual(req.cantidad_necesaria, 20)
        self.assertEqual(req.precio_actual, 50.0)
        self.assertEqual(req.subtotal, 1000.0)
        self.assertEqual(req.id_lista, self.lista)

        # La relación Material–Proveedor existe y tiene el precio esperado
        rel = MaterialProveedore.objects.get(material=self.material, id_proveedor=self.proveedor)
        self.assertEqual(rel.precio_actual, 50.0)

    # ----------------------------------------------------------------------
    def test_editar_requerimiento_materiale_cambia_precio_y_historial(self):
        """
        Al cambiar precio_actual en el requerimiento:
        - Debe actualizarse la relación MaterialProveedore
        - Debe existir exactamente un historial activo (fecha_fin NULL)
        - Ese historial activo debe tener el nuevo precio
        - Los historiales anteriores deben quedar cerrados
        """
        nuevo_precio = 60.0

        # ACT: cambiar precio en el requerimiento
        self.requerimiento.precio_actual = nuevo_precio
        self.requerimiento.save()

        # ASSERT 1: la relación material-proveedor tiene el nuevo precio
        rel = MaterialProveedore.objects.get(
            material=self.material,
            id_proveedor=self.proveedor
        )
        self.assertEqual(rel.precio_actual, nuevo_precio)

        # ASSERT 2: historiales asociados
        historiales = HistorialPrecio.objects.filter(
            material=self.material,
            proveedor=self.proveedor
        )
        # Debe haber al menos 1 historial (el actual)
        self.assertGreaterEqual(historiales.count(), 1)

        # Historial activo (fecha_fin = NULL)
        historiales_activos = historiales.filter(fecha_fin__isnull=True)
        self.assertEqual(
            historiales_activos.count(),
            1,
            "Debe haber exactamente un historial activo"
        )
        historial_activo = historiales_activos.first()
        self.assertEqual(historial_activo.precio, nuevo_precio)

        # (Opcional pero bonito) – todos los demás historiales deben estar cerrados
        for h in historiales.exclude(id=historial_activo.id):
            self.assertIsNotNone(
                h.fecha_fin,
                "Los historiales antiguos deben tener fecha_fin distinta de NULL"
            )

    # ----------------------------------------------------------------------
    def test_eliminar_requerimiento_materiale(self):
        """
        Eliminar el requerimiento no debe eliminar:
        - el Material
        - el Proveedor
        - la relación MaterialProveedore
        """
        req_id = self.requerimiento.id
        mat_id = self.material.id
        prov_id = self.proveedor.id
        rel_id = self.relacion_mp.id

        self.requerimiento.delete()

        self.assertFalse(RequerimientoMateriale.objects.filter(id=req_id).exists())
        self.assertTrue(Materiale.objects.filter(id=mat_id).exists())
        self.assertTrue(Proveedore.objects.filter(id=prov_id).exists())
        self.assertTrue(MaterialProveedore.objects.filter(id=rel_id).exists())

class InventarioMaterialeCrudTest(TestCase):
    def setUp(self):
        # Estado "Disponible" para usar en inventarios
        self.estado_disponible = Estados.objects.create(tipo="Disponible")

        # Estado de personas para proveedor
        self.estado_persona_activo = EstadosPersonas.objects.create(tipo="Activo")

        # Cat. material
        self.categoria = CategoriasMateriale.objects.create(
            nombre="Maderas",
            descripcion="Materiales de madera",
            imagen="maderas.png",
            imagen_url="",
        )

        # Unidad de medida
        self.unidad = UnidadesMedida.objects.create(
            nombre="Unidad",
            abreviatura="ud",
        )

        # Material base
        self.material = Materiale.objects.create(
            nombre="Madera Pino",
            imagen="madera_pino.png",
            stock_minimo=5,
            stock_maximo=100,
            categoria=self.categoria,
            imagen_url="",
            medida=self.unidad,
        )

        # Ubicación / sucursal
        self.ubicacion = Sucursale.objects.create(
            codigo_sucursal="001",
            nombre="Sucursal Central",
            direccion="Avenida Principal 123",
            telefono="98761234",
        )

        # Inventario inicial del material
        self.inventario_inicial = InventarioMateriale.objects.create(
            id_material=self.material,
            cantidad_disponible=20,
            estado=self.estado_disponible,
            ubicación=self.ubicacion,
            ultima_entrada=timezone.now().date(),
        )

    def test_crear_inventario_material_valido(self):
        """
        Debe crearse correctamente un nuevo registro de inventario de material
        usando el formulario del admin (InventarioMForm).
        """
        form_data = {
            "id_material": self.material.id,
            "cantidad_disponible": 50,  # menor o igual a stock_maximo
            "estado": self.estado_disponible.id,
            "ubicación": self.ubicacion.id,
            "cantidad_reservada": 0,
            "ultima_entrada": "",
            "ultima_salida": "",
        }

        form = InventarioMForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

        inventario_nuevo = form.save()

        self.assertEqual(InventarioMateriale.objects.count(), 2)
        self.assertEqual(inventario_nuevo.id_material, self.material)
        self.assertEqual(inventario_nuevo.cantidad_disponible, 50)
        self.assertEqual(inventario_nuevo.estado, self.estado_disponible)
        self.assertEqual(inventario_nuevo.ubicación, self.ubicacion)

    def test_editar_inventario_material_actualiza_cantidad_y_estado(self):
        """
        Al editar un inventario existente mediante el formulario,
        debe actualizarse la cantidad_disponible y el estado correctamente.
        """
        # Creamos otro estado para probar el cambio
        estado_bajo_stock = Estados.objects.create(tipo="Bajo Stock")

        form_data = {
            "id_material": self.material.id,
            "cantidad_disponible": 80,  # sigue <= stock_maximo
            "estado": estado_bajo_stock.id,
            "ubicación": self.ubicacion.id,
            "cantidad_reservada": self.inventario_inicial.cantidad_reservada
            if self.inventario_inicial.cantidad_reservada is not None
            else 0,
            "ultima_entrada": self.inventario_inicial.ultima_entrada
            or "",
            "ultima_salida": self.inventario_inicial.ultima_salida
            or "",
        }

        form = InventarioMForm(data=form_data, instance=self.inventario_inicial)
        self.assertTrue(form.is_valid(), form.errors)

        inventario_editado = form.save()
        self.inventario_inicial.refresh_from_db()

        self.assertEqual(inventario_editado.id, self.inventario_inicial.id)
        self.assertEqual(self.inventario_inicial.cantidad_disponible, 80)
        self.assertEqual(self.inventario_inicial.estado, estado_bajo_stock)

    def test_crear_inventario_material_rechaza_cantidad_mayor_a_stock_maximo(self):
        """
        El formulario debe marcar error si la cantidad_disponible
        excede el stock_maximo del material.
        """
        cantidad_invalida = self.material.stock_maximo + 10

        form_data = {
            "id_material": self.material.id,
            "cantidad_disponible": cantidad_invalida,
            "estado": self.estado_disponible.id,
            "ubicación": self.ubicacion.id,
            "cantidad_reservada": 0,
            "ultima_entrada": "",
            "ultima_salida": "",
        }

        form = InventarioMForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("cantidad_disponible", form.errors)
        self.assertIn(
            f"La cantidad no puede exceder el stock máximo de {self.material.stock_maximo}",
            form.errors["cantidad_disponible"][0],
        )

    def test_eliminar_inventario_material_no_elimina_material(self):
        """
        Al eliminar un registro de inventario, el material asociado debe permanecer.
        """
        self.assertEqual(InventarioMateriale.objects.count(), 1)
        self.assertEqual(Materiale.objects.count(), 1)

        self.inventario_inicial.delete()

        self.assertEqual(InventarioMateriale.objects.count(), 0)
        # El material sigue existiendo
        self.assertEqual(Materiale.objects.count(), 1)
        self.assertTrue(Materiale.objects.filter(id=self.material.id).exists())