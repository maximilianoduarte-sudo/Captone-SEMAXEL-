package cl.semaxel.tecnico.data

import cl.semaxel.tecnico.data.local.SesionStore
import cl.semaxel.tecnico.data.remote.DisponibilidadPeticion
import cl.semaxel.tecnico.data.remote.Inicio
import cl.semaxel.tecnico.data.remote.LoginPeticion
import cl.semaxel.tecnico.data.remote.LogoutPeticion
import cl.semaxel.tecnico.data.remote.SemaxelApi
import cl.semaxel.tecnico.data.remote.Tecnico
import kotlinx.coroutines.flow.Flow

/**
 * Punto único de acceso a los datos para las pantallas.
 *
 * Las pantallas no conocen Retrofit ni el almacén del token: piden datos aquí
 * y reciben un [Resultado]. Así se pueden probar con un repositorio falso.
 */
interface Repositorio {
    /** Token guardado; null si no hay sesión. */
    val token: Flow<String?>

    suspend fun iniciarSesion(usuario: String, clave: String): Resultado<Tecnico>
    suspend fun cerrarSesion()
    suspend fun perfil(): Resultado<Tecnico>
    suspend fun cambiarDisponibilidad(disponible: Boolean): Resultado<Tecnico>
    suspend fun inicio(): Resultado<Inicio>
}

class RepositorioApi(
    private val api: SemaxelApi,
    private val sesion: SesionStore,
) : Repositorio {

    override val token: Flow<String?> = sesion.token

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
}
