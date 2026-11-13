from datetime import time

from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Empresa

from .models import HorarioSucursal, Sucursal


class CoordenadasYHorarioTests(TestCase):
    """Coordenadas GPS y horario de la sucursal (Documento A, flujo 2)."""

    def setUp(self):
        # Datos hipotéticos de prueba.
        empresa = Empresa.objects.create(nombre="Cadena Demo", rut="76.000.000-0", codigo="DEMO")
        self.sucursal = Sucursal(
            empresa=empresa, nombre="Local Centro", codigo="CEN", direccion="Av. Ejemplo 123"
        )

    def test_coordenadas_validas(self):
        self.sucursal.latitud, self.sucursal.longitud = "-33.437800", "-70.650400"
        self.sucursal.full_clean()
        self.assertTrue(self.sucursal.tiene_coordenadas)

    def test_sin_coordenadas_es_valido(self):
        self.sucursal.full_clean()
        self.assertFalse(self.sucursal.tiene_coordenadas)

    def test_latitud_sin_longitud_no_es_valido(self):
        self.sucursal.latitud = "-33.437800"
        with self.assertRaises(ValidationError):
            self.sucursal.full_clean()

    def test_latitud_fuera_de_rango(self):
        self.sucursal.latitud, self.sucursal.longitud = "-95", "-70.650400"
        with self.assertRaises(ValidationError):
            self.sucursal.full_clean()

    def test_horario_con_apertura_posterior_al_cierre_no_es_valido(self):
        self.sucursal.save()
        horario = HorarioSucursal(
            sucursal=self.sucursal, dia_semana=0, hora_apertura=time(20), hora_cierre=time(9)
        )
        with self.assertRaises(ValidationError):
            horario.full_clean()
