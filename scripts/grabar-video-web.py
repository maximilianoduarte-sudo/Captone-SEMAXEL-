"""Graba un video de demostración de la web de SEMAXEL con datos de prueba.

Recorre el ciclo de un trabajo en la web, con tres roles:

1. Encargado (qa_encargado): Dashboard, crea un ticket, publica la oferta y
   cierra con calificación un trabajo que el técnico resolvió desde la app
   (con su llegada GPS, fotos y firma).
2. Administrador (qa_admin): usuarios, empresa, sucursales, técnicos y
   mantenimiento preventivo (genera los preventivos vencidos).
3. Técnico (qa_tecnico): toma la oferta nueva y ve su orden con el contacto
   de la sucursal (el trabajo se avanza desde la app).
4. Gerencia (qa_gerencia): Dashboard y Reportes.

Lo graba Chrome sin ventana (headless) con su transmisión de pantalla
(screencast) y un cursor dibujado sobre la página que se mueve de forma
suave y marca cada clic; se escribe letra por letra con pausas variables.
El video queda declarado como grabación automatizada en la bitácora.

Requisitos: servidor en http://localhost:8000, datos de QA y Google Chrome.
Antes de grabar deja libre a qa_tecnico (un técnico solo puede tener un
trabajo activo). La contraseña de los usuarios qa_* se lee del archivo de
credenciales y nunca se muestra.

    .\\venv\\Scripts\\python.exe scripts\\grabar-video-web.py --salida D:\\videos\\web.mp4
"""

import argparse
import base64
import importlib.util
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("capturas", AQUI / "capturas-manual-web.py")
capturas = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(capturas)  # también deja Django configurado

from django.utils import timezone  # noqa: E402

from ofertas.models import OfertaTicket  # noqa: E402
from tickets.models import OrdenTrabajo  # noqa: E402
from tickets.services import cambiar_estado_orden  # noqa: E402

BASE = capturas.BASE
ANCHO, ALTO = 1440, 900
CLAVE_QA = Path(os.environ.get("SEMAXEL_CLAVE_QA", r"D:\herramientas-servidor\credenciales\qa.txt"))
TITULO_TICKET = "Enchufe sin corriente en caja 3"

CURSOR_JS = r"""
(() => {
  const crear = () => {
    if (document.getElementById('__cursor')) return;
    const c = document.createElement('div');
    c.id = '__cursor';
    c.innerHTML = '<svg width="24" height="34" viewBox="0 0 24 34"><path d="M2 2 L2 27 L8.5 20.5 L13 31 L17.5 29 L13 19 L21.5 19 Z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, {position: 'fixed', left: (localStorage.cx || 720) + 'px', top: (localStorage.cy || 450) + 'px',
      zIndex: 2147483647, pointerEvents: 'none', filter: 'drop-shadow(1px 2px 2px rgba(0,0,0,.35))'});
    document.documentElement.appendChild(c);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', crear); else crear();
  window.__moverCursor = (x, y, ms) => new Promise(listo => {
    crear();
    const c = document.getElementById('__cursor');
    const x0 = parseFloat(c.style.left), y0 = parseFloat(c.style.top), t0 = performance.now();
    const paso = t => {
      let k = Math.min(1, (t - t0) / ms);
      k = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      c.style.left = (x0 + (x - x0) * k) + 'px'; c.style.top = (y0 + (y - y0) * k) + 'px';
      if (k < 1) requestAnimationFrame(paso); else { localStorage.cx = x; localStorage.cy = y; listo(); }
    };
    requestAnimationFrame(paso);
  });
  window.__clic = (x, y) => {
    const o = document.createElement('div');
    Object.assign(o.style, {position: 'fixed', left: (x - 16) + 'px', top: (y - 16) + 'px', width: '32px', height: '32px',
      borderRadius: '50%', background: 'rgba(46,117,182,.40)', zIndex: 2147483646, pointerEvents: 'none',
      transition: 'transform .4s ease-out, opacity .4s ease-out'});
    document.documentElement.appendChild(o);
    requestAnimationFrame(() => { o.style.transform = 'scale(1.9)'; o.style.opacity = '0'; });
    setTimeout(() => o.remove(), 450);
  };
})();
"""


