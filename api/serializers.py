from rest_framework import serializers

from tecnicos.models import Tecnico


class LoginSerializer(serializers.Serializer):
    """Datos que envía la app para iniciar sesión (los mismos de la web)."""

    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)


class TecnicoSerializer(serializers.ModelSerializer):
    """Perfil del técnico que la app muestra en Inicio y Perfil."""

    username = serializers.CharField(source="usuario.username")
    nombre = serializers.CharField()
    correo = serializers.EmailField(source="usuario.email")
    estado = serializers.CharField()
    estado_display = serializers.CharField(source="get_estado_display")
    especialidades = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="nombre"
    )

    class Meta:
        model = Tecnico
        fields = [
            "id",
            "username",
            "nombre",
            "correo",
            "telefono",
            "estado",
            "estado_display",
            "especialidades",
        ]
