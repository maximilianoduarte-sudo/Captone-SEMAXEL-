import os

from django import template

register = template.Library()


@register.filter
def estado_label(value):
    """Devuelve la etiqueta legible de un estado (prototipo)."""
    labels = {
        "ABIERTO": "Abierto",
        "EN_REVISION": "En revisión",
        "PUBLICADO": "Publicado",
        "EN_EJECUCION": "En ejecución",
        "RESUELTO": "Resuelto",
        "CERRADO": "Cerrado",
        "CANCELADO": "Cancelado",
        "ASIGNADA": "Asignada",
        "RESUELTA": "Resuelta",
    }
    return labels.get(value, value or "—")


@register.filter
def prioridad_label(value):
    """Devuelve la etiqueta legible de una prioridad (prototipo)."""
    labels = {
        "BAJA": "Baja",
        "MEDIA": "Media",
        "ALTA": "Alta",
        "CRITICA": "Crítica",
    }
    return labels.get(value, value or "—")


@register.filter
def availability_label(value):
    """Devuelve la etiqueta legible de disponibilidad de un técnico."""
    labels = {
        "DISPONIBLE": "Disponible",
        "OCUPADO": "Ocupado",
        "NO_DISPONIBLE": "No disponible",
        "INACTIVO": "Inactivo",
    }
    return labels.get(value, value or "—")


@register.simple_tag
def nombre_archivo(path):
    """Devuelve el nombre base de un archivo o ruta."""
    return os.path.basename(path) if path else ""
