package cl.semaxel.tecnico.ui.perfil

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import cl.semaxel.tecnico.data.Repositorio
import cl.semaxel.tecnico.data.Resultado
import cl.semaxel.tecnico.data.remote.Tecnico
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class EstadoPerfil(
    val tecnico: Tecnico? = null,
    val cargando: Boolean = true,
    val guardando: Boolean = false,
    val error: String? = null,
)

class PerfilViewModel(private val repositorio: Repositorio) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoPerfil())
    val estado: StateFlow<EstadoPerfil> = _estado.asStateFlow()

    init {
        cargar()
    }

    fun cargar() {
        _estado.update { it.copy(cargando = true, error = null) }
        viewModelScope.launch {
            when (val resultado = repositorio.perfil()) {
                is Resultado.Exito -> _estado.update { it.copy(tecnico = resultado.dato, cargando = false) }
                is Resultado.Fallo -> _estado.update { it.copy(cargando = false, error = resultado.error.mensaje) }
            }
        }
    }

    /** Disponible / No disponible. El servidor lo rechaza (409) si está ocupado. */
    fun cambiarDisponibilidad(disponible: Boolean) {
        _estado.update { it.copy(guardando = true, error = null) }
        viewModelScope.launch {
            when (val resultado = repositorio.cambiarDisponibilidad(disponible)) {
                is Resultado.Exito -> _estado.update { it.copy(tecnico = resultado.dato, guardando = false) }
                is Resultado.Fallo -> _estado.update { it.copy(guardando = false, error = resultado.error.mensaje) }
            }
        }
    }

    /** Cierra la sesión; la pantalla raíz vuelve sola al login. */
    fun cerrarSesion() {
        viewModelScope.launch { repositorio.cerrarSesion() }
    }
}
