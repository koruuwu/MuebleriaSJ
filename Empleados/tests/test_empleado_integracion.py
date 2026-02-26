from django.forms import model_to_dict
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib import admin

from Empleados.models import PerfilUsuario
from Empleados.admin import UsuarioChangeForm, UsuarioCreationForm, UsuarioAdmin


class UsuarioCrudTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_crear_usuario_valido_crea_perfil(self):
        """
        Debe crear un usuario válido y, por el signal post_save,
        también debe crearse automáticamente su PerfilUsuario.
        """
        form_data = {
            "username": "usuario_test",
            "password1": "ClaveSegura123",
            "password2": "ClaveSegura123",
        }

        form = UsuarioCreationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

        user = form.save()

        # Usuario creado
        self.assertTrue(User.objects.filter(username="usuario_test").exists())

        # PerfilUsuario creado por el signal
        self.assertTrue(PerfilUsuario.objects.filter(user=user).exists())
        perfil = PerfilUsuario.objects.get(user=user)
        self.assertIsNone(perfil.sucursal)
        self.assertIsNone(perfil.caja)

    def test_editar_usuario_cambiar_username_valido(self):
        """
        Debe permitir editar el username de un usuario existente
        usando UsuarioChangeForm y guardar el cambio correctamente.
        """
        # Crear usuario inicial
        user = User.objects.create_user(
            username="usuario_original",
            password="ClaveSegura123",
        )

        # Construir data del form a partir del usuario actual
        form_data = model_to_dict(user)
        # model_to_dict no incluye el campo password por defecto, pero
        # UserChangeForm usa el campo 'password' como ReadOnly, así que
        # para evitar problemas lo agregamos con su valor actual:
        form_data["password"] = user.password

        # Cambiar solo el username
        form_data["username"] = "usuario_editado"

        form = UsuarioChangeForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid(), form.errors)

        usuario_editado = form.save()

        # Verificar cambio en BD
        self.assertEqual(usuario_editado.username, "usuario_editado")
        self.assertTrue(
            User.objects.filter(username="usuario_editado").exists()
        )


    def test_eliminar_usuario_elimina_perfil(self):
        """
        Al eliminar un usuario, su PerfilUsuario (OneToOne, on_delete=CASCADE)
        también debe eliminarse.
        """
        # Crear usuario (dispara la señal que crea PerfilUsuario)
        user = User.objects.create_user(
            username="usuario_cascade",
            password="ClaveSegura123"
        )

        # Guardar el id antes de borrar
        user_id = user.id

        # Asegurarnos de que el perfil existe
        self.assertTrue(
            PerfilUsuario.objects.filter(user_id=user_id).exists(),
            "Debe existir un PerfilUsuario ligado al usuario recién creado."
        )

        # Eliminar usuario
        user.delete()

        # Ahora consultamos usando user_id, NO la instancia user (porque ya no tiene pk)
        self.assertFalse(
            PerfilUsuario.objects.filter(user_id=user_id).exists(),
            "Al eliminar el usuario, su PerfilUsuario debe eliminarse por CASCADE."
        )
