package cl.semaxel.tecnico.data

import cl.semaxel.tecnico.data.remote.Evidencia
import cl.semaxel.tecnico.data.remote.Inicio
import cl.semaxel.tecnico.data.remote.Oferta
import cl.semaxel.tecnico.data.remote.Orden
import cl.semaxel.tecnico.data.remote.Sucursal
import cl.semaxel.tecnico.data.remote.Tecnico
import cl.semaxel.tecnico.data.remote.TomarOfertaRespuesta
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/**
 * Repositorio falso para pruebas: no usa red. Cada prueba sobrescribe solo
 * las operaciones que necesita; las demás fallan si se llaman por error.
 */
open class RepositorioFalso : Repositorio {
    override val token: StateFlow<String?> = MutableStateFlow(null)

    override suspend fun iniciarSesion(usuario: String, clave: String): Resultado<Tecnico> = noUsado()
    override suspend fun cerrarSesion() = Unit
    override suspend fun perfil(): Resultado<Tecnico> = noUsado()
    override suspend fun cambiarDisponibilidad(disponible: Boolean): Resultado<Tecnico> = noUsado()
    override suspend fun inicio(): Resultado<Inicio> = noUsado()
    override suspend fun ofertas(): Resultado<List<Oferta>> = noUsado()
    override suspend fun oferta(id: Int): Resultado<Oferta> = noUsado()
    override suspend fun tomarOferta(id: Int): Resultado<TomarOfertaRespuesta> = noUsado()
    override suspend fun ordenes(): Resultado<List<Orden>> = noUsado()
    override suspend fun orden(id: Int): Resultado<Orden> = noUsado()
    override suspend fun iniciar(id: Int, diagnostico: String, costoEstimado: String?): Resultado<Orden> = noUsado()
    override suspend fun resolver(
        id: Int,
        trabajoRealizado: String,
        observaciones: String?,
        costoFinal: String?,
    ): Resultado<Orden> = noUsado()
    override suspend fun registrarLlegada(
        id: Int,
        latitud: Double,
        longitud: Double,
        precisionM: Float?,
    ): Resultado<Orden> = noUsado()
    override suspend fun subirEvidencia(id: Int, imagenJpeg: ByteArray, descripcion: String): Resultado<Evidencia> =
        noUsado()
    override suspend fun eliminarEvidencia(id: Int, evidenciaId: Int): Resultado<Unit> = noUsado()
    override suspend fun registrarFirma(id: Int, firmaPng: ByteArray, nombreFirmante: String): Resultado<Orden> =
        noUsado()

    private fun noUsado(): Nothing = error("Operación no preparada en esta prueba")
}

/** Datos de prueba (hipotéticos). */
object Muestras {
    val sucursal = Sucursal(nombre = "Local Centro", direccion = "Av. Ejemplo 123", comuna = "Santiago")

    fun orden(estado: String = "ASIGNADA", acciones: List<String> = listOf("iniciar")) = Orden(
        id = 6,
        estado = estado,
        titulo = "Enchufe quemado",
        prioridad = "ALTA",
        sucursal = sucursal,
        fechaAsignacion = "2026-11-13T15:40:02-03:00",
        acciones = acciones,
    )

    fun oferta(estado: String = "DISPONIBLE") = Oferta(
        id = 2,
        estado = estado,
        titulo = "Enchufe quemado",
        prioridad = "ALTA",
        sucursal = sucursal,
        fechaPublicacion = "2026-11-13T10:00:00-03:00",
    )
}
