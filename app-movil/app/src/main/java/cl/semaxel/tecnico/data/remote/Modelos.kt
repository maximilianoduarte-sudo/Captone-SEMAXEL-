package cl.semaxel.tecnico.data.remote

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/*
 * Modelos del JSON de la API (ver docs/.../11 APP MOVIL/Guia_API_App_Movil.md).
 * Los nombres en snake_case del servidor se mapean con @SerialName.
 * Montos y coordenadas llegan como texto decimal para no perder precisión.
 */

// ------------------------------------------------------------- sesión y perfil

@Serializable
data class LoginPeticion(val username: String, val password: String)

@Serializable
data class LoginRespuesta(val token: String, val tecnico: Tecnico)

@Serializable
data class LogoutPeticion(
    @SerialName("token_dispositivo") val tokenDispositivo: String? = null,
)

@Serializable
data class Tecnico(
    val id: Int,
    val username: String,
    val nombre: String,
    val correo: String = "",
    val telefono: String = "",
    val estado: String,
    @SerialName("estado_display") val estadoDisplay: String = "",
    val especialidades: List<String> = emptyList(),
) {
    /** El técnico solo puede cambiar su disponibilidad si no está ocupado ni inactivo. */
    val puedeCambiarDisponibilidad: Boolean
        get() = estado == ESTADO_DISPONIBLE || estado == ESTADO_NO_DISPONIBLE

    companion object {
        const val ESTADO_DISPONIBLE = "DISPONIBLE"
        const val ESTADO_NO_DISPONIBLE = "NO_DISPONIBLE"
    }
}

@Serializable
data class DisponibilidadPeticion(val estado: String)

@Serializable
data class DispositivoPeticion(val token: String, val plataforma: String = "ANDROID")

@Serializable
data class Dispositivo(val id: Int, val token: String, val plataforma: String)

// ------------------------------------------------------------- sucursal y ofertas

@Serializable
data class Horario(
    @SerialName("dia_semana") val diaSemana: Int,
    val dia: String,
    val apertura: String,
    val cierre: String,
)

@Serializable
data class Sucursal(
    val nombre: String,
    val direccion: String = "",
    val comuna: String = "",
    val ciudad: String = "",
    val region: String = "",
    val telefono: String = "",
    val latitud: String? = null,
    val longitud: String? = null,
    val horario: List<Horario> = emptyList(),
)

@Serializable
data class Oferta(
    val id: Int,
    val estado: String,
    val titulo: String,
    val descripcion: String = "",
    val prioridad: String,
    @SerialName("prioridad_display") val prioridadDisplay: String = "",
    val categoria: String = "",
    val especialidad: String? = null,
    val empresa: String = "",
    val sucursal: Sucursal,
    @SerialName("fecha_publicacion") val fechaPublicacion: String,
    @SerialName("fecha_vencimiento") val fechaVencimiento: String? = null,
    val observaciones: String = "",
)

@Serializable
data class TomarOfertaRespuesta(
    @SerialName("orden_id") val ordenId: Int,
    val oferta: Oferta,
)

// ------------------------------------------------------------- órdenes

@Serializable
data class Llegada(
    val fecha: String,
    val latitud: String,
    val longitud: String,
    @SerialName("precision_m") val precisionM: Double? = null,
    @SerialName("distancia_m") val distanciaM: Int? = null,
    val verificada: Boolean? = null,
)

@Serializable
data class Evidencia(
    val id: Int,
    val url: String,
    val descripcion: String = "",
    @SerialName("fecha_subida") val fechaSubida: String,
)

@Serializable
data class Firma(
    @SerialName("nombre_firmante") val nombreFirmante: String,
    val url: String,
    @SerialName("fecha_firma") val fechaFirma: String,
)

@Serializable
data class Orden(
    val id: Int,
    val estado: String,
    @SerialName("estado_display") val estadoDisplay: String = "",
    val titulo: String,
    val descripcion: String = "",
    val prioridad: String,
    @SerialName("prioridad_display") val prioridadDisplay: String = "",
    val categoria: String = "",
    val empresa: String = "",
    val sucursal: Sucursal,
    val diagnostico: String = "",
    @SerialName("trabajo_realizado") val trabajoRealizado: String = "",
    val observaciones: String = "",
    @SerialName("costo_estimado") val costoEstimado: String? = null,
    @SerialName("costo_final") val costoFinal: String? = null,
    @SerialName("fecha_asignacion") val fechaAsignacion: String,
    @SerialName("fecha_inicio") val fechaInicio: String? = null,
    @SerialName("fecha_fin") val fechaFin: String? = null,
    val llegada: Llegada? = null,
    @SerialName("tiempo_respuesta_minutos") val tiempoRespuestaMinutos: Int? = null,
    @SerialName("sla_respuesta_minutos") val slaRespuestaMinutos: Int? = null,
    @SerialName("sla_respuesta_cumplido") val slaRespuestaCumplido: Boolean? = null,
    val evidencias: List<Evidencia> = emptyList(),
    val firma: Firma? = null,
    /** Botones que la app debe mostrar: registrar_llegada, iniciar, resolver, subir_evidencia, firmar. */
    val acciones: List<String> = emptyList(),
)

@Serializable
data class IniciarPeticion(
    val diagnostico: String,
    @SerialName("costo_estimado") val costoEstimado: String? = null,
)

@Serializable
data class ResolverPeticion(
    @SerialName("trabajo_realizado") val trabajoRealizado: String,
    val observaciones: String? = null,
    @SerialName("costo_final") val costoFinal: String? = null,
)

@Serializable
data class LlegadaPeticion(
    val latitud: String,
    val longitud: String,
    @SerialName("precision_m") val precisionM: Double? = null,
)

// ------------------------------------------------------------- inicio

@Serializable
data class Inicio(
    val tecnico: Tecnico,
    @SerialName("ofertas_disponibles") val ofertasDisponibles: Int,
    @SerialName("ordenes_activas") val ordenesActivas: Int,
    val ordenes: List<Orden> = emptyList(),
)
