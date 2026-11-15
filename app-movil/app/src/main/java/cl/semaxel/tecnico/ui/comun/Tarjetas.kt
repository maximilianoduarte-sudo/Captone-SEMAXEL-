package cl.semaxel.tecnico.ui.comun

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import cl.semaxel.tecnico.data.remote.Oferta
import cl.semaxel.tecnico.data.remote.Orden
import cl.semaxel.tecnico.ui.tema.VerdeOk

/** Etiqueta de color con la prioridad del ticket. */
@Composable
fun EtiquetaPrioridad(prioridad: String, texto: String) {
    Etiqueta(texto.ifBlank { prioridad }, Formato.colorPrioridad(prioridad))
}

@Composable
fun Etiqueta(texto: String, color: Color) {
    Surface(color = color.copy(alpha = 0.12f), shape = RoundedCornerShape(6.dp)) {
        Text(
            texto,
            color = color,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.SemiBold,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
        )
    }
}

/** Fila "etiqueta: valor" para las fichas de detalle. */
@Composable
fun Dato(etiqueta: String, valor: String, modifier: Modifier = Modifier) {
    Column(modifier) {
        Text(etiqueta, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(valor, style = MaterialTheme.typography.bodyLarge)
    }
}

/** Mensaje destacado: error (rojo) o aviso de éxito (verde). */
@Composable
fun Mensaje(texto: String, esError: Boolean, modifier: Modifier = Modifier) {
    val color = if (esError) MaterialTheme.colorScheme.error else VerdeOk
    Surface(
        modifier.fillMaxWidth(),
        color = color.copy(alpha = 0.1f),
        shape = RoundedCornerShape(8.dp),
    ) {
        Text(texto, color = color, modifier = Modifier.padding(12.dp))
    }
}

/** Tarjeta de una oferta en el listado. */
@Composable
fun TarjetaOferta(oferta: Oferta, alTocar: () -> Unit) {
    Card(onClick = alTocar, modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(oferta.titulo, style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(1f))
                EtiquetaPrioridad(oferta.prioridad, oferta.prioridadDisplay)
            }
            Text(
                "${oferta.sucursal.nombre} · ${Formato.direccion(oferta.sucursal)}",
                style = MaterialTheme.typography.bodySmall,
            )
            Text(
                "${oferta.especialidad ?: oferta.categoria} · Publicada ${Formato.fecha(oferta.fechaPublicacion)}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

/** Tarjeta de una orden de trabajo en los listados. */
@Composable
fun TarjetaOrden(orden: Orden, alTocar: (() -> Unit)? = null, pie: String? = null) {
    val contenido: @Composable () -> Unit = {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(orden.titulo, style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(1f))
                EtiquetaPrioridad(orden.prioridad, orden.prioridadDisplay)
            }
            Text(
                "${orden.sucursal.nombre} · ${Formato.direccion(orden.sucursal)}",
                style = MaterialTheme.typography.bodySmall,
            )
            Text(
                orden.estadoDisplay.ifBlank { orden.estado },
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.SemiBold,
            )
            pie?.let {
                Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
    if (alTocar != null) {
        Card(onClick = alTocar, modifier = Modifier.fillMaxWidth()) { contenido() }
    } else {
        Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors()) { contenido() }
    }
}
