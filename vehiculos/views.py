# vehiculos/views.py - Versión COMPLETA y CORREGIDA
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, Q, Count, Avg
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone
import openpyxl
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import json

# REST FRAMEWORK
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

# MODELOS Y SERIALIZERS
from .models import Vehiculo, Mantenimiento, Siniestro, Kilometraje, Perfil, LogActividad
from .serializers import (
    VehiculoSerializer, MantenimientoSerializer, SiniestroSerializer,
    KilometrajeSerializer
)
from .permissions import IsOwnerOrAdmin, IsAdminOrReadOnly, PuedeVerKilometraje

# OTROS
from .forms import MantenimientoForm
from django.contrib.auth import authenticate, login


# ==========================
# API - AUTENTICACIÓN
# ==========================

@api_view(['POST'])
def api_register(request):
    """Registro de nuevos usuarios desde la app"""
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    rol = request.data.get('rol', 'operador')
    
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Usuario ya existe'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, password=password, email=email)
    Perfil.objects.create(user=user, rol=rol)
    token, _ = Token.objects.get_or_create(user=user)
    
    return Response({
        'token': token.key,
        'user_id': user.id,
        'username': user.username,
        'rol': rol
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def api_login_mobile(request):
    """Login específico para móvil - CORREGIDO"""
    import json
    
    print("=" * 60)
    print("=== LOGIN RECIBIDO ===")
    print(f"Content-Type: {request.content_type}")
    
    username = None
    password = None
    
    # Leer el body correctamente
    if request.body:
        try:
            body_str = request.body.decode('utf-8')
            print(f"Body: {body_str}")
            body_json = json.loads(body_str)
            username = body_json.get('username')
            password = body_json.get('password')
            print(f"Usuario extraído: {username}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Si no se encontró, intentar con request.data
    if not username:
        username = request.data.get('username')
        password = request.data.get('password')
        print(f"Desde request.data: {username}")
    
    print(f"Username final: {username}")
    print("=" * 60)
    
    if not username or not password:
        return Response(
            {'error': 'Usuario y contraseña requeridos'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        rol = user.perfil.rol if hasattr(user, 'perfil') else 'lector'
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'rol': rol,
            'email': user.email
        })
    
    return Response(
        {'error': 'Credenciales inválidas'}, 
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_info(request):
    """Obtener información del usuario actual"""
    user = request.user
    perfil = get_object_or_404(Perfil, user=user)
    
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'rol': perfil.rol,
        'date_joined': user.date_joined
    })


# ==========================
# VIEWSETS
# ==========================

class VehiculoViewSet(viewsets.ModelViewSet):
    serializer_class = VehiculoSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['marca', 'modelo', 'placas']
    ordering_fields = ['kilometraje_actual', 'anio', 'created_at']
    filterset_fields = ['activo', 'marca', 'anio']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'perfil') and user.perfil.rol == 'admin':
            return Vehiculo.objects.all()
        return Vehiculo.objects.filter(usuario=user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=False, methods=['get'])
    def mis_vehiculos(self, request):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def registrar_km(self, request, pk=None):
        vehiculo = self.get_object()
        km = request.data.get('kilometraje')
        
        try:
            km = int(km)
            if km <= vehiculo.kilometraje_actual:
                return Response({
                    'error': f'El kilometraje debe ser mayor a {vehiculo.kilometraje_actual}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            Kilometraje.objects.create(vehiculo=vehiculo, valor=km)
            vehiculo.kilometraje_actual = km
            vehiculo.save()
            
            return Response({
                'message': 'Kilometraje actualizado correctamente',
                'kilometraje_actual': km
            })
        except ValueError:
            return Response({'error': 'Kilometraje inválido'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def alertas(self, request, pk=None):
        vehiculo = self.get_object()
        alerts = []
        
        if vehiculo.proximo_mantenimiento_km and vehiculo.kilometraje_actual >= vehiculo.proximo_mantenimiento_km:
            alerts.append({
                'tipo': 'mantenimiento',
                'mensaje': f'Mantenimiento requerido - KM actual: {vehiculo.kilometraje_actual}'
            })
        
        if vehiculo.proximo_mantenimiento_fecha and timezone.now().date() >= vehiculo.proximo_mantenimiento_fecha:
            alerts.append({
                'tipo': 'fecha',
                'mensaje': f'Mantenimiento por fecha vencido para: {vehiculo.proximo_mantenimiento_fecha}'
            })
        
        return Response({'alertas': alerts})


class MantenimientoViewSet(viewsets.ModelViewSet):
    serializer_class = MantenimientoSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tipo', 'vehiculo']
    ordering_fields = ['fecha', 'costo']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'perfil') and user.perfil.rol == 'admin':
            return Mantenimiento.objects.all()
        return Mantenimiento.objects.filter(vehiculo__usuario=user)

    def perform_create(self, serializer):
        mantenimiento = serializer.save()
        if mantenimiento.kilometraje:
            mantenimiento.vehiculo.actualizar_mantenimiento(mantenimiento.kilometraje)
        
        LogActividad.objects.create(
            usuario=self.request.user,
            accion="Creó mantenimiento",
            modelo="Mantenimiento",
            objeto_id=mantenimiento.id,
            descripcion=f"Costo: {mantenimiento.costo}"
        )


class KilometrajeViewSet(viewsets.ModelViewSet):
    serializer_class = KilometrajeSerializer
    permission_classes = [IsAuthenticated, PuedeVerKilometraje]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['vehiculo']
    ordering_fields = ['fecha', 'valor']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'perfil') and user.perfil.rol == 'admin':
            return Kilometraje.objects.all()
        return Kilometraje.objects.filter(vehiculo__usuario=user)

    def perform_create(self, serializer):
        km = serializer.save()
        if km.valor > km.vehiculo.kilometraje_actual:
            km.vehiculo.kilometraje_actual = km.valor
            km.vehiculo.save()


class SiniestroViewSet(viewsets.ModelViewSet):
    serializer_class = SiniestroSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['vehiculo']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'perfil') and user.perfil.rol == 'admin':
            return Siniestro.objects.all()
        return Siniestro.objects.filter(vehiculo__usuario=user)


class EstadisticasViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        user = request.user
        if hasattr(user, 'perfil') and user.perfil.rol == 'admin':
            vehiculos = Vehiculo.objects.all()
        else:
            vehiculos = Vehiculo.objects.filter(usuario=user)
        
        stats = {
            "vehiculos": vehiculos.count(),
            "vehiculos_activos": vehiculos.filter(activo=True).count(),
            "mantenimientos": Mantenimiento.objects.filter(vehiculo__in=vehiculos).count(),
            "siniestros": Siniestro.objects.filter(vehiculo__in=vehiculos).count(),
            "kms_totales": Kilometraje.objects.filter(vehiculo__in=vehiculos).aggregate(total=Sum('valor'))['total'] or 0,
            "costo_mantenimientos": Mantenimiento.objects.filter(vehiculo__in=vehiculos).aggregate(total=Sum('costo'))['total'] or 0,
            "costo_siniestros": Siniestro.objects.filter(vehiculo__in=vehiculos).aggregate(total=Sum('costo'))['total'] or 0,
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def dashboard_mobile(self, request):
        user = request.user
        if hasattr(user, 'perfil') and user.perfil.rol == 'admin':
            vehiculos = Vehiculo.objects.all()
        else:
            vehiculos = Vehiculo.objects.filter(usuario=user)
        
        alertas = vehiculos.filter(
            Q(proximo_mantenimiento_km__lte=F('kilometraje_actual')) |
            Q(proximo_mantenimiento_fecha__lte=timezone.now().date())
        )
        
        ultimos_kms = Kilometraje.objects.filter(vehiculo__in=vehiculos)[:10]
        
        return Response({
            'stats': {
                'total': vehiculos.count(),
                'activos': vehiculos.filter(activo=True).count(),
                'con_alerta': alertas.count(),
            },
            'alertas': [{
                'id': v.id,
                'nombre': f"{v.marca} {v.modelo}",
                'placa': v.placas,
                'tipo': 'km' if v.kilometraje_actual >= v.proximo_mantenimiento_km else 'fecha'
            } for v in alertas[:5]],
            'ultimas_actividades': [{
                'tipo': 'km',
                'vehiculo': str(km.vehiculo),
                'valor': km.valor,
                'fecha': km.fecha
            } for km in ultimos_kms]
        })


# ==========================
# VISTAS WEB
# ==========================

@login_required
def home(request):
    return redirect('dashboard')

@login_required
def dashboard(request):
    vehiculos = Vehiculo.objects.filter(usuario=request.user).annotate(
        total_mantenimiento=Sum('mantenimientos__costo'),
        total_siniestros=Sum('siniestros__costo')
    )
    
    context = {
        'vehiculos': vehiculos,
        'total_vehiculos': vehiculos.count(),
        'total_mantenimientos': Mantenimiento.objects.filter(vehiculo__in=vehiculos).count(),
        'total_siniestros': Siniestro.objects.filter(vehiculo__in=vehiculos).count(),
        'alertas': vehiculos.filter(
            kilometraje_actual__gte=F('proximo_mantenimiento_km')
        ) if vehiculos else [],
    }
    
    return render(request, 'vehiculos/dashboard.html', context)

@login_required
def lista_vehiculos(request):
    vehiculos = Vehiculo.objects.filter(usuario=request.user)
    return render(request, 'vehiculos/lista_vehiculos.html', {'vehiculos': vehiculos})

@login_required
def alertas_vehiculos(request):
    vehiculos = Vehiculo.objects.filter(
        usuario=request.user,
        kilometraje_actual__gte=F('proximo_mantenimiento_km')
    )
    return render(request, 'vehiculos/alertas.html', {'vehiculos': vehiculos})

@login_required
def registrar_mantenimiento(request):
    if request.method == 'POST':
        form = MantenimientoForm(request.POST)
        if form.is_valid():
            mantenimiento = form.save()
            mantenimiento.vehiculo.actualizar_mantenimiento(mantenimiento.kilometraje)
            return redirect('lista_vehiculos')
    else:
        form = MantenimientoForm()
    return render(request, 'vehiculos/form_mantenimiento.html', {'form': form})

@login_required
def registrar_siniestro(request):
    return render(request, 'vehiculos/registrar_siniestro.html')

@login_required
def actualizar_kilometraje(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    
    if request.method == 'POST':
        km = request.POST.get('kilometraje')
        try:
            km = int(km)
            if km > vehiculo.kilometraje_actual:
                Kilometraje.objects.create(vehiculo=vehiculo, valor=km)
                vehiculo.kilometraje_actual = km
                vehiculo.save()
            return redirect('lista_vehiculos')
        except ValueError:
            pass
    
    return render(request, 'vehiculos/actualizar_km.html', {'vehiculo': vehiculo})

@login_required
def reporte_costos(request):
    vehiculos = Vehiculo.objects.filter(usuario=request.user)
    return render(request, 'vehiculos/reporte_costos.html', {'vehiculos': vehiculos})

@login_required
def exportar_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Vehículos"
    
    headers = ["Marca", "Modelo", "Placa", "Año", "KM Actual", "Próximo Mantenimiento KM"]
    ws.append(headers)
    
    for v in Vehiculo.objects.filter(usuario=request.user):
        ws.append([
            v.marca, v.modelo, v.placas, v.anio,
            v.kilometraje_actual, v.proximo_mantenimiento_km
        ])
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=vehiculos.xlsx'
    wb.save(response)
    return response

@login_required
def reporte_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_vehiculos.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Reporte de Parque Vehicular")
    
    p.setFont("Helvetica", 10)
    y = height - 100
    for v in Vehiculo.objects.filter(usuario=request.user):
        p.drawString(50, y, f"{v.marca} {v.modelo} - {v.placas} - KM: {v.kilometraje_actual}")
        y -= 20
        if y < 50:
            p.showPage()
            y = height - 50
    
    p.save()
    return response


# ============================================
# ENDPOINT PARA ESTADÍSTICAS
# ============================================

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


# ============================================
# ENDPOINT DE PRUEBA PARA LOGIN (APP MÓVIL)
# ============================================

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

@api_view(['POST'])
@permission_classes([AllowAny])
def login_test(request):
    """Endpoint de prueba para login - más simple y compatible"""
    import json
    
    print("=" * 50)
    print("=== LOGIN TEST ===")
    
    username = None
    password = None
    
    # Método 1: x-www-form-urlencoded
    if request.content_type == 'application/x-www-form-urlencoded':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Desde form-urlencoded: {username}")
    
    # Método 2: JSON
    if not username and request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            print(f"Desde JSON: {username}")
        except:
            pass
    
    # Método 3: FormData
    if not username:
        username = request.data.get('username')
        password = request.data.get('password')
        print(f"Desde request.data: {username}")
    
    # Método 4: Body directo
    if not username and request.body:
        try:
            body_str = request.body.decode('utf-8')
            if 'username' in body_str:
                data = json.loads(body_str)
                username = data.get('username')
                password = data.get('password')
                print(f"Desde body directo: {username}")
        except:
            pass
    
    print(f"Username final: {username}")
    print(f"Password final: {password}")
    print("=" * 50)
    
    if not username or not password:
        return Response(
            {'error': 'Usuario y contraseña requeridos'}, 
            status=400
        )
    
    user = authenticate(username=username, password=password)
    
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        
        # Obtener el rol del usuario
        rol = 'lector'
        if hasattr(user, 'perfil') and user.perfil:
            rol = user.perfil.rol
            print(f"Rol encontrado: {rol}")
        else:
            print("Usuario sin perfil, asignando 'lector'")
        
        return Response({
            'success': True,
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'rol': rol,
        })
    
    return Response(
        {'error': 'Credenciales inválidas'}, 
        status=401
    )


# ============================================
# DASHBOARD MÓVIL CON GRÁFICAS (NUEVO)
# ============================================

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_graficas(request):
    """Endpoint específico para gráficas del dashboard móvil"""
    user = request.user
    if hasattr(user, 'perfil') and user.perfil.rol == 'admin':
        vehiculos = Vehiculo.objects.all()
    else:
        vehiculos = Vehiculo.objects.filter(usuario=user)
    
    # Vehículos por marca (top 5)
    vehiculos_por_marca = vehiculos.values('marca').annotate(total=Count('id')).order_by('-total')[:5]
    
    # Kilometraje por mes (últimos 6 meses)
    km_por_mes = Kilometraje.objects.filter(
        vehiculo__in=vehiculos,
        fecha__gte=timezone.now() - timezone.timedelta(days=180)
    ).annotate(mes=TruncMonth('fecha')).values('mes').annotate(total_km=Sum('valor')).order_by('mes')
    
    km_por_mes_list = []
    for item in km_por_mes:
        if item['mes']:
            km_por_mes_list.append({
                'mes': item['mes'].strftime('%b'), 
                'total_km': item['total_km'] or 0
            })
    
    return Response({
        'vehiculosPorMarca': list(vehiculos_por_marca),
        'kmPorMes': km_por_mes_list,
    })


# ============================================
# CAMBIAR CONTRASEÑA
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_password(request):
    """Cambiar contraseña del usuario autenticado"""
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not user.check_password(old_password):
        return Response({'error': 'Contraseña actual incorrecta'}, status=400)
    
    if len(new_password) < 6:
        return Response({'error': 'La nueva contraseña debe tener al menos 6 caracteres'}, status=400)
    
    user.set_password(new_password)
    user.save()
    
    return Response({'message': 'Contraseña actualizada correctamente'})