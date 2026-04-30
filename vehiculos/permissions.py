# vehiculos/permissions.py
from django.core.exceptions import PermissionDenied
from functools import wraps
from rest_framework import permissions


def permiso_requerido(modulo, accion):
    """
    Sistema de permisos PRO para vistas web

    Ejemplo:
    @permiso_requerido('vehiculos', 'ver')
    @permiso_requerido('mantenimientos', 'crear')
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # 🔒 validar autenticación
            if not request.user.is_authenticated:
                raise PermissionDenied("Debes iniciar sesión")

            # 🔒 validar perfil
            if not hasattr(request.user, 'perfil'):
                raise PermissionDenied("Usuario sin perfil asignado")

            rol = request.user.perfil.rol

            # 🔥 matriz de permisos
            PERMISOS = {
                'admin': {
                    'vehiculos': ['ver', 'crear', 'editar', 'eliminar'],
                    'mantenimientos': ['ver', 'crear', 'editar'],
                    'siniestros': ['ver', 'crear'],
                    'reportes': ['ver'],
                },
                'operador': {
                    'vehiculos': ['ver', 'editar'],
                    'mantenimientos': ['ver', 'crear'],
                    'siniestros': ['ver', 'crear'],
                    'reportes': ['ver'],
                },
                'lector': {
                    'vehiculos': ['ver'],
                    'mantenimientos': ['ver'],
                    'siniestros': ['ver'],
                    'reportes': ['ver'],
                }
            }

            # 🔒 validar permiso
            if modulo not in PERMISOS.get(rol, {}):
                raise PermissionDenied("Sin acceso a este módulo")

            if accion not in PERMISOS[rol][modulo]:
                raise PermissionDenied("No tienes permiso para esta acción")

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


# ============================================
# PERMISOS PARA API REST (DRF)
# ============================================

class IsAdminOrReadOnly(permissions.BasePermission):
    """Admin puede hacer todo, los demás solo lectura"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'perfil'):
            return request.user.perfil.rol == 'admin'
        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permite editar solo si eres dueño o admin"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(request.user, 'perfil') and request.user.perfil.rol == 'admin':
            return True
        
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        if hasattr(obj, 'vehiculo') and hasattr(obj.vehiculo, 'usuario'):
            return obj.vehiculo.usuario == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class PuedeVerKilometraje(permissions.BasePermission):
    """Operadores y admin pueden ver y editar, lectores solo ven"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(request.user, 'perfil'):
            rol = request.user.perfil.rol
            return rol in ['admin', 'operador']
        return False