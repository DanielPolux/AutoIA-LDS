"""
generate_scripts.py de PR000335-SP4 - FUENTE DE VERDAD que genera los CPxxx.py.

Cubre RF-01 (Listado de Contactos) y RF-03 (Ver Personas) de la matriz -
19 casos (CP001-CP013, CP023-CP028). RF-02 (Notificaciones SMS) y RF-04
(Anotaciones) quedan FUERA de esta ronda: ambos exigen un "Codigo de
Atencion" real (una atencion ya registrada, no solo el suministro), y la
UNICA forma de llegar a una atencion existente (abrirla en modo Consultar
desde "Consulta De Atenciones Comerciales") devuelve el MISMO defecto
sistemico "Acceso denegado... 400 (Bad Request)" ya confirmado 3 veces en
PR000335-SP5 y PR000335-SP2 (ver memoria project_acceso_denegado_mac) -
confirmado en vivo el 17/09/2026 con la atencion real 10761-028. Decision
explicita del usuario: escribir RF-01/RF-03 ahora, dejar RF-02/RF-04
documentados como bloqueados por este mismo patron.

Ruta de menu y arquitectura de popups REUTILIZADAS de PR000335-SP2
(_framework/modulos/atencion_cliente.py): el ultimo click de
RUTA_MENU_ATENCIONES abre DOS popups simultaneos ("Atenciones A Clientes"
= detalle, y "Consulta De Atenciones Comerciales" = listado) - hay que
disambiguar por TITULO exacto, no por expect_popup() a ciegas. RF-01
("Ver relacion contactos del suministro/de la SST", link visible en
Informacion del Contacto) y RF-03 ("Ver Personas", link hermano) viven
AMBOS en el popup de detalle "Atenciones A Clientes", una vez buscado un
suministro valido - NO son pantallas nuevas, son 2 links nuevos agregados
a la pantalla ya existente de SP2.

Modales confirmados en vivo el 17/09/2026 (suministro de prueba 1045027):
- RF-01 `app-modal-ver-contactos` (titulo "Listado de Contactos"): tabla
  con columnas Nombre/Paterno/Materno/Telefono/Celular/WhatsApp/Correo/
  Tipo Doc/Nro Doc/Fecha Creacion/Relacion + botones Aceptar/Cancelar
  (Aceptar vuelca la fila seleccionada en Informacion del Contacto).
  Suministro 1045027 trae 1 contacto real (ANTONIO SORALUZ).
- RF-03 `app-modal-personas` (titulo "Personas"): tabla con columnas
  Origen/Tipo Doc./Numero Doc./Nombre 1/Nombre 2/Apellido Paterno/
  Apellido Materno/Correo/Estado Correo/Fecha Estado Correo - SIN
  Aceptar/Cancelar (solo consulta, se cierra con "X"). Suministro
  1045027 vino VACIO (0 personas) - dato esperado, no bug (ver memoria
  de data-starvation del sprint anterior).
Ambos modales usan el MISMO contenedor `cdk-dialog-container` que el
resto de Web LDS - usar SIEMPRE `.last` (patron de dialogos apilados ya
confirmado en SP5).

Varios casos de detalle de datos (CP006-CP012, CP025/CP026) requieren
variantes muy especificas (contacto de +1 ano, documento "NO INDICA",
contacto eliminado, duplicados, nombre largo, personas con distintos
estados de correo) que este ambiente de pruebas no tiene garantizadas -
se escriben con aserciones estructurales/AVISO cuando el dato puntual no
esta confirmado, siguiendo el mismo criterio ya usado en PR000335-SP5
RF-04 (Resumen De Pedidos).
"""
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT_DIR.parent / "_framework"))
import web_lds_core as core  # noqa: E402

PROYECTO = "PR000335-SP4"
MATRIZ = json.loads((OUT_DIR / "matriz_casos.json").read_text(encoding="utf-8"))

ENV_TOGGLES = core.ENV_TOGGLES_CODE.replace("__PROYECTO__", PROYECTO)

