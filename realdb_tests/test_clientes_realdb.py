from django.test import SimpleTestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from clientes.models import Cliente, DocumentosCliente
from archivos.models import Documento


# =========================================================
# CLIENTE CRUD REAL DB
# =========================================================

class ClienteRealDBCrudTests(SimpleTestCase):
    databases = {"default"}

    def setUp(self):
        self.test_prefix = "test_cliente_realdb_"
        Cliente.objects.filter(nombre__startswith=self.test_prefix).delete()

    def tearDown(self):
        Cliente.objects.filter(nombre__startswith=self.test_prefix).delete()

    def test_insert_cliente_realdb(self):
        c = Cliente.objects.create(
            creado=timezone.now(),
            nombre=f"{self.test_prefix}insert",
            telefono="99999999",
            direccion="direccion_test",
            rtn=None,
        )

        self.assertIsNotNone(c.id)
        self.assertTrue(
            Cliente.objects.filter(id=c.id).exists()
        )

    def test_update_cliente_realdb(self):
        c = Cliente.objects.create(
            creado=timezone.now(),
            nombre=f"{self.test_prefix}update",
            telefono="11111111",
            direccion="direccion_test",
            rtn=None,
        )

        c.telefono = "22222222"
        c.save(update_fields=["telefono"])

        updated = Cliente.objects.get(id=c.id)
        self.assertEqual(updated.telefono, "22222222")

    def test_delete_cliente_realdb(self):
        c = Cliente.objects.create(
            creado=timezone.now(),
            nombre=f"{self.test_prefix}delete",
            telefono="33333333",
            direccion="direccion_test",
            rtn=None,
        )

        cid = c.id
        c.delete()

        self.assertFalse(
            Cliente.objects.filter(id=cid).exists()
        )


# =========================================================
# DOCUMENTOS CLIENTE CRUD REAL DB
# =========================================================

class DocumentosClienteRealDBCrudTests(SimpleTestCase):
    databases = {"default"}

    def setUp(self):
        self.cliente = Cliente.objects.create(
            creado=timezone.now(),
            nombre="test_cliente_doc_realdb",
            telefono="44444444",
            direccion="direccion_doc_test",
            rtn=None,
        )

        self.documento = Documento.objects.create(
            fecha_registro=timezone.now(),
            tipo_documento="test_doc_tipo_realdb",
            descripcion="test_doc_desc_realdb",
        )

        DocumentosCliente.objects.filter(
            id_cliente=self.cliente
        ).delete()

    def tearDown(self):
        DocumentosCliente.objects.filter(
            id_cliente=self.cliente
        ).delete()

        Documento.objects.filter(id=self.documento.id).delete()
        Cliente.objects.filter(id=self.cliente.id).delete()

    def test_insert_documento_cliente_realdb(self):
        dc = DocumentosCliente.objects.create(
            id_cliente=self.cliente,
            id_documento=self.documento,
            valor="valor_test",
        )

        self.assertIsNotNone(dc.id)
        self.assertTrue(
            DocumentosCliente.objects.filter(id=dc.id).exists()
        )

    def test_update_documento_cliente_realdb(self):
        dc = DocumentosCliente.objects.create(
            id_cliente=self.cliente,
            id_documento=self.documento,
            valor="valor_inicial",
        )

        dc.valor = "valor_actualizado"
        dc.save(update_fields=["valor"])

        updated = DocumentosCliente.objects.get(id=dc.id)
        self.assertEqual(updated.valor, "valor_actualizado")

    def test_delete_documento_cliente_realdb(self):
        dc = DocumentosCliente.objects.create(
            id_cliente=self.cliente,
            id_documento=self.documento,
            valor="valor_delete",
        )

        dcid = dc.id
        dc.delete()

        self.assertFalse(
            DocumentosCliente.objects.filter(id=dcid).exists()
        )

    def test_no_permite_documento_duplicado_realdb(self):
        DocumentosCliente.objects.create(
            id_cliente=self.cliente,
            id_documento=self.documento,
            valor="valor_1",
        )

        with self.assertRaises(ValidationError):
            dc2 = DocumentosCliente(
                id_cliente=self.cliente,
                id_documento=self.documento,
                valor="valor_2",
            )
            dc2.save()