package cl.semaxel.tecnico.ui.comun

import androidx.compose.ui.graphics.Color
import cl.semaxel.tecnico.data.remote.Horario
import cl.semaxel.tecnico.data.remote.Sucursal
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter

/** Utilidades de formato para mostrar datos de la API. */
object Formato {

    private val fechaHora = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm")
    private val zonaChile = ZoneId.of("America/Santiago")

    /** "2026-11-13T15:42:10-03:00" -> "13/11/2026 15:42" (hora de Chile). Null -> "—". */
    fun fecha(iso: String?): String {
        if (iso.isNullOrBlank()) return "—"
        return try {
            OffsetDateTime.parse(iso).atZoneSameInstant(zonaChile).format(fechaHora)
        } catch (e: Exception) {
            iso
        }
    }

    /** "25000.00" -> "$25.000". Null -> "—". */
    fun pesos(monto: String?): String {
        val valor = monto?.toBigDecimalOrNull() ?: return "—"
        val entero = valor.setScale(0, java.math.RoundingMode.HALF_UP).toPlainString()
        return "$" + entero.reversed().chunked(3).joinToString(".").reversed()
    }

    fun direccion(sucursal: Sucursal): String =
        listOf(sucursal.direccion, sucursal.comuna, sucursal.ciudad)
            .filter { it.isNotBlank() }
            .joinToString(", ")

    /** Horario por día; los días sin registro están cerrados. */
    fun horario(horarios: List<Horario>): List<String> {
        if (horarios.isEmpty()) return listOf("Horario no informado")
        val dias = listOf("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
        return dias.mapIndexed { indice, dia ->
            val h = horarios.firstOrNull { it.diaSemana == indice }
            if (h == null) "$dia: cerrado" else "$dia: ${h.apertura} a ${h.cierre}"
        }
    }

    /** Color según prioridad del ticket. */
    fun colorPrioridad(prioridad: String): Color = when (prioridad) {
        "CRITICA" -> Color(0xFFC62828)
        "ALTA" -> Color(0xFFE65100)
        "MEDIA" -> Color(0xFF4F81BD)
        else -> Color(0xFF607D8B)
    }
}