class Grabador:
    """Chrome headless con un hilo que recibe los cuadros del screencast."""

    def __init__(self, carpeta):
        self.carpeta = carpeta
        self.datos = tempfile.mkdtemp(prefix="semaxel-chrome-")
        self.proceso = subprocess.Popen([
            capturas.CHROME, "--headless=new", f"--remote-debugging-port={capturas.PUERTO}",
            f"--user-data-dir={self.datos}", "--hide-scrollbars", "--no-first-run",
            "--lang=es-CL", f"--window-size={ANCHO},{ALTO}", "about:blank",
        ])
        for _ in range(50):
            try:
                import urllib.request
                paginas = json.load(urllib.request.urlopen(f"http://127.0.0.1:{capturas.PUERTO}/json"))
                pagina = next(p for p in paginas if p["type"] == "page")
                break
            except Exception:
                time.sleep(0.2)
        self.ws = capturas.WebSocket(pagina["webSocketDebuggerUrl"])
        self.lock = threading.Lock()
        self.n = 0
        self.respuestas = {}
        self.eventos = {}
        self.cuadros = []
        self.vivo = True
        threading.Thread(target=self._leer, daemon=True).start()
        self.cmd("Page.enable")
        self.cmd("Emulation.setDeviceMetricsOverride", width=ANCHO, height=ALTO,
                 deviceScaleFactor=1, mobile=False)
        self.cmd("Page.addScriptToEvaluateOnNewDocument", source=CURSOR_JS)

    def _leer(self):
        while self.vivo:
            try:
                m = json.loads(self.ws.recibir())
            except Exception:
                return
            if m.get("method") == "Page.screencastFrame":
                p = m["params"]
                archivo = self.carpeta / f"{len(self.cuadros):06d}.jpg"
                archivo.write_bytes(base64.b64decode(p["data"]))
                self.cuadros.append((p["metadata"]["timestamp"], archivo))
                self._enviar({"id": 10**9 + len(self.cuadros), "method": "Page.screencastFrameAck",
                              "params": {"sessionId": p["sessionId"]}})
            elif "id" in m:
                ev = self.eventos.get(m["id"])
                if ev:
                    self.respuestas[m["id"]] = m
                    ev.set()

    def _enviar(self, mensaje):
        with self.lock:
            self.ws.enviar(json.dumps(mensaje))

    def cmd(self, metodo, **params):
        with self.lock:
            self.n += 1
            n = self.n
        ev = threading.Event()
        self.eventos[n] = ev
        self._enviar({"id": n, "method": metodo, "params": params})
        if not ev.wait(30):
            raise RuntimeError(f"Sin respuesta de Chrome: {metodo}")
        m = self.respuestas.pop(n)
        if "error" in m:
            raise RuntimeError(f"{metodo}: {m['error']}")
        return m.get("result", {})

    def js(self, codigo, esperar=False):
        r = self.cmd("Runtime.evaluate", expression=codigo, returnByValue=True, awaitPromise=esperar)
        return r.get("result", {}).get("value")

    def grabar(self):
        self.cmd("Page.startScreencast", format="jpeg", quality=88, maxWidth=ANCHO, maxHeight=ALTO,
                 everyNthFrame=1)

    def detener(self):
        try:
            self.cmd("Page.stopScreencast")
        finally:
            self.vivo = False
            self.proceso.terminate()


# ---------------------------------------------------------- acciones humanas

g = None  # Grabador activo


def pausa(a=0.6, b=1.3):
    time.sleep(random.uniform(a, b))


def esperar_carga(espera=1.0):
    time.sleep(0.4)
    for _ in range(80):
        if g.js("document.readyState") == "complete":
            break
        time.sleep(0.15)
    time.sleep(espera)


def ir(ruta):
    g.cmd("Page.navigate", url=BASE + ruta)
    esperar_carga()


