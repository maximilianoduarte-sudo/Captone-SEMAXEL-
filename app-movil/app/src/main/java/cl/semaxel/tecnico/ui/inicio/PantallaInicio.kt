package cl.semaxel.tecnico.ui.inicio

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import cl.semaxel.tecnico.data.remote.Inicio
import cl.semaxel.tecnico.data.remote.Orden
import cl.semaxel.tecnico.ui.comun.Cargando
import cl.semaxel.tecnico.ui.comun.MensajeError
import cl.semaxel.tecnico.ui.viewModelConRepositorio

@Composable
fun PantallaInicio() {
    val vm = viewModelConRepositorio { InicioViewModel(it) }
    val estado by vm.estado.collectAsStateWithLifecycle()

    when (val e = estado) {
        EstadoCarga.Cargando -> Cargando()
        is EstadoCarga.Error -> MensajeError(e.mensaje, alReintentar = vm::cargar)
        is EstadoCarga.Listo -> ContenidoInicio(e.dato, alActualizar = vm::cargar)
    }
}

@Composable
private fun ContenidoInicio(inicio: Inicio, alActualizar: () -> Unit) {
    LazyColumn(
        Modifier.fillMaxSize().padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Row(
                Modifier.fillMaxWidth().padding(top = 16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Column {
                    Text("Hola, ${inicio.tecnico.nombre}", style = MaterialTheme.typography.titleLarge)
                    Text(
                        inicio.tecnico.estadoDisplay,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                TextButton(onClick = alActualizar) { Text("Actualizar") }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Indicador("Ofertas para ti", inicio.ofertasDisponibles, Modifier.weight(1f))
                Indicador("Trabajos activos", inicio.ordenesActivas, Modifier.weight(1f))
            }
        }
        item {
            Text(
                "Trabajos activos",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(top = 8.dp),
            )
        }
        if (inicio.ordenes.isEmpty()) {
            item {
                Text(
                    "No tienes trabajos activos. Revisa la sección Ofertas.",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        items(inicio.ordenes, key = { it.id }) { orden -> TarjetaOrden(orden) }
    }
}

@Composable
private fun Indicador(titulo: String, valor: Int, modifier: Modifier = Modifier) {
    Card(
        modifier,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(
                valor.toString(),
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary,
            )
            Text(titulo, style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
private fun TarjetaOrden(orden: Orden) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(orden.titulo, style = MaterialTheme.typography.titleSmall)
            Text("${orden.sucursal.nombre} · ${orden.sucursal.direccion}", style = MaterialTheme.typography.bodySmall)
            Text(
                "${orden.estadoDisplay} · Prioridad ${orden.prioridadDisplay}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.primary,
            )
        }
    }
}
