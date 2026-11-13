"""Vistas de la API de la app móvil del técnico.

Las vistas son delgadas: validan la entrada con un serializer, llaman al
servicio que aplica la regla de negocio (el mismo que usa la web) y traducen
el resultado a una respuesta HTTP. La documentación OpenAPI (Swagger) se
genera desde las anotaciones @extend_schema de cada vista.

Autenticación: POST /auth/login/ entrega un token; todas las demás
operaciones exigen la cabecera "Authorization: Token <token>".
"""
from django.contrib.auth import authenticate
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ofertas.models import OfertaTicket
from ofertas.services import OfertaNoTomable, ofertas_disponibles_para, tomar_oferta
from sucursales.models import HorarioSucursal
from tecnicos.services import DisponibilidadNoPermitida, cambiar_disponibilidad
from tickets.models import EvidenciaOrden, OrdenTrabajo
from tickets.services import (
    ESTADOS_ACTIVOS,
    ReglaNoCumplida,
    agregar_evidencia,
    cambiar_estado_orden,
    eliminar_evidencia,
    registrar_firma,
    registrar_llegada,
)

from .models import Dispositivo
from .permissions import EsTecnicoHabilitado, tecnico_habilitado
from .serializers import (
    DisponibilidadSerializer,
    DispositivoSerializer,
    ErrorSerializer,
    EvidenciaSerializer,
    FirmaEntradaSerializer,
    IniciarOrdenSerializer,
    InicioSerializer,
    LoginRespuestaSerializer,
    LoginSerializer,
    LogoutSerializer,
    OfertaSerializer,
    OrdenSerializer,
    RegistrarLlegadaSerializer,
    ResolverOrdenSerializer,
    SubirEvidenciaSerializer,
    TecnicoSerializer,
    TomarOfertaRespuestaSerializer,
)

# Respuestas de error comunes, para la documentación.
R401 = OpenApiResponse(ErrorSerializer, description="Falta el token o no es válido.")
R403 = OpenApiResponse(ErrorSerializer, description="No es un técnico habilitado.")
R404 = OpenApiResponse(ErrorSerializer, description="No existe o no le corresponde.")
R409 = OpenApiResponse(
    ErrorSerializer, description="La regla de negocio no lo permite; ver `codigo`."
)
R400 = OpenApiResponse(description="Datos inválidos: un mensaje por cada campo con error.")


def _conflicto(error):
    """Respuesta 409 a partir de un error de regla de negocio (mensaje + código)."""
    return Response(
        {"detail": error.mensaje, "codigo": error.codigo},
        status=status.HTTP_409_CONFLICT,
    )


# =========================================================== sesión y perfil

