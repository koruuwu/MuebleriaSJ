# realdb_tests/test_muebles_realdb.py
from uuid import uuid4
from django.test import SimpleTestCase
from django.utils import timezone

from Muebles.models import (
    CategoriasMueble,
    Tamaño,
    Mueble,
    MuebleMateriale,
    HistorialPreciosMueble,
)

from Materiales.models import (
    UnidadesMedida,
    CategoriasMateriale,
    Materiale,
)


class MueblesRealDBTests(SimpleTestCase):
    
    databases = {"default"}

    def setUp(self):
        self.tag = f"test_{uuid4().hex[:8]}"
        self.created = {
            "cats_mueble": [],
            "tamano": [],
            "muebles": [],
            "hist_mueble": [],
            "mueble_material": [],
            
            "cats_mat": [],
            "unidades_medida": [],
            "materiales": [],
        }

    def tearDown(self):
        
        # 1) Puentes / dependientes
        if self.created["mueble_material"]:
            MuebleMateriale.objects.filter(id__in=self.created["mueble_material"]).delete()

        # 2) Historiales (pueden existir por save automático)
        if self.created["hist_mueble"]:
            HistorialPreciosMueble.objects.filter(id__in=self.created["hist_mueble"]).delete()

        if self.created["muebles"]:
            HistorialPreciosMueble.objects.filter(id_mueble_id__in=self.created["muebles"]).delete()

        # 3) Padres
        if self.created["muebles"]:
            Mueble.objects.filter(id__in=self.created["muebles"]).delete()

        if self.created["tamano"]:
            Tamaño.objects.filter(id__in=self.created["tamano"]).delete()

        if self.created["cats_mueble"]:
            CategoriasMueble.objects.filter(id__in=self.created["cats_mueble"]).delete()

        # 4) Dependencias Materiales (solo si las creamos aquí)
        if self.created["materiales"]:
            Materiale.objects.filter(id__in=self.created["materiales"]).delete()

        if self.created["cats_mat"]:
            CategoriasMateriale.objects.filter(id__in=self.created["cats_mat"]).delete()

        if self.created["unidades_medida"]:
            UnidadesMedida.objects.filter(id__in=self.created["unidades_medida"]).delete()

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _mk_um(self):
        # Para no depender de datos base, intentamos reutilizar primero.
        um = UnidadesMedida.objects.first()
        if um:
            return um

        # nombre max_length=15 -> mantener corto
        um = UnidadesMedida.objects.create(nombre=f"{self.tag[:10]}_um", abreviatura="un")
        self.created["unidades_medida"].append(um.id)
        return um

    def _mk_cat_mueble(self):
        cat = CategoriasMueble.objects.create(
            nombre=f"{self.tag}_cat_mueble",
            descripcion="cat mueble test",
            imagen="x",
            imagen_url=None,
        )
        self.created["cats_mueble"].append(cat.id)
        return cat

    def _mk_tamano(self):
        # Campos sin max_length explícito en nombre; descripcion max 50 -> corto
        t = Tamaño.objects.create(
            nombre=f"{self.tag}_tam",
            descripcion="tam test",
        )
        self.created["tamano"].append(t.id)
        return t

    def _mk_mueble(self, precio=100.0):
        um = self._mk_um()
        cat = self._mk_cat_mueble()
        tam = self._mk_tamano()

        m = Mueble.objects.create(
            nombre=f"{self.tag}_mueble",
            descripcion="mueble test",
            precio_base=float(precio),
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

    def _mk_cat_material(self):
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
        cat = self._mk_cat_material()
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

    # ---------------------------------------------------------------------
    # Tests
    # ---------------------------------------------------------------------

    def test_01_categorias_mueble_crud_realdb(self):
        cat = self._mk_cat_mueble()
        self.assertIsNotNone(cat.id)

        cat.descripcion = "cat mueble edit"
        cat.save(update_fields=["descripcion"])
        self.assertEqual(CategoriasMueble.objects.get(id=cat.id).descripcion, "cat mueble edit")

        cid = cat.id
        cat.delete()
        self.assertFalse(CategoriasMueble.objects.filter(id=cid).exists())
        self.created["cats_mueble"] = [i for i in self.created["cats_mueble"] if i != cid]

    def test_02_tamano_crud_realdb(self):
        t = self._mk_tamano()
        self.assertIsNotNone(t.id)

        t.descripcion = "tam edit"
        t.save(update_fields=["descripcion"])
        self.assertEqual(Tamaño.objects.get(id=t.id).descripcion, "tam edit")

        tid = t.id
        t.delete()
        self.assertFalse(Tamaño.objects.filter(id=tid).exists())
        self.created["tamano"] = [i for i in self.created["tamano"] if i != tid]

    def test_03_mueble_crea_historial_y_update_realdb(self):
        hoy = timezone.now().date()
        mueble = self._mk_mueble(precio=100.0)
        self.assertIsNotNone(mueble.id)

        # Al crear, debe existir historial abierto
        hist = HistorialPreciosMueble.objects.filter(
            id_mueble=mueble,
            fecha_fin__isnull=True,
        ).order_by("-fecha_inicio").first()
        self.assertIsNotNone(hist)
        self.created["hist_mueble"].append(hist.id)
        self.assertEqual(float(hist.precio), 100.0)
        self.assertEqual(hist.fecha_inicio, hoy)

        # Guardar sin cambiar precio -> NO crea historial nuevo
        before_count = HistorialPreciosMueble.objects.filter(id_mueble=mueble).count()
        mueble.descripcion = "edit sin cambio precio"
        mueble.save()
        after_count = HistorialPreciosMueble.objects.filter(id_mueble=mueble).count()
        self.assertEqual(before_count, after_count)

        # Cambiar precio -> cierra anterior y crea nuevo abierto
        mueble.precio_base = 120.0
        mueble.save()

        cerrado = HistorialPreciosMueble.objects.filter(
            id_mueble=mueble,
            fecha_fin__isnull=False,
        ).order_by("-fecha_inicio").first()
        self.assertIsNotNone(cerrado)
        self.assertEqual(cerrado.fecha_fin, hoy)

        nuevo = HistorialPreciosMueble.objects.filter(
            id_mueble=mueble,
            fecha_fin__isnull=True,
        ).order_by("-fecha_inicio").first()
        self.assertIsNotNone(nuevo)
        self.assertEqual(float(nuevo.precio), 120.0)
        self.created["hist_mueble"].append(nuevo.id)

    def test_04_mueble_material_crud_realdb(self):
        mueble = self._mk_mueble(precio=80.0)
        material = self._mk_material()

        rel = MuebleMateriale.objects.create(
            id_mueble=mueble,
            id_material=material,
            cantidad=5,
        )
        self.created["mueble_material"].append(rel.id)
        self.assertIsNotNone(rel.id)

        rel.cantidad = 7
        rel.save(update_fields=["cantidad"])
        self.assertEqual(MuebleMateriale.objects.get(id=rel.id).cantidad, 7)

        rid = rel.id
        rel.delete()
        self.assertFalse(MuebleMateriale.objects.filter(id=rid).exists())
        self.created["mueble_material"] = [i for i in self.created["mueble_material"] if i != rid]