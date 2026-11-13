"""Pruebas del trabajo en terreno y del resto de la API completa.

Llegada con GPS, fotos de evidencia, firma de conformidad, disponibilidad,
inicio, dispositivos, notificaciones push y documentación OpenAPI.
"""
import io
import shutil
import tempfile
from datetime import time, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.authtoken.models import Token

from accounts.models import Usuario
from ofertas.models import OfertaTicket
from ofertas.services import tomar_oferta
from sla.models import SLAPolicy
from sucursales.models import HorarioSucursal
from tecnicos.models import Tecnico
from tickets.models import EvidenciaOrden, FirmaConformidad, OrdenTrabajo, Ticket, TicketHistorial
from tickets.services import cambiar_estado_orden, distancia_metros

from . import notificaciones
from .models import Dispositivo
from .tests import EscenarioOfertasMixin, crear_usuario

MEDIA_TEMPORAL = tempfile.mkdtemp(prefix="semaxel_media_pruebas_")


def imagen_png(nombre="foto.png", tamano=(20, 20)):
    """Imagen PNG real y pequeña, creada en memoria."""
    buffer = io.BytesIO()
    Image.new("RGB", tamano, (200, 30, 30)).save(buffer, format="PNG")
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type="image/png")


class DistanciaTests(TestCase):
    def test_un_milesimo_de_grado_de_latitud_son_unos_111_metros(self):
        self.assertAlmostEqual(distancia_metros(-33.0, -70.0, -33.001, -70.0), 111.2, delta=0.5)

    def test_mismo_punto(self):
        self.assertEqual(distancia_metros(-33.4, -70.6, -33.4, -70.6), 0)


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL, SEMAXEL_PUSH_BACKEND="memoria")
class TerrenoBase(EscenarioOfertasMixin, TestCase):
    """Escenario con una orden ASIGNADA del técnico en un local con coordenadas."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)

    def setUp(self):
        super().setUp()
        notificaciones.BANDEJA.clear()
        self.sucursal.latitud, self.sucursal.longitud = "-33.437800", "-70.650400"
        self.sucursal.save()
        self.orden = tomar_oferta(self.oferta_electrica, self.tecnico, usuario=self.user)

    def url(self, nombre, *args):
        return reverse(f"api:{nombre}", args=args or [self.orden.pk])

    def iniciar(self):
        cambiar_estado_orden(
            self.orden, OrdenTrabajo.Estado.EN_EJECUCION, self.user, datos={"diagnostico": "x"}
        )

    def como(self, user):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {Token.objects.get_or_create(user=user)[0].key}"
        )


class LlegadaApiTests(TerrenoBase):
    def llegar(self, lat, lon, **extra):
        return self.client.post(
            self.url("llegada"), {"latitud": lat, "longitud": lon, **extra}, format="json"
        )

    def test_llegada_dentro_del_radio_queda_verificada(self):
        resp = self.llegar("-33.437900", "-70.650400", precision_m=8)  # ~11 m
        self.assertEqual(resp.status_code, 201)
        llegada = resp.data["llegada"]
        self.assertTrue(llegada["verificada"])
        self.assertLess(llegada["distancia_m"], 20)
        self.assertEqual(llegada["precision_m"], 8)
        self.assertNotIn("registrar_llegada", resp.data["acciones"])

    def test_llegada_fuera_del_radio(self):
        resp = self.llegar("-33.447800", "-70.650400")  # ~1,1 km
        self.assertEqual(resp.status_code, 201)
        self.assertFalse(resp.data["llegada"]["verificada"])
        self.assertGreater(resp.data["llegada"]["distancia_m"], 1000)

    def test_sucursal_sin_coordenadas_no_es_verificable(self):
        self.sucursal.latitud = self.sucursal.longitud = None
        self.sucursal.save()
        resp = self.llegar("-33.4", "-70.6")
        self.assertEqual(resp.status_code, 201)
        self.assertIsNone(resp.data["llegada"]["verificada"])
        self.assertIsNone(resp.data["llegada"]["distancia_m"])

    def test_completa_fecha_de_respuesta_historial_y_sla(self):
        SLAPolicy.objects.create(
            nombre="Media", prioridad="MEDIA", tiempo_maximo_respuesta=60,
            tiempo_maximo_resolucion=480,
        )
        resp = self.llegar("-33.437800", "-70.650400")
        self.assertEqual(resp.data["tiempo_respuesta_minutos"], 0)
        self.assertEqual(resp.data["sla_respuesta_minutos"], 60)
        self.assertTrue(resp.data["sla_respuesta_cumplido"])
        self.oferta_electrica.refresh_from_db()
        self.assertIsNotNone(self.oferta_electrica.fecha_respuesta)
        self.assertTrue(
            TicketHistorial.objects.filter(comentario__startswith="Llegada del técnico").exists()
        )

    def test_respuesta_tardia_no_cumple_el_sla(self):
        SLAPolicy.objects.create(
            nombre="Media", prioridad="MEDIA", tiempo_maximo_respuesta=60,
            tiempo_maximo_resolucion=480,
        )
        Ticket.objects.filter(pk=self.orden.ticket_id).update(
            fecha_creacion=self.orden.ticket.fecha_creacion - timedelta(hours=2)
        )
        resp = self.llegar("-33.437800", "-70.650400")
        self.assertGreaterEqual(resp.data["tiempo_respuesta_minutos"], 120)
        self.assertFalse(resp.data["sla_respuesta_cumplido"])

    def test_solo_una_vez(self):
        self.llegar("-33.437800", "-70.650400")
        resp = self.llegar("-33.437800", "-70.650400")
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.data["codigo"], "llegada_ya_registrada")

    def test_orden_resuelta_no_admite_llegada(self):
        self.iniciar()
        cambiar_estado_orden(
            self.orden, OrdenTrabajo.Estado.RESUELTA, self.user, datos={"trabajo_realizado": "x"}
        )
        resp = self.llegar("-33.437800", "-70.650400")
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.data["codigo"], "orden_no_activa")

    def test_coordenadas_invalidas_responden_400(self):
        self.assertEqual(self.llegar("-91", "-70.6").status_code, 400)
        self.assertEqual(self.llegar("-33.4", "181").status_code, 400)

    def test_orden_ajena_responde_404(self):
        self.como(crear_usuario("tecnico2", Usuario.Rol.TECNICO, tecnico=True))
        self.assertEqual(self.llegar("-33.4", "-70.6").status_code, 404)


class EvidenciasApiTests(TerrenoBase):
    def subir(self, archivo=None, **extra):
        return self.client.post(
            self.url("evidencias"),
            {"imagen": archivo or imagen_png(), **extra},
            format="multipart",
        )

    def test_subir_listar_y_ver_en_la_orden(self):
        resp = self.subir(descripcion="Enchufe antes del cambio")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.data["url"].startswith("http://testserver/media/evidencias_ordenes/"))
        self.assertEqual(len(self.client.get(self.url("evidencias")).data), 1)
        detalle = self.client.get(self.url("orden_detalle")).data
        self.assertEqual(detalle["evidencias"][0]["descripcion"], "Enchufe antes del cambio")

    def test_archivo_que_no_es_imagen_responde_400(self):
        falso = SimpleUploadedFile("foto.png", b"esto no es una imagen", content_type="image/png")
        self.assertEqual(self.subir(falso).status_code, 400)
        self.assertFalse(EvidenciaOrden.objects.exists())

    @override_settings(SEMAXEL_MAX_EVIDENCIAS_POR_ORDEN=1)
    def test_limite_de_fotos(self):
        self.subir()
        resp = self.subir()
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.data["codigo"], "limite_evidencias")

    @override_settings(SEMAXEL_MAX_TAMANO_IMAGEN_MB=0)
    def test_imagen_demasiado_grande_responde_400(self):
        self.assertEqual(self.subir().status_code, 400)

    def test_eliminar_foto(self):
        evidencia_id = self.subir().data["id"]
        resp = self.client.delete(self.url("evidencia_detalle", self.orden.pk, evidencia_id))
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(EvidenciaOrden.objects.exists())

    def test_orden_cancelada_no_admite_fotos_ni_borrarlas(self):
        evidencia_id = self.subir().data["id"]
        cambiar_estado_orden(self.orden, OrdenTrabajo.Estado.CANCELADA, self.encargado)
        self.assertEqual(self.subir().data["codigo"], "orden_no_activa")
        resp = self.client.delete(self.url("evidencia_detalle", self.orden.pk, evidencia_id))
        self.assertEqual(resp.status_code, 409)


class FirmaApiTests(TerrenoBase):
    def firmar(self, nombre="Juan Pérez"):
        return self.client.post(
            self.url("firma"),
            {"imagen": imagen_png("firma.png"), "nombre_firmante": nombre},
            format="multipart",
        )

    def test_no_se_firma_una_orden_solo_asignada(self):
        resp = self.firmar()
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.data["codigo"], "orden_no_activa")

    def test_firma_en_ejecucion_y_solo_una_vez(self):
        self.iniciar()
        resp = self.firmar()
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["firma"]["nombre_firmante"], "Juan Pérez")
        self.assertNotIn("firmar", resp.data["acciones"])
        self.assertTrue(FirmaConformidad.objects.filter(orden=self.orden).exists())
        self.assertEqual(self.firmar().data["codigo"], "firma_ya_registrada")

    def test_falta_el_nombre_responde_400(self):
        self.iniciar()
        resp = self.client.post(self.url("firma"), {"imagen": imagen_png()}, format="multipart")
        self.assertEqual(resp.status_code, 400)


class PerfilInicioYDispositivosApiTests(TerrenoBase):
    def test_cambiar_disponibilidad(self):
        # Tras tomar la oferta el técnico está OCUPADO: no puede cambiarla.
        resp = self.client.patch(reverse("api:perfil"), {"estado": "NO_DISPONIBLE"}, format="json")
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.data["codigo"], "tecnico_ocupado")

        Tecnico.objects.filter(pk=self.tecnico.pk).update(estado=Tecnico.Estado.DISPONIBLE)
        resp = self.client.patch(reverse("api:perfil"), {"estado": "NO_DISPONIBLE"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["estado"], "NO_DISPONIBLE")

    def test_estado_no_elegible_responde_400(self):
        resp = self.client.patch(reverse("api:perfil"), {"estado": "INACTIVO"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_inicio_resume_ofertas_y_ordenes_activas(self):
        HorarioSucursal.objects.create(
            sucursal=self.sucursal, dia_semana=0, hora_apertura=time(9), hora_cierre=time(18)
        )
        resp = self.client.get(reverse("api:inicio"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["ofertas_disponibles"], 0)  # la única la tomó
        self.assertEqual(resp.data["ordenes_activas"], 1)
        horario = resp.data["ordenes"][0]["sucursal"]["horario"]
        self.assertEqual(horario, [{"dia_semana": 0, "dia": "Lunes", "apertura": "09:00", "cierre": "18:00"}])

    def test_registrar_dispositivo_y_quitarlo_al_cerrar_sesion(self):
        resp = self.client.post(reverse("api:dispositivos"), {"token": "fcm-abc"}, format="json")
        self.assertEqual(resp.status_code, 201)
        resp = self.client.post(reverse("api:dispositivos"), {"token": "fcm-abc"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Dispositivo.objects.count(), 1)

        resp = self.client.post(
            reverse("api:logout"), {"token_dispositivo": "fcm-abc"}, format="json"
        )
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Dispositivo.objects.exists())

    def test_quitar_dispositivo_ajeno_responde_404(self):
        otro = crear_usuario("tecnico2", Usuario.Rol.TECNICO, tecnico=True)
        ajeno = Dispositivo.objects.create(usuario=otro, token="fcm-otro")
        resp = self.client.delete(reverse("api:dispositivo_detalle", args=[ajeno.pk]))
        self.assertEqual(resp.status_code, 404)


@override_settings(SEMAXEL_PUSH_BACKEND="memoria")
class NotificacionesTests(EscenarioOfertasMixin, TestCase):
    def setUp(self):
        super().setUp()
        notificaciones.BANDEJA.clear()
        Dispositivo.objects.create(usuario=self.user, token="fcm-electricista")
        gasfiter = crear_usuario("gasfiter", Usuario.Rol.TECNICO, tecnico=True)
        gasfiter.tecnico.especialidades.set([self.cat_gas.especialidad])
        Dispositivo.objects.create(usuario=gasfiter, token="fcm-gasfiter")

    def test_oferta_nueva_avisa_solo_a_tecnicos_de_la_especialidad(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.crear_oferta("Tablero eléctrico", self.cat_electrica)
        self.assertEqual([n["token"] for n in notificaciones.BANDEJA], ["fcm-electricista"])
        self.assertEqual(notificaciones.BANDEJA[0]["datos"]["tipo"], "oferta_nueva")

    def test_republicar_avisa_y_editar_una_disponible_no(self):
        oferta = self.oferta_electrica
        with self.captureOnCommitCallbacks(execute=True):
            oferta.observaciones = "Traer escalera"
            oferta.save()
        self.assertEqual(notificaciones.BANDEJA, [])
        with self.captureOnCommitCallbacks(execute=True):
            oferta.estado = OfertaTicket.Estado.EXPIRADA
            oferta.save()
            oferta.estado = OfertaTicket.Estado.DISPONIBLE
            oferta.save()
        self.assertEqual(len(notificaciones.BANDEJA), 1)

    def test_cierre_de_orden_avisa_al_tecnico(self):
        orden = tomar_oferta(self.oferta_electrica, self.tecnico, usuario=self.user)
        with self.captureOnCommitCallbacks(execute=True):
            cambiar_estado_orden(orden, OrdenTrabajo.Estado.CANCELADA, self.encargado)
        self.assertEqual(notificaciones.BANDEJA[-1]["datos"]["tipo"], "orden_cancelada")
        self.assertEqual(notificaciones.BANDEJA[-1]["token"], "fcm-electricista")


class DocumentacionApiTests(TestCase):
    def test_esquema_y_swagger_son_publicos(self):
        esquema = self.client.get(reverse("api:schema"))
        self.assertEqual(esquema.status_code, 200)
        self.assertIn(b"/api/v1/ordenes/{orden_id}/llegada/", esquema.content)
        self.assertEqual(self.client.get(reverse("api:docs")).status_code, 200)