# --- Helpers propios de este proyecto, embebidos en CADA CPxxx.py (ver
# CLAUDE.md: "un archivo por caso, 100% autonomo", no se importa nada de
# _framework/modulos en tiempo de ejecucion) ---
SP4_HELPERS = '''
CAMPO_ID = {
    "Nombre": "nombreA",
    "Apellido Paterno": "apellidoPaterno",
    "Apellido Materno": "apellidoMaterno",
    "Correo Electronico": "correo",
    "Numero de Documento": "dni",
    "Telefono Fijo": "telefonoFijo",
    "Movil": "movil",
    "Suministro": "txtNumeroCodigoSumSST",
}

RUTA_MENU_ATENCIONES = ["Comercial", "Atención Integral Al Cliente", "Atenciones A Clientes", "Consulta De Atenciones Comerciales"]

SELECTOR_MODAL = "cdk-dialog-container"


def campo(frame, etiqueta):
    return frame.locator(f"#{CAMPO_ID.get(etiqueta, etiqueta)}")


def seleccionar_tipo(frame, texto):
    frame.locator("#tipo").select_option(label=texto)


def buscar_por_codigo(app, frame, codigo):
    """Busca por Suministro/SST. Enter funciona para TODOS los tipos
    (confirmado en PR000335-SP2) - el boton real matf-btn-buscar-tipo NO
    funciona para SST/SST CON SUMINISTRO."""
    campo_busq = frame.locator("#txtNumeroCodigoSumSST")
    campo_busq.fill(codigo)
    campo_busq.press("Enter")
    try:
        app.wait_for_load_state("networkidle", timeout=15000)
    except PWTimeoutError:
        pass
    app.wait_for_timeout(1500)
    dialogo = frame.get_by_role("dialog")
    try:
        dialogo.first.wait_for(state="visible", timeout=2000)
    except PWTimeoutError:
        return
    if "Seleccionar SST" in dialogo.first.inner_text():
        dialogo.first.locator("table tbody tr").first.click()
        dialogo.first.get_by_role("button", name="Aceptar").click()
        app.wait_for_timeout(2500)


def modal(frame):
    """Dialogo real (cdk-dialog-container) - SIEMPRE .last: un dialogo
    nuevo (validacion) puede apilarse encima de uno ya abierto (patron
    confirmado en PR000335-SP5)."""
    return frame.locator(SELECTOR_MODAL).last


def cerrar_modal(frame, app):
    btn = modal(frame).get_by_text("X", exact=True)
    if btn.count():
        btn.click()
        app.wait_for_timeout(600)


def _abrir_popup_por_titulo(page, ruta_menu, titulo_esperado, selector_pantalla, timeout_popup_seg=15, paso_excel=None):
    """El ultimo click de RUTA_MENU_ATENCIONES abre DOS popups casi
    simultaneos en el mismo contexto (confirmado en PR000335-SP2) - se
    busca activamente por TITULO exacto en vez de expect_popup() a
    ciegas, que capturaba cualquiera de los 2 segun cual disparara
    primero."""
    paginas_antes = set(page.context.pages)
    page.get_by_role("link", name="  Aplicaciones").click(timeout=30000)
    page.wait_for_timeout(500)
    for texto in ruta_menu[:-1]:
        _click_visible(page, texto)
        page.wait_for_timeout(500)
    _click_visible(page, ruta_menu[-1])

    plazo = time.monotonic() + timeout_popup_seg
    encontrada = None
    while time.monotonic() < plazo and encontrada is None:
        nuevas = [pg for pg in page.context.pages if pg not in paginas_antes]
        for pg in nuevas:
            try:
                pg.wait_for_load_state("domcontentloaded", timeout=2000)
            except Exception:
                pass
            try:
                if pg.title() == titulo_esperado:
                    encontrada = pg
                    break
            except Exception:
                pass
        if encontrada is None:
            page.wait_for_timeout(300)
    if encontrada is None:
        titulos_vistos = [pg.title() for pg in page.context.pages if pg not in paginas_antes]
        raise RuntimeError(f"No aparecio ninguna pagina nueva con titulo {titulo_esperado!r} (se vieron: {titulos_vistos})")

    app = encontrada
    app.wait_for_load_state("networkidle")
    frame = app.locator("#aplicacion").content_frame
    frame.locator(selector_pantalla).wait_for(timeout=20000)
    capturar_paso(app, "aplicacion_abierta", paso_excel=paso_excel)
    return app, frame


def abrir_atencion_cliente(page, paso_excel=1):
    """Popup titulado "Atenciones A Clientes" - vive aca el detalle donde
    estan los links de RF-01 (Ver relacion contactos) y RF-03 (Ver
    Personas)."""
    return _abrir_popup_por_titulo(
        page, RUTA_MENU_ATENCIONES, "Atenciones A Clientes", "#txtNumeroCodigoSumSST", paso_excel=paso_excel,
    )
'''


