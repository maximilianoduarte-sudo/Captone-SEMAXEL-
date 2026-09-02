from django.urls import path

from . import ordenes_views

app_name = 'ordenes'

urlpatterns = [
    path('', ordenes_views.lista, name='lista'),
    path('<int:oid>/', ordenes_views.detalle, name='detalle'),
]
