from rest_framework import serializers
from .models import Vehiculo, Mantenimiento, Siniestro, Kilometraje, Perfil


# ==========================
# VEHICULO
# ==========================
class VehiculoSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Vehiculo
        fields = [
            'id', 'usuario', 'usuario_nombre',
            'placas', 'marca', 'modelo', 'anio',
            'responsable',
            'kilometraje_actual',
            'proximo_mantenimiento_km',
            'proximo_mantenimiento_fecha',
            'activo',
            'created_at', 'updated_at'
        ]

        read_only_fields = [
            'usuario',
            'proximo_mantenimiento_km',
            'proximo_mantenimiento_fecha',
            'created_at',
            'updated_at'
        ]

    # 🔒 Validación de placas únicas (extra control)
    def validate_placas(self, value):
        if Vehiculo.objects.filter(placas=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Ya existe un vehículo con estas placas")
        return value

    # 🔒 Validación de año
    def validate_anio(self, value):
        if value < 1900:
            raise serializers.ValidationError("Año inválido")
        return value


# ==========================
# MANTENIMIENTO
# ==========================
class MantenimientoSerializer(serializers.ModelSerializer):
    vehiculo_info = serializers.CharField(source='vehiculo.__str__', read_only=True)

    class Meta:
        model = Mantenimiento
        fields = [
            'id',
            'vehiculo',
            'vehiculo_info',
            'tipo',
            'descripcion',
            'costo',
            'kilometraje',
            'fecha',
            'created_at'
        ]

        read_only_fields = ['fecha', 'created_at']

    # 🔒 Validación de costo
    def validate_costo(self, value):
        if value < 0:
            raise serializers.ValidationError("El costo no puede ser negativo")
        return value


# ==========================
# SINIESTRO
# ==========================
class SiniestroSerializer(serializers.ModelSerializer):
    vehiculo_info = serializers.CharField(source='vehiculo.__str__', read_only=True)

    class Meta:
        model = Siniestro
        fields = [
            'id',
            'vehiculo',
            'vehiculo_info',
            'descripcion',
            'costo',
            'fecha',
            'created_at'
        ]

        read_only_fields = ['fecha', 'created_at']

    def validate_costo(self, value):
        if value < 0:
            raise serializers.ValidationError("El costo no puede ser negativo")
        return value


# ==========================
# KILOMETRAJE
# ==========================
class KilometrajeSerializer(serializers.ModelSerializer):
    vehiculo_info = serializers.CharField(source='vehiculo.__str__', read_only=True)

    class Meta:
        model = Kilometraje
        fields = ['id', 'vehiculo', 'vehiculo_info', 'valor', 'fecha']
        read_only_fields = ['fecha']

    def validate_valor(self, value):
        if value < 0:
            raise serializers.ValidationError("El kilometraje no puede ser negativo")
        return value


# ==========================
# PERFIL
# ==========================
class PerfilSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Perfil
        fields = ['id', 'user', 'username', 'rol']
        read_only_fields = ['user']

    # 🔒 Validar roles
    def validate_rol(self, value):
        roles_validos = ['admin', 'operador', 'lector']
        if value not in roles_validos:
            raise serializers.ValidationError("Rol inválido")
        return value