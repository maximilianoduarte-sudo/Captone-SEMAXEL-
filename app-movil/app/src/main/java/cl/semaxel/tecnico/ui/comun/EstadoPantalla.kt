package cl.semaxel.tecnico.ui.comun

/**
 * Estado común de las pantallas que muestran un dato de la API y permiten
 * acciones sobre él.
 *
 * @property dato lo que se muestra (null mientras no se ha cargado).
 * @property cargando se está pidiendo el dato por primera vez o actualizando.
 * @property procesando se está ejecutando una acción (tomar, iniciar, subir...).
 * @property error mensaje de error para mostrar (por ejemplo, un 409).
 * @property aviso mensaje de éxito para mostrar.
 */
data class EstadoPantalla<T>(
    val dato: T? = null,
    val cargando: Boolean = true,
    val procesando: Boolean = false,
    val error: String? = null,
    val aviso: String? = null,
)