class LoginView(APIView):
    """Inicio de sesión: entrega un token a un técnico habilitado."""

    # Es la única operación abierta: todavía no hay token que revisar.
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Sesión"],
        summary="Iniciar sesión",
        description=(
            "Usuario y contraseña (los mismos de la web). Solo los técnicos con "
            "cuenta activa, rol TECNICO y perfil no INACTIVO reciben token. "
            "Si el técnico ya tenía token, se reutiliza."
        ),
        request=LoginSerializer,
        responses={
            200: LoginRespuestaSerializer,
            400: OpenApiResponse(ErrorSerializer, description="Usuario o contraseña incorrectos."),
            403: R403,
        },
        auth=[],
    )
    def post(self, request):
        datos = LoginSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=datos.validated_data["username"],
            password=datos.validated_data["password"],
        )
        if user is None:
            # Mismo mensaje si falla el usuario o la contraseña, para no
            # revelar qué usuarios existen.
            return Response(
                {"detail": "Usuario o contraseña incorrectos."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tecnico = tecnico_habilitado(user)
        if tecnico is None:
            return Response(
                {"detail": EsTecnicoHabilitado.message},
                status=status.HTTP_403_FORBIDDEN,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "tecnico": TecnicoSerializer(tecnico).data})


class LogoutView(APIView):
    """Cierre de sesión: borra el token (y, si se indica, el dispositivo)."""

    @extend_schema(
        tags=["Sesión"],
        summary="Cerrar sesión",
        description=(
            "Borra el token: deja de servir. Si se envía `token_dispositivo`, ese "
            "celular deja de recibir notificaciones. Basta con estar autenticado "
            "(aunque el técnico haya sido desactivado, puede cerrar su sesión)."
        ),
        request=LogoutSerializer,
        responses={204: None, 401: R401},
    )
    def post(self, request):
        datos = LogoutSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        token_dispositivo = datos.validated_data.get("token_dispositivo")
        if token_dispositivo:
            Dispositivo.objects.filter(usuario=request.user, token=token_dispositivo).delete()
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PerfilView(APIView):
    """Perfil del técnico y cambio de disponibilidad."""

    permission_classes = [EsTecnicoHabilitado]

    @extend_schema(
        tags=["Perfil"],
        summary="Ver mi perfil",
        responses={200: TecnicoSerializer, 401: R401, 403: R403},
    )
    def get(self, request):
        return Response(TecnicoSerializer(request.user.tecnico).data)

    @extend_schema(
        tags=["Perfil"],
        summary="Cambiar mi disponibilidad",
        description=(
            "El técnico elige DISPONIBLE o NO_DISPONIBLE. No se puede cambiar "
            "mientras está OCUPADO (tiene órdenes activas): el sistema lo libera "
            "al terminarlas. Códigos 409: `tecnico_ocupado`, `tecnico_inactivo`."
        ),
        request=DisponibilidadSerializer,
        responses={200: TecnicoSerializer, 400: R400, 401: R401, 403: R403, 409: R409},
    )
    def patch(self, request):
        datos = DisponibilidadSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        try:
            tecnico = cambiar_disponibilidad(request.user.tecnico, datos.validated_data["estado"])
        except DisponibilidadNoPermitida as error:
            return _conflicto(error)
        return Response(TecnicoSerializer(tecnico).data)


class DispositivosView(APIView):
    """Registro del celular para recibir notificaciones push."""

    permission_classes = [EsTecnicoHabilitado]

    @extend_schema(
        tags=["Notificaciones"],
        summary="Registrar este celular",
        description=(
            "La app envía el token de Firebase Cloud Messaging (FCM) al iniciar "
            "sesión y cada vez que Firebase lo renueva. Si el token ya existía, "
            "se actualiza y queda a nombre de este técnico (201 si es nuevo, 200 "
            "si ya estaba)."
        ),
        request=DispositivoSerializer,
        responses={200: DispositivoSerializer, 201: DispositivoSerializer, 400: R400,
                   401: R401, 403: R403},
    )
    def post(self, request):
        datos = DispositivoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        dispositivo, creado = Dispositivo.objects.update_or_create(
            token=datos.validated_data["token"],
            defaults={
                "usuario": request.user,
                "plataforma": datos.validated_data.get("plataforma", Dispositivo.Plataforma.ANDROID),
            },
        )
        return Response(
            DispositivoSerializer(dispositivo).data,
            status=status.HTTP_201_CREATED if creado else status.HTTP_200_OK,
        )


class DispositivoDetalleView(APIView):
    permission_classes = [EsTecnicoHabilitado]

    @extend_schema(
        tags=["Notificaciones"],
        summary="Quitar un celular",
        responses={204: None, 401: R401, 403: R403, 404: R404},
    )
    def delete(self, request, dispositivo_id):
        get_object_or_404(Dispositivo, pk=dispositivo_id, usuario=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =========================================================== inicio y ofertas

def _ordenes_del_tecnico(user):
    """Órdenes del técnico autenticado, con todo lo que muestra la app."""
    return (
        OrdenTrabajo.objects.filter(tecnico__usuario=user)
        .select_related("ticket__sucursal__empresa", "ticket__categoria", "firma")
        .prefetch_related(
            "evidencias",
            Prefetch("ticket__sucursal__horarios", queryset=HorarioSucursal.objects.order_by("dia_semana")),
        )
        .order_by("-fecha_creacion")
    )


def _con_horarios(ofertas):
    return ofertas.prefetch_related(
        Prefetch("ticket__sucursal__horarios", queryset=HorarioSucursal.objects.order_by("dia_semana"))
    )


class InicioView(APIView):
    """Resumen para la pantalla Inicio de la app."""

    permission_classes = [EsTecnicoHabilitado]

    @extend_schema(
        tags=["Inicio"],
        summary="Resumen de inicio",
        description="Perfil, cantidad de ofertas que puede tomar y sus órdenes activas.",
        responses={200: InicioSerializer, 401: R401, 403: R403},
    )
    def get(self, request):
        tecnico = request.user.tecnico
        activas = list(_ordenes_del_tecnico(request.user).filter(estado__in=ESTADOS_ACTIVOS))
        datos = {
            "tecnico": tecnico,
            "ofertas_disponibles": ofertas_disponibles_para(tecnico, usuario=request.user).count(),
            "ordenes_activas": len(activas),
            "ordenes": activas,
        }
        return Response(InicioSerializer(datos, context={"request": request}).data)


class OfertasDisponiblesView(APIView):
    permission_classes = [EsTecnicoHabilitado]

    @extend_schema(
        tags=["Ofertas"],
        summary="Ofertas que puedo tomar",
        description=(
            "Ofertas DISPONIBLES cuya categoría exige una especialidad que el "
            "técnico tiene (historia HU-09). Antes de responder se expiran las "
            "vencidas, igual que en la web."
        ),
        responses={200: OfertaSerializer(many=True), 401: R401, 403: R403},
    )
    def get(self, request):
        ofertas = _con_horarios(ofertas_disponibles_para(request.user.tecnico, usuario=request.user))
        return Response(OfertaSerializer(ofertas, many=True).data)


class OfertaDetalleView(APIView):
    permission_classes = [EsTecnicoHabilitado]

    @extend_schema(
        tags=["Ofertas"],
        summary="Detalle de una oferta",
        description=(
            "Visible si está entre las que puede tomar o si ya la tomó él. "
            "Cualquier otra responde 404 (no se revela que existe)."
        ),
        responses={200: OfertaSerializer, 401: R401, 403: R403, 404: R404},
    )
    def get(self, request, oferta_id):
        tecnico = request.user.tecnico
        disponibles = ofertas_disponibles_para(tecnico, usuario=request.user)
        visibles = _con_horarios(
            OfertaTicket.objects.filter(
                Q(pk__in=disponibles.values("pk")) | Q(tecnico=tecnico)
            ).select_related("ticket__sucursal__empresa", "ticket__categoria__especialidad")
        )
        oferta = get_object_or_404(visibles, pk=oferta_id)
        return Response(OfertaSerializer(oferta).data)


class TomarOfertaView(APIView):
    permission_classes = [EsTecnicoHabilitado]

    @extend_schema(
        tags=["Ofertas"],
        summary="Tomar una oferta",
        description=(
            "Usa la misma regla que la web (`ofertas.services.tomar_oferta`). "
            "Crea la orden de trabajo ASIGNADA y deja al técnico OCUPADO. "
            "Códigos 409: `no_disponible`, `vencida`, `ticket_no_permite`, "
            "`sin_especialidad`, `especialidad_no_coincide`."
        ),
        request=None,
        responses={201: TomarOfertaRespuestaSerializer, 401: R401, 403: R403, 404: R404, 409: R409},
    )
    def post(self, request, oferta_id):
        oferta = get_object_or_404(OfertaTicket, pk=oferta_id)
        try:
            orden = tomar_oferta(oferta, request.user.tecnico, usuario=request.user)
        except OfertaNoTomable as error:
            return _conflicto(error)
        oferta = _con_horarios(OfertaTicket.objects.filter(pk=oferta.pk)).get()
        return Response(
            {"orden_id": orden.pk, "oferta": OfertaSerializer(oferta).data},
            status=status.HTTP_201_CREATED,
        )


# =========================================================== mis trabajos

class _OrdenBaseView(APIView):
    """Utilidades comunes a las vistas de una orden del técnico."""

    permission_classes = [EsTecnicoHabilitado]

    def obtener_orden(self, request, orden_id):
        # Las órdenes de otros técnicos responden 404: no se revela que existen.
        return get_object_or_404(_ordenes_del_tecnico(request.user), pk=orden_id)

    def responder_orden(self, request, orden_id, codigo=status.HTTP_200_OK):
        orden = _ordenes_del_tecnico(request.user).get(pk=orden_id)
        return Response(OrdenSerializer(orden, context={"request": request}).data, status=codigo)


class MisOrdenesView(_OrdenBaseView):
    @extend_schema(
        tags=["Mis trabajos"],
        summary="Mis órdenes de trabajo",
        parameters=[
            OpenApiParameter(
                "estado", str, required=False,
                enum=OrdenTrabajo.Estado.values,
                description="Filtra por estado. Un estado desconocido responde 400.",
            )
        ],
        responses={200: OrdenSerializer(many=True), 400: R400, 401: R401, 403: R403},
    )
    def get(self, request):
        ordenes = _ordenes_del_tecnico(request.user)
        estado = request.query_params.get("estado")
        if estado:
            if estado not in OrdenTrabajo.Estado.values:
                return Response(
                    {"detail": f"Estado desconocido: {estado}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ordenes = ordenes.filter(estado=estado)
        return Response(OrdenSerializer(ordenes, many=True, context={"request": request}).data)


class OrdenDetalleView(_OrdenBaseView):
    @extend_schema(
        tags=["Mis trabajos"],
        summary="Detalle de una orden",
        description=(
            "Incluye llegada, tiempo de respuesta frente al SLA, fotos, firma y "
            "`acciones`: los botones que la app debe mostrar."
        ),
        responses={200: OrdenSerializer, 401: R401, 403: R403, 404: R404},
    )
    def get(self, request, orden_id):
        orden = self.obtener_orden(request, orden_id)
        return Response(OrdenSerializer(orden, context={"request": request}).data)


class _TransicionOrdenView(_OrdenBaseView):
    """Base de iniciar y resolver: valida los datos y llama al servicio común."""

    destino = None
    serializer_class = None

    def post(self, request, orden_id):
        orden = self.obtener_orden(request, orden_id)
        datos = self.serializer_class(data=request.data)
        datos.is_valid(raise_exception=True)
        try:
            cambiar_estado_orden(orden, self.destino, request.user, datos=datos.validated_data)
        except ReglaNoCumplida as error:
            return _conflicto(error)
        return self.responder_orden(request, orden.pk)


_DESC_TRANSICION = (
    "Usa la misma regla que la web (`tickets.services.cambiar_estado_orden`). "
    "Códigos 409: `sin_cambio`, `transicion_invalida`, `sin_permiso`."
)


@extend_schema(
    tags=["Mis trabajos"],
    summary="Iniciar el trabajo",
    description="ASIGNADA → EN_EJECUCION. Exige diagnóstico. " + _DESC_TRANSICION,
    request=IniciarOrdenSerializer,
    responses={200: OrdenSerializer, 400: R400, 401: R401, 403: R403, 404: R404, 409: R409},
)
class IniciarOrdenView(_TransicionOrdenView):
    destino = OrdenTrabajo.Estado.EN_EJECUCION
    serializer_class = IniciarOrdenSerializer


@extend_schema(
    tags=["Mis trabajos"],
    summary="Marcar como resuelta",
    description=(
        "EN_EJECUCION → RESUELTA. Exige el trabajo realizado. El ticket pasa a "
        "RESUELTO y el técnico queda disponible si no tiene otras órdenes "
        "activas. El cierre lo hace el encargado en la web. " + _DESC_TRANSICION
    ),
    request=ResolverOrdenSerializer,
    responses={200: OrdenSerializer, 400: R400, 401: R401, 403: R403, 404: R404, 409: R409},
)
class ResolverOrdenView(_TransicionOrdenView):
    destino = OrdenTrabajo.Estado.RESUELTA
    serializer_class = ResolverOrdenSerializer


class RegistrarLlegadaView(_OrdenBaseView):
    @extend_schema(
        tags=["Mis trabajos"],
        summary="Registrar llegada con GPS",
        description=(
            "Guarda la hora y la posición del técnico. Si la sucursal tiene "
            "coordenadas, calcula la distancia y marca la llegada como verificada "
            "cuando está dentro del radio permitido (150 m por defecto). Con esto "
            "se mide el tiempo de respuesta del SLA. Se registra una sola vez. "
            "Códigos 409: `orden_no_activa`, `llegada_ya_registrada`."
        ),
        request=RegistrarLlegadaSerializer,
        responses={201: OrdenSerializer, 400: R400, 401: R401, 403: R403, 404: R404, 409: R409},
    )
    def post(self, request, orden_id):
        orden = self.obtener_orden(request, orden_id)
        datos = RegistrarLlegadaSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        try:
            registrar_llegada(
                orden,
                request.user,
                datos.validated_data["latitud"],
                datos.validated_data["longitud"],
                datos.validated_data.get("precision_m"),
            )
        except ReglaNoCumplida as error:
            return _conflicto(error)
        return self.responder_orden(request, orden.pk, status.HTTP_201_CREATED)


class EvidenciasView(_OrdenBaseView):
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["Evidencias"],
        summary="Fotos de la orden",
        responses={200: EvidenciaSerializer(many=True), 401: R401, 403: R403, 404: R404},
    )
    def get(self, request, orden_id):
        orden = self.obtener_orden(request, orden_id)
        return Response(
            EvidenciaSerializer(orden.evidencias.all(), many=True, context={"request": request}).data
        )

    @extend_schema(
        tags=["Evidencias"],
        summary="Subir una foto",
        description=(
            "Envío multipart/form-data con el campo `imagen` (JPG o PNG, máximo "
            "8 MB) y, opcionalmente, `descripcion`. Se acepta mientras la orden "
            "está asignada, en ejecución o resuelta, hasta 10 fotos. "
            "Códigos 409: `orden_no_activa`, `limite_evidencias`."
        ),
        request={"multipart/form-data": SubirEvidenciaSerializer},
        responses={201: EvidenciaSerializer, 400: R400, 401: R401, 403: R403, 404: R404, 409: R409},
    )
    def post(self, request, orden_id):
        orden = self.obtener_orden(request, orden_id)
        datos = SubirEvidenciaSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        try:
            evidencia = agregar_evidencia(
                orden, request.user, datos.validated_data["imagen"],
                datos.validated_data.get("descripcion", ""),
            )
        except ReglaNoCumplida as error:
            return _conflicto(error)
        return Response(
            EvidenciaSerializer(evidencia, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class EvidenciaDetalleView(_OrdenBaseView):
    @extend_schema(
        tags=["Evidencias"],
        summary="Eliminar una foto",
        description=(
            "Solo quien la subió y antes del cierre de la orden. "
            "Códigos 409: `orden_no_activa`, `sin_permiso`."
        ),
        responses={204: None, 401: R401, 403: R403, 404: R404, 409: R409},
    )
    def delete(self, request, orden_id, evidencia_id):
        orden = self.obtener_orden(request, orden_id)
        evidencia = get_object_or_404(EvidenciaOrden, pk=evidencia_id, orden=orden)
        try:
            eliminar_evidencia(evidencia, request.user)
        except ReglaNoCumplida as error:
            return _conflicto(error)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FirmaView(_OrdenBaseView):
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["Evidencias"],
        summary="Registrar la firma de conformidad",
        description=(
            "El encargado firma en el celular del técnico. Envío multipart/form-data "
            "con `imagen` (PNG del trazo) y `nombre_firmante`. Una sola vez por "
            "orden, con la orden en ejecución o resuelta. "
            "Códigos 409: `orden_no_activa`, `firma_ya_registrada`."
        ),
        request={"multipart/form-data": FirmaEntradaSerializer},
        responses={201: OrdenSerializer, 400: R400, 401: R401, 403: R403, 404: R404, 409: R409},
    )
    def post(self, request, orden_id):
        orden = self.obtener_orden(request, orden_id)
        datos = FirmaEntradaSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        try:
            registrar_firma(
                orden, request.user, datos.validated_data["imagen"],
                datos.validated_data["nombre_firmante"],
            )
        except ReglaNoCumplida as error:
            return _conflicto(error)
        return self.responder_orden(request, orden.pk, status.HTTP_201_CREATED)
