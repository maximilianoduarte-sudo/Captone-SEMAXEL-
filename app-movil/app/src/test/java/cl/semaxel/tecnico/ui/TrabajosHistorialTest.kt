package cl.semaxel.tecnico.ui

import cl.semaxel.tecnico.data.Muestras
import cl.semaxel.tecnico.data.remote.Ganancias
import cl.semaxel.tecnico.data.remote.Tecnico
import cl.semaxel.tecnico.ui.comun.WhatsApp
import cl.semaxel.tecnico.ui.trabajos.historialPorMes
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** WhatsApp a la sucursal, historial por mes y ganancias del perfil. */
class TrabajosHistorialTest {

    // ------------------------------------------------------------ WhatsApp

    @Test
    fun `el telefono chileno queda en formato internacional`() {
        assertEquals("56912345678", WhatsApp.numero("+56 9 1234 5678"))
        assertEquals("56912345678", WhatsApp.numero("9 1234 5678"))
        assertEquals("56221234567", WhatsApp.numero("+56 2 2123 4567"))
        assertNull(WhatsApp.numero(""))
        assertNull(WhatsApp.numero("123"))
    }

    @Test
    fun `el enlace abre la conversacion con el mensaje del trabajo`() {
        val orden = Muestras.orden().copy(sucursal = Muestras.sucursal.copy(telefono = "+56 9 1234 5678"))
        val enlace = WhatsApp.enlace(orden)!!
        assertTrue(enlace.startsWith("https://wa.me/56912345678?text=Hola%2C%20le%20escribe"))
        assertTrue("sin + ni espacios crudos", " " !in enlace && "+" !in enlace)
        assertNull("sin teléfono no hay botón", WhatsApp.enlace(Muestras.orden()))
    }

    // ------------------------------------------------------------ historial

    @Test
    fun `el historial se agrupa por mes del mas reciente al mas antiguo`() {
        val base = Muestras.orden(estado = "CERRADA")
        val ordenes = listOf(
            base.copy(id = 1, fechaFin = "2026-10-05T12:00:00-03:00", costoFinal = "20000.00"),
            base.copy(id = 2, fechaFin = "2026-11-02T12:00:00-03:00", costoFinal = "52000.00"),
            base.copy(id = 3, estado = "RESUELTA", fechaFin = "2026-11-10T12:00:00-03:00", costoFinal = "8000.00"),
            // Cancelada: sin fecha de fin, va en el mes de asignación y no suma.
            base.copy(id = 4, estado = "CANCELADA", fechaAsignacion = "2026-11-01T09:00:00-03:00", costoFinal = "999"),
        )
        val meses = historialPorMes(ordenes)

        assertEquals(listOf("Noviembre 2026", "Octubre 2026"), meses.map { it.titulo })
        assertEquals(listOf(3, 2, 4), meses[0].ordenes.map { it.id })
        assertEquals(0, meses[0].total.compareTo("60000".toBigDecimal()))
        assertEquals(0, meses[1].total.compareTo("20000".toBigDecimal()))
    }

    @Test
    fun `el mes se calcula en hora de Chile`() {
        // 1 de diciembre 01:00 UTC = 30 de noviembre 22:00 en Chile.
        val orden = Muestras.orden(estado = "CERRADA").copy(fechaFin = "2026-12-01T01:00:00Z")
        assertEquals("Noviembre 2026", historialPorMes(listOf(orden)).single().titulo)
    }

    // ------------------------------------------------------------ perfil

    @Test
    fun `el perfil lee las ganancias del servidor`() {
        val json = Json { ignoreUnknownKeys = true }
        val tecnico = json.decodeFromString(
            Tecnico.serializer(),
            """{"id":1,"username":"u","nombre":"N","estado":"OCUPADO",
               "ganancias":{"mes":"104000.00","anio":"360000.00","total":"512000.00"}}""",
        )
        assertEquals(Ganancias("104000.00", "360000.00", "512000.00"), tecnico.ganancias)
    }
}
