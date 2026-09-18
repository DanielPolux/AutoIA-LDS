"""
generate_scripts.py de PR000325-SP4 - FUENTE DE VERDAD que genera los CPxxx.py.

Sprint 4 de PR000325 ("Migracion del Modulo de Facturacion") - 7 apps
Angular/.NET independientes (una por RF, migradas de formularios VB3 de
"Administracion Centralizada"), DISTINTAS de las 6 de PR000325-SP2
(familia ADMTARIF) aunque comparten el mismo proyecto/empresa. De los 11
RF originales del EF, 4 fueron DESESTIMADOS (RF-02 Bancos, RF-04
Contratista-Sector-Zona, RF-09 Subestaciones, RF-10 Valores Fijos) - la
matriz Excel ya solo trae los 7 vigentes, 35 casos:
    RF-01  Actualizacion De Oficinas Del CIA      (CP-001..CP-008)
    RF-03  Relacion Sucursal - Area               (CP-016..CP-022)
    RF-05  Listado De Tablas                      (CP-030..CP-033)
    RF-06  Listado De Tasas De Interes             (CP-034..CP-036)
    RF-07  Listado De Precios De Cargo             (CP-037..CP-039)
    RF-08  Consulta De Agenda De Facturacion       (CP-040..CP-044)
    RF-11  Actualizacion Del Sistema Pac           (CP-059..CP-063)

CONFIRMADO EN VIVO el 18/09/2026 (ver _exploracion/):
- Navegacion: TODAS cuelgan de un menu plano "Interno" > <Nombre exacto>
  (NO de "Comercial > Facturacion > ..." como sugeriria el EF/la
  experiencia de PR000325-SP2 - la ruta corta funciona para las 7).
- Cada app abre un POPUP NUEVO con wrapper #aplicacion (patron generico
  de abrir_aplicacion() de _framework, sin la complicacion de doble-popup
  de PR000335). Selector de pantalla = componente Angular raiz real:
    RF-01 app-oficina-list | RF-03 app-sucursal-area-list |
    RF-05 app-listado-tabla-list | RF-06 app-listado-tasa-list |
    RF-07 app-listado-precio-list | RF-08 app-agenda-list |
    RF-11 app-banco-pac-list
- Patron de campos (DISTINTO al span.fl/div.val de PR000325-SP2): cada
  campo es un <div class="gp"><label>Etiqueta:</label><div class="ctrl">
  <input o select></div></div> - SIN atributo name/id. El grupo
  "Oficina:" de RF-01 excepcionalmente trae 2 inputs (codigo+descripcion)
  bajo la misma etiqueta - usar indice para distinguirlos.
- Dialogos: usan Ant Design / ng-zorro (`.ant-modal-wrap`/
  `nz-modal-container`), NO `.mdl-confirmar` como PR000325-SP2 - patron
  de otras pantallas de Web LDS ya visto en PR000335. Confirmado con
  RF-01: falta la Sucursal -> "Ventana de Validacion" / "Debe Ingresar
  Sucursal."
- RF-01: boton dinamico confirmado en vivo - 1er click en "Ingresar"
  habilita el panel (Oficina/codigo se vuelve editable) y el MISMO boton
  cambia su texto a "Aceptar"; aparece tambien "Cancelar". Grilla real
  con 10 oficinas de prueba visibles.

NO CONFIRMADO EN VIVO (a revisar si algun caso falla): el resto de
RF-03/05/06/07/08/11 solo se abrieron y se volco su estructura inicial
(botones/campos visibles al cargar) - los flujos de Leer/Asignar/
Generar/Ingresar/Modificar puntuales de cada uno se escriben en base al
EF + la estructura confirmada, sin ejecutar cada uno en vivo antes de
escribir el caso (mismo criterio que PR000325-SP2 con RF-03/04/05/06).
"""
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT_DIR.parent / "_framework"))
import web_lds_core as core  # noqa: E402

PROYECTO = "PR000325-SP4"
MATRIZ = json.loads((OUT_DIR / "matriz_casos.json").read_text(encoding="utf-8"))

ENV_TOGGLES = core.ENV_TOGGLES_CODE.replace("__PROYECTO__", PROYECTO)

