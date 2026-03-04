# realdb_tests/test_empleados_realdb.py
from uuid import uuid4

from django.test import SimpleTestCase
from django.contrib.auth import get_user_model

from Empleados.models import PerfilUsuario
from Sucursales.models import Sucursale, Caja


class EmpleadosAuthPerfilRealDBTests(SimpleTestCase):
    
    databases = {"default"}

    def setUp(self):
        self.tag = f"test_{uuid4().hex[:8]}"
        self.UserModel = get_user_model()

        self.created = {
            "auth_users": [],
            "perfiles": [],
        }

    def tearDown(self):
        # 1) PerfilUsuario (por si algo no cascada)
        perfiles = self.created.get("perfiles", [])
        if perfiles:
            PerfilUsuario.objects.filter(id__in=perfiles).delete()

        # 2) auth_user (CASCADE debería borrar perfil, pero ya lo intentamos arriba)
        users = self.created.get("auth_users", [])
        if users:
            self.UserModel.objects.filter(id__in=users).delete()

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _mk_auth_user(self):
        u = self.UserModel.objects.create_user(
            username=f"{self.tag}_auth",
            email=f"{self.tag}@test.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User",
        )
        self.created["auth_users"].append(u.id)
        return u

    def _pick_sucursal(self):
        # No crear sucursales aquí para no tocar lógica de otra app.
        # Si no hay sucursales existentes, devolvemos None y el test sigue.
        return Sucursale.objects.first()

    def _pick_caja(self):
        return Caja.objects.first()

    # ---------------------------------------------------------------------
    # Tests
    # ---------------------------------------------------------------------

    def test_01_auth_user_crea_perfil_usuario_realdb(self):
        u = self._mk_auth_user()

        perfil = PerfilUsuario.objects.filter(user=u).first()
        self.assertIsNotNone(perfil, "Al crear auth_user debería crearse PerfilUsuario por señal post_save.")
        self.created["perfiles"].append(perfil.id)

        self.assertEqual(perfil.user_id, u.id)
        # sucursal/caja pueden ser null inicialmente
        self.assertTrue(perfil.sucursal_id is None or isinstance(perfil.sucursal_id, int))
        self.assertTrue(perfil.caja_id is None or isinstance(perfil.caja_id, int))

    def test_02_update_perfil_sucursal_caja_si_existen_realdb(self):
        u = self._mk_auth_user()

        perfil = PerfilUsuario.objects.get(user=u)
        self.created["perfiles"].append(perfil.id)

        suc = self._pick_sucursal()
        caja = self._pick_caja()

        # Solo actualizamos si existen registros base; si no, no fallamos.
        update_fields = []
        if suc:
            perfil.sucursal = suc
            update_fields.append("sucursal")
        if caja:
            perfil.caja = caja
            update_fields.append("caja")

        if update_fields:
            perfil.save(update_fields=update_fields)

            perfil_ref = PerfilUsuario.objects.get(id=perfil.id)
            if suc:
                self.assertEqual(perfil_ref.sucursal_id, suc.id)
            if caja:
                self.assertEqual(perfil_ref.caja_id, caja.id)
        else:
            # No hay sucursal/caja en la BD real (o no están cargadas): validamos que al menos el perfil exista
            self.assertTrue(PerfilUsuario.objects.filter(id=perfil.id).exists())

    def test_03_delete_auth_user_elimina_perfil_realdb(self):
        u = self._mk_auth_user()

        perfil = PerfilUsuario.objects.get(user=u)
        self.created["perfiles"].append(perfil.id)

        pid = perfil.id
        uid = u.id

        # borramos el user: debe cascadear el perfil (OneToOneField(on_delete=CASCADE))
        u.delete()

        self.assertFalse(self.UserModel.objects.filter(id=uid).exists())
        self.assertFalse(PerfilUsuario.objects.filter(id=pid).exists())

        # Como ya lo borramos manualmente, evita que tearDown intente borrarlo otra vez
        self.created["auth_users"] = [i for i in self.created["auth_users"] if i != uid]
        self.created["perfiles"] = [i for i in self.created["perfiles"] if i != pid]