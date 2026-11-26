package cl.semaxel.tecnico.data.remote

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Comprueba que la app entiende el JSON tal como lo envía la API (ejemplos de la Guía). */
class ModelosJsonTest {

    private val json = ClienteApi.json

    @Test
    fun `lee una orden completa con llegada, evidencias y acciones`() {
        val orden = json.decodeFromString(
            Orden.serializer(),
            """
            {
              "id": 6, "estado": "EN_EJECUCION", "estado_display": "En ejecución",
              "titulo": "Reparación de tablero eléctrico", "descripcion": "Se apaga solo.",
              "prioridad": "ALTA", "prioridad_display": "Alta", "categoria": "Eléctrica",
              "empresa": "Cadena Demo",
              "sucursal": {
                "nombre": "Providencia", "direccion": "Av. Providencia 1200", "comuna": "Providencia",
                "ciudad": "Santiago", "region": "Metropolitana", "telefono": "+56 2 2345 1000",
                "latitud": "-33.429500", "longitud": "-70.617700",
                "horario": [{"dia_semana": 0, "dia": "Lunes", "apertura": "09:00", "cierre": "20:00"}]
              },
              "diagnostico": "Falla revisada", "trabajo_realizado": "", "observaciones": "",
              "costo_estimado": null, "costo_final": null,
              "fecha_asignacion": "2026-11-13T15:40:02-03:00",
              "fecha_inicio": "2026-11-13T15:45:10-03:00", "fecha_fin": null,
              "llegada": {"fecha": "2026-11-13T15:42:10-03:00", "latitud": "-33.429500",
                          "longitud": "-70.617700", "precision_m": 12.0, "distancia_m": 0,
                          "verificada": true},
              "tiempo_respuesta_minutos": 32, "sla_respuesta_minutos": 60, "sla_respuesta_cumplido": true,
              "evidencias": [{"id": 1, "url": "http://servidor/media/foto.png", "descripcion": "Antes",
                              "fecha_subida": "2026-11-13T15:50:00-03:00"}],
              "firma": null,
              "acciones": ["resolver", "subir_evidencia", "firmar"],
              "campo_nuevo_del_servidor": "se ignora"
            }
            """.trimIndent(),
        )
        assertEquals(6, orden.id)
        assertEquals("-33.429500", orden.sucursal.latitud)
        assertEquals("Lunes", orden.sucursal.horario.single().dia)
        assertEquals(true, orden.llegada?.verificada)
        assertEquals(1, orden.evidencias.size)
        assertNull(orden.firma)
        assertNull(orden.costoEstimado)
        assertEquals(listOf("resolver", "subir_evidencia", "firmar"), orden.acciones)
    }

    @Test
    fun `no envia los campos opcionales en null`() {
        // El servidor rechaza null en campos opcionales: deben omitirse.
        assertEquals("{}", json.encodeToString(LogoutPeticion.serializer(), LogoutPeticion()))
        assertEquals(
            """{"diagnostico":"x"}""",
            json.encodeToString(IniciarPeticion.serializer(), IniciarPeticion("x")),
        )
    }

    @Test
    fun `disponibilidad solo se puede cambiar si no esta ocupado`() {
        fun tecnico(estado: String) = Tecnico(id = 1, username = "u", nombre = "N", estado = estado)
        assertTrue(tecnico("DISPONIBLE").puedeCambiarDisponibilidad)
        assertTrue(tecnico("NO_DISPONIBLE").puedeCambiarDisponibilidad)
        assertFalse(tecnico("OCUPADO").puedeCambiarDisponibilidad)
        assertFalse(tecnico("INACTIVO").puedeCambiarDisponibilidad)
    }
}