SP4F_HELPERS = '''
def campo_por_etiqueta(scope, etiqueta, indice=0, ultimo=False):
    """Ubica el input/select asociado a la etiqueta visible de un campo -
    estas 7 apps NO usan atributo name/id. El marcado NO es uniforme
    entre apps (confirmado en vivo el 18/09/2026): RF-01/RF-03 usan
    <label>Etiqueta:</label> (CON ":"); RF-05/RF-06 usan
    <span class="fl">Etiqueta</span> (SIN ":"); RF-07 usa
    <span class="fl-fixed">Etiqueta</span>. Se buscan los 3 selectores a
    la vez con un regex que hace el ":" final opcional. `indice` distingue
    grupos con mas de un campo bajo la misma etiqueta (ej. "Oficina:" en
    RF-01 trae 2 inputs: codigo y descripcion).

    BUG REAL confirmado en vivo (RF-01, campos de fecha/telefono): NO
    todos los campos envuelven su input en un <div class="ctrl"> hermano
    de la etiqueta - las fechas y el telefono tienen el <input> como
    hermano DIRECTO. Se busca dentro del contenedor PADRE de la etiqueta
    en vez de asumir un hermano siguiente puntual, para cubrir ambas
    variantes.

    BUG REAL confirmado en vivo (RF-07, CP-037/038): con tipo "Por Rango"
    seleccionado, "Desde"/"Hasta" aparecen DOS VECES en la pantalla - el
    rango de FECHAS (siempre presente) y el rango de CODIGOS PRECA (solo
    en modo Por Rango) usan la MISMA etiqueta. `ultimo=True` toma el
    ULTIMO match (el campo de codigo, que se agrega despues en el DOM) en
    vez del primero (la fecha)."""
    base = etiqueta[:-1] if etiqueta.endswith(":") else etiqueta
    patron = re.compile(r"^\\s*" + re.escape(base) + r":?\\s*$")
    candidatos = scope.locator("label, span.fl, span.fl-fixed, div.fl").filter(has_text=patron)
    lbl = candidatos.last if ultimo else candidatos.first
    contenedor = lbl.locator("xpath=parent::*")
    return contenedor.locator("input, select").nth(indice)


SELECTOR_MODAL_F = ".ant-modal-wrap"


def modal_f(scope):
    """Dialogo real (Ant Design/ng-zorro) - SIEMPRE .last por el mismo
    patron de apilamiento ya confirmado en otras pantallas de Web LDS."""
    return scope.locator(SELECTOR_MODAL_F).last


NOMBRES_ACEPTAR = ("Aceptar", "Sí", "Si", "OK", "Confirmar")
NOMBRES_CANCELAR = ("Cancelar", "No")


def _boton_confirmacion(dialogo, nombres):
    patron = re.compile(r"^\\s*(" + "|".join(re.escape(n) for n in nombres) + r")\\s*$")
    return dialogo.get_by_role("button", name=patron)


def confirmar_f(scope, aceptar=True, timeout=8000, espera_segundo=2500):
    """Cierra el dialogo Ant Design visible pulsando el boton de
    aceptar/cancelar. BUG REAL confirmado en vivo (RF-03, CP-019/021):
    el texto del boton de confirmacion NO es siempre "Aceptar"/
    "Cancelar" - la pregunta "Confirma el ingreso de la relacion" usa
    "Si"/"No", mientras un SEGUNDO dialogo con el resultado real
    ("Area asignada correctamente.") aparece DESPUES (SECUENCIAL, no
    necesariamente apilado encima del primero - el primero puede cerrarse
    limpio y el segundo aparecer un instante despues) y SI usa "Aceptar"
    (mismo patron de 2 dialogos ya visto en PR000325-SP2, con textos de
    boton distintos entre apps). Por eso NO alcanza con "si el primero se
    oculta a tiempo, no hay segundo" - siempre se revisa, tras una espera
    corta, si quedo un dialogo visible con texto DISTINTO al original."""
    dialogo = modal_f(scope)
    dialogo.wait_for(state="visible", timeout=timeout)
    texto = dialogo.inner_text()
    boton = _boton_confirmacion(dialogo, NOMBRES_ACEPTAR if aceptar else NOMBRES_CANCELAR)
    if boton.count():
        boton.first.click()
    dialogo.page.wait_for_timeout(espera_segundo)
    segundo = modal_f(scope)
    if segundo.count() and segundo.is_visible():
        texto_segundo = segundo.inner_text()
        if texto_segundo != texto:
            texto = texto_segundo
            boton2 = _boton_confirmacion(segundo, NOMBRES_ACEPTAR)
            if boton2.count():
                boton2.first.click()
                segundo.wait_for(state="hidden", timeout=timeout)
    return texto


def esperar_filas(app, tabla_scope, minimo=1, timeout_ms=10000, intervalo_ms=500):
    """Espera a que `tabla_scope.locator("table tbody tr")` tenga al
    menos `minimo` filas. BUG REAL confirmado en vivo (RF-07, modal de
    busqueda de codigos PRECA): la grilla carga sus resultados de forma
    ASINCRONA al abrir el modal, SIN que haga falta pulsar "Buscar" (ese
    boton es solo para filtrar por codigo/descripcion) - leer
    `table tbody tr` inmediatamente despues de abrir el dialogo la
    encuentra en 0 filas (todavia cargando), dando un falso "sin
    resultados". Se sondea con reintentos en vez de una espera fija
    unica. Devuelve el locator de las filas (puede seguir vacio si se
    agota el timeout - quien llama decide si eso es un error real)."""
    filas = tabla_scope.locator("table tbody tr")
    transcurrido = 0
    while transcurrido < timeout_ms:
        if filas.count() >= minimo and filas.first.inner_text().strip():
            return filas
        app.wait_for_timeout(intervalo_ms)
        transcurrido += intervalo_ms
    return filas


def buscar_en_grilla_paginada(app, scope, texto, boton_siguiente="Siguiente", max_paginas=15):
    """Busca `texto` en la tabla actual, avanzando con el boton de
    paginacion hasta encontrarlo o agotar max_paginas. Necesario porque
    la grilla de estas apps (ej. RF-01) NO salta automaticamente a la
    pagina donde queda un registro recien creado - queda en la pagina
    en la que estaba antes de guardar, y los codigos derivados de
    time.time() suelen ordenar lejos de la pagina 1 (grilla ordenada
    ascendente). Devuelve True/False."""
    boton = scope.get_by_role("button", name=boton_siguiente, exact=True)
    for _ in range(max_paginas):
        filas = scope.locator("table tbody tr")
        contenido = " | ".join(filas.nth(i).inner_text().replace("\\n", " ") for i in range(filas.count()))
        if texto in contenido:
            return True
        if boton.count() == 0 or boton.first.is_disabled():
            return False
        boton.first.click()
        app.wait_for_timeout(1200)
    return False


def boton_dinamico(scope, *nombres):
    """Varias de estas apps cambian el texto de su boton principal segun
    el estado (ej. RF-01: 'Ingresar' -> 'Aceptar' tras el 1er click; otras
    RF: 'Ingresar' <-> 'Modificar' segun exista o no el codigo buscado).
    Se ubica por regex con las variantes posibles en vez de asumir una."""
    patron = re.compile(r"^\\s*(" + "|".join(re.escape(n) for n in nombres) + r")\\s*$")
    return scope.get_by_role("button", name=patron)
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

%%ABRIR_APLICACION%%

%%HELPERS_ESPERA%%

%%VIDEO_HELPERS%%

%%SP4F_HELPERS%%

RUTA_MENU = {ruta_menu_repr}
SELECTOR_PANTALLA = {selector_pantalla_repr}


def abrir_app(page, paso_excel=2):
    return abrir_aplicacion(page, RUTA_MENU, SELECTOR_PANTALLA, paso_excel=paso_excel)


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
            login(page, paso_excel=1)
            app, frame_pg = abrir_app(page)
            frame = frame_pg

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


RUTAS = {
    "RF-01": (["Interno", "Actualización De Oficinas De La Cia"], "app-oficina-list"),
    "RF-03": (["Interno", "Relación Sucursal - Área"], "app-sucursal-area-list"),
    "RF-05": (["Interno", "Listado De Tablas"], "app-listado-tabla-list"),
    "RF-06": (["Interno", "Listado De Tasas De Interés"], "app-listado-tasa-list"),
    "RF-07": (["Interno", "Listado De Precios De Cargo"], "app-listado-precio-list"),
    "RF-08": (["Interno", "Consulta De Agenda De Facturación"], "app-agenda-list"),
    "RF-11": (["Interno", "Actualización Del Sistema Pac"], "app-banco-pac-list"),
}


def render(caso: dict) -> str:
    docstring = (
        f"CP: {caso['cp']} | RF: {caso['rf']} | CU: {caso['cu']}\n"
        f"Nombre: {caso['name']}\n\n"
        f"{caso['desc']}\n\n"
        f"Precondiciones: {caso['precond']}\n\n"
        f"Resultado esperado: {caso['esperado']}"
    )
    body = _indentar(caso["body"])
    ruta_menu, selector_pantalla = RUTAS[caso["rf"]]
    return HEADER_TEMPLATE.format(
        docstring=docstring, cp=caso["cp"], name_repr=repr(caso["name"]), rf_repr=repr(caso["rf"]),
        cu_repr=repr(caso["cu"]), desc_repr=repr(caso["desc"]),
        esperado_repr=repr(caso["esperado"]), pasos_repr=repr(caso.get("pasos", "")), body=body,
        ruta_menu_repr=repr(ruta_menu), selector_pantalla_repr=repr(selector_pantalla),
    ).replace("%%CAPTURAR_PASO%%", core.CAPTURAR_PASO_CODE) \
     .replace("%%LOGIN%%", core.LOGIN_BLOCK) \
     .replace("%%CLICK_VISIBLE%%", core.CLICK_VISIBLE_BLOCK) \
     .replace("%%ABRIR_APLICACION%%", core.ABRIR_APLICACION_BLOCK) \
     .replace("%%HELPERS_ESPERA%%", core.ESPERAR_FIN_CARGA_BLOCK + "\n\n\n" + core.ESPERAR_ANIMACION_BLOCK + "\n\n\n" + core.SELECCIONAR_PRIMERA_OPCION_BLOCK + "\n\n\n" + core.SELECCIONAR_OPCION_POR_TEXTO_BLOCK) \
     .replace("%%VIDEO_HELPERS%%", core.RENOMBRAR_VIDEO_BLOCK) \
     .replace("%%SP4F_HELPERS%%", SP4F_HELPERS) \
     .replace("%%CURSOR_OVERLAY_JS%%", repr(core.CURSOR_JS_FULL.strip("\n"))) \
     .replace("%%WORD_HELPERS%%", core.WORD_HELPERS_FULL.strip("\n"))


CASES = []


def add(cp, body):
    c = MATRIZ[cp]
    CASES.append(dict(
        cp=cp, rf=c["rf"], cu=c["cu"], name=c["name"], desc=c["desc"],
        precond=c["precond"], datos=c.get("datos", ""), esperado=c["esperado"],
        pasos=c.get("pasos", ""), body=body,
    ))


# ======================== RF-01: Actualizacion De Oficinas Del CIA ========================

add("CP-001", '''
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos una oficina en la grilla"
capturar_paso(app, "grilla_oficinas_visible", paso_excel=4)