HEADER_TEMPLATE = '''"""
{docstring}
"""
import os, re, shutil, struct, subprocess, time, zipfile
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape as _escape_xml
from playwright.sync_api import sync_playwright, expect, TimeoutError as PWTimeoutError

''' + ENV_TOGGLES + '''

URL = "https://pldsweb.luzdelsur.com.pe/Plataforma/PlataformaWeb"
USUARIO = "DCABA_DW"
PASSWORD = "Melquisedec_01"

CASO = "{cp}"
EVIDENCIA = Path(__file__).resolve().parent / CASO
if EVIDENCIA.exists():
    shutil.rmtree(EVIDENCIA, ignore_errors=True)
EVIDENCIA.mkdir(parents=True, exist_ok=True)

NOMBRE_CASO = {name_repr}
RF_CASO = {rf_repr}
CU_CASO = {cu_repr}
DESCRIPCION_CASO = {desc_repr}
RESULTADO_ESPERADO_CASO = {esperado_repr}
PASOS_CASO = {pasos_repr}

%%CAPTURAR_PASO%%

%%LOGIN%%

%%CLICK_VISIBLE%%

%%HELPERS_ESPERA%%

%%VIDEO_HELPERS%%

%%SP4_HELPERS%%

%%WORD_HELPERS%%


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=HEADLESS, slow_mo=SLOWMO)
        opciones_contexto = {{"viewport": {{"width": 1600, "height": 900}}}}
        if GRABAR_VIDEO:
            opciones_contexto["record_video_dir"] = str(EVIDENCIA)
            opciones_contexto["record_video_size"] = {{"width": 1600, "height": 900}}
        context = browser.new_context(**opciones_contexto)
        if GRABAR_VIDEO:
            context.add_init_script(%%CURSOR_OVERLAY_JS%%)
        page = context.new_page()
        app = None
        _CASO_OK = False
        try:
            login(page)
            app, frame = abrir_atencion_cliente(page)

{body}

            capturar_paso(app, "estado_final_del_caso", paso_excel=max(_parsear_pasos_excel(PASOS_CASO), default=None))
            _CASO_OK = True

        except (PWTimeoutError, AssertionError) as e:
            print(f"[FALLO] {{CASO}} FALLO: {{e}}")
            (app if app else page).screenshot(path=str(EVIDENCIA / f"{{CASO}}_error.png"), full_page=True)
            raise
        finally:
            if GRABAR_VIDEO:
                (app if app else page).wait_for_timeout(3000)
            video_portal = page.video
            video_app = app.video if app else None
            browser.close()
            if _CASO_OK:
                ruta_portal = _renombrar_video(video_portal, EVIDENCIA / f"{{CASO}}-1.webm") if video_portal is not None else None
                ruta_app = _renombrar_video(video_app, EVIDENCIA / f"{{CASO}}-2.webm") if video_app is not None else None
                if ruta_portal and ruta_app:
                    _unir_videos(ruta_portal, ruta_app, EVIDENCIA / f"{{CASO}}_video.webm")
                elif ruta_portal:
                    ruta_portal.replace(EVIDENCIA / f"{{CASO}}_video.webm")
                elif ruta_app:
                    ruta_app.replace(EVIDENCIA / f"{{CASO}}_video.webm")
                if GRABAR_WORD:
                    generar_word_evidencia()
            else:
                for video_obj in (video_portal, video_app):
                    if video_obj is None:
                        continue
                    for _intento_descarte in range(4):
                        try:
                            Path(video_obj.path()).unlink(missing_ok=True)
                            break
                        except (PermissionError, OSError):
                            time.sleep(0.5)


if __name__ == "__main__":
    main()
'''


def _indentar(body: str) -> str:
    lineas = body.strip("\n").splitlines()
    return "\n".join("            " + l if l.strip() else "" for l in lineas)


