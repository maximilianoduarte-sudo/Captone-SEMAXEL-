from django.urls import path

from . import views

app_name = 'tecnicos'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('<str:nombre>/', views.detalle, name='detalle'),
]
