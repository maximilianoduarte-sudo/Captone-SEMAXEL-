package cl.semaxel.tecnico.data

import cl.semaxel.tecnico.data.remote.ErrorApi
import cl.semaxel.tecnico.data.remote.ErroresApi
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.SerializationException
import retrofit2.HttpException
import java.io.IOException

/** Resultado de una llamada a la API: o trae el dato, o trae un error ya explicado. */
sealed interface Resultado<out T> {
    data class Exito<T>(val dato: T) : Resultado<T>
    data class Fallo(val error: ErrorApi) : Resultado<Nothing>
}

/**
 * Ejecuta una llamada a la API y convierte cualquier falla en [Resultado.Fallo]:
 * - HttpException (el servidor respondió 4xx/5xx): se lee el cuerpo del error.
 * - IOException (sin señal, servidor apagado, tiempo agotado): mensaje de conexión.
 * - SerializationException (JSON inesperado): mensaje de formato.
 */
suspend fun <T> llamarApi(bloque: suspend () -> T): Resultado<T> =
    try {
        Resultado.Exito(bloque())
    } catch (e: CancellationException) {
        throw e // la pantalla se cerró: no es un error
    } catch (e: HttpException) {
        val cuerpo = e.response()?.errorBody()?.string()
        Resultado.Fallo(ErroresApi.desdeRespuesta(e.code(), cuerpo))
    } catch (e: IOException) {
        Resultado.Fallo(ErrorApi(ErroresApi.SIN_CONEXION))
    } catch (e: SerializationException) {
        // El servidor respondió algo que la app no sabe leer (versiones distintas).
        Resultado.Fallo(ErrorApi("La respuesta del servidor no tiene el formato esperado."))
    }