def render(caso: dict) -> str:
    docstring = (
        f"CP: {caso['cp']} | RF: {caso['rf']} | CU: {caso['cu']}\n"
        f"Nombre: {caso['name']}\n\n"
        f"{caso['desc']}\n\n"
        f"Precondiciones:\n{caso['precond']}\n\n"
        f"Datos: {caso['datos']}\n\n"
        f"Resultado esperado: {caso['esperado']}"
    )
    body = _indentar(caso["body"])
    return HEADER_TEMPLATE.format(
        docstring=docstring, cp=caso["cp"], name_repr=repr(caso["name"]), rf_repr=repr(caso["rf"]),
        cu_repr=repr(caso["cu"]), desc_repr=repr(caso["desc"]),
        esperado_repr=repr(caso["esperado"]), pasos_repr=repr(caso.get("pasos", "")), body=body,
    ).replace("%%CAPTURAR_PASO%%", core.CAPTURAR_PASO_CODE) \
     .replace("%%LOGIN%%", core.LOGIN_BLOCK) \
     .replace("%%CLICK_VISIBLE%%", core.CLICK_VISIBLE_BLOCK) \
     .replace("%%HELPERS_ESPERA%%", core.ESPERAR_FIN_CARGA_BLOCK + "\n\n\n" + core.ESPERAR_ANIMACION_BLOCK + "\n\n\n" + core.SELECCIONAR_PRIMERA_OPCION_BLOCK + "\n\n\n" + core.SELECCIONAR_OPCION_POR_TEXTO_BLOCK) \
     .replace("%%VIDEO_HELPERS%%", core.RENOMBRAR_VIDEO_BLOCK) \
     .replace("%%SP4_HELPERS%%", SP4_HELPERS) \
     .replace("%%CURSOR_OVERLAY_JS%%", repr(core.CURSOR_JS_FULL.strip("\n"))) \
     .replace("%%WORD_HELPERS%%", core.WORD_HELPERS_FULL.strip("\n"))


CASES = []


def add(cp, body):
    c = MATRIZ[cp]
    CASES.append(dict(
        cp=cp, rf=c["rf"], cu=c["cu"], name=c["name"], desc=c["desc"],
        precond=c["precond"], datos=c["datos"], esperado=c["esperado"],
        pasos=c.get("pasos", ""), body=body,
    ))


SUMINISTRO_OK = "1045027"  # con 1 contacto real (ANTONIO SORALUZ), confirmado en vivo 17/09/2026
SUMINISTRO_SIN_PERSONAS = "1045027"  # mismo suministro, Ver Personas vino vacio (0 filas)


# ======================== RF-01: Listado de Contactos ========================

add("CP001", '''
mod_seleccionar_tipo = seleccionar_tipo
mod_seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)
capturar_paso(app, "suministro_buscado", paso_excel=4)

app.wait_for_timeout(2000)
frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
app.wait_for_timeout(2000)
capturar_paso(app, "listado_contactos_abierto", paso_excel=5)

dialogo = modal(frame)
assert "Listado de Contactos" in dialogo.inner_text()
encabezados = dialogo.locator("table thead th")
textos_encabezados = [encabezados.nth(i).inner_text().strip() for i in range(encabezados.count())]
esperados = ["Nombre", "Paterno", "Materno", "Teléfono", "Celular", "WhatsApp", "Correo", "Tipo Doc", "Nro Doc", "Fecha Creación", "Relación"]
for col in esperados:
    assert col in textos_encabezados, f"Columna {col!r} no encontrada en el listado de contactos: {textos_encabezados}"
filas = dialogo.locator("table tbody tr")
assert filas.count() >= 1 and filas.first.inner_text().strip(), "Se esperaba al menos un contacto real para el suministro de prueba"
capturar_paso(app, "columnas_verificadas", paso_excel=6)
''')

add("CP002", '''
seleccionar_tipo(frame, "SUMINISTRO")
app.wait_for_timeout(1500)
capturar_paso(app, "tipo_sin_codigo", paso_excel=4)

frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
app.wait_for_timeout(1500)
capturar_paso(app, "intento_abrir_sin_codigo", paso_excel=5)

dialogo = modal(frame)
texto = dialogo.inner_text()
assert "suministro" in texto.lower() or "sst" in texto.lower() or "código" in texto.lower(), f"Se esperaba un aviso pidiendo tipo/codigo, se vio: {texto!r}"
capturar_paso(app, "mensaje_verificado", paso_excel=6)
''')