BUSCAR_JS = """((sel, texto, ultimo) => {
  let els = [...document.querySelectorAll(sel)].filter(e => {
    const r = e.getBoundingClientRect(); const st = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && st.visibility !== 'hidden' && st.display !== 'none';
  });
  if (texto) els = els.filter(e => (e.innerText || e.value || e.placeholder || '').toLowerCase().includes(texto.toLowerCase()));
  const e = ultimo ? els[els.length - 1] : els[0];
  if (!e) return null;
  e.scrollIntoView({block: 'center', behavior: 'smooth'});
  window.__objetivo = e;
  return true;
})(%s, %s, %s)"""


def buscar(sel, texto=None, ultimo=False, espera=10):
    limite = time.time() + espera
    while time.time() < limite:
        if g.js(BUSCAR_JS % (json.dumps(sel), json.dumps(texto), "true" if ultimo else "false")):
            time.sleep(0.7)  # el desplazamiento suave
            r = g.js("(() => { const r = window.__objetivo.getBoundingClientRect();"
                     " return [r.left + r.width / 2, r.top + r.height / 2]; })()")
            return r
        time.sleep(0.3)
    raise RuntimeError(f"No apareció en pantalla: {sel} {texto or ''}")


def mover(x, y):
    actual = g.js("[parseFloat(localStorage.cx || 720), parseFloat(localStorage.cy || 450)]") or [720, 450]
    distancia = ((x - actual[0]) ** 2 + (y - actual[1]) ** 2) ** 0.5
    ms = int(min(1100, max(350, distancia * 0.9))) + random.randint(-60, 60)
    g.js(f"window.__moverCursor({x}, {y}, {ms})", esperar=True)
    g.cmd("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)


def clic(sel, texto=None, ultimo=False, navega=False):
    x, y = buscar(sel, texto, ultimo)
    x += random.randint(-6, 6)
    y += random.randint(-3, 3)
    mover(x, y)
    pausa(0.15, 0.35)
    g.js(f"window.__clic({x}, {y})")
    for tipo in ("mousePressed", "mouseReleased"):
        g.cmd("Input.dispatchMouseEvent", type=tipo, x=x, y=y, button="left", clickCount=1)
    if navega:
        esperar_carga()
    else:
        pausa(0.5, 0.9)


def escribir(sel, texto):
    clic(sel)
    for letra in texto:
        g.cmd("Input.insertText", text=letra)
        time.sleep(random.uniform(0.04, 0.13))
        if letra == " " and random.random() < 0.2:
            time.sleep(random.uniform(0.15, 0.35))
    pausa(0.4, 0.8)


def elegir(sel, opcion):
    """Elige una opción de una lista desplegable por su texto."""
    clic(sel)
    ok = g.js("""((sel, t) => { const s = document.querySelector(sel);
      const o = [...s.options].find(o => o.text.toLowerCase().includes(t.toLowerCase()));
      if (!o) return false; s.value = o.value; s.dispatchEvent(new Event('change', {bubbles: true})); return true;
    })(%s, %s)""" % (json.dumps(sel), json.dumps(opcion)))
    if not ok:
        raise RuntimeError(f"No hay opción «{opcion}» en {sel}")
    pausa(0.5, 0.9)


def desplazar(pixeles, pasos=1):
    for _ in range(pasos):
        g.js(f"window.scrollBy({{top: {pixeles}, behavior: 'smooth'}})")
        pausa(0.9, 1.4)


def arriba():
    g.js("window.scrollTo({top: 0, behavior: 'smooth'})")
    pausa(0.9, 1.2)


def clave_qa():
    return re.search(r"Contraseña:\s*(\S+)", CLAVE_QA.read_text(encoding="utf-8")).group(1)


def entrar(usuario):
    ir("/login/")
    pausa(1.2, 1.8)
    escribir("input[name=username]", usuario)
    escribir("input[name=password]", clave_qa())
    clic("button[type=submit]", navega=True)
    pausa(1.5, 2.2)


def salir():
    arriba()
    clic("[data-bs-toggle=dropdown]")
    pausa(0.8, 1.2)
    clic("a.dropdown-item", "Cerrar sesión", navega=True)
    pausa(1.0, 1.5)


# --------------------------------------------------------------- escenas

def escena_encargado():
    entrar("qa_encargado")
    desplazar(420, 2)
    pausa(1.0, 1.5)
    arriba()

    clic("a.side-link", "Tickets", navega=True)
    pausa(1.5, 2.0)
    clic("a", "Nuevo ticket", navega=True)
    elegir("select[name=sucursal]", "QA Providencia")
    elegir("select[name=categoria]", "Fallo eléctrico")
    elegir("select[name=prioridad]", "Alta")
    escribir("input[name=titulo]", TITULO_TICKET)
    escribir("textarea[name=descripcion]",
             "El enchufe de la caja 3 no tiene corriente desde la mañana. El resto de las cajas funciona.")
    clic("button[type=submit]", "Crear ticket", navega=True)
    pausa(2.0, 2.6)

    clic("a", "Publicar oferta", navega=True)
    pausa(1.2, 1.8)
    vence = timezone.localtime() + timezone.timedelta(days=2)
    clic("input[name=fecha_vencimiento]")
    g.js("document.querySelector('input[name=fecha_vencimiento]').value = %s"
         % json.dumps(vence.strftime("%Y-%m-%dT%H:%M")))
    escribir("textarea[name=observaciones]", "Llevar tester y repuesto de enchufe doble.")
    clic("button[type=submit]", "Publicar oferta", ultimo=True, navega=True)
    pausa(2.0, 2.6)

    # Cierra un trabajo que el técnico resolvió desde la app.
    clic("a.side-link", "Órdenes de Trabajo", navega=True)
    pausa(1.2, 1.8)
    orden = (OrdenTrabajo.objects.filter(estado="RESUELTA", ticket__sucursal__codigo__in=["QPR", "QNU"],
                                         evidencias__isnull=False)
             .order_by("-fecha_fin").first())
    clic(f'a[href="/ordenes/{orden.pk}/"]', navega=True)
    pausa(1.5, 2.0)
    desplazar(380, 2)
    pausa(2.0, 2.6)
    elegir("select[name=estado]", "Cerrada")
    escribir("input[name=puntuacion]", "5")
    escribir("textarea[name=comentario_calificacion]", "Trabajo limpio y rápido. Llegó dentro del plazo.")
    clic("button[type=submit]", "Aplicar transición", navega=True)
    pausa(2.2, 2.8)
    salir()


def escena_admin():
    """Administrador de la empresa: usuarios, empresa, sucursales, técnicos y mantenimiento."""
    from empresas.models import Empresa
    from tecnicos.models import Tecnico

    entrar("qa_admin")
    pausa(1.2, 1.6)
    clic("a.side-link", "Usuarios", navega=True)
    pausa(2.0, 2.6)
    clic("a.side-link", "Empresas", navega=True)
    pausa(1.0, 1.4)
    empresa = Empresa.objects.get(codigo="QA")
    clic(f'a[href="/empresas/{empresa.pk}/"]', navega=True)
    pausa(1.2, 1.6)
    desplazar(380, 2)
    pausa(1.2, 1.6)
    clic("a.side-link", "Sucursales", navega=True)
    pausa(2.0, 2.5)
    clic("a.side-link", "Técnicos", navega=True)
    pausa(1.5, 2.0)
    tecnico = Tecnico.objects.get(usuario__username="qa_tecnico")
    clic(f'a[href="/tecnicos/{tecnico.pk}/"]', navega=True)
    pausa(2.0, 2.6)
    clic("a.side-link", "Mantenimiento", navega=True)
    pausa(1.2, 1.6)
    clic("button[type=submit]", "Generar preventivos", navega=True)
    pausa(2.2, 2.8)
    salir()


def escena_tecnico():
    entrar("qa_tecnico")
    pausa(1.0, 1.5)
    oferta = OfertaTicket.objects.filter(ticket__titulo=TITULO_TICKET, estado="DISPONIBLE").latest("pk")
    clic(f'a[href="/ofertas/{oferta.pk}/"]', navega=True)
    pausa(1.5, 2.0)
    desplazar(300)
    arriba()
    clic("button", "TOMAR OFERTA")
    pausa(1.0, 1.4)
    clic("button[type=submit]", "Confirmar toma", navega=True)
    pausa(2.0, 2.6)

    clic("a.side-link", "Órdenes de Trabajo", navega=True)
    pausa(1.2, 1.6)
    orden = OrdenTrabajo.objects.get(oferta=oferta)
    clic(f'a[href="/ordenes/{orden.pk}/"]', navega=True)
    pausa(1.5, 2.0)
    x, y = buscar("a", "Escribir por WhatsApp")
    mover(x, y)
    pausa(2.5, 3.0)
    desplazar(300)
    pausa(2.0, 2.5)
    salir()


def escena_gerencia():
    entrar("qa_gerencia")
    desplazar(420, 2)
    arriba()
    clic("a.side-link", "Reportes", navega=True)
    pausa(1.5, 2.0)
    desplazar(420, 3)
    pausa(1.5, 2.0)
    arriba()
    pausa(2.0, 2.5)


def preparar_datos():
    """qa_tecnico libre: resuelve sus trabajos activos (solo puede tener uno)."""
    for o in OrdenTrabajo.objects.filter(tecnico__usuario__username="qa_tecnico",
                                         estado__in=["ASIGNADA", "EN_EJECUCION"]):
        u = o.tecnico.usuario
        if o.estado == "ASIGNADA":
            cambiar_estado_orden(o, "EN_EJECUCION", u, {"diagnostico": "Revision previa."})
        cambiar_estado_orden(o, "RESUELTA", u, {"trabajo_realizado": "Trabajo terminado."})


def video(cuadros, salida, velocidad):
    """Arma el video respetando el tiempo real entre cuadros."""
    lista = cuadros[0][1].parent / "lista.txt"
    lineas = []
    for (t, archivo), (t2, _) in zip(cuadros, cuadros[1:] + [(cuadros[-1][0] + 2.0, None)]):
        lineas.append(f"file '{archivo.as_posix()}'")
        lineas.append(f"duration {max(t2 - t, 0.001):.4f}")
    lineas.append(f"file '{cuadros[-1][1].as_posix()}'")
    lista.write_text("\n".join(lineas), encoding="utf-8")
    # Los JPEG de Chrome son de rango completo: se convierten al rango de video
    # (limitado) y se etiqueta el color como BT.709 (SDR), para que los
    # reproductores no lo muestren lavado o demasiado brillante.
    filtro = (f"setpts=PTS/{velocidad},fps=30,"
              f"scale={ANCHO}:{ALTO}:in_range=full:out_range=limited:out_color_matrix=bt709,format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-vf", filtro, "-c:v", "libx264", "-crf", "22",
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-color_range", "tv",
                    "-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=1"
                              ":matrix_coefficients=1:video_full_range_flag=0",
                    "-movflags", "+faststart", str(salida)], check=True)


def main():
    global g
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--salida", default=str(Path.home() / "Downloads" / "SEMAXEL - demo web.mp4"))
    p.add_argument("--velocidad", type=float, default=1.0)
    args = p.parse_args()

    random.seed()
    preparar_datos()
    carpeta = Path(tempfile.mkdtemp(prefix="semaxel-video-web-"))
    g = Grabador(carpeta)
    try:
        g.cmd("Page.navigate", url=BASE + "/login/")
        esperar_carga()
        g.js("localStorage.cx = 720; localStorage.cy = 450")
        g.grabar()
        time.sleep(1.5)
        for escena in (escena_encargado, escena_admin, escena_tecnico, escena_gerencia):
            print(f"  {escena.__name__}", flush=True)
            escena()
    finally:
        g.detener()
    print(f"  cuadros: {len(g.cuadros)}")
    video(g.cuadros, args.salida, args.velocidad)
    shutil.rmtree(carpeta, ignore_errors=True)
    print(f"Video listo: {args.salida}")


if __name__ == "__main__":
    main()
