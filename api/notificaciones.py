"""Notificaciones push a los celulares de los técnicos.

Funciona con "backends" intercambiables, elegidos con SEMAXEL_PUSH_BACKEND:

- "consola" (por defecto): no envía nada; escribe la notificación en el log.
  Sirve para desarrollar sin cuenta de Firebase.
- "memoria": guarda las notificaciones en la lista `BANDEJA` (para pruebas).
- "fcm": envía con Firebase Cloud Messaging (API HTTP v1). Necesita
  FCM_CREDENTIALS_FILE (JSON de la cuenta de servicio de Firebase) y el
  paquete google-auth instalado.

Un error al notificar nunca debe romper la operación que lo originó (tomar,
publicar o cerrar): se registra en el log y se sigue.
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

from .models import Dispositivo

logger = logging.getLogger(__name__)

BANDEJA = []  # usada por el backend "memoria"


def notificar(usuarios, titulo, cuerpo, datos=None):
    """Envía una notificación a todos los dispositivos de esos usuarios.

    `datos` es un diccionario de textos que la app recibe junto al aviso,
    por ejemplo {"tipo": "oferta_nueva", "oferta_id": "12"}.
    Devuelve cuántos dispositivos se intentaron notificar.
    """
    datos = {clave: str(valor) for clave, valor in (datos or {}).items()}
    dispositivos = list(Dispositivo.objects.filter(usuario__in=usuarios))
    backend = settings.SEMAXEL_PUSH_BACKEND
    for dispositivo in dispositivos:
        try:
            if backend == "fcm":
                _enviar_fcm(dispositivo, titulo, cuerpo, datos)
            elif backend == "memoria":
                BANDEJA.append({
                    "usuario": dispositivo.usuario_id,
                    "token": dispositivo.token,
                    "titulo": titulo,
                    "cuerpo": cuerpo,
                    "datos": datos,
                })
            else:
                logger.info("[push] %s -> %s: %s | %s", dispositivo.usuario, titulo, cuerpo, datos)
        except Exception:  # noqa: BLE001 - notificar nunca debe romper el flujo
            logger.exception("No se pudo notificar al dispositivo %s", dispositivo.pk)
    return len(dispositivos)


# ---------------------------------------------------------------- FCM HTTP v1

_credenciales = None


def _token_de_acceso():
    """Token OAuth de la cuenta de servicio de Firebase (se renueva solo)."""
    global _credenciales
    from google.auth.transport.requests import Request  # import diferido: opcional
    from google.oauth2 import service_account

    if _credenciales is None:
        _credenciales = service_account.Credentials.from_service_account_file(
            settings.FCM_CREDENTIALS_FILE,
            scopes=["https://www.googleapis.com/auth/firebase.messaging"],
        )
    if not _credenciales.valid:
        _credenciales.refresh(Request())
    return _credenciales.token, _credenciales.project_id


def _enviar_fcm(dispositivo, titulo, cuerpo, datos):
    token_acceso, proyecto = _token_de_acceso()
    mensaje = {
        "message": {
            "token": dispositivo.token,
            "notification": {"title": titulo, "body": cuerpo},
            "data": datos,
        }
    }
    peticion = urllib.request.Request(
        f"https://fcm.googleapis.com/v1/projects/{proyecto}/messages:send",
        data=json.dumps(mensaje).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token_acceso}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(peticion, timeout=10).close()
    except urllib.error.HTTPError as error:
        # 404 o 400 con UNREGISTERED: la app se desinstaló o el token cambió.
        if error.code in (400, 404) and b"UNREGISTERED" in error.read():
            dispositivo.delete()
            return
        raise
