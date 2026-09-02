from django.urls import path

from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('nuevo/', views.crear, name='crear'),
    path('<str:numero>/', views.detalle, name='detalle'),
    path('<str:numero>/publicar-oferta/', views.publicar_oferta, name='publicar_oferta'),
]
