package cl.semaxel.tecnico.ui.principal

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Work
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import cl.semaxel.tecnico.ui.evidencias.PantallaFirma
import cl.semaxel.tecnico.ui.evidencias.PantallaFotosOrden
import cl.semaxel.tecnico.ui.inicio.PantallaInicio
import cl.semaxel.tecnico.ui.ofertas.PantallaDetalleOferta
import cl.semaxel.tecnico.ui.ofertas.PantallaOfertas
import cl.semaxel.tecnico.ui.perfil.PantallaPerfil
import cl.semaxel.tecnico.ui.trabajos.PantallaDetalleTrabajo
import cl.semaxel.tecnico.ui.trabajos.PantallaTrabajos

/**
 * Las cinco secciones de la app (Documento B, sección 3.3).
 * [titulo] va en la barra superior; [etiqueta], más corta, en la barra
 * inferior (con cinco pestañas, "Mis trabajos" no cabe y se cortaba).
 */
enum class Seccion(val ruta: String, val titulo: String, val icono: ImageVector, val etiqueta: String = titulo) {
    INICIO("inicio", "Inicio", Icons.Filled.Home),
    OFERTAS("ofertas", "Ofertas", Icons.Filled.Work),
    TRABAJOS("trabajos", "Mis trabajos", Icons.Filled.Build, etiqueta = "Trabajos"),
    PERFIL("perfil", "Perfil", Icons.Filled.Person),
}

/** Pantallas internas (se abren desde una sección y tienen flecha para volver). */
private object Rutas {
    const val OFERTA = "oferta/{id}"
    const val TRABAJO = "trabajo/{id}"
    const val FOTOS = "trabajo/{id}/fotos"
    const val FIRMA = "trabajo/{id}/firma"

    fun oferta(id: Int) = "oferta/$id"
    fun trabajo(id: Int) = "trabajo/$id"
    fun fotos(id: Int) = "trabajo/$id/fotos"
    fun firma(id: Int) = "trabajo/$id/firma"

    val titulos = mapOf(
        OFERTA to "Detalle de la oferta",
        TRABAJO to "Detalle del trabajo",
        FOTOS to "Fotos de evidencia",
        FIRMA to "Firma de conformidad",
    )
    val argumentoId = listOf(navArgument("id") { type = NavType.IntType })
}

/**
 * Estructura de la app con sesión iniciada: barra superior, contenido y
 * barra de navegación inferior con las cinco secciones.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaPrincipal() {
    val navegador = rememberNavController()
    val entradaActual by navegador.currentBackStackEntryAsState()
    val rutaActual = entradaActual?.destination?.route
    val seccionActual = Seccion.entries.firstOrNull { it.ruta == rutaActual }
    val esInterna = rutaActual != null && seccionActual == null

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(seccionActual?.titulo ?: Rutas.titulos[rutaActual] ?: "SEMAXEL") },
                navigationIcon = {
                    if (esInterna) {
                        IconButton(onClick = { navegador.popBackStack() }) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Volver")
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    navigationIconContentColor = MaterialTheme.colorScheme.onPrimary,
                ),
            )
        },
        bottomBar = {
            NavigationBar {
                Seccion.entries.forEach { seccion ->
                    NavigationBarItem(
                        selected = seccion == seccionActual,
                        onClick = { irASeccion(navegador, seccion) },
                        icon = { Icon(seccion.icono, contentDescription = null) },
                        label = { Text(seccion.etiqueta, maxLines = 1) },
                    )
                }
            }
        },
    ) { margenes ->
        NavHost(
            navController = navegador,
            startDestination = Seccion.INICIO.ruta,
            modifier = Modifier.padding(margenes),
        ) {
            // ------------------------------------------------ secciones
            composable(Seccion.INICIO.ruta) {
                PantallaInicio(alAbrirTrabajo = { navegador.navigate(Rutas.trabajo(it)) })
            }
            composable(Seccion.OFERTAS.ruta) {
                PantallaOfertas(alAbrirOferta = { navegador.navigate(Rutas.oferta(it)) })
            }
            composable(Seccion.TRABAJOS.ruta) {
                PantallaTrabajos(alAbrirTrabajo = { navegador.navigate(Rutas.trabajo(it)) })
            }
            composable(Seccion.PERFIL.ruta) { PantallaPerfil() }

            // ------------------------------------------------ pantallas internas
            composable(Rutas.OFERTA, arguments = Rutas.argumentoId) { entrada ->
                val id = entrada.arguments?.getInt("id") ?: return@composable
                PantallaDetalleOferta(id, alTomar = { ordenId ->
                    // Tras tomar la oferta se abre la orden creada (y "volver" lleva a Ofertas).
                    navegador.navigate(Rutas.trabajo(ordenId)) {
                        popUpTo(Seccion.OFERTAS.ruta)
                    }
                })
            }
            composable(Rutas.TRABAJO, arguments = Rutas.argumentoId) { entrada ->
                val id = entrada.arguments?.getInt("id") ?: return@composable
                PantallaDetalleTrabajo(
                    id,
                    alAbrirEvidencias = { navegador.navigate(Rutas.fotos(id)) },
                    alAbrirFirma = { navegador.navigate(Rutas.firma(id)) },
                )
            }
            composable(Rutas.FOTOS, arguments = Rutas.argumentoId) { entrada ->
                val id = entrada.arguments?.getInt("id") ?: return@composable
                PantallaFotosOrden(id)
            }
            composable(Rutas.FIRMA, arguments = Rutas.argumentoId) { entrada ->
                val id = entrada.arguments?.getInt("id") ?: return@composable
                PantallaFirma(id, alTerminar = { navegador.popBackStack() })
            }
        }
    }
}

/** Patrón estándar de barra inferior: no apilar secciones y recordar el estado de cada una. */
private fun irASeccion(navegador: NavHostController, seccion: Seccion) {
    navegador.navigate(seccion.ruta) {
        popUpTo(navegador.graph.findStartDestination().id) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}
