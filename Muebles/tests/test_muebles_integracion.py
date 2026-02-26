# Muebles/tests/test_muebles_integracion.py

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from Muebles.admin import (
    ImagenForm,
    TamañoForm,
    MuebleForm,
    MuebleMaterialeForm,
)

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


class CategoriasMuebleCrudTest(TestCase):
    def setUp(self):
        self.data = {
            "nombre": "Categoria Mueble",
            "descripcion": "Categoria para muebles de sala",
            "imagen": "muebles_cat/cat_mueble_test.jpg",
            "imagen_url": "https://example.com/muebles_cat/cat_mueble_test.jpg",
        }

    def test_crear_categoria_mueble_valida(self):
        """Valida que se pueda crear una categoría de mueble."""
        obj = CategoriasMueble.objects.create(**self.data)

        self.assertEqual(CategoriasMueble.objects.count(), 1)
        self.assertEqual(obj.nombre, self.data["nombre"])
        self.assertEqual(obj.descripcion, self.data["descripcion"])

    def test_editar_categoria_mueble_modifica_descripcion(self):
        """Valida que editar la descripción se refleje en base de datos."""
        obj = CategoriasMueble.objects.create(**self.data)

        obj.descripcion = "Categoria para muebles de comedor"
        obj.save()

        obj_refrescado = CategoriasMueble.objects.get(pk=obj.pk)
        self.assertEqual(obj_refrescado.descripcion, "Categoria para muebles de comedor")

    def test_eliminar_categoria_mueble_elimina_registro(self):
        """Valida que se elimine el registro de categoría de mueble."""
        obj = CategoriasMueble.objects.create(**self.data)

        obj.delete()
        self.assertEqual(CategoriasMueble.objects.count(), 0)


class TamanoFormCrudTest(TestCase):
    def setUp(self):
        self.data = {
            "nombre": "Grande",
            "descripcion": "Tamano para 6 personas",
        }

    def test_crear_tamano_valido(self):
        """Valida que TamañoForm permita crear un tamaño."""
        form = TamañoForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        obj = form.save()
        self.assertEqual(Tamaño.objects.count(), 1)
        self.assertEqual(obj.nombre, "Grande")
        self.assertEqual(obj.descripcion, "Tamano para 6 personas")

    def test_editar_tamano_modifica_descripcion(self):
        """Valida que editar la descripción se refleje en base de datos."""
        obj = Tamaño.objects.create(nombre="Grande", descripcion="Tamano para 6 personas")
        obj.descripcion = "Tamano para 8 personas"
        obj.save()

        obj_refrescado = Tamaño.objects.get(pk=obj.pk)
        self.assertEqual(obj_refrescado.descripcion, "Tamano para 8 personas")

    def test_eliminar_tamano_elimina_registro(self):
        """Valida que se elimine el registro de tamaño."""
        obj = Tamaño.objects.create(nombre="Grande", descripcion="Tamano para 6 personas")
        obj.delete()
        self.assertEqual(Tamaño.objects.count(), 0)


