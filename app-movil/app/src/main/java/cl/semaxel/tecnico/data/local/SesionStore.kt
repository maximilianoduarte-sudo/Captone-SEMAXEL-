package cl.semaxel.tecnico.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.almacenSesion: DataStore<Preferences> by preferencesDataStore(name = "sesion")

/**
 * Guarda el token de la API en el celular (DataStore), para no pedir la
 * contraseña cada vez que se abre la app.
 *
 * [token] es un flujo: cuando el token cambia (inicio de sesión, cierre o
 * sesión expirada), la interfaz reacciona sola y muestra la pantalla que
 * corresponde.
 */
class SesionStore(private val context: Context) {

    private val claveToken = stringPreferencesKey("token")

    val token: Flow<String?> = context.almacenSesion.data.map { it[claveToken] }

    suspend fun tokenActual(): String? = token.first()

    suspend fun guardar(token: String) {
        context.almacenSesion.edit { it[claveToken] = token }
    }

    suspend fun borrar() {
        context.almacenSesion.edit { it.remove(claveToken) }
    }
}