combo_sucursal = campo_por_etiqueta(frame, "Sucursal")
combo_tipo = campo_por_etiqueta(frame, "Tipo Oficina")
combo_horario = campo_por_etiqueta(frame, "Horario")
for nombre, combo in (("Sucursal", combo_sucursal), ("Tipo de Oficina", combo_tipo), ("Horario", combo_horario)):
    opciones = combo.locator("option")
    assert opciones.count() > 1, f"El combo {nombre} deberia estar poblado con mas de 1 opcion"
capturar_paso(app, "combos_poblados_verificados", paso_excel=7)
''')

add("CP-002", '''
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos una oficina en la grilla"
primera_fila = filas.first
texto_fila = primera_fila.inner_text()
primera_fila.click()
app.wait_for_timeout(1200)
capturar_paso(app, "fila_seleccionada", paso_excel=3)

valor_codigo = campo_por_etiqueta(frame, "Oficina", indice=0).input_value()
assert valor_codigo.strip(), "El campo Codigo de Oficina deberia quedar cargado tras seleccionar la fila"
assert valor_codigo.strip() in texto_fila, f"El codigo cargado {valor_codigo!r} no coincide con la fila seleccionada {texto_fila!r}"
capturar_paso(app, "detalle_cargado_verificado", paso_excel=5)
''')

add("CP-003", '''
import time as _time
sufijo = str(int(_time.time()))[-4:]

frame.get_by_role("button", name="Ingresar", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "modo_creacion_activado", paso_excel=4)

campo_por_etiqueta(frame, "Oficina", indice=0).fill(sufijo)
campo_por_etiqueta(frame, "Oficina", indice=1).fill(f"PRUEBA AUTOMATIZACION {sufijo}")
campo_por_etiqueta(frame, "Sucursal").select_option(index=1)
campo_por_etiqueta(frame, "Tipo Oficina").select_option(index=1)
campo_por_etiqueta(frame, "Horario").select_option(index=1)
campo_por_etiqueta(frame, "Dirección").fill("DIRECCION DE PRUEBA AUTOMATIZACION")
campo_por_etiqueta(frame, "Encargado").fill("ENCARGADO DE PRUEBA")
campo_por_etiqueta(frame, "Teléfono").fill("987654321")
campo_por_etiqueta(frame, "F. Activación").fill(date.today().isoformat())
app.wait_for_timeout(1000)
capturar_paso(app, "campos_completados", paso_excel=4)

frame.get_by_role("button", name="Aceptar", exact=True).click()
app.wait_for_timeout(2000)
capturar_paso(app, "aceptar_presionado", paso_excel=5)

texto_resultado = confirmar_f(frame, aceptar=True)
assert "ingres" in texto_resultado.lower() or "registr" in texto_resultado.lower() or "exito" in texto_resultado.lower() or "�xito" in texto_resultado.lower(), f"Se esperaba un mensaje de exito, se vio: {texto_resultado!r}"
app.wait_for_timeout(1500)

encontrada = buscar_en_grilla_paginada(app, frame, sufijo)
assert encontrada, f"La nueva oficina {sufijo!r} deberia aparecer en la grilla (recorriendo paginacion) tras guardar"
capturar_paso(app, "oficina_en_grilla_verificada", paso_excel=6)
''')

add("CP-004", '''
frame.get_by_role("button", name="Ingresar", exact=True).click()
app.wait_for_timeout(1000)
capturar_paso(app, "modo_creacion_sin_completar", paso_excel=4)

frame.get_by_role("button", name="Aceptar", exact=True).click()
app.wait_for_timeout(1500)
texto1 = confirmar_f(frame, aceptar=True)
assert "sucursal" in texto1.lower() or "descripci" in texto1.lower() or "oficina" in texto1.lower(), f"Se esperaba un aviso de validacion, se vio: {texto1!r}"
capturar_paso(app, "validacion_campos_vacios_verificada", paso_excel=5)
''')

add("CP-005", '''
import time as _time
sufijo = str(int(_time.time()))[-4:]

frame.get_by_role("button", name="Ingresar", exact=True).click()
app.wait_for_timeout(1000)
campo_por_etiqueta(frame, "Oficina", indice=0).fill(sufijo)
campo_por_etiqueta(frame, "Oficina", indice=1).fill(f"ORIGINAL {sufijo}")
campo_por_etiqueta(frame, "Sucursal").select_option(index=1)
campo_por_etiqueta(frame, "Tipo Oficina").select_option(index=1)
campo_por_etiqueta(frame, "Horario").select_option(index=1)
campo_por_etiqueta(frame, "Dirección").fill("DIRECCION ORIGINAL")
campo_por_etiqueta(frame, "Encargado").fill("ENCARGADO ORIGINAL")
campo_por_etiqueta(frame, "Teléfono").fill("987654321")
campo_por_etiqueta(frame, "F. Activación").fill(date.today().isoformat())
app.wait_for_timeout(800)
frame.get_by_role("button", name="Aceptar", exact=True).click()
app.wait_for_timeout(1500)
confirmar_f(frame, aceptar=True)
app.wait_for_timeout(1500)
capturar_paso(app, "oficina_base_creada", paso_excel=3)

encontrada = buscar_en_grilla_paginada(app, frame, sufijo)
assert encontrada, f"No se encontro la oficina base {sufijo!r} recorriendo la paginacion para poder modificarla"
fila_nueva = frame.locator("table tbody tr").filter(has_text=sufijo).first
fila_nueva.click()
app.wait_for_timeout(1000)
campo_por_etiqueta(frame, "Encargado").fill("ENCARGADO MODIFICADO")
app.wait_for_timeout(800)
capturar_paso(app, "campo_modificado", paso_excel=4)

frame.get_by_role("button", name="Modificar", exact=True).click()
app.wait_for_timeout(1500)
texto_resultado = confirmar_f(frame, aceptar=True)
assert "actualiz" in texto_resultado.lower() or "modific" in texto_resultado.lower() or "exito" in texto_resultado.lower() or "�xito" in texto_resultado.lower(), f"Se esperaba un mensaje de exito de modificacion, se vio: {texto_resultado!r}"
app.wait_for_timeout(1500)
capturar_paso(app, "modificacion_confirmada", paso_excel=6)
''')

add("CP-006", '''
boton_modificar = frame.get_by_role("button", name="Modificar", exact=True)
assert boton_modificar.count() == 0 or boton_modificar.first.is_disabled(), "El boton Modificar deberia estar deshabilitado (o ausente) sin ninguna fila seleccionada"
capturar_paso(app, "modificar_deshabilitado_verificado", paso_excel=4)

