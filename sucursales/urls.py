from django.urls import path

from . import views

app_name = 'sucursales'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('nuevo/', views.crear, name='crear'),
    path('<int:suc_id>/', views.detalle, name='detalle'),
]
