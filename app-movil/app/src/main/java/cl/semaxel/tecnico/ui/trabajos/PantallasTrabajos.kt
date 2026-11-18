package cl.semaxel.tecnico.ui.trabajos

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import cl.semaxel.tecnico.data.remote.Orden
import cl.semaxel.tecnico.dispositivo.Ubicacion
import cl.semaxel.tecnico.ui.comun.Cargando
import cl.semaxel.tecnico.ui.comun.RecargarAlMostrarse
import cl.semaxel.tecnico.ui.comun.Dato
import cl.semaxel.tecnico.ui.comun.Etiqueta
import cl.semaxel.tecnico.ui.comun.EtiquetaPrioridad
import cl.semaxel.tecnico.ui.comun.Formato
import cl.semaxel.tecnico.ui.comun.Mensaje
import cl.semaxel.tecnico.ui.comun.MensajeError
import cl.semaxel.tecnico.ui.comun.TarjetaOrden
import cl.semaxel.tecnico.ui.tema.RojoError
import cl.semaxel.tecnico.ui.tema.VerdeOk
import cl.semaxel.tecnico.ui.viewModelConRepositorio
import kotlinx.coroutines.launch

/** Sección Mis trabajos: órdenes del técnico, con filtro Activos / Todos. */
@Composable
fun PantallaTrabajos(alAbrirTrabajo: (Int) -> Unit) {
    val vm = viewModelConRepositorio { TrabajosViewModel(it) }
    val estado by vm.estado.collectAsStateWithLifecycle()
    RecargarAlMostrarse(vm::cargar)
    var soloActivos by rememberSaveable { mutableStateOf(true) }
    val ordenes = estado.dato

    when {
        ordenes == null && estado.cargando -> Cargando()
        ordenes == null -> MensajeError(estado.error ?: "No se pudieron cargar tus trabajos.", vm::cargar)
        else -> {
            val visibles = if (soloActivos) ordenes.filter { it.estado in ESTADOS_ACTIVOS } else ordenes
            LazyColumn(
                Modifier.fillMaxSize().padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                item {
                    Row(
                        Modifier.fillMaxWidth().padding(top = 12.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        FilterChip(selected = soloActivos, onClick = { soloActivos = true }, label = { Text("Activos") })
                        FilterChip(selected = !soloActivos, onClick = { soloActivos = false }, label = { Text("Todos") })
                        Spacer(Modifier.weight(1f))
                        TextButton(onClick = vm::cargar, enabled = !estado.cargando) { Text("Actualizar") }
                    }
                }
                estado.error?.let { item { Mensaje(it, esError = true) } }
                if (visibles.isEmpty()) {
                    item {
                        Text(
                            if (soloActivos) "No tienes trabajos activos. Toma uno en la sección Ofertas."
                            else "Todavía no tienes trabajos.",
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
                items(visibles, key = { it.id }) { orden ->
                    TarjetaOrden(
                        orden,
                        alTocar = { alAbrirTrabajo(orden.id) },
                        pie = "Asignada ${Formato.fecha(orden.fechaAsignacion)}",
                    )
                }
                item { Spacer(Modifier.height(8.dp)) }
            }
        }
    }
}

/** Detalle de una orden con las acciones de terreno. */
@Composable
fun PantallaDetalleTrabajo(id: Int, alAbrirEvidencias: () -> Unit, alAbrirFirma: () -> Unit) {
    val vm = viewModelConRepositorio { TrabajoDetalleViewModel(it, id) }
    val estado by vm.estado.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val alcance = rememberCoroutineScope()
    var dialogo by remember { mutableStateOf<Dialogo?>(null) }

    // Llegada: se pide la ubicación actual y se envía al servidor, que calcula la distancia.
    fun enviarUbicacion() {
        alcance.launch {
            val posicion = Ubicacion.actual(context)
            if (posicion == null) {
                vm.mostrarError("No se pudo obtener tu ubicación. Activa el GPS e inténtalo de nuevo.")
            } else {
                vm.registrarLlegada(
                    posicion.latitude,
                    posicion.longitude,
                    if (posicion.hasAccuracy()) posicion.accuracy else null,
                )
            }
        }
    }

    val pedirPermiso = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { respuestas ->
        if (respuestas.values.any { it }) {
            enviarUbicacion()
        } else {
            vm.mostrarError("Sin permiso de ubicación no se puede registrar la llegada.")
        }
    }

    val orden = estado.dato
    when {
        orden == null && estado.cargando -> Cargando()
        orden == null -> MensajeError(estado.error ?: "No se pudo cargar el trabajo.", vm::cargar)
        else -> ContenidoTrabajo(
            orden = orden,
            procesando = estado.procesando,
            error = estado.error,
            aviso = estado.aviso,
            alRegistrarLlegada = {
                if (Ubicacion.tienePermiso(context)) enviarUbicacion() else pedirPermiso.launch(Ubicacion.PERMISOS)
            },
            alIniciar = { dialogo = Dialogo.INICIAR },
            alResolver = { dialogo = Dialogo.RESOLVER },
            alAbrirEvidencias = alAbrirEvidencias,
            alAbrirFirma = alAbrirFirma,
            alActualizar = vm::cargar,
        )
    }

    when (dialogo) {
        Dialogo.INICIAR -> DialogoDosCampos(
            titulo = "Iniciar trabajo",
            etiqueta1 = "Diagnóstico *",
            etiqueta2 = "Costo estimado (opcional)",
            numerico2 = true,
            textoConfirmar = "Iniciar",
            alCancelar = { dialogo = null },
            alConfirmar = { diagnostico, costo ->
                dialogo = null
                vm.iniciar(diagnostico, costo)
            },
        )
        Dialogo.RESOLVER -> DialogoResolver(
            alCancelar = { dialogo = null },
            alConfirmar = { trabajo, observaciones, costo ->
                dialogo = null
                vm.resolver(trabajo, observaciones, costo)
            },
        )
        null -> Unit
    }
}

private enum class Dialogo { INICIAR, RESOLVER }

@Composable
private fun ContenidoTrabajo(
    orden: Orden,
    procesando: Boolean,
    error: String?,
    aviso: String?,
    alRegistrarLlegada: () -> Unit,
    alIniciar: () -> Unit,
    alResolver: () -> Unit,
    alAbrirEvidencias: () -> Unit,
    alAbrirFirma: () -> Unit,
    alActualizar: () -> Unit,
) {
    val context = LocalContext.current
    val acciones = orden.acciones
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(orden.titulo, style = MaterialTheme.typography.titleLarge)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            EtiquetaPrioridad(orden.prioridad, "Prioridad ${orden.prioridadDisplay}")
            Etiqueta(orden.estadoDisplay.ifBlank { orden.estado }, MaterialTheme.colorScheme.primary)
        }
        error?.let { Mensaje(it, esError = true) }
        aviso?.let { Mensaje(it, esError = false) }

        // ---------------- acciones (las decide el servidor) ----------------
        if ("registrar_llegada" in acciones) {
            Button(onClick = alRegistrarLlegada, enabled = !procesando, modifier = Modifier.fillMaxWidth()) {
                Text("Registrar llegada al local (GPS)")
            }
        }
        if ("iniciar" in acciones) {
            Button(onClick = alIniciar, enabled = !procesando, modifier = Modifier.fillMaxWidth()) {
                Text("Iniciar trabajo")
            }
        }
        if ("resolver" in acciones) {
            Button(onClick = alResolver, enabled = !procesando, modifier = Modifier.fillMaxWidth()) {
                Text("Marcar como resuelto")
            }
        }
        if ("subir_evidencia" in acciones || orden.evidencias.isNotEmpty()) {
            OutlinedButton(onClick = alAbrirEvidencias, modifier = Modifier.fillMaxWidth()) {
                Text("Fotos de evidencia (${orden.evidencias.size})")
            }
        }
        if ("firmar" in acciones) {
            OutlinedButton(onClick = alAbrirFirma, modifier = Modifier.fillMaxWidth()) {
                Text("Firma de conformidad del encargado")
            }
        }
        if (procesando) Text("Enviando…", color = MaterialTheme.colorScheme.onSurfaceVariant)

        // ---------------- llegada y SLA ----------------
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Llegada y tiempo de respuesta", style = MaterialTheme.typography.titleSmall)
                val llegada = orden.llegada
                if (llegada == null) {
                    Dato("Llegada", "Sin registrar")
                } else {
                    val verificacion = when (llegada.verificada) {
                        true -> "verificada a ${llegada.distanciaM} m del local"
                        false -> "fuera del radio: a ${llegada.distanciaM} m del local"
                        null -> "no verificable (el local no tiene coordenadas)"
                    }
                    Dato("Llegada", "${Formato.fecha(llegada.fecha)}, $verificacion")
                }
                orden.tiempoRespuestaMinutos?.let { minutos ->
                    val sla = when (orden.slaRespuestaCumplido) {
                        true -> " · cumple el SLA (${orden.slaRespuestaMinutos} min)"
                        false -> " · excede el SLA (${orden.slaRespuestaMinutos} min)"
                        null -> ""
                    }
                    Text(
                        "Tiempo de respuesta: $minutos min$sla",
                        color = when (orden.slaRespuestaCumplido) {
                            true -> VerdeOk
                            false -> RojoError
                            null -> MaterialTheme.colorScheme.onSurface
                        },
                    )
                }
            }
        }

        // ---------------- datos del trabajo ----------------
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Trabajo", style = MaterialTheme.typography.titleSmall)
                Dato("Descripción de la falla", orden.descripcion.ifBlank { "—" })
                Dato("Diagnóstico", orden.diagnostico.ifBlank { "—" })
                Dato("Trabajo realizado", orden.trabajoRealizado.ifBlank { "—" })
                if (orden.observaciones.isNotBlank()) Dato("Observaciones", orden.observaciones)
                Dato("Costo estimado", Formato.pesos(orden.costoEstimado))
                Dato("Costo final", Formato.pesos(orden.costoFinal))
                Dato("Asignada", Formato.fecha(orden.fechaAsignacion))
                Dato("Inicio", Formato.fecha(orden.fechaInicio))
                Dato("Fin", Formato.fecha(orden.fechaFin))
                Dato("Firma", orden.firma?.let { "${it.nombreFirmante}, ${Formato.fecha(it.fechaFirma)}" } ?: "Sin firma")
            }
        }

        // ---------------- local ----------------
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Local", style = MaterialTheme.typography.titleSmall)
                Dato(orden.sucursal.nombre, Formato.direccion(orden.sucursal))
                Dato("Empresa", orden.empresa)
                if (orden.sucursal.telefono.isNotBlank()) Dato("Teléfono", orden.sucursal.telefono)
                Dato("Horario de atención", Formato.horario(orden.sucursal.horario).joinToString("\n"))
                OutlinedButton(onClick = { Ubicacion.abrirEnMapa(context, orden.sucursal) }) {
                    Text("Ver en el mapa")
                }
            }
        }
        TextButton(onClick = alActualizar) { Text("Actualizar") }
    }
}

/** Diálogo con un campo obligatorio y uno opcional (se usa para iniciar). */
@Composable
private fun DialogoDosCampos(
    titulo: String,
    etiqueta1: String,
    etiqueta2: String,
    numerico2: Boolean,
    textoConfirmar: String,
    alCancelar: () -> Unit,
    alConfirmar: (String, String) -> Unit,
) {
    var campo1 by rememberSaveable { mutableStateOf("") }
    var campo2 by rememberSaveable { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = alCancelar,
        title = { Text(titulo) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(campo1, { campo1 = it }, label = { Text(etiqueta1) }, minLines = 3)
                OutlinedTextField(
                    campo2,
                    { campo2 = it.filter { c -> c.isDigit() || !numerico2 } },
                    label = { Text(etiqueta2) },
                    singleLine = true,
                    keyboardOptions = if (numerico2) KeyboardOptions(keyboardType = KeyboardType.Number) else KeyboardOptions.Default,
                )
            }
        },
        confirmButton = {
            Button(onClick = { alConfirmar(campo1, campo2) }, enabled = campo1.isNotBlank()) { Text(textoConfirmar) }
        },
        dismissButton = { TextButton(onClick = alCancelar) { Text("Cancelar") } },
    )
}

@Composable
private fun DialogoResolver(alCancelar: () -> Unit, alConfirmar: (String, String, String) -> Unit) {
    var trabajo by rememberSaveable { mutableStateOf("") }
    var observaciones by rememberSaveable { mutableStateOf("") }
    var costo by rememberSaveable { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = alCancelar,
        title = { Text("Marcar como resuelto") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(trabajo, { trabajo = it }, label = { Text("Trabajo realizado *") }, minLines = 3)
                OutlinedTextField(observaciones, { observaciones = it }, label = { Text("Observaciones (opcional)") })
                OutlinedTextField(
                    costo,
                    { costo = it.filter(Char::isDigit) },
                    label = { Text("Costo final (opcional)") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                )
            }
        },
        confirmButton = {
            Button(onClick = { alConfirmar(trabajo, observaciones, costo) }, enabled = trabajo.isNotBlank()) {
                Text("Resolver")
            }
        },
        dismissButton = { TextButton(onClick = alCancelar) { Text("Cancelar") } },
    )
}