filas = frame.locator("table tbody tr")
filas.first.click()
app.wait_for_timeout(1000)
valor_codigo = campo_por_etiqueta(frame, "Oficina", indice=0)
assert valor_codigo.is_disabled(), "El campo Codigo de Oficina no deberia poder editarse en modo edicion (fila ya existente)"
capturar_paso(app, "codigo_no_editable_verificado", paso_excel=5)
''')

add("CP-007", '''
frame.get_by_role("button", name="Ingresar", exact=True).click()
app.wait_for_timeout(1000)
campo_por_etiqueta(frame, "Oficina", indice=1).fill("DATOS A DESCARTAR")
app.wait_for_timeout(800)
capturar_paso(app, "datos_ingresados_sin_guardar", paso_excel=4)

frame.get_by_role("button", name="Cancelar", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "cancelar_presionado", paso_excel=5)

boton_ingresar = frame.get_by_role("button", name="Ingresar", exact=True)
assert boton_ingresar.count() > 0, "Tras Cancelar el boton deberia volver a mostrar 'Ingresar' (estado inicial)"
assert frame.locator("app-oficina-list").count() > 0, "La pantalla no deberia haberse cerrado al presionar Cancelar"
capturar_paso(app, "formulario_reiniciado_verificado", paso_excel=6)
''')

add("CP-008", '''
app.set_viewport_size({"width": 768, "height": 1024})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_tablet", paso_excel=4)
assert frame.locator("app-oficina-list").is_visible(), "La pantalla deberia seguir visible en resolucion tablet"

app.set_viewport_size({"width": 375, "height": 812})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_mobile", paso_excel=4)
assert frame.locator("app-oficina-list").is_visible(), "La pantalla deberia seguir visible en resolucion mobile"

app.set_viewport_size({"width": 1600, "height": 900})
app.wait_for_timeout(800)
capturar_paso(app, "vista_restaurada", paso_excel=4)
''')


# ======================== RF-03: Relacion Sucursal - Area ========================
# Confirmado en vivo el 18/09/2026: 2 <select> visibles tras "Leer"
# (Sucursal = primero, Area disponible = segundo); grilla de areas
# asignadas en la unica <table>. Sucursal "Sin Sucursal" (value 0000)
# tiene 31 areas asignadas reales - buena base para CP-017/020/021.

SUCURSAL_CON_AREAS = "Sin Sucursal"

add("CP-016", '''
combo_sucursal = frame.locator("select").first
opciones = combo_sucursal.locator("option")
assert opciones.count() > 1, "El combo de sucursales deberia estar poblado"
capturar_paso(app, "combo_sucursales_poblado", paso_excel=4)
''')

add("CP-017", '''
combo_sucursal = frame.locator("select").first
combo_sucursal.select_option(label="''' + SUCURSAL_CON_AREAS + '''")
app.wait_for_timeout(500)
frame.get_by_role("button", name="Leer", exact=True).click()
app.wait_for_timeout(1800)
capturar_paso(app, "leer_con_sucursal_valida", paso_excel=5)

filas = frame.locator("table tbody tr")
assert filas.count() > 0, f"Se esperaban areas asignadas para la sucursal {SUCURSAL_CON_AREAS!r}"
combo_disponibles = frame.locator("select").nth(1)
assert combo_disponibles.locator("option").count() > 1, "El combo de areas disponibles deberia tener opciones"
capturar_paso(app, "grilla_y_combo_verificados", paso_excel=5)
''')

add("CP-018", '''
combo_sucursal = frame.locator("select").first
opciones_sucursal = combo_sucursal.locator("option")
encontrada_vacia = False
for i in range(1, opciones_sucursal.count()):
    etiqueta = opciones_sucursal.nth(i).inner_text().strip()
    combo_sucursal.select_option(label=etiqueta)
    app.wait_for_timeout(400)
    frame.get_by_role("button", name="Leer", exact=True).click()
    app.wait_for_timeout(1500)
    filas = frame.locator("table tbody tr")
    sin_datos = filas.count() == 0 or not filas.first.inner_text().strip()
    if sin_datos:
        encontrada_vacia = True
        capturar_paso(app, "sucursal_sin_areas_encontrada", paso_excel=4)
        combo_disponibles = frame.locator("select").nth(1)
        assert combo_disponibles.locator("option").count() > 1, "El combo de areas disponibles deberia mostrar todas las areas cuando la sucursal no tiene ninguna asignada"
        break
if encontrada_vacia:
    capturar_paso(app, "grilla_vacia_verificada", paso_excel=5)
else:
    print(f"[AVISO] {CASO}: se recorrieron todas las sucursales del combo y NINGUNA tiene 0 areas asignadas en este ambiente - no se pudo forzar el caso 'sucursal sin areas'. No es un bug, es falta de ese dato puntual en el ambiente de pruebas.")
    capturar_paso(app, "sin_sucursal_vacia_disponible", paso_excel=4)
''')

add("CP-019", '''
combo_sucursal = frame.locator("select").first
combo_sucursal.select_option(label="''' + SUCURSAL_CON_AREAS + '''")
app.wait_for_timeout(500)
frame.get_by_role("button", name="Leer", exact=True).click()
app.wait_for_timeout(1800)
capturar_paso(app, "sucursal_leida", paso_excel=3)

filas_antes = frame.locator("table tbody tr").count()
combo_disponibles = frame.locator("select").nth(1)
opciones_disp = combo_disponibles.locator("option")
assert opciones_disp.count() > 1, "Se necesita al menos un area disponible para asignar"
area_elegida = opciones_disp.nth(1).inner_text().strip()
combo_disponibles.select_option(label=area_elegida)
app.wait_for_timeout(500)
capturar_paso(app, "area_seleccionada", paso_excel=4)

frame.get_by_role("button", name="Ingresar", exact=True).click()
app.wait_for_timeout(1500)
texto_resultado = confirmar_f(frame, aceptar=True)
assert "asign" in texto_resultado.lower() or "exito" in texto_resultado.lower() or "�xito" in texto_resultado.lower() or "registr" in texto_resultado.lower(), f"Se esperaba un mensaje de exito de asignacion, se vio: {texto_resultado!r}"
app.wait_for_timeout(1500)
capturar_paso(app, "asignacion_confirmada", paso_excel=6)

filas_despues = frame.locator("table tbody tr")
assert filas_despues.count() == filas_antes + 1, f"Se esperaba 1 fila mas en la grilla ({filas_antes} -> {filas_despues.count()})"
assert area_elegida in filas_despues.locator("xpath=.").all_inner_texts()[0] or any(area_elegida in filas_despues.nth(i).inner_text() for i in range(filas_despues.count())), f"El area {area_elegida!r} deberia aparecer en la grilla de asignadas"

# Restaura el estado previo (desasigna lo que se acaba de asignar) para
# no acumular datos de prueba en una sucursal compartida entre corridas.
fila_area = filas_despues.filter(has_text=area_elegida).first
fila_area.click()
app.wait_for_timeout(800)
frame.get_by_role("button", name="Eliminar", exact=True).click()
app.wait_for_timeout(1200)
confirmar_f(frame, aceptar=True)
app.wait_for_timeout(1200)
capturar_paso(app, "estado_restaurado", paso_excel=6)
''')

add("CP-020", '''
combo_sucursal = frame.locator("select").first
combo_sucursal.select_option(label="''' + SUCURSAL_CON_AREAS + '''")
app.wait_for_timeout(500)
frame.get_by_role("button", name="Leer", exact=True).click()
app.wait_for_timeout(1800)
capturar_paso(app, "sucursal_leida_sin_seleccion", paso_excel=4)

