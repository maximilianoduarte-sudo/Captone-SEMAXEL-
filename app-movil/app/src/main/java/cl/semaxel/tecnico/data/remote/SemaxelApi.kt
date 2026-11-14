package cl.semaxel.tecnico.data.remote

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * Operaciones de la API REST de SEMAXEL (/api/v1/), una función por endpoint.
 *
 * Retrofit genera la implementación. El token se agrega solo en
 * [ClienteApi] (cabecera "Authorization: Token <token>"), así que aquí no aparece.
 */
interface SemaxelApi {

    // ---------------------------------------------------------- sesión y perfil

    @POST("api/v1/auth/login/")
    suspend fun login(@Body peticion: LoginPeticion): LoginRespuesta

    @POST("api/v1/auth/logout/")
    suspend fun logout(@Body peticion: LogoutPeticion): Response<Unit>

    @GET("api/v1/auth/perfil/")
    suspend fun perfil(): Tecnico

    @PATCH("api/v1/auth/perfil/")
    suspend fun cambiarDisponibilidad(@Body peticion: DisponibilidadPeticion): Tecnico

    @POST("api/v1/dispositivos/")
    suspend fun registrarDispositivo(@Body peticion: DispositivoPeticion): Dispositivo

    // ---------------------------------------------------------- inicio y ofertas

    @GET("api/v1/inicio/")
    suspend fun inicio(): Inicio

    @GET("api/v1/ofertas/")
    suspend fun ofertas(): List<Oferta>

    @GET("api/v1/ofertas/{id}/")
    suspend fun oferta(@Path("id") id: Int): Oferta

    @POST("api/v1/ofertas/{id}/tomar/")
    suspend fun tomarOferta(@Path("id") id: Int): TomarOfertaRespuesta

    // ---------------------------------------------------------- mis trabajos

    @GET("api/v1/ordenes/")
    suspend fun ordenes(@Query("estado") estado: String? = null): List<Orden>

    @GET("api/v1/ordenes/{id}/")
    suspend fun orden(@Path("id") id: Int): Orden

    @POST("api/v1/ordenes/{id}/iniciar/")
    suspend fun iniciar(@Path("id") id: Int, @Body peticion: IniciarPeticion): Orden

    @POST("api/v1/ordenes/{id}/resolver/")
    suspend fun resolver(@Path("id") id: Int, @Body peticion: ResolverPeticion): Orden

    @POST("api/v1/ordenes/{id}/llegada/")
    suspend fun registrarLlegada(@Path("id") id: Int, @Body peticion: LlegadaPeticion): Orden

    // ---------------------------------------------------------- evidencias y firma

    @Multipart
    @POST("api/v1/ordenes/{id}/evidencias/")
    suspend fun subirEvidencia(
        @Path("id") id: Int,
        @Part imagen: MultipartBody.Part,
        @Part("descripcion") descripcion: RequestBody,
    ): Evidencia

    @DELETE("api/v1/ordenes/{id}/evidencias/{evidenciaId}/")
    suspend fun eliminarEvidencia(
        @Path("id") id: Int,
        @Path("evidenciaId") evidenciaId: Int,
    ): Response<Unit>

    @Multipart
    @POST("api/v1/ordenes/{id}/firma/")
    suspend fun registrarFirma(
        @Path("id") id: Int,
        @Part imagen: MultipartBody.Part,
        @Part("nombre_firmante") nombreFirmante: RequestBody,
    ): Orden
}
