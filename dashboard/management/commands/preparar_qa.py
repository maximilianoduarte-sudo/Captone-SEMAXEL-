"""
Prepara un perfil de QA para probar a mano la app y la web.

Crea (o deja como nuevos):

- ``qa_tecnico`` (rol TECNICO), para la app móvil. Tiene las especialidades
  Electricidad, Gasfitería e Infraestructura; a propósito NO tiene
  Climatización, para comprobar que la app no le muestra ofertas que no
  puede tomar.
- ``qa_admin`` (rol ADMIN de la empresa SEMAXEL), para revisar en la web los
  tickets y las órdenes de QA (fotos, firma y registro de llegada).
- Seis tickets ``QA-0001`` a ``QA-0006`` con un caso de prueba cada uno (ver
  ESCENARIO). Todos son datos hipotéticos.

Cada ejecución borra los tickets ``QA-`` anteriores (con sus órdenes, fotos y
firmas) y los vuelve a crear, para repetir las pruebas desde cero. No toca los
datos de ``seed_demo``.

La contraseña de los dos usuarios es aleatoria y nunca queda en el
repositorio: se genera al crearlos (o con ``--nueva-clave``) y se muestra una
sola vez en la consola, o se guarda en el archivo de ``--archivo-clave``.

Requiere haber ejecutado ``seed_demo`` antes (empresa, categorías y
sucursales con coordenadas).

Uso:
    python manage.py preparar_qa
    python manage.py preparar_qa --archivo-clave D:\\herramientas-servidor\\credenciales\\qa.txt
    python manage.py preparar_qa --nueva-clave
"""

import secrets
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Usuario
from empresas.models import Empresa
from ofertas.models import OfertaTicket
from ofertas.services import OfertaNoTomable, tomar_oferta
from sucursales.models import Sucursal
from tecnicos.models import Especialidad, Tecnico
from tickets.models import Categoria, Ticket, TicketHistorial

PREFIJO = "QA-"
USUARIO_TECNICO = "qa_tecnico"
USUARIO_ADMIN = "qa_admin"
ESPECIALIDADES_TECNICO = ("Electricidad", "Gasfitería", "Infraestructura")

# (número, título, código de sucursal, categoría, prioridad, horas de vigencia
#  de la oferta, ¿la toma qa_tecnico al preparar?, qué se prueba)
ESCENARIO = [
    ("QA-0001", "[QA] Enchufe quemado en caja 2", "PRO", "Fallo eléctrico", "ALTA", 72, False,
     "Flujo completo: tomar, llegar DENTRO del radio, iniciar, fotos, firma y resolver."),
    ("QA-0002", "[QA] Fuga bajo lavamanos", "NUN", "Fuga de agua", "MEDIA", 48, False,
     "Llegada FUERA del radio: poner una ubicación lejana; debe quedar no verificada."),
    ("QA-0003", "[QA] Grieta en muro de bodega", "STC", "Infraestructura / Obra", "CRITICA", 2, False,
     "Oferta urgente: vence en 2 horas."),
    ("QA-0004", "[QA] Aire acondicionado con ruido", "PRO", "Aire acondicionado", "ALTA", 48, False,
     "NO debe aparecer en la app: qa_tecnico no tiene Climatización."),
    ("QA-0005", "[QA] Llave de paso goteando", "STC", "Plomería", "MEDIA", 48, True,
     "Ya tomada por qa_tecnico: probar directo llegada, fotos y firma."),
    ("QA-0006", "[QA] Luminaria de pasillo apagada", "NUN", "Fallo eléctrico", "BAJA", -1, False,
     "NO debe aparecer en la app: la oferta venció hace 1 hora."),
]


