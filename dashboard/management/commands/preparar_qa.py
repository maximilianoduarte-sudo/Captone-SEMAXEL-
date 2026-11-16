"""
Prepara un entorno de QA completo para probar a mano la app y la web.

Crea (o deja como nuevos) datos **falsos** que cubren todo el sistema:

- Dos empresas de prueba: ``QA`` (la que se prueba) y ``QAOTRA`` (para
  comprobar que una empresa no ve los datos de otra).
- Cinco sucursales de QA: tres con GPS y horario, una sin GPS ni horario y
  una inactiva.
- Un usuario por rol (``qa_admin``, ``qa_gestor``, ``qa_encargado``,
  ``qa_gerencia``), cuatro técnicos en distintos estados y el administrador
  de la otra empresa (``qa_otra_admin``).
- Tickets en todos los estados (abierto, en revisión, publicado, en
  ejecución, resuelto, cerrado y cancelado), órdenes en todos sus estados,
  fotos, firmas, calificaciones, un adjunto, SLA cumplidos y vencidos,
  planes de mantenimiento y un ticket preventivo.

Los datos se generan con las mismas reglas que usan la web y la app
(``tomar_oferta``, ``registrar_llegada``, ``agregar_evidencia``,
``registrar_firma`` y ``cambiar_estado_orden``), así quedan coherentes: el
historial, los estados del ticket y la disponibilidad de los técnicos.
Después se reparten las fechas de los trabajos terminados en las últimas
semanas para que los reportes tengan historia.

Cada ejecución borra todos los tickets de las empresas de QA (con sus fotos,
firmas y adjuntos) y los planes de mantenimiento de QA, y los vuelve a
crear. No toca los datos de ``seed_demo``. No envía notificaciones push.

La contraseña de todos los usuarios de QA es la misma, aleatoria, y nunca
queda en el repositorio: se genera al crear los usuarios (o con
``--nueva-clave``) y se muestra una sola vez, o se guarda en el archivo de
``--archivo-clave``.

Requiere haber ejecutado ``seed_demo`` antes (especialidades, categorías y
políticas SLA).

Uso:
    python manage.py preparar_qa
    python manage.py preparar_qa --archivo-clave D:\\herramientas-servidor\\credenciales\\qa.txt
    python manage.py preparar_qa --nueva-clave
"""

import io
import math
import secrets
from datetime import time
from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.test.utils import override_settings
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from accounts.models import Usuario
from api.models import Dispositivo
from empresas.models import Empresa
from mantenimiento.models import PlanMantenimiento
from mantenimiento.services import generar_tickets_preventivos
from ofertas.models import OfertaTicket
from ofertas.services import tomar_oferta
from sla.models import SLAPolicy
from sucursales.models import HorarioSucursal, Sucursal
from tecnicos.models import Especialidad, Tecnico
from tickets.models import (
    Calificacion,
    Categoria,
    EvidenciaOrden,
    EvidenciaTicket,
    FirmaConformidad,
    OrdenTrabajo,
    Ticket,
    TicketHistorial,
)
from tickets.services import (
    agregar_evidencia,
    cambiar_estado_orden,
    registrar_firma,
    registrar_llegada,
)

# --------------------------------------------------------------------------
# Datos del escenario (todos hipotéticos)
# --------------------------------------------------------------------------

EMPRESAS = {
    "QA": {
        "nombre": "QA Retail SpA (datos de prueba)",
        "rut": "11.111.111-1",
        "ciudad": "Santiago",
        "region": "Metropolitana",
        "telefono": "+56 2 2000 0000",
        "correo": "contacto@qa-retail.test",
    },
    "QAOTRA": {
        "nombre": "QA Otra Empresa (datos de prueba)",
        "rut": "22.222.222-2",
        "ciudad": "Valparaíso",
        "region": "Valparaíso",
        "telefono": "+56 32 200 0000",
        "correo": "contacto@qa-otra.test",
    },
}

# Horarios: día (0 = lunes) -> (apertura, cierre). Sin entrada = cerrado.
HORARIO_COMERCIO = {d: (time(9), time(20)) for d in range(5)} | {5: (time(9), time(14))}
HORARIO_EXTENDIDO = {d: (time(10), time(19)) for d in range(6)}
HORARIO_TODOS_LOS_DIAS = {d: (time(8), time(22)) for d in range(7)}