class MuebleFormCrudTest(TestCase):
    def setUp(self):
        self.image = SimpleUploadedFile(
            name="mueble_test.jpg",
            content=b"\x47\x49\x46\x38\x39\x61",
            content_type="image/jpeg",
        )

        self.categoria = CategoriasMueble.objects.create(
            nombre="Categoria Mueble",
            descripcion="Categoria para muebles",
            imagen="muebles_cat/cat.jpg",
            imagen_url="https://example.com/muebles_cat/cat.jpg",
        )

        self.tamano = Tamaño.objects.create(
            nombre="Mediano",
            descripcion="Tamano para 4 personas",
        )

        self.medida = UnidadesMedida.objects.create(
            nombre="Centimetro",
            abreviatura="Cm",
        )

        self.data = {
            "nombre": "Mesa Roble",
            "descripcion": "Mesa color cafe, ideal para 4 personas",
            "precio_base": 20000.00,
            "categoria": self.categoria.id,
            "medida": self.medida.id,
            "alto": 75,
            "ancho": 90,
            "largo": 140,
            "imagen": "muebles/mueble_test.jpg",
            "imagen_url": "https://example.com/muebles/mueble_test.jpg",
            "tamano": self.tamano.id,
            "Descontinuado": False,
            "stock_minimo": 5,
            "stock_maximo": 50,
            "archivo_temp": self.image,
        }

    def test_crear_mueble_valido_y_crea_historial_precio(self):
        """Valida que MuebleForm cree el mueble y genere historial inicial de precio."""
        form = MuebleForm(data=self.data, files={"archivo_temp": self.image})
        self.assertTrue(form.is_valid(), form.errors)

        mueble = form.save()
        self.assertEqual(Mueble.objects.count(), 1)
        self.assertEqual(mueble.nombre, "Mesa Roble")
        self.assertEqual(mueble.categoria_id, self.categoria.id)
        self.assertEqual(mueble.medida_id, self.medida.id)
        self.assertEqual(mueble.tamano_id, self.tamano.id)

        # save() debe crear historial inicial (precio_viejo=None)
        self.assertEqual(HistorialPreciosMueble.objects.count(), 1)
        hist = HistorialPreciosMueble.objects.get(id_mueble=mueble, fecha_fin__isnull=True)
        self.assertAlmostEqual(hist.precio, 20000.00, places=2)
        self.assertEqual(hist.fecha_inicio, timezone.now().date())
        self.assertIsNone(hist.fecha_fin)

    def test_editar_mueble_cambia_precio_y_actualiza_historial(self):
        """Valida que al cambiar precio se cierre historial anterior y se cree uno nuevo."""
        mueble = Mueble.objects.create(
            nombre="Mesa Roble",
            descripcion="Mesa color cafe, ideal para 4 personas",
            precio_base=20000.00,
            categoria=self.categoria,
            medida=self.medida,
            alto=75,
            ancho=90,
            largo=140,
            imagen="muebles/mueble_test.jpg",
            imagen_url="https://example.com/muebles/mueble_test.jpg",
            tamano=self.tamano,
            Descontinuado=False,
            stock_minimo=5,
            stock_maximo=50,
        )

        self.assertEqual(HistorialPreciosMueble.objects.count(), 1)

        hoy = timezone.now().date()
        mueble.precio_base = 25000.00
        mueble.save()

        self.assertEqual(HistorialPreciosMueble.objects.count(), 2)

        # Evitar ambigüedad por misma fecha_inicio (hoy) -> usar fecha_fin NULL / NOT NULL
        cerrado = HistorialPreciosMueble.objects.get(
            id_mueble=mueble,
            precio=20000.00,
            fecha_fin__isnull=False,
        )
        self.assertEqual(cerrado.fecha_fin, hoy)

        abierto = HistorialPreciosMueble.objects.get(
            id_mueble=mueble,
            precio=25000.00,
            fecha_fin__isnull=True,
        )
        self.assertEqual(abierto.fecha_inicio, hoy)
        self.assertIsNone(abierto.fecha_fin)

    def test_eliminar_mueble_elimina_registro(self):
        """Valida que se pueda eliminar el mueble (limpiando dependencias por FK en BD)."""
        mueble = Mueble.objects.create(
            nombre="Mesa Roble",
            descripcion="Mesa color cafe, ideal para 4 personas",
            precio_base=20000.00,
            categoria=self.categoria,
            medida=self.medida,
            alto=75,
            ancho=90,
            largo=140,
            imagen="muebles/mueble_test.jpg",
            imagen_url="https://example.com/muebles/mueble_test.jpg",
            tamano=self.tamano,
            Descontinuado=False,
            stock_minimo=5,
            stock_maximo=50,
        )

        # Forzar 2 historiales
        mueble.precio_base = 25000.00
        mueble.save()
        self.assertEqual(HistorialPreciosMueble.objects.filter(id_mueble=mueble).count(), 2)

        # IMPORTANTE: En PostgreSQL la FK existe y se valida.
        # DO_NOTHING solo afecta el ORM, no elimina la restricción en la BD.
        HistorialPreciosMueble.objects.filter(id_mueble=mueble).delete()
        MuebleMateriale.objects.filter(id_mueble=mueble).delete()  # por si existieran relaciones

        mueble.delete()
        self.assertEqual(Mueble.objects.count(), 0)


