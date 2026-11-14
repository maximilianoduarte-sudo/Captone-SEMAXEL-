package cl.semaxel.tecnico.ui.principal

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.PhotoCamera
import androidx.compose.material.icons.filled.Work
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
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
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import cl.semaxel.tecnico.ui.comun.Proximamente
import cl.semaxel.tecnico.ui.inicio.PantallaInicio
import cl.semaxel.tecnico.ui.perfil.PantallaPerfil

/** Las cinco secciones de la app (Documento B, sección 3.3). */
enum class Seccion(val ruta: String, val titulo: String, val icono: ImageVector) {
    INICIO("inicio", "Inicio", Icons.Filled.Home),
    OFERTAS("ofertas", "Ofertas", Icons.Filled.Work),
    TRABAJOS("trabajos", "Mis trabajos", Icons.Filled.Build),
    EVIDENCIAS("evidencias", "Evidencias", Icons.Filled.PhotoCamera),
    PERFIL("perfil", "Perfil", Icons.Filled.Person),
}

/**
 * Estructura de la app con sesión iniciada: barra superior, contenido de la
 * sección elegida y barra de navegación inferior.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaPrincipal() {
    val navegador = rememberNavController()
    val entradaActual by navegador.currentBackStackEntryAsState()
    val destinoActual = entradaActual?.destination
    val seccionActual = Seccion.entries.firstOrNull { it.ruta == destinoActual?.route } ?: Seccion.INICIO

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(seccionActual.titulo) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                ),
            )
        },
        bottomBar = {
            NavigationBar {
                Seccion.entries.forEach { seccion ->
                    val elegida = destinoActual?.hierarchy?.any { it.route == seccion.ruta } == true
                    NavigationBarItem(
                        selected = elegida,
                        onClick = {
                            navegador.navigate(seccion.ruta) {
                                // Patrón estándar de barra inferior: no apilar
                                // secciones y recordar el estado de cada una.
                                popUpTo(navegador.graph.findStartDestination().id) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(seccion.icono, contentDescription = null) },
                        label = { Text(seccion.titulo, maxLines = 1) },
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
            composable(Seccion.INICIO.ruta) { PantallaInicio() }
            composable(Seccion.OFERTAS.ruta) {
                Proximamente(
                    "Ofertas",
                    "Aquí verás las ofertas de tu especialidad y podrás tomarlas.",
                )
            }
            composable(Seccion.TRABAJOS.ruta) {
                Proximamente(
                    "Mis trabajos",
                    "Aquí verás tus órdenes: llegada con GPS, iniciar y resolver.",
                )
            }
            composable(Seccion.EVIDENCIAS.ruta) {
                Proximamente(
                    "Evidencias",
                    "Aquí podrás subir fotos y registrar la firma del encargado.",
                )
            }
            composable(Seccion.PERFIL.ruta) { PantallaPerfil() }
        }
    }
}
