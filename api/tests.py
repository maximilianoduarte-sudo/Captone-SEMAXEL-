from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import Usuario
from empresas.models import Empresa
from ofertas.models import OfertaTicket
from sucursales.models import Sucursal
from tecnicos.models import Especialidad, Tecnico
from tickets.models import Categoria, Ticket

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


class OfertasApiTests(TestCase):
    """GET /api/v1/ofertas/ y /ofertas/<id>/: el técnico ve lo que puede tomar."""

    def setUp(self):
        self.client = APIClient()
        electricidad = Especialidad.objects.create(nombre="Electricidad")
        gasfiteria = Especialidad.objects.create(nombre="Gasfitería")
        self.cat_electrica = Categoria.objects.create(
            nombre="Eléctrica", especialidad=electricidad
        )
        self.cat_gas = Categoria.objects.create(nombre="Gas", especialidad=gasfiteria)
        self.cat_sin_especialidad = Categoria.objects.create(nombre="Otros")

        # Datos hipotéticos de prueba.
        empresa = Empresa.objects.create(nombre="Cadena Demo", rut="76.000.000-0", codigo="DEMO")
        self.sucursal = Sucursal.objects.create(
            empresa=empresa, nombre="Local Centro", codigo="CEN",
            direccion="Av. Ejemplo 123", comuna="Santiago", telefono="+56 2 2000 0000",
        )
        self.encargado = crear_usuario("encargado1", Usuario.Rol.ENCARGADO)

        self.user = crear_usuario("tecnico1", Usuario.Rol.TECNICO, tecnico=True)
        self.tecnico = self.user.tecnico
        self.tecnico.especialidades.set([electricidad])
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=self.user).key}"
        )

        self.oferta_electrica = self.crear_oferta("Enchufe quemado", self.cat_electrica)
        self.oferta_gas = self.crear_oferta("Fuga de gas", self.cat_gas)
        self.oferta_sin_especialidad = self.crear_oferta("Varios", self.cat_sin_especialidad)

    def crear_oferta(self, titulo, categoria, **campos):
        n = Ticket.objects.count() + 1
        ticket = Ticket.objects.create(
            numero=f"DEMO-{n:05d}", sucursal=self.sucursal, creador=self.encargado,
            categoria=categoria, titulo=titulo, descripcion=f"Detalle de {titulo}",
            estado=Ticket.Estado.PUBLICADO,
        )
        return OfertaTicket.objects.create(ticket=ticket, **campos)

    def ids_listado(self):
        resp = self.client.get(reverse("api:ofertas"))
        self.assertEqual(resp.status_code, 200)
        return [o["id"] for o in resp.data]

    def test_lista_solo_ofertas_de_su_especialidad(self):
        self.assertEqual(self.ids_listado(), [self.oferta_electrica.pk])

    def test_no_lista_ofertas_tomadas(self):
        self.oferta_electrica.estado = OfertaTicket.Estado.TOMADA
        self.oferta_electrica.save()
        self.assertEqual(self.ids_listado(), [])

    def test_expira_y_oculta_ofertas_vencidas(self):
        vencida = self.crear_oferta(
            "Luz cortada", self.cat_electrica,
            fecha_vencimiento=timezone.now() - timedelta(hours=1),
        )
        self.assertNotIn(vencida.pk, self.ids_listado())
        vencida.refresh_from_db()
        self.assertEqual(vencida.estado, OfertaTicket.Estado.EXPIRADA)

    def test_datos_de_la_oferta_sin_numero_interno_del_ticket(self):
        oferta = self.client.get(reverse("api:ofertas")).data[0]
        self.assertEqual(oferta["titulo"], "Enchufe quemado")
        self.assertEqual(oferta["especialidad"], "Electricidad")
        self.assertEqual(oferta["sucursal"]["direccion"], "Av. Ejemplo 123")
        self.assertEqual(oferta["empresa"], "Cadena Demo")
        self.assertNotIn("numero", oferta)
        self.assertNotIn("DEMO-", str(oferta))

    def test_detalle_de_una_oferta_que_puede_tomar(self):
        url = reverse("api:oferta_detalle", args=[self.oferta_electrica.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["descripcion"], "Detalle de Enchufe quemado")

    def test_detalle_de_otra_especialidad_responde_404(self):
        for oferta in (self.oferta_gas, self.oferta_sin_especialidad):
            with self.subTest(oferta=oferta.titulo):
                url = reverse("api:oferta_detalle", args=[oferta.pk])
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_detalle_de_oferta_tomada_por_el_mismo_tecnico(self):
        self.oferta_gas.estado = OfertaTicket.Estado.TOMADA
        self.oferta_gas.tecnico = self.tecnico
        self.oferta_gas.save()
        url = reverse("api:oferta_detalle", args=[self.oferta_gas.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_detalle_de_oferta_tomada_por_otro_responde_404(self):
        otro = crear_usuario("tecnico2", Usuario.Rol.TECNICO, tecnico=True).tecnico
        self.oferta_electrica.estado = OfertaTicket.Estado.TOMADA
        self.oferta_electrica.tecnico = otro
        self.oferta_electrica.save()
        url = reverse("api:oferta_detalle", args=[self.oferta_electrica.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_sin_token_responde_401(self):
        self.client.credentials()
        self.assertEqual(self.client.get(reverse("api:ofertas")).status_code, 401)

    def test_otro_rol_responde_403(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=self.encargado).key}"
        )
        self.assertEqual(self.client.get(reverse("api:ofertas")).status_code, 403)
