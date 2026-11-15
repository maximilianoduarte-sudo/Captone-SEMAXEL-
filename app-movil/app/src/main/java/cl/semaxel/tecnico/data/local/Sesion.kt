package cl.semaxel.tecnico.data.local

import kotlinx.coroutines.flow.Flow

/**
 * Dónde se guarda el token de la sesión.
 *
 * En la app es [SesionStore] (DataStore del celular). En las pruebas de JVM se
 * usa una versión en memoria, para probar la capa de datos sin Android.
 */
interface Sesion {
    /** Token guardado; null si no hay sesión. Cambia al iniciar o cerrar sesión. */
    val token: Flow<String?>

    suspend fun tokenActual(): String?
    suspend fun guardar(token: String)
    suspend fun borrar()
}
