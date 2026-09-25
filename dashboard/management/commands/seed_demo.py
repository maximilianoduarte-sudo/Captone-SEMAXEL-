"""
Comando de carga de datos de demostración (Fase 4).

Puebla la base de datos con usuarios, sucursales, técnicos, especialidades,
categorías, tickets, ofertas, órdenes de trabajo y políticas SLA para poder
navegar el sistema conectado al ORM.

Uso:
    python manage.py seed_demo

Es idempotente: si los datos ya existen no los duplica.
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Usuario
from empresas.models import Empresa
from mantenimiento import models as _mantenimiento  # noqa: F401
from mantenimiento.models import PlanMantenimiento
from ofertas.models import OfertaTicket
from sla.models import SLAPolicy
from sucursales.models import Sucursal
from tecnicos.models import Especialidad, Tecnico
from tickets.models import Calificacion, Categoria, OrdenTrabajo, Ticket, TicketHistorial

PASS = "Semaxel2026!"


class Command(BaseCommand):
    help = "Carga datos de demostración (usuarios, sucursales, tickets, ofertas, órdenes, SLA)."

    def handle(self, *args, **options):
        self.stdout.write("Cargando datos de demostración...")

        # ---- Especialidades ----
        esp_data = [
            ("Electricidad", "Instalaciones y reparaciones eléctricas."),
            ("Gasfitería", "Tuberías, llaves y artefactos sanitarios."),
            ("Infraestructura", "Obra menor, muros, techos y acabados."),
            ("Climatización", "Aire acondicionado y climatización."),
            ("Carpintería", "Reparaciones y fabricación en madera."),
        ]
        especialidades = {}
        for nombre, desc in esp_data:
            esp, _ = Especialidad.objects.get_or_create(nombre=nombre, defaults={"descripcion": desc})
            especialidades[nombre] = esp
        self.stdout.write("  especialidades: listas")

        # ---- Categorías ----
        cat_data = [
            ("Fuga de agua", "Gasfitería"),
            ("Fallo eléctrico", "Electricidad"),
            ("Aire acondicionado", "Climatización"),
            ("Infraestructura / Obra", "Infraestructura"),
            ("Plomería", "Gasfitería"),
        ]
        categorias = {}
        for nombre, esp_nombre in cat_data:
            cat, _ = Categoria.objects.get_or_create(
                nombre=nombre, defaults={"especialidad": especialidades[esp_nombre]}
            )
            categorias[nombre] = cat
        self.stdout.write("  categorías: listas")

        # ---- SLA ----
        sla_data = [
            ("SLA Crítica", "CRITICA", 15, 60),
            ("SLA Alta", "ALTA", 30, 180),
            ("SLA Media", "MEDIA", 60, 360),
            ("SLA Baja", "BAJA", 120, 720),
        ]
        for nombre, prioridad, respuesta, resolucion in sla_data:
            SLAPolicy.objects.get_or_create(
                prioridad=prioridad,
                empresa=None,
                defaults={
                    "nombre": nombre,
                    "tiempo_maximo_respuesta": respuesta,
                    "tiempo_maximo_resolucion": resolucion,
                },
            )
        self.stdout.write("  SLA: políticas creadas")

        # ---- Empresa ----
        empresa, _ = Empresa.objects.get_or_create(
            codigo="SEMAXEL",
            defaults={
                "nombre": "SEMAXEL",
                "rut": "76.128.123-4",
                "ciudad": "Santiago",
                "region": "Metropolitana",
            },
        )
        self.stdout.write("  empresa: lista")

        # ---- Usuarios ----
        def crear_usuario(username, first, last, email, rol, tecnico=False, is_staff=False, is_superuser=False):
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": email,
                    "is_staff": is_staff,
                    "is_superuser": is_superuser,
                    "is_active": True,
                },
            )
            user.set_password(PASS)
            user.save()
            Usuario.objects.get_or_create(
                user=user,
                defaults={
                    "rol": rol,
                    "empresa": None if rol == "TECNICO" else empresa,
                },
            )
            return user

        admin_user = crear_usuario("admin", "Administrador", "SEMAXEL", "admin@semaxel.cl", "ADMIN", is_staff=True, is_superuser=True)
        crear_usuario("gestor", "Gestor", "SEMAXEL", "gestor@semaxel.cl", "GESTOR", is_staff=True)
        juan = crear_usuario("jperez", "Juan", "Pérez", "juan.perez@semaxel.cl", "ENCARGADO", tecnico=True)
        maria = crear_usuario("mgonzalez", "María", "González", "maria.gonzalez@semaxel.cl", "ENCARGADO", tecnico=True)
        crear_usuario("cdiaz", "Carlos", "Díaz", "carlos.diaz@semaxel.cl", "TECNICO", tecnico=True)
        crear_usuario("atorres", "Ana", "Torres", "ana.torres@semaxel.cl", "TECNICO", tecnico=True)
        crear_usuario("lfernandez", "Luis", "Fernández", "luis.fernandez@semaxel.cl", "TECNICO", tecnico=True)
        self.stdout.write("  usuarios: creados")

        # ---- Sucursales ----
        suc_data = [
            ("Providencia", "PRO", "Av. Providencia 1200", "Providencia", "Santiago", "Metropolitana", "+56 2 2345 1000", "providencia@semaxel.cl"),
            ("Santiago Centro", "STC", "Huérfanos 789", "Santiago", "Santiago", "Metropolitana", "+56 2 2345 2000", "santiagocentro@semaxel.cl"),
            ("Ñuñoa", "NUN", "Av. Irarrázaval 3450", "Ñuñoa", "Santiago", "Metropolitana", "+56 2 2345 3000", "nunoa@semaxel.cl"),
            ("Las Condes", "LCO", "Av. Apoquindo 4500", "Las Condes", "Santiago", "Metropolitana", "+56 2 2345 4000", "lascondes@semaxel.cl"),
        ]
        sucursales = {}
        for nombre, codigo, direccion, comuna, ciudad, region, tel, correo in suc_data:
            suc, _ = Sucursal.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "empresa": empresa,
                    "nombre": nombre,
                    "direccion": direccion,
                    "comuna": comuna,
                    "ciudad": ciudad,
                    "region": region,
                    "telefono": tel,
                    "correo": correo,
                },
            )
            sucursales[nombre] = suc
        sucursales["Providencia"].encargados.add(juan)
        sucursales["Santiago Centro"].encargados.add(maria)
        sucursales["Ñuñoa"].encargados.add(admin_user)
        sucursales["Las Condes"].estado = "INACTIVA"
        sucursales["Las Condes"].save()
        self.stdout.write("  sucursales: creadas")

        # ---- Técnicos ----
        tecnicos = {}
        tec_data = [
            ("jperez", [("Electricidad",), ("Gasfitería",)], "DISPONIBLE", "+56 9 1234 5678"),
            ("mgonzalez", [("Gasfitería",), ("Carpintería",)], "OCUPADO", "+56 9 2345 6789"),
            ("cdiaz", [("Climatización",), ("Electricidad",)], "DISPONIBLE", "+56 9 3456 7890"),
            ("atorres", [("Infraestructura",), ("Carpintería",)], "NO_DISPONIBLE", "+56 9 4567 8901"),
            ("lfernandez", [("Electricidad",)], "INACTIVO", "+56 9 5678 9012"),
        ]
        for username, esp_nombres, estado, tel in tec_data:
            user = User.objects.get(username=username)
            tec, _ = Tecnico.objects.get_or_create(
                usuario=user,
                defaults={"telefono": tel, "estado": estado, "documento": f"DOC-{username.upper()}"},
            )
            for (esp_nombre,) in esp_nombres:
                tec.especialidades.add(especialidades[esp_nombre])
            tecnicos[username] = tec
        self.stdout.write("  técnicos: creados")

        # ---- Tickets ----
        ahora = timezone.now()
        tk_data = [
            ("TK-00001", "Fuga de agua en cocina", "Providencia", "Fuga de agua", "ALTA", "ABIERTO", juan, "Se detectó una fuga de agua bajo el lavaplatos de la cocina principal. El piso se está mojando y requiere atención urgente para evitar daños mayores."),
            ("TK-00002", "Fallo en iluminación de bodega", "Santiago Centro", "Fallo eléctrico", "MEDIA", "EN_REVISION", maria, "Las luminarias del sector bodega parpadean y dos no encienden. Posible sobrecarga en el circuito."),
            ("TK-00003", "Aire acondicionado sin enfriar", "Ñuñoa", "Aire acondicionado", "ALTA", "PUBLICADO", maria, "El equipo de aire acondicionado de la sala de reuniones no enfría correctamente. Temperatura ambiente superior a lo normal."),
            ("TK-00004", "Drenaje obstruido en baño", "Providencia", "Plomería", "MEDIA", "EN_EJECUCION", juan, "El lavaplatos del segundo baño tiene un drenaje lento por obstrucción. Se requiere despeje de cañerías."),
            ("TK-00005", "Grifo con filtración", "Santiago Centro", "Plomería", "BAJA", "RESUELTO", maria, "El grifo del primer piso filtra permanentemente. Se reemplazó empaquetadura y quedó resuelto."),
            ("TK-00006", "Pintura y reparación de muro", "Ñuñoa", "Infraestructura / Obra", "BAJA", "CERRADO", juan, "Reparación de grietas y repintado de muro en el pasillo de acceso."),
            ("TK-00007", "Reparación de tablero eléctrico", "Providencia", "Fallo eléctrico", "CRITICA", "ABIERTO", maria, "Cortocircuito en tablero general. Requiere técnico eléctrico certificado con urgencia."),
            ("TK-00008", "Mantención de sellos de ventanas", "Santiago Centro", "Infraestructura / Obra", "BAJA", "ABIERTO", juan, "Reemplazo de sellos de goma en ventanas del segundo piso para evitar filtraciones."),
            ("TK-00009", "Reparación de grifería", "Ñuñoa", "Plomería", "MEDIA", "ABIERTO", maria, "Reparación de grifería del baño de personal con fuga en la base."),
        ]
        tickets = {}
        for numero, titulo, suc_nombre, cat_nombre, prioridad, estado, creador, descripcion in tk_data:
            tk, _ = Ticket.objects.get_or_create(
                numero=numero,
                defaults={
                    "titulo": titulo,
                    "sucursal": sucursales[suc_nombre],
                    "categoria": categorias[cat_nombre],
                    "prioridad": prioridad,
                    "estado": estado,
                    "creador": creador,
                    "descripcion": descripcion,
                },
            )
            tickets[numero] = tk
        self.stdout.write("  tickets: creados")

        # ---- Historial inicial ----
        for numero, ticket in tickets.items():
            TicketHistorial.objects.get_or_create(
                ticket=ticket,
                estado_nuevo=ticket.estado,
                defaults={
                    "usuario": ticket.creador,
                    "estado_anterior": None,
                    "comentario": "Creación del ticket por incidencia.",
                },
            )

        # ---- Ofertas ----
        def crea_oferta(numero, estado, tecnico=None, dias_vencimiento=2, tomada=None):
            ticket = tickets[numero]
            defaults = {"estado": estado}
            if tecnico:
                defaults["tecnico"] = tecnico
                defaults["fecha_tomada"] = tomada or ahora
            defaults["fecha_vencimiento"] = ahora + timezone.timedelta(days=dias_vencimiento)
            oferta, _ = OfertaTicket.objects.get_or_create(ticket=ticket, defaults=defaults)
            return oferta

        crea_oferta("TK-00003", "DISPONIBLE", dias_vencimiento=-1)
        crea_oferta("TK-00007", "DISPONIBLE", dias_vencimiento=1)
        crea_oferta("TK-00008", "DISPONIBLE", dias_vencimiento=4)
        crea_oferta("TK-00009", "DISPONIBLE", dias_vencimiento=3)
        crea_oferta("TK-00004", "TOMADA", tecnico=tecnicos["jperez"], tomada=ahora - timezone.timedelta(hours=4))
        crea_oferta("TK-00005", "COMPLETADA", tecnico=tecnicos["cdiaz"], tomada=ahora - timezone.timedelta(days=1))
        self.stdout.write("  ofertas: creadas")

        # ---- Órdenes de trabajo ----
        def crea_orden(numero, tecnico, estado, inicio=None, fin=None, diagnostico="", trabajo="", observaciones=""):
            ticket = tickets[numero]
            orden, _ = OrdenTrabajo.objects.get_or_create(
                ticket=ticket,
                defaults={
                    "tecnico": tecnico,
                    "oferta": ticket.oferta if hasattr(ticket, "oferta") else None,
                    "estado": estado,
                    "fecha_inicio": inicio,
                    "fecha_fin": fin,
                    "diagnostico": diagnostico,
                    "trabajo_realizado": trabajo,
                    "observaciones": observaciones,
                },
            )
            return orden

        crea_orden(
            "TK-00004", tecnicos["jperez"], "EN_EJECUCION",
            inicio=ahora - timezone.timedelta(hours=3),
            diagnostico="Obstrucción parcial en la trampa del drenaje.",
            trabajo="Despeje de cañerías en curso.",
            observaciones="Se aplicará desatascador y se verificará flujo.",
        )
        crea_orden(
            "TK-00005", tecnicos["cdiaz"], "RESUELTA",
            inicio=ahora - timezone.timedelta(days=1, hours=-1),
            fin=ahora - timezone.timedelta(days=1),
            diagnostico="Empaquetadura en mal estado.",
            trabajo="Reemplazo de empaquetadura del grifo.",
            observaciones="Trabajo finalizado correctamente. Sin fugas posteriores.",
        )
        crea_orden(
            "TK-00006", tecnicos["atorres"], "CERRADA",
            inicio=ahora - timezone.timedelta(days=2),
            fin=ahora - timezone.timedelta(days=1),
            diagnostico="Grietas superficiales en muro de acceso.",
            trabajo="Reparación de grietas y repintado.",
            observaciones="Orden cerrada tras inspección final.",
        )
        # Calificación de la orden cerrada
        orden_cerrada = OrdenTrabajo.objects.get(ticket=tickets["TK-00006"])
        Calificacion.objects.get_or_create(
            orden_trabajo=orden_cerrada,
            defaults={"tecnico": tecnicos["atorres"], "puntuacion": 5, "comentario": "Excelente trabajo."},
        )
        self.stdout.write("  órdenes de trabajo: creadas")

        # ================= Segunda empresa (aislamiento multi-empresa) =================
        empresa_b, _ = Empresa.objects.get_or_create(
            codigo="EMPB",
            defaults={
                "nombre": "TecnoMant SPA",
                "rut": "77.123.456-5",
                "ciudad": "Temuco",
                "region": "Araucanía",
            },
        )
        self.stdout.write("  empresa B: lista")

        # ---- SLA específico de la empresa B (por empresa) ----
        sla_data_b = [
            ("SLA Crítica TecnoMant", "CRITICA", 10, 45),
            ("SLA Alta TecnoMant", "ALTA", 20, 120),
            ("SLA Media TecnoMant", "MEDIA", 45, 240),
            ("SLA Baja TecnoMant", "BAJA", 90, 480),
        ]
        for nombre, prioridad, respuesta, resolucion in sla_data_b:
            SLAPolicy.objects.get_or_create(
                prioridad=prioridad,
                empresa=empresa_b,
                defaults={
                    "nombre": nombre,
                    "tiempo_maximo_respuesta": respuesta,
                    "tiempo_maximo_resolucion": resolucion,
                },
            )
        self.stdout.write("  SLA B: políticas por empresa creadas")

        def crear_usuario_b(username, first, last, email, rol, is_staff=False):
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": email,
                    "is_staff": is_staff,
                    "is_active": True,
                },
            )
            user.set_password(PASS)
            user.save()
            Usuario.objects.get_or_create(
                user=user,
                defaults={"rol": rol, "empresa": empresa_b},
            )
            return user

        gestor_b = crear_usuario_b(
            "gestionb", "Gabriela", "Fuentes", "gestionb@tecnomant.cl", "GESTOR", is_staff=True
        )
        encargado_b = crear_usuario_b(
            "encargadob", "Enrique", "Rojas", "encargado@tecnomant.cl", "ENCARGADO"
        )
        self.stdout.write("  usuarios B: creados")

        suc_data_b = [
            ("Centro", "CEN", "Manuel Montt 555, Temuco", "Temuco", "Temuco", "Araucanía", "+56 45 2231 100", "centro@tecnomant.cl"),
            ("Mall Plaza", "MAL", "Av. San Martín 890, Temuco", "Temuco", "Temuco", "Araucanía", "+56 45 2231 200", "mall@tecnomant.cl"),
        ]
        sucursales_b = {}
        for nombre, codigo, direccion, comuna, ciudad, region, tel, correo in suc_data_b:
            suc, _ = Sucursal.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "empresa": empresa_b,
                    "nombre": nombre,
                    "direccion": direccion,
                    "comuna": comuna,
                    "ciudad": ciudad,
                    "region": region,
                    "telefono": tel,
                    "correo": correo,
                },
            )
            sucursales_b[nombre] = suc
        sucursales_b["Centro"].encargados.add(encargado_b)
        sucursales_b["Mall Plaza"].encargados.add(encargado_b)
        self.stdout.write("  sucursales B: creadas")

        tk_data_b = [
            ("EMPB-00001", "Falla de bomba de agua", "Centro", "Plomería", "ALTA", "ABIERTO", gestor_b, "La bomba del estanque elevado no presuriza. Riesgo de corte de suministro principal."),
            ("EMPB-00002", "Climatización de sala de servidores", "Mall Plaza", "Aire acondicionado", "MEDIA", "PUBLICADO", encargado_b, "El equipo de climatización de la sala de servidores opera a media capacidad."),
            ("EMPB-00003", "Cortocircuito en bodega", "Centro", "Fallo eléctrico", "CRITICA", "EN_EJECUCION", encargado_b, "Cortocircuito intermitente en tablero de bodega. Requiere revisión eléctrica urgente."),
        ]
        tickets_b = {}
        for numero, titulo, suc_nombre, cat_nombre, prioridad, estado, creador, descripcion in tk_data_b:
            tk, _ = Ticket.objects.get_or_create(
                numero=numero,
                defaults={
                    "titulo": titulo,
                    "sucursal": sucursales_b[suc_nombre],
                    "categoria": categorias[cat_nombre],
                    "prioridad": prioridad,
                    "estado": estado,
                    "creador": creador,
                    "descripcion": descripcion,
                },
            )
            tickets_b[numero] = tk
        for numero, ticket in tickets_b.items():
            TicketHistorial.objects.get_or_create(
                ticket=ticket,
                estado_nuevo=ticket.estado,
                defaults={
                    "usuario": ticket.creador,
                    "estado_anterior": None,
                    "comentario": "Creación del ticket por incidencia.",
                },
            )

        def crea_oferta_b(numero, estado, tecnico=None, dias_vencimiento=2, tomada=None):
            ticket = tickets_b[numero]
            defaults = {"estado": estado}
            if tecnico:
                defaults["tecnico"] = tecnico
                defaults["fecha_tomada"] = tomada or ahora
            defaults["fecha_vencimiento"] = ahora + timezone.timedelta(days=dias_vencimiento)
            oferta, _ = OfertaTicket.objects.get_or_create(ticket=ticket, defaults=defaults)
            return oferta

        crea_oferta_b("EMPB-00002", "DISPONIBLE", dias_vencimiento=3)
        crea_oferta_b("EMPB-00003", "TOMADA", tecnico=tecnicos["cdiaz"], tomada=ahora - timezone.timedelta(hours=2))

        def crea_orden_b(numero, tecnico, estado, inicio=None, fin=None, diagnostico="", trabajo="", observaciones=""):
            ticket = tickets_b[numero]
            orden, _ = OrdenTrabajo.objects.get_or_create(
                ticket=ticket,
                defaults={
                    "tecnico": tecnico,
                    "oferta": ticket.oferta if hasattr(ticket, "oferta") else None,
                    "estado": estado,
                    "fecha_inicio": inicio,
                    "fecha_fin": fin,
                    "diagnostico": diagnostico,
                    "trabajo_realizado": trabajo,
                    "observaciones": observaciones,
                },
            )
            return orden

        crea_orden_b(
            "EMPB-00003", tecnicos["cdiaz"], "EN_EJECUCION",
            inicio=ahora - timezone.timedelta(hours=1),
            diagnostico="Posible falso contacto en tablero de bodega.",
            trabajo="Revisión de empalmes y protecciones en curso.",
            observaciones="Se aislará circuito mientras se repara.",
        )
        self.stdout.write("  tickets, ofertas y órdenes B: creadas")

        # ---- Planes de mantenimiento preventivo ----
        plan_sem_data = [
            ("Mantención A/A", "Ñuñoa", "Aire acondicionado", "SEMESTRAL", ahora + timezone.timedelta(days=15)),
            ("Limpieza filtros eléctricos", "Providencia", "Fallo eléctrico", "MENSUAL", ahora + timezone.timedelta(days=5)),
            ("Revisión de grifería y sellos", "Santiago Centro", "Plomería", "TRIMESTRAL", ahora - timezone.timedelta(days=3)),
        ]
        for nombre, suc_nombre, cat_nombre, frecuencia, fecha in plan_sem_data:
            PlanMantenimiento.objects.get_or_create(
                nombre=nombre,
                sucursal=sucursales[suc_nombre],
                defaults={
                    "descripcion": f"Ejecución preventiva programada del plan {nombre}.",
                    "categoria": categorias[cat_nombre],
                    "frecuencia": frecuencia,
                    "fecha_proxima": fecha,
                },
            )
        plan_b_data = [
            ("Mantenimiento bomba de agua", "Centro", "Plomería", "MENSUAL", ahora - timezone.timedelta(days=1)),
            ("Clima sala de servidores", "Mall Plaza", "Aire acondicionado", "BIMESTRAL", ahora + timezone.timedelta(days=10)),
        ]
        for nombre, suc_nombre, cat_nombre, frecuencia, fecha in plan_b_data:
            PlanMantenimiento.objects.get_or_create(
                nombre=nombre,
                sucursal=sucursales_b[suc_nombre],
                defaults={
                    "descripcion": f"Ejecución preventiva programada del plan {nombre}.",
                    "categoria": categorias[cat_nombre],
                    "frecuencia": frecuencia,
                    "fecha_proxima": fecha,
                },
            )
        self.stdout.write("  planes de mantenimiento: creados")

        # Generación inicial de los preventivos vencidos (idempotente)
        from mantenimiento.services import generar_tickets_preventivos

        generados = generar_tickets_preventivos()
        self.stdout.write(f"  preventivos: {generados} ticket(s) generado(s)")

        # ---- Backfill SLA: fecha_limite_sla en tickets sin ella (idempotente) ----
        actualizados = 0
        for ticket_sla in (
            Ticket.objects.filter(fecha_limite_sla__isnull=True)
            .select_related("sucursal__empresa")
        ):
            politica = SLAPolicy.obtener(ticket_sla.sucursal.empresa, ticket_sla.prioridad)
            if politica:
                base = ticket_sla.fecha_creacion or timezone.now()
                ticket_sla.fecha_limite_sla = base + timezone.timedelta(
                    minutes=politica.tiempo_maximo_resolucion
                )
                ticket_sla.save(update_fields=["fecha_limite_sla"])
                actualizados += 1
        self.stdout.write(f"  SLA: backfill fecha_limite_sla en {actualizados} tickets")

        # ---- Backfill fecha_cierre para tickets cerrados/resueltos (idempotente) ----
        cerrados_ci = 0
        for ticket_ci in Ticket.objects.filter(
            estado__in=[Ticket.Estado.CERRADO, Ticket.Estado.RESUELTO],
            fecha_cierre__isnull=True,
        ):
            orden_ci = OrdenTrabajo.objects.filter(ticket=ticket_ci).first()
            fecha_ci = (
                orden_ci.fecha_fin if orden_ci and orden_ci.fecha_fin
                else ticket_ci.fecha_actualizacion
            )
            if fecha_ci:
                ticket_ci.fecha_cierre = fecha_ci
                ticket_ci.save(update_fields=["fecha_cierre"])
                cerrados_ci += 1
        self.stdout.write(f"  SLA: backfill fecha_cierre en {cerrados_ci} tickets cerrados/resueltos")

        self.stdout.write(self.style.SUCCESS(f"Datos de demostración cargados. Todos los usuarios usan la contraseña: {PASS}"))