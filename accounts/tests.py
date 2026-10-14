"""Aislamiento del rol ENCARGADO por sucursal asignada.

Escenario cubierto:
- `sucursal_asignada`:      sucursal de la propia empresa con el encargado asignado.
- `sucursal_no_asignada`:   sucursal de la misma empresa SIN asignación.
- `sucursal_otra_empresa`:  sucursal de una empresa distinta.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from empresas.models import Empresa
from mantenimiento.models import PlanMantenimiento
from ofertas.models import OfertaTicket
from sucursales.forms import SucursalForm
from sucursales.models import Sucursal
from tecnicos.models import Especialidad, Tecnico
from tickets.models import Categoria, OrdenTrabajo, Ticket

from .models import Usuario
from .roles import (
    es_encargado_de,
    puede_gestionar_ticket,
    puede_ver_oferta,
    puede_ver_sucursal,
    puede_ver_ticket,
    sucursales_visibles,
    tickets_visibles,
)


class EscenarioEncargadoMixin:
    """Construye dos empresas, tres sucursales y el encargado asignado a una."""

    def setUp(self):
        self.empresa_a = Empresa.objects.create(
            nombre="Empresa Alfa", rut="76.111.111-1", codigo="ALFA"
        )
        self.empresa_b = Empresa.objects.create(
            nombre="Empresa Beta", rut="76.222.222-2", codigo="BETA"
        )

        self.sucursal_asignada = self.crear_sucursal(
            self.empresa_a, "Sucursal Asignada", "ASIG"
        )
        self.sucursal_no_asignada = self.crear_sucursal(
            self.empresa_a, "Sucursal No Asignada", "NOAS"
        )
        self.sucursal_otra_empresa = self.crear_sucursal(
            self.empresa_b, "Sucursal Otra Empresa", "OTRA"
        )

        self.encargado = self.crear_usuario(
            "encargado", Usuario.Rol.ENCARGADO, self.empresa_a
        )
        self.sucursal_asignada.encargados.add(self.encargado)

        self.categoria = Categoria.objects.create(nombre="Electricidad")

        self.ticket_propio = self.crear_ticket(self.sucursal_asignada, "ALFA-00001")
        self.ticket_no_asignado = self.crear_ticket(self.sucursal_no_asignada, "ALFA-00002")
        self.ticket_otra_empresa = self.crear_ticket(self.sucursal_otra_empresa, "BETA-00001")

        self.tecnico_usuario = User.objects.create_user(
            username="tecnico", password="clave-de-prueba"
        )
        Usuario.objects.create(user=self.tecnico_usuario, rol=Usuario.Rol.TECNICO, empresa=None)
        self.tecnico = Tecnico.objects.create(
            usuario=self.tecnico_usuario, estado=Tecnico.Estado.DISPONIBLE
        )

        self.orden_propia = OrdenTrabajo.objects.create(
            ticket=self.ticket_propio, tecnico=self.tecnico
        )
        self.orden_no_asignada = OrdenTrabajo.objects.create(
            ticket=self.ticket_no_asignado, tecnico=self.tecnico
        )
        self.orden_otra_empresa = OrdenTrabajo.objects.create(
            ticket=self.ticket_otra_empresa, tecnico=self.tecnico
        )

        self.oferta_propia = OfertaTicket.objects.create(
            ticket=self.ticket_propio, estado=OfertaTicket.Estado.DISPONIBLE
        )
        self.oferta_no_asignada = OfertaTicket.objects.create(
            ticket=self.ticket_no_asignado, estado=OfertaTicket.Estado.DISPONIBLE
        )
        self.oferta_otra_empresa = OfertaTicket.objects.create(
            ticket=self.ticket_otra_empresa, estado=OfertaTicket.Estado.DISPONIBLE
        )

        self.plan_propio = self.crear_plan(self.sucursal_asignada, "Plan Asignado")
        self.plan_no_asignado = self.crear_plan(self.sucursal_no_asignada, "Plan No Asignado")
        self.plan_otra_empresa = self.crear_plan(self.sucursal_otra_empresa, "Plan Otra Empresa")

    def crear_sucursal(self, empresa, nombre, codigo):
        return Sucursal.objects.create(
            empresa=empresa, nombre=nombre, codigo=codigo, direccion=f"Calle {nombre}"
        )

    def crear_usuario(self, username, rol, empresa):
        user = User.objects.create_user(username=username, password="clave-de-prueba")
        Usuario.objects.create(user=user, rol=rol, empresa=empresa)
        return user

    def crear_ticket(self, sucursal, numero):
        return Ticket.objects.create(
            numero=numero,
            sucursal=sucursal,
            categoria=self.categoria,
            creador=self.encargado,
            titulo=f"Incidencia {numero}",
            descripcion="Descripción de la incidencia.",
        )

    def crear_plan(self, sucursal, nombre):
        return PlanMantenimiento.objects.create(
            nombre=nombre,
            sucursal=sucursal,
            categoria=self.categoria,
            fecha_proxima=timezone.now() - timezone.timedelta(days=1),
        )

    def entrar(self, user):
        self.assertTrue(self.client.login(username=user.username, password="clave-de-prueba"))
        return user


class VisibilidadQuerysetTests(EscenarioEncargadoMixin, TestCase):
    """Los querysets de aislamiento solo incluyen las sucursales asignadas."""

    def test_sucursales_visibles_solo_las_asignadas(self):
        visibles = sucursales_visibles(self.encargado)

        self.assertEqual(list(visibles), [self.sucursal_asignada])
        self.assertNotIn(self.sucursal_no_asignada, visibles)
        self.assertNotIn(self.sucursal_otra_empresa, visibles)

    def test_tickets_visibles_solo_los_de_sus_sucursales(self):
        visibles = tickets_visibles(self.encargado)

        self.assertEqual(list(visibles), [self.ticket_propio])

    def test_es_encargado_de_exige_sucursal_de_su_empresa(self):
        """Una asignación indebida a otra empresa no habilita el acceso."""
        self.sucursal_otra_empresa.encargados.add(self.encargado)

        self.assertFalse(es_encargado_de(self.encargado, self.sucursal_otra_empresa))
        self.assertFalse(puede_ver_sucursal(self.encargado, self.sucursal_otra_empresa))
        self.assertFalse(puede_ver_ticket(self.encargado, self.ticket_otra_empresa))
        self.assertFalse(puede_ver_oferta(self.encargado, self.oferta_otra_empresa))
        self.assertNotIn(self.sucursal_otra_empresa, sucursales_visibles(self.encargado))


class VisibilidadSucursalesTests(EscenarioEncargadoMixin, TestCase):
    """Listados y detalle de sucursales."""

    def setUp(self):
        super().setUp()
        self.entrar(self.encargado)

    def test_lista_muestra_solo_su_sucursal(self):
        respuesta = self.client.get(reverse("sucursales:lista"))

        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.content.decode()
        self.assertIn(self.sucursal_asignada.nombre, contenido)
        self.assertNotIn(self.sucursal_no_asignada.nombre, contenido)
        self.assertNotIn(self.sucursal_otra_empresa.nombre, contenido)

    def test_detalle_de_su_sucursal(self):
        respuesta = self.client.get(
            reverse("sucursales:detalle", args=[self.sucursal_asignada.pk])
        )

        self.assertEqual(respuesta.status_code, 200)

    def test_detalle_sucursal_no_asignada_por_url(self):
        respuesta = self.client.get(
            reverse("sucursales:detalle", args=[self.sucursal_no_asignada.pk])
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_detalle_sucursal_de_otra_empresa_por_url(self):
        respuesta = self.client.get(
            reverse("sucursales:detalle", args=[self.sucursal_otra_empresa.pk])
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_no_puede_crear_sucursales(self):
        respuesta = self.client.get(reverse("sucursales:crear"))

        self.assertEqual(respuesta.status_code, 403)

    def test_no_puede_editar_su_sucursal_ni_asignarse_otras(self):
        """No administra sucursales: tampoco la suya ni puede cambiar el alcance."""
        editar = self.client.get(
            reverse("sucursales:editar", args=[self.sucursal_asignada.pk])
        )
        enviar = self.client.post(
            reverse("sucursales:editar", args=[self.sucursal_asignada.pk]),
            {
                "nombre": self.sucursal_asignada.nombre,
                "codigo": self.sucursal_asignada.codigo,
                "direccion": self.sucursal_asignada.direccion,
                "encargados": [self.sucursal_no_asignada.pk],
                "estado": self.sucursal_asignada.estado,
            },
        )

        self.assertEqual(editar.status_code, 403)
        self.assertEqual(enviar.status_code, 403)
        self.assertNotIn(
            self.encargado, self.sucursal_no_asignada.encargados.all()
        )


class AislamientoTicketsTests(EscenarioEncargadoMixin, TestCase):
    """Tickets, ofertas y órdenes de trabajo."""

    def setUp(self):
        super().setUp()
        self.entrar(self.encargado)

    def test_lista_de_tickets_muestra_solo_sus_tickets(self):
        respuesta = self.client.get(reverse("tickets:lista"))

        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.content.decode()
        self.assertIn(self.ticket_propio.numero, contenido)
        self.assertNotIn(self.ticket_no_asignado.numero, contenido)
        self.assertNotIn(self.ticket_otra_empresa.numero, contenido)

    def test_detalle_de_ticket_ajeno_por_url(self):
        for ticket in (self.ticket_no_asignado, self.ticket_otra_empresa):
            with self.subTest(ticket=ticket.numero):
                respuesta = self.client.get(
                    reverse("tickets:detalle", args=[ticket.numero])
                )
                self.assertEqual(respuesta.status_code, 403)

    def test_no_puede_cambiar_estado_de_ticket_ajeno(self):
        respuesta = self.client.post(
            reverse("tickets:cambiar_estado", args=[self.ticket_no_asignado.numero]),
            {"estado": Ticket.Estado.EN_REVISION, "comentario": ""},
        )

        self.assertEqual(respuesta.status_code, 403)
        self.ticket_no_asignado.refresh_from_db()
        self.assertEqual(self.ticket_no_asignado.estado, Ticket.Estado.ABIERTO)

    def test_crear_ticket_solo_para_su_sucursal(self):
        datos = {
            "sucursal": self.sucursal_asignada.pk,
            "categoria": self.categoria.pk,
            "prioridad": Ticket.Prioridad.MEDIA,
            "tipo": Ticket.Tipo.INCIDENCIA,
            "titulo": "Fuga en mi sucursal",
            "descripcion": "Descripción",
        }
        permitido = self.client.post(reverse("tickets:crear"), datos)

        self.assertEqual(permitido.status_code, 302)
        creado = Ticket.objects.filter(sucursal=self.sucursal_asignada).exclude(
            pk=self.ticket_propio.pk
        )
        self.assertEqual(creado.count(), 1)
        self.assertEqual(creado.first().creador, self.encargado)

    def test_crear_ticket_en_sucursal_no_asignada_es_rechazado(self):
        respuesta = self.client.post(
            reverse("tickets:crear"),
            {
                "sucursal": self.sucursal_no_asignada.pk,
                "categoria": self.categoria.pk,
                "prioridad": Ticket.Prioridad.MEDIA,
                "tipo": Ticket.Tipo.INCIDENCIA,
                "titulo": "Fuga ajena",
                "descripcion": "Descripción",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(
            Ticket.objects.filter(sucursal=self.sucursal_no_asignada).exclude(
                pk=self.ticket_no_asignado.pk
            ).exists()
        )

    def test_crear_ticket_en_sucursal_de_otra_empresa_es_rechazado(self):
        respuesta = self.client.post(
            reverse("tickets:crear"),
            {
                "sucursal": self.sucursal_otra_empresa.pk,
                "categoria": self.categoria.pk,
                "prioridad": Ticket.Prioridad.MEDIA,
                "tipo": Ticket.Tipo.INCIDENCIA,
                "titulo": "Fuga ajena",
                "descripcion": "Descripción",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(
            Ticket.objects.filter(sucursal=self.sucursal_otra_empresa).exclude(
                pk=self.ticket_otra_empresa.pk
            ).exists()
        )

    def test_no_puede_publicar_oferta_de_ticket_ajeno(self):
        respuesta = self.client.get(
            reverse("tickets:publicar_oferta", args=[self.ticket_no_asignado.numero])
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_detalle_de_oferta_ajena_por_url(self):
        for oferta in (self.oferta_no_asignada, self.oferta_otra_empresa):
            with self.subTest(oferta=oferta.pk):
                respuesta = self.client.get(
                    reverse("ofertas:detalle", args=[oferta.pk])
                )
                self.assertEqual(respuesta.status_code, 403)

    def test_ofertas_disponibles_solo_de_sus_sucursales(self):
        respuesta = self.client.get(reverse("ofertas:disponibles"))

        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.content.decode()
        self.assertIn(self.ticket_propio.titulo, contenido)
        self.assertNotIn(self.ticket_no_asignado.titulo, contenido)
        self.assertNotIn(self.ticket_otra_empresa.titulo, contenido)

    def test_lista_de_ordenes_solo_de_sus_sucursales(self):
        respuesta = self.client.get(reverse("ordenes:lista"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            list(respuesta.context["ordenes"]),
            [self.orden_propia],
        )

    def test_detalle_de_orden_ajena_por_url(self):
        for orden in (self.orden_no_asignada, self.orden_otra_empresa):
            with self.subTest(orden=orden.pk):
                respuesta = self.client.get(reverse("ordenes:detalle", args=[orden.pk]))
                self.assertEqual(respuesta.status_code, 403)

    def test_no_puede_cerrar_orden_ajena(self):
        respuesta = self.client.post(
            reverse("ordenes:cambiar_estado", args=[self.orden_no_asignada.pk]),
            {"estado": OrdenTrabajo.Estado.CERRADA, "puntuacion": 5},
        )

        self.assertEqual(respuesta.status_code, 403)
        self.orden_no_asignada.refresh_from_db()
        self.assertEqual(self.orden_no_asignada.estado, OrdenTrabajo.Estado.ASIGNADA)


class AislamientoDashboardTests(EscenarioEncargadoMixin, TestCase):
    """Los indicadores del dashboard solo cubren las sucursales asignadas."""

    def setUp(self):
        super().setUp()
        self.entrar(self.encargado)

    def test_dashboard_cuenta_solo_sus_tickets_y_ordenes(self):
        respuesta = self.client.get(reverse("dashboard"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["tickets_abiertos"], 1)
        self.assertEqual(respuesta.context["ordenes_trabajo"], 1)
        self.assertEqual(respuesta.context["ofertas_disponibles"], 1)
        self.assertEqual(
            list(respuesta.context["tickets_recientes"]),
            [self.ticket_propio],
        )

    def test_dashboard_no_expone_ordenes_ajenas(self):
        contenido = self.client.get(reverse("dashboard")).content.decode()

        self.assertNotIn(self.ticket_no_asignado.numero, contenido)
        self.assertNotIn(self.ticket_otra_empresa.numero, contenido)

    def test_dashboard_sin_sucursales_asignadas_queda_vacio(self):
        self.sucursal_asignada.encargados.clear()

        respuesta = self.client.get(reverse("dashboard"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["tickets_abiertos"], 0)
        self.assertEqual(respuesta.context["ordenes_trabajo"], 0)

    def test_no_accede_a_reportes(self):
        respuesta = self.client.get(reverse("reportes"))

        self.assertEqual(respuesta.status_code, 403)


class AislamientoMantenimientoTests(EscenarioEncargadoMixin, TestCase):
    """Planes de mantenimiento y generación de preventivos."""

    def setUp(self):
        super().setUp()
        self.entrar(self.encargado)

    def test_lista_de_planes_muestra_solo_sus_sucursales(self):
        respuesta = self.client.get(reverse("mantenimiento:lista"))

        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.content.decode()
        self.assertIn(self.plan_propio.nombre, contenido)
        self.assertNotIn(self.plan_no_asignado.nombre, contenido)
        self.assertNotIn(self.plan_otra_empresa.nombre, contenido)

    def test_detalle_de_plan_ajeno_por_url(self):
        for plan in (self.plan_no_asignado, self.plan_otra_empresa):
            with self.subTest(plan=plan.nombre):
                respuesta = self.client.get(reverse("mantenimiento:detalle", args=[plan.pk]))
                self.assertEqual(respuesta.status_code, 404)

    def test_generar_preventivos_solo_de_sus_sucursales(self):
        respuesta = self.client.post(reverse("mantenimiento:lista"))

        self.assertEqual(respuesta.status_code, 200)
        preventivos = Ticket.objects.filter(tipo=Ticket.Tipo.PREVENTIVO)
        self.assertEqual(
            list(preventivos.values_list("sucursal", flat=True)),
            [self.sucursal_asignada.pk],
        )
        self.plan_no_asignado.refresh_from_db()
        self.plan_otra_empresa.refresh_from_db()
        self.assertFalse(self.plan_no_asignado.programaciones.exists())
        self.assertFalse(self.plan_otra_empresa.programaciones.exists())


class AislamientoTecnicosTests(EscenarioEncargadoMixin, TestCase):
    """El detalle de un técnico no revela órdenes de sucursales ajenas."""

    def setUp(self):
        super().setUp()
        self.entrar(self.encargado)

    def test_detalle_tecnico_solo_muestra_ordenes_permitidas(self):
        respuesta = self.client.get(reverse("tecnicos:detalle", args=[self.tecnico.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(list(respuesta.context["ordenes"]), [self.orden_propia])


class AsignacionSucursalesTests(EscenarioEncargadoMixin, TestCase):
    """La asignación de un encargado se hace desde un rol con permisos."""

    def test_formulario_rechaza_encargado_de_otra_empresa(self):
        encargado_b = self.crear_usuario(
            "encargado_beta", Usuario.Rol.ENCARGADO, self.empresa_b
        )
        formulario = SucursalForm(
            data={
                "nombre": self.sucursal_asignada.nombre,
                "codigo": self.sucursal_asignada.codigo,
                "direccion": self.sucursal_asignada.direccion,
                "encargados": [encargado_b.pk],
                "estado": Sucursal.Estado.ACTIVA,
            },
            empresa=self.empresa_a,
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("encargados", formulario.errors)

    def test_formulario_rechaza_usuario_ajeno_a_la_empresa(self):
        for usuario in (
            self.crear_usuario("encargado_beta", Usuario.Rol.ENCARGADO, self.empresa_b),
            self.tecnico_usuario,
        ):
            with self.subTest(usuario=usuario.username):
                formulario = SucursalForm(
                    data={
                        "nombre": self.sucursal_asignada.nombre,
                        "codigo": self.sucursal_asignada.codigo,
                        "direccion": self.sucursal_asignada.direccion,
                        "encargados": [usuario.pk],
                        "estado": Sucursal.Estado.ACTIVA,
                    },
                    empresa=self.empresa_a,
                )

                self.assertFalse(formulario.is_valid())
                self.assertIn("encargados", formulario.errors)

    def test_formulario_acepta_encargado_de_la_misma_empresa(self):
        formulario = SucursalForm(
            data={
                "nombre": "Sucursal Reasignada",
                "codigo": "REAS",
                "direccion": "Calle Reasignada",
                "encargados": [self.encargado.pk],
                "estado": Sucursal.Estado.ACTIVA,
            },
            empresa=self.empresa_a,
        )

        self.assertTrue(formulario.is_valid(), formulario.errors)


class RestriccionAdminTests(EscenarioEncargadoMixin, TestCase):
    """El rol ENCARGADO no utiliza el Django Admin."""

    def test_encargado_staff_no_entra_al_admin(self):
        self.encargado.is_staff = True
        self.encargado.save()
        self.entrar(self.encargado)

        respuesta = self.client.get("/admin/")

        self.assertNotEqual(respuesta.status_code, 200)

    def test_encargado_staff_no_llega_a_una_sucursal_por_url(self):
        self.encargado.is_staff = True
        self.encargado.save()
        self.entrar(self.encargado)

        respuesta = self.client.get(
            f"/admin/sucursales/sucursal/{self.sucursal_otra_empresa.pk}/change/"
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta.url.startswith(reverse("admin:login")))

    def test_admin_de_empresa_sigue_entrando(self):
        admin_a = self.crear_usuario("admin_a", Usuario.Rol.ADMIN, self.empresa_a)
        admin_a.is_staff = True
        admin_a.save()
        self.entrar(admin_a)

        respuesta = self.client.get("/admin/")

        self.assertEqual(respuesta.status_code, 200)


class BotonesSegunRolTests(EscenarioEncargadoMixin, TestCase):
    """Los botones coinciden con lo que el backend realmente permite.

    GERENCIA entra al listado de tickets pero no crea tickets ni publica
    ofertas: antes veía los botones y recibía un 403.
    """

    def setUp(self):
        super().setUp()
        self.gerencia = self.crear_usuario(
            "gerencia_a", Usuario.Rol.GERENCIA, self.empresa_a
        )
        self.entrar(self.gerencia)

    def test_gerencia_ve_el_listado_sin_botones_de_gestion(self):
        respuesta = self.client.get(reverse("tickets:lista"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.context["puede_gestionar_tickets"])
        contenido = respuesta.content.decode()
        self.assertNotIn(reverse("tickets:crear"), contenido)
        self.assertNotIn(
            reverse("tickets:publicar_oferta", args=[self.ticket_propio.numero]),
            contenido,
        )

    def test_gerencia_no_puede_crear_ticket(self):
        respuesta = self.client.get(reverse("tickets:crear"))

        self.assertEqual(respuesta.status_code, 403)

    def test_gerencia_no_puede_publicar_oferta(self):
        respuesta = self.client.get(
            reverse("tickets:publicar_oferta", args=[self.ticket_propio.numero])
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_encargado_sigue_viendo_los_botones(self):
        self.entrar(self.encargado)

        respuesta = self.client.get(reverse("tickets:lista"))

        self.assertTrue(respuesta.context["puede_gestionar_tickets"])
        self.assertIn(reverse("tickets:crear"), respuesta.content.decode())

    def test_publicar_oferta_no_se_muestra_si_el_ticket_no_es_publicable(self):
        self.ticket_propio.estado = Ticket.Estado.CERRADO
        self.ticket_propio.save()
        self.entrar(self.encargado)

        respuesta = self.client.get(
            reverse("tickets:detalle", args=[self.ticket_propio.numero])
        )

        self.assertFalse(respuesta.context["puede_publicar_oferta"])
        self.assertNotIn(
            reverse("tickets:publicar_oferta", args=[self.ticket_propio.numero]),
            respuesta.content.decode(),
        )


class RegresionOtrosRolesTests(EscenarioEncargadoMixin, TestCase):
    """ADMIN, GESTOR, GERENCIA y TECNICO conservan su alcance."""

    def test_admin_ve_todas_las_sucursales_de_su_empresa(self):
        admin_a = self.crear_usuario("admin_a", Usuario.Rol.ADMIN, self.empresa_a)

        self.assertEqual(
            list(sucursales_visibles(admin_a)),
            [self.sucursal_asignada, self.sucursal_no_asignada],
        )

    def test_gestor_ve_todas_las_sucursales_de_su_empresa(self):
        gestor_a = self.crear_usuario("gestor_a", Usuario.Rol.GESTOR, self.empresa_a)

        self.assertEqual(
            list(sucursales_visibles(gestor_a)),
            [self.sucursal_asignada, self.sucursal_no_asignada],
        )

    def test_admin_ve_las_ordenes_de_su_empresa(self):
        admin_a = self.crear_usuario("admin_a", Usuario.Rol.ADMIN, self.empresa_a)
        self.entrar(admin_a)

        respuesta = self.client.get(reverse("ordenes:lista"))

        self.assertEqual(
            set(respuesta.context["ordenes"]),
            {self.orden_propia, self.orden_no_asignada},
        )

    def test_tecnico_ve_solo_las_ordenes_asignadas(self):
        self.entrar(self.tecnico_usuario)

        respuesta = self.client.get(reverse("ordenes:lista"))

        self.assertEqual(
            set(respuesta.context["ordenes"]),
            {self.orden_propia, self.orden_no_asignada, self.orden_otra_empresa},
        )

    def test_superuser_ve_todas_las_sucursales(self):
        superuser = User.objects.create_superuser(
            username="root", password="clave-de-prueba", email=""
        )

        self.assertEqual(
            set(sucursales_visibles(superuser)),
            {
                self.sucursal_asignada,
                self.sucursal_no_asignada,
                self.sucursal_otra_empresa,
            },
        )


class EscrituraTicketTests(EscenarioEncargadoMixin, TestCase):
    """#1 Ver una oferta disponible NO habilita a cambiar el estado del ticket.

    Regresión del exploit: `cambiar_estado` solo comprobaba lectura, así que un
    técnico podía resolver cualquier ticket publicado en el marketplace.
    """

    def setUp(self):
        super().setUp()
        # Ticket publicado y disponible en el marketplace, SIN orden para este
        # técnico: es exactamente el caso que el exploit necesitaba.
        self.ticket_publicado = Ticket.objects.create(
            numero="ALFA-00003",
            sucursal=self.sucursal_asignada,
            categoria=self.categoria,
            creador=self.encargado,
            titulo="Incidencia publicada sin técnico asignado",
            descripcion="Descripción de la incidencia.",
            estado=Ticket.Estado.PUBLICADO,
        )
        OfertaTicket.objects.create(
            ticket=self.ticket_publicado, estado=OfertaTicket.Estado.DISPONIBLE
        )

    def test_el_tecnico_puede_leer_pero_no_escribir(self):
        self.entrar(self.tecnico_usuario)

        # Lectura permitida: la oferta está publicada en el marketplace.
        self.assertTrue(puede_ver_ticket(self.tecnico_usuario, self.ticket_publicado))
        # Escritura denegada: no tiene orden viva sobre este ticket.
        self.assertFalse(
            puede_gestionar_ticket(self.tecnico_usuario, self.ticket_publicado)
        )

    def test_tecnico_no_cambia_el_estado_de_un_ticket_que_no_gestiona(self):
        self.entrar(self.tecnico_usuario)

        respuesta = self.client.post(
            reverse("tickets:cambiar_estado", args=[self.ticket_publicado.numero]),
            {"estado": Ticket.Estado.EN_EJECUCION, "comentario": "Lo tomo yo."},
        )

        self.assertEqual(respuesta.status_code, 403)
        self.ticket_publicado.refresh_from_db()
        self.assertEqual(self.ticket_publicado.estado, Ticket.Estado.PUBLICADO)

    def test_el_encargado_su_cambia_el_estado_de_su_sucursal(self):
        self.entrar(self.encargado)

        self.assertTrue(
            puede_gestionar_ticket(self.encargado, self.ticket_publicado)
        )
        respuesta = self.client.post(
            reverse("tickets:cambiar_estado", args=[self.ticket_publicado.numero]),
            {"estado": Ticket.Estado.EN_EJECUCION},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.ticket_publicado.refresh_from_db()
        self.assertEqual(self.ticket_publicado.estado, Ticket.Estado.EN_EJECUCION)

    def test_el_tecnico_si_puede_cambiar_el_estado_con_orden_viva(self):
        """La autorización no es una prohibición total para el técnico."""
        OrdenTrabajo.objects.create(
            ticket=self.ticket_publicado, tecnico=self.tecnico
        )
        self.entrar(self.tecnico_usuario)

        self.assertTrue(
            puede_gestionar_ticket(self.tecnico_usuario, self.ticket_publicado)
        )

    def test_el_encargado_no_gestiona_tickets_de_otra_empresa(self):
        self.entrar(self.encargado)

        self.assertFalse(
            puede_gestionar_ticket(self.encargado, self.ticket_otra_empresa)
        )
        respuesta = self.client.post(
            reverse("tickets:cambiar_estado", args=[self.ticket_otra_empresa.numero]),
            {"estado": Ticket.Estado.CANCELADO},
        )

        self.assertEqual(respuesta.status_code, 403)


class ReaperturaTicketTests(EscenarioEncargadoMixin, TestCase):
    """#10 Reabrir un ticket limpia la fecha de cierre."""

    def setUp(self):
        super().setUp()
        # RESUELTO -> EN_EJECUCION es la reapertura: la máquina de estados no
        # permite salir de CERRADO ni de CANCELADO.
        self.ticket_propio.estado = Ticket.Estado.RESUELTO
        self.ticket_propio.fecha_cierre = timezone.now() - timezone.timedelta(days=3)
        self.ticket_propio.save()
        self.entrar(self.encargado)

    def test_reabrir_deja_fecha_cierre_vacia(self):
        self.client.post(
            reverse("tickets:cambiar_estado", args=[self.ticket_propio.numero]),
            {"estado": Ticket.Estado.EN_EJECUCION},
        )

        self.ticket_propio.refresh_from_db()
        self.assertEqual(self.ticket_propio.estado, Ticket.Estado.EN_EJECUCION)
        self.assertIsNone(self.ticket_propio.fecha_cierre)

    def test_cerrar_asigna_fecha_cierre(self):
        self.ticket_propio.fecha_cierre = None
        self.ticket_propio.save()

        self.client.post(
            reverse("tickets:cambiar_estado", args=[self.ticket_propio.numero]),
            {"estado": Ticket.Estado.CERRADO},
        )

        self.ticket_propio.refresh_from_db()
        self.assertEqual(self.ticket_propio.estado, Ticket.Estado.CERRADO)
        self.assertIsNotNone(self.ticket_propio.fecha_cierre)


