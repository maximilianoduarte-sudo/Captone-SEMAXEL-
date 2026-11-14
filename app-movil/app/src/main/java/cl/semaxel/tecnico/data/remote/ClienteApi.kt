package cl.semaxel.tecnico.data.remote

import cl.semaxel.tecnico.data.local.SesionStore
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Response
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit

/** Crea el cliente Retrofit de la API de SEMAXEL. */
object ClienteApi {

    /**
     * - ignoreUnknownKeys: si el servidor agrega campos nuevos, la app no falla.
     * - explicitNulls = false: los campos opcionales en null no se envían
     *   (el servidor rechaza null en campos opcionales).
     */
    val json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
    }

    fun crear(urlBase: String, sesion: SesionStore, depuracion: Boolean): SemaxelApi {
        val registro = HttpLoggingInterceptor().apply {
            // En depuración se ven las peticiones en Logcat, sin el token.
            level = if (depuracion) HttpLoggingInterceptor.Level.BASIC else HttpLoggingInterceptor.Level.NONE
            redactHeader("Authorization")
        }
        val cliente = OkHttpClient.Builder()
            .addInterceptor(InterceptorToken(sesion))
            .addInterceptor(registro)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS) // subir fotos puede tardar
            .build()
        return Retrofit.Builder()
            .baseUrl(urlBase)
            .client(cliente)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(SemaxelApi::class.java)
    }
}

/**
 * Agrega el token a cada petición y cierra la sesión si el servidor responde 401.
 *
 * OkHttp ejecuta los interceptores en sus propios hilos (no en el hilo de la
 * interfaz), por eso aquí se puede leer el almacén con runBlocking.
 */
private class InterceptorToken(private val sesion: SesionStore) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val token = runBlocking { sesion.tokenActual() }
        val peticion = chain.request().newBuilder().apply {
            if (token != null) header("Authorization", "Token $token")
        }.build()

        val respuesta = chain.proceed(peticion)
        val esLogout = peticion.url.encodedPath.endsWith("/auth/logout/")
        if (respuesta.code == 401 && token != null && !esLogout) {
            // Token vencido o borrado en el servidor: se olvida y la app vuelve al login.
            runBlocking { sesion.borrar() }
        }
        return respuesta
    }
}
