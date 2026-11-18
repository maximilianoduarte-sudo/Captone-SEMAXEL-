package cl.semaxel.tecnico.ui.inicio

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import cl.semaxel.tecnico.data.Repositorio
import cl.semaxel.tecnico.data.Resultado
import cl.semaxel.tecnico.data.remote.Inicio
import kotlinx.coroutines.Job
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

/**
 * Resumen de la pestaña Inicio. Se carga cada vez que la pestaña se muestra
 * (ver RecargarAlMostrarse), no al crearse.
 */
class InicioViewModel(private val repositorio: Repositorio) : ViewModel() {

    private val _estado = MutableStateFlow<EstadoCarga<Inicio>>(EstadoCarga.Cargando)
    val estado: StateFlow<EstadoCarga<Inicio>> = _estado.asStateFlow()

    fun cargar(): Job {
        // Si ya hay datos en pantalla se actualizan sin mostrar la rueda de
        // carga, para que la pantalla no parpadee cada vez que se abre.
        if (_estado.value !is EstadoCarga.Listo) _estado.value = EstadoCarga.Cargando
        return viewModelScope.launch {
            _estado.value = when (val resultado = repositorio.inicio()) {
                is Resultado.Exito -> EstadoCarga.Listo(resultado.dato)
                is Resultado.Fallo -> EstadoCarga.Error(resultado.error.mensaje)
            }
        }
    }
}