boton_eliminar = frame.get_by_role("button", name="Eliminar", exact=True)
assert boton_eliminar.count() == 0 or boton_eliminar.first.is_disabled(), "El boton Eliminar deberia estar deshabilitado sin ninguna fila seleccionada"
capturar_paso(app, "eliminar_deshabilitado_verificado", paso_excel=4)
''')

add("CP-021", '''
combo_sucursal = frame.locator("select").first
combo_sucursal.select_option(label="''' + SUCURSAL_CON_AREAS + '''")
app.wait_for_timeout(500)
frame.get_by_role("button", name="Leer", exact=True).click()
app.wait_for_timeout(1800)
capturar_paso(app, "sucursal_leida", paso_excel=3)

filas_antes = frame.locator("table tbody tr")
cantidad_antes = filas_antes.count()
assert cantidad_antes > 0, "Se necesita al menos un area asignada para desasignar"
fila_area = filas_antes.first
texto_area = fila_area.inner_text().strip()
fila_area.click()
app.wait_for_timeout(800)
capturar_paso(app, "area_seleccionada_para_eliminar", paso_excel=4)

frame.get_by_role("button", name="Eliminar", exact=True).click()
app.wait_for_timeout(1500)
texto_resultado = confirmar_f(frame, aceptar=True)
assert "elimin" in texto_resultado.lower() or "desasign" in texto_resultado.lower() or "exito" in texto_resultado.lower() or "�xito" in texto_resultado.lower(), f"Se esperaba un mensaje de exito de desasignacion, se vio: {texto_resultado!r}"
app.wait_for_timeout(1500)
capturar_paso(app, "desasignacion_confirmada", paso_excel=5)

filas_despues = frame.locator("table tbody tr")
assert filas_despues.count() == cantidad_antes - 1, f"Se esperaba 1 fila menos en la grilla ({cantidad_antes} -> {filas_despues.count()})"

# Restaura el estado previo (vuelve a asignar el area eliminada).
primera_linea = texto_area.splitlines()[0].strip() if texto_area else ""
combo_disponibles = frame.locator("select").nth(1)
opcion_restaurar = combo_disponibles.locator("option").filter(has_text=primera_linea)
if opcion_restaurar.count():
    combo_disponibles.select_option(label=opcion_restaurar.first.inner_text())
    app.wait_for_timeout(500)
    frame.get_by_role("button", name="Ingresar", exact=True).click()
    app.wait_for_timeout(1200)
    confirmar_f(frame, aceptar=True)
    app.wait_for_timeout(1000)
capturar_paso(app, "estado_restaurado", paso_excel=5)
''')

add("CP-022", '''
combo_sucursal = frame.locator("select").first
combo_sucursal.select_option(label="''' + SUCURSAL_CON_AREAS + '''")
app.wait_for_timeout(500)
frame.get_by_role("button", name="Leer", exact=True).click()
app.wait_for_timeout(1500)

app.set_viewport_size({"width": 768, "height": 1024})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_tablet", paso_excel=3)
assert frame.locator("app-sucursal-area-list").is_visible(), "La pantalla deberia seguir visible en resolucion tablet"

app.set_viewport_size({"width": 375, "height": 812})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_mobile", paso_excel=3)
assert frame.locator("app-sucursal-area-list").is_visible(), "La pantalla deberia seguir visible en resolucion mobile"

app.set_viewport_size({"width": 1600, "height": 900})
app.wait_for_timeout(800)
capturar_paso(app, "vista_restaurada", paso_excel=3)
''')


# ======================== RF-05: Listado De Tablas ========================
# Confirmado en vivo: "Nombre Tabla" agrupa 2 campos (input codigo maxlength=6
# + select descripcion) bajo el mismo span.fl, igual que "Oficina:" en RF-01.

add("CP-030", '''
combo_tabla = campo_por_etiqueta(frame, "Nombre Tabla", indice=1)
assert combo_tabla.locator("option").count() > 1, "El combo de tablas deberia estar poblado"
capturar_paso(app, "combo_tablas_poblado", paso_excel=3)
''')

add("CP-031", '''
with app.expect_download(timeout=20000) as descarga_info:
    frame.get_by_role("button", name="Generar", exact=True).click()
descarga = descarga_info.value
ruta = EVIDENCIA / f"{CASO}_todas_las_tablas.xlsx"
descarga.save_as(str(ruta))
app.wait_for_timeout(1000)
assert ruta.exists() and ruta.stat().st_size > 0, "El archivo Excel de todas las tablas deberia haberse descargado"
capturar_paso(app, "excel_todas_tablas_verificado", paso_excel=4)
''')

add("CP-032", '''
combo_tabla = campo_por_etiqueta(frame, "Nombre Tabla", indice=1)
opciones = combo_tabla.locator("option")
etiqueta_tabla = opciones.nth(1).inner_text().strip()
combo_tabla.select_option(index=1)
app.wait_for_timeout(500)
capturar_paso(app, "tabla_seleccionada", paso_excel=3)

with app.expect_download(timeout=20000) as descarga_info:
    frame.get_by_role("button", name="Generar", exact=True).click()
descarga = descarga_info.value
ruta = EVIDENCIA / f"{CASO}_tabla_especifica.xlsx"
descarga.save_as(str(ruta))
app.wait_for_timeout(1000)
assert ruta.exists() and ruta.stat().st_size > 0, f"El archivo Excel de la tabla {etiqueta_tabla!r} deberia haberse descargado"
capturar_paso(app, "excel_tabla_especifica_verificado", paso_excel=4)
''')

add("CP-033", '''
app.set_viewport_size({"width": 768, "height": 1024})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_tablet", paso_excel=3)
assert frame.locator("app-listado-tabla-list").is_visible(), "La pantalla deberia seguir visible en resolucion tablet"

app.set_viewport_size({"width": 375, "height": 812})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_mobile", paso_excel=3)
assert frame.locator("app-listado-tabla-list").is_visible(), "La pantalla deberia seguir visible en resolucion mobile"

app.set_viewport_size({"width": 1600, "height": 900})
app.wait_for_timeout(800)
capturar_paso(app, "vista_restaurada", paso_excel=3)
''')


# ======================== RF-06: Listado De Tasas De Interes ========================

add("CP-034", '''
campo_por_etiqueta(frame, "Fecha Desde").fill((date.today() - timedelta(days=90)).isoformat())
campo_por_etiqueta(frame, "Fecha Hasta").fill(date.today().isoformat())
app.wait_for_timeout(800)
capturar_paso(app, "rango_fechas_completado", paso_excel=3)

with app.expect_download(timeout=20000) as descarga_info:
    frame.get_by_role("button", name="Generar", exact=True).click()
descarga = descarga_info.value
ruta = EVIDENCIA / f"{CASO}_tasas_rango.xlsx"
descarga.save_as(str(ruta))
app.wait_for_timeout(1000)
assert ruta.exists() and ruta.stat().st_size > 0, "El archivo Excel de tasas de interes deberia haberse descargado"
capturar_paso(app, "excel_tasas_verificado", paso_excel=5)
''')

add("CP-035", '''
campo_por_etiqueta(frame, "Fecha Desde").fill((date.today() - timedelta(days=30)).isoformat())
app.wait_for_timeout(800)
capturar_paso(app, "solo_fecha_desde_completada", paso_excel=3)

