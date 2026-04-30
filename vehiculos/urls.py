# vehiculos/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Crear el router
router = DefaultRouter()

# Registrar SOLO los ViewSets que existen en views.py
router.register(r'vehiculos', views.VehiculoViewSet, basename='vehiculo')
router.register(r'mantenimientos', views.MantenimientoViewSet, basename='mantenimiento')
router.register(r'siniestros', views.SiniestroViewSet, basename='siniestro')
router.register(r'kilometrajes', views.KilometrajeViewSet, basename='kilometraje')
# router.register(r'perfil', views.PerfilViewSet, basename='perfil')  # Comentado porque no existe
# router.register(r'estadisticas', views.EstadisticasViewSet, basename='estadistica')  # Comentado porque causa problemas

# Endpoint simple para estadísticas (para la app móvil)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Vehiculo, Mantenimiento, Siniestro

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estadisticas_simples(request):
    """Endpoint simple para estadísticas - compatible con la app móvil"""
    user = request.user
    
    vehiculos_count = Vehiculo.objects.filter(usuario=user).count()
    mantenimientos_count = Mantenimiento.objects.filter(vehiculo__usuario=user).count()
    siniestros_count = Siniestro.objects.filter(vehiculo__usuario=user).count()
    
    return Response({
        'vehiculos': vehiculos_count,
        'mantenimientos': mantenimientos_count,
        'siniestros': siniestros_count
    })


urlpatterns = [
    # API REST
    path('api/', include(router.urls)),
    
    # Endpoint simple para estadísticas
    path('api/estadisticas/', estadisticas_simples, name='estadisticas'),
    
    # Login para app móvil
    path('api/token/', views.api_login_mobile, name='api_token_auth'),
    path('api/register/', views.api_register, name='api_register'),
    
    # Vistas web
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('vehiculos/', views.lista_vehiculos, name='lista_vehiculos'),
    path('alertas/', views.alertas_vehiculos, name='alertas'),
    path('mantenimiento/registrar/', views.registrar_mantenimiento, name='registrar_mantenimiento'),
    path('siniestro/registrar/', views.registrar_siniestro, name='registrar_siniestro'),
    path('kilometraje/actualizar/<int:vehiculo_id>/', views.actualizar_kilometraje, name='actualizar_kilometraje'),
    path('reporte/costos/', views.reporte_costos, name='reporte_costos'),
    path('exportar/excel/', views.exportar_excel, name='exportar_excel'),
    path('reporte/pdf/', views.reporte_pdf, name='reporte_pdf'),
    path('api/login-test/', views.login_test, name='login_test'),
    path('api/cambiar-password/', views.cambiar_password, name='cambiar_password'),
    path('api/estadisticas/graficas/', views.dashboard_graficas, name='dashboard_graficas'),
    path('api/estadisticas/graficas/', views.dashboard_graficas, name='dashboard_graficas'),
]