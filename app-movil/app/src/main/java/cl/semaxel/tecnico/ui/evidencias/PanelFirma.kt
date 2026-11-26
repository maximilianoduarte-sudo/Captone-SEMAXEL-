package cl.semaxel.tecnico.ui.evidencias

import android.graphics.Bitmap
import android.graphics.Paint
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.snapshots.SnapshotStateList
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import java.io.ByteArrayOutputStream

/**
 * Estado del panel de firma: los trazos dibujados con el dedo.
 * Cada trazo es la lista de puntos de un toque continuo.
 */
class EstadoFirma {
    val trazos: SnapshotStateList<SnapshotStateList<Offset>> = mutableStateListOf()
    var tamano: IntSize = IntSize.Zero

    val vacia: Boolean get() = trazos.none { it.size > 1 }

    fun limpiar() = trazos.clear()

    /**
     * Dibuja la firma en una imagen PNG con fondo blanco (lo que se sube al servidor).
     * Devuelve null si no hay firma.
     */
    fun aPng(): ByteArray? {
        if (vacia || tamano.width == 0 || tamano.height == 0) return null
        val bitmap = Bitmap.createBitmap(tamano.width, tamano.height, Bitmap.Config.ARGB_8888)
        val lienzo = android.graphics.Canvas(bitmap)
        lienzo.drawColor(android.graphics.Color.WHITE)
        val pincel = Paint().apply {
            color = android.graphics.Color.BLACK
            strokeWidth = 6f
            style = Paint.Style.STROKE
            strokeCap = Paint.Cap.ROUND
            strokeJoin = Paint.Join.ROUND
            isAntiAlias = true
        }
        trazos.forEach { trazo ->
            trazo.zipWithNext { a, b -> lienzo.drawLine(a.x, a.y, b.x, b.y, pincel) }
        }
        return ByteArrayOutputStream().use { salida ->
            bitmap.compress(Bitmap.CompressFormat.PNG, 100, salida)
            salida.toByteArray()
        }
    }
}

@Composable
fun rememberEstadoFirma(): EstadoFirma = remember { EstadoFirma() }

/** Recuadro blanco donde el encargado firma con el dedo. */
@Composable
fun PanelFirma(estado: EstadoFirma, modifier: Modifier = Modifier) {
    Canvas(
        modifier
            .fillMaxWidth()
            .height(220.dp)
            .background(Color.White)
            .border(1.dp, Color(0xFF9E9E9E))
            .onSizeChanged { estado.tamano = it }
            .pointerInput(Unit) {
                detectDragGestures(
                    onDragStart = { inicio -> estado.trazos.add(mutableStateListOf(inicio)) },
                    onDrag = { cambio, _ -> estado.trazos.lastOrNull()?.add(cambio.position) },
                )
            },
    ) {
        estado.trazos.forEach { trazo ->
            if (trazo.size > 1) {
                val camino = Path().apply {
                    moveTo(trazo.first().x, trazo.first().y)
                    trazo.drop(1).forEach { lineTo(it.x, it.y) }
                }
                drawPath(
                    camino,
                    color = Color.Black,
                    style = Stroke(width = 6f, cap = StrokeCap.Round, join = StrokeJoin.Round),
                )
            }
        }
    }
}
