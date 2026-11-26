package cl.semaxel.tecnico.ui.comun

import cl.semaxel.tecnico.data.remote.Horario
import cl.semaxel.tecnico.data.remote.Sucursal
import org.junit.Assert.assertEquals
import org.junit.Test

class FormatoTest {

    @Test
    fun `fecha ISO del servidor se muestra en hora de Chile`() {
        assertEquals("13/11/2026 15:42", Formato.fecha("2026-11-13T15:42:10.512-03:00"))
        // La misma hora en UTC se convierte a la hora de Chile.
        assertEquals("13/11/2026 15:42", Formato.fecha("2026-11-13T18:42:10Z"))
        assertEquals("—", Formato.fecha(null))
    }

    @Test
    fun `montos en pesos con separador de miles`() {
        assertEquals("$25.000", Formato.pesos("25000.00"))
        assertEquals("$1.250.000", Formato.pesos("1250000"))
        assertEquals("$900", Formato.pesos("900.40"))
        assertEquals("—", Formato.pesos(null))
    }

    @Test
    fun `la direccion no repite comuna ni ciudad`() {
        // Caso real de seed_demo: la dirección ya trae la ciudad y comuna = ciudad.
        val centro = Sucursal(nombre = "Centro", direccion = "Manuel Montt 555, Temuco", comuna = "Temuco", ciudad = "Temuco")
        assertEquals("Manuel Montt 555, Temuco", Formato.direccion(centro))
        val providencia = Sucursal(nombre = "P", direccion = "Av. Providencia 1200", comuna = "Providencia", ciudad = "Santiago")
        assertEquals("Av. Providencia 1200, Santiago", Formato.direccion(providencia))
        val soloComuna = Sucursal(nombre = "S", direccion = "Av. Ejemplo 123", comuna = "Ñuñoa")
        assertEquals("Av. Ejemplo 123, Ñuñoa", Formato.direccion(soloComuna))
    }

    @Test
    fun `dias sin horario se muestran cerrados`() {
        val horario = Formato.horario(listOf(Horario(diaSemana = 0, dia = "Lunes", apertura = "09:00", cierre = "20:00")))
        assertEquals(7, horario.size)
        assertEquals("Lunes: 09:00 a 20:00", horario[0])
        assertEquals("Domingo: cerrado", horario[6])
        assertEquals(listOf("Horario no informado"), Formato.horario(emptyList()))
    }
}
