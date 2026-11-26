from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views

app_name = "api"

urlpatterns = [
    # Sesión, perfil y notificaciones
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/perfil/", views.PerfilView.as_view(), name="perfil"),
    path("dispositivos/", views.DispositivosView.as_view(), name="dispositivos"),
    path("dispositivos/<int:dispositivo_id>/", views.DispositivoDetalleView.as_view(),
         name="dispositivo_detalle"),
    # Inicio y ofertas
    path("inicio/", views.InicioView.as_view(), name="inicio"),
    path("ofertas/", views.OfertasDisponiblesView.as_view(), name="ofertas"),
    path("ofertas/<int:oferta_id>/", views.OfertaDetalleView.as_view(), name="oferta_detalle"),
    path("ofertas/<int:oferta_id>/tomar/", views.TomarOfertaView.as_view(), name="tomar_oferta"),
    # Mis trabajos
    path("ordenes/", views.MisOrdenesView.as_view(), name="ordenes"),
    path("ordenes/<int:orden_id>/", views.OrdenDetalleView.as_view(), name="orden_detalle"),
    path("ordenes/<int:orden_id>/iniciar/", views.IniciarOrdenView.as_view(), name="iniciar_orden"),
    path("ordenes/<int:orden_id>/resolver/", views.ResolverOrdenView.as_view(), name="resolver_orden"),
    path("ordenes/<int:orden_id>/llegada/", views.RegistrarLlegadaView.as_view(), name="llegada"),
    # Evidencias y firma
    path("ordenes/<int:orden_id>/evidencias/", views.EvidenciasView.as_view(), name="evidencias"),
    path("ordenes/<int:orden_id>/evidencias/<int:evidencia_id>/",
         views.EvidenciaDetalleView.as_view(), name="evidencia_detalle"),
    path("ordenes/<int:orden_id>/firma/", views.FirmaView.as_view(), name="firma"),
    # Documentación: esquema OpenAPI y Swagger UI (públicos, no muestran datos)
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="docs"),
]
