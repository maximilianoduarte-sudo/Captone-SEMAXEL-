from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from accounts.models import Usuario
from empresas.models import Empresa
from sucursales.models import Sucursal
from tecnicos.models import Especialidad, Tecnico
from tickets.models import Categoria, OrdenTrabajo, Ticket, TicketHistorial

from .models import OfertaTicket
from .services import OfertaNoTomable, tomar_oferta


class TomarOfertaServicioTests(TestCase):
    """ofertas.services.tomar_oferta: la regla única que usan la web y la API."""

    def setUp(self):
        self.electricidad = Especialidad.objects.create(nombre="Electricidad")
        self.categoria = Categoria.objects.create(
            nombre="Eléctrica", especialidad=self.electricidad
        )
        # Datos hipotéticos de prueba.
        empresa = Empresa.objects.create(nombre="Cadena Demo", rut="76.000.000-0", codigo="DEMO")
        sucursal = Sucursal.objects.create(
            empresa=empresa, nombre="Local Centro", codigo="CEN", direccion="Av. Ejemplo 123"
        )
        encargado = User.objects.create_user(username="encargado1", password="x")
        self.ticket = Ticket.objects.create(
            numero="DEMO-00001", sucursal=sucursal, creador=encargado,
            categoria=self.categoria, titulo="Enchufe quemado", descripcion="Sin energía",
            estado=Ticket.Estado.PUBLICADO,
        )
        self.oferta = OfertaTicket.objects.create(ticket=self.ticket)
        self.user = User.objects.create_user(
            username="tecnico1", password="x", first_name="Ana", last_name="Pérez"
        )
        Usuario.objects.create(user=self.user, rol=Usuario.Rol.TECNICO)
        self.tecnico = Tecnico.objects.create(usuario=self.user)
        self.tecnico.especialidades.add(self.electricidad)

    def assertNoCambio(self):
        self.oferta.refresh_from_db()
        self.tecnico.refresh_from_db()
        self.assertIsNone(self.oferta.tecnico)
        self.assertFalse(OrdenTrabajo.objects.exists())
        self.assertEqual(self.tecnico.estado, Tecnico.Estado.DISPONIBLE)

    def assertCodigo(self, codigo):
        with self.assertRaises(OfertaNoTomable) as ctx:
            tomar_oferta(self.oferta, self.tecnico, usuario=self.user)
        self.assertEqual(ctx.exception.codigo, codigo)

    def test_toma_exitosa_actualiza_oferta_orden_ticket_y_tecnico(self):
        orden = tomar_oferta(self.oferta, self.tecnico, usuario=self.user)

        self.oferta.refresh_from_db()
        self.ticket.refresh_from_db()
        self.tecnico.refresh_from_db()
        self.assertEqual(self.oferta.estado, OfertaTicket.Estado.TOMADA)
        self.assertEqual(self.oferta.tecnico, self.tecnico)
        self.assertIsNotNone(self.oferta.fecha_tomada)
        self.assertEqual(orden.estado, OrdenTrabajo.Estado.ASIGNADA)
        self.assertEqual(orden.tecnico, self.tecnico)
        self.assertEqual(self.ticket.estado, Ticket.Estado.EN_EJECUCION)
        self.assertEqual(self.tecnico.estado, Tecnico.Estado.OCUPADO)
        historial = TicketHistorial.objects.get(ticket=self.ticket)
        self.assertEqual(historial.usuario, self.user)
        self.assertEqual(historial.comentario, "Oferta tomada por el técnico Ana Pérez.")

    def test_no_se_puede_tomar_dos_veces(self):
        tomar_oferta(self.oferta, self.tecnico, usuario=self.user)
        self.assertCodigo("no_disponible")
        self.assertEqual(OrdenTrabajo.objects.count(), 1)

    def test_oferta_vencida_queda_expirada(self):
        self.oferta.fecha_vencimiento = timezone.now() - timedelta(minutes=1)
        self.oferta.save()
        self.assertCodigo("vencida")
        self.assertNoCambio()
        self.assertEqual(self.oferta.estado, OfertaTicket.Estado.EXPIRADA)

    def test_ticket_que_no_permite_ejecucion(self):
        self.ticket.estado = Ticket.Estado.CANCELADO
        self.ticket.save()
        self.assertCodigo("ticket_no_permite")
        self.assertNoCambio()

    def test_categoria_sin_especialidad(self):
        self.categoria.especialidad = None
        self.categoria.save()
        self.assertCodigo("sin_especialidad")
        self.assertNoCambio()

    def test_tecnico_sin_la_especialidad(self):
        self.tecnico.especialidades.clear()
        self.assertCodigo("especialidad_no_coincide")
        self.assertNoCambio()
