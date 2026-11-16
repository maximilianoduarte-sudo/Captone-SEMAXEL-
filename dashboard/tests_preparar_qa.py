"""Pruebas del comando preparar_qa (perfil de QA para pruebas manuales)."""

import shutil
import tempfile
from io import StringIO
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from accounts.models import Usuario
from ofertas.services import ofertas_disponibles_para
from tecnicos.models import Tecnico
from tickets.models import EvidenciaOrden, OrdenTrabajo, Ticket

# Contenido de la "foto": el modelo no valida la imagen al guardar.
FOTO = b"foto de prueba"


def _correr(*args):
    salida = StringIO()
    call_command("preparar_qa", *args, stdout=salida)
    return salida.getvalue()


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

    def test_crea_usuarios_y_escenario(self):
        salida = _correr()

        tecnico = Tecnico.objects.get(usuario__username="qa_tecnico")
        self.assertEqual(Usuario.objects.get(user__username="qa_tecnico").rol, "TECNICO")
        self.assertEqual(Usuario.objects.get(user__username="qa_admin").rol, "ADMIN")
        self.assertEqual(
            set(tecnico.especialidades.values_list("nombre", flat=True)),
            {"Electricidad", "Gasfitería", "Infraestructura"},
        )
        self.assertEqual(Ticket.objects.filter(numero__startswith="QA-").count(), 6)
        self.assertIn("contraseña nueva", salida)

        # QA-0005 queda tomada: orden asignada y técnico ocupado.
        orden = OrdenTrabajo.objects.get(ticket__numero="QA-0005")
        self.assertEqual(orden.tecnico, tecnico)
        self.assertEqual(orden.estado, OrdenTrabajo.Estado.ASIGNADA)
        tecnico.refresh_from_db()
        self.assertEqual(tecnico.estado, Tecnico.Estado.OCUPADO)

    def test_la_app_solo_muestra_las_ofertas_que_corresponden(self):
        _correr()
        tecnico = Tecnico.objects.get(usuario__username="qa_tecnico")
        numeros = set(
            ofertas_disponibles_para(tecnico)
            .filter(ticket__numero__startswith="QA-")
            .values_list("ticket__numero", flat=True)
        )
        # 0004: sin la especialidad; 0005: ya tomada; 0006: vencida.
        self.assertEqual(numeros, {"QA-0001", "QA-0002", "QA-0003"})

    def test_reiniciar_borra_lo_anterior_y_conserva_la_clave(self):
        _correr("--archivo-clave", str(Path(self.media) / "qa.txt"))
        clave = (Path(self.media) / "qa.txt").read_text(encoding="utf-8").split("Contraseña: ")[1].strip()

        # El tester sube una foto a QA-0005 y luego reinicia el escenario.
        orden = OrdenTrabajo.objects.get(ticket__numero="QA-0005")
        evidencia = EvidenciaOrden.objects.create(
            orden=orden,
            imagen=SimpleUploadedFile("foto.jpg", FOTO, content_type="image/jpeg"),
            subida_por=User.objects.get(username="qa_tecnico"),
        )
        archivo_foto = Path(evidencia.imagen.path)
        self.assertTrue(archivo_foto.exists())
        tickets_demo = Ticket.objects.exclude(numero__startswith="QA-").count()

        salida = _correr()

        self.assertIn("sin cambios", salida)
        self.assertTrue(User.objects.get(username="qa_tecnico").check_password(clave))
        self.assertEqual(Ticket.objects.filter(numero__startswith="QA-").count(), 6)
        self.assertFalse(EvidenciaOrden.objects.filter(pk=evidencia.pk).exists())
        self.assertFalse(archivo_foto.exists())
        # Los datos de seed_demo no se tocan.
        self.assertEqual(Ticket.objects.exclude(numero__startswith="QA-").count(), tickets_demo)

    def test_archivo_clave_guarda_la_clave_y_no_la_muestra(self):
        ruta = Path(self.media) / "credenciales" / "qa.txt"
        salida = _correr("--archivo-clave", str(ruta))

        clave = ruta.read_text(encoding="utf-8").split("Contraseña: ")[1].strip()
        self.assertNotIn(clave, salida)
        self.assertTrue(User.objects.get(username="qa_tecnico").check_password(clave))
        self.assertTrue(User.objects.get(username="qa_admin").check_password(clave))

    def test_nueva_clave_cambia_la_contrasena(self):
        ruta = Path(self.media) / "qa.txt"
        _correr("--archivo-clave", str(ruta))
        antes = ruta.read_text(encoding="utf-8").split("Contraseña: ")[1].strip()
        _correr("--archivo-clave", str(ruta), "--nueva-clave")
        despues = ruta.read_text(encoding="utf-8").split("Contraseña: ")[1].strip()

        self.assertNotEqual(antes, despues)
        self.assertTrue(User.objects.get(username="qa_tecnico").check_password(despues))
