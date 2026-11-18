"""Pruebas del comando preparar_qa (entorno de QA con datos falsos)."""

import shutil
import tempfile
from io import StringIO
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.roles import tickets_visibles
from api.models import Dispositivo
from mantenimiento.models import PlanMantenimiento
from ofertas.services import ofertas_disponibles_para
from tecnicos.models import Tecnico
from tickets.models import (
    Calificacion,
    EvidenciaOrden,
    EvidenciaTicket,
    FirmaConformidad,
    OrdenTrabajo,
    Ticket,
)


def _correr(*args):
    salida = StringIO()
    call_command("preparar_qa", *args, stdout=salida)
    return salida.getvalue()


def _clave(ruta):
    return Path(ruta).read_text(encoding="utf-8").split("Contraseña: ")[1].strip()


class PrepararQASinDatosBaseTests(TestCase):
    def test_sin_seed_demo_avisa_que_falta(self):
        with self.assertRaisesMessage(CommandError, "seed_demo"):
            _correr()


class PrepararQATests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())

    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        ajustes = override_settings(MEDIA_ROOT=self.media)
        ajustes.enable()
        self.addCleanup(ajustes.disable)

    def _tickets_qa(self):
        return Ticket.objects.filter(sucursal__empresa__codigo="QA")

    def test_un_usuario_por_rol(self):
        _correr()
        roles = dict(User.objects.filter(username__startswith="qa_").values_list("username", "perfil__rol"))
        self.assertEqual(roles["qa_admin"], "ADMIN")
        self.assertEqual(roles["qa_gestor"], "GESTOR")
        self.assertEqual(roles["qa_encargado"], "ENCARGADO")
        self.assertEqual(roles["qa_gerencia"], "GERENCIA")
        self.assertEqual(roles["qa_tecnico"], "TECNICO")
        self.assertEqual(roles["qa_otra_admin"], "ADMIN")

    def test_tickets_y_ordenes_en_todos_los_estados(self):
        _correr()
        self.assertEqual(
            set(self._tickets_qa().values_list("estado", flat=True)),
            set(Ticket.Estado.values),
        )
        self.assertEqual(
            set(OrdenTrabajo.objects.filter(ticket__sucursal__empresa__codigo="QA")
                .values_list("estado", flat=True)),
            set(OrdenTrabajo.Estado.values),
        )
        self.assertTrue(self._tickets_qa().filter(tipo=Ticket.Tipo.PREVENTIVO).exists())

    def test_fotos_firmas_calificaciones_y_adjunto_reales(self):
        _correr()
        fotos = EvidenciaOrden.objects.filter(orden__ticket__sucursal__empresa__codigo="QA")
        self.assertGreater(fotos.count(), 0)
        self.assertTrue(Path(fotos.first().imagen.path).exists())
        self.assertGreater(FirmaConformidad.objects.filter(orden__ticket__numero__startswith="QA-").count(), 0)
        self.assertEqual(
            sorted(Calificacion.objects.filter(orden_trabajo__ticket__numero__startswith="QA-")
                   .values_list("puntuacion", flat=True)),
            [3, 4, 4, 5],
        )
        self.assertTrue(EvidenciaTicket.objects.filter(ticket__numero="QA-00014").exists())
        self.assertTrue(Dispositivo.objects.filter(usuario__username="qa_tecnico").exists())

    def test_la_app_muestra_a_cada_tecnico_lo_que_corresponde(self):
        _correr()
        def numeros(username):
            tecnico = Tecnico.objects.get(usuario__username=username)
            return set(
                ofertas_disponibles_para(tecnico)
                .filter(ticket__sucursal__empresa__codigo__in=["QA", "QAOTRA"])
                .values_list("ticket__numero", flat=True)
            )
        # 04: sin la especialidad; 05: ya tomada; 06: vencida.
        self.assertEqual(numeros("qa_tecnico"), {"QA-00001", "QA-00002", "QA-00003", "QA-00007", "QAOTRA-00002"})
        self.assertEqual(numeros("qa_tecnico2"), {"QA-00004"})

    def test_estados_de_los_tecnicos(self):
        _correr()
        estados = dict(Tecnico.objects.filter(usuario__username__startswith="qa_")
                       .values_list("usuario__username", "estado"))
        self.assertEqual(estados, {
            "qa_tecnico": "OCUPADO",
            "qa_tecnico2": "OCUPADO",
            "qa_tecnico_nodisp": "NO_DISPONIBLE",
            "qa_tecnico_inactivo": "INACTIVO",
        })

    def test_cada_empresa_y_cada_encargado_ve_solo_lo_suyo(self):
        _correr()
        admin = User.objects.get(username="qa_admin")
        self.assertFalse(tickets_visibles(admin).filter(numero__startswith="QAOTRA").exists())
        self.assertTrue(tickets_visibles(admin).filter(numero="QA-00003").exists())
        encargado = User.objects.get(username="qa_encargado")
        self.assertEqual(
            set(tickets_visibles(encargado).values_list("sucursal__codigo", flat=True)),
            {"QPR", "QNU"},
        )

    def test_sla_y_fechas_para_los_reportes(self):
        _correr()
        cerrados = self._tickets_qa().filter(estado=Ticket.Estado.CERRADO)
        fuera = [t.numero for t in cerrados if t.fecha_cierre > t.fecha_limite_sla]
        self.assertEqual(fuera, ["QA-00011"])
        # Los trabajos cerrados quedan repartidos en las últimas semanas.
        self.assertLess(cerrados.order_by("fecha_cierre").first().fecha_cierre,
                        timezone.now() - timezone.timedelta(days=20))
        abierto = Ticket.objects.get(numero="QA-00014")
        self.assertLess(abierto.fecha_limite_sla, timezone.now())  # SLA vencido

    def test_planes_de_mantenimiento(self):
        _correr()
        planes = PlanMantenimiento.objects.filter(sucursal__empresa__codigo="QA")
        self.assertEqual(planes.count(), 4)
        self.assertEqual(planes.filter(activo=False).count(), 1)
        # Uno queda vencido para probar el botón "Generar" de la web.
        self.assertTrue(planes.filter(activo=True, fecha_proxima__lte=timezone.now()).exists())

    def test_reiniciar_deja_todo_como_nuevo_y_conserva_la_clave(self):
        ruta = Path(self.media) / "qa.txt"
        _correr("--archivo-clave", str(ruta))
        clave = _clave(ruta)
        archivos = sorted(p.name for p in Path(self.media).rglob("*") if p.is_file())
        totales = (self._tickets_qa().count(), EvidenciaOrden.objects.count())
        tickets_demo = Ticket.objects.exclude(sucursal__empresa__codigo__in=["QA", "QAOTRA"]).count()

        salida = _correr()

        self.assertIn("sin cambios", salida)
        self.assertTrue(User.objects.get(username="qa_tecnico").check_password(clave))
        self.assertEqual((self._tickets_qa().count(), EvidenciaOrden.objects.count()), totales)
        # Se borraron los archivos anteriores: misma cantidad, no el doble.
        self.assertEqual(len([p for p in Path(self.media).rglob("*") if p.is_file()]), len(archivos))
        self.assertEqual(
            Ticket.objects.exclude(sucursal__empresa__codigo__in=["QA", "QAOTRA"]).count(), tickets_demo
        )

    def test_archivo_clave_guarda_la_clave_y_no_la_muestra(self):
        ruta = Path(self.media) / "credenciales" / "qa.txt"
        salida = _correr("--archivo-clave", str(ruta))

        clave = _clave(ruta)
        self.assertNotIn(clave, salida)
        for username in ("qa_tecnico", "qa_admin", "qa_gerencia", "qa_otra_admin"):
            self.assertTrue(User.objects.get(username=username).check_password(clave), username)

    def test_agregar_trabajos_suma_sin_borrar_nada(self):
        ruta = Path(self.media) / "qa.txt"
        _correr("--archivo-clave", str(ruta))
        clave = _clave(ruta)
        antes = set(self._tickets_qa().values_list("numero", flat=True))
        ordenes = OrdenTrabajo.objects.filter(tecnico__usuario__username="qa_tecnico")
        activas_antes = ordenes.filter(estado__in=["ASIGNADA", "EN_EJECUCION"]).count()

        salida = _correr("--agregar-trabajos")
        salida += _correr("--agregar-trabajos")  # se puede repetir

        nuevos = set(self._tickets_qa().values_list("numero", flat=True)) - antes
        self.assertEqual(len(nuevos), 16)
        self.assertIn("QA-00019", nuevos)  # sigue la numeración del sistema
        self.assertTrue(antes <= set(self._tickets_qa().values_list("numero", flat=True)))
        self.assertEqual(ordenes.filter(estado="ASIGNADA").count() + ordenes.filter(estado="EN_EJECUCION").count(),
                         activas_antes + 10)
        tecnico = Tecnico.objects.get(usuario__username="qa_tecnico")
        self.assertEqual(
            ofertas_disponibles_para(tecnico).filter(ticket__numero__in=nuevos).count(), 6
        )
        self.assertTrue(User.objects.get(username="qa_tecnico").check_password(clave))
        self.assertNotIn("Contraseña", salida)

    def test_agregar_trabajos_sin_entorno_avisa(self):
        with self.assertRaisesMessage(CommandError, "preparar_qa"):
            _correr("--agregar-trabajos")

    def test_nueva_clave_cambia_la_contrasena(self):
        ruta = Path(self.media) / "qa.txt"
        _correr("--archivo-clave", str(ruta))
        antes = _clave(ruta)
        _correr("--archivo-clave", str(ruta), "--nueva-clave")
        despues = _clave(ruta)

        self.assertNotEqual(antes, despues)
        self.assertTrue(User.objects.get(username="qa_encargado").check_password(despues))

