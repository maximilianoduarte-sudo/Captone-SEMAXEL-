package cl.semaxel.tecnico.ui.login

import cl.semaxel.tecnico.data.RepositorioFalso
import cl.semaxel.tecnico.data.Resultado
import cl.semaxel.tecnico.data.remote.ErrorApi
import cl.semaxel.tecnico.data.remote.Tecnico
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test

/** Repositorio que responde al login lo que la prueba indique. */
private class RepositorioLogin(private val respuesta: Resultado<Tecnico>) : RepositorioFalso() {
    var llamadasLogin = 0

    override suspend fun iniciarSesion(usuario: String, clave: String): Resultado<Tecnico> {
        llamadasLogin++
        return respuesta
    }
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
        val repo = RepositorioLogin(Resultado.Exito(tecnico))
        val vm = LoginViewModel(repo)
        assertFalse(vm.estado.value.puedeIngresar)
        vm.ingresar()
        assertEquals(0, repo.llamadasLogin)
    }

    @Test
    fun `login correcto limpia la clave y no muestra error`() {
        val vm = LoginViewModel(RepositorioLogin(Resultado.Exito(tecnico)))
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
        val vm = LoginViewModel(RepositorioLogin(fallo))
        vm.cambiarUsuario("cdiaz")
        vm.cambiarClave("mala")
        vm.ingresar()
        assertEquals("Usuario o contraseña incorrectos.", vm.estado.value.error)
        assertFalse(vm.estado.value.cargando)
    }

    @Test
    fun `escribir de nuevo borra el error`() {
        val vm = LoginViewModel(RepositorioLogin(Resultado.Fallo(ErrorApi("x"))))
        vm.cambiarUsuario("cdiaz")
        vm.cambiarClave("mala")
        vm.ingresar()
        vm.cambiarClave("otra")
        assertNull(vm.estado.value.error)
    }
}
