# realdb_tests/test_materiales_realdb.py
from uuid import uuid4
from django.test import SimpleTestCase
from django.utils import timezone

from Materiales.models import (
    CategoriasMateriale,
    UnidadesMedida,
    Materiale,
    EstadosPersonas,
    Proveedore,
    MaterialProveedore,
    HistorialPrecio,
    Calificacione,
)


class MaterialesRealDBTests(SimpleTestCase):
    
    databases = {"default"}

    def setUp(self):
        self.tag = f"test_{uuid4().hex[:8]}"
        self.created = {
            "cats_mat": [],
            "unidades_medida": [],
            "materiales": [],
            "estados_personas": [],
            "proveedores": [],
            "material_proveedor": [],
            "hist_precios": [],
            "calificaciones": [],
        }

    def tearDown(self):
        
        # 1) Dependientes / historiales
        if self.created["calificaciones"]:
            Calificacione.objects.filter(id__in=self.created["calificaciones"]).delete()

        # HistorialPrecio puede existir aunque no guardes IDs (por save automático),
        # así que borramos por IDs guardados + por combinaciones creadas.
        if self.created["hist_precios"]:
            HistorialPrecio.objects.filter(id__in=self.created["hist_precios"]).delete()

        if self.created["materiales"] or self.created["proveedores"]:
            q = HistorialPrecio.objects.all()
            if self.created["materiales"]:
                q = q.filter(material_id__in=self.created["materiales"])
            if self.created["proveedores"]:
                q = q | HistorialPrecio.objects.filter(proveedor_id__in=self.created["proveedores"])
            q.delete()

        # 2) Puentes
        if self.created["material_proveedor"]:
            MaterialProveedore.objects.filter(id__in=self.created["material_proveedor"]).delete()

        # 3) Padres
        if self.created["materiales"]:
            Materiale.objects.filter(id__in=self.created["materiales"]).delete()

        if self.created["proveedores"]:
            Proveedore.objects.filter(id__in=self.created["proveedores"]).delete()

        # EstadosPersonas a veces tiene default=1 en Proveedor, así que solo borramos si lo creamos nosotros
        if self.created["estados_personas"]:
            EstadosPersonas.objects.filter(id__in=self.created["estados_personas"]).delete()

        if self.created["cats_mat"]:
            CategoriasMateriale.objects.filter(id__in=self.created["cats_mat"]).delete()

        if self.created["unidades_medida"]:
            UnidadesMedida.objects.filter(id__in=self.created["unidades_medida"]).delete()

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
        # Preferimos reutilizar si ya existe uno "genérico", pero si no hay nada, creamos uno test_
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
            email=f"{self.tag}@test.com",
            estado=ep,
        )
        self.created["proveedores"].append(p.id)
        return p

    # ---------------------------------------------------------------------
    # Tests
    # ---------------------------------------------------------------------

    def test_01_categorias_material_crud_realdb(self):
        cat = self._mk_categoria_material()
        self.assertIsNotNone(cat.id)

        cat.descripcion = "cat mat test edit"
        cat.save(update_fields=["descripcion"])
        self.assertEqual(
            CategoriasMateriale.objects.get(id=cat.id).descripcion,
            "cat mat test edit",
        )

        cid = cat.id
        cat.delete()
        self.assertFalse(CategoriasMateriale.objects.filter(id=cid).exists())
        self.created["cats_mat"] = [i for i in self.created["cats_mat"] if i != cid]

    def test_02_unidades_medida_crud_realdb(self):
        um = UnidadesMedida.objects.create(
        nombre=f"{self.tag[:10]}_um",  
        abreviatura="un",
        )
        self.created["unidades_medida"].append(um.id)
        self.assertIsNotNone(um.id)

        um.abreviatura = "u"
        um.save(update_fields=["abreviatura"])
        self.assertEqual(UnidadesMedida.objects.get(id=um.id).abreviatura, "u")

        uid = um.id
        um.delete()
        self.assertFalse(UnidadesMedida.objects.filter(id=uid).exists())
        self.created["unidades_medida"] = [i for i in self.created["unidades_medida"] if i != uid]

    def test_03_materiales_crud_realdb(self):
        material = self._mk_material()
        self.assertIsNotNone(material.id)

        material.stock_maximo = 250
        material.save(update_fields=["stock_maximo"])
        self.assertEqual(Materiale.objects.get(id=material.id).stock_maximo, 250)

        mid = material.id
        material.delete()
        self.assertFalse(Materiale.objects.filter(id=mid).exists())
        self.created["materiales"] = [i for i in self.created["materiales"] if i != mid]

    def test_04_proveedores_crud_realdb(self):
        prov = self._mk_proveedor()
        self.assertIsNotNone(prov.id)

        prov.telefono = "88888888"
        prov.save(update_fields=["telefono"])
        self.assertEqual(Proveedore.objects.get(id=prov.id).telefono, "88888888")

        pid = prov.id
        prov.delete()
        self.assertFalse(Proveedore.objects.filter(id=pid).exists())
        self.created["proveedores"] = [i for i in self.created["proveedores"] if i != pid]

    def test_05_material_proveedor_crea_historial_y_update_realdb(self):
        material = self._mk_material()
        prov = self._mk_proveedor()

        hoy = timezone.now().date()

        rel = MaterialProveedore.objects.create(
            material=material,
            id_proveedor=prov,
            precio_actual=10.0,
            tiempo=3,
            unidad_tiempo=MaterialProveedore.DIAS,
            comentarios="test",
        )
        self.created["material_proveedor"].append(rel.id)

        # Debe existir historial abierto (fecha_fin null)
        hist = HistorialPrecio.objects.filter(
            material=material,
            proveedor=prov,
            fecha_fin__isnull=True,
        ).order_by("-fecha_inicio").first()

        self.assertIsNotNone(hist)
        # Guardamos por si acaso (aunque igual lo borramos por filtros en tearDown)
        self.created["hist_precios"].append(hist.id)
        self.assertEqual(float(hist.precio), 10.0)
        self.assertEqual(hist.fecha_inicio, hoy)

        # Guardar sin cambio de precio -> NO debe crear historial nuevo
        before_count = HistorialPrecio.objects.filter(material=material, proveedor=prov).count()
        rel.comentarios = "edit sin cambio precio"
        rel.save()
        after_count = HistorialPrecio.objects.filter(material=material, proveedor=prov).count()
        self.assertEqual(before_count, after_count)

        # Cambiar precio -> debe cerrar historial anterior y crear nuevo abierto
        rel.precio_actual = 12.5
        rel.save()

        # anterior debe quedar con fecha_fin = hoy
        hist_prev = HistorialPrecio.objects.filter(
            material=material,
            proveedor=prov,
        ).order_by("-fecha_inicio")[1:2].first()  # el segundo más reciente

        # Si solo hay 2 entradas, esto existe; si por algún motivo ya existía historial previo,
        # igual validamos que al menos haya uno cerrado.
        cerrado = HistorialPrecio.objects.filter(
            material=material,
            proveedor=prov,
            fecha_fin__isnull=False,
        ).order_by("-fecha_inicio").first()
        self.assertIsNotNone(cerrado)
        self.assertEqual(cerrado.fecha_fin, hoy)

        # nuevo abierto con precio 12.5
        hist_new = HistorialPrecio.objects.filter(
            material=material,
            proveedor=prov,
            fecha_fin__isnull=True,
        ).order_by("-fecha_inicio").first()
        self.assertIsNotNone(hist_new)
        self.assertEqual(float(hist_new.precio), 12.5)
        self.created["hist_precios"].append(hist_new.id)

    def test_06_calificaciones_crud_realdb(self):
        prov = self._mk_proveedor()

        cal = Calificacione.objects.create(
            criterio=Calificacione.PUNTUALIDAD,
            calificacion=Calificacione.CIN,
            comentario="Buen proveedor",
            id_prov=prov,
        )
        self.created["calificaciones"].append(cal.id)
        self.assertIsNotNone(cal.id)

        cal.comentario = "Excelente proveedor"
        cal.save(update_fields=["comentario"])
        self.assertEqual(Calificacione.objects.get(id=cal.id).comentario, "Excelente proveedor")

        cid = cal.id
        cal.delete()
        self.assertFalse(Calificacione.objects.filter(id=cid).exists())
        self.created["calificaciones"] = [i for i in self.created["calificaciones"] if i != cid]