from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario

from .forms import TecnicoForm
from .models import Especialidad, Tecnico


class EspecialidadesTecnicoTests(TestCase):
    """Un técnico puede tener varias especialidades y el listado las muestra todas."""

    def setUp(self):
        self.electricidad = Especialidad.objects.create(nombre="Electricidad")
        self.gasfiteria = Especialidad.objects.create(nombre="Gasfitería")

        usuario_tecnico = User.objects.create_user(username="tecnico1", password="clave")
        Usuario.objects.create(
            user=usuario_tecnico, rol=Usuario.Rol.TECNICO, empresa=None
        )
        self.tecnico = Tecnico.objects.create(usuario=usuario_tecnico)
        self.tecnico.especialidades.set([self.electricidad, self.gasfiteria])

        self.superuser = User.objects.create_superuser(
            username="admin", password="clave"
        )

    def test_tecnico_admite_varias_especialidades(self):
        self.assertEqual(
            set(self.tecnico.especialidades.values_list("nombre", flat=True)),
            {"Electricidad", "Gasfitería"},
        )

    def test_formulario_guarda_multiples_especialidades(self):
        nuevo_usuario = User.objects.create_user(username="tecnico2", password="clave")
        Usuario.objects.create(
            user=nuevo_usuario, rol=Usuario.Rol.TECNICO, empresa=None
        )
        form = TecnicoForm(
            data={
                "usuario": nuevo_usuario.pk,
                "telefono": "+56 9 1234 5678",
                "estado": Tecnico.Estado.DISPONIBLE,
                "especialidades": [self.electricidad.pk, self.gasfiteria.pk],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        tecnico = form.save()
        self.assertEqual(tecnico.especialidades.count(), 2)

    def test_listado_muestra_todas_las_especialidades(self):
        self.client.force_login(self.superuser)
        respuesta = self.client.get(reverse("tecnicos:lista"))
        contenido = respuesta.content.decode()
        self.assertContains(respuesta, "Electricidad")
        self.assertContains(respuesta, "Gasfitería")
        self.assertNotIn("Especialidad.None", contenido)

    def test_detalle_muestra_todas_las_especialidades(self):
        self.client.force_login(self.superuser)
        respuesta = self.client.get(
            reverse("tecnicos:detalle", args=[self.tecnico.pk])
        )
        contenido = respuesta.content.decode()
        self.assertContains(respuesta, "Electricidad")
        self.assertContains(respuesta, "Gasfitería")
        self.assertNotIn("Especialidad.None", contenido)
