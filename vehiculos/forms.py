from django import forms
from .models import Vehiculo, Mantenimiento

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = [
    'placas',
    'marca',
    'modelo',
    'anio',
    'responsable',
    'kilometraje_actual',
    'proximo_mantenimiento_km',
    'proximo_mantenimiento_fecha',
]

class MantenimientoForm(forms.ModelForm):
    class Meta:
        model = Mantenimiento
        fields = ['vehiculo', 'tipo', 'descripcion', 'costo', 'kilometraje']