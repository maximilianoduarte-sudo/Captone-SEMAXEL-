package cl.semaxel.tecnico.ui.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import cl.semaxel.tecnico.data.Repositorio
import cl.semaxel.tecnico.data.Resultado
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class EstadoLogin(
    val usuario: String = "",
    val clave: String = "",
    val cargando: Boolean = false,
    val error: String? = null,
) {
    val puedeIngresar: Boolean get() = usuario.isNotBlank() && clave.isNotEmpty() && !cargando
}

/**
 * Lógica de la pantalla de inicio de sesión.
 *
 * Si el login funciona, el repositorio guarda el token y la pantalla raíz
 * cambia sola a la app (no hay que navegar desde aquí).
 */
class LoginViewModel(private val repositorio: Repositorio) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoLogin())
    val estado: StateFlow<EstadoLogin> = _estado.asStateFlow()

    fun cambiarUsuario(valor: String) = _estado.update { it.copy(usuario = valor, error = null) }

    fun cambiarClave(valor: String) = _estado.update { it.copy(clave = valor, error = null) }

    fun ingresar() {
        val actual = _estado.value
        if (!actual.puedeIngresar) return
        _estado.update { it.copy(cargando = true, error = null) }
        viewModelScope.launch {
            when (val resultado = repositorio.iniciarSesion(actual.usuario, actual.clave)) {
                is Resultado.Exito -> _estado.update { it.copy(cargando = false, clave = "") }
                is Resultado.Fallo -> _estado.update {
                    it.copy(cargando = false, error = resultado.error.mensaje)
                }
            }
        }
    }
}
