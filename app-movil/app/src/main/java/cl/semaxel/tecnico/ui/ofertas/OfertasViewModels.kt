package cl.semaxel.tecnico.ui.ofertas

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import cl.semaxel.tecnico.data.Repositorio
import cl.semaxel.tecnico.data.Resultado
import cl.semaxel.tecnico.data.remote.Oferta
import cl.semaxel.tecnico.ui.comun.EstadoPantalla
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Listado de ofertas que el técnico puede tomar (solo de sus especialidades). */
class OfertasViewModel(private val repositorio: Repositorio) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoPantalla<List<Oferta>>())
    val estado: StateFlow<EstadoPantalla<List<Oferta>>> = _estado.asStateFlow()

    init {
        cargar()
    }

    fun cargar() {
        _estado.update { it.copy(cargando = true, error = null) }
        viewModelScope.launch {
            when (val r = repositorio.ofertas()) {
                is Resultado.Exito -> _estado.update { it.copy(dato = r.dato, cargando = false) }
                is Resultado.Fallo -> _estado.update { it.copy(cargando = false, error = r.error.mensaje) }
            }
        }
    }
}

/**
 * Detalle de una oferta y acción de tomarla.
 *
 * Al tomarla con éxito, [ordenCreada] trae el id de la orden para que la
 * pantalla navegue a su detalle.
 */
class OfertaDetalleViewModel(private val repositorio: Repositorio, private val id: Int) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoPantalla<Oferta>())
    val estado: StateFlow<EstadoPantalla<Oferta>> = _estado.asStateFlow()

    private val _ordenCreada = MutableStateFlow<Int?>(null)
    val ordenCreada: StateFlow<Int?> = _ordenCreada.asStateFlow()

    init {
        cargar()
    }

    fun cargar() {
        _estado.update { it.copy(cargando = true) }
        viewModelScope.launch {
            when (val r = repositorio.oferta(id)) {
                is Resultado.Exito -> _estado.update { it.copy(dato = r.dato, cargando = false) }
                is Resultado.Fallo -> _estado.update { it.copy(cargando = false, error = r.error.mensaje) }
            }
        }
    }

    fun tomar() {
        if (_estado.value.procesando) return
        _estado.update { it.copy(procesando = true, error = null) }
        viewModelScope.launch {
            when (val r = repositorio.tomarOferta(id)) {
                is Resultado.Exito -> {
                    _estado.update { it.copy(dato = r.dato.oferta, procesando = false) }
                    _ordenCreada.value = r.dato.ordenId
                }
                // 409: otro técnico la tomó, venció, etc. Se muestra el motivo del servidor.
                is Resultado.Fallo -> _estado.update { it.copy(procesando = false, error = r.error.mensaje) }
            }
        }
    }

    /** La pantalla ya navegó a la orden: no volver a hacerlo. */
    fun navegacionHecha() {
        _ordenCreada.value = null
    }
}
