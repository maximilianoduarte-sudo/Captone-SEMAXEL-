package cl.semaxel.tecnico.dispositivo

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.net.Uri
import androidx.core.content.FileProvider
import androidx.exifinterface.media.ExifInterface
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.io.File

/** Preparación de fotos antes de subirlas. */
object Imagenes {

    /** Lado mayor máximo de la foto subida: suficiente como evidencia y liviana para datos móviles. */
    private const val LADO_MAXIMO = 1600
    private const val CALIDAD_JPEG = 85

    /**
     * Crea un archivo temporal y su Uri para que la app de cámara guarde ahí la foto.
     * Los archivos quedan en la caché de la app (carpeta "fotos").
     */
    fun nuevoArchivoParaCamara(context: Context): Uri {
        val carpeta = File(context.cacheDir, "fotos").apply { mkdirs() }
        val archivo = File.createTempFile("evidencia_", ".jpg", carpeta)
        return FileProvider.getUriForFile(context, "${context.packageName}.archivos", archivo)
    }

    /**
     * Lee la foto, la endereza según la orientación que guardó la cámara (EXIF),
     * la reduce a un máximo de [LADO_MAXIMO] px y la comprime en JPEG.
     * Así una foto de 10 MB queda en unos cientos de KB (el servidor acepta hasta 8 MB).
     */
    suspend fun prepararParaSubir(context: Context, uri: Uri): ByteArray? = withContext(Dispatchers.IO) {
        val resolver = context.contentResolver
        val limites = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        resolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, limites) }
        if (limites.outWidth <= 0 || limites.outHeight <= 0) return@withContext null

        var muestreo = 1
        while (maxOf(limites.outWidth, limites.outHeight) / (muestreo * 2) >= LADO_MAXIMO) muestreo *= 2
        val opciones = BitmapFactory.Options().apply { inSampleSize = muestreo }
        val original = resolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, opciones) }
            ?: return@withContext null

        val rotacion = resolver.openInputStream(uri)?.use {
            when (ExifInterface(it).getAttributeInt(ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL)) {
                ExifInterface.ORIENTATION_ROTATE_90 -> 90f
                ExifInterface.ORIENTATION_ROTATE_180 -> 180f
                ExifInterface.ORIENTATION_ROTATE_270 -> 270f
                else -> 0f
            }
        } ?: 0f

        val escala = minOf(1f, LADO_MAXIMO.toFloat() / maxOf(original.width, original.height))
        val matriz = Matrix().apply {
            postScale(escala, escala)
            postRotate(rotacion)
        }
        val final = Bitmap.createBitmap(original, 0, 0, original.width, original.height, matriz, true)
        ByteArrayOutputStream().use { salida ->
            final.compress(Bitmap.CompressFormat.JPEG, CALIDAD_JPEG, salida)
            salida.toByteArray()
        }
    }
}
