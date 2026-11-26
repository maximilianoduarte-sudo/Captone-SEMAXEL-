package cl.semaxel.tecnico.ui.evidencias

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import cl.semaxel.tecnico.data.Repositorio
import cl.semaxel.tecnico.data.Resultado
import cl.semaxel.tecnico.data.remote.Orden
import cl.semaxel.tecnico.ui.comun.EstadoPantalla
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Estados en que la orden todavía admite fotos (antes del cierre). */
val ESTADOS_CON_EVIDENCIA = setOf("ASIGNADA", "EN_EJECUCION", "RESUELTA")

/** Fotos de una orden: ver, subir y eliminar. */
class EvidenciasOrdenViewModel(private val repositorio: Repositorio, private val id: Int) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoPantalla<Orden>())
    val estado: StateFlow<EstadoPantalla<Orden>> = _estado.asStateFlow()

    init {
        cargar()
    }

    fun cargar() {
        _estado.update { it.copy(cargando = true) }
        viewModelScope.launch {
            when (val r = repositorio.orden(id)) {
                is Resultado.Exito -> _estado.update { it.copy(dato = r.dato, cargando = false) }
                is Resultado.Fallo -> _estado.update { it.copy(cargando = false, error = r.error.mensaje) }
            }
        }
    }

    /** Sube una foto ya preparada (JPEG reducido) y recarga la orden. */
    fun subir(imagenJpeg: ByteArray, descripcion: String) {
        _estado.update { it.copy(procesando = true, error = null, aviso = null) }
        viewModelScope.launch {
            when (val r = repositorio.subirEvidencia(id, imagenJpeg, descripcion)) {
                is Resultado.Exito -> {
                    _estado.update { it.copy(procesando = false, aviso = "Foto subida.") }
                    cargar()
                }
                is Resultado.Fallo -> _estado.update { it.copy(procesando = false, error = r.error.mensaje) }
            }
        }
    }

    fun eliminar(evidenciaId: Int) {
        _estado.update { it.copy(procesando = true, error = null, aviso = null) }
        viewModelScope.launch {
            when (val r = repositorio.eliminarEvidencia(id, evidenciaId)) {
                is Resultado.Exito -> {
                    _estado.update { it.copy(procesando = false, aviso = "Foto eliminada.") }
                    cargar()
                }
                is Resultado.Fallo -> _estado.update { it.copy(procesando = false, error = r.error.mensaje) }
            }
        }
    }

    fun mostrarError(mensaje: String) = _estado.update { it.copy(error = mensaje, aviso = null) }
}

/** Firma de conformidad: el encargado firma en el celular del técnico. */
class FirmaViewModel(private val repositorio: Repositorio, private val id: Int) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoPantalla<Orden>(cargando = false))
    val estado: StateFlow<EstadoPantalla<Orden>> = _estado.asStateFlow()

    private val _guardada = MutableStateFlow(false)
    val guardada: StateFlow<Boolean> = _guardada.asStateFlow()

    fun guardar(firmaPng: ByteArray, nombreFirmante: String) {
        if (_estado.value.procesando) return
        _estado.update { it.copy(procesando = true, error = null) }
        viewModelScope.launch {
            when (val r = repositorio.registrarFirma(id, firmaPng, nombreFirmante)) {
                is Resultado.Exito -> {
                    _estado.update { it.copy(dato = r.dato, procesando = false) }
                    _guardada.value = true
                }
                is Resultado.Fallo -> _estado.update { it.copy(procesando = false, error = r.error.mensaje) }
            }
        }
    }

    fun mostrarError(mensaje: String) = _estado.update { it.copy(error = mensaje) }
}
