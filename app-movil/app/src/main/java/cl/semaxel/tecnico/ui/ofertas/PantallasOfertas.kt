package cl.semaxel.tecnico.ui.ofertas

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import cl.semaxel.tecnico.data.remote.Oferta
import cl.semaxel.tecnico.dispositivo.Ubicacion
import cl.semaxel.tecnico.ui.comun.Cargando
import cl.semaxel.tecnico.ui.comun.DeslizarParaActualizar
import cl.semaxel.tecnico.ui.comun.RecargarAlMostrarse
import cl.semaxel.tecnico.ui.comun.Dato
import cl.semaxel.tecnico.ui.comun.EtiquetaPrioridad
import cl.semaxel.tecnico.ui.comun.Formato
import cl.semaxel.tecnico.ui.comun.Mensaje
import cl.semaxel.tecnico.ui.comun.MensajeError
import cl.semaxel.tecnico.ui.comun.TarjetaOferta
import cl.semaxel.tecnico.ui.viewModelConRepositorio

/** Sección Ofertas: listado de ofertas de la especialidad del técnico. */
@Composable
fun PantallaOfertas(alAbrirOferta: (Int) -> Unit) {
    val vm = viewModelConRepositorio { OfertasViewModel(it) }
    val estado by vm.estado.collectAsStateWithLifecycle()
    RecargarAlMostrarse(vm::cargar)
    val ofertas = estado.dato

    when {
        ofertas == null && estado.cargando -> Cargando()
        ofertas == null -> MensajeError(estado.error ?: "No se pudieron cargar las ofertas.", vm::cargar)
        else -> DeslizarParaActualizar(vm::cargar) { LazyColumn(
            Modifier.fillMaxSize().padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item {
                Text(
                    "${ofertas.size} oferta(s) de tus especialidades",
                    style = MaterialTheme.typography.titleSmall,
                    modifier = Modifier.padding(top = 12.dp),
                )
            }
            estado.error?.let { item { Mensaje(it, esError = true) } }
            if (ofertas.isEmpty()) {
                item {
                    Text(
                        "No hay ofertas disponibles para tus especialidades en este momento.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            items(ofertas, key = { it.id }) { oferta ->
                TarjetaOferta(oferta, alTocar = { alAbrirOferta(oferta.id) })
            }
            item { Spacer(Modifier.height(8.dp)) }
        } }
    }
}

/** Detalle de una oferta con el botón para tomarla. */
@Composable
fun PantallaDetalleOferta(id: Int, alTomar: (ordenId: Int) -> Unit) {
    val vm = viewModelConRepositorio { OfertaDetalleViewModel(it, id) }
    val estado by vm.estado.collectAsStateWithLifecycle()
    val ordenCreada by vm.ordenCreada.collectAsStateWithLifecycle()
    var confirmar by remember { mutableStateOf(false) }

    LaunchedEffect(ordenCreada) {
        ordenCreada?.let {
            vm.navegacionHecha()
            alTomar(it)
        }
    }

    val oferta = estado.dato
    when {
        oferta == null && estado.cargando -> Cargando()
        oferta == null -> MensajeError(estado.error ?: "No se pudo cargar la oferta.", vm::cargar)
        else -> ContenidoOferta(
            oferta = oferta,
            procesando = estado.procesando,
            error = estado.error,
            alTomar = { confirmar = true },
        )
    }

    if (confirmar && oferta != null) {
        AlertDialog(
            onDismissRequest = { confirmar = false },
            title = { Text("¿Tomar esta oferta?") },
            text = {
                Text("Se creará una orden de trabajo a tu nombre en ${oferta.sucursal.nombre} y quedarás ocupado.")
            },
            confirmButton = {
                Button(onClick = {
                    confirmar = false
                    vm.tomar()
                }) { Text("Tomar oferta") }
            },
            dismissButton = { TextButton(onClick = { confirmar = false }) { Text("Cancelar") } },
        )
    }
}

@Composable
private fun ContenidoOferta(oferta: Oferta, procesando: Boolean, error: String?, alTomar: () -> Unit) {
    val context = LocalContext.current
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(oferta.titulo, style = MaterialTheme.typography.titleLarge)
        EtiquetaPrioridad(oferta.prioridad, "Prioridad ${oferta.prioridadDisplay}")
        error?.let { Mensaje(it, esError = true) }

        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Dato("Descripción de la falla", oferta.descripcion.ifBlank { "—" })
                Dato("Categoría", oferta.categoria)
                oferta.especialidad?.let { Dato("Especialidad requerida", it) }
                Dato("Empresa", oferta.empresa)
                Dato("Publicada", Formato.fecha(oferta.fechaPublicacion))
                Dato("Vence", Formato.fecha(oferta.fechaVencimiento))
                if (oferta.observaciones.isNotBlank()) Dato("Observaciones", oferta.observaciones)
            }
        }

        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Local", style = MaterialTheme.typography.titleSmall)
                Dato(oferta.sucursal.nombre, Formato.direccion(oferta.sucursal))
                if (oferta.sucursal.telefono.isNotBlank()) Dato("Teléfono", oferta.sucursal.telefono)
                Dato("Horario de atención", Formato.horario(oferta.sucursal.horario).joinToString("\n"))
                OutlinedButton(onClick = { Ubicacion.abrirEnMapa(context, oferta.sucursal) }) {
                    Text("Ver en el mapa")
                }
            }
        }

        if (oferta.estado == "DISPONIBLE") {
            Button(
                onClick = alTomar,
                enabled = !procesando,
                modifier = Modifier.fillMaxWidth().height(48.dp),
            ) { Text(if (procesando) "Tomando…" else "Tomar oferta") }
        } else {
            Mensaje("Esta oferta ya no está disponible.", esError = false)
        }
    }
}
