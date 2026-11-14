package cl.semaxel.tecnico.data.remote

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ErroresApiTest {

    @Test
    fun `409 trae mensaje y codigo de la regla de negocio`() {
        val error = ErroresApi.desdeRespuesta(
            409,
            """{"detail": "Esta oferta ya no está disponible.", "codigo": "no_disponible"}""",
        )
        assertEquals("Esta oferta ya no está disponible.", error.mensaje)
        assertEquals("no_disponible", error.codigo)
        assertEquals(409, error.http)
    }

    @Test
    fun `400 junta los mensajes de cada campo`() {
        val error = ErroresApi.desdeRespuesta(
            400,
            """{"diagnostico": ["Este campo es requerido."], "costo_estimado": ["Debe ser mayor o igual a 0."]}""",
        )
        assertEquals("Este campo es requerido.\nDebe ser mayor o igual a 0.", error.mensaje)
        assertNull(error.codigo)
    }

    @Test
    fun `login incorrecto usa el detail del servidor`() {
        val error = ErroresApi.desdeRespuesta(400, """{"detail": "Usuario o contraseña incorrectos."}""")
        assertEquals("Usuario o contraseña incorrectos.", error.mensaje)
    }

    @Test
    fun `cuerpo vacio o que no es JSON usa un mensaje por defecto`() {
        assertEquals("Tu sesión expiró. Vuelve a iniciar sesión.", ErroresApi.desdeRespuesta(401, null).mensaje)
        assertEquals(
            "El servidor tuvo un problema. Inténtalo más tarde.",
            ErroresApi.desdeRespuesta(500, "<html>Server Error</html>").mensaje,
        )
    }
}
