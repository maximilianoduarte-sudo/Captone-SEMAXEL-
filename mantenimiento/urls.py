from django.urls import path

from . import views

app_name = 'mantenimiento'

urlpatterns = [
    path('', views.lista, name='lista'),
]
