from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import Usuario
from tecnicos.models import Especialidad, Tecnico

CLAVE = "Clave.Segura1"


def crear_usuario(username, rol, tecnico=False, estado=Tecnico.Estado.DISPONIBLE):
    user = User.objects.create_user(
        username=username, password=CLAVE, first_name="Ana", last_name="Pérez",
        email=f"{username}@ejemplo.cl",
    )
    Usuario.objects.create(user=user, rol=rol, empresa=None)
    if tecnico:
        Tecnico.objects.create(usuario=user, telefono="+56 9 1111 1111", estado=estado)
    return user


class LoginApiTests(TestCase):
    """POST /api/v1/auth/login/: solo los técnicos habilitados obtienen token."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("api:login")
        self.tecnico_user = crear_usuario("tecnico1", Usuario.Rol.TECNICO, tecnico=True)
        self.tecnico_user.tecnico.especialidades.set(
            [Especialidad.objects.create(nombre="Electricidad")]
        )

    def login(self, username, password=CLAVE):
        return self.client.post(
            self.url, {"username": username, "password": password}, format="json"
        )

    def test_tecnico_recibe_token_y_perfil(self):
        resp = self.login("tecnico1")
        self.assertEqual(resp.status_code, 200)
        token = Token.objects.get(user=self.tecnico_user)
        self.assertEqual(resp.data["token"], token.key)
        self.assertEqual(resp.data["tecnico"]["username"], "tecnico1")
        self.assertEqual(resp.data["tecnico"]["nombre"], "Ana Pérez")
        self.assertEqual(resp.data["tecnico"]["especialidades"], ["Electricidad"])

    def test_dos_logins_reutilizan_el_mismo_token(self):
        primero = self.login("tecnico1").data["token"]
        segundo = self.login("tecnico1").data["token"]
        self.assertEqual(primero, segundo)
        self.assertEqual(Token.objects.filter(user=self.tecnico_user).count(), 1)

    def test_contrasena_incorrecta_responde_400_sin_token(self):
        resp = self.login("tecnico1", "otra")
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Token.objects.exists())

    def test_usuario_inexistente_responde_el_mismo_mensaje(self):
        incorrecta = self.login("tecnico1", "otra").data["detail"]
        inexistente = self.login("nadie").data["detail"]
        self.assertEqual(incorrecta, inexistente)

    def test_faltan_datos_responde_400(self):
        resp = self.client.post(self.url, {"username": "tecnico1"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_otros_roles_no_pueden_usar_la_app(self):
        for rol in (Usuario.Rol.ADMIN, Usuario.Rol.GESTOR, Usuario.Rol.ENCARGADO,
                    Usuario.Rol.GERENCIA):
            with self.subTest(rol=rol):
                crear_usuario(f"u_{rol.lower()}", rol)
                resp = self.login(f"u_{rol.lower()}")
                self.assertEqual(resp.status_code, 403)
        self.assertFalse(Token.objects.exists())

    def test_tecnico_inactivo_no_puede_entrar(self):
        crear_usuario("tecnico_inactivo", Usuario.Rol.TECNICO, tecnico=True,
                      estado=Tecnico.Estado.INACTIVO)
        self.assertEqual(self.login("tecnico_inactivo").status_code, 403)

    def test_rol_tecnico_sin_perfil_de_tecnico_no_puede_entrar(self):
        crear_usuario("sin_perfil", Usuario.Rol.TECNICO, tecnico=False)
        self.assertEqual(self.login("sin_perfil").status_code, 403)

    def test_cuenta_desactivada_no_puede_entrar(self):
        self.tecnico_user.is_active = False
        self.tecnico_user.save()
        self.assertEqual(self.login("tecnico1").status_code, 400)


class PerfilYLogoutApiTests(TestCase):
    """GET /auth/perfil/ y POST /auth/logout/ exigen un token válido."""

    def setUp(self):
        self.client = APIClient()
        self.user = crear_usuario("tecnico1", Usuario.Rol.TECNICO, tecnico=True)
        self.token = Token.objects.create(user=self.user)

    def con_token(self, key=None):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {key or self.token.key}")

    def test_perfil_con_token(self):
        self.con_token()
        resp = self.client.get(reverse("api:perfil"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["username"], "tecnico1")
        self.assertEqual(resp.data["estado"], Tecnico.Estado.DISPONIBLE)

    def test_perfil_sin_token_responde_401(self):
        self.assertEqual(self.client.get(reverse("api:perfil")).status_code, 401)

    def test_perfil_con_token_falso_responde_401(self):
        self.con_token("token-falso")
        self.assertEqual(self.client.get(reverse("api:perfil")).status_code, 401)

    def test_perfil_rechaza_a_un_tecnico_que_fue_inactivado(self):
        self.user.tecnico.estado = Tecnico.Estado.INACTIVO
        self.user.tecnico.save()
        self.con_token()
        self.assertEqual(self.client.get(reverse("api:perfil")).status_code, 403)

    def test_token_de_otro_rol_no_sirve(self):
        admin = crear_usuario("admin1", Usuario.Rol.ADMIN)
        self.con_token(Token.objects.create(user=admin).key)
        self.assertEqual(self.client.get(reverse("api:perfil")).status_code, 403)

    def test_logout_borra_el_token(self):
        self.con_token()
        resp = self.client.post(reverse("api:logout"))
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Token.objects.filter(user=self.user).exists())
        # Con el token borrado, el perfil ya no responde.
        self.assertEqual(self.client.get(reverse("api:perfil")).status_code, 401)

    def test_la_api_no_usa_la_sesion_web(self):
        # Una sesión iniciada en la web no da acceso a la API: se exige token.
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("api:perfil")).status_code, 401)
