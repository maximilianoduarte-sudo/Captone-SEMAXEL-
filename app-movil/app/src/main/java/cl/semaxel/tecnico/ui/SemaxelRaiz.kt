package cl.semaxel.tecnico.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import cl.semaxel.tecnico.ui.comun.Cargando
import cl.semaxel.tecnico.ui.login.PantallaLogin
import cl.semaxel.tecnico.ui.principal.PantallaPrincipal

/**
 * Pantalla raíz: muestra el login o la app según haya sesión.
 *
 * No se navega "a mano" entre login y app: si el token desaparece (cerrar
 * sesión o el servidor responde 401), esta función se vuelve a dibujar sola y
 * aparece el login.
 */
@Composable
fun SemaxelRaiz() {
    val vm = viewModelConRepositorio { RaizViewModel(it) }
    val estado by vm.estado.collectAsStateWithLifecycle()

    when (estado) {
        EstadoSesion.CARGANDO -> Cargando()
        EstadoSesion.SIN_SESION -> PantallaLogin()
        EstadoSesion.CON_SESION -> PantallaPrincipal()
    }
}
