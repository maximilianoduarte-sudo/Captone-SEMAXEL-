package cl.semaxel.tecnico

import android.app.Application

/** Clase Application: crea el [Contenedor] al abrir la app. */
class SemaxelApp : Application() {

    lateinit var contenedor: Contenedor
        private set

    override fun onCreate() {
        super.onCreate()
        contenedor = Contenedor(this)
    }
}
