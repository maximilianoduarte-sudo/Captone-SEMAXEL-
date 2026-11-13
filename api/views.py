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
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import EsTecnicoHabilitado, tecnico_habilitado
from .serializers import LoginSerializer, TecnicoSerializer


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
