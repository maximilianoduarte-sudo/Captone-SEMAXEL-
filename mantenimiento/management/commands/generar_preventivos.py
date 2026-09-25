from django.core.management.base import BaseCommand

from mantenimiento.services import generar_tickets_preventivos


class Command(BaseCommand):
    help = "Genera los tickets preventivos vencidos de los planes de mantenimiento activos."

    def handle(self, *args, **options):
        generados = generar_tickets_preventivos()
        self.stdout.write(self.style.SUCCESS(f"{generados} ticket(s) preventivo(s) generado(s)."))