class Command(BaseCommand):
    help = "Crea o reinicia el perfil de QA (qa_tecnico y qa_admin) con tickets de prueba propios."

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
        with transaction.atomic():
            base = self._datos_base()
            clave, admin, tecnico = self._usuarios(base, opciones["nueva_clave"])
            borrados = self._borrar_escenario_anterior()
            self._crear_escenario(base, admin, tecnico)

        self.stdout.write(f"  tickets QA anteriores borrados: {borrados}")
        self.stdout.write(f"  tickets QA creados: {len(ESCENARIO)}")
        for numero, _t, _s, _c, _p, _h, _tomada, prueba in ESCENARIO:
            self.stdout.write(f"    {numero}: {prueba}")
        self._informar_clave(clave, opciones["archivo_clave"])
        self.stdout.write(self.style.SUCCESS("Perfil de QA listo."))

    # ------------------------------------------------------------------ datos

    def _datos_base(self):
        """Empresa, sucursales, categorías y especialidades que crea seed_demo."""
        try:
            empresa = Empresa.objects.get(codigo="SEMAXEL")
            sucursales = {s.codigo: s for s in Sucursal.objects.filter(codigo__in=["PRO", "STC", "NUN"])}
            categorias = {c.nombre: c for c in Categoria.objects.all()}
            especialidades = [Especialidad.objects.get(nombre=n) for n in ESPECIALIDADES_TECNICO]
        except (Empresa.DoesNotExist, Especialidad.DoesNotExist):
            raise CommandError("Faltan los datos base. Ejecuta primero: python manage.py seed_demo")
        faltan = {"PRO", "STC", "NUN"} - set(sucursales)
        faltan |= {c for _n, _t, _s, c, *_ in ESCENARIO} - set(categorias)
        if faltan:
            raise CommandError(
                f"Faltan datos base ({', '.join(sorted(faltan))}). "
                "Ejecuta primero: python manage.py seed_demo"
            )
        sin_gps = [s.nombre for s in sucursales.values() if s.latitud is None]
        if sin_gps:
            raise CommandError(f"Estas sucursales no tienen coordenadas: {', '.join(sin_gps)}.")
        return {
            "empresa": empresa,
            "sucursales": sucursales,
            "categorias": categorias,
            "especialidades": especialidades,
        }

    def _usuarios(self, base, nueva_clave):
        """Crea qa_tecnico y qa_admin. Devuelve la clave solo si es nueva."""
        existen = User.objects.filter(username__in=[USUARIO_TECNICO, USUARIO_ADMIN]).count() == 2
        clave = secrets.token_urlsafe(12) if (nueva_clave or not existen) else None

        admin = self._usuario(USUARIO_ADMIN, "QA", "Administración", Usuario.Rol.ADMIN, base["empresa"], clave)
        user_tecnico = self._usuario(USUARIO_TECNICO, "QA", "Técnico", Usuario.Rol.TECNICO, None, clave)

        tecnico, _ = Tecnico.objects.get_or_create(
            usuario=user_tecnico,
            defaults={"telefono": "+56 9 0000 0000", "documento": "DOC-QA-TECNICO"},
        )
        tecnico.especialidades.set(base["especialidades"])
        tecnico.estado = Tecnico.Estado.DISPONIBLE
        tecnico.save(update_fields=["estado"])
        return clave, admin, tecnico

    def _usuario(self, username, nombre, apellido, rol, empresa, clave):
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": nombre,
                "last_name": apellido,
                "email": f"{username.replace('_', '.')}@semaxel.test",
                "is_active": True,
            },
        )
        if clave:
            user.set_password(clave)
        user.is_active = True
        user.save()
        perfil, _ = Usuario.objects.get_or_create(user=user, defaults={"rol": rol, "empresa": empresa})
        if perfil.rol != rol or perfil.empresa != empresa:
            perfil.rol, perfil.empresa = rol, empresa
            perfil.save()
        return user

    def _borrar_escenario_anterior(self):
        """Borra los tickets QA- y los archivos de sus fotos y firmas."""
        tickets = Ticket.objects.filter(numero__startswith=PREFIJO)
        for ticket in tickets:
            orden = getattr(ticket, "orden_trabajo", None)
            if orden is None:
                continue
            for evidencia in orden.evidencias.all():
                evidencia.imagen.delete(save=False)
            firma = getattr(orden, "firma", None)
            if firma is not None:
                firma.imagen.delete(save=False)
        total = tickets.count()
        tickets.delete()  # en cascada: oferta, orden, fotos, firma e historial
        return total

    def _crear_escenario(self, base, admin, tecnico):
        ahora = timezone.now()
        for numero, titulo, suc, cat, prioridad, horas, tomada, prueba in ESCENARIO:
            ticket = Ticket.objects.create(
                numero=numero,
                titulo=titulo,
                sucursal=base["sucursales"][suc],
                categoria=base["categorias"][cat],
                prioridad=prioridad,
                estado=Ticket.Estado.PUBLICADO,
                creador=admin,
                descripcion=f"Ticket de prueba (datos hipotéticos). Qué se prueba: {prueba}",
            )
            TicketHistorial.objects.create(
                ticket=ticket,
                usuario=admin,
                estado_anterior=None,
                estado_nuevo=ticket.estado,
                comentario="Ticket de QA creado por preparar_qa.",
            )
            oferta = OfertaTicket.objects.create(
                ticket=ticket,
                estado=OfertaTicket.Estado.DISPONIBLE,
                fecha_vencimiento=ahora + timezone.timedelta(hours=horas),
                observaciones="Oferta de QA.",
            )
            if tomada:
                try:
                    tomar_oferta(oferta, tecnico, tecnico.usuario)
                except OfertaNoTomable as error:
                    raise CommandError(f"No se pudo tomar {numero}: {error.mensaje}")

    # ------------------------------------------------------------- contraseña

    def _informar_clave(self, clave, archivo):
        if clave is None:
            self.stdout.write(
                "  contraseña: sin cambios (usa --nueva-clave para generar otra)."
            )
            return
        usuarios = f"{USUARIO_TECNICO} (app) y {USUARIO_ADMIN} (web)"
        if archivo:
            ruta = Path(archivo)
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(
                f"Perfil de QA de SEMAXEL. Usuarios: {usuarios}\n"
                f"Generada: {timezone.localtime():%d-%m-%Y %H:%M}\n"
                f"Contraseña: {clave}\n",
                encoding="utf-8",
            )
            self.stdout.write(f"  contraseña nueva guardada en {ruta} (no se muestra).")
        else:
            self.stdout.write(f"  contraseña nueva de {usuarios}: {clave}")
            self.stdout.write("  (guárdala: no se vuelve a mostrar)")
