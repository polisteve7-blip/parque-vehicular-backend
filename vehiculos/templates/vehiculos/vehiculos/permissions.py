# vehiculos/permissions.py
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """Admin puede hacer todo, los demás solo lectura"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.perfil.rol == 'admin'

class IsOwnerOrAdmin(permissions.BasePermission):
    """Permite editar solo si eres dueño o admin"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Verificar si el usuario es admin
        if hasattr(request.user, 'perfil') and request.user.perfil.rol == 'admin':
            return True
        
        # Verificar si es el dueño (el campo puede variar)
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        if hasattr(obj, 'vehiculo') and hasattr(obj.vehiculo, 'usuario'):
            return obj.vehiculo.usuario == request.user
        
        return False

class PuedeVerKilometraje(permissions.BasePermission):
    """Operadores y admin pueden ver y editar, lectores solo ven"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        rol = request.user.perfil.rol if hasattr(request.user, 'perfil') else 'lector'
        return rol in ['admin', 'operador']