package cl.semaxel.tecnico.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import cl.semaxel.tecnico.data.Repositorio
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn

/** ¿Qué mostrar al abrir la app? Depende solo de si hay un token guardado. */
enum class EstadoSesion { CARGANDO, SIN_SESION, CON_SESION }

class RaizViewModel(repositorio: Repositorio) : ViewModel() {

    val estado: StateFlow<EstadoSesion> = repositorio.token
        .map { token -> if (token == null) EstadoSesion.SIN_SESION else EstadoSesion.CON_SESION }
        .stateIn(viewModelScope, SharingStarted.Eagerly, EstadoSesion.CARGANDO)
}
