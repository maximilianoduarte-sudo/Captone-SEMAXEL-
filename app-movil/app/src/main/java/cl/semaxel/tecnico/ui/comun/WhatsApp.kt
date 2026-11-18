package cl.semaxel.tecnico.ui.comun

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Phone
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.path
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import cl.semaxel.tecnico.data.remote.Orden
import java.net.URLEncoder

/** Enlaces para escribirle a la sucursal por WhatsApp (sin depender de su app). */
object WhatsApp {

    /**
     * Teléfono de la sucursal en formato internacional, solo dígitos, o null
     * si no sirve para WhatsApp. Pensado para Chile:
     * "+56 9 1234 5678" -> "56912345678"; "9 1234 5678" -> "56912345678".
     */
    fun numero(telefono: String): String? {
        val digitos = telefono.filter { it.isDigit() }
        return when {
            digitos.startsWith("56") && digitos.length in 10..11 -> digitos
            digitos.length == 9 -> "56$digitos"
            digitos.length >= 10 -> digitos
            else -> null
        }
    }

    /** Mensaje inicial: quién escribe y por qué trabajo. */
    fun mensaje(orden: Orden): String =
        "Hola, le escribe el técnico de SEMAXEL asignado al trabajo \"${orden.titulo}\" " +
            "en ${orden.sucursal.nombre}."

    /** https://wa.me/<número>?text=<mensaje>, o null si la sucursal no tiene un teléfono válido. */
    fun enlace(orden: Orden): String? {
        val numero = numero(orden.sucursal.telefono) ?: return null
        val texto = URLEncoder.encode(mensaje(orden), "UTF-8").replace("+", "%20")
        return "https://wa.me/$numero?text=$texto"
    }
}

/** Verde de la marca WhatsApp. */
private val VerdeWhatsApp = Color(0xFF25D366)

/**
 * Globo de conversación redondo con la cola abajo a la izquierda, como el
 * de WhatsApp (dibujado aquí; no es el archivo oficial del logo).
 */
private val GloboConversacion: ImageVector =
    ImageVector.Builder("GloboConversacion", 24.dp, 24.dp, 24f, 24f).apply {
        // Anillo: círculo de radio 8 centrado en (12, 12).
        path(stroke = SolidColor(Color.White), strokeLineWidth = 1.9f) {
            moveTo(20f, 12f)
            arcToRelative(8f, 8f, 0f, isMoreThanHalf = true, isPositiveArc = true, dx1 = -16f, dy1 = 0f)
            arcToRelative(8f, 8f, 0f, isMoreThanHalf = true, isPositiveArc = true, dx1 = 16f, dy1 = 0f)
            close()
        }
        // Cola del globo.
        path(fill = SolidColor(Color.White)) {
            moveTo(5.6f, 15.4f)
            lineTo(3.6f, 20.6f)
            lineTo(9.0f, 19.1f)
            close()
        }
    }.build()

/**
 * Botón redondo verde (globo de conversación con teléfono, como el logo de
 * WhatsApp) que abre la conversación con la sucursal de la orden. No se
 * muestra si la sucursal no tiene un teléfono válido.
 */
@Composable
fun BotonWhatsApp(orden: Orden, modifier: Modifier = Modifier) {
    val enlace = WhatsApp.enlace(orden) ?: return
    val context = LocalContext.current
    IconButton(
        onClick = {
            try {
                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(enlace)))
            } catch (e: ActivityNotFoundException) {
                Toast.makeText(context, "No hay una app para abrir WhatsApp.", Toast.LENGTH_SHORT).show()
            }
        },
        modifier = modifier,
    ) {
        Box(
            Modifier.size(36.dp).background(VerdeWhatsApp, CircleShape),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                GloboConversacion,
                contentDescription = "Escribir a la sucursal por WhatsApp",
                tint = Color.White,
                modifier = Modifier.size(28.dp),
            )
            Icon(
                Icons.Filled.Phone,
                contentDescription = null,
                tint = Color.White,
                modifier = Modifier.size(13.dp),
            )
        }
    }
}