class PublicarOfertaGetTests(EscenarioEncargadoMixin, TestCase):
    """#8 Un simple GET no debe crear ni publicar la oferta."""

    def setUp(self):
        super().setUp()
        OfertaTicket.objects.filter(ticket=self.ticket_propio).delete()
        self.entrar(self.encargado)

    def test_get_no_crea_la_oferta(self):
        respuesta = self.client.get(
            reverse("tickets:publicar_oferta", args=[self.ticket_propio.numero])
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(OfertaTicket.objects.filter(ticket=self.ticket_propio).exists())
        self.ticket_propio.refresh_from_db()
        self.assertEqual(self.ticket_propio.estado, Ticket.Estado.ABIERTO)

    def test_post_si_publica_la_oferta(self):
        respuesta = self.client.post(
            reverse("tickets:publicar_oferta", args=[self.ticket_propio.numero]),
            {"fecha_vencimiento": "", "observaciones": "Urgente"},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(OfertaTicket.objects.filter(ticket=self.ticket_propio).exists())
        self.ticket_propio.refresh_from_db()
        self.assertEqual(self.ticket_propio.estado, Ticket.Estado.PUBLICADO)


class CuentasTecnicoTests(EscenarioEncargadoMixin, TestCase):
    """#4 y #3 Las cuentas de técnicos las administra el superusuario, no un ADMIN."""

    def setUp(self):
        super().setUp()
        self.admin_a = self.crear_usuario("admin_a", Usuario.Rol.ADMIN, self.empresa_a)

    def test_admin_no_ve_los_tecnicos_en_el_listado_de_usuarios(self):
        self.entrar(self.admin_a)

        respuesta = self.client.get(reverse("usuarios"))

        self.assertEqual(respuesta.status_code, 200)
        # Se comprueba el enlace de edición, no el literal "tecnico": el sidebar
        # siempre incluye /tecnicos/.
        self.assertNotContains(
            respuesta, reverse("usuario_editar", args=[self.tecnico_usuario.pk])
        )
        self.assertContains(
            respuesta, reverse("usuario_editar", args=[self.admin_a.pk])
        )

    def test_admin_no_puede_editar_la_cuenta_de_un_tecnico(self):
        self.entrar(self.admin_a)

        respuesta = self.client.post(
            reverse("usuario_editar", args=[self.tecnico_usuario.pk]),
            {
                "username": "tecnico",
                "first_name": "Intruso",
                "email": "intruso@ejemplo.com",
                "is_active": "on",
                "rol": Usuario.Rol.ADMIN,
                "telefono": "",
            },
        )

        self.assertEqual(respuesta.status_code, 403)
        self.tecnico_usuario.refresh_from_db()
        self.assertEqual(self.tecnico_usuario.first_name, "")
        self.assertEqual(
            Usuario.objects.get(user=self.tecnico_usuario).rol, Usuario.Rol.TECNICO
        )

    def test_superuser_si_puede_editar_la_cuenta_de_un_tecnico(self):
        superuser = User.objects.create_superuser(
            username="root", password="clave-de-prueba", email=""
        )
        self.entrar(superuser)

        respuesta = self.client.post(
            reverse("usuario_editar", args=[self.tecnico_usuario.pk]),
            {
                "username": "tecnico",
                "first_name": "Tecnico",
                "email": "tecnico@ejemplo.com",
                "is_active": "on",
                "rol": Usuario.Rol.TECNICO,
                "telefono": "",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        self.tecnico_usuario.refresh_from_db()
        self.assertEqual(self.tecnico_usuario.first_name, "Tecnico")

    def test_admin_no_crea_tecnicos(self):
        self.entrar(self.admin_a)

        for url in (
            reverse("tecnicos:crear"),
            reverse("tecnicos:editar", args=[self.tecnico.pk]),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_admin_no_ve_los_enlaces_de_gestion_de_tecnicos(self):
        self.entrar(self.admin_a)

        lista = self.client.get(reverse("tecnicos:lista"))
        detalle = self.client.get(reverse("tecnicos:detalle", args=[self.tecnico.pk]))

        for respuesta in (lista, detalle):
            self.assertNotContains(respuesta, reverse("tecnicos:crear"))
            self.assertNotContains(respuesta, reverse("tecnicos:editar", args=[self.tecnico.pk]))

    def test_superuser_si_administra_tecnicos(self):
        superuser = User.objects.create_superuser(
            username="root", password="clave-de-prueba", email=""
        )
        self.entrar(superuser)

        lista = self.client.get(reverse("tecnicos:lista"))
        detalle = self.client.get(reverse("tecnicos:detalle", args=[self.tecnico.pk]))

        # El alta se muestra en el listado; la edición, en la ficha.
        self.assertContains(lista, reverse("tecnicos:crear"))
        self.assertContains(
            detalle, reverse("tecnicos:editar", args=[self.tecnico.pk])
        )


class EspecialidadOfertaTests(EscenarioEncargadoMixin, TestCase):
    """#13 Tomar una oferta exige categoría con especialidad y perfil compatible."""

    def setUp(self):
        super().setUp()
        self.electricidad = Especialidad.objects.create(nombre="Electricidad")
        self.gasfiteria = Especialidad.objects.create(nombre="Gasfitería")
        self.categoria.especialidad = self.electricidad
        self.categoria.save()

        self.ticket_propio.categoria = self.categoria
        self.ticket_propio.estado = Ticket.Estado.PUBLICADO
        self.ticket_propio.save()
        self.tecnico.especialidades.add(self.electricidad)

        self.entrar(self.tecnico_usuario)

    def test_toma_la_oferta_si_tiene_la_especialidad(self):
        respuesta = self.client.get(reverse("ofertas:tomar", args=[self.oferta_propia.pk]))

        self.assertEqual(respuesta.status_code, 302)
        self.oferta_propia.refresh_from_db()
        self.assertEqual(self.oferta_propia.estado, OfertaTicket.Estado.TOMADA)

    def test_no_toma_si_le_falta_la_especialidad(self):
        self.tecnico.especialidades.clear()
        self.tecnico.especialidades.add(self.gasfiteria)
        ordenes_previas = set(
            OrdenTrabajo.objects.values_list("pk", flat=True)
        )

        respuesta = self.client.get(reverse("ofertas:tomar", args=[self.oferta_propia.pk]))

        self.assertEqual(respuesta.status_code, 302)
        self.oferta_propia.refresh_from_db()
        self.assertEqual(self.oferta_propia.estado, OfertaTicket.Estado.DISPONIBLE)
        self.assertIsNone(self.oferta_propia.tecnico)
        # No se genera ninguna orden nueva ni se ocupa al técnico.
        self.assertEqual(
            set(OrdenTrabajo.objects.values_list("pk", flat=True)), ordenes_previas
        )
        self.tecnico.refresh_from_db()
        self.assertEqual(self.tecnico.estado, Tecnico.Estado.DISPONIBLE)

    def test_no_toma_si_la_categoria_no_tiene_especialidad(self):
        self.categoria.especialidad = None
        self.categoria.save()

        respuesta = self.client.get(reverse("ofertas:tomar", args=[self.oferta_propia.pk]))

        self.assertEqual(respuesta.status_code, 302)
        self.oferta_propia.refresh_from_db()
        self.assertEqual(self.oferta_propia.estado, OfertaTicket.Estado.DISPONIBLE)
        self.assertIsNone(self.oferta_propia.tecnico)


class DocumentoOpcionalTests(EscenarioEncargadoMixin, TestCase):
    """#16 Varios técnicos pueden quedar sin documento de identificación."""

    def test_dos_tecnicos_sin_documento_no_colisionan(self):
        otro_usuario = User.objects.create_user(
            username="tecnico2", password="clave-de-prueba"
        )
        Usuario.objects.create(
            user=otro_usuario, rol=Usuario.Rol.TECNICO, empresa=None
        )

        segundo = Tecnico.objects.create(
            usuario=otro_usuario, estado=Tecnico.Estado.DISPONIBLE
        )

        self.assertIsNone(self.tecnico.documento or None)
        self.assertIsNone(segundo.documento)