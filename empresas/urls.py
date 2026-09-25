from django.urls import path

from . import views

app_name = "empresas"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<int:pk>/", views.detalle, name="detalle"),
]