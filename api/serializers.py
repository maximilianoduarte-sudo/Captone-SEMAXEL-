"""Formato JSON de lo que entra y sale de la API.

Los serializers de salida describen lo que recibe la app; los de entrada
validan lo que envía (tipos, rangos y campos obligatorios) antes de llegar a
los servicios, que aplican las reglas de negocio.
"""
from django.conf import settings
from rest_framework import serializers

from tecnicos.models import Tecnico
from tickets.models import EvidenciaOrden, OrdenTrabajo
from tickets.services import ESTADOS_ACTIVOS, ESTADOS_CON_EVIDENCIA, ESTADOS_PARA_FIRMAR

from .models import Dispositivo


def _url_absoluta(serializer, archivo):
    """URL completa del archivo (con dominio) para que la app pueda descargarlo."""
    if not archivo:
        return None
    request = serializer.context.get("request")
    return request.build_absolute_uri(archivo.url) if request else archivo.url


class ErrorSerializer(serializers.Serializer):
    """Cuerpo de los errores 403, 404 y 409."""

    detail = serializers.CharField(help_text="Mensaje para mostrar a la persona.")
    codigo = serializers.CharField(
        required=False, help_text="Código para que la app decida qué hacer (solo en 409)."
    )


# ---------------------------------------------------------------- sesión y perfil

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


class LoginRespuestaSerializer(serializers.Serializer):
    token = serializers.CharField()
    tecnico = TecnicoSerializer()


class LogoutSerializer(serializers.Serializer):
    token_dispositivo = serializers.CharField(
        required=False,
        help_text="Token FCM del celular, para dejar de enviarle notificaciones.",
    )


class DisponibilidadSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(
        choices=[(e.value, e.label) for e in Tecnico.ESTADOS_DISPONIBILIDAD]
    )


# ---------------------------------------------------------------- sucursal y ofertas

class HorarioSerializer(serializers.Serializer):
    dia_semana = serializers.IntegerField(help_text="0 = lunes … 6 = domingo.")
    dia = serializers.CharField(source="get_dia_semana_display")
    apertura = serializers.TimeField(source="hora_apertura", format="%H:%M")
    cierre = serializers.TimeField(source="hora_cierre", format="%H:%M")


class SucursalSerializer(serializers.Serializer):
    """Datos del local que el técnico necesita para ir y validar su llegada."""

    nombre = serializers.CharField()
    direccion = serializers.CharField()
    comuna = serializers.CharField()
    ciudad = serializers.CharField()
    region = serializers.CharField()
    telefono = serializers.CharField()
    latitud = serializers.DecimalField(max_digits=9, decimal_places=6, allow_null=True)
    longitud = serializers.DecimalField(max_digits=9, decimal_places=6, allow_null=True)
    horario = HorarioSerializer(source="horarios", many=True)


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
    sucursal = SucursalSerializer(source="ticket.sucursal")
    fecha_publicacion = serializers.DateTimeField()
    fecha_vencimiento = serializers.DateTimeField(allow_null=True)
    observaciones = serializers.CharField()


class TomarOfertaRespuestaSerializer(serializers.Serializer):
    orden_id = serializers.IntegerField()
    oferta = OfertaSerializer()


# ---------------------------------------------------------------- órdenes

class EvidenciaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = EvidenciaOrden
        fields = ["id", "url", "descripcion", "fecha_subida"]

    def get_url(self, evidencia) -> str:
        return _url_absoluta(self, evidencia.imagen)


class FirmaSerializer(serializers.Serializer):
    nombre_firmante = serializers.CharField()
    url = serializers.SerializerMethodField()
    fecha_firma = serializers.DateTimeField()

    def get_url(self, firma) -> str:
        return _url_absoluta(self, firma.imagen)


class LlegadaSerializer(serializers.Serializer):
    fecha = serializers.DateTimeField(source="fecha_llegada")
    latitud = serializers.DecimalField(source="llegada_latitud", max_digits=9, decimal_places=6)
    longitud = serializers.DecimalField(source="llegada_longitud", max_digits=9, decimal_places=6)
    precision_m = serializers.FloatField(source="llegada_precision_m", allow_null=True)
    distancia_m = serializers.IntegerField(
        source="llegada_distancia_m", allow_null=True,
        help_text="Distancia a la sucursal; null si la sucursal no tiene coordenadas.",
    )
    verificada = serializers.BooleanField(
        source="llegada_verificada", allow_null=True,
        help_text="true: dentro del radio; false: fuera; null: no verificable.",
    )


