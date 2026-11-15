package cl.semaxel.tecnico.ui

import cl.semaxel.tecnico.data.Muestras
import cl.semaxel.tecnico.data.RepositorioFalso
import cl.semaxel.tecnico.data.Resultado
import cl.semaxel.tecnico.data.remote.ErrorApi
import cl.semaxel.tecnico.data.remote.Oferta
import cl.semaxel.tecnico.data.remote.Orden
import cl.semaxel.tecnico.data.remote.TomarOfertaRespuesta
import cl.semaxel.tecnico.ui.ofertas.OfertaDetalleViewModel
import cl.semaxel.tecnico.ui.trabajos.TrabajoDetalleViewModel
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

/** Lógica de las pantallas de ofertas y trabajos, con un repositorio falso. */
@OptIn(ExperimentalCoroutinesApi::class)
class TerrenoViewModelsTest {

    @Before
    fun preparar() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @After
    fun limpiar() = Dispatchers.resetMain()

    // ------------------------------------------------------------ ofertas

    private class RepositorioOfertas(private val alTomar: Resultado<TomarOfertaRespuesta>) : RepositorioFalso() {
        override suspend fun oferta(id: Int): Resultado<Oferta> = Resultado.Exito(Muestras.oferta())
        override suspend fun tomarOferta(id: Int) = alTomar
    }

    @Test
    fun `tomar una oferta entrega la orden creada para navegar`() {
        val respuesta = TomarOfertaRespuesta(ordenId = 6, oferta = Muestras.oferta("TOMADA"))
        val vm = OfertaDetalleViewModel(RepositorioOfertas(Resultado.Exito(respuesta)), id = 2)
        vm.tomar()
        assertEquals(6, vm.ordenCreada.value)
        assertEquals("TOMADA", vm.estado.value.dato?.estado)
        vm.navegacionHecha()
        assertNull(vm.ordenCreada.value)
    }

    @Test
    fun `si otro tecnico la tomo primero se muestra el motivo`() {
        val fallo = Resultado.Fallo(ErrorApi("Esta oferta ya no está disponible.", 409, "no_disponible"))
        val vm = OfertaDetalleViewModel(RepositorioOfertas(fallo), id = 2)
        vm.tomar()
        assertNull(vm.ordenCreada.value)
        assertEquals("Esta oferta ya no está disponible.", vm.estado.value.error)
        assertFalse(vm.estado.value.procesando)
    }

    // ------------------------------------------------------------ trabajos

    private class RepositorioTrabajo : RepositorioFalso() {
        var diagnosticoRecibido: String? = null
        var llegadaRecibida: Pair<Double, Double>? = null

        override suspend fun orden(id: Int): Resultado<Orden> = Resultado.Exito(Muestras.orden())

        override suspend fun iniciar(id: Int, diagnostico: String, costoEstimado: String?): Resultado<Orden> {
            diagnosticoRecibido = diagnostico
            return Resultado.Exito(Muestras.orden("EN_EJECUCION", listOf("resolver")))
        }

        override suspend fun resolver(
            id: Int,
            trabajoRealizado: String,
            observaciones: String?,
            costoFinal: String?,
        ): Resultado<Orden> = Resultado.Fallo(ErrorApi("Transición no permitida.", 409, "transicion_invalida"))

        override suspend fun registrarLlegada(
            id: Int,
            latitud: Double,
            longitud: Double,
            precisionM: Float?,
        ): Resultado<Orden> {
            llegadaRecibida = latitud to longitud
            return Resultado.Exito(Muestras.orden(acciones = listOf("iniciar")))
        }
    }

    @Test
    fun `iniciar actualiza la orden y muestra el aviso`() {
        val repo = RepositorioTrabajo()
        val vm = TrabajoDetalleViewModel(repo, id = 6)
        vm.iniciar("Enchufe derretido", "")
        assertEquals("Enchufe derretido", repo.diagnosticoRecibido)
        assertEquals("EN_EJECUCION", vm.estado.value.dato?.estado)
        assertEquals(listOf("resolver"), vm.estado.value.dato?.acciones)
        assertEquals("Trabajo iniciado.", vm.estado.value.aviso)
    }

    @Test
    fun `un 409 al resolver se muestra como error y no cambia la orden`() {
        val vm = TrabajoDetalleViewModel(RepositorioTrabajo(), id = 6)
        vm.resolver("Listo", "", "")
        assertEquals("Transición no permitida.", vm.estado.value.error)
        assertEquals("ASIGNADA", vm.estado.value.dato?.estado)
        assertNull(vm.estado.value.aviso)
    }

    @Test
    fun `la llegada envia la posicion al servidor`() {
        val repo = RepositorioTrabajo()
        val vm = TrabajoDetalleViewModel(repo, id = 6)
        vm.registrarLlegada(-33.4378, -70.6504, 8f)
        assertEquals(-33.4378 to -70.6504, repo.llegadaRecibida)
        assertEquals("Llegada registrada.", vm.estado.value.aviso)
    }

    @Test
    fun `los errores del celular se muestran sin llamar al servidor`() {
        val vm = TrabajoDetalleViewModel(RepositorioTrabajo(), id = 6)
        vm.mostrarError("No se pudo obtener tu ubicación.")
        assertEquals("No se pudo obtener tu ubicación.", vm.estado.value.error)
    }
}
