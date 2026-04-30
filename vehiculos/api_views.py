# vehiculos/api_views.py
from rest_framework import viewsets, permissions
from django.shortcuts import get_object_or_404
from .models import Vehiculo, Mantenimiento, Siniestro, Kilometraje, Perfil
from .serializers import (
    VehiculoSerializer,
    MantenimientoSerializer,
    SiniestroSerializer,
    KilometrajeSerializer,
    PerfilSerializer
)

class VehiculoViewSet(viewsets.ModelViewSet):
    serializer_class = VehiculoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vehiculo.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class MantenimientoViewSet(viewsets.ModelViewSet):
    serializer_class = MantenimientoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Mantenimiento.objects.filter(vehiculo__usuario=self.request.user)

    def perform_create(self, serializer):
        mantenimiento = serializer.save()
        if mantenimiento.kilometraje:
            mantenimiento.vehiculo.actualizar_mantenimiento(mantenimiento.kilometraje)

class SiniestroViewSet(viewsets.ModelViewSet):
    serializer_class = SiniestroSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Siniestro.objects.filter(vehiculo__usuario=self.request.user)

class KilometrajeViewSet(viewsets.ModelViewSet):
    serializer_class = KilometrajeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Kilometraje.objects.filter(vehiculo__usuario=self.request.user)

    def perform_create(self, serializer):
        km = serializer.save()
        km.vehiculo.kilometraje_actual = km.valor
        km.vehiculo.save()

class PerfilViewSet(viewsets.ModelViewSet):
    serializer_class = PerfilSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Perfil.objects.filter(user=self.request.user)