# codigo: (empresa, nombre, dirección, comuna, latitud, longitud, estado, horario)
SUCURSALES = {
    "QPR": ("QA", "QA Providencia", "Av. Providencia 1200", "Providencia",
            "-33.429500", "-70.617700", "ACTIVA", HORARIO_COMERCIO),
    "QNU": ("QA", "QA Ñuñoa", "Av. Irarrázaval 3450", "Ñuñoa",
            "-33.455000", "-70.595900", "ACTIVA", HORARIO_EXTENDIDO),
    "QSC": ("QA", "QA Santiago Centro", "Huérfanos 789", "Santiago",
            "-33.439400", "-70.650800", "ACTIVA", HORARIO_TODOS_LOS_DIAS),
    "QMA": ("QA", "QA Maipú (sin GPS)", "Av. Pajaritos 2100", "Maipú",
            None, None, "ACTIVA", {}),
    "QLC": ("QA", "QA Las Condes (inactiva)", "Av. Apoquindo 4500", "Las Condes",
            "-33.413600", "-70.583300", "INACTIVA", HORARIO_COMERCIO),
    "QOT": ("QAOTRA", "QA Otra Sucursal", "Av. Brasil 1500", "Valparaíso",
            "-33.047200", "-71.612700", "ACTIVA", HORARIO_COMERCIO),
}
SUCURSALES_DEL_ENCARGADO = ("QPR", "QNU")

# username: (nombre, apellido, rol, empresa)
USUARIOS = {
    "qa_admin": ("QA", "Administración", "ADMIN", "QA"),
    "qa_gestor": ("QA", "Gestión", "GESTOR", "QA"),
    "qa_encargado": ("QA", "Encargado", "ENCARGADO", "QA"),
    "qa_gerencia": ("QA", "Gerencia", "GERENCIA", "QA"),
    "qa_tecnico": ("QA", "Técnico", "TECNICO", None),
    "qa_tecnico2": ("QA", "Técnico Dos", "TECNICO", None),
    "qa_tecnico_nodisp": ("QA", "Técnico No Disponible", "TECNICO", None),
    "qa_tecnico_inactivo": ("QA", "Técnico Inactivo", "TECNICO", None),
    "qa_otra_admin": ("QA Otra", "Administración", "ADMIN", "QAOTRA"),
}

# username: (especialidades, estado fijo o None si lo decide el escenario)
TECNICOS = {
    "qa_tecnico": (("Electricidad", "Gasfitería", "Infraestructura"), None),
    "qa_tecnico2": (("Climatización", "Carpintería"), None),
    "qa_tecnico_nodisp": (("Electricidad",), "NO_DISPONIBLE"),
    "qa_tecnico_inactivo": (("Gasfitería",), "INACTIVO"),
}

FIRMANTES = {"QPR": "Paula Rojas", "QNU": "Diego Soto", "QSC": "Marta Vidal", "QMA": "Jorge Lagos"}

