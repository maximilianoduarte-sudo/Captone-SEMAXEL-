package cl.semaxel.tecnico.ui.inicio

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import cl.semaxel.tecnico.data.Repositorio
import cl.semaxel.tecnico.data.Resultado
import cl.semaxel.tecnico.data.remote.Inicio
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** Estados posibles de una pantalla que carga datos de la API. */
sealed interface EstadoCarga<out T> {
    data object Cargando : EstadoCarga<Nothing>
    data class Listo<T>(val dato: T) : EstadoCarga<T>
    data class Error(val mensaje: String) : EstadoCarga<Nothing>
}

class InicioViewModel(private val repositorio: Repositorio) : ViewModel() {

    private val _estado = MutableStateFlow<EstadoCarga<Inicio>>(EstadoCarga.Cargando)
    val estado: StateFlow<EstadoCarga<Inicio>> = _estado.asStateFlow()

    init {
        cargar()
    }

    fun cargar() {
        _estado.value = EstadoCarga.Cargando
        viewModelScope.launch {
            _estado.value = when (val resultado = repositorio.inicio()) {
                is Resultado.Exito -> EstadoCarga.Listo(resultado.dato)
                is Resultado.Fallo -> EstadoCarga.Error(resultado.error.mensaje)
            }
        }
    }
}
