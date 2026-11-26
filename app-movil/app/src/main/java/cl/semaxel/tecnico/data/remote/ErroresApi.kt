package cl.semaxel.tecnico.data.remote

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonObject

/**
 * Error que devolvió el servidor, ya traducido a un mensaje para mostrar.
 *
 * @property http código HTTP (401, 404, 409...); 0 si no hubo respuesta.
 * @property codigo código de regla de negocio del 409 (por ejemplo "no_disponible").
 */
data class ErrorApi(
    val mensaje: String,
    val http: Int = 0,
    val codigo: String? = null,
)

/**
 * Convierte el cuerpo de una respuesta de error de la API en un [ErrorApi].
 *
 * Formatos que manda el servidor (ver la Guía de la API, sección 2):
 * - 401, 403, 404 y 409: `{"detail": "...", "codigo": "..."}`.
 * - 400: un mensaje por campo, `{"diagnostico": ["Este campo es requerido."]}`.
 *
 * Es una función pura (sin Android ni red) para poder probarla con JUnit.
 */
object ErroresApi {

    const val SIN_CONEXION = "No se pudo conectar con el servidor. Revisa tu conexión."
    private const val GENERICO = "Ocurrió un error inesperado. Inténtalo de nuevo."

    private val json = Json { ignoreUnknownKeys = true }

    fun desdeRespuesta(http: Int, cuerpo: String?): ErrorApi {
        val objeto = try {
            cuerpo?.takeIf { it.isNotBlank() }?.let { json.parseToJsonElement(it).jsonObject }
        } catch (e: Exception) {
            null
        } ?: return ErrorApi(mensajePorDefecto(http), http)

        val detalle = (objeto["detail"] as? JsonPrimitive)?.content
        val codigo = (objeto["codigo"] as? JsonPrimitive)?.content
        if (detalle != null) return ErrorApi(detalle, http, codigo)

        val mensajesDeCampos = mensajesDeCampos(objeto)
        return if (mensajesDeCampos.isNotEmpty()) {
            ErrorApi(mensajesDeCampos.joinToString("\n"), http)
        } else {
            ErrorApi(mensajePorDefecto(http), http)
        }
    }

    private fun mensajesDeCampos(objeto: JsonObject): List<String> =
        objeto.values.flatMap { valor ->
            when (valor) {
                is JsonArray -> valor.mapNotNull { (it as? JsonPrimitive)?.content }
                is JsonPrimitive -> listOf(valor.content)
                else -> emptyList()
            }
        }

    private fun mensajePorDefecto(http: Int): String = when (http) {
        401 -> "Tu sesión expiró. Vuelve a iniciar sesión."
        403 -> "Esta app es solo para técnicos habilitados."
        404 -> "No se encontró lo que buscabas."
        in 500..599 -> "El servidor tuvo un problema. Inténtalo más tarde."
        else -> GENERICO
    }
}
