from django.urls import path
from .api_views import VehiculoListAPI

urlpatterns = [
    path('vehiculos/', VehiculoListAPI.as_view(), name='api_vehiculos'),
]