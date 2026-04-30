# vehiculos/services/log_service.py

from vehiculos.models import LogActividad

def registrar_log(usuario, accion, modelo, objeto_id=None, descripcion=""):
    """
    Registra una acción del usuario en LogActividad.

    Args:
        usuario: instancia del usuario que realiza la acción.
        accion: str, acción realizada (ej: "CREAR", "ACTUALIZAR").
        modelo: str, nombre del modelo afectado.
        objeto_id: int, id del objeto afectado (opcional).
        descripcion: str, descripción adicional (opcional).
    """
    LogActividad.objects.create(
        usuario=usuario,
        accion=accion,
        modelo=modelo,
        objeto_id=objeto_id,
        descripcion=descripcion
    )