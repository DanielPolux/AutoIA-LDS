"""
sesion_manual_con_red.py (GENERICO, copiar a PR0000NN\\_exploracion\\ y
ajustar los 3 valores marcados <-- TUYO - ver NUEVO_PROYECTO_CHECKLIST.md,
seccion "Metodologia para distinguir bug de automatizacion vs defecto
real").

Abre un Edge VISIBLE (headed), hace login y deja el menu "Aplicaciones"
desplegado para que el USUARIO DEL PROYECTO reproduzca un flujo A MANO
(el que sea - vos no necesitas saber de antemano cual boton/pantalla).

Mientras tanto, escucha TODAS las respuestas HTTP >= 400 (de la pestaña
principal Y de CUALQUIER popup nuevo que se abra durante la sesion) y las
vuelca a network_log.txt en tiempo real (flush inmediato) - asi podes leer
el archivo sin esperar a que la sesion termine, apenas el usuario te
avise que reprodujo el problema. Tambien registra errores de consola del
navegador (utiles cuando el error nunca llega a mostrarse en la UI).

Se queda viva ~20 minutos o hasta que se cierre el navegador a mano.

Origen: PR000335-2 (15/09/2026), usado para confirmar en vivo que el
guardado de "Modificar" en Listado de Atenciones era rechazado con 400
"Acceso Denegado" sin que el frontend mostrara ningun error - el log de
red fue la unica forma de distinguir "bug de automatizacion" de "defecto
real de la app" (ver casos_fallidos_confirmados.json / metodologia de
3 estados en generar_reporte_excel.py).
"""
import re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://.../Plataforma/PlataformaWeb"  # <-- TUYO
USER = "..."  # <-- TUYO
PASSWORD = "..."  # <-- TUYO

OUT_DIR = Path(__file__).parent
LOG_PATH = OUT_DIR / "network_log.txt"
MINUTOS_ABIERTA = 20

log_file = open(LOG_PATH, "w", encoding="utf-8")


def log(msg):
    linea = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(linea)
    log_file.write(linea + "\n")
    log_file.flush()


def click_visible(page, text):
    """Click en un <a> visible cuyo texto exacto (recortado) sea `text` -
    el mismo patron que _click_visible del framework, pero standalone
    para no depender de generate_scripts.py en un script descartable."""
    patron = re.compile(r"^\s*" + re.escape(text) + r"\s*$")
    candidatos = page.locator("a").filter(has_text=patron)
    for i in reversed(range(candidatos.count())):
        c = candidatos.nth(i)
        if c.is_visible():
            c.click()
            return True
    raise RuntimeError(f"No encontrado (exacto): {text!r}")


def hook_pagina(pg, etiqueta):
    def on_response(resp):
        try:
            if resp.status >= 400:
                try:
                    body = resp.text()[:2000]
                except Exception as e:
                    body = f"(no se pudo leer body: {e})"
                log(f"[{etiqueta}] RESPUESTA {resp.status} {resp.request.method} {resp.url}")
                log(f"    body: {body}")
        except Exception as e:
            log(f"[{etiqueta}] error leyendo response: {e}")

    def on_console(msg):
        if msg.type in ("error", "warning"):
            log(f"[{etiqueta}] CONSOLE {msg.type}: {msg.text}")

    def on_pageerror(err):
        log(f"[{etiqueta}] PAGE ERROR: {err}")

    pg.on("response", on_response)
    pg.on("console", on_console)
    pg.on("pageerror", on_pageerror)
    log(f"Hook de red instalado en pagina: {etiqueta}")


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False)
    context = browser.new_context(viewport=None)  # ventana a tamano real

    def on_new_page(pg):
        pg.wait_for_timeout(300)
        titulo = "?"
        try:
            titulo = pg.title()
        except Exception:
            pass
        hook_pagina(pg, f"popup:{titulo}")

    context.on("page", on_new_page)

    page = context.new_page()
    hook_pagina(page, "portal")
    page.goto(URL)
    page.get_by_role("textbox", name="Usuario").click()
    page.get_by_role("textbox", name="Usuario").fill(USER)
    page.get_by_role("textbox", name="Usuario").press("Tab")
    page.get_by_role("textbox", name="Contraseña").fill(PASSWORD)
    page.wait_for_timeout(1000)
    page.get_by_role("button", name="Ingresar ").click()
    page.wait_for_load_state("networkidle")

    page.get_by_role("link", name="  Aplicaciones").click(timeout=30000)
    page.wait_for_timeout(600)

    log("=" * 70)
    log("Sesion lista: login hecho, menu 'Aplicaciones' desplegado.")
    log("Pedile al usuario del proyecto que navegue A MANO desde aca y")
    log("reproduzca el flujo que falla. Cualquier respuesta HTTP >= 400")
    log("(de esta pestana o de cualquier popup nuevo) se registra sola.")
    log(f"Log en vivo (con flush) en: {LOG_PATH}")
    log(f"La ventana se queda abierta ~{MINUTOS_ABIERTA} min o hasta que se cierre a mano.")
    log("=" * 70)

    try:
        page.wait_for_timeout(MINUTOS_ABIERTA * 60 * 1000)
    except Exception as e:
        log(f"Sesion terminada: {e}")
    browser.close()
    log_file.close()
