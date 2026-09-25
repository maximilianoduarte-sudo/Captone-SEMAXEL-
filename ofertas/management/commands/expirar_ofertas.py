from django.core.management.base import BaseCommand

from ofertas.services import expirar_ofertas_vencidas


class Command(BaseCommand):
    help = "Marca como expiradas las ofertas DISPONIBLE cuyo vencimiento llegó."

    def handle(self, *args, **options):
        expiradas = expirar_ofertas_vencidas()
        self.stdout.write(
            self.style.SUCCESS(f"{expiradas} oferta(s) expirada(s).")
        )