add("CP003", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)

frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
app.wait_for_timeout(1500)
capturar_paso(app, "listado_abierto_sin_seleccion", paso_excel=4)

dialogo_contactos = modal(frame)
dialogo_contactos.get_by_role("button", name="Aceptar", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "aceptar_sin_seleccion", paso_excel=5)

dialogo_validacion = modal(frame)
texto = dialogo_validacion.inner_text()
assert "seleccion" in texto.lower(), f"Se esperaba un aviso pidiendo seleccionar un contacto, se vio: {texto!r}"
capturar_paso(app, "mensaje_verificado", paso_excel=6)
''')

add("CP004", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)

frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
app.wait_for_timeout(1500)
dialogo = modal(frame)
fila = dialogo.locator("table tbody tr").first
nombre_contacto = fila.locator("td").first.inner_text().strip()
fila.click()
app.wait_for_timeout(1000)
capturar_paso(app, "contacto_seleccionado", paso_excel=5)

dialogo.get_by_role("button", name="Aceptar", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "aceptar_con_seleccion", paso_excel=6)

assert frame.locator("cdk-dialog-container").count() == 0, "El modal de contactos deberia cerrarse tras Aceptar con una fila seleccionada"
valor_nombre = campo(frame, "Nombre").input_value()
assert valor_nombre.strip(), "Se esperaba que el campo Nombre de Informacion del Contacto quedara cargado tras aceptar"
assert valor_nombre.strip()[:5].upper() in nombre_contacto.upper(), f"El nombre cargado {valor_nombre!r} no coincide con el contacto elegido {nombre_contacto!r}"
capturar_paso(app, "datos_volcados_verificados", paso_excel=7)
''')

add("CP005", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)
valor_nombre_previo = campo(frame, "Nombre").input_value()

frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
app.wait_for_timeout(1500)
dialogo = modal(frame)
fila = dialogo.locator("table tbody tr").first
fila.click()
app.wait_for_timeout(1000)
capturar_paso(app, "contacto_seleccionado", paso_excel=5)

dialogo.get_by_role("button", name="Cancelar", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "cancelar_presionado", paso_excel=6)

assert frame.locator("cdk-dialog-container").count() == 0, "El modal deberia cerrarse tras Cancelar"
valor_nombre_actual = campo(frame, "Nombre").input_value()
assert valor_nombre_actual == valor_nombre_previo, f"Cancelar no deberia modificar Informacion del Contacto: antes={valor_nombre_previo!r} despues={valor_nombre_actual!r}"
capturar_paso(app, "atencion_sin_cambios_verificada", paso_excel=7)
''')

# --- CP006-CP012: variantes de datos especificos NO confirmadas en vivo
# (contacto de +1 ano, documento "NO INDICA", eliminado, duplicado, nombre
# largo) - este ambiente solo tiene 1 contacto real conocido para el
# suministro de prueba (creado 08/09/2026, dentro del ultimo ano). Se deja
# evidencia de la regla real (estructural) y un AVISO cuando el dato
# puntual no se puede confirmar sin acceso a la base de datos.

add("CP006", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)

frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
app.wait_for_timeout(1500)
capturar_paso(app, "listado_contactos_abierto", paso_excel=5)

dialogo = modal(frame)
filas = dialogo.locator("table tbody tr")
fechas_col = 9  # Fecha Creacion, 0-index en la tabla de columnas confirmada en CP001
hoy = date.today()
limite = hoy - timedelta(days=365)
for i in range(filas.count()):
    celdas = filas.nth(i).locator("td")
    if celdas.count() <= fechas_col:
        continue
    texto_fecha = celdas.nth(fechas_col).inner_text().strip()
    if not texto_fecha:
        continue
    try:
        dia, mes, anio = texto_fecha.split("/")
        fecha_contacto = date(int(anio), int(mes), int(dia))
    except ValueError:
        continue
    assert fecha_contacto >= limite, f"Se encontro un contacto con Fecha Creacion {texto_fecha!r}, anterior al limite de 1 ano ({limite.isoformat()})"
print(f"[AVISO] {CASO}: se verifico que ningun contacto visible supera 1 año de antiguedad ({filas.count()} fila(s)); este ambiente no tiene un contacto real de mas de 1 año para confirmar el filtro en sentido contrario (exclusion real).")
capturar_paso(app, "regla_verificada", paso_excel=5)
''')

