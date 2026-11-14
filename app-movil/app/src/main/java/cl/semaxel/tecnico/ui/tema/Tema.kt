package cl.semaxel.tecnico.ui.tema

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

/** Azul marino institucional de SEMAXEL (el mismo de los documentos y la web). */
val AzulSemaxel = Color(0xFF17365D)
val AzulClaro = Color(0xFFEAF0F7)
val VerdeOk = Color(0xFF2E7D32)
val RojoError = Color(0xFFC62828)

private val colores = lightColorScheme(
    primary = AzulSemaxel,
    onPrimary = Color.White,
    primaryContainer = AzulClaro,
    onPrimaryContainer = AzulSemaxel,
    secondary = Color(0xFF4F81BD),
    onSecondary = Color.White,
    background = Color(0xFFF7F9FC),
    surface = Color.White,
    error = RojoError,
)

@Composable
fun TemaSemaxel(contenido: @Composable () -> Unit) {
    MaterialTheme(colorScheme = colores, content = contenido)
}
