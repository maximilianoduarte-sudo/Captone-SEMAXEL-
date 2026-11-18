package cl.semaxel.tecnico.ui.evidencias

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.FilledTonalIconButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import cl.semaxel.tecnico.dispositivo.Imagenes
import cl.semaxel.tecnico.ui.comun.Cargando
import cl.semaxel.tecnico.ui.comun.Formato
import cl.semaxel.tecnico.ui.comun.Mensaje
import cl.semaxel.tecnico.ui.comun.MensajeError
import cl.semaxel.tecnico.ui.viewModelConRepositorio
import coil.compose.AsyncImage
import kotlinx.coroutines.launch

/** Fotos de una orden: tomar con la cámara, elegir de la galería y eliminar. */
@Composable
fun PantallaFotosOrden(id: Int) {
    val vm = viewModelConRepositorio { EvidenciasOrdenViewModel(it, id) }
    val estado by vm.estado.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val alcance = rememberCoroutineScope()
    var descripcion by rememberSaveable { mutableStateOf("") }
    var uriCamara by rememberSaveable { mutableStateOf<Uri?>(null) }
    var porEliminar by remember { mutableStateOf<Int?>(null) }
    var preparando by remember { mutableStateOf(false) }

    // Reduce y endereza la foto antes de subirla (ver Imagenes.prepararParaSubir).
    fun subir(uri: Uri) {
        alcance.launch {
            preparando = true
            val bytes = Imagenes.prepararParaSubir(context, uri)
            preparando = false
            if (bytes == null) {
                vm.mostrarError("No se pudo leer la imagen.")
            } else {
                vm.subir(bytes, descripcion)
                descripcion = ""
            }
        }
    }

    val camara = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { tomada ->
        val uri = uriCamara
        if (tomada && uri != null) subir(uri)
    }
    val galeria = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        if (uri != null) subir(uri)
    }

    val orden = estado.dato
    when {
        orden == null && estado.cargando -> Cargando()
        orden == null -> MensajeError(estado.error ?: "No se pudo cargar el trabajo.", vm::cargar)
        else -> {
            val admite = orden.estado in ESTADOS_CON_EVIDENCIA
            val ocupado = estado.procesando || preparando
            LazyVerticalGrid(
                columns = GridCells.Fixed(3),
                modifier = Modifier.fillMaxSize().padding(horizontal = 12.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                item(span = { GridItemSpan(maxLineSpan) }) {
                    Column(Modifier.padding(top = 12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(orden.titulo, style = MaterialTheme.typography.titleMedium)
                        Text(
                            "${orden.sucursal.nombre} · ${orden.estadoDisplay}",
                            style = MaterialTheme.typography.bodySmall,
                        )
                        estado.error?.let { Mensaje(it, esError = true) }
                        estado.aviso?.let { Mensaje(it, esError = false) }
                        if (admite) {
                            OutlinedTextField(
                                descripcion,
                                { descripcion = it.take(255) },
                                label = { Text("Descripción de la próxima foto (opcional)") },
                                singleLine = true,
                                modifier = Modifier.fillMaxWidth(),
                            )
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Button(
                                    onClick = {
                                        val uri = Imagenes.nuevoArchivoParaCamara(context)
                                        uriCamara = uri
                                        camara.launch(uri)
                                    },
                                    enabled = !ocupado,
                                    modifier = Modifier.weight(1f),
                                ) { Text("Tomar foto") }
                                OutlinedButton(
                                    onClick = {
                                        galeria.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly))
                                    },
                                    enabled = !ocupado,
                                    modifier = Modifier.weight(1f),
                                ) { Text("Galería") }
                            }
                            if (ocupado) Text("Subiendo…", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        } else {
                            Mensaje("La orden está ${orden.estadoDisplay.lowercase()}: ya no admite fotos.", esError = false)
                        }
                        Text("${orden.evidencias.size} foto(s)", style = MaterialTheme.typography.titleSmall)
                    }
                }
                items(orden.evidencias, key = { it.id }) { evidencia ->
                    Box(Modifier.aspectRatio(1f)) {
                        AsyncImage(
                            model = evidencia.url,
                            contentDescription = evidencia.descripcion.ifBlank { "Foto de evidencia" },
                            contentScale = ContentScale.Crop,
                            modifier = Modifier.fillMaxSize(),
                        )
                        if (admite) {
                            FilledTonalIconButton(
                                onClick = { porEliminar = evidencia.id },
                                enabled = !ocupado,
                                modifier = Modifier.align(Alignment.TopEnd).padding(4.dp),
                            ) { Icon(Icons.Filled.Delete, contentDescription = "Eliminar foto") }
                        }
                    }
                }
            }
        }
    }

    porEliminar?.let { evidenciaId ->
        AlertDialog(
            onDismissRequest = { porEliminar = null },
            title = { Text("¿Eliminar esta foto?") },
            text = { Text("Se borrará del servidor. Solo puedes eliminar fotos que subiste tú.") },
            confirmButton = {
                Button(onClick = {
                    porEliminar = null
                    vm.eliminar(evidenciaId)
                }) { Text("Eliminar") }
            },
            dismissButton = { TextButton(onClick = { porEliminar = null }) { Text("Cancelar") } },
        )
    }
}

/** Firma de conformidad: el encargado escribe su nombre y firma con el dedo. */
@Composable
fun PantallaFirma(id: Int, alTerminar: () -> Unit) {
    val vm = viewModelConRepositorio { FirmaViewModel(it, id) }
    val estado by vm.estado.collectAsStateWithLifecycle()
    val guardada by vm.guardada.collectAsStateWithLifecycle()
    val firma = rememberEstadoFirma()
    var nombre by rememberSaveable { mutableStateOf("") }

    LaunchedEffect(guardada) { if (guardada) alTerminar() }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(
            "Pide al encargado del local que revise el trabajo, escriba su nombre y firme en el recuadro.",
            style = MaterialTheme.typography.bodyMedium,
        )
        estado.error?.let { Mensaje(it, esError = true) }
        OutlinedTextField(
            nombre,
            { nombre = it.take(150) },
            label = { Text("Nombre de quien firma *") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        PanelFirma(firma)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = firma::limpiar, modifier = Modifier.weight(1f)) { Text("Limpiar") }
            Button(
                onClick = {
                    val png = firma.aPng()
                    if (png == null) vm.mostrarError("Falta la firma.") else vm.guardar(png, nombre)
                },
                enabled = nombre.isNotBlank() && !estado.procesando,
                modifier = Modifier.weight(1f),
            ) { Text(if (estado.procesando) "Guardando…" else "Guardar firma") }
        }
        Text(
            "Fecha: ${Formato.fecha(java.time.OffsetDateTime.now().toString())}",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
