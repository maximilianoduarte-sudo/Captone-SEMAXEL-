package cl.semaxel.tecnico.data

import cl.semaxel.tecnico.data.local.Sesion
import cl.semaxel.tecnico.data.remote.ClienteApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.util.Base64

/**
 * Prueba de contrato: usa la capa de datos REAL de la app (Retrofit, modelos
 * JSON y RepositorioApi) contra un servidor SEMAXEL de verdad, y recorre el
 * flujo completo de un trabajo.
 *
 * Comprueba que la app entiende exactamente lo que responde la API. Solo corre
 * si se indica el servidor (con los datos de `seed_demo` recién cargados):
 *
 *   ./gradlew testDebugUnitTest -Psemaxel.apiContrato=http://127.0.0.1:8000/ \
 *       -Psemaxel.usuarioContrato=cdiaz -Psemaxel.claveContrato=<clave de seed_demo>
 *
 * Sin esas propiedades la prueba se omite (no falla).
 */
class ContratoApiTest {

    private val url = System.getProperty("semaxel.apiContrato").orEmpty()
    private val usuario = System.getProperty("semaxel.usuarioContrato").orEmpty()
    private val clave = System.getProperty("semaxel.claveContrato").orEmpty()

    /** Token en memoria (en la app real se guarda con DataStore). */
    private class SesionEnMemoria : Sesion {
        private val actual = MutableStateFlow<String?>(null)
        override val token: StateFlow<String?> = actual
        override suspend fun tokenActual() = actual.value
        override suspend fun guardar(token: String) { actual.value = token }
        override suspend fun borrar() { actual.value = null }
    }

    private fun <T> exito(resultado: Resultado<T>): T = when (resultado) {
        is Resultado.Exito -> resultado.dato
        is Resultado.Fallo -> throw AssertionError("Se esperaba éxito y el servidor respondió: ${resultado.error}")
    }

    /** Imágenes reales de 8x8 px (generadas con Pillow): las clases gráficas de Java no existen en Android. */
    private val fotoJpeg: ByteArray = Base64.getDecoder().decode(
        "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAIAAgDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDgKKKK+eP2E//Z",
    )
    private val firmaPng: ByteArray = Base64.getDecoder().decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAFUlEQVR4nGP8//8/AzbAhFV00EoAAFbUAw037MyjAAAAAElFTkSuQmCC",
    )

    @Test
    fun `flujo completo de un trabajo contra el servidor`() = runBlocking {
        assumeTrue("Prueba de contrato omitida: falta -Psemaxel.apiContrato", url.isNotBlank() && clave.isNotBlank())

        val sesion = SesionEnMemoria()
        val repo = RepositorioApi(ClienteApi.crear(url, sesion, depuracion = false), sesion)

        // 1. Inicio de sesión: el token queda guardado.
        val tecnico = exito(repo.iniciarSesion(usuario, clave))
        assertEquals(usuario, tecnico.username)
        assertNotNull(sesion.tokenActual())

        // 2. Inicio y ofertas.
        exito(repo.inicio())
        val ofertas = exito(repo.ofertas())
        val oferta = ofertas.firstOrNull { it.sucursal.latitud != null } ?: ofertas.firstOrNull()
            ?: throw AssertionError("El técnico de prueba no tiene ofertas: recargar seed_demo")
        assertEquals(oferta.id, exito(repo.oferta(oferta.id)).id)

        // 3. Tomar la oferta; tomarla otra vez debe dar 409 "no_disponible".
        val ordenId = exito(repo.tomarOferta(oferta.id)).ordenId
        val repetida = repo.tomarOferta(oferta.id)
        assertTrue(repetida is Resultado.Fallo && repetida.error.codigo == "no_disponible")

        // 4. Llegada con GPS en las coordenadas del local.
        val lat = oferta.sucursal.latitud?.toDouble() ?: -33.4
        val lon = oferta.sucursal.longitud?.toDouble() ?: -70.6
        val conLlegada = exito(repo.registrarLlegada(ordenId, lat, lon, 10f))
        assertNotNull(conLlegada.llegada)
        if (oferta.sucursal.latitud != null) assertEquals(true, conLlegada.llegada?.verificada)
        assertNotNull(conLlegada.tiempoRespuestaMinutos)

        // 5. Iniciar.
        val iniciada = exito(repo.iniciar(ordenId, "Diagnóstico de la prueba de contrato", "12000"))
        assertEquals("EN_EJECUCION", iniciada.estado)
        assertEquals("12000.00", iniciada.costoEstimado)

        // 6. Fotos: subir, eliminar y volver a subir.
        val foto = exito(repo.subirEvidencia(ordenId, fotoJpeg, "Antes"))
        assertTrue(foto.url.startsWith("http"))
        exito(repo.eliminarEvidencia(ordenId, foto.id))
        exito(repo.subirEvidencia(ordenId, fotoJpeg, "Después"))
        assertEquals(1, exito(repo.orden(ordenId)).evidencias.size)

        // 7. Firma de conformidad.
        val firmada = exito(repo.registrarFirma(ordenId, firmaPng, "Encargado de prueba"))
        assertEquals("Encargado de prueba", firmada.firma?.nombreFirmante)
        assertTrue("firmar" !in firmada.acciones)

        // 8. Resolver.
        val resuelta = exito(repo.resolver(ordenId, "Trabajo de la prueba de contrato", "", "25000"))
        assertEquals("RESUELTA", resuelta.estado)
        assertTrue(exito(repo.ordenes()).any { it.id == ordenId })

        // 9. Cerrar sesión: el token se borra y el servidor ya no lo acepta.
        repo.cerrarSesion()
        assertNull(sesion.tokenActual())
        val sinSesion = repo.perfil()
        assertTrue(sinSesion is Resultado.Fallo && sinSesion.error.http == 401)
    }
}
