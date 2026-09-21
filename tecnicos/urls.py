from django.urls import path

from . import views

app_name = 'tecnicos'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('nuevo/', views.crear, name='crear'),
    path('<int:pk>/editar/', views.editar, name='editar'),
    path('<int:pk>/', views.detalle, name='detalle'),
]