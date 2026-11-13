from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from empresas.models import Empresa
from sucursales.models import Sucursal
from tecnicos.models import Tecnico

from .models import Calificacion, Categoria, OrdenTrabajo, Ticket, TicketHistorial
from .services import TransicionNoPermitida, cambiar_estado_orden, transiciones_permitidas

CLAVE = "Clave.Segura1"


class EscenarioOrdenMixin:
    """Una empresa con un local, su encargado, Gerencia y un técnico con una orden asignada."""

    def setUp(self):
        # Datos hipotéticos de prueba.
        self.empresa = Empresa.objects.create(nombre="Cadena Demo", rut="76.000.000-0", codigo="DEMO")
        sucursal = Sucursal.objects.create(
            empresa=self.empresa, nombre="Local Centro", codigo="CEN", direccion="Av. Ejemplo 123"
        )
        self.encargado = self.crear_usuario("encargado1", Usuario.Rol.ENCARGADO, self.empresa)
        sucursal.encargados.add(self.encargado)
        self.gerencia = self.crear_usuario("gerencia1", Usuario.Rol.GERENCIA, self.empresa)
        self.tecnico_user = self.crear_usuario("tecnico1", Usuario.Rol.TECNICO)
        self.tecnico = Tecnico.objects.create(
            usuario=self.tecnico_user, estado=Tecnico.Estado.OCUPADO
        )
        self.ticket = Ticket.objects.create(
            numero="DEMO-00001", sucursal=sucursal, creador=self.encargado,
            categoria=Categoria.objects.create(nombre="Eléctrica"),
            titulo="Enchufe quemado", descripcion="Sin energía",
            estado=Ticket.Estado.EN_EJECUCION,
        )
        self.orden = OrdenTrabajo.objects.create(ticket=self.ticket, tecnico=self.tecnico)

    @staticmethod
    def crear_usuario(username, rol, empresa=None):
        user = User.objects.create_user(username=username, password=CLAVE)
        Usuario.objects.create(user=user, rol=rol, empresa=empresa)
        return user

    def recargar(self):
        for obj in (self.orden, self.ticket, self.tecnico):
            obj.refresh_from_db()


class CambiarEstadoOrdenServicioTests(EscenarioOrdenMixin, TestCase):
    """tickets.services.cambiar_estado_orden: la regla única que usan la web y la API."""

    def assertCodigo(self, codigo, destino, usuario, datos=None):
        with self.assertRaises(TransicionNoPermitida) as ctx:
            cambiar_estado_orden(self.orden, destino, usuario, datos=datos)
        self.assertEqual(ctx.exception.codigo, codigo)

    def iniciar(self):
        cambiar_estado_orden(
            self.orden, OrdenTrabajo.Estado.EN_EJECUCION, self.tecnico_user,
            datos={"diagnostico": "Enchufe derretido"},
        )

    def test_iniciar_guarda_diagnostico_y_fecha(self):
        self.iniciar()
        self.recargar()
        self.assertEqual(self.orden.estado, OrdenTrabajo.Estado.EN_EJECUCION)
        self.assertEqual(self.orden.diagnostico, "Enchufe derretido")
        self.assertIsNotNone(self.orden.fecha_inicio)

    def test_iniciar_sin_diagnostico(self):
        self.assertCodigo("falta_diagnostico", OrdenTrabajo.Estado.EN_EJECUCION, self.tecnico_user)
        self.recargar()
        self.assertEqual(self.orden.estado, OrdenTrabajo.Estado.ASIGNADA)

    def test_resolver_sincroniza_ticket_historial_y_libera_al_tecnico(self):
        self.iniciar()
        cambiar_estado_orden(
            self.orden, OrdenTrabajo.Estado.RESUELTA, self.tecnico_user,
            datos={"trabajo_realizado": "Cambio de enchufe", "costo_final": 15000},
        )
        self.recargar()
        self.assertEqual(self.orden.estado, OrdenTrabajo.Estado.RESUELTA)
        self.assertEqual(self.orden.trabajo_realizado, "Cambio de enchufe")
        self.assertIsNotNone(self.orden.fecha_fin)
        self.assertEqual(self.ticket.estado, Ticket.Estado.RESUELTO)
        self.assertIsNotNone(self.ticket.fecha_cierre)
        self.assertTrue(
            TicketHistorial.objects.filter(
                ticket=self.ticket, estado_nuevo=Ticket.Estado.RESUELTO, usuario=self.tecnico_user
            ).exists()
        )
        self.assertEqual(self.tecnico.estado, Tecnico.Estado.DISPONIBLE)

    def test_resolver_sin_trabajo_realizado(self):
        self.iniciar()
        self.assertCodigo("falta_trabajo", OrdenTrabajo.Estado.RESUELTA, self.tecnico_user)

    def test_tecnico_sigue_ocupado_si_tiene_otra_orden_activa(self):
        otro_ticket = Ticket.objects.create(
            numero="DEMO-00002", sucursal=self.ticket.sucursal, creador=self.encargado,
            categoria=self.ticket.categoria, titulo="Otro", descripcion="x",
            estado=Ticket.Estado.EN_EJECUCION,
        )
        OrdenTrabajo.objects.create(ticket=otro_ticket, tecnico=self.tecnico)
        self.iniciar()
        cambiar_estado_orden(
            self.orden, OrdenTrabajo.Estado.RESUELTA, self.tecnico_user,
            datos={"trabajo_realizado": "Listo"},
        )
        self.recargar()
        self.assertEqual(self.tecnico.estado, Tecnico.Estado.OCUPADO)

    def test_transicion_invalida(self):
        self.assertCodigo(
            "transicion_invalida", OrdenTrabajo.Estado.RESUELTA, self.tecnico_user,
            datos={"trabajo_realizado": "x"},
        )

    def test_sin_cambio(self):
        self.assertCodigo("sin_cambio", OrdenTrabajo.Estado.ASIGNADA, self.encargado)

    def test_tecnico_no_puede_cerrar_ni_cancelar(self):
        self.assertCodigo("sin_permiso", OrdenTrabajo.Estado.CANCELADA, self.tecnico_user)

    def test_otro_tecnico_no_puede_avanzar_la_orden(self):
        otro = self.crear_usuario("tecnico2", Usuario.Rol.TECNICO)
        Tecnico.objects.create(usuario=otro)
        self.assertCodigo(
            "sin_permiso", OrdenTrabajo.Estado.EN_EJECUCION, otro, datos={"diagnostico": "x"}
        )

    def test_gerencia_no_puede_aplicar_ninguna_transicion(self):
        self.assertEqual(transiciones_permitidas(self.gerencia, self.orden), set())
        self.assertCodigo("sin_permiso", OrdenTrabajo.Estado.CANCELADA, self.gerencia)

    def test_encargado_cierra_con_calificacion(self):
        self.iniciar()
        cambiar_estado_orden(
            self.orden, OrdenTrabajo.Estado.RESUELTA, self.tecnico_user,
            datos={"trabajo_realizado": "Listo"},
        )
        cambiar_estado_orden(
            self.orden, OrdenTrabajo.Estado.CERRADA, self.encargado,
            datos={"puntuacion": 5, "comentario_calificacion": "Rápido"},
        )
        self.recargar()
        self.assertEqual(self.orden.estado, OrdenTrabajo.Estado.CERRADA)
        self.assertEqual(self.ticket.estado, Ticket.Estado.CERRADO)
        calificacion = Calificacion.objects.get(orden_trabajo=self.orden)
        self.assertEqual((calificacion.puntuacion, calificacion.tecnico), (5, self.tecnico))

    def test_cerrar_sin_calificacion(self):
        self.iniciar()
        cambiar_estado_orden(
            self.orden, OrdenTrabajo.Estado.RESUELTA, self.tecnico_user,
            datos={"trabajo_realizado": "Listo"},
        )
        self.assertCodigo("falta_calificacion", OrdenTrabajo.Estado.CERRADA, self.encargado)

    def test_cancelar_no_toca_los_datos_de_trabajo(self):
        self.iniciar()
        cambiar_estado_orden(
            self.orden, OrdenTrabajo.Estado.CANCELADA, self.encargado,
            datos={"diagnostico": "otro texto"},
        )
        self.recargar()
        self.assertEqual(self.orden.diagnostico, "Enchufe derretido")
        self.assertEqual(self.ticket.estado, Ticket.Estado.CANCELADO)


class GerenciaOrdenWebTests(EscenarioOrdenMixin, TestCase):
    """Corrección: Gerencia ve las órdenes en la web, pero no puede cambiarlas."""

    def test_gerencia_ve_la_orden_sin_formulario_de_transicion(self):
        self.client.login(username="gerencia1", password=CLAVE)
        resp = self.client.get(reverse("ordenes:detalle", args=[self.orden.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context["form_estado"].fields["estado"].choices), [])
        self.assertFalse(resp.context["puede_cerrar"])

    def test_gerencia_no_puede_cancelar_por_post(self):
        self.client.login(username="gerencia1", password=CLAVE)
        resp = self.client.post(
            reverse("ordenes:cambiar_estado", args=[self.orden.pk]),
            {"estado": OrdenTrabajo.Estado.CANCELADA},
        )
        self.assertEqual(resp.status_code, 403)
        self.recargar()
        self.assertEqual(self.orden.estado, OrdenTrabajo.Estado.ASIGNADA)

    def test_encargado_si_puede_cancelar_por_post(self):
        self.client.login(username="encargado1", password=CLAVE)
        resp = self.client.post(
            reverse("ordenes:cambiar_estado", args=[self.orden.pk]),
            {"estado": OrdenTrabajo.Estado.CANCELADA},
        )
        self.assertEqual(resp.status_code, 302)
        self.recargar()
        self.assertEqual(self.orden.estado, OrdenTrabajo.Estado.CANCELADA)


class RegistroEnTerrenoWebTests(EscenarioOrdenMixin, TestCase):
    """El encargado ve en la web lo que el técnico registró desde la app."""

    def test_detalle_muestra_llegada_y_tiempo_de_respuesta(self):
        from .services import registrar_llegada

        sucursal = self.ticket.sucursal
        sucursal.latitud, sucursal.longitud = "-33.437800", "-70.650400"
        sucursal.save()
        registrar_llegada(self.orden, self.tecnico_user, "-33.437800", "-70.650400")

        self.client.login(username="encargado1", password=CLAVE)
        resp = self.client.get(reverse("ordenes:detalle", args=[self.orden.pk]))
        self.assertContains(resp, "Registro en terreno")
        self.assertContains(resp, "Verificada")
        self.assertContains(resp, "Sin política SLA")
        self.assertContains(resp, "Sin firma.")