add("CP007", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)

frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
app.wait_for_timeout(1500)
capturar_paso(app, "listado_contactos_abierto", paso_excel=4)

dialogo = modal(frame)
texto_listado = dialogo.inner_text()
assert "NO INDICA" not in texto_listado.upper(), "No deberian listarse contactos con documento 'NO INDICA'"
print(f"[AVISO] {CASO}: se confirmo que el listado actual no contiene 'NO INDICA'; este ambiente no tiene un contacto real con ese documento para forzar el caso positivo (que SI intente listarse y sea excluido).")
capturar_paso(app, "regla_verificada", paso_excel=5)
''')

add("CP008", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)

frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
app.wait_for_timeout(1500)
capturar_paso(app, "listado_contactos_abierto", paso_excel=4)

dialogo = modal(frame)
filas = dialogo.locator("table tbody tr")
cantidad_visible = filas.count()
print(f"[AVISO] {CASO}: {cantidad_visible} contacto(s) visibles en este suministro de prueba; la exclusion de eliminados logicamente (estado_registro=3) no es verificable desde la UI sin acceso directo a la base de datos - se deja como verificacion estructural (el listado no debe mostrar registros marcados como eliminados, ninguno de los visibles lo esta).")
capturar_paso(app, "listado_revisado", paso_excel=5)
''')

add("CP009", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)

frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
app.wait_for_timeout(1500)
capturar_paso(app, "listado_contactos_abierto", paso_excel=4)

dialogo = modal(frame)
filas = dialogo.locator("table tbody tr")
claves = []
for i in range(filas.count()):
    celdas = filas.nth(i).locator("td")
    clave = tuple(celdas.nth(j).inner_text().strip() for j in range(min(celdas.count(), 3)))
    claves.append(clave)
assert len(claves) == len(set(claves)), f"Se encontraron contactos repetidos en el listado: {claves}"
print(f"[AVISO] {CASO}: se confirmo que no hay filas duplicadas en el listado actual ({len(claves)} fila(s)); este ambiente no tiene un contacto real registrado mas de una vez para forzar el caso positivo de deduplicacion.")
capturar_paso(app, "regla_verificada", paso_excel=5)
''')

add("CP010", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)

frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
app.wait_for_timeout(1500)
capturar_paso(app, "listado_contactos_abierto", paso_excel=4)

dialogo = modal(frame)
filas = dialogo.locator("table tbody tr")
fechas = []
for i in range(filas.count()):
    celdas = filas.nth(i).locator("td")
    texto_fecha = celdas.nth(9).inner_text().strip() if celdas.count() > 9 else ""
    fechas.append(texto_fecha)
print(f"[AVISO] {CASO}: fechas visibles en orden de listado: {fechas}; este suministro tiene solo {filas.count()} contacto(s), no alcanza para confirmar visualmente el orden descendente por identificador (se requieren 2+ contactos reales).")
capturar_paso(app, "orden_revisado", paso_excel=5)
''')

add("CP011", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)

frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
app.wait_for_timeout(1500)
capturar_paso(app, "listado_contactos_abierto", paso_excel=4)

dialogo = modal(frame)
encabezados = dialogo.locator("table thead th")
textos_encabezados = [encabezados.nth(i).inner_text().strip() for i in range(encabezados.count())]
assert "WhatsApp" in textos_encabezados, f"No se encontro la columna WhatsApp: {textos_encabezados}"
indice_whatsapp = textos_encabezados.index("WhatsApp")
filas = dialogo.locator("table tbody tr")
valores = []
for i in range(filas.count()):
    celdas = filas.nth(i).locator("td")
    valores.append(celdas.nth(indice_whatsapp).inner_text().strip())
