from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/perfil/", views.PerfilView.as_view(), name="perfil"),
    path("ofertas/", views.OfertasDisponiblesView.as_view(), name="ofertas"),
    path("ofertas/<int:oferta_id>/", views.OfertaDetalleView.as_view(), name="oferta_detalle"),
    path("ofertas/<int:oferta_id>/tomar/", views.TomarOfertaView.as_view(), name="tomar_oferta"),
    path("ordenes/", views.MisOrdenesView.as_view(), name="ordenes"),
    path("ordenes/<int:orden_id>/", views.OrdenDetalleView.as_view(), name="orden_detalle"),
    path("ordenes/<int:orden_id>/iniciar/", views.IniciarOrdenView.as_view(), name="iniciar_orden"),
    path("ordenes/<int:orden_id>/resolver/", views.ResolverOrdenView.as_view(), name="resolver_orden"),
]