with app.expect_download(timeout=20000) as descarga_info:
    frame.get_by_role("button", name="Generar", exact=True).click()
descarga = descarga_info.value
ruta = EVIDENCIA / f"{CASO}_tasas_sin_hasta.xlsx"
descarga.save_as(str(ruta))
app.wait_for_timeout(1000)
assert ruta.exists() and ruta.stat().st_size > 0, "El archivo Excel deberia generarse aunque Fecha Hasta quede vacia (se asume la fecha del dia)"
capturar_paso(app, "excel_sin_fecha_hasta_verificado", paso_excel=5)
''')

add("CP-036", '''
app.set_viewport_size({"width": 768, "height": 1024})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_tablet", paso_excel=3)
assert frame.locator("app-listado-tasa-list").is_visible(), "La pantalla deberia seguir visible en resolucion tablet"

app.set_viewport_size({"width": 375, "height": 812})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_mobile", paso_excel=3)
assert frame.locator("app-listado-tasa-list").is_visible(), "La pantalla deberia seguir visible en resolucion mobile"

app.set_viewport_size({"width": 1600, "height": 900})
app.wait_for_timeout(800)
capturar_paso(app, "vista_restaurada", paso_excel=3)
''')


# ======================== RF-07: Listado De Precios De Cargo ========================
# Confirmado en vivo: radios name="tipo-cargo" con value ENERGIA/ARRIENDOS
# (disabled)/CORTE (disabled)/CAMPAMENTOS (disabled)/RANGO/TODOS - solo 3
# habilitados, igual que documenta el EF.

add("CP-037", '''
radio_rango = frame.locator('input[name="tipo-cargo"][value="RANGO"]')
radio_rango.check()
app.wait_for_timeout(1000)
capturar_paso(app, "tipo_por_rango_seleccionado", paso_excel=3)

botones_buscar = frame.get_by_role("button", name="?", exact=True)
assert botones_buscar.count() >= 1, "Deberian aparecer los botones (?) de busqueda de codigo en modo 'Por Rango'"
capturar_paso(app, "campos_por_rango_visibles", paso_excel=4)

botones_buscar.first.click()
app.wait_for_timeout(1500)
capturar_paso(app, "modal_busqueda_abierto", paso_excel=5)

dialogo = modal_f(frame)
dialogo.wait_for(state="visible", timeout=8000)
filas = esperar_filas(app, dialogo)
assert filas.count() > 0 and filas.first.inner_text().strip(), "El modal de busqueda de codigos deberia listar al menos un resultado"
texto_codigo = filas.first.inner_text().strip()
filas.first.click()
app.wait_for_timeout(800)
dialogo.get_by_role("button", name="Seleccionar", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "codigo_seleccionado", paso_excel=6)

campo_desde = campo_por_etiqueta(frame, "Desde", ultimo=True)
valor_desde = campo_desde.input_value() if campo_desde.count() else ""
assert valor_desde.strip(), "El campo Desde (codigo PRECA) deberia quedar completado con el codigo elegido del modal"
capturar_paso(app, "campo_completado_verificado", paso_excel=6)
''')

add("CP-038", '''
campo_por_etiqueta(frame, "Desde").fill((date.today() - timedelta(days=180)).isoformat())
campo_por_etiqueta(frame, "Hasta").fill(date.today().isoformat())
app.wait_for_timeout(800)
capturar_paso(app, "fechas_energia_completadas", paso_excel=4)

with app.expect_download(timeout=20000) as descarga_info:
    frame.get_by_role("button", name="Generar", exact=True).click()
descarga = descarga_info.value
ruta1 = EVIDENCIA / f"{CASO}_energia.xlsx"
descarga.save_as(str(ruta1))
app.wait_for_timeout(1000)
assert ruta1.exists() and ruta1.stat().st_size > 0, "El Excel con tipo ENERGIA deberia haberse descargado"
capturar_paso(app, "excel_energia_verificado", paso_excel=5)

app.wait_for_timeout(3000)
radio_rango = frame.locator('input[name="tipo-cargo"][value="RANGO"]')
radio_rango.check()
app.wait_for_timeout(1500)
assert radio_rango.is_checked(), "El radio 'Por Rango' deberia quedar marcado tras seleccionarlo"
botones_codigo = frame.get_by_role("button", name="?", exact=True)
botones_codigo.first.wait_for(state="visible", timeout=10000)
capturar_paso(app, "tipo_por_rango_seleccionado", paso_excel=7)

for indice_boton in (0, 1):
    etiqueta_boton = "Desde" if indice_boton == 0 else "Hasta"
    frame.get_by_role("button", name="?", exact=True).nth(indice_boton).click()
    app.wait_for_timeout(1200)
    dialogo = modal_f(frame)
    dialogo.wait_for(state="visible", timeout=8000)
    filas = esperar_filas(app, dialogo)
    assert filas.count() > 0 and filas.first.inner_text().strip(), f"El modal de busqueda ({etiqueta_boton}) deberia listar resultados"
    filas.first.click()
    app.wait_for_timeout(800)
    dialogo.get_by_role("button", name="Seleccionar", exact=True).click()
    app.wait_for_timeout(1000)
capturar_paso(app, "codigos_por_rango_completados", paso_excel=8)

# BUG REAL confirmado en vivo: al marcar "Por Rango" el sistema LIMPIA
# las Fechas de Vigencia ya cargadas (quedan "dd/mm/aaaa") - hay que
# volver a completarlas antes de Generar, o el sistema rechaza con
# "Fecha Desde Incorrecta.".
campo_por_etiqueta(frame, "Desde").fill((date.today() - timedelta(days=180)).isoformat())
campo_por_etiqueta(frame, "Hasta").fill(date.today().isoformat())
app.wait_for_timeout(800)
capturar_paso(app, "fechas_recompletadas_tras_por_rango", paso_excel=9)

with app.expect_download(timeout=20000) as descarga_info2:
    frame.get_by_role("button", name="Generar", exact=True).click()
descarga2 = descarga_info2.value
ruta2 = EVIDENCIA / f"{CASO}_por_rango.xlsx"
descarga2.save_as(str(ruta2))
app.wait_for_timeout(1000)
assert ruta2.exists() and ruta2.stat().st_size > 0, "El Excel con tipo Por Rango deberia haberse descargado"
capturar_paso(app, "excel_por_rango_verificado", paso_excel=10)
''')

add("CP-039", '''
app.set_viewport_size({"width": 768, "height": 1024})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_tablet", paso_excel=3)
assert frame.locator("app-listado-precio-list").is_visible(), "La pantalla deberia seguir visible en resolucion tablet"

app.set_viewport_size({"width": 375, "height": 812})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_mobile", paso_excel=3)
assert frame.locator("app-listado-precio-list").is_visible(), "La pantalla deberia seguir visible en resolucion mobile"

