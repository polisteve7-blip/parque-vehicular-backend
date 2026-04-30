from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.timezone import now
import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

# ==========================
# PERFIL
# ==========================
class Perfil(models.Model):
    ROLES = [
        ('admin', 'Administrador'),
        ('operador', 'Operador'),
        ('lector', 'Lector'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES, default='lector')

    def __str__(self):
        return f"{self.user.username} - {self.rol}"


# ==========================
# VEHICULO
# ==========================
class Vehiculo(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    placas = models.CharField(max_length=20, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.PositiveIntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(datetime.date.today().year + 1)]
    )
    responsable = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="vehiculos_asignados"
    )
    kilometraje_actual = models.PositiveIntegerField(default=0)
    proximo_mantenimiento_km = models.PositiveIntegerField(null=True, blank=True)
    proximo_mantenimiento_fecha = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["placas"]),
            models.Index(fields=["usuario"]),
        ]

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.placas})"

    def actualizar_mantenimiento(self, km=None):
        if km is not None:
            self.kilometraje_actual = km
        self.proximo_mantenimiento_km = self.kilometraje_actual + 10000
        self.proximo_mantenimiento_fecha = now().date() + datetime.timedelta(days=180)
        self.save()


# ==========================
# MANTENIMIENTO
# ==========================
class Mantenimiento(models.Model):
    TIPOS = [('preventivo', 'Preventivo'), ('correctivo', 'Correctivo')]
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name="mantenimientos")
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descripcion = models.TextField(blank=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    kilometraje = models.PositiveIntegerField(default=0)
    fecha = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    activo = models.BooleanField(default=True)

    def clean(self):
        if self.costo < 0:
            raise ValidationError("El costo no puede ser negativo")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        if self.kilometraje:
            self.vehiculo.actualizar_mantenimiento(self.kilometraje)

    def __str__(self):
        return f"{self.vehiculo} - {self.tipo} - {self.fecha}"


# ==========================
# SINIESTRO
# ==========================
class Siniestro(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name="siniestros")
    descripcion = models.TextField()
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    activo = models.BooleanField(default=True)

    def clean(self):
        if self.costo < 0:
            raise ValidationError("El costo no puede ser negativo")

    def __str__(self):
        return f"{self.vehiculo} - {self.fecha}"


# ==========================
# HISTORIAL KM
# ==========================
class Kilometraje(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name="historial_km")
    valor = models.IntegerField()
    fecha = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.vehiculo} - {self.valor} km - {self.fecha}"


# ==========================
# LOGS DE ACTIVIDAD
# ==========================
class LogActividad(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    objeto_id = models.IntegerField(null=True, blank=True)
    descripcion = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Log de actividad"
        verbose_name_plural = "Logs de actividad"

    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.modelo}"


# ==========================
# SEÑALES AUTOMÁTICAS PARA LOGS
# ==========================
@receiver(post_save, sender=Mantenimiento)
def log_mantenimiento(sender, instance, created, **kwargs):
    accion = "Creado" if created else "Actualizado"
    LogActividad.objects.create(
        usuario=instance.vehiculo.usuario,
        accion=f"{accion} mantenimiento",
        modelo="Mantenimiento",
        objeto_id=instance.id,
        descripcion=f"Costo: {instance.costo}, KM: {instance.kilometraje}"
    )

@receiver(post_save, sender=Siniestro)
def log_siniestro(sender, instance, created, **kwargs):
    accion = "Creado" if created else "Actualizado"
    LogActividad.objects.create(
        usuario=instance.vehiculo.usuario,
        accion=f"{accion} siniestro",
        modelo="Siniestro",
        objeto_id=instance.id,
        descripcion=f"Costo: {instance.costo}, Desc: {instance.descripcion}"
    )

@receiver(post_save, sender=Kilometraje)
def log_kilometraje(sender, instance, created, **kwargs):
    accion = "Creado" if created else "Actualizado"
    LogActividad.objects.create(
        usuario=instance.vehiculo.usuario,
        accion=f"{accion} kilometraje",
        modelo="Kilometraje",
        objeto_id=instance.id,
        descripcion=f"Valor: {instance.valor}"
    )
    # vehiculos/models.py - Al final del archivo
from django.db.models.signals import post_save
from django.dispatch import receiver

# ... (tu código existente) ...

# Asegurar que las señales están registradas
default_app_config = 'vehiculos.apps.VehiculosConfig'