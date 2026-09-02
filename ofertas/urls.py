from django.urls import path

from . import views

app_name = 'ofertas'

urlpatterns = [
    path('', views.disponibles, name='disponibles'),
    path('<int:oid>/', views.detalle, name='detalle'),
    path('<int:oid>/tomar/', views.tomar, name='tomar'),
]