# Cada ticket: número, título, sucursal, categoría, prioridad, flujo y qué se
# prueba. El flujo indica hasta dónde se lleva con las reglas del sistema:
#   abierto, revision, oferta, asignada, ejecucion, resuelta, cerrada, cancelada
# Claves opcionales: horas (vigencia de la oferta), tecnico, dias (antigüedad),
# sla_ok (cumple o no el SLA al cerrar), puntuacion, adjunto, sla_vencido,
# llegada ("dentro" o "fuera").
TICKETS = [
    dict(n="QA-00001", titulo="[QA] Enchufe quemado en caja 2", suc="QPR", cat="Fallo eléctrico",
         prio="ALTA", flujo="oferta", horas=72,
         prueba="App: flujo completo (tomar, llegar DENTRO del radio, iniciar, fotos, firma y resolver)."),
    dict(n="QA-00002", titulo="[QA] Fuga bajo lavamanos", suc="QNU", cat="Fuga de agua",
         prio="MEDIA", flujo="oferta", horas=48,
         prueba="App: llegada FUERA del radio (debe quedar no verificada, con la distancia)."),
    dict(n="QA-00003", titulo="[QA] Grieta en muro de bodega", suc="QSC", cat="Infraestructura / Obra",
         prio="CRITICA", flujo="oferta", horas=2,
         prueba="App: oferta urgente, vence en 2 horas."),
    dict(n="QA-00004", titulo="[QA] Aire acondicionado con ruido", suc="QPR", cat="Aire acondicionado",
         prio="ALTA", flujo="oferta", horas=48,
         prueba="App: qa_tecnico NO la ve (sin Climatización); qa_tecnico2 sí."),
    dict(n="QA-00005", titulo="[QA] Llave de paso goteando", suc="QSC", cat="Plomería",
         prio="MEDIA", flujo="asignada", tecnico="qa_tecnico",
         prueba="App: orden asignada; probar llegada, iniciar, fotos y firma."),
    dict(n="QA-00006", titulo="[QA] Luminaria de pasillo apagada", suc="QNU", cat="Fallo eléctrico",
         prio="BAJA", flujo="oferta", horas=-1,
         prueba="App: NO debe aparecer (oferta vencida hace 1 hora); en la web vuelve a revisión."),
    dict(n="QA-00007", titulo="[QA] Corte de luz en bodega", suc="QMA", cat="Fallo eléctrico",
         prio="MEDIA", flujo="oferta", horas=48,
         prueba="App: sucursal sin GPS ni horario (llegada no verificable, 'Horario no informado')."),
    dict(n="QA-00008", titulo="[QA] Filtración en baño de clientes", suc="QPR", cat="Fuga de agua",
         prio="ALTA", flujo="ejecucion", tecnico="qa_tecnico", llegada="dentro",
         prueba="App: en ejecución con 2 fotos y sin firma; probar firma y resolver."),
    dict(n="QA-00009", titulo="[QA] Reparación de cielo falso", suc="QNU", cat="Infraestructura / Obra",
         prio="MEDIA", flujo="resuelta", tecnico="qa_tecnico", llegada="dentro", dias=1,
         prueba="Web (qa_encargado): cerrar con calificación, o reabrir."),
    dict(n="QA-00010", titulo="[QA] Cambio de interruptor", suc="QPR", cat="Fallo eléctrico",
         prio="ALTA", flujo="cerrada", tecnico="qa_tecnico", llegada="dentro", dias=20,
         sla_ok=True, puntuacion=5,
         prueba="Reportes: cerrada dentro del SLA, calificación 5."),
    dict(n="QA-00011", titulo="[QA] Destape de cañería", suc="QSC", cat="Plomería",
         prio="MEDIA", flujo="cerrada", tecnico="qa_tecnico", llegada="fuera", dias=12,
         sla_ok=False, puntuacion=3,
         prueba="Reportes: cerrada FUERA del SLA, calificación 3, llegada fuera del radio."),
    dict(n="QA-00012", titulo="[QA] Revisión de medidor de agua", suc="QNU", cat="Fuga de agua",
         prio="BAJA", flujo="cancelada", tecnico="qa_tecnico", dias=5,
         prueba="Web: orden y ticket cancelados (estado terminal)."),
    dict(n="QA-00013", titulo="[QA] Equipo de aire sin enfriar", suc="QSC", cat="Aire acondicionado",
         prio="ALTA", flujo="ejecucion", tecnico="qa_tecnico2", llegada="dentro",
         prueba="App: orden de OTRO técnico; qa_tecnico no la ve ni puede tocarla."),
    dict(n="QA-00014", titulo="[QA] Tablero eléctrico con olor a quemado", suc="QPR", cat="Fallo eléctrico",
         prio="CRITICA", flujo="abierto", dias=2, adjunto=True, sla_vencido=True,
         prueba="Web: ticket abierto con foto adjunta y SLA vencido; pasar a revisión y publicar."),
    dict(n="QA-00015", titulo="[QA] Goteo en lavaplatos", suc="QNU", cat="Plomería",
         prio="BAJA", flujo="revision",
         prueba="Web (qa_encargado): ticket en revisión; publicar la oferta."),
    dict(n="QA-00016", titulo="[QA] Mantención de split en oficina", suc="QSC", cat="Aire acondicionado",
         prio="MEDIA", flujo="cerrada", tecnico="qa_tecnico2", llegada="dentro", dias=25,
         sla_ok=True, puntuacion=4,
         prueba="Reportes: trabajo cerrado de qa_tecnico2 (ranking de técnicos)."),
    dict(n="QA-00017", titulo="[QA] Cambio de flexible de WC", suc="QNU", cat="Plomería",
         prio="MEDIA", flujo="cerrada", tecnico="qa_tecnico", llegada="dentro", dias=8,
         sla_ok=True, puntuacion=4,
         prueba="Reportes: cerrada dentro del SLA, calificación 4."),
    dict(n="QAOTRA-00001", titulo="[QA otra empresa] Puerta de acceso trabada", suc="QOT",
         cat="Infraestructura / Obra", prio="MEDIA", flujo="abierto",
         prueba="Web: qa_admin NO debe ver este ticket (es de otra empresa)."),
    dict(n="QAOTRA-00002", titulo="[QA otra empresa] Enchufe sin corriente", suc="QOT",
         cat="Fallo eléctrico", prio="BAJA", flujo="oferta", horas=72,
         prueba="App: los técnicos ven ofertas de cualquier empresa; muestra 'QA Otra Empresa'."),
]

