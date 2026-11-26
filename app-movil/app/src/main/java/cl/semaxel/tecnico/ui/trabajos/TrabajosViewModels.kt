package cl.semaxel.tecnico.ui.trabajos

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import cl.semaxel.tecnico.data.Repositorio
import cl.semaxel.tecnico.data.Resultado
import cl.semaxel.tecnico.data.remote.Orden
import cl.semaxel.tecnico.ui.comun.Formato
import java.math.BigDecimal
import java.time.YearMonth
import cl.semaxel.tecnico.ui.comun.EstadoPantalla
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Estados en que la orden sigue en manos del técnico. */
val ESTADOS_ACTIVOS = setOf("ASIGNADA", "EN_EJECUCION")

/** Estados en que el trabajo está hecho y cuenta como dinero generado. */
val ESTADOS_TERMINADOS = setOf("RESUELTA", "CERRADA")

/** Un mes del historial: "Noviembre 2026", sus órdenes y lo generado (costo final de las terminadas). */
data class MesHistorial(val titulo: String, val ordenes: List<Orden>, val total: BigDecimal)

/**
 * Agrupa las órdenes por mes (hora de Chile), del mes más reciente al más
 * antiguo. Cada orden cuenta en el mes en que terminó (fecha_fin) o, si no
 * terminó (cancelada), en el que se asignó. Las que no tienen fecha legible
 * quedan al final, en "Sin fecha".
 */
fun historialPorMes(ordenes: List<Orden>): List<MesHistorial> {
    fun fecha(orden: Orden) = Formato.instante(orden.fechaFin ?: orden.fechaAsignacion)
    val (conFecha, sinFecha) = ordenes.partition { fecha(it) != null }
    val meses = conFecha
        .sortedByDescending { fecha(it) }
        .groupBy { YearMonth.from(fecha(it)!!) }
        .map { (mes, lista) -> MesHistorial(Formato.nombreMes(mes), lista, totalGenerado(lista)) }
    return if (sinFecha.isEmpty()) meses else meses + MesHistorial("Sin fecha", sinFecha, totalGenerado(sinFecha))
}

private fun totalGenerado(ordenes: List<Orden>): BigDecimal =
    ordenes.filter { it.estado in ESTADOS_TERMINADOS }
        .mapNotNull { it.costoFinal?.toBigDecimalOrNull() }
        .fold(BigDecimal.ZERO, BigDecimal::add)

/**
 * Listado de órdenes del técnico (Mis trabajos y Evidencias).
 * Se carga cada vez que la pestaña se muestra (ver RecargarAlMostrarse).
 */
class TrabajosViewModel(private val repositorio: Repositorio) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoPantalla<List<Orden>>())
    val estado: StateFlow<EstadoPantalla<List<Orden>>> = _estado.asStateFlow()

    fun cargar(): Job {
        _estado.update { it.copy(cargando = true, error = null) }
        return viewModelScope.launch {
            when (val r = repositorio.ordenes()) {
                is Resultado.Exito -> _estado.update { it.copy(dato = r.dato, cargando = false) }
                is Resultado.Fallo -> _estado.update { it.copy(cargando = false, error = r.error.mensaje) }
            }
        }
    }
}

/**
 * Detalle de una orden y sus acciones: registrar llegada, iniciar y resolver.
 *
 * Qué botones mostrar lo decide el servidor (campo `acciones` de la orden),
 * así la app no repite la máquina de estados.
 */
class TrabajoDetalleViewModel(private val repositorio: Repositorio, private val id: Int) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoPantalla<Orden>())
    val estado: StateFlow<EstadoPantalla<Orden>> = _estado.asStateFlow()

    init {
        cargar()
    }

    fun cargar(): Job {
        _estado.update { it.copy(cargando = true) }
        return viewModelScope.launch {
            when (val r = repositorio.orden(id)) {
                is Resultado.Exito -> _estado.update { it.copy(dato = r.dato, cargando = false) }
                is Resultado.Fallo -> _estado.update { it.copy(cargando = false, error = r.error.mensaje) }
            }
        }
    }

    fun registrarLlegada(latitud: Double, longitud: Double, precisionM: Float?) =
        ejecutar("Llegada registrada.") { repositorio.registrarLlegada(id, latitud, longitud, precisionM) }

    fun iniciar(diagnostico: String, costoEstimado: String) =
        ejecutar("Trabajo iniciado.") { repositorio.iniciar(id, diagnostico, costoEstimado) }

    fun resolver(trabajoRealizado: String, observaciones: String, costoFinal: String) =
        ejecutar("Trabajo marcado como resuelto. El encargado lo cerrará en la web.") {
            repositorio.resolver(id, trabajoRealizado, observaciones, costoFinal)
        }

    /** Errores que ocurren en el celular (por ejemplo, GPS apagado). */
    fun mostrarError(mensaje: String) = _estado.update { it.copy(error = mensaje, aviso = null) }

    private fun ejecutar(avisoExito: String, accion: suspend () -> Resultado<Orden>) {
        if (_estado.value.procesando) return
        _estado.update { it.copy(procesando = true, error = null, aviso = null) }
        viewModelScope.launch {
            when (val r = accion()) {
                is Resultado.Exito -> _estado.update { it.copy(dato = r.dato, procesando = false, aviso = avisoExito) }
                is Resultado.Fallo -> _estado.update { it.copy(procesando = false, error = r.error.mensaje) }
            }
        }
    }
}