def _tiene_firma(orden):
    try:
        return orden.firma is not None
    except OrdenTrabajo.firma.RelatedObjectDoesNotExist:
        return False


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
    sucursal = SucursalSerializer(source="ticket.sucursal")
    diagnostico = serializers.CharField()
    trabajo_realizado = serializers.CharField()
    observaciones = serializers.CharField()
    costo_estimado = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    costo_final = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    fecha_asignacion = serializers.DateTimeField(source="fecha_creacion")
    fecha_inicio = serializers.DateTimeField(allow_null=True)
    fecha_fin = serializers.DateTimeField(allow_null=True)
    llegada = serializers.SerializerMethodField()
    tiempo_respuesta_minutos = serializers.IntegerField(
        allow_null=True, help_text="Desde la creación del ticket hasta la llegada."
    )
    sla_respuesta_minutos = serializers.IntegerField(
        allow_null=True, help_text="Tiempo máximo de respuesta según la política SLA."
    )
    sla_respuesta_cumplido = serializers.BooleanField(allow_null=True)
    evidencias = EvidenciaSerializer(many=True)
    firma = serializers.SerializerMethodField()
    acciones = serializers.SerializerMethodField()

    def get_llegada(self, orden) -> LlegadaSerializer(allow_null=True):
        return LlegadaSerializer(orden).data if orden.fecha_llegada else None

    def get_firma(self, orden) -> FirmaSerializer(allow_null=True):
        if not _tiene_firma(orden):
            return None
        return FirmaSerializer(orden.firma, context=self.context).data

    def get_acciones(self, orden) -> list[str]:
        """Botones que la app debe mostrar según el estado de la orden.

        Valores posibles: registrar_llegada, iniciar, resolver,
        subir_evidencia y firmar.
        """
        acciones = []
        if orden.estado in ESTADOS_ACTIVOS and not orden.fecha_llegada:
            acciones.append("registrar_llegada")
        if orden.estado == OrdenTrabajo.Estado.ASIGNADA:
            acciones.append("iniciar")
        if orden.estado == OrdenTrabajo.Estado.EN_EJECUCION:
            acciones.append("resolver")
        if (
            orden.estado in ESTADOS_CON_EVIDENCIA
            and len(orden.evidencias.all()) < settings.SEMAXEL_MAX_EVIDENCIAS_POR_ORDEN
        ):
            acciones.append("subir_evidencia")
        if orden.estado in ESTADOS_PARA_FIRMAR and not _tiene_firma(orden):
            acciones.append("firmar")
        return acciones


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


class RegistrarLlegadaSerializer(serializers.Serializer):
    """Posición GPS del técnico al llegar al local."""

    latitud = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=-90, max_value=90)
    longitud = serializers.DecimalField(
        max_digits=10, decimal_places=6, min_value=-180, max_value=180
    )
    precision_m = serializers.FloatField(
        required=False, min_value=0, help_text="Precisión informada por el GPS del teléfono."
    )


def _validar_tamano(imagen):
    maximo = settings.SEMAXEL_MAX_TAMANO_IMAGEN_MB
    if imagen.size > maximo * 1024 * 1024:
        raise serializers.ValidationError(f"La imagen supera el máximo de {maximo} MB.")
    return imagen


class SubirEvidenciaSerializer(serializers.Serializer):
    """Foto de evidencia (multipart/form-data). Se valida que sea una imagen real."""

    imagen = serializers.ImageField()
    descripcion = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_imagen(self, imagen):
        return _validar_tamano(imagen)


class FirmaEntradaSerializer(serializers.Serializer):
    """Firma de conformidad (multipart/form-data): imagen PNG del trazo y nombre."""

    imagen = serializers.ImageField()
    nombre_firmante = serializers.CharField(max_length=150)

    def validate_imagen(self, imagen):
        return _validar_tamano(imagen)


# ---------------------------------------------------------------- inicio y dispositivos

class InicioSerializer(serializers.Serializer):
    tecnico = TecnicoSerializer()
    ofertas_disponibles = serializers.IntegerField(help_text="Cuántas ofertas puede tomar.")
    ordenes_activas = serializers.IntegerField(help_text="Órdenes asignadas o en ejecución.")
    ordenes = OrdenSerializer(many=True, help_text="Sus órdenes activas, la más reciente primero.")


class DispositivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispositivo
        fields = ["id", "token", "plataforma", "fecha_registro"]
        read_only_fields = ["id", "fecha_registro"]
        # El token es único, pero registrarlo de nuevo no es un error:
        # la vista lo actualiza (por ejemplo, si cambió de usuario).
        extra_kwargs = {"token": {"validators": []}}