# nombre, sucursal, categoría, frecuencia, días hasta la próxima ejecución, activo
PLANES = [
    ("[QA] Revisión mensual de tablero eléctrico", "QPR", "Fallo eléctrico", "MENSUAL", -1, True),
    ("[QA] Mantención trimestral de aire acondicionado", "QSC", "Aire acondicionado", "TRIMESTRAL", 20, True),
    ("[QA] Limpieza semanal de desagües (pausado)", "QNU", "Plomería", "SEMANAL", 3, False),
    ("[QA] Inspección semestral de muros", "QSC", "Infraestructura / Obra", "SEMESTRAL", -2, True),
]
# Este plan se genera al preparar (queda un ticket PREVENTIVO); el de tablero
# eléctrico queda vencido para que quien prueba use el botón "Generar".
PLAN_GENERADO_AL_PREPARAR = "[QA] Inspección semestral de muros"

COLORES_FOTOS = ["#1f4e79", "#2e7d32", "#8e24aa", "#c62828", "#ef6c00"]


class Command(BaseCommand):
    help = "Crea o reinicia el entorno de QA: usuarios de todos los roles y datos falsos para probar todo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--archivo-clave",
            help="Guarda la contraseña en este archivo en vez de mostrarla en la consola.",
        )
        parser.add_argument(
            "--nueva-clave",
            action="store_true",
            help="Genera una contraseña nueva aunque los usuarios ya existan.",
        )

    def handle(self, *args, **opciones):
        # Las reglas avisan por push al publicar ofertas y cerrar órdenes; al
        # preparar datos de prueba no se debe avisar a nadie.
        with override_settings(SEMAXEL_PUSH_BACKEND="memoria"):
            with transaction.atomic():
                self.base = self._datos_base()
                self.empresas = self._empresas()
                self.sucursales = self._sucursales()
                clave, self.usuarios = self._usuarios(opciones["nueva_clave"])
                self.tecnicos = self._tecnicos()
                self._asignar_encargado()
                borrados = self._borrar_datos_anteriores()
                for datos in TICKETS:
                    self._crear_ticket(datos)
                generados = self._planes()
                self._estados_fijos_de_tecnicos()
                self._dispositivo()
        from api import notificaciones

        notificaciones.BANDEJA.clear()
        self._resumen(borrados, generados)
        self._informar_clave(clave, opciones["archivo_clave"])
        self.stdout.write(self.style.SUCCESS("Entorno de QA listo."))

    # ------------------------------------------------------------ datos base

    def _datos_base(self):
        """Especialidades, categorías y SLA que crea seed_demo."""
        categorias = {c.nombre: c for c in Categoria.objects.select_related("especialidad")}
        especialidades = {e.nombre: e for e in Especialidad.objects.all()}
        faltan = {d["cat"] for d in TICKETS} | {p[2] for p in PLANES}
        faltan -= set(categorias)
        faltan |= {e for esp, _ in TECNICOS.values() for e in esp} - set(especialidades)
        if faltan or not SLAPolicy.objects.filter(empresa__isnull=True).exists():
            raise CommandError(
                "Faltan los datos base"
                + (f" ({', '.join(sorted(faltan))})" if faltan else "")
                + ". Ejecuta primero: python manage.py seed_demo"
            )
        return {"categorias": categorias, "especialidades": especialidades}

    def _empresas(self):
        empresas = {}
        for codigo, datos in EMPRESAS.items():
            empresa, _ = Empresa.objects.update_or_create(
                codigo=codigo, defaults={**datos, "estado": "ACTIVA"}
            )
            empresas[codigo] = empresa
        return empresas

    def _sucursales(self):
        sucursales = {}
        for codigo, (emp, nombre, direccion, comuna, lat, lon, estado, horario) in SUCURSALES.items():
            empresa = self.empresas[emp]
            sucursal, _ = Sucursal.objects.update_or_create(
                empresa=empresa,
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "direccion": direccion,
                    "comuna": comuna,
                    "ciudad": empresa.ciudad,
                    "region": empresa.region,
                    "telefono": empresa.telefono,
                    "correo": f"{codigo.lower()}@qa.test",
                    "estado": estado,
                    "latitud": Decimal(lat) if lat else None,
                    "longitud": Decimal(lon) if lon else None,
                },
            )
            sucursal.horarios.all().delete()
            for dia, (apertura, cierre) in horario.items():
                HorarioSucursal.objects.create(
                    sucursal=sucursal, dia_semana=dia, hora_apertura=apertura, hora_cierre=cierre
                )
            sucursales[codigo] = sucursal
        return sucursales

    def _usuarios(self, nueva_clave):
        existen = User.objects.filter(username__in=USUARIOS).count() == len(USUARIOS)
        clave = secrets.token_urlsafe(12) if (nueva_clave or not existen) else None
        usuarios = {}
        for username, (nombre, apellido, rol, emp) in USUARIOS.items():
            user, creado = User.objects.get_or_create(
                username=username,
                defaults={"first_name": nombre, "last_name": apellido,
                          "email": f"{username.replace('_', '.')}@qa.test"},
            )
            if creado and not clave:
                # Usuario nuevo en una ejecución sin clave nueva: usa la del
                # resto para que todos compartan la misma.
                clave = secrets.token_urlsafe(12)
            if clave:
                user.set_password(clave)
            user.first_name, user.last_name, user.is_active = nombre, apellido, True
            user.save()
            empresa = self.empresas[emp] if emp else None
            Usuario.objects.update_or_create(user=user, defaults={"rol": rol, "empresa": empresa})
            usuarios[username] = user
        if clave:
            # Si un usuario era nuevo, la clave nueva debe valer para todos.
            for user in usuarios.values():
                if not user.check_password(clave):
                    user.set_password(clave)
                    user.save(update_fields=["password"])
        return clave, usuarios

    def _tecnicos(self):
        tecnicos = {}
        for username, (especialidades, _estado) in TECNICOS.items():
            tecnico, _ = Tecnico.objects.get_or_create(
                usuario=self.usuarios[username],
                defaults={"telefono": "+56 9 0000 0000", "documento": f"DOC-{username.upper()}"},
            )
            tecnico.especialidades.set([self.base["especialidades"][e] for e in especialidades])
            tecnico.descripcion = "Técnico de prueba (datos falsos)."
            tecnico.estado = Tecnico.Estado.DISPONIBLE
            tecnico.save()
            tecnicos[username] = tecnico
        return tecnicos

    def _asignar_encargado(self):
        encargado = self.usuarios["qa_encargado"]
        for codigo, sucursal in self.sucursales.items():
            if codigo in SUCURSALES_DEL_ENCARGADO:
                sucursal.encargados.set([encargado])
            else:
                sucursal.encargados.clear()

    # ------------------------------------------------------- limpieza previa

    def _borrar_datos_anteriores(self):
        """Borra los tickets de QA (y sus archivos) y los planes de QA."""
        tickets = Ticket.objects.filter(
            Q(sucursal__empresa__codigo__in=EMPRESAS) | Q(numero__startswith="QA-")
        )
        for evidencia in EvidenciaOrden.objects.filter(orden__ticket__in=tickets):
            evidencia.imagen.delete(save=False)
        for firma in FirmaConformidad.objects.filter(orden__ticket__in=tickets):
            firma.imagen.delete(save=False)
        for adjunto in EvidenciaTicket.objects.filter(ticket__in=tickets):
            adjunto.archivo.delete(save=False)
        total = tickets.count()
        tickets.delete()  # en cascada: ofertas, órdenes, fotos, firmas, calificaciones e historial
        PlanMantenimiento.objects.filter(sucursal__empresa__codigo__in=EMPRESAS).delete()
        return total

    # -------------------------------------------------------------- tickets

    def _crear_ticket(self, d):
        sucursal = self.sucursales[d["suc"]]
        empresa = sucursal.empresa.codigo
        if empresa == "QAOTRA":
            creador = admin = self.usuarios["qa_otra_admin"]
        else:
            admin = self.usuarios["qa_admin"]
            creador = self.usuarios["qa_encargado"] if d["suc"] in SUCURSALES_DEL_ENCARGADO else admin

        ticket = Ticket.objects.create(
            numero=d["n"],
            titulo=d["titulo"],
            sucursal=sucursal,
            categoria=self.base["categorias"][d["cat"]],
            prioridad=d["prio"],
            estado=Ticket.Estado.ABIERTO,
            creador=creador,
            descripcion=f"Ticket de prueba (datos falsos). Qué se prueba: {d['prueba']}",
        )
        self._historial(ticket, creador, None, Ticket.Estado.ABIERTO, "Creación del ticket por incidencia.")
        if d.get("adjunto"):
            EvidenciaTicket.objects.create(
                ticket=ticket,
                archivo=ContentFile(_foto(f"{ticket.numero} · foto de la falla", 0), name="qa_falla.jpg"),
                nombre="Foto de la falla (prueba)",
            )

        flujo = d["flujo"]
        if flujo == "abierto":
            self._fechar_abierto(ticket, d)
            return
        self._cambiar_ticket(ticket, admin, Ticket.Estado.EN_REVISION, "Ticket en revisión.")
        if flujo == "revision":
            return
        oferta = self._publicar(ticket, admin, d.get("horas", 48))
        if flujo == "oferta":
            return

        tecnico = self.tecnicos[d["tecnico"]]
        user_tecnico = tecnico.usuario
        orden = tomar_oferta(oferta, tecnico, user_tecnico)
        if flujo == "asignada":
            return
        if flujo == "cancelada":
            cambiar_estado_orden(orden, OrdenTrabajo.Estado.CANCELADA, admin)
            self._fechar(ticket, d)
            return

        self._llegar(orden, user_tecnico, sucursal, d.get("llegada", "dentro"))
        cambiar_estado_orden(orden, OrdenTrabajo.Estado.EN_EJECUCION, user_tecnico, {
            "diagnostico": "Diagnóstico de prueba: se revisó la falla en terreno.",
            "costo_estimado": "45000",
        })
        for i in range(2):
            agregar_evidencia(
                orden, user_tecnico,
                ContentFile(_foto(f"{ticket.numero} · foto {i + 1}", i + 1), name=f"qa_foto_{i + 1}.jpg"),
                "Antes del trabajo" if i == 0 else "Durante el trabajo",
            )
        if flujo == "ejecucion":
            return

        registrar_firma(
            orden, user_tecnico,
            ContentFile(_firma(FIRMANTES.get(d["suc"], "Encargado")), name="qa_firma.png"),
            FIRMANTES.get(d["suc"], "Encargado"),
        )
        cambiar_estado_orden(orden, OrdenTrabajo.Estado.RESUELTA, user_tecnico, {
            "trabajo_realizado": "Trabajo de prueba: se reparó la falla y se probó el funcionamiento.",
            "costo_final": "52000",
        })
        if flujo == "cerrada":
            cerrador = self.usuarios["qa_encargado"] if d["suc"] in SUCURSALES_DEL_ENCARGADO else admin
            cambiar_estado_orden(orden, OrdenTrabajo.Estado.CERRADA, cerrador, {
                "puntuacion": d["puntuacion"],
                "comentario_calificacion": "Calificación de prueba.",
            })
        self._fechar(ticket, d)

    def _historial(self, ticket, usuario, anterior, nuevo, comentario):
        TicketHistorial.objects.create(
            ticket=ticket, usuario=usuario, estado_anterior=anterior, estado_nuevo=nuevo,
            comentario=comentario,
        )

    def _cambiar_ticket(self, ticket, usuario, nuevo, comentario):
        anterior = ticket.estado
        ticket.estado = nuevo
        ticket.save(update_fields=["estado"])
        self._historial(ticket, usuario, anterior, nuevo, comentario)

    def _publicar(self, ticket, usuario, horas):
        oferta = OfertaTicket.objects.create(
            ticket=ticket,
            estado=OfertaTicket.Estado.DISPONIBLE,
            fecha_vencimiento=timezone.now() + timezone.timedelta(hours=horas),
            observaciones="Oferta de prueba.",
        )
        self._cambiar_ticket(ticket, usuario, Ticket.Estado.PUBLICADO, "Oferta publicada para técnicos.")
        return oferta

    def _llegar(self, orden, usuario, sucursal, donde):
        if sucursal.tiene_coordenadas:
            # ≈30 m de la sucursal (dentro) o ≈2 km (fuera).
            desvio = Decimal("0.0003") if donde == "dentro" else Decimal("0.0180")
            lat, lon = sucursal.latitud + desvio, sucursal.longitud
        else:
            lat, lon = Decimal("-33.500000"), Decimal("-70.750000")
        registrar_llegada(orden, usuario, lat, lon, precision_m=8)

    # ---------------------------------------------------------------- fechas

    def _fechar_abierto(self, ticket, d):
        """Antigüedad del ticket abierto y, si corresponde, SLA ya vencido."""
        if not d.get("dias"):
            return
        inicio = timezone.now() - timezone.timedelta(days=d["dias"])
        cambios = {"fecha_creacion": inicio}
        if d.get("sla_vencido"):
            cambios["fecha_limite_sla"] = inicio + timezone.timedelta(minutes=_minutos_sla(ticket))
        Ticket.objects.filter(pk=ticket.pk).update(**cambios)
        TicketHistorial.objects.filter(ticket=ticket).update(fecha_cambio=inicio)
        EvidenciaTicket.objects.filter(ticket=ticket).update(fecha_subida=inicio)

    def _fechar(self, ticket, d):
        """Reparte las fechas de un trabajo terminado `dias` atrás.

        Con sla_ok el trabajo dura el 60 % del tiempo del SLA; si no, 2,5
        veces ese tiempo (queda fuera del SLA en los reportes).
        """
        if not d.get("dias"):
            return
        t0 = timezone.now() - timezone.timedelta(days=d["dias"])
        sla = _minutos_sla(ticket)
        duracion = timezone.timedelta(minutes=sla * (0.6 if d.get("sla_ok", True) else 2.5))
        minuto = timezone.timedelta(minutes=1)
        publicada, tomada = t0 + 10 * minuto, t0 + 20 * minuto
        llegada, inicio = t0 + 35 * minuto, t0 + 40 * minuto
        cierre = t0 + duracion
        fin = cierre - 5 * minuto

        ticket = Ticket.objects.get(pk=ticket.pk)
        Ticket.objects.filter(pk=ticket.pk).update(
            fecha_creacion=t0,
            fecha_limite_sla=t0 + timezone.timedelta(minutes=sla),
            fecha_cierre=cierre if ticket.fecha_cierre else None,
        )
        OfertaTicket.objects.filter(ticket=ticket).update(
            fecha_publicacion=publicada, fecha_tomada=tomada
        )
        orden = OrdenTrabajo.objects.filter(ticket=ticket).first()
        if orden:
            OfertaTicket.objects.filter(ticket=ticket).update(
                fecha_respuesta=llegada if orden.fecha_llegada else None
            )
            OrdenTrabajo.objects.filter(pk=orden.pk).update(
                fecha_creacion=tomada,
                fecha_llegada=llegada if orden.fecha_llegada else None,
                fecha_inicio=inicio if orden.fecha_inicio else None,
                fecha_fin=fin if orden.fecha_fin else None,
            )
            EvidenciaOrden.objects.filter(orden=orden).update(fecha_subida=inicio + 5 * minuto)
            FirmaConformidad.objects.filter(orden=orden).update(fecha_firma=fin - minuto)
            Calificacion.objects.filter(orden_trabajo=orden).update(fecha_calificacion=cierre)

        # Historial: en orden, repartido entre la creación y el cierre.
        historial = list(TicketHistorial.objects.filter(ticket=ticket).order_by("pk"))
        paso = (cierre - t0) / max(len(historial) - 1, 1)
        for i, registro in enumerate(historial):
            TicketHistorial.objects.filter(pk=registro.pk).update(fecha_cambio=t0 + i * paso)

    # ------------------------------------------------------------- el resto

    def _planes(self):
        ahora = timezone.now()
        for nombre, suc, cat, frecuencia, dias, activo in PLANES:
            PlanMantenimiento.objects.create(
                nombre=nombre,
                descripcion="Plan de mantenimiento de prueba (datos falsos).",
                sucursal=self.sucursales[suc],
                categoria=self.base["categorias"][cat],
                frecuencia=frecuencia,
                fecha_proxima=ahora + timezone.timedelta(days=dias),
                activo=activo,
            )
        plan = PlanMantenimiento.objects.get(nombre=PLAN_GENERADO_AL_PREPARAR)
        return generar_tickets_preventivos(
            usuario=self.usuarios["qa_admin"],
            sucursales=Sucursal.objects.filter(pk=plan.sucursal_id),
        )

    def _estados_fijos_de_tecnicos(self):
        for username, (_esp, estado) in TECNICOS.items():
            if estado:
                Tecnico.objects.filter(usuario__username=username).update(estado=estado)

    def _dispositivo(self):
        """Un celular registrado (falso) para qa_tecnico, como si hubiera abierto la app."""
        Dispositivo.objects.filter(usuario__username__in=USUARIOS).delete()
        Dispositivo.objects.create(
            usuario=self.usuarios["qa_tecnico"],
            token=f"qa-dispositivo-falso-{secrets.token_hex(8)}",
            plataforma=Dispositivo.Plataforma.ANDROID,
        )

    # ------------------------------------------------------------- mensajes

    def _resumen(self, borrados, generados):
        qa = Ticket.objects.filter(sucursal__empresa__codigo__in=EMPRESAS)
        self.stdout.write(f"  tickets de QA anteriores borrados: {borrados}")
        self.stdout.write(f"  tickets de QA creados: {qa.count()} (incluye {generados} preventivo)")
        self.stdout.write("  usuarios: " + ", ".join(USUARIOS))
        for d in TICKETS:
            self.stdout.write(f"    {d['n']}: {d['prueba']}")

    def _informar_clave(self, clave, archivo):
        if clave is None:
            self.stdout.write("  contraseña: sin cambios (usa --nueva-clave para generar otra).")
            return
        if archivo:
            ruta = Path(archivo)
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(
                "Entorno de QA de SEMAXEL. Misma contraseña para todos los usuarios qa_*:\n"
                f"{', '.join(USUARIOS)}\n"
                f"Generada: {timezone.localtime():%d-%m-%Y %H:%M}\n"
                f"Contraseña: {clave}\n",
                encoding="utf-8",
            )
            self.stdout.write(f"  contraseña nueva guardada en {ruta} (no se muestra).")
        else:
            self.stdout.write(f"  contraseña nueva de todos los usuarios qa_*: {clave}")
            self.stdout.write("  (guárdala: no se vuelve a mostrar)")


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------

