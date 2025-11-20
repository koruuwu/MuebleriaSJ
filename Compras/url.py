from django.urls import path
from .views import obtener_precio_mueble

urlpatterns = [
    path('api/precio-mueble/<int:pk>/', obtener_precio_mueble, name="precio_mueble"),
]
