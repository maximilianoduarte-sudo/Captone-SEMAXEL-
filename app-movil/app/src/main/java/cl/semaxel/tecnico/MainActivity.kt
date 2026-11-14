package cl.semaxel.tecnico

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import cl.semaxel.tecnico.ui.SemaxelRaiz
import cl.semaxel.tecnico.ui.tema.TemaSemaxel

/** Única Activity: todas las pantallas son composables de Jetpack Compose. */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            TemaSemaxel {
                SemaxelRaiz()
            }
        }
    }
}
