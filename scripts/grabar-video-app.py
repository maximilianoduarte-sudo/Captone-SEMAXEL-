"""Graba un video de demostración de la app SEMAXEL Técnico en el emulador.

Recorre el flujo completo del técnico con los datos de prueba (entorno de QA):
iniciar sesión, Inicio, Ofertas (deslizar para actualizar), tomar una oferta,
registrar la llegada con GPS, iniciar el trabajo, tomar una foto con la
cámara, la firma del encargado, resolver, el historial en Mis trabajos y el
Perfil.

Lo maneja este guion con adb, a ritmo humano: los toques se ven en pantalla,
se escribe letra por letra con pausas variables y la firma se dibuja como un
trazo continuo. El video queda declarado como grabación automatizada en la
bitácora (no se presenta como grabado a mano).

Requisitos: servidor y emulador corriendo (scripts\\levantar-todo.ps1), la
app instalada y el entorno de QA cargado. Antes de empezar, el guion agrega
ofertas nuevas y resuelve los trabajos activos de qa_tecnico (un técnico solo
puede tener un trabajo activo); en el video se muestra esa regla.

Uso:
    python scripts\\grabar-video-app.py                 # graba
    python scripts\\grabar-video-app.py --ensayo        # recorre sin grabar
    python scripts\\grabar-video-app.py --salida D:\\videos\\demo.mp4

La contraseña de qa_tecnico se lee de <credenciales>\\qa.txt y nunca se
muestra.
"""

import argparse
import math
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

HERRAMIENTAS = Path(os.environ.get("SEMAXEL_HERRAMIENTAS_ANDROID", r"D:\herramientas-android"))
ADB = str(HERRAMIENTAS / "sdk" / "platform-tools" / "adb.exe")
CLAVE_QA = Path(os.environ.get("SEMAXEL_CLAVE_QA", r"D:\herramientas-servidor\credenciales\qa.txt"))
PAQUETE = "cl.semaxel.tecnico"
USUARIO = "qa_tecnico"
OFERTA = "Puerta de bodega descuadrada"   # sucursal QA Providencia (con GPS)
OTRA_OFERTA = "Cortocircuito en vitrina"   # para mostrar la regla de un trabajo activo
PYTHON_PROYECTO = Path(__file__).resolve().parent.parent / "venv" / "Scripts" / "python.exe"
GPS_SUCURSAL = (-70.6177, -33.4295)        # longitud, latitud de QA Providencia
ANCHO, ALTO = 1080, 2400


# ------------------------------------------------------------------ adb

