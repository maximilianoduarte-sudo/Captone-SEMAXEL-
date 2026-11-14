package cl.semaxel.tecnico.ui

import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import cl.semaxel.tecnico.SemaxelApp
import cl.semaxel.tecnico.data.Repositorio

/**
 * Crea un ViewModel que recibe el [Repositorio] de la app.
 *
 * Uso: `val vm = viewModelConRepositorio { repo -> LoginViewModel(repo) }`
 */
@Composable
inline fun <reified VM : ViewModel> viewModelConRepositorio(
    crossinline crear: (Repositorio) -> VM,
): VM {
    val app = LocalContext.current.applicationContext as SemaxelApp
    val repositorio = app.contenedor.repositorio
    return viewModel<VM>(factory = viewModelFactory { initializer<VM> { crear(repositorio) } })
}