def _minutos_sla(ticket):
    politica = SLAPolicy.obtener(ticket.sucursal.empresa, ticket.prioridad)
    return politica.tiempo_maximo_resolucion if politica else 360


def _fuente(tamano):
    try:
        return ImageFont.load_default(size=tamano)
    except TypeError:  # Pillow antiguo
        return ImageFont.load_default()


def _foto(texto, indice):
    """JPEG de 800x600 con un color y un texto: una "foto" falsa pero válida."""
    imagen = Image.new("RGB", (800, 600), COLORES_FOTOS[indice % len(COLORES_FOTOS)])
    dibujo = ImageDraw.Draw(imagen)
    dibujo.rectangle((40, 40, 760, 560), outline="white", width=6)
    dibujo.text((80, 250), "FOTO DE PRUEBA (QA)", fill="white", font=_fuente(48))
    dibujo.text((80, 330), texto, fill="white", font=_fuente(32))
    salida = io.BytesIO()
    imagen.save(salida, format="JPEG", quality=80)
    return salida.getvalue()


def _firma(nombre):
    """PNG con un trazo tipo firma y el nombre de quien firma."""
    imagen = Image.new("RGB", (600, 250), "white")
    dibujo = ImageDraw.Draw(imagen)
    puntos = [(40 + x, 120 + 45 * math.sin(x / 28) * math.cos(x / 90)) for x in range(0, 520, 4)]
    dibujo.line(puntos, fill="#0b2545", width=5)
    dibujo.line((40, 200, 560, 200), fill="#888888", width=2)
    dibujo.text((40, 210), nombre, fill="#333333", font=_fuente(24))
    salida = io.BytesIO()
    imagen.save(salida, format="PNG")
    return salida.getvalue()
