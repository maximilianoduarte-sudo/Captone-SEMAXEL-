package cl.semaxel.tecnico.dispositivo

import android.Manifest
import android.annotation.SuppressLint
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.location.Location
import android.net.Uri
import androidx.core.content.ContextCompat
import cl.semaxel.tecnico.data.remote.Sucursal
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import kotlinx.coroutines.tasks.await

/** Acceso al GPS del celular. */
object Ubicacion {

    val PERMISOS = arrayOf(
        Manifest.permission.ACCESS_FINE_LOCATION,
        Manifest.permission.ACCESS_COARSE_LOCATION,
    )

    fun tienePermiso(context: Context): Boolean = PERMISOS.any {
        ContextCompat.checkSelfPermission(context, it) == PackageManager.PERMISSION_GRANTED
    }

    /**
     * Pide una posición actual (no la última guardada), con alta precisión.
     * Devuelve null si el GPS está apagado o no responde.
     * Quien la llame debe haber comprobado antes el permiso.
     */
    @SuppressLint("MissingPermission")
    suspend fun actual(context: Context): Location? {
        if (!tienePermiso(context)) return null
        val cliente = LocationServices.getFusedLocationProviderClient(context)
        val cancelacion = CancellationTokenSource()
        return try {
            cliente.getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, cancelacion.token).await()
        } catch (e: Exception) {
            null
        }
    }

    /**
     * Abre la sucursal en la app de mapas: por coordenadas si las tiene, si no
     * por dirección.
     */
    fun abrirEnMapa(context: Context, sucursal: Sucursal) {
        val consulta = if (sucursal.latitud != null && sucursal.longitud != null) {
            "${sucursal.latitud},${sucursal.longitud}(${sucursal.nombre})"
        } else {
            listOf(sucursal.direccion, sucursal.comuna, sucursal.ciudad).filter { it.isNotBlank() }.joinToString(", ")
        }
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse("geo:0,0?q=" + Uri.encode(consulta)))
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        try {
            context.startActivity(intent)
        } catch (e: ActivityNotFoundException) {
            // Sin app de mapas instalada: no se hace nada.
        }
    }
}
