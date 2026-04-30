from django.contrib import admin
from .models import Vehiculo, Mantenimiento, Kilometraje, Siniestro, Perfil, LogActividad

# ==========================
# VEHICULO ADMIN
# ==========================
@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = (
        'placas',
        'marca',
        'modelo',
        'anio',
        'usuario',
        'responsable',
        'kilometraje_actual',
        'activo'
    )

    search_fields = ('placas', 'marca', 'modelo', 'usuario__username')
    list_filter = ('marca', 'anio', 'activo')
    ordering = ('-created_at',)

    autocomplete_fields = ['usuario', 'responsable']


# ==========================
# MANTENIMIENTO ADMIN
# ==========================
@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = (
        'vehiculo',
        'tipo',
        'costo',
        'kilometraje',
        'fecha',
        'activo'
    )

    search_fields = (
        'vehiculo__placas',
        'vehiculo__marca',
        'vehiculo__modelo'
    )

    list_filter = ('tipo', 'fecha', 'activo')
    ordering = ('-fecha',)

    autocomplete_fields = ['vehiculo']


# ==========================
# SINIESTRO ADMIN
# ==========================
@admin.register(Siniestro)
class SiniestroAdmin(admin.ModelAdmin):
    list_display = (
        'vehiculo',
        'costo',
        'fecha',
        'activo'
    )

    search_fields = (
        'vehiculo__placas',
        'vehiculo__marca'
    )

    list_filter = ('fecha', 'activo')
    ordering = ('-fecha',)

    autocomplete_fields = ['vehiculo']


# ==========================
# KILOMETRAJE ADMIN
# ==========================
@admin.register(Kilometraje)
class KilometrajeAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'valor', 'fecha')
    search_fields = ('vehiculo__placas',)
    ordering = ('-fecha',)

    autocomplete_fields = ['vehiculo']


# ==========================
# PERFIL ADMIN
# ==========================
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol')
    list_filter = ('rol',)
    search_fields = ('user__username',)


# ==========================
# LOG ACTIVIDAD ADMIN
# ==========================
@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    list_display = (
        'usuario',
        'accion',
        'modelo',
        'objeto_id',
        'fecha'
    )

    search_fields = ('usuario__username', 'accion', 'modelo')
    list_filter = ('accion', 'modelo', 'fecha')
    ordering = ('-fecha',)

    readonly_fields = [field.name for field in LogActividad._meta.fields]