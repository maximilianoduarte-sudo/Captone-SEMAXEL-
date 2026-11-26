package cl.semaxel.tecnico.ui.comun

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.ui.graphics.graphicsLayer
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.LifecycleResumeEffect

/**
 * Ejecuta [accion] cada vez que la pantalla queda a la vista: al abrir su
 * pestaña, al volver desde un detalle y al volver a la app. Así las listas
 * muestran siempre lo último del servidor sin tocar "Actualizar".
 */
@Composable
fun RecargarAlMostrarse(accion: () -> Unit) {
    val accionActual by rememberUpdatedState(accion)
    LifecycleResumeEffect(Unit) {
        accionActual()
        onPauseOrDispose { }
    }
}

/**
 * Deslizar hacia abajo para actualizar, como en las apps móviles: al tirar
 * la lista desde arriba aparece la rueda y se vuelve a pedir el dato al
 * servidor. [alActualizar] devuelve el Job de la carga para saber cuándo
 * quitar la rueda.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DeslizarParaActualizar(
    alActualizar: () -> Job,
    modifier: Modifier = Modifier,
    contenido: @Composable BoxScope.() -> Unit,
) {
    var actualizando by remember { mutableStateOf(false) }
    val alfa = remember { Animatable(1f) }
    val alcance = rememberCoroutineScope()
    PullToRefreshBox(
        isRefreshing = actualizando,
        onRefresh = {
            alcance.launch {
                actualizando = true
                val inicio = System.currentTimeMillis()
                try {
                    alActualizar().join()
                    // El servidor suele responder en milisegundos: la rueda se
                    // deja un mínimo para que se note que se actualizó.
                    val resto = RUEDA_MINIMA_MS - (System.currentTimeMillis() - inicio)
                    if (resto > 0) delay(resto)
                } finally {
                    actualizando = false
                }
                // Parpadeo corto de la lista al llegar los datos nuevos.
                alfa.animateTo(0.3f, tween(120))
                alfa.animateTo(1f, tween(250))
            }
        },
        modifier = modifier.fillMaxSize(),
    ) {
        Box(Modifier.fillMaxSize().graphicsLayer { alpha = alfa.value }) { contenido() }
    }
}

private const val RUEDA_MINIMA_MS = 600L

/** Indicador de carga centrado. */
@Composable
fun Cargando(modifier: Modifier = Modifier) {
    Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        CircularProgressIndicator()
    }
}

/** Mensaje de error con botón para reintentar. */
@Composable
fun MensajeError(mensaje: String, alReintentar: () -> Unit, modifier: Modifier = Modifier) {
    Column(
        modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp, Alignment.CenterVertically),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(mensaje, textAlign = TextAlign.Center, color = MaterialTheme.colorScheme.error)
        OutlinedButton(onClick = alReintentar) { Text("Reintentar") }
    }
}

/** Sección que todavía no está construida (se completa en las próximas partes). */
@Composable
fun Proximamente(titulo: String, descripcion: String, modifier: Modifier = Modifier) {
    Column(
        modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterVertically),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(titulo, style = MaterialTheme.typography.titleLarge)
        Text(descripcion, textAlign = TextAlign.Center, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
