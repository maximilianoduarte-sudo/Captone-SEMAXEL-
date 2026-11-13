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


class SucursalOfertaSerializer(serializers.Serializer):
    """Datos del local que el técnico necesita para decidir si va."""

    nombre = serializers.CharField()
    direccion = serializers.CharField()
    comuna = serializers.CharField()
    ciudad = serializers.CharField()
    region = serializers.CharField()
    telefono = serializers.CharField()


class OfertaSerializer(serializers.Serializer):
    """Oferta de trabajo tal como la ve el técnico en la app.

    No incluye el número interno del ticket (p. ej. SEMAXEL-00001): igual que
    en la web, el técnico trabaja con ofertas, no con la administración de
    tickets.
    """

    id = serializers.IntegerField()
    estado = serializers.CharField()
    titulo = serializers.CharField(source="ticket.titulo")
    descripcion = serializers.CharField(source="ticket.descripcion")
    prioridad = serializers.CharField(source="ticket.prioridad")
    prioridad_display = serializers.CharField(source="ticket.get_prioridad_display")
    categoria = serializers.CharField(source="ticket.categoria.nombre")
    especialidad = serializers.CharField(
        source="ticket.categoria.especialidad.nombre", default=None
    )
    empresa = serializers.CharField(source="ticket.sucursal.empresa.nombre")
    sucursal = SucursalOfertaSerializer(source="ticket.sucursal")
    fecha_publicacion = serializers.DateTimeField()
    fecha_vencimiento = serializers.DateTimeField()
    observaciones = serializers.CharField()


class OrdenSerializer(serializers.Serializer):
    """Orden de trabajo del técnico (sección Mis trabajos de la app)."""

    id = serializers.IntegerField()
    estado = serializers.CharField()
    estado_display = serializers.CharField(source="get_estado_display")
    titulo = serializers.CharField(source="ticket.titulo")
    descripcion = serializers.CharField(source="ticket.descripcion")
    prioridad = serializers.CharField(source="ticket.prioridad")
    prioridad_display = serializers.CharField(source="ticket.get_prioridad_display")
    categoria = serializers.CharField(source="ticket.categoria.nombre")
    empresa = serializers.CharField(source="ticket.sucursal.empresa.nombre")
    sucursal = SucursalOfertaSerializer(source="ticket.sucursal")
    diagnostico = serializers.CharField()
    trabajo_realizado = serializers.CharField()
    observaciones = serializers.CharField()
    costo_estimado = serializers.DecimalField(max_digits=12, decimal_places=2)
    costo_final = serializers.DecimalField(max_digits=12, decimal_places=2)
    fecha_asignacion = serializers.DateTimeField(source="fecha_creacion")
    fecha_inicio = serializers.DateTimeField()
    fecha_fin = serializers.DateTimeField()
    acciones = serializers.SerializerMethodField()

    def get_acciones(self, orden):
        """Qué botones mostrar en la app según el estado: "iniciar" y/o "resolver"."""
        from tickets.models import OrdenTrabajo

        return {
            OrdenTrabajo.Estado.ASIGNADA: ["iniciar"],
            OrdenTrabajo.Estado.EN_EJECUCION: ["resolver"],
        }.get(orden.estado, [])


class IniciarOrdenSerializer(serializers.Serializer):
    """Datos para iniciar el trabajo (ASIGNADA -> EN_EJECUCION)."""

    diagnostico = serializers.CharField()
    costo_estimado = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False
    )


class ResolverOrdenSerializer(serializers.Serializer):
    """Datos para marcar el trabajo como resuelto (EN_EJECUCION -> RESUELTA)."""

    trabajo_realizado = serializers.CharField()
    observaciones = serializers.CharField(required=False, allow_blank=True)
    costo_final = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False
    )
