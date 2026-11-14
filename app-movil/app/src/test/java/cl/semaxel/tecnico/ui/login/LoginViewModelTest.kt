package cl.semaxel.tecnico.ui.login

import cl.semaxel.tecnico.data.Repositorio
import cl.semaxel.tecnico.data.Resultado
import cl.semaxel.tecnico.data.remote.ErrorApi
import cl.semaxel.tecnico.data.remote.Inicio
import cl.semaxel.tecnico.data.remote.Tecnico
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test

/** Repositorio falso: responde lo que la prueba indique, sin red. */
private class RepositorioFalso(var respuestaLogin: Resultado<Tecnico>) : Repositorio {
    override val token: StateFlow<String?> = MutableStateFlow(null)
    var llamadasLogin = 0

    override suspend fun iniciarSesion(usuario: String, clave: String): Resultado<Tecnico> {
        llamadasLogin++
        return respuestaLogin
    }

    override suspend fun cerrarSesion() = Unit
    override suspend fun perfil(): Resultado<Tecnico> = error("no se usa")
    override suspend fun cambiarDisponibilidad(disponible: Boolean): Resultado<Tecnico> = error("no se usa")
    override suspend fun inicio(): Resultado<Inicio> = error("no se usa")
}

@OptIn(ExperimentalCoroutinesApi::class)
class LoginViewModelTest {

    private val tecnico = Tecnico(id = 1, username = "cdiaz", nombre = "Carlos Díaz", estado = "DISPONIBLE")

    @Before
    fun preparar() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @After
    fun limpiar() = Dispatchers.resetMain()

    @Test
    fun `no permite ingresar con campos vacios`() {
        val repo = RepositorioFalso(Resultado.Exito(tecnico))
        val vm = LoginViewModel(repo)
        assertFalse(vm.estado.value.puedeIngresar)
        vm.ingresar()
        assertEquals(0, repo.llamadasLogin)
    }

    @Test
    fun `login correcto limpia la clave y no muestra error`() {
        val vm = LoginViewModel(RepositorioFalso(Resultado.Exito(tecnico)))
        vm.cambiarUsuario("cdiaz")
        vm.cambiarClave("secreta")
        vm.ingresar()
        val estado = vm.estado.value
        assertFalse(estado.cargando)
        assertNull(estado.error)
        assertEquals("", estado.clave)
    }

    @Test
    fun `login fallido muestra el mensaje del servidor`() {
        val fallo = Resultado.Fallo(ErrorApi("Usuario o contraseña incorrectos.", http = 400))
        val vm = LoginViewModel(RepositorioFalso(fallo))
        vm.cambiarUsuario("cdiaz")
        vm.cambiarClave("mala")
        vm.ingresar()
        assertEquals("Usuario o contraseña incorrectos.", vm.estado.value.error)
        assertFalse(vm.estado.value.cargando)
    }

    @Test
    fun `escribir de nuevo borra el error`() {
        val vm = LoginViewModel(RepositorioFalso(Resultado.Fallo(ErrorApi("x"))))
        vm.cambiarUsuario("cdiaz")
        vm.cambiarClave("mala")
        vm.ingresar()
        vm.cambiarClave("otra")
        assertNull(vm.estado.value.error)
    }
}
