package cl.semaxel.tecnico.ui.perfil

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import cl.semaxel.tecnico.data.remote.Tecnico
import cl.semaxel.tecnico.ui.comun.Cargando
import cl.semaxel.tecnico.ui.comun.MensajeError
import cl.semaxel.tecnico.ui.viewModelConRepositorio

@Composable
fun PantallaPerfil() {
    val vm = viewModelConRepositorio { PerfilViewModel(it) }
    val estado by vm.estado.collectAsStateWithLifecycle()
    val tecnico = estado.tecnico

    when {
        estado.cargando && tecnico == null -> Cargando()
        tecnico == null -> MensajeError(estado.error ?: "No se pudo cargar el perfil.", vm::cargar)
        else -> ContenidoPerfil(
            tecnico = tecnico,
            guardando = estado.guardando,
            error = estado.error,
            alCambiarDisponibilidad = vm::cambiarDisponibilidad,
            alCerrarSesion = vm::cerrarSesion,
        )
    }
}

@Composable
private fun ContenidoPerfil(
    tecnico: Tecnico,
    guardando: Boolean,
    error: String?,
    alCambiarDisponibilidad: (Boolean) -> Unit,
    alCerrarSesion: () -> Unit,
) {
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(tecnico.nombre, style = MaterialTheme.typography.titleLarge)
                Dato("Usuario", tecnico.username)
                Dato("Correo", tecnico.correo.ifBlank { "—" })
                Dato("Teléfono", tecnico.telefono.ifBlank { "—" })
                Dato("Especialidades", tecnico.especialidades.joinToString().ifBlank { "—" })
                Dato("Estado", tecnico.estadoDisplay)
            }
        }

        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Disponible para recibir trabajos", style = MaterialTheme.typography.titleSmall)
                        if (!tecnico.puedeCambiarDisponibilidad) {
                            Text(
                                "Mientras tengas trabajos activos el sistema te mantiene ocupado.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                    Switch(
                        checked = tecnico.estado == Tecnico.ESTADO_DISPONIBLE,
                        onCheckedChange = alCambiarDisponibilidad,
                        enabled = tecnico.puedeCambiarDisponibilidad && !guardando,
                    )
                }
                error?.let {
                    HorizontalDivider(Modifier.padding(vertical = 8.dp))
                    Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                }
            }
        }

        Spacer(Modifier.padding(4.dp))
        OutlinedButton(onClick = alCerrarSesion, modifier = Modifier.fillMaxWidth()) {
            Text("Cerrar sesión")
        }
    }
}

@Composable
private fun Dato(etiqueta: String, valor: String) {
    Column {
        Text(etiqueta, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(valor, style = MaterialTheme.typography.bodyLarge)
    }
}