class MuebleMaterialeFormCrudTest(TestCase):
    def setUp(self):
        # Dependencias para Materiale (Materiales app)
        self.cat_material = CategoriasMateriale.objects.create(
            nombre="Categoria Material",
            descripcion="Categoria material base",
            imagen="materiales_cat/cat.jpg",
            imagen_url="https://example.com/materiales_cat/cat.jpg",
        )
        self.medida_material = UnidadesMedida.objects.create(
            nombre="Unidad",
            abreviatura="Un",
        )
        self.material = Materiale.objects.create(
            nombre="Madera Pino",
            imagen="materiales/mat.jpg",
            stock_minimo=10,
            stock_maximo=100,
            categoria=self.cat_material,
            imagen_url="https://example.com/materiales/mat.jpg",
            medida=self.medida_material,
        )

        # Dependencias para Mueble
        self.categoria_mueble = CategoriasMueble.objects.create(
            nombre="Categoria Mueble",
            descripcion="Categoria para muebles",
            imagen="muebles_cat/cat.jpg",
            imagen_url="https://example.com/muebles_cat/cat.jpg",
        )
        self.tamano = Tamaño.objects.create(nombre="Mediano", descripcion="Tamano para 4 personas")
        self.medida_mueble = UnidadesMedida.objects.create(nombre="Centimetro", abreviatura="Cm")

        self.mueble = Mueble.objects.create(
            nombre="Mesa Roble",
            descripcion="Mesa color cafe, ideal para 4 personas",
            precio_base=20000.00,
            categoria=self.categoria_mueble,
            medida=self.medida_mueble,
            alto=75,
            ancho=90,
            largo=140,
            imagen="muebles/mueble_test.jpg",
            imagen_url="https://example.com/muebles/mueble_test.jpg",
            tamano=self.tamano,
            Descontinuado=False,
            stock_minimo=5,
            stock_maximo=50,
        )

        self.data = {
            "id_material": self.material.id,
            "id_mueble": self.mueble.id,
            "cantidad": 2,
        }

    def test_crear_mueble_material_valido(self):
        """Valida que MuebleMaterialeForm permita crear relación mueble-material."""
        form = MuebleMaterialeForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        obj = form.save()
        self.assertEqual(MuebleMateriale.objects.count(), 1)
        self.assertEqual(obj.id_material_id, self.material.id)
        self.assertEqual(obj.id_mueble_id, self.mueble.id)
        self.assertEqual(obj.cantidad, 2)

    def test_editar_mueble_material_modifica_cantidad(self):
        """Valida que editar la cantidad se refleje en base de datos."""
        obj = MuebleMateriale.objects.create(
            id_material=self.material,
            id_mueble=self.mueble,
            cantidad=2,
        )

        obj.cantidad = 3
        obj.save()

        obj_refrescado = MuebleMateriale.objects.get(pk=obj.pk)
        self.assertEqual(obj_refrescado.cantidad, 3)

    def test_eliminar_mueble_material_elimina_registro(self):
        """Valida que se elimine el registro de MuebleMateriale."""
        obj = MuebleMateriale.objects.create(
            id_material=self.material,
            id_mueble=self.mueble,
            cantidad=2,
        )

        obj.delete()
        self.assertEqual(MuebleMateriale.objects.count(), 0)