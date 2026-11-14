package cl.semaxel.tecnico

import android.content.Context
import cl.semaxel.tecnico.data.Repositorio
import cl.semaxel.tecnico.data.RepositorioApi
import cl.semaxel.tecnico.data.local.SesionStore
import cl.semaxel.tecnico.data.remote.ClienteApi

/**
 * Crea una sola vez los objetos compartidos de la app (inyección de
 * dependencias manual, sin bibliotecas extra).
 */
class Contenedor(context: Context) {

    private val sesion = SesionStore(context.applicationContext)

    private val api = ClienteApi.crear(
        urlBase = BuildConfig.API_BASE_URL,
        sesion = sesion,
        depuracion = BuildConfig.DEBUG,
    )

    val repositorio: Repositorio = RepositorioApi(api, sesion)
}
