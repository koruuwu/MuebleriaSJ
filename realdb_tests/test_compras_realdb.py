# realdb_tests/test_compras_realdb.py
from uuid import uuid4
from django.test import SimpleTestCase

from clientes.models import Cliente
from Sucursales.models import Sucursale

from Compras.models import (
    Cotizacione,
    DetalleCotizaciones,
    ListaCompra,
    RequerimientoMateriale,
    DetalleRecibido,
    InventarioMateriale,
    InventarioMueble,
    Estados,  # Estados_M en DB
    MaterialProveedore,
)

from Materiales.models import (
    CategoriasMateriale,
    UnidadesMedida,
    Materiale,
    EstadosPersonas,
    Proveedore,
    HistorialPrecio,  # Historial_Precios
)

from Muebles.models import (
    CategoriasMueble,
    Tamaño,
    Mueble,
    HistorialPreciosMueble,  # Historial_Precios_muebles
)


class ComprasRealDBTests(SimpleTestCase):
    
    databases = {"default"}

    def setUp(self):
        # uuid4 solo genera un sufijo único para que no choque con otros runs
        self.tag = f"test_{uuid4().hex[:8]}"

        self.created = {
            "clientes": [],
            "sucursales": [],
            "cotizaciones": [],
            "detalle_cotizaciones": [],
            "listas_compra": [],
            "cats_mat": [],
            "materiales": [],
            "estados_personas": [],
            "proveedores": [],
            "reqs": [],
            "material_proveedor": [],
            "hist_precios": [],
            "detalle_recibido": [],
            "inventario_material": [],
            "cats_mueble": [],
            "tamano": [],
            "muebles": [],
            "inventario_mueble": [],
            "estados_m": [],
            "unidades_medida": [],  # <-- FALTABA
        }

    def tearDown(self):
        
        # 1) Historiales que bloquean deletes por FK
        if self.created["muebles"]:
            HistorialPreciosMueble.objects.filter(
                id_mueble_id__in=self.created["muebles"]
            ).delete()

        # HistorialPrecio puede referenciar material y/o proveedor
        if self.created["materiales"] or self.created["proveedores"]:
            q = HistorialPrecio.objects.all()
            if self.created["proveedores"]:
                q = q.filter(proveedor_id__in=self.created["proveedores"])
            if self.created["materiales"]:
                q = q | HistorialPrecio.objects.filter(material_id__in=self.created["materiales"])
            q.delete()

        # 2) Detalles / dependientes
        if self.created["detalle_cotizaciones"]:
            DetalleCotizaciones.objects.filter(id__in=self.created["detalle_cotizaciones"]).delete()

        if self.created["reqs"]:
            RequerimientoMateriale.objects.filter(id__in=self.created["reqs"]).delete()

        if self.created["detalle_recibido"]:
            DetalleRecibido.objects.filter(id__in=self.created["detalle_recibido"]).delete()

        if self.created["inventario_mueble"]:
            InventarioMueble.objects.filter(id__in=self.created["inventario_mueble"]).delete()

        if self.created["inventario_material"]:
            InventarioMateriale.objects.filter(id__in=self.created["inventario_material"]).delete()

        if self.created["cotizaciones"]:
            Cotizacione.objects.filter(id__in=self.created["cotizaciones"]).delete()

        if self.created["listas_compra"]:
            ListaCompra.objects.filter(id__in=self.created["listas_compra"]).delete()

        # 3) Relaciones “puente”
        if self.created["material_proveedor"]:
            MaterialProveedore.objects.filter(id__in=self.created["material_proveedor"]).delete()

        # 4) “Padres”
        if self.created["muebles"]:
            Mueble.objects.filter(id__in=self.created["muebles"]).delete()

        if self.created["materiales"]:
            Materiale.objects.filter(id__in=self.created["materiales"]).delete()

        if self.created["proveedores"]:
            Proveedore.objects.filter(id__in=self.created["proveedores"]).delete()

        if self.created["tamano"]:
            Tamaño.objects.filter(id__in=self.created["tamano"]).delete()

        if self.created["cats_mueble"]:
            CategoriasMueble.objects.filter(id__in=self.created["cats_mueble"]).delete()

        if self.created["cats_mat"]:
            CategoriasMateriale.objects.filter(id__in=self.created["cats_mat"]).delete()

        if self.created["unidades_medida"]:
            UnidadesMedida.objects.filter(id__in=self.created["unidades_medida"]).delete()

        if self.created["sucursales"]:
            Sucursale.objects.filter(id__in=self.created["sucursales"]).delete()

        if self.created["clientes"]:
            Cliente.objects.filter(id__in=self.created["clientes"]).delete()

        if self.created["estados_m"]:
            Estados.objects.filter(id__in=self.created["estados_m"]).delete()

        if self.created["estados_personas"]:
            EstadosPersonas.objects.filter(id__in=self.created["estados_personas"]).delete()

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _mk_um(self):
        um = UnidadesMedida.objects.first()
        if um:
            return um
        um = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="un")
        self.created["unidades_medida"].append(um.id)
        return um

    def _mk_cliente(self):
        c = Cliente.objects.create(
            nombre=f"{self.tag}_cliente",
            telefono="99999999",
            direccion="Direccion test",
            rtn=None,
        )
        self.created["clientes"].append(c.id)
        return c

    def _mk_sucursal(self):
        s = Sucursale.objects.create(
            codigo_sucursal="001",
            nombre=f"{self.tag}_sucursal",
            direccion="Direccion test",
            telefono="99999999",
            rtn=None,
        )
        self.created["sucursales"].append(s.id)
        return s

    def _mk_lista_compra(self):
        s = self._mk_sucursal()
        lc = ListaCompra.objects.create(
            sucursal=s,
            prioridad="alta",
            estado="pendiente",
        )
        self.created["listas_compra"].append(lc.id)
        return lc, s

    def _mk_categoria_material(self):
        cat = CategoriasMateriale.objects.create(
            nombre=f"{self.tag}_cat_mat",
            descripcion="cat mat test",
            imagen="x",
            imagen_url=None,
        )
        self.created["cats_mat"].append(cat.id)
        return cat

    def _mk_material(self):
        um = self._mk_um()
        cat = self._mk_categoria_material()
        m = Materiale.objects.create(
            nombre=f"{self.tag}_material",
            imagen="x",
            stock_minimo=10,
            stock_maximo=100,
            categoria=cat,
            imagen_url=None,
            medida=um,
        )
        self.created["materiales"].append(m.id)
        return m

    def _mk_estado_persona(self):
        ep = EstadosPersonas.objects.first()
        if ep:
            return ep
        ep = EstadosPersonas.objects.create(tipo=f"{self.tag}_estado_persona")
        self.created["estados_personas"].append(ep.id)
        return ep

    def _mk_proveedor(self):
        ep = self._mk_estado_persona()
        p = Proveedore.objects.create(
            compañia=f"{self.tag}_comp",
            nombre="Proveedor Test",
            telefono="99999999",
            email="test@test.com",
            estado=ep,
        )
        self.created["proveedores"].append(p.id)
        return p

    def _mk_categoria_mueble(self):
        cat = CategoriasMueble.objects.create(
            nombre=f"{self.tag}_cat_mueble",
            descripcion="cat mueble test",
            imagen="x",
            imagen_url=None,
        )
        self.created["cats_mueble"].append(cat.id)
        return cat

    def _mk_tamano(self):
        t = Tamaño.objects.create(nombre=f"{self.tag}_tam", descripcion="tam test")
        self.created["tamano"].append(t.id)
        return t

    def _mk_mueble(self):
        um = self._mk_um()
        cat = self._mk_categoria_mueble()
        tam = self._mk_tamano()
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

    def _mk_estado_m_disponible(self):
        est = Estados.objects.filter(id=1).first() or Estados.objects.filter(tipo__icontains="Disponible").first()
        if est:
            return est
        est = Estados.objects.create(tipo="Disponible")
        self.created["estados_m"].append(est.id)
        return est

    def _ensure_estados_base(self):
        for idx, tipo in [(1, "Disponible"), (2, "Bajo Stock"), (3, "Agotado"), (4, "Descontinuado")]:
            if not Estados.objects.filter(id=idx).exists():
                try:
                    Estados.objects.create(id=idx, tipo=tipo)
                except Exception:
                    pass

    # ---------------------------------------------------------------------
    # 1) Cotizaciones CRUD
    # ---------------------------------------------------------------------

    def test_01_cotizaciones_crud_realdb(self):
        cliente = self._mk_cliente()

        cot = Cotizacione.objects.create(
            activo=True,
            fecha_vencimiento="2099-12-31",
            cliente=cliente,
            subtotal=100.0,
            isv=15.0,
            total=115.0,
        )
        self.created["cotizaciones"].append(cot.id)
        self.assertIsNotNone(cot.id)

        cot.total = 200.0
        cot.save(update_fields=["total"])
        self.assertEqual(float(Cotizacione.objects.get(id=cot.id).total), 200.0)

        cid = cot.id
        cot.delete()
        self.assertFalse(Cotizacione.objects.filter(id=cid).exists())

    # ---------------------------------------------------------------------
    # 2) DetalleCotizaciones CRUD
    # ---------------------------------------------------------------------

    def test_02_detalle_cotizaciones_crud_realdb(self):
        cliente = self._mk_cliente()
        cot = Cotizacione.objects.create(
            activo=True,
            fecha_vencimiento="2099-12-31",
            cliente=cliente,
            subtotal=100.0,
            isv=15.0,
            total=115.0,
        )
        self.created["cotizaciones"].append(cot.id)

        mueble = self._mk_mueble()

        det = DetalleCotizaciones.objects.create(
            id_cotizacion=cot,
            id_mueble=mueble,
            cantidad=2,
            precio_unitario=100.0,
            subtotal=200.0,
        )
        self.created["detalle_cotizaciones"].append(det.id)
        self.assertIsNotNone(det.id)

        det.cantidad = 3
        det.subtotal = 300.0
        det.save(update_fields=["cantidad", "subtotal"])
        det_ref = DetalleCotizaciones.objects.get(id=det.id)
        self.assertEqual(det_ref.cantidad, 3)
        self.assertEqual(float(det_ref.subtotal), 300.0)

        did = det.id
        det.delete()
        self.assertFalse(DetalleCotizaciones.objects.filter(id=did).exists())

    # ---------------------------------------------------------------------
    # 3) ListaCompra CRUD
    # ---------------------------------------------------------------------

    def test_03_lista_compra_crud_realdb(self):
        lista, _ = self._mk_lista_compra()
        self.assertIsNotNone(lista.id)

        lista.estado = "aprobada"
        lista.save(update_fields=["estado"])
        self.assertEqual(ListaCompra.objects.get(id=lista.id).estado, "aprobada")

        lid = lista.id
        lista.delete()
        self.assertFalse(ListaCompra.objects.filter(id=lid).exists())

    # ---------------------------------------------------------------------
    # 4) RequerimientoMateriale CRUD + relación + historial
    # ---------------------------------------------------------------------

    def test_04_requerimiento_material_crud_realdb(self):
        lista, _ = self._mk_lista_compra()
        material = self._mk_material()
        proveedor = self._mk_proveedor()

        req = RequerimientoMateriale.objects.create(
            material=material,
            proveedor=proveedor,
            cantidad_necesaria=5,
            motivo="reposicion stock",
            prioridad="alta",
            precio_actual=20.0,
            subtotal=0.0,
            id_lista=lista,
        )
        self.created["reqs"].append(req.id)

        req_ref = RequerimientoMateriale.objects.get(id=req.id)
        self.assertEqual(float(req_ref.subtotal), 5.0 * 20.0)

        rel = MaterialProveedore.objects.filter(material=material, id_proveedor=proveedor).first()
        self.assertIsNotNone(rel)
        self.created["material_proveedor"].append(rel.id)

        req.precio_actual = 25.0
        req.save()

        rel2 = MaterialProveedore.objects.filter(material=material, id_proveedor=proveedor).first()
        self.assertIsNotNone(rel2)
        self.assertEqual(float(rel2.precio_actual), 25.0)

        hist = HistorialPrecio.objects.filter(material=material, proveedor=proveedor).order_by("-fecha_inicio").first()
        self.assertIsNotNone(hist)
        self.created["hist_precios"].append(hist.id)

        rid = req.id
        req.delete()
        self.assertFalse(RequerimientoMateriale.objects.filter(id=rid).exists())

    # ---------------------------------------------------------------------
    # 5) DetalleRecibido CRUD + inventario + estado lista
    # ---------------------------------------------------------------------

    def test_05_detalle_recibido_crud_realdb(self):
        self._ensure_estados_base()

        lista, suc = self._mk_lista_compra()
        material = self._mk_material()

        det = DetalleRecibido.objects.create(
            orden=lista,
            product=material,
            cantidad_ord=10,
            aporte=5,
            cantidad_recibida=None,
            estado_item="completo",
        )
        self.created["detalle_recibido"].append(det.id)

        det_ref = DetalleRecibido.objects.get(id=det.id)
        self.assertEqual(det_ref.cantidad_recibida, 5)
        self.assertEqual(det_ref.aporte, 0)

        inv = InventarioMateriale.objects.filter(id_material=material, ubicación=suc).first()
        self.assertIsNotNone(inv)
        self.created["inventario_material"].append(inv.id)
        self.assertEqual(inv.cantidad_disponible, 5)

        lista_ref = ListaCompra.objects.get(id=lista.id)
        self.assertEqual(lista_ref.estado, ListaCompra.COMPLETA)

        det.aporte = 3
        det.save()

        det_ref2 = DetalleRecibido.objects.get(id=det.id)
        self.assertEqual(det_ref2.cantidad_recibida, 8)
        self.assertEqual(det_ref2.aporte, 0)

        inv2 = InventarioMateriale.objects.filter(id_material=material, ubicación=suc).first()
        self.assertIsNotNone(inv2)
        self.assertEqual(inv2.cantidad_disponible, 8)

        did = det.id
        det.delete()
        self.assertFalse(DetalleRecibido.objects.filter(id=did).exists())

    # ---------------------------------------------------------------------
    # 6) InventarioMateriale CRUD
    # ---------------------------------------------------------------------

    def test_06_inventario_material_crud_realdb(self):
        material = self._mk_material()
        suc = self._mk_sucursal()
        est = self._mk_estado_m_disponible()

        inv = InventarioMateriale.objects.create(
            id_material=material,
            cantidad_disponible=0,
            estado=est,
            ubicación=suc,
            cantidad_reservada=0,
        )
        self.created["inventario_material"].append(inv.id)
        self.assertIsNotNone(inv.id)

        inv.cantidad_disponible = 25
        inv.save(update_fields=["cantidad_disponible"])
        self.assertEqual(InventarioMateriale.objects.get(id=inv.id).cantidad_disponible, 25)

        iid = inv.id
        inv.delete()
        self.assertFalse(InventarioMateriale.objects.filter(id=iid).exists())

    # ---------------------------------------------------------------------
    # 7) InventarioMueble CRUD
    # ---------------------------------------------------------------------

    def test_07_inventario_mueble_crud_realdb(self):
        suc = self._mk_sucursal()
        mueble = self._mk_mueble()
        est = self._mk_estado_m_disponible()

        inv = InventarioMueble.objects.create(
            id_mueble=mueble,
            cantidad_disponible=10,
            ubicación=suc,
            estado=est,
        )
        self.created["inventario_mueble"].append(inv.id)
        self.assertIsNotNone(inv.id)

        inv.cantidad_disponible = 3
        inv.save(update_fields=["cantidad_disponible"])
        self.assertEqual(InventarioMueble.objects.get(id=inv.id).cantidad_disponible, 3)

        iid = inv.id
        inv.delete()
        self.assertFalse(InventarioMueble.objects.filter(id=iid).exists())