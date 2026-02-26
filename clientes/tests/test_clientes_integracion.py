from django.test import TestCase

from clientes.models import Cliente, DocumentosCliente
from clientes.admin import ClienteForm, DocumentosClienteForm
from django.core.exceptions import ValidationError
from archivos.models import Documento


class ClienteCRUDTest(TestCase):

    def setUp(self):
        self.valid_data = {
            'nombre': 'Juan Pérez',
            'telefono': '33332222',
            'direccion': 'Calle Falsa 123',
            'rtn': '08011990123456',
        }

    def test_insertar_cliente(self):
        form = ClienteForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), form.errors)
        cliente = form.save()

        self.assertEqual(Cliente.objects.count(), 1)
        self.assertEqual(cliente.nombre, 'Juan Pérez')
        self.assertEqual(cliente.telefono, '33332222')
        self.assertEqual(cliente.direccion, 'Calle Falsa 123')
        self.assertEqual(cliente.rtn, '08011990123456')

    def test_editar_cliente(self):
        cliente = Cliente.objects.create(
            nombre='Juan Pérez Original',
            telefono='33332222',
            direccion='Calle Falsa 123',
            rtn='08011990123456',
        )

        updated_data = {
            'nombre': 'Juan Pérez Editado',
            'telefono': '33332222',
            'direccion': 'Calle Mas Falsa 123',
            'rtn': '08011990123456',
        }

        form = ClienteForm(data=updated_data, instance=cliente)
        self.assertTrue(form.is_valid(), form.errors)
        
        cliente_editado = form.save()

        self.assertEqual(cliente_editado.nombre, 'Juan Pérez Editado')
        self.assertEqual(cliente_editado.direccion, 'Calle Mas Falsa 123')
        self.assertEqual(Cliente.objects.count(), 1)

        def test_eliminar_cliente(self):
            cliente = Cliente.objects.create(
                nombre='Juan Pérez',
                telefono='33332222',
                direccion='Calle Falsa 123',
                rtn='08011990123456',
            )

            self.assertEqual(Cliente.objects.count(), 1)

            cliente.delete()
            self.assertEqual(Cliente.objects.count(), 0)

class DocumentosClienteCRUDTest(TestCase):

    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre='Juan Pérez',
            telefono='33332222',
            direccion='Calle Falsa 123',
            rtn='08011990123456',
        )

        self.documento = Documento.objects.create(
            tipo_documento='DNI',
            descripcion='Documento Nacional de Identidad',
        )

    def test_crear_documento_cliente_valido(self):
        form = DocumentosClienteForm(
            data = {
                'id_cliente': self.cliente.id,
                'id_documento': self.documento.id,
                'valor': '0801199012345',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        instancia = form.save()

        self.assertEqual(DocumentosCliente.objects.count(), 1)
        self.assertEqual(instancia.id_cliente, self.cliente)
        self.assertEqual(instancia.id_documento, self.documento)
        self.assertEqual(instancia.valor, '0801199012345')

        self.assertIn(self.cliente.nombre, str(instancia))
        self.assertIn(self.documento.tipo_documento, str(instancia))

    def test_editar_documento_cliente(self):
        documento_cliente = DocumentosCliente.objects.create(
            id_cliente=self.cliente,
            id_documento=self.documento,
            valor='0801199012345',
        )

        form = DocumentosClienteForm(
            instance=documento_cliente,
            data={
                'id_cliente': self.cliente.id,
                'id_documento': self.documento.id,
                'valor': '0801199054321',
            },
        )

        self.assertTrue(form.is_valid(), form.errors)

        actualizado = form.save()

        actualizado.refresh_from_db()
        self.assertEqual(actualizado.valor, '0801199054321')

    def test_eliminar_documento_cliente(self):
        documento_cliente = DocumentosCliente.objects.create(
            id_cliente=self.cliente,
            id_documento=self.documento,
            valor='0801199012345',
        )

        self.assertEqual(DocumentosCliente.objects.count(), 1)

        documento_cliente.delete()

        self.assertEqual(DocumentosCliente.objects.count(), 0)