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
]
