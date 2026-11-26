package cl.semaxel.tecnico.data

import cl.semaxel.tecnico.data.local.Sesion
import cl.semaxel.tecnico.data.remote.DisponibilidadPeticion
import cl.semaxel.tecnico.data.remote.Evidencia
import cl.semaxel.tecnico.data.remote.IniciarPeticion
import cl.semaxel.tecnico.data.remote.Inicio
import cl.semaxel.tecnico.data.remote.LlegadaPeticion
import cl.semaxel.tecnico.data.remote.LoginPeticion
import cl.semaxel.tecnico.data.remote.LogoutPeticion
import cl.semaxel.tecnico.data.remote.Oferta
import cl.semaxel.tecnico.data.remote.Orden
import cl.semaxel.tecnico.data.remote.ResolverPeticion
import cl.semaxel.tecnico.data.remote.SemaxelApi
import cl.semaxel.tecnico.data.remote.Tecnico
import cl.semaxel.tecnico.data.remote.TomarOfertaRespuesta
import kotlinx.coroutines.flow.Flow
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.Locale

/**
 * Punto único de acceso a los datos para las pantallas.
 *
 * Las pantallas no conocen Retrofit ni el almacén del token: piden datos aquí
 * y reciben un [Resultado]. Así se pueden probar con un repositorio falso.
 */
interface Repositorio {
    /** Token guardado; null si no hay sesión. */
    val token: Flow<String?>

    // Sesión y perfil
    suspend fun iniciarSesion(usuario: String, clave: String): Resultado<Tecnico>
    suspend fun cerrarSesion()
    suspend fun perfil(): Resultado<Tecnico>
    suspend fun cambiarDisponibilidad(disponible: Boolean): Resultado<Tecnico>
    suspend fun inicio(): Resultado<Inicio>

    // Ofertas
    suspend fun ofertas(): Resultado<List<Oferta>>
    suspend fun oferta(id: Int): Resultado<Oferta>
    suspend fun tomarOferta(id: Int): Resultado<TomarOfertaRespuesta>

    // Mis trabajos
    suspend fun ordenes(): Resultado<List<Orden>>
    suspend fun orden(id: Int): Resultado<Orden>
    suspend fun iniciar(id: Int, diagnostico: String, costoEstimado: String?): Resultado<Orden>
    suspend fun resolver(id: Int, trabajoRealizado: String, observaciones: String?, costoFinal: String?): Resultado<Orden>
    suspend fun registrarLlegada(id: Int, latitud: Double, longitud: Double, precisionM: Float?): Resultado<Orden>

    // Evidencias y firma
    suspend fun subirEvidencia(id: Int, imagenJpeg: ByteArray, descripcion: String): Resultado<Evidencia>
    suspend fun eliminarEvidencia(id: Int, evidenciaId: Int): Resultado<Unit>
    suspend fun registrarFirma(id: Int, firmaPng: ByteArray, nombreFirmante: String): Resultado<Orden>
}

class RepositorioApi(
    private val api: SemaxelApi,
    private val sesion: Sesion,
) : Repositorio {

    override val token: Flow<String?> = sesion.token

    // ------------------------------------------------------------ sesión y perfil

    override suspend fun iniciarSesion(usuario: String, clave: String): Resultado<Tecnico> {
        val resultado = llamarApi { api.login(LoginPeticion(usuario.trim(), clave)) }
        return when (resultado) {
            is Resultado.Exito -> {
                sesion.guardar(resultado.dato.token)
                Resultado.Exito(resultado.dato.tecnico)
            }
            is Resultado.Fallo -> resultado
        }
    }

    override suspend fun cerrarSesion() {
        // Se avisa al servidor para invalidar el token, pero aunque no haya
        // señal la sesión se cierra igual en el celular.
        llamarApi { api.logout(LogoutPeticion()) }
        sesion.borrar()
    }

    override suspend fun perfil(): Resultado<Tecnico> = llamarApi { api.perfil() }

    override suspend fun cambiarDisponibilidad(disponible: Boolean): Resultado<Tecnico> {
        val estado = if (disponible) Tecnico.ESTADO_DISPONIBLE else Tecnico.ESTADO_NO_DISPONIBLE
        return llamarApi { api.cambiarDisponibilidad(DisponibilidadPeticion(estado)) }
    }

    override suspend fun inicio(): Resultado<Inicio> = llamarApi { api.inicio() }

    // ------------------------------------------------------------ ofertas

    override suspend fun ofertas(): Resultado<List<Oferta>> = llamarApi { api.ofertas() }

    override suspend fun oferta(id: Int): Resultado<Oferta> = llamarApi { api.oferta(id) }

    override suspend fun tomarOferta(id: Int): Resultado<TomarOfertaRespuesta> =
        llamarApi { api.tomarOferta(id) }

    // ------------------------------------------------------------ mis trabajos

    override suspend fun ordenes(): Resultado<List<Orden>> = llamarApi { api.ordenes() }

    override suspend fun orden(id: Int): Resultado<Orden> = llamarApi { api.orden(id) }

    override suspend fun iniciar(id: Int, diagnostico: String, costoEstimado: String?): Resultado<Orden> =
        llamarApi {
            api.iniciar(id, IniciarPeticion(diagnostico.trim(), costoEstimado?.trim()?.ifBlank { null }))
        }

    override suspend fun resolver(
        id: Int,
        trabajoRealizado: String,
        observaciones: String?,
        costoFinal: String?,
    ): Resultado<Orden> = llamarApi {
        api.resolver(
            id,
            ResolverPeticion(
                trabajoRealizado = trabajoRealizado.trim(),
                observaciones = observaciones?.trim()?.ifBlank { null },
                costoFinal = costoFinal?.trim()?.ifBlank { null },
            ),
        )
    }

    override suspend fun registrarLlegada(
        id: Int,
        latitud: Double,
        longitud: Double,
        precisionM: Float?,
    ): Resultado<Orden> = llamarApi {
        api.registrarLlegada(
            id,
            LlegadaPeticion(
                latitud = coordenada(latitud),
                longitud = coordenada(longitud),
                precisionM = precisionM?.toDouble(),
            ),
        )
    }

    // ------------------------------------------------------------ evidencias y firma

    override suspend fun subirEvidencia(id: Int, imagenJpeg: ByteArray, descripcion: String): Resultado<Evidencia> =
        llamarApi {
            api.subirEvidencia(
                id,
                parteImagen("foto.jpg", imagenJpeg, "image/jpeg"),
                descripcion.trim().toRequestBody(TEXTO),
            )
        }

    override suspend fun eliminarEvidencia(id: Int, evidenciaId: Int): Resultado<Unit> =
        llamarApiSinCuerpo { api.eliminarEvidencia(id, evidenciaId) }

    override suspend fun registrarFirma(id: Int, firmaPng: ByteArray, nombreFirmante: String): Resultado<Orden> =
        llamarApi {
            api.registrarFirma(
                id,
                parteImagen("firma.png", firmaPng, "image/png"),
                nombreFirmante.trim().toRequestBody(TEXTO),
            )
        }

    private companion object {
        val TEXTO = "text/plain; charset=utf-8".toMediaType()

        /** Seis decimales con punto (no coma), como espera el servidor. */
        fun coordenada(valor: Double): String = String.format(Locale.ROOT, "%.6f", valor)

        fun parteImagen(nombre: String, bytes: ByteArray, tipo: String): MultipartBody.Part =
            MultipartBody.Part.createFormData("imagen", nombre, bytes.toRequestBody(tipo.toMediaType()))
    }
}
