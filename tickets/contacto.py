"""Contacto del técnico con la sucursal (cliente) desde la web.

Mismas reglas que la app móvil (ui/comun/WhatsApp.kt): el teléfono se pasa
a formato internacional chileno y el enlace abre WhatsApp con un mensaje
listo sobre el trabajo.
"""

from urllib.parse import quote


def numero_whatsapp(telefono):
    """"+56 9 1234 5678" -> "56912345678"; None si no sirve para WhatsApp."""
    digitos = "".join(c for c in (telefono or "") if c.isdigit())
    if digitos.startswith("56") and 10 <= len(digitos) <= 11:
        return digitos
    if len(digitos) == 9:
        return "56" + digitos
    if len(digitos) >= 10:
        return digitos
    return None


def contacto_sucursal(orden):
    """Datos para que el técnico se comunique con la sucursal de la orden."""
    sucursal = orden.ticket.sucursal
    numero = numero_whatsapp(sucursal.telefono)
    mensaje = (
        f'Hola, le escribe el técnico de SEMAXEL asignado al trabajo "{orden.ticket.titulo}" '
        f"en {sucursal.nombre}."
    )
    return {
        "sucursal": sucursal,
        "telefono": sucursal.telefono,
        "enlace_telefono": f"tel:+{numero}" if numero else "",
        "enlace_whatsapp": f"https://wa.me/{numero}?text={quote(mensaje)}" if numero else "",
        "correo": sucursal.correo,
        "encargados": list(sucursal.encargados.all()),
    }
