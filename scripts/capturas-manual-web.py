"""Toma las capturas de la web de SEMAXEL para el Manual de usuario.

Abre Chrome sin ventana (modo headless) y lo maneja por su protocolo de
depuración (DevTools) con un cliente WebSocket mínimo de la biblioteca
estándar. Para entrar con cada rol no escribe contraseñas: crea con Django una
sesión del usuario de prueba y se la pasa a Chrome como cookie.

Requisitos: servidor en http://localhost:8000 (scripts\\levantar-todo.ps1),
datos de QA cargados y Google Chrome instalado. Se ejecuta con el Python del
proyecto:

    .\\venv\\Scripts\\python.exe scripts\\capturas-manual-web.py <carpeta_salida>
"""

import base64
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from django.contrib.sessions.backends.db import SessionStore  # noqa: E402

BASE = "http://localhost:8000"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PUERTO = 9333
ANCHO, ALTO = 1440, 900


# ------------------------------------------------------- WebSocket mínimo

class WebSocket:
    def __init__(self, url):
        host_port, ruta = url[len("ws://"):].split("/", 1)
        host, puerto = host_port.split(":")
        self.s = socket.create_connection((host, int(puerto)))
        clave = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((
            f"GET /{ruta} HTTP/1.1\r\nHost: {host_port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {clave}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        ).encode())
        respuesta = b""
        while b"\r\n\r\n" not in respuesta:
            respuesta += self.s.recv(4096)
        self.resto = respuesta.split(b"\r\n\r\n", 1)[1]

    def _leer(self, n):
        while len(self.resto) < n:
            datos = self.s.recv(1 << 20)
            if not datos:
                raise ConnectionError("Chrome cerró la conexión")
            self.resto += datos
        trozo, self.resto = self.resto[:n], self.resto[n:]
        return trozo

    def enviar(self, texto):
        datos = texto.encode()
        cabecera = bytearray([0x81])
        n = len(datos)
        if n < 126:
            cabecera.append(0x80 | n)
        elif n < 65536:
            cabecera += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            cabecera += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mascara = os.urandom(4)
        self.s.sendall(bytes(cabecera) + mascara + bytes(b ^ mascara[i % 4] for i, b in enumerate(datos)))

    def recibir(self):
        mensaje = b""
        while True:
            b1, b2 = self._leer(2)
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._leer(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._leer(8))[0]
            mensaje += self._leer(n)
            if b1 & 0x80:
                return mensaje.decode()


class Chrome:
    def __init__(self):
        self.datos = tempfile.mkdtemp(prefix="semaxel-chrome-")
        self.proceso = subprocess.Popen([
            CHROME, "--headless=new", f"--remote-debugging-port={PUERTO}",
            f"--user-data-dir={self.datos}", "--hide-scrollbars", "--no-first-run",
            "--lang=es-CL", f"--window-size={ANCHO},{ALTO}", "about:blank",
        ])
        for _ in range(50):
            try:
                paginas = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PUERTO}/json"))
                pagina = next(p for p in paginas if p["type"] == "page")
                break
            except Exception:
                time.sleep(0.2)
        self.ws = WebSocket(pagina["webSocketDebuggerUrl"])
        self.n = 0
        self.cmd("Page.enable")
        self.cmd("Network.enable")
        self.cmd("Emulation.setDeviceMetricsOverride", width=ANCHO, height=ALTO,
                 deviceScaleFactor=1, mobile=False)

    def cmd(self, metodo, **params):
        self.n += 1
        self.ws.enviar(json.dumps({"id": self.n, "method": metodo, "params": params}))
        while True:
            m = json.loads(self.ws.recibir())
            if m.get("id") == self.n:
                if "error" in m:
                    raise RuntimeError(f"{metodo}: {m['error']}")
                return m.get("result", {})

    def js(self, codigo):
        return self.cmd("Runtime.evaluate", expression=codigo, returnByValue=True).get("result", {}).get("value")

    def ir(self, ruta, espera=1.2):
        self.cmd("Page.navigate", url=BASE + ruta)
        for _ in range(60):
            if self.js("document.readyState") == "complete":
                break
            time.sleep(0.2)
        time.sleep(espera)

    def entrar_como(self, username):
        self.cmd("Network.clearBrowserCookies")
        if not username:
            return
        user = User.objects.get(username=username)
        sesion = SessionStore()
        sesion[SESSION_KEY] = str(user.pk)
        sesion[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0] if getattr(
            settings, "AUTHENTICATION_BACKENDS", None) else "django.contrib.auth.backends.ModelBackend"
        sesion[HASH_SESSION_KEY] = user.get_session_auth_hash()
        sesion.create()
        self.cmd("Network.setCookie", name=settings.SESSION_COOKIE_NAME, value=sesion.session_key,
                 domain="localhost", path="/")

    def foto(self, archivo, alto_max=None):
        """Captura la ventana; con alto_max, la página completa hasta ese alto."""
        if alto_max:
            alto = min(int(self.js("document.documentElement.scrollHeight")), alto_max)
            self.cmd("Emulation.setDeviceMetricsOverride", width=ANCHO, height=alto,
                     deviceScaleFactor=1, mobile=False)
            time.sleep(0.6)
        datos = self.cmd("Page.captureScreenshot", format="png")["data"]
        Path(archivo).write_bytes(base64.b64decode(datos))
        if alto_max:
            self.cmd("Emulation.setDeviceMetricsOverride", width=ANCHO, height=ALTO,
                     deviceScaleFactor=1, mobile=False)

    def cerrar(self):
        self.proceso.terminate()


# ------------------------------------------------------------- capturas

def ids():
    """Registros de QA que se muestran en las capturas."""
    from empresas.models import Empresa
    from mantenimiento.models import PlanMantenimiento
    from ofertas.models import OfertaTicket
    from sucursales.models import Sucursal
    from tecnicos.models import Tecnico
    from tickets.models import OrdenTrabajo

    def orden(estado, sucursales=("QPR", "QNU")):
        return OrdenTrabajo.objects.filter(
            ticket__numero__startswith="QA-", estado=estado, ticket__sucursal__codigo__in=sucursales
        ).order_by("-pk").first().pk

    return {
        "empresa": Empresa.objects.get(codigo="QA").pk,
        "sucursal": Sucursal.objects.get(codigo="QPR").pk,
        "tecnico": Tecnico.objects.get(usuario__username="qa_tecnico").pk,
        "plan": PlanMantenimiento.objects.filter(sucursal__empresa__codigo="QA", activo=True).first().pk,
        "oferta": OfertaTicket.objects.filter(
            estado="DISPONIBLE", ticket__numero__startswith="QA-"
        ).order_by("-pk").first().pk,
        "orden_asignada": orden("ASIGNADA"),
        "orden_ejecucion": orden("EN_EJECUCION"),
        "orden_resuelta": orden("RESUELTA"),
        "usuario": User.objects.get(username="qa_gestor").pk,
    }


CLIC_TEXTO = """(() => { const t = %r.toLowerCase();
  const b = [...document.querySelectorAll('button, a, input[type=submit]')]
    .find(e => (e.innerText || e.value || '').trim().toLowerCase().includes(t));
  if (b) b.click(); return !!b; })()"""

ELEGIR = """(() => { const s = document.querySelector('select[name=estado]');
  if (!s) return false; s.value = %r; s.dispatchEvent(new Event('change', {bubbles: true})); return true; })()"""


def capturas(i):
    # (archivo, usuario, ruta, js antes de capturar, alto máximo de página completa)
    return [
        ("web01_login", None, "/login/", None, None),
        ("web02_registro", None, "/registro/", None, None),
        ("web03_registro_tecnico", None, "/registro/tecnico/", None, 1500),
        ("web04_vista_general", "qa_admin", "/", None, None),
        ("web05_usuarios", "qa_admin", "/usuarios/", None, None),
        ("web06_usuario_form", "qa_admin", f"/usuarios/{i['usuario']}/editar/", None, 1400),
        ("web07_perfil_tecnico", "qa_tecnico", "/perfil/", None, None),
        ("web08_empresas", "qa_admin", "/empresas/", None, None),
        ("web09_empresa_detalle", "qa_admin", f"/empresas/{i['empresa']}/", None, 1700),
        ("web10_sucursales", "qa_admin", "/sucursales/", None, None),
        ("web11_sucursal_form", "qa_admin", "/sucursales/nuevo/", None, 1400),
        ("web12_sucursal_detalle", "qa_admin", f"/sucursales/{i['sucursal']}/", None, 1400),
        ("web13_tecnicos", "qa_encargado", "/tecnicos/", None, None),
        ("web14_tecnico_form", "admin", "/tecnicos/nuevo/", None, 1500),
        ("web15_tecnico_detalle", "qa_encargado", f"/tecnicos/{i['tecnico']}/", None, 1300),
        ("web17_tickets", "qa_admin", "/tickets/", None, None),
        ("web18_ticket_form", "qa_admin", "/tickets/nuevo/", None, 1500),
        ("web19_tickets_filtro", "qa_admin", "/tickets/?estado=ABIERTO&prioridad=", None, None),
        ("web20_ticket_detalle", "qa_admin", "/tickets/QA-00014/", None, 1500),
        ("web21_publicar_oferta", "qa_encargado", "/tickets/QA-00015/publicar-oferta/", None, 1500),
        ("web22_ofertas", "qa_tecnico", "/ofertas/", None, None),
        ("web23_oferta_detalle", "qa_tecnico", f"/ofertas/{i['oferta']}/", None, 1300),
        ("web25_tomar_confirmar", "qa_tecnico", f"/ofertas/{i['oferta']}/", CLIC_TEXTO % "tomar oferta", None),
        ("web26_ordenes", "qa_admin", "/ordenes/", None, None),
        ("web27_orden_detalle", "qa_encargado", f"/ordenes/{i['orden_ejecucion']}/", None, 1500),
        ("web28_orden_tecnico_contacto", "qa_tecnico", f"/ordenes/{i['orden_asignada']}/", None, 1500),
        ("web29_cerrar_orden", "qa_encargado", f"/ordenes/{i['orden_resuelta']}/", ELEGIR % "CERRADA", 1500),
        ("web31_mantenimiento", "qa_admin", "/mantenimiento/", None, None),
        ("web32_plan_form", "qa_admin", "/mantenimiento/nuevo/", None, 1300),
        ("web34_plan_detalle", "qa_admin", f"/mantenimiento/{i['plan']}/", None, 1300),
        ("web35_dashboard", "qa_admin", "/", None, 1800),
        ("web36_reportes", "qa_admin", "/reportes/", None, 1900),
        ("web38_acceso_denegado", "qa_encargado", "/reportes/", None, None),
        ("web39_menu_usuario", "qa_admin", "/", "(() => { const t = document.querySelector('[data-bs-toggle=dropdown]'); if (t) t.click(); return !!t; })()", None),
    ]


def main():
    salida = Path(sys.argv[1] if len(sys.argv) > 1 else "capturas-web")
    salida.mkdir(parents=True, exist_ok=True)
    chrome = Chrome()
    try:
        for archivo, usuario, ruta, codigo, alto in capturas(ids()):
            chrome.entrar_como(usuario)
            chrome.ir(ruta)
            if codigo:
                ok = chrome.js(codigo)
                time.sleep(1.0)
                if not ok:
                    print(f"  aviso: la acción de {archivo} no encontró el elemento")
            chrome.foto(salida / f"{archivo}.png", alto)
            print(f"  {archivo}  ({ruta}, {usuario or 'sin sesión'})")
    finally:
        chrome.cerrar()


if __name__ == "__main__":
    main()