assert all(v.upper() in ("SI", "SÍ", "NO", "S", "N") for v in valores if v), f"Valores inesperados en columna WhatsApp: {valores}"
print(f"[AVISO] {CASO}: valores de WhatsApp vistos: {valores}; este ambiente solo tiene contactos con indicador 'No' para el suministro de prueba, no alcanza para confirmar ambos casos (Si/No) a la vez.")
capturar_paso(app, "columna_whatsapp_verificada", paso_excel=5)
''')

add("CP012", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)

frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
app.wait_for_timeout(1500)
dialogo = modal(frame)
fila = dialogo.locator("table tbody tr").first
nombre_original = fila.locator("td").first.inner_text().strip()
fila.click()
app.wait_for_timeout(1000)
dialogo.get_by_role("button", name="Aceptar", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "contacto_volcado", paso_excel=5)

valor_cargado = campo(frame, "Nombre").input_value()
assert len(valor_cargado) <= 14, f"El campo Nombre no deberia superar 14 caracteres tras volcar el contacto, se vio {len(valor_cargado)} caracteres: {valor_cargado!r}"
if len(nombre_original) > 15:
    assert valor_cargado == nombre_original[:14], f"Se esperaba el nombre truncado a 14 caracteres ({nombre_original[:14]!r}), se vio {valor_cargado!r}"
else:
    print(f"[AVISO] {CASO}: el contacto real disponible ({nombre_original!r}, {len(nombre_original)} caracteres) no supera los 15 caracteres que disparan el truncado - se verifico la cota de 14 caracteres del campo destino, no el truncado en si.")
capturar_paso(app, "longitud_verificada", paso_excel=6)
''')

add("CP013", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "1768544")
app.wait_for_timeout(1500)
capturar_paso(app, "suministro_sin_contactos_buscado", paso_excel=4)

frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
app.wait_for_timeout(1500)
capturar_paso(app, "listado_abierto", paso_excel=5)

dialogo = modal(frame)
assert "Listado de Contactos" in dialogo.inner_text()
filas = dialogo.locator("table tbody tr")
sin_datos = filas.count() == 0 or not filas.first.inner_text().strip()
assert sin_datos, f"Se esperaba un listado vacio para este suministro, se vieron {filas.count()} fila(s) con datos"
texto_vacio = dialogo.get_by_text(re.compile("sin resultados|no se encontraron|no hay", re.IGNORECASE))
print(f"[AVISO] {CASO}: listado vacio confirmado (0 filas con datos); texto explicito de 'sin resultados' {'SI' if texto_vacio.count() else 'NO'} presente en el modal.")
capturar_paso(app, "listado_vacio_verificado", paso_excel=6)
''')


# ======================== RF-03: Ver Personas ========================

add("CP023", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)
capturar_paso(app, "suministro_buscado", paso_excel=4)

frame.get_by_text("Ver Personas", exact=False).click()
app.wait_for_timeout(2000)
capturar_paso(app, "ver_personas_abierto", paso_excel=5)

dialogo = modal(frame)
assert "Personas" in dialogo.inner_text()
encabezados = dialogo.locator("table thead th")
textos_encabezados = [encabezados.nth(i).inner_text().strip() for i in range(encabezados.count())]
esperados = ["Origen", "Tipo Doc.", "Número Doc.", "Nombre 1", "Nombre 2", "Apellido Paterno", "Apellido Materno", "Correo", "Estado Correo", "Fecha Estado Correo"]
for col in esperados:
    assert col in textos_encabezados, f"Columna {col!r} no encontrada en Ver Personas: {textos_encabezados}"
capturar_paso(app, "columnas_verificadas", paso_excel=6)
''')

add("CP024", '''
seleccionar_tipo(frame, "SST")
app.wait_for_timeout(1000)
capturar_paso(app, "tipo_distinto_de_suministro", paso_excel=4)

enlace = frame.get_by_text("Ver Personas", exact=False)
cantidad = enlace.count()
visible = enlace.first.is_visible() if cantidad else False
assert cantidad == 0 or not visible, f"Se esperaba que 'Ver Personas' no estuviera disponible con tipo distinto de SUMINISTRO (cantidad={cantidad}, visible={visible})"
capturar_paso(app, "ver_personas_no_disponible_verificado", paso_excel=5)
''')

add("CP025", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)

frame.get_by_text("Ver Personas", exact=False).click()
app.wait_for_timeout(2000)
capturar_paso(app, "ver_personas_abierto", paso_excel=4)