def adb(*args, salida=False):
    r = subprocess.run([ADB, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if salida else None


def shell(*args):
    return adb("shell", *args, salida=True)


def pausa(a=0.6, b=1.3):
    time.sleep(random.uniform(a, b))


def pantalla():
    """Elementos visibles: (texto, descripción, id, centro x, centro y)."""
    shell("uiautomator", "dump", "/sdcard/ui.xml")
    xml = shell("cat", "/sdcard/ui.xml") or ""
    nodos = []
    for m in re.finditer(r"<node ([^>]*)>", xml):
        a = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
        b = re.findall(r"\d+", a.get("bounds", ""))
        if len(b) != 4:
            continue
        x1, y1, x2, y2 = map(int, b)
        nodos.append((a.get("text", ""), a.get("content-desc", ""), a.get("resource-id", ""),
                      (x1 + x2) // 2, (y1 + y2) // 2, (x1, y1, x2, y2)))
    return nodos


def buscar(texto=None, contiene=None, desc=None, rid=None, espera=15, ultimo=False, opcional=False):
    limite = time.time() + espera
    while True:
        hallados = [
            n for n in pantalla()
            if (texto is None or n[0] == texto)
            and (contiene is None or contiene.lower() in n[0].lower())
            and (desc is None or desc.lower() in n[1].lower())
            and (rid is None or n[2].endswith(rid))
        ]
        if hallados:
            return hallados[-1] if ultimo else hallados[0]
        if time.time() > limite:
            if opcional:
                return None
            raise RuntimeError(f"No apareció en pantalla: {texto or contiene or desc or rid}")
        time.sleep(0.4)


def tocar(nodo, pausa_despues=True):
    # Un dedo no cae siempre en el centro exacto.
    x = nodo[3] + random.randint(-14, 14)
    y = nodo[4] + random.randint(-8, 8)
    shell("input", "tap", str(x), str(y))
    if pausa_despues:
        pausa()


def tocar_texto(texto=None, **kw):
    tocar(buscar(texto, **kw))


def escribir(texto):
    """Letra por letra, con pausas de persona escribiendo en el celular."""
    for i, letra in enumerate(texto):
        # Entre comillas para que el shell del emulador no interprete - _ , . como opciones.
        shell("input", "text", "%s" if letra == " " else f"'{letra}'")
        time.sleep(random.uniform(0.05, 0.16))
        if letra == " " and random.random() < 0.25:
            time.sleep(random.uniform(0.2, 0.45))  # pensar la palabra siguiente
    pausa(0.4, 0.8)


def deslizar(y1, y2, x=None, ms=None):
    x = x or ANCHO // 2 + random.randint(-60, 60)
    shell("input", "swipe", str(x), str(y1), str(x + random.randint(-20, 20)), str(y2),
          str(ms or random.randint(350, 600)))
    pausa(0.7, 1.2)


def bajar(veces=1):
    for _ in range(veces):
        deslizar(1750, 900)


def subir(veces=1):
    for _ in range(veces):
        deslizar(800, 1650)


def bajar_hasta(texto=None, contiene=None, maximo=6):
    """Desliza hacia abajo hasta que aparezca el elemento y lo devuelve."""
    for _ in range(maximo):
        nodo = buscar(texto, contiene=contiene, espera=1, opcional=True)
        if nodo and nodo[4] < 2050:
            return nodo
        bajar()
    return buscar(texto, contiene=contiene, espera=2)


def subir_hasta(texto=None, contiene=None, maximo=6):
    for _ in range(maximo):
        nodo = buscar(texto, contiene=contiene, espera=1, opcional=True)
        if nodo and nodo[4] > 330:
            return nodo
        subir()
    return buscar(texto, contiene=contiene, espera=2)


def ocultar_teclado():
    # Con el teclado del PC conectado al emulador, Gboard muestra una barra
    # flotante en vez del teclado completo; su botón ✓ la cierra (ESC y Atrás
    # no sirven: Atrás además vuelve a la pantalla anterior).
    if "mInputShown=true" in (shell("dumpsys", "input_method") or ""):
        shell("input", "tap", "985", "1983")
        pausa(0.4, 0.7)


CAPTURAS = None  # carpeta donde guardar capturas (opción --capturas)


def captura(nombre):
    if CAPTURAS:
        datos = subprocess.run([ADB, "exec-out", "screencap", "-p"], capture_output=True).stdout
        (CAPTURAS / f"{nombre}.png").write_bytes(datos)


def dibujar_firma(area):
    """Trazo continuo tipo firma dentro del rectángulo del panel."""
    x1, y1, x2, y2 = area
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    ancho, alto = (x2 - x1) * 0.7, (y2 - y1) * 0.35
    puntos = []
    for i in range(70):
        t = i / 69
        x = cx - ancho / 2 + ancho * t
        y = cy + alto / 2 * math.sin(t * 5.5 * math.pi) * (1 - 0.4 * t) + random.uniform(-4, 4)
        puntos.append((int(x), int(y)))
    shell("input", "motionevent", "DOWN", *map(str, puntos[0]))
    for p in puntos[1:]:
        shell("input", "motionevent", "MOVE", *map(str, p))
    shell("input", "motionevent", "UP", *map(str, puntos[-1]))
    pausa(0.3, 0.6)
    # Rúbrica: línea bajo el nombre.
    shell("input", "swipe", str(int(cx - ancho / 2.2)), str(int(cy + alto * 0.9)),
          str(int(cx + ancho / 2.4)), str(int(cy + alto * 0.75)), "420")
    pausa()


def clave_qa():
    texto = CLAVE_QA.read_text(encoding="utf-8")
    return re.search(r"Contraseña:\s*(\S+)", texto).group(1)


# --------------------------------------------------------------- escenas

def preparar_datos():
    """Ofertas nuevas y qa_tecnico libre (solo puede tener un trabajo activo).

    Primero se agregan ofertas (con qa_tecnico ocupado no se le agrega un
    trabajo en ejecución) y después se resuelven sus trabajos activos.
    """
    raiz = PYTHON_PROYECTO.parent.parent.parent
    subprocess.run([str(PYTHON_PROYECTO), "manage.py", "preparar_qa", "--agregar-trabajos"],
                   cwd=raiz, check=True, capture_output=True)
    codigo = (
        "from tickets.models import OrdenTrabajo\n"
        "from tickets.services import cambiar_estado_orden\n"
        "for o in OrdenTrabajo.objects.filter(tecnico__usuario__username='qa_tecnico',"
        " estado__in=['ASIGNADA', 'EN_EJECUCION']):\n"
        "    u = o.tecnico.usuario\n"
        "    if o.estado == 'ASIGNADA':\n"
        "        cambiar_estado_orden(o, 'EN_EJECUCION', u, {'diagnostico': 'Revision previa.'})\n"
        "    cambiar_estado_orden(o, 'RESUELTA', u, {'trabajo_realizado': 'Trabajo terminado.'})\n"
    )
    subprocess.run([str(PYTHON_PROYECTO), "manage.py", "shell", "-c", codigo],
                   cwd=raiz, check=True, capture_output=True)


def preparar():
    """Deja la app en la pantalla de login y el emulador listo (no se graba)."""
    preparar_datos()
    shell("settings", "put", "system", "show_touches", "1")
    adb("emu", "geo", "fix", str(GPS_SUCURSAL[0]), str(GPS_SUCURSAL[1]))
    shell("pm", "clear", PAQUETE)  # sesión cerrada: el video parte en el login
    for permiso in ("ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "CAMERA"):
        shell("pm", "grant", PAQUETE, f"android.permission.{permiso}")
    shell("am", "start", "-n", f"{PAQUETE}/.MainActivity")
    buscar("Ingresar", espera=20)
    time.sleep(1.5)


def escena_login():
    pausa(1.5, 2.0)
    tocar(buscar("Usuario"))
    escribir(USUARIO)
    tocar(buscar("Contraseña"))
    escribir(clave_qa())
    ocultar_teclado()
    captura("app01_login")
    tocar_texto("Ingresar")
    buscar(contiene="Hola,", espera=20)


def escena_inicio():
    pausa(2.0, 2.8)
    captura("app02_inicio")
    bajar()
    pausa(1.0, 1.6)
    subir()


def escena_ofertas_y_tomar():
    tocar_texto("Ofertas")
    buscar(contiene="oferta(s) de tus especialidades")
    pausa(1.2, 1.8)
    captura("app03_ofertas")
    deslizar(700, 1500, ms=700)  # deslizar para actualizar
    pausa(1.5, 2.0)
    tocar(buscar(contiene=OFERTA))
    buscar("Detalle de la oferta")
    pausa(1.5, 2.2)
    captura("app04_oferta_detalle")
    tocar(bajar_hasta("Tomar oferta"))
    buscar("¿Tomar esta oferta?")
    pausa(1.0, 1.5)
    captura("app05_tomar_confirmar")
    tocar(buscar("Tomar oferta", ultimo=True))  # botón del diálogo
    buscar("Registrar llegada al local (GPS)", espera=20)


def escena_un_trabajo_a_la_vez():
    """Con un trabajo activo, intenta tomar otra oferta: la app no lo deja."""
    pausa(1.5, 2.0)
    # El detalle del trabajo quedó dentro de la pestaña Ofertas: se vuelve con
    # la flecha hasta llegar al listado.
    for _ in range(3):
        if buscar(contiene="oferta(s) de tus especialidades", espera=1, opcional=True):
            break
        tocar(buscar(desc="Volver"))
    buscar(contiene="oferta(s) de tus especialidades")
    pausa(1.0, 1.5)
    tocar(buscar(contiene=OTRA_OFERTA))
    buscar("Detalle de la oferta")
    pausa(1.0, 1.5)
    tocar(bajar_hasta("Tomar oferta"))
    buscar("¿Tomar esta oferta?")
    pausa(0.8, 1.2)
    tocar(buscar("Tomar oferta", ultimo=True))
    subir_hasta(contiene="Ya tienes un trabajo activo")
    pausa(3.0, 3.8)
    captura("app05b_trabajo_activo")
    tocar_texto("Trabajos")
    tocar(buscar(contiene=OFERTA))
    buscar("Registrar llegada al local (GPS)", espera=20)


def escena_llegada_e_inicio():
    pausa(1.5, 2.2)
    captura("app06_trabajo_asignado")
    tocar_texto("Registrar llegada al local (GPS)")
    permiso = buscar(contiene="While using the app", espera=3, opcional=True) or \
        buscar(contiene="Mientras la app", espera=1, opcional=True)
    if permiso:
        tocar(permiso)
    buscar("Llegada registrada.", espera=25)
    pausa(1.5, 2.0)
    captura("app07_llegada")
    bajar_hasta("Local")
    bajar()
    pausa(1.2, 1.8)
    captura("app08_contacto_whatsapp")
    tocar(subir_hasta("Iniciar trabajo"))
    tocar(buscar("Diagnóstico *"))
    escribir("Bisagra superior suelta, la puerta roza el marco. Se cambia bisagra y se ajusta")
    tocar(buscar(contiene="Costo estimado"))
    escribir("35000")
    # Dentro de un diálogo no se cierra el teclado: tocar fuera cerraría el diálogo.
    captura("app09_iniciar")
    tocar(buscar("Iniciar", ultimo=True))
    buscar("Marcar como resuelto", espera=20)
    ocultar_teclado()


def escena_foto():
    pausa(1.2, 1.8)
    tocar(bajar_hasta(contiene="Fotos de evidencia"))
    tocar(buscar(contiene="Descripción de la próxima foto"))
    escribir("Bisagra antes del cambio")
    ocultar_teclado()
    tocar_texto("Tomar foto")
    # Cámara del emulador: obturador y confirmar.
    obturador = buscar(rid="shutter_button", espera=15, opcional=True) or \
        buscar(desc="Shutter", espera=5)
    pausa(1.5, 2.2)
    captura("app10_camara")
    tocar(obturador)
    listo = buscar(rid="done_button", espera=10, opcional=True) or buscar(desc="Done", espera=5)
    pausa(0.8, 1.2)
    tocar(listo)
    buscar("Foto subida.", espera=30)
    pausa(2.5, 3.2)
    captura("app11_fotos")
    tocar(buscar(desc="Volver"))


def escena_firma():
    buscar("Detalle del trabajo")
    pausa(1.0, 1.5)
    tocar(bajar_hasta(contiene="Firma de conformidad"))
    buscar("Guardar firma")
    pausa(1.0, 1.5)
    tocar(buscar(contiene="Nombre de quien firma"))
    escribir("Paula Rojas")
    ocultar_teclado()
    # El recuadro de firma (220 dp de alto) no aparece como elemento: se
    # ubica justo encima del botón Limpiar.
    limpiar = buscar("Limpiar")[5]
    abajo = limpiar[1] - 50
    dibujar_firma((60, abajo - 560, ANCHO - 60, abajo))
    pausa(0.8, 1.2)
    captura("app12_firma")
    tocar_texto("Guardar firma")
    buscar("Detalle del trabajo", espera=20)


def escena_resolver():
    pausa(1.2, 1.8)
    tocar(subir_hasta("Marcar como resuelto"))
    tocar(buscar("Trabajo realizado *"))
    escribir("Se cambio la bisagra superior y se ajusto la puerta. Cierra sin roce")
    tocar(buscar(contiene="Costo final"))
    escribir("38000")
    captura("app13_resolver")
    tocar(buscar("Resolver", ultimo=True))
    buscar("Resuelta", espera=20)
    ocultar_teclado()
    pausa(2.0, 2.8)
    captura("app14_resuelto")
    bajar(2)
    pausa(1.5, 2.0)


def escena_cierre():
    tocar(buscar(desc="Volver"))
    tocar_texto("Trabajos")
    buscar(contiene="Activos (")
    pausa(1.5, 2.0)
    captura("app15_trabajos")
    historial = bajar_hasta("Historial", maximo=15)
    deslizar(historial[4], 450, ms=700)  # deja "Historial" arriba
    pausa(2.0, 2.5)
    captura("app16_historial")
    tocar_texto("Perfil")
    pausa(3.0, 3.5)
    captura("app17_perfil")
    tocar_texto("Inicio")
    pausa(2.5, 3.0)


ESCENAS = [escena_login, escena_inicio, escena_ofertas_y_tomar, escena_un_trabajo_a_la_vez,
           escena_llegada_e_inicio,
           escena_foto, escena_firma, escena_resolver, escena_cierre]


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--ensayo", action="store_true", help="Recorre el flujo sin grabar.")
    p.add_argument("--velocidad", type=float, default=1.6,
                   help="Velocidad del video final (1.6 = 60 %% más rápido que la grabación).")
    p.add_argument("--capturas", help="Carpeta donde guardar capturas de cada paso.")
    p.add_argument("--salida", default=str(Path(__file__).resolve().parent.parent / "video-demo-app.mp4"))
    args = p.parse_args()

    random.seed()
    global CAPTURAS
    if args.capturas:
        CAPTURAS = Path(args.capturas)
        CAPTURAS.mkdir(parents=True, exist_ok=True)
    preparar()
    # La consola del emulador corta la ruta en los espacios: se graba en una
    # ruta temporal sin espacios y después se convierte al nombre final.
    import tempfile
    webm = Path(tempfile.gettempdir()) / "semaxel_video_demo.webm"
    if not args.ensayo:
        webm.unlink(missing_ok=True)
        adb("emu", "screenrecord", "start", "--time-limit", "600", str(webm))
        time.sleep(1.0)
    try:
        for escena in ESCENAS:
            print(f"  {escena.__name__}", flush=True)
            escena()
    finally:
        if not args.ensayo:
            adb("emu", "screenrecord", "stop")
            time.sleep(3)
        shell("settings", "put", "system", "show_touches", "0")
    if not args.ensayo:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(webm),
                        "-vf", f"setpts=PTS/{args.velocidad}", "-an",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-r", "30",
                        "-movflags", "+faststart", args.salida], check=True)
        webm.unlink(missing_ok=True)
        print(f"Video listo: {args.salida}")


if __name__ == "__main__":
    sys.exit(main())
