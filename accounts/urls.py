from django.urls import path

from . import views

urlpatterns = [
    path("", views.usuarios, name="usuarios"),
    path("nuevo/", views.usuario_nuevo, name="usuario_nuevo"),
    path("<int:pk>/editar/", views.usuario_editar, name="usuario_editar"),
]