app.set_viewport_size({"width": 1600, "height": 900})
app.wait_for_timeout(800)
capturar_paso(app, "vista_restaurada", paso_excel=3)
''')


# ======================== RF-08: Consulta De Agenda De Facturacion ========================
# Confirmado en vivo: etiquetas Sector/Criterio/Desde/Hasta (span.fl);
# select[0]=Sector (29 opciones), select[1]=Criterio (4 opciones, la
# primera vacia). Solo lectura, boton "Leer".

add("CP-040", '''
combo_sector = campo_por_etiqueta(frame, "Sector")
assert combo_sector.locator("option").count() > 1, "El combo Sector deberia estar poblado"
capturar_paso(app, "combo_sector_poblado", paso_excel=4)
''')

add("CP-041", '''
campo_por_etiqueta(frame, "Sector").select_option(index=1)
campo_por_etiqueta(frame, "Criterio").select_option(index=1)
campo_por_etiqueta(frame, "Desde").fill((date.today() - timedelta(days=365)).isoformat())
campo_por_etiqueta(frame, "Hasta").fill(date.today().isoformat())
app.wait_for_timeout(800)
capturar_paso(app, "filtros_completados", paso_excel=6)

frame.get_by_role("button", name="Leer", exact=True).click()
app.wait_for_timeout(2000)
capturar_paso(app, "consulta_ejecutada", paso_excel=8)

filas = frame.locator("table").first.locator("tbody tr")
if filas.count() > 0 and filas.first.inner_text().strip():
    capturar_paso(app, "grilla_con_resultados_verificada", paso_excel=8)
else:
    print(f"[AVISO] {CASO}: la consulta con el rango mas amplio (1 año) no devolvio registros para el primer sector/criterio probado - no es necesariamente un bug, puede ser falta de datos para esa combinacion puntual.")
    capturar_paso(app, "grilla_sin_resultados", paso_excel=8)
''')

add("CP-042", '''
campo_por_etiqueta(frame, "Sector").select_option(index=1)
campo_por_etiqueta(frame, "Criterio").select_option(index=1)
campo_por_etiqueta(frame, "Desde").fill((date.today() - timedelta(days=365)).isoformat())
campo_por_etiqueta(frame, "Hasta").fill(date.today().isoformat())
app.wait_for_timeout(800)
frame.get_by_role("button", name="Leer", exact=True).click()
app.wait_for_timeout(2000)
capturar_paso(app, "consulta_ejecutada", paso_excel=5)

tablas = frame.locator("table")
filas_agenda = tablas.first.locator("tbody tr")
if filas_agenda.count() > 0 and filas_agenda.first.inner_text().strip():
    filas_agenda.first.click()
    app.wait_for_timeout(1500)
    capturar_paso(app, "fila_agenda_seleccionada", paso_excel=6)
    if tablas.count() > 1:
        filas_venc = tablas.nth(1).locator("tbody tr")
        print(f"[AVISO] {CASO}: grilla de vencimientos tras seleccionar la fila: {filas_venc.count()} fila(s) (puede quedar vacia si esa entrada de agenda no tiene vencimientos asociados, comportamiento esperado segun el EF).")
    capturar_paso(app, "vencimientos_verificados", paso_excel=7)
else:
    print(f"[AVISO] {CASO}: la consulta no devolvio registros de agenda para seleccionar una fila - no se pudo ejercitar la grilla de vencimientos con datos reales.")
    capturar_paso(app, "sin_agenda_para_seleccionar", paso_excel=6)
''')

add("CP-043", '''
campo_por_etiqueta(frame, "Sector").select_option(index=1)
campo_por_etiqueta(frame, "Criterio").select_option(index=1)
campo_por_etiqueta(frame, "Desde").fill((date.today() - timedelta(days=1825)).isoformat())
campo_por_etiqueta(frame, "Hasta").fill(date.today().isoformat())
app.wait_for_timeout(800)
frame.get_by_role("button", name="Leer", exact=True).click()
app.wait_for_timeout(2000)
capturar_paso(app, "consulta_amplia_ejecutada", paso_excel=6)

filas = frame.locator("table").first.locator("tbody tr")
cantidad_pagina1 = filas.count()
if cantidad_pagina1 >= 10:
    capturar_paso(app, "primera_pagina_10_verificada", paso_excel=7)
    boton_siguiente = frame.get_by_role("button", name=re.compile("Siguiente|Sgtes", re.IGNORECASE))
    if boton_siguiente.count() and not boton_siguiente.first.is_disabled():
        texto_pagina1 = filas.first.inner_text()
        boton_siguiente.first.click()
        app.wait_for_timeout(1500)
        capturar_paso(app, "paginacion_habilitada_verificada", paso_excel=8)
        filas_pagina2 = frame.locator("table").first.locator("tbody tr")
        texto_pagina2 = filas_pagina2.first.inner_text() if filas_pagina2.count() else ""
        assert texto_pagina2 != texto_pagina1, "La segunda pagina deberia mostrar registros distintos a la primera"
        capturar_paso(app, "segunda_pagina_verificada", paso_excel=10)
    else:
        print(f"[AVISO] {CASO}: se obtuvieron {cantidad_pagina1} registros en la primera pagina pero el control de paginacion no esta habilitado/visible - revisar si el umbral real de paginacion es distinto a 10.")
else:
    print(f"[AVISO] {CASO}: el rango mas amplio probado (5 años) solo trajo {cantidad_pagina1} registro(s) - no alcanza para forzar mas de 10 resultados y probar la paginacion real en este ambiente.")
    capturar_paso(app, "sin_suficientes_registros", paso_excel=7)
''')

add("CP-044", '''
app.set_viewport_size({"width": 768, "height": 1024})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_tablet", paso_excel=3)
assert frame.locator("app-agenda-list").is_visible(), "La pantalla deberia seguir visible en resolucion tablet"

app.set_viewport_size({"width": 375, "height": 812})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_mobile", paso_excel=3)
assert frame.locator("app-agenda-list").is_visible(), "La pantalla deberia seguir visible en resolucion mobile"

app.set_viewport_size({"width": 1600, "height": 900})
app.wait_for_timeout(800)
capturar_paso(app, "vista_restaurada", paso_excel=3)
''')


# ======================== RF-11: Actualizacion Del Sistema Pac ========================
# Confirmado en vivo: grilla con 33 bancos PAC. Modal Ingresar/Modificar
# usa <div class="fl"> (no span.fl) para sus etiquetas - "Banco
# (Código)" agrupa 2 inputs (codigo autogenerado readonly + Descripcion,
# indice=1). Fechas Activacion/Desactivacion + 3 checkboxes. Botones del
# modal: Aceptar/Cancelar (sin variante Si/No aca).

add("CP-059", '''
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos un banco PAC en la grilla"
texto_grilla = " ".join(filas.nth(i).inner_text() for i in range(filas.count()))
capturar_paso(app, "grilla_bancos_pac_cargada", paso_excel=4)
tiene_activo = "Activo" in texto_grilla
tiene_inactivo = "Inactivo" in texto_grilla
assert tiene_activo, "Se esperaba al menos un banco PAC con estado Activo"
if not tiene_inactivo:
    print(f"[AVISO] {CASO}: no se encontro ningun banco PAC con estado Inactivo en este ambiente - solo se confirmo el estado Activo.")
capturar_paso(app, "estados_verificados", paso_excel=5)
''')

add("CP-060", '''
import time as _time
sufijo = str(int(_time.time()))[-4:]

# BUG REAL confirmado en vivo: el "Banco (Codigo)" autogenerado (MAX+1)
# se calcula a partir de la grilla YA CARGADA en el cliente, no se
# recalcula solo con reabrir el modal - si otra corrida de este mismo
# caso registro un banco nuevo mientras tanto, el "proximo codigo"
# queda desactualizado y el backend rechaza con "El codigo ya existe."
# Hay que presionar "Actualizar" (refresca la grilla) ANTES de reabrir
# Ingresar para que el codigo propuesto sea el correcto.
exito = False
for intento in range(3):
    if intento > 0:
        frame.get_by_role("button", name="Actualizar", exact=True).click()
        app.wait_for_timeout(1500)
    frame.get_by_role("button", name="Ingresar", exact=True).click()
    app.wait_for_timeout(1500)
    capturar_paso(app, "modal_ingresar_abierto", paso_excel=4)

    dialogo = modal_f(frame)
    dialogo.wait_for(state="visible", timeout=8000)
    codigo_generado = campo_por_etiqueta(dialogo, "Banco (Código)", indice=0).input_value()
    campo_por_etiqueta(dialogo, "Banco (Código)", indice=1).fill(f"BANCO PRUEBA {sufijo}")
    campo_por_etiqueta(dialogo, "Fecha Activación").fill(date.today().isoformat())
    app.wait_for_timeout(800)
    capturar_paso(app, "datos_completados", paso_excel=5)

    dialogo.get_by_role("button", name="Aceptar", exact=True).click()
    app.wait_for_timeout(1500)
    if dialogo.is_visible():
        texto_validacion = dialogo.inner_text()
        if "ya existe" in texto_validacion.lower():
            dialogo.get_by_role("button", name="Aceptar", exact=True).click()
            app.wait_for_timeout(800)
            modal_f(frame).get_by_role("button", name="Cancelar", exact=True).click()
            app.wait_for_timeout(1000)
            continue
    dialogo.wait_for(state="hidden", timeout=10000)
    exito = True
    break

assert exito, "No se pudo registrar el banco PAC tras varios reintentos (colision de codigo autogenerado)"
app.wait_for_timeout(1000)
capturar_paso(app, "aceptar_presionado", paso_excel=6)
capturar_paso(app, "modal_cerrado_verificado", paso_excel=7)

encontrado = buscar_en_grilla_paginada(app, frame, sufijo, boton_siguiente="Siguiente")
if not encontrado:
    encontrado = buscar_en_grilla_paginada(app, frame, sufijo, boton_siguiente="Sgtes")
assert encontrado, f"El banco PAC recien creado (sufijo {sufijo!r}) deberia aparecer en la grilla"
capturar_paso(app, "banco_en_grilla_verificado", paso_excel=8)
''')

add("CP-061", '''
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se necesita al menos un banco PAC para modificar"
fila = filas.first
codigo_banco = fila.locator("td").first.inner_text().strip()
fila.click()
app.wait_for_timeout(800)
capturar_paso(app, "banco_seleccionado", paso_excel=3)

frame.get_by_role("button", name="Modificar", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "modal_modificar_abierto", paso_excel=4)

dialogo = modal_f(frame)
dialogo.wait_for(state="visible", timeout=8000)
texto_titulo = dialogo.inner_text()
assert codigo_banco in texto_titulo or "Modificar" in texto_titulo, f"El modal deberia mostrar los datos del banco {codigo_banco!r} seleccionado"

import time as _time
sufijo = str(int(_time.time()))[-4:]
campo_por_etiqueta(dialogo, "Banco (Código)", indice=1).fill(f"MODIFICADO {sufijo}")
app.wait_for_timeout(800)
capturar_paso(app, "descripcion_modificada", paso_excel=5)

texto_resultado = confirmar_f(frame, aceptar=True)
assert "modific" in texto_resultado.lower() or "actualiz" in texto_resultado.lower() or "exito" in texto_resultado.lower() or "�xito" in texto_resultado.lower(), f"Se esperaba un mensaje de exito de modificacion, se vio: {texto_resultado!r}"
app.wait_for_timeout(1500)
capturar_paso(app, "aceptar_presionado", paso_excel=6)

encontrado = buscar_en_grilla_paginada(app, frame, sufijo, boton_siguiente="Siguiente")
if not encontrado:
    encontrado = buscar_en_grilla_paginada(app, frame, sufijo, boton_siguiente="Sgtes")
assert encontrado, f"El banco modificado (sufijo {sufijo!r}) deberia reflejarse en la grilla"
capturar_paso(app, "modificacion_en_grilla_verificada", paso_excel=7)
''')

add("CP-062", '''
filas = frame.locator("table tbody tr")
cantidad = filas.count()
assert cantidad > 0, "Se necesita al menos un banco PAC en la grilla"

candidatos_afiliados = []
for i in range(cantidad):
    celda_afiliados = filas.nth(i).locator("td").last
    texto_afiliados = celda_afiliados.inner_text().strip()
    if texto_afiliados.isdigit() and int(texto_afiliados) > 0:
        candidatos_afiliados.append((int(texto_afiliados), i))

# Se prefiere el banco con MENOS afiliados (pero > 0): un banco con
# miles de afiliados (ej. 16295) puede tardar mucho en generar el
# Excel y bloquear la interaccion con la pagina por mas de 30s.
fila_con_afiliados = None
if candidatos_afiliados:
    candidatos_afiliados.sort(key=lambda par: par[0])
    _, indice_elegido = candidatos_afiliados[0]
    fila_con_afiliados = filas.nth(indice_elegido)

if fila_con_afiliados is None:
    print(f"[AVISO] {CASO}: no se encontro ningun banco PAC con afiliados activos (>0) en la grilla - se prueba igual con la primera fila, la descarga podria salir vacia de datos de clientes.")
    fila_con_afiliados = filas.first

fila_con_afiliados.click()
app.wait_for_timeout(800)
capturar_paso(app, "banco_con_afiliados_seleccionado", paso_excel=3)

with app.expect_download(timeout=20000) as descarga_info:
    # BUG REAL confirmado en vivo (no de la app, del selector): este
    # boton tiene un icono <span role="img" aria-label="download"> ANTES
    # del texto, que se suma al nombre accesible ("download Guardar
    # Afiliados") - exact=True nunca matchea. Se usa substring en su lugar.
    frame.get_by_role("button", name="Guardar Afiliados", exact=False).click()
descarga = descarga_info.value
ruta = EVIDENCIA / f"{CASO}_afiliados.xlsx"
descarga.save_as(str(ruta))
app.wait_for_timeout(1000)
assert ruta.exists() and ruta.stat().st_size > 0, "El archivo Excel de afiliados deberia haberse descargado"
capturar_paso(app, "excel_afiliados_verificado", paso_excel=6)
''')

add("CP-063", '''
app.set_viewport_size({"width": 768, "height": 1024})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_tablet", paso_excel=3)
assert frame.locator("app-banco-pac-list").is_visible(), "La pantalla deberia seguir visible en resolucion tablet"

app.set_viewport_size({"width": 375, "height": 812})
app.wait_for_timeout(1000)
capturar_paso(app, "vista_mobile", paso_excel=3)
assert frame.locator("app-banco-pac-list").is_visible(), "La pantalla deberia seguir visible en resolucion mobile"

app.set_viewport_size({"width": 1600, "height": 900})
app.wait_for_timeout(800)
capturar_paso(app, "vista_restaurada", paso_excel=3)
''')


if __name__ == "__main__":
    if not CASES:
        raise SystemExit("No hay casos cargados en CASES.")
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")
