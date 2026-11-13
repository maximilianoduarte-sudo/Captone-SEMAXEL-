"""Inicio de sesión de la app móvil del técnico.

Flujo:
1. La app envía usuario y contraseña a /api/v1/auth/login/.
2. Si son correctos y el usuario es un técnico habilitado, el servidor
   responde con un token y el perfil del técnico.
3. La app guarda el token y lo envía en cada petición siguiente, en la
   cabecera "Authorization: Token <token>".
4. Al cerrar sesión, /api/v1/auth/logout/ borra el token: deja de servir.
"""
from django.contrib.auth import authenticate
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ofertas.models import OfertaTicket
from ofertas.services import OfertaNoTomable, ofertas_disponibles_para, tomar_oferta

from .permissions import EsTecnicoHabilitado, tecnico_habilitado
from tickets.models import OrdenTrabajo
from tickets.services import TransicionNoPermitida, cambiar_estado_orden

from .serializers import (
    IniciarOrdenSerializer,
    LoginSerializer,
    OfertaSerializer,
    OrdenSerializer,
    ResolverOrdenSerializer,
    TecnicoSerializer,
)


class LoginView(APIView):
    """POST: entrega un token a un técnico habilitado."""

    # Es la única operación abierta: todavía no hay token que revisar.
    authentication_classes = []
    permission_classes = [AllowAny]

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

        # Un token por usuario: si ya tenía uno (otro inicio de sesión), se reutiliza.
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "tecnico": TecnicoSerializer(tecnico).data,
        })


class LogoutView(APIView):
    """POST: borra el token del técnico; la app deberá iniciar sesión de nuevo.

    Basta con estar autenticado: aunque el técnico haya sido desactivado
    mientras tenía la sesión abierta, debe poder cerrarla.
    """

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PerfilView(APIView):
    """GET: perfil del técnico dueño del token."""

    permission_classes = [EsTecnicoHabilitado]

    def get(self, request):
        return Response(TecnicoSerializer(request.user.tecnico).data)


class OfertasDisponiblesView(APIView):
    """GET: ofertas que el técnico puede tomar ahora (sección Ofertas de la app)."""

    permission_classes = [EsTecnicoHabilitado]

    def get(self, request):
        ofertas = ofertas_disponibles_para(request.user.tecnico, usuario=request.user)
        return Response(OfertaSerializer(ofertas, many=True).data)


class OfertaDetalleView(APIView):
    """GET: detalle de una oferta.

    El técnico puede ver una oferta si está entre las que puede tomar o si ya
    la tomó él. Cualquier otra responde 404 (no se revela que existe).
    """

    permission_classes = [EsTecnicoHabilitado]

    def get(self, request, oferta_id):
        tecnico = request.user.tecnico
        disponibles = ofertas_disponibles_para(tecnico, usuario=request.user)
        visibles = OfertaTicket.objects.filter(
            Q(pk__in=disponibles.values("pk")) | Q(tecnico=tecnico)
        ).select_related("ticket__sucursal__empresa", "ticket__categoria__especialidad")
        oferta = get_object_or_404(visibles, pk=oferta_id)
        return Response(OfertaSerializer(oferta).data)


class TomarOfertaView(APIView):
    """POST: el técnico toma la oferta y se crea su orden de trabajo.

    Usa la misma función que la web (ofertas.services.tomar_oferta).
    Respuestas:
    - 201: tomada; incluye el id de la orden de trabajo creada.
    - 404: la oferta no existe.
    - 409: no se pudo tomar (ya la tomó otro, venció, especialidad distinta...).
      El cuerpo trae "detail" (mensaje para mostrar) y "codigo" (para la app).
    """

    permission_classes = [EsTecnicoHabilitado]

    def post(self, request, oferta_id):
        oferta = get_object_or_404(OfertaTicket, pk=oferta_id)
        try:
            orden = tomar_oferta(oferta, request.user.tecnico, usuario=request.user)
        except OfertaNoTomable as error:
            return Response(
                {"detail": error.mensaje, "codigo": error.codigo},
                status=status.HTTP_409_CONFLICT,
            )
        oferta.refresh_from_db()
        return Response(
            {"orden_id": orden.pk, "oferta": OfertaSerializer(oferta).data},
            status=status.HTTP_201_CREATED,
        )


def _ordenes_del_tecnico(user):
    """Órdenes del técnico autenticado, con los datos que muestra la app."""
    return (
        OrdenTrabajo.objects.filter(tecnico__usuario=user)
        .select_related("ticket__sucursal__empresa", "ticket__categoria")
        .order_by("-fecha_creacion")
    )


class MisOrdenesView(APIView):
    """GET: órdenes del técnico (sección Mis trabajos).

    Filtro opcional: ?estado=ASIGNADA (o EN_EJECUCION, RESUELTA, CERRADA,
    CANCELADA). Un estado que no existe responde 400.
    """

    permission_classes = [EsTecnicoHabilitado]

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
        return Response(OrdenSerializer(ordenes, many=True).data)


class OrdenDetalleView(APIView):
    """GET: detalle de una orden del técnico. Las órdenes ajenas responden 404."""

    permission_classes = [EsTecnicoHabilitado]

    def get(self, request, orden_id):
        orden = get_object_or_404(_ordenes_del_tecnico(request.user), pk=orden_id)
        return Response(OrdenSerializer(orden).data)


class _TransicionOrdenView(APIView):
    """Base de iniciar y resolver: valida los datos y llama al servicio común.

    Respuestas: 200 con la orden actualizada; 400 si faltan datos; 404 si la
    orden no es suya; 409 si el estado actual no permite la acción.
    """

    permission_classes = [EsTecnicoHabilitado]
    destino = None
    serializer_class = None

    def post(self, request, orden_id):
        orden = get_object_or_404(_ordenes_del_tecnico(request.user), pk=orden_id)
        datos = self.serializer_class(data=request.data)
        datos.is_valid(raise_exception=True)
        try:
            cambiar_estado_orden(orden, self.destino, request.user, datos=datos.validated_data)
        except TransicionNoPermitida as error:
            return Response(
                {"detail": error.mensaje, "codigo": error.codigo},
                status=status.HTTP_409_CONFLICT,
            )
        orden = _ordenes_del_tecnico(request.user).get(pk=orden.pk)
        return Response(OrdenSerializer(orden).data)


class IniciarOrdenView(_TransicionOrdenView):
    """POST: el técnico inicia el trabajo (exige diagnóstico)."""

    destino = OrdenTrabajo.Estado.EN_EJECUCION
    serializer_class = IniciarOrdenSerializer


class ResolverOrdenView(_TransicionOrdenView):
    """POST: el técnico marca el trabajo como resuelto (exige el trabajo realizado)."""

    destino = OrdenTrabajo.Estado.RESUELTA
    serializer_class = ResolverOrdenSerializer