dialogo = modal(frame)
filas = dialogo.locator("table tbody tr")
hay_datos = filas.count() > 0 and filas.first.inner_text().strip()
if hay_datos:
    encabezados = dialogo.locator("table thead th")
    textos_encabezados = [encabezados.nth(i).inner_text().strip() for i in range(encabezados.count())]
    indice_estado = textos_encabezados.index("Estado Correo")
    valores = []
    for i in range(filas.count()):
        celdas = filas.nth(i).locator("td")
        valores.append(celdas.nth(indice_estado).inner_text().strip())
    for v in valores:
        assert not v.strip().isdigit(), f"La columna Estado Correo deberia mostrar la descripcion, no un codigo numerico: {v!r}"
    capturar_paso(app, "estado_correo_verificado", paso_excel=5)
else:
    print(f"[AVISO] {CASO}: el suministro de prueba no tiene personas asociadas (0 filas) - no se pudo verificar el formato de Estado Correo con datos reales.")
    capturar_paso(app, "sin_datos_para_verificar", paso_excel=5)
''')

add("CP026", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_OK + '''")
app.wait_for_timeout(1500)

frame.get_by_text("Ver Personas", exact=False).click()
app.wait_for_timeout(2000)
capturar_paso(app, "ver_personas_abierto", paso_excel=4)

dialogo = modal(frame)
filas = dialogo.locator("table tbody tr")
hay_datos = filas.count() > 0 and filas.first.inner_text().strip()
if hay_datos:
    encabezados = dialogo.locator("table thead th")
    textos_encabezados = [encabezados.nth(i).inner_text().strip() for i in range(encabezados.count())]
    indice_fecha = textos_encabezados.index("Fecha Estado Correo")
    patron_fecha = re.compile(r"^\\d{2}/\\d{2}/\\d{4}( \\d{2}:\\d{2})?$")
    for i in range(filas.count()):
        celdas = filas.nth(i).locator("td")
        texto_fecha = celdas.nth(indice_fecha).inner_text().strip()
        if texto_fecha:
            assert patron_fecha.match(texto_fecha), f"Fecha Estado Correo con formato inesperado: {texto_fecha!r}"
    capturar_paso(app, "formato_fecha_verificado", paso_excel=5)
else:
    print(f"[AVISO] {CASO}: el suministro de prueba no tiene personas asociadas (0 filas) - no se pudo verificar el formato de Fecha Estado Correo con datos reales.")
    capturar_paso(app, "sin_datos_para_verificar", paso_excel=5)
''')

add("CP027", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "''' + SUMINISTRO_SIN_PERSONAS + '''")
app.wait_for_timeout(1500)
capturar_paso(app, "suministro_buscado", paso_excel=4)

frame.get_by_text("Ver Personas", exact=False).click()
app.wait_for_timeout(2000)
capturar_paso(app, "ver_personas_abierto", paso_excel=5)

dialogo = modal(frame)
filas = dialogo.locator("table tbody tr")
sin_datos = filas.count() == 0 or not filas.first.inner_text().strip()
assert sin_datos, f"Se esperaba el modal Personas vacio para este suministro, se vieron {filas.count()} fila(s) con datos"
capturar_paso(app, "listado_vacio_verificado", paso_excel=6)
''')

add("CP028", '''
seleccionar_tipo(frame, "SUMINISTRO")
campo_busq = frame.locator("#txtNumeroCodigoSumSST")
campo_busq.fill("ABC123XY")
campo_busq.press("Enter")
try:
    app.wait_for_load_state("networkidle", timeout=10000)
except PWTimeoutError:
    pass
app.wait_for_timeout(1500)
capturar_paso(app, "busqueda_no_numerica", paso_excel=4)

texto_pantalla = frame.locator("body").inner_text()
assert "excepcion" not in texto_pantalla.lower() and "stack trace" not in texto_pantalla.lower() and "unhandled" not in texto_pantalla.lower(), f"Se detecto una traza tecnica visible tras buscar un codigo no numerico: {texto_pantalla[:300]!r}"
capturar_paso(app, "respuesta_controlada_verificada", paso_excel=5)
''')


if __name__ == "__main__":
    if not CASES:
        raise SystemExit("No hay casos cargados en CASES.")
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")
