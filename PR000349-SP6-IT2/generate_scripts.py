"""
generate_scripts.py - PR000349-SP6 (Migracion Modulos Enccobra y
Medidores: administracion de Encargos de Cobranza + consulta de
Catastros de Conexiones Electricas).

CONFIRMADO EN VIVO 12/10/2026 (_exploracion/explore_0[1-3]*.py):

1. 8 RF, 77 casos (MCP_PR000349_SP6_v2.xlsx). 7 pantallas del dominio
   Enccobra (RF-01 a RF-07, BD Informix "clientes" - mismo schema que
   PR000325-SP6) + 1 pantalla de consulta tecnica de catastros (RF-08,
   dominio "Medidores"/SISTEC).

2. Usuario de pruebas: **DCABA_DW / Melquisedec_01** (cambiado de
   SCASTI_DW el 12/10/2026 - DCABA_DW ve 7 de las 8 pantallas, SCASTI_DW
   solo 6: a DCABA_DW SI le aparece "Consulta De Catastro De Conexiones
   Eléctricas" (RF-08, nombre real de menu, no coincide con lo que
   sugiere el EF/ET) en su menu, confirmado abriendo la app real
   -> app-catastro. Ambas cuentas comparten el mismo rol LUZENCAR para
   RF-02 a RF-07.

3. Navegacion: Aplicaciones > Comercial > <Nombre exacto>, DIRECTO (2
   niveles, sin categoria intermedia tipo "Reclamos Comerciales" de
   otros proyectos). Abre POPUP con iframe #aplicacion, mismo mecanismo
   de core.abrir_aplicacion() de siempre.

4. Componentes Angular raiz + nombre real de menu confirmados para 6 de
   8 pantallas:
   RF-02 Tipo de Cambio -> "Administración De Tipos De Cambio" -> app-tipocambio
   RF-03 Seguros -> "Mantenimiento De Seguros De Encargo" -> app-seguro
   RF-04 Promotores -> "Mantenimiento De Promotores" -> app-promotor
   RF-05 Niveles de Promotor -> "Niveles De Promotor" -> app-nivel
   RF-06 Parametros de Encargo -> "Parámetros De Encargo" -> app-parametroencargo
   RF-07 Comision -> "Comisión De Encargos De Cobranza" -> app-comision

5. **RF-01 (Plan de Encargos) RESUELTO 12/10/2026**: el nombre real de
   menu es **"Administración De Planes De Encargo"** (no "Plan de
   Encargo(s)" como sugeria el EF - por eso la busqueda inicial por
   substring no lo encontraba, era un problema de termino de busqueda,
   no de acceso faltante). Confirmado abriendo con DCABA_DW ->
   app-plan, pantalla con filtro Encargo + grilla "Planes registrados"
   + campos Codigo de plan/Plan o producto/Valor/Moneda, tal como
   describe el EF. **Las 8 pantallas del proyecto quedan confirmadas.**

6. Patron de botones confirmado en las 6 pantallas: "Ingresar" (modo
   captura; 2do uso = "Aceptar" para confirmar), "Modificar" (edicion;
   2do uso = "Cancelar"), "Eliminar"/"Desactivar" segun si es baja
   fisica o logica, "Cancelar"/"Cerrar" generico. Diseno clasico de
   ventana (no ant-design/ng-zorro como PR000349-SP1) - mas parecido a
   PR000325/PR000335.

7. Sin explorar todavia en este pase: estructura interna de cada
   pantalla (selectores de campo exactos, mensajes reales de validacion,
   comportamiento del modal de confirmacion) - Paso 2 completo pendiente
   por pantalla antes de escribir el cuerpo real de cada CP.
"""
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).parent
sys.path.insert(0, str(OUT_DIR.parent / "_framework"))
import web_lds_core as core

PROYECTO = "PR000349-SP6-IT2"
MATRIZ = json.loads((OUT_DIR / "matriz_casos.json").read_text(encoding="utf-8"))

ENV_TOGGLES = core.ENV_TOGGLES_CODE.replace("__PROYECTO__", PROYECTO)

HEADER_TEMPLATE = '''"""
{docstring_con_ficha_del_caso}
"""
import os, re, shutil, struct, subprocess, sys, time, zipfile
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape as _escape_xml
from playwright.sync_api import sync_playwright, expect, TimeoutError as PWTimeoutError

# La consola de Windows puede estar en cp1252 (no UTF-8) - un mensaje de
# error que incluya un emoji u otro caracter fuera de ese charset (ej. el
# texto real de una pantalla con iconos) tira UnicodeEncodeError al
# imprimirlo, lo que tapa el mensaje real del defecto con un crash
# secundario (confirmado en vivo 21/10/2026, CP068 de PR000349-SP6-IT2).
# reconfigure(errors="replace") evita el crash sin cambiar el encoding
# real de la terminal - los caracteres no representables se cambian por
# "?" en vez de abortar el print().
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass

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

%%NAV%%

%%HELPERS_ESPERA%%

%%VIDEO_HELPERS%%

# --- Navegacion propia de este proyecto: Aplicaciones > Comercial > <pantalla>, directo ---
# CONFIRMADO EN VIVO 12/10/2026: 2 niveles de menu (sin categoria
# intermedia), entrar SIEMPRE por el portal.

def abrir_tipo_cambio(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Administración De Tipos De Cambio"], "app-tipocambio", paso_excel=paso_excel)


def abrir_seguros(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Mantenimiento De Seguros De Encargo"], "app-seguro", paso_excel=paso_excel)


def abrir_promotores(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Mantenimiento De Promotores"], "app-promotor", paso_excel=paso_excel)


def abrir_niveles(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Niveles De Promotor"], "app-nivel", paso_excel=paso_excel)


def abrir_parametros_encargo(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Parámetros De Encargo"], "app-parametroencargo", paso_excel=paso_excel)


def abrir_comision(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Comisión De Encargos De Cobranza"], "app-comision", paso_excel=paso_excel)


def abrir_catastro(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Consulta De Catastro De Conexiones Eléctricas"], "app-catastro", paso_excel=paso_excel)


def abrir_plan(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Administración De Planes De Encargo"], "app-plan", paso_excel=paso_excel)


# Las 8 pantallas confirmadas con DCABA_DW (ver docstring del modulo).

def filas_tabla(frame):
    """nz-table de ant-design siempre trae una fila oculta extra
    tr.ant-table-measure-now de uso interno - filtrarla siempre (ver
    NUEVO_PROYECTO_CHECKLIST.md, gotchas PR000349-SP1). Cuando la
    grilla esta vacia, ant-design agrega ademas una fila placeholder
    real (tr.ant-table-placeholder, texto "No hay datos") que NO es un
    registro - filtrarla tambien para que count() refleje filas de
    datos reales."""
    return frame.locator("tbody tr:not(.ant-table-measure-now):not(.ant-table-placeholder)")


def fila_por_codigo(frame, codigo):
    """Busca la fila cuya PRIMERA celda sea exactamente `codigo`
    (recorriendo en Python, no con has_text=regex: confirmado en vivo
    que el \\b de Playwright no matchea contra el texto real de las
    filas de esta tabla - usar siempre esto en vez de
    filas_tabla(frame).filter(has_text=regex) para codigos cortos)."""
    filas = filas_tabla(frame)
    for i in range(filas.count()):
        primera_celda = filas.nth(i).locator("td").first.inner_text().strip()
        if primera_celda == codigo:
            return filas.nth(i)
    raise AssertionError(f"No se encontro ninguna fila con Codigo de Plan = {{codigo!r}}")


def buscar_fila_en_paginas(app, frame, columna_idx, valor, max_paginas=25):
    """Recorre las paginas de la grilla (boton 'Siguiente' de
    ant-design) buscando una fila cuya columna `columna_idx` (separada
    por tabs en inner_text()) sea exactamente `valor`. Necesario en
    grillas con muchas paginas (ej. Promotores, ~190 filas/19 paginas)
    donde una fila recien creada puede no caer en la pagina 1 segun el
    orden del listado. Devuelve el texto completo de la fila, o ""
    si no se encontro en `max_paginas` paginas.

    SIEMPRE reinicia a la pagina 1 antes de buscar (clickeando
    'Anterior' repetidas veces) - confirmado en vivo que buscar solo
    hacia adelante desde la pagina actual falla cuando una fila
    cambia de pagina entre una llamada y la siguiente (ej. un
    Promotor que se reordena tras Desactivar)."""
    anterior = frame.locator("li.ant-pagination-prev button, .ant-pagination-prev")
    for _ in range(max_paginas):
        if anterior.count() and not anterior.first.is_disabled():
            anterior.first.click()
            app.wait_for_timeout(500)
        else:
            break
    for _ in range(max_paginas):
        filas = filas_tabla(frame)
        for i in range(filas.count()):
            texto = filas.nth(i).inner_text()
            columnas = texto.split("\\t")
            if len(columnas) > columna_idx and columnas[columna_idx] == valor:
                return texto
        siguiente = frame.locator("li.ant-pagination-next button, .ant-pagination-next")
        if siguiente.count() and not siguiente.first.is_disabled():
            siguiente.first.click()
            app.wait_for_timeout(800)
        else:
            break
    return ""


def elegir_opcion_combo(app, frame, indice_combo, texto_opcion, max_scrolls=15):
    """Abre el combo .ant-select-selector en la posicion `indice_combo`
    y selecciona la opcion cuyo texto completo sea `texto_opcion`,
    forzando scroll dentro del cdk-virtual-scroll-viewport si hace
    falta (confirmado en vivo: varios combos de este proyecto no
    renderizan todas sus opciones de entrada - RF-01/RF-06). Devuelve
    True si la encontro y clickeo, False si no, SIN lanzar excepcion
    (el caller decide si eso es un error)."""
    combos = frame.locator(".ant-select-selector")
    combos.nth(indice_combo).click()
    app.wait_for_timeout(600)
    contenedor = frame.locator("cdk-virtual-scroll-viewport").first
    for _ in range(max_scrolls):
        opciones = frame.locator("nz-option-item, [role='option']")
        for i in range(opciones.count()):
            if opciones.nth(i).inner_text().strip() == texto_opcion:
                opciones.nth(i).click()
                return True
        if contenedor.count():
            contenedor.evaluate("el => el.scrollTo(0, el.scrollHeight)")
            app.wait_for_timeout(400)
        else:
            break
    return False


def confirmar_dialogo_si_aparece(app, frame, timeout_ms=4000):
    """Cierra un dialogo .ant-modal/nz-modal-container si aparece
    (tolerante: si no aparece nada en el timeout, sigue sin fallar).
    Devuelve el texto del dialogo si aparecio, o None."""
    dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
    try:
        dialogo.first.wait_for(state="visible", timeout=timeout_ms)
    except PWTimeoutError:
        return None
    texto = dialogo.first.inner_text()
    boton = dialogo.first.get_by_role("button", name=re.compile(r"^\\s*(Aceptar|S[ií]|Cerrar)\\s*$", re.I))
    if boton.count():
        boton.first.click()
    app.wait_for_timeout(1000)
    return texto


def capturar_mensaje_dialogo(app, frame, descripcion, paso_excel=None, timeout_ms=5000):
    """Espera el dialogo de validacion/error y lo CAPTURA en evidencia
    MIENTRAS SIGUE ABIERTO -a diferencia de llamar a
    confirmar_dialogo_si_aparece() y recien despues capturar_paso(),
    que cierra el modal en la MISMA llamada que lee su texto y deja la
    evidencia mostrando la pantalla ya sin el mensaje (confirmado en
    vivo: CP004 de RF-01, Word de evidencia sin el dialogo visible
    pese a que el assert sobre el mensaje pasaba bien)-. Devuelve el
    texto del dialogo, o el texto de toda la pantalla si no aparecio
    ningun dialogo dentro de `timeout_ms`."""
    dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
    try:
        dialogo.first.wait_for(state="visible", timeout=timeout_ms)
    except PWTimeoutError:
        texto = frame.locator("body").inner_text()
        capturar_paso(app, descripcion, paso_excel=paso_excel)
        return texto
    texto = dialogo.first.inner_text()
    capturar_paso(app, descripcion, paso_excel=paso_excel)
    boton = dialogo.first.get_by_role("button", name=re.compile(r"^\\s*(Aceptar|S[ií]|Cerrar)\\s*$", re.I))
    if boton.count():
        boton.first.click()
    app.wait_for_timeout(500)
    return texto

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
            {abrir_call}

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
            if GRABAR_VIDEO:
                # browser.close() retorna antes de que el flush a disco de
                # un video de una pagina extra (page@*.webm huerfano) este
                # garantizado completo - confirmado en vivo (CP008/016/017/
                # 018/021): sin esta espera, el glob de abajo a veces corre
                # justo antes de que el archivo termine de escribirse y
                # queda sin fusionar en el video final.
                time.sleep(1.5)
            if _CASO_OK:
                ruta_portal = _renombrar_video(video_portal, EVIDENCIA / f"{{CASO}}-1.webm") if video_portal is not None else None
                ruta_app = _renombrar_video(video_app, EVIDENCIA / f"{{CASO}}-2.webm") if video_app is not None else None
                rutas_videos = [r for r in (ruta_portal, ruta_app) if r is not None]
                rutas_videos.extend(p for p in sorted(EVIDENCIA.glob("page@*.webm")) if p not in rutas_videos)
                if len(rutas_videos) > 1:
                    _unir_videos(EVIDENCIA / f"{{CASO}}_video.webm", *rutas_videos)
                elif len(rutas_videos) == 1:
                    try:
                        rutas_videos[0].replace(EVIDENCIA / f"{{CASO}}_video.webm")
                    except (PermissionError, OSError) as e:
                        print(f"  (aviso) no se pudo renombrar el video final: {{e}}")
                if GRABAR_WORD:
                    generar_word_evidencia()
                # Barrido final: cualquier page@*.webm que haya quedado
                # suelto (no se incluyo en rutas_videos, ej. por llegar
                # despues del glob pese a la espera de arriba) se
                # confirmo en vivo que es un artefacto EN BLANCO (una
                # pagina interna de Chromium sin contenido util, no
                # footage perdido) - se descarta para no dejar basura
                # visual en la carpeta de evidencia.
                for extra in EVIDENCIA.glob("page@*.webm"):
                    for _intento_descarte in range(4):
                        try:
                            extra.unlink(missing_ok=True)
                            break
                        except (PermissionError, OSError):
                            time.sleep(0.5)
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
                for extra in EVIDENCIA.glob("page@*.webm"):
                    for _intento_descarte in range(4):
                        try:
                            extra.unlink(missing_ok=True)
                            break
                        except (PermissionError, OSError):
                            time.sleep(0.5)


if __name__ == "__main__":
    main()
'''


def render(caso: dict) -> str:
    body = "\n".join("            " + linea if linea.strip() else "" for linea in caso["body"].strip("\n").splitlines())
    docstring = f"""CP: {caso['cp']}
RF: {caso['rf']}  |  CU: {caso['cu']}
Nombre: {caso['name']}
Descripcion: {caso['desc']}
Resultado esperado: {caso['esperado']}"""
    return HEADER_TEMPLATE.format(
        docstring_con_ficha_del_caso=docstring,
        cp=caso["cp"], name_repr=repr(caso["name"]), rf_repr=repr(caso["rf"]),
        cu_repr=repr(caso["cu"]), desc_repr=repr(caso["desc"]),
        esperado_repr=repr(caso["esperado"]), pasos_repr=repr(caso.get("pasos", "")),
        body=body, abrir_call=caso["abrir_call"],
    ).replace("%%CAPTURAR_PASO%%", core.CAPTURAR_PASO_CODE) \
     .replace("%%LOGIN%%", core.LOGIN_BLOCK) \
     .replace("%%NAV%%", core.CLICK_VISIBLE_BLOCK + "\n\n\n" + core.ABRIR_APLICACION_BLOCK) \
     .replace("%%HELPERS_ESPERA%%", core.ESPERAR_FIN_CARGA_BLOCK + "\n\n\n" + core.ESPERAR_ANIMACION_BLOCK + "\n\n\n" + core.SELECCIONAR_PRIMERA_OPCION_BLOCK + "\n\n\n" + core.SELECCIONAR_OPCION_POR_TEXTO_BLOCK) \
     .replace("%%VIDEO_HELPERS%%", core.RENOMBRAR_VIDEO_BLOCK) \
     .replace("%%CURSOR_OVERLAY_JS%%", repr(core.CURSOR_JS_FULL.strip("\n"))) \
     .replace("%%WORD_HELPERS%%", core.WORD_HELPERS_FULL.strip("\n"))


CASES = []


def add(cp, abrir_call, body):
    m = MATRIZ[cp]
    CASES.append(dict(
        cp=cp, rf=m["rf"], cu=m["cu"], name=m["name"], desc=m["desc"],
        esperado=m["esperado"], pasos=m.get("pasos", ""),
        abrir_call=abrir_call, body=body,
    ))


# ===========================================================================
# RF-05: Niveles de promotor (pantalla mas simple, arranca primero)
# ===========================================================================
# CONFIRMADO EN VIVO 12/10/2026 (_exploracion/explore_04_niveles_flujo.py):
# - Framework ng-zorro/ant-design (nz-button, nz-table, nz-modal-container,
#   cdk-overlay-container) - mismos gotchas ya documentados para
#   PR000349-SP1 en NUEVO_PROYECTO_CHECKLIST.md (filtrar fila
#   ant-table-measure-now, toasts que se autodesvanecen, confirmar con
#   helper tolerante).
# - Campos de "Ingreso" SIN aria-label: Nivel = input[type=text] nth(0),
#   Descripcion = input[type=text] nth(1), Promotor Especial =
#   input[type=checkbox] (unico en la pantalla). Los 3 arrancan
#   disabled=True (modo consulta) y se habilitan recien tras clickear
#   "Ingresar".
# - Boton "Ingresar"/"Aceptar" y "Modificar"/"Cancelar" tienen icono
#   (texto accesible no es el texto exacto) - usar
#   re.compile(r"Ingresar"/"Aceptar", re.I) en vez de name exacto.
# - Validacion de campo obligatorio CONFIRMADA: modal "Ventana de
#   Validación" con mensaje "El Código es obligatorio." + boton Aceptar
#   propio (distinto del Aceptar del formulario).
# - Grilla real (4 filas, ya ordenada ascendente por Codigo): 1-Sucursal-N,
#   2-Fonoluz-N, 3-Campo-N, 4-LDS-S.
# - PENDIENTE (no confirmado todavia, necesita otra ronda en vivo): el
#   mensaje real de registro exitoso y de codigo duplicado - el primer
#   intento de registrar en vivo (codigo "9") dejo un modal/overlay sin
#   cerrar que bloqueo el siguiente clic ("nz-modal-container... subtree
#   intercepts pointer events"), no se pudo leer el mensaje real todavia.
#   NO escribir CP040-046 (registrar/modificar/eliminar) hasta confirmar
#   esos mensajes en vivo - solo CP039 (consulta, de solo lectura) esta
#   confirmado de punta a punta.

# ===========================================================================
# RF-01: Plan de encargos
# ===========================================================================
# CONFIRMADO via Manual_RF01_Plan_Encargos.docx (manual de usuario real,
# ya contrastado contra el codigo SPA - documenta discrepancias EF/ET vs
# codigo real) + exploracion en vivo
# (_exploracion/explore_08_plan_selectores.py):
# - Encargo real con Plan ya registrado: "0001 — FONAVI" (facturable,
#   SIN rango de edad - al seleccionarlo aparece el campo "Cargo de
#   facturación" pero NO "Rango de edad"). Tiene 1 Plan real: codigo
#   "A", descripcion "PLAN UNICO", cuota 0.00.
# - 16 Encargos reales en el combo (0001 a 0016).
# - Inputs en orden POSICIONAL confirmado para el Encargo 0001
#   (facturable, sin rango): [0]=trigger del combo Encargo,
#   [1]=Codigo de plan, [2]=Plan o producto, [3]=Valor,
#   [4]=Cargo de facturacion. OJO: este orden cambia si el Encargo
#   maneja rango de edad (aparece un campo extra) - no asumir para
#   otros Encargos sin volver a confirmar.
# - Boton "Ingresar" se deshabilita y aparece "Aceptar" en modo
#   captura (igual patron que RF-05). Modificar/Eliminar quedan
#   deshabilitados hasta clickear una fila de la grilla.
# - Mensajes EXACTOS confirmados por el manual (no inventados):
#   "El Código de Plan es obligatorio y debe tener 2 caracteres."
#   "El Valor es obligatorio y debe ser mayor o igual a 0."
#   "El Encargo es facturable: debe indicar el Cargo de Facturación."
#   "Plan guardado." / "Plan eliminado."
#   Duplicado: el manual NO da un texto fijo - aclara que es "Rechazo
#   del servicio" (mensaje de error generico del backend) - no
#   hardcodear un texto exacto para CP005, solo verificar que rechaza
#   y no duplica.
# - NO existe boton "Cerrar" (discrepancia real EF vs codigo,
#   documentada en el manual seccion 9).

add("CP001", "app, frame = abrir_plan(page, paso_excel=2)", '''
campo_encargo = frame.locator(".ant-select-selector").first
campo_encargo.click()
app.wait_for_timeout(500)
frame.get_by_text("0001 — FONAVI", exact=True).click()
app.wait_for_load_state("networkidle")
app.wait_for_timeout(1500)
capturar_paso(app, "encargo_con_planes", paso_excel=2)
filas = filas_tabla(frame)
n = filas.count()
assert n >= 1, f"Se esperaba al menos 1 Plan registrado para 0001-FONAVI, se vieron {n}"
texto_fila = fila_por_codigo(frame, "A").inner_text()
assert "PLAN UNICO" in texto_fila, f"No se encontro el Plan real esperado: {texto_fila!r}"
''')

add("CP002", "app, frame = abrir_plan(page, paso_excel=2)", '''
# El combo de Encargo tiene en realidad 21 opciones reales (0001-0021),
# no 16 - el nz-select usa cdk-virtual-scroll-viewport y solo renderiza
# una ventana visible a la vez; hay que forzar scroll dentro de ese
# contenedor para que Angular renderice las opciones siguientes
# (confirmado en vivo: un primer intento con scrollTop directo no
# disparaba el re-render de CDK, scrollTo(0, scrollHeight) si).
# "0021 — PAGOS INLAND LIBRO 401" es el ultimo y SI esta confirmado sin
# Planes ("No hay datos").
campo_encargo = frame.locator(".ant-select-selector").first
campo_encargo.click()
app.wait_for_timeout(1000)
contenedor = frame.locator("cdk-virtual-scroll-viewport").first
for _ in range(8):
    contenedor.evaluate("el => el.scrollTo(0, el.scrollHeight)")
    app.wait_for_timeout(500)
frame.get_by_text("0021 — PAGOS INLAND LIBRO 401", exact=True).click()
app.wait_for_load_state("networkidle")
app.wait_for_timeout(1500)
capturar_paso(app, "encargo_sin_planes", paso_excel=2)
filas_actuales = filas_tabla(frame)
assert filas_actuales.count() == 0, f"Se esperaba el Encargo 0021 sin Planes, se vieron {filas_actuales.count()} fila(s)"
texto_pantalla = frame.locator("body").inner_text()
assert "No hay datos" in texto_pantalla, f"Se esperaba el mensaje de grilla vacia 'No hay datos': {texto_pantalla[:300]!r}"
assert "Error" not in texto_pantalla, f"No deberia aparecer ningun error con la grilla vacia: {texto_pantalla[:300]!r}"

frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
capturar_paso(app, "ingresar_habilitado", paso_excel=4)
inputs = frame.locator("input")
assert not inputs.nth(1).is_disabled(), "El campo Codigo de plan deberia habilitarse tras Ingresar aunque el Encargo no tenga Planes previos"
frame.get_by_role("button", name=re.compile(r"Cancelar", re.I)).click()
app.wait_for_timeout(500)
''')

add("CP003", "app, frame = abrir_plan(page, paso_excel=2)", '''
campo_encargo = frame.locator(".ant-select-selector").first
campo_encargo.click()
app.wait_for_timeout(500)
frame.get_by_text("0001 — FONAVI", exact=True).click()
app.wait_for_load_state("networkidle")
app.wait_for_timeout(1500)

# Idempotencia: si el Plan "01" ya existe (de una corrida anterior de
# este mismo caso), el Aceptar de mas abajo es rechazado como duplicado
# y la pantalla queda en modo alta sin volver a consulta sola (mismo
# patron de fixture no idempotente ya visto en otros RF) - se elimina
# primero para poder probar limpio el registro desde cero.
filas_previas = filas_tabla(frame)
ya_existe_01 = any(filas_previas.nth(i).locator("td").first.inner_text().strip() == "01" for i in range(filas_previas.count()))
if ya_existe_01:
    fila_por_codigo(frame, "01").click()
    app.wait_for_timeout(500)
    frame.get_by_role("button", name=re.compile(r"Eliminar", re.I)).click()
    app.wait_for_timeout(1000)
    dialogo_borrado = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
    dialogo_borrado.first.wait_for(state="visible", timeout=5000)
    for _intento_borrado in range(3):
        boton_aceptar_borrado = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S)).first.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$", re.I))
        if boton_aceptar_borrado.count():
            boton_aceptar_borrado.first.click()
        app.wait_for_timeout(2000)
        filas_tras_borrado = filas_tabla(frame)
        if not any(filas_tras_borrado.nth(i).locator("td").first.inner_text().strip() == "01" for i in range(filas_tras_borrado.count())):
            break
    # Tras confirmar la eliminacion puede quedar un modal de EXITO
    # aparte ("Plan eliminado.") que CP008 nunca topa (ahi el caso
    # termina en la grilla sin volver a hacer clic en nada) - aca si se
    # sigue de inmediato al Ingresar, y ese modal residual intercepta el
    # clic ("subtree intercepts pointer events") si no se cierra antes.
    confirmar_dialogo_si_aparece(app, frame, timeout_ms=4000)
    app.wait_for_timeout(500)

frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
inputs = frame.locator("input")
inputs.nth(1).fill("01")
inputs.nth(2).fill("Plan de prueba QA")
inputs.nth(3).fill("5.50")
inputs.nth(4).fill("Facturación directa QA")
capturar_paso(app, "datos_completos", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2500)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(500)
filas = filas_tabla(frame)
texto_grilla = filas.first.inner_text() if filas.count() else ""
encontrado = any("01" in filas.nth(i).inner_text() for i in range(filas.count()))
assert encontrado, f"El Plan 01 deberia aparecer en la grilla tras registrar (mensaje visto: {mensaje!r})"
# El formulario de alta no se limpia solo tras Aceptar (queda con los
# mismos datos recien cargados) - Cancelar para volver a modo consulta,
# pero eso TAMBIEN limpia el filtro de Encargo (queda "Seleccione un
# Encargo..." y la grilla en "No hay datos") - hay que volver a elegir
# 0001-FONAVI para que la evidencia final muestre la grilla real con
# el Plan 01 ya agregado, en vez de la pantalla todavia en modo alta
# o una grilla vacia por falta de filtro.
boton_cancelar = frame.locator("button").filter(has_text=re.compile(r"^\\s*Cancelar\\s*$", re.I))
if boton_cancelar.count():
    boton_cancelar.first.click()
    app.wait_for_timeout(800)
campo_encargo_final = frame.locator(".ant-select-selector").first
campo_encargo_final.click()
app.wait_for_timeout(500)
frame.get_by_text("0001 — FONAVI", exact=True).click()
app.wait_for_load_state("networkidle")
app.wait_for_timeout(1500)
capturar_paso(app, "plan_agregado_en_grilla", paso_excel=5)
''')

add("CP004", "app, frame = abrir_plan(page, paso_excel=2)", '''
campo_encargo = frame.locator(".ant-select-selector").first
campo_encargo.click()
app.wait_for_timeout(500)
frame.get_by_text("0001 — FONAVI", exact=True).click()
app.wait_for_load_state("networkidle")
app.wait_for_timeout(1500)
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
inputs = frame.locator("input")
inputs.nth(3).fill("1.00")
capturar_paso(app, "codigo_vacio", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_codigo_obligatorio", paso_excel=4, timeout_ms=4000)
assert "código" in mensaje.lower() and ("obligatorio" in mensaje.lower() or "2 caracteres" in mensaje.lower()), f"Se esperaba el mensaje de Codigo de Plan obligatorio: {mensaje!r}"
''')

add("CP005", "app, frame = abrir_plan(page, paso_excel=2)", '''
# El Codigo de Plan "A" (preexistente, legado) tiene solo 1 caracter -
# usarlo aca dispara la validacion de LARGO ("debe tener 2 caracteres")
# antes de que el backend llegue a chequear duplicado, con lo cual este
# caso terminaba probando sin querer la validacion de largo en vez de
# la de duplicado (bug real detectado al corregir la evidencia: una vez
# visible el dialogo, el mensaje capturado no era el de duplicado).
# Se usa el Plan "01" (2 caracteres, registrado por CP003 y dejado
# como fixture permanente del proyecto) para probar el duplicado real.
campo_encargo = frame.locator(".ant-select-selector").first
campo_encargo.click()
app.wait_for_timeout(500)
frame.get_by_text("0001 — FONAVI", exact=True).click()
app.wait_for_load_state("networkidle")
app.wait_for_timeout(1500)
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
inputs = frame.locator("input")
inputs.nth(1).fill("01")
inputs.nth(2).fill("Plan duplicado QA")
inputs.nth(3).fill("2.00")
inputs.nth(4).fill("Facturación directa QA")
capturar_paso(app, "codigo_duplicado_antes_de_aceptar", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2500)
mensaje = capturar_mensaje_dialogo(app, frame, "resultado_duplicado", paso_excel=4, timeout_ms=5000)
assert "ya existe" in mensaje.lower() or "duplicad" in mensaje.lower(), f"Se esperaba el mensaje de Codigo de Plan duplicado: {mensaje!r}"
filas_despues = filas_tabla(frame)
filas_con_01 = [i for i in range(filas_despues.count()) if filas_despues.nth(i).locator("td").first.inner_text().strip() == "01"]
assert len(filas_con_01) <= 1, f"El Plan 01 no deberia duplicarse en la grilla tras el rechazo (mensaje visto: {mensaje!r})"
''')

add("CP006", "app, frame = abrir_plan(page, paso_excel=2)", '''
campo_encargo = frame.locator(".ant-select-selector").first
campo_encargo.click()
app.wait_for_timeout(500)
frame.get_by_text("0001 — FONAVI", exact=True).click()
app.wait_for_load_state("networkidle")
app.wait_for_timeout(1500)
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
inputs = frame.locator("input")
inputs.nth(1).fill("02")
inputs.nth(2).fill("Plan sin cargo QA")
inputs.nth(3).fill("3.00")
capturar_paso(app, "sin_cargo_facturacion", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_cargo_obligatorio", paso_excel=5, timeout_ms=4000)
assert "facturaci" in mensaje.lower() and "cargo" in mensaje.lower(), f"Se esperaba el mensaje de Cargo de Facturacion obligatorio: {mensaje!r}"
''')

add("CP007", "app, frame = abrir_plan(page, paso_excel=2)", '''
campo_encargo = frame.locator(".ant-select-selector").first
campo_encargo.click()
app.wait_for_timeout(500)
frame.get_by_text("0001 — FONAVI", exact=True).click()
app.wait_for_load_state("networkidle")
app.wait_for_timeout(1500)
fila_a = fila_por_codigo(frame, "A")
fila_a.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Modificar", re.I)).click()
app.wait_for_timeout(800)
inputs = frame.locator("input")
campo_valor = inputs.nth(3)
campo_valor.fill("7.77")
app.wait_for_timeout(500)
capturar_paso(app, "valor_modificado", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2500)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
capturar_paso(app, "cambio_reflejado", paso_excel=5)
fila_actualizada = fila_por_codigo(frame, "A")
assert "7.77" in fila_actualizada.inner_text(), f"La Cuota deberia reflejar 7.77 tras modificar (mensaje visto: {mensaje!r})"
''')

add("CP008", "app, frame = abrir_plan(page, paso_excel=2)", '''
# Se registra un Plan descartable propio (no se reutiliza "A", que
# usan otros casos) para no dejar el fixture de otros CP sin su dato.
campo_encargo = frame.locator(".ant-select-selector").first
campo_encargo.click()
app.wait_for_timeout(500)
frame.get_by_text("0001 — FONAVI", exact=True).click()
app.wait_for_load_state("networkidle")
app.wait_for_timeout(1500)
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
inputs = frame.locator("input")
inputs.nth(1).fill("ZZ")
inputs.nth(2).fill("Plan a eliminar QA")
inputs.nth(3).fill("9.99")
inputs.nth(4).fill("Facturación directa QA")
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2500)
confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(2000)

fila_zz = fila_por_codigo(frame, "ZZ")
fila_zz.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Eliminar", re.I)).click()
app.wait_for_timeout(1000)
capturar_paso(app, "confirmacion_eliminar", paso_excel=2)
dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
dialogo.first.wait_for(state="visible", timeout=5000)
mensaje_confirmacion = dialogo.first.inner_text()
# El clic en Aceptar es intermitente en esta pantalla (confirmado en vivo:
# a veces el modal tarda en terminar su animacion de entrada y el primer
# clic no se registra) - reintentar hasta 3 veces verificando la grilla.
sigue_zz = True
for _intento in range(3):
    boton_aceptar = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S)).first.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$", re.I))
    if boton_aceptar.count():
        boton_aceptar.first.click()
    app.wait_for_timeout(2000)
    filas_final = filas_tabla(frame)
    sigue_zz = any(filas_final.nth(i).locator("td").first.inner_text().strip() == "ZZ" for i in range(filas_final.count()))
    if not sigue_zz:
        break
capturar_paso(app, "plan_eliminado", paso_excel=4)
assert not sigue_zz, f"El Plan ZZ deberia haber desaparecido de la grilla (mensaje de confirmacion visto: {mensaje_confirmacion!r})"
''')

add("CP009", "app, frame = abrir_plan(page, paso_excel=2)", '''
campo_encargo = frame.locator(".ant-select-selector").first
campo_encargo.click()
app.wait_for_timeout(500)
frame.get_by_text("0001 — FONAVI", exact=True).click()
app.wait_for_load_state("networkidle")
app.wait_for_timeout(1500)
fila_a = fila_por_codigo(frame, "A")
fila_a.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Eliminar", re.I)).click()
app.wait_for_timeout(1000)
capturar_paso(app, "confirmacion_abierta", paso_excel=2)
dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
dialogo.first.wait_for(state="visible", timeout=5000)
boton_no = dialogo.first.get_by_role("button", name=re.compile(r"^\\s*(No|Cancelar)\\s*$", re.I))
boton_no.first.click()
app.wait_for_timeout(1500)
capturar_paso(app, "plan_sigue_en_grilla", paso_excel=4)
fila_por_codigo(frame, "A")  # no lanza AssertionError => el Plan A sigue existiendo
''')

add("CP010", "app, frame = abrir_plan(page, paso_excel=2)", '''
for ancho, alto, nombre in [(1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(1000)
    capturar_paso(app, f"responsive_{nombre}", paso_excel=2)
    desbordamiento = app.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 5")
    assert not desbordamiento, f"La pantalla se desborda horizontalmente en resolucion {nombre} ({ancho}x{alto})"
app.set_viewport_size({"width": 1600, "height": 900})
''')


# ===========================================================================
# RF-02: Tipo de Cambio
# ===========================================================================
# CONFIRMADO via Manual_RF02_TipoCambio.docx + exploracion en vivo
# (_exploracion/explore_2[3-7]*.py):
# - Pantalla SIN filtro: carga TODO el listado al abrir (32 paginas de
#   10, orden Año/Mes descendente - confirmado visualmente, el mas
#   reciente real es Agosto 2026).
# - Boton "Ingresar" SIEMPRE habilitado (no requiere fila seleccionada,
#   a diferencia de RF-01). "Modificar"/"Eliminar" SI requieren fila
#   seleccionada.
# - Tras Ingresar, 3 inputs en orden fijo: [0]=Mes (combo, "Enero" ..
#   "Diciembre", ojo "Setiembre" sin la primera "p" como en el DNI
#   peruano, no "Septiembre"), [1]=Año (texto, se autopropone el año
#   actual "2026" al entrar), [2]=Valor (numerico).
# - Mensajes EXACTOS confirmados en vivo (no solo el manual):
#   "El Valor es obligatorio y debe ser mayor a cero."
#   "El Año debe estar entre 2021 y 2031." (año actual 2026 +/-5, RN-16)
#   "Ya existe un Tipo de Cambio registrado para ese Año y Mes." (RN-18)
#   "Tipo de Cambio guardado." / "Tipo de Cambio eliminado."
#   "¿Confirma eliminar el Tipo de Cambio de <Mes> <Año>?"
# - A diferencia de RF-01 (CP007), el Modificar de ESTA pantalla SI
#   funciona bien: Mes/Año quedan disabled=True (bloqueados, RN-19)
#   pero el Valor se actualiza y guarda correctamente - confirmado en
#   vivo (Setiembre 2026 modificado de 3.80 a 3.90 con "Tipo de Cambio
#   guardado."). No es el mismo bug de FormControl disabled de RF-01.
# - El dialogo de confirmacion "Eliminar" puede ser intermitente igual
#   que en RF-01 (primer clic en Aceptar no siempre se registra) - usar
#   reintento, igual que en CP008 de RF-01.
# - Al elegir una opcion del combo Mes mientras la grilla ya tiene una
#   fila visible con el mismo nombre de mes (ej. "Agosto" ya en la
#   grilla), `get_by_text("Agosto", exact=True)` da strict-mode
#   violation (matchea la celda de la grilla Y la opcion del dropdown)
#   - escopar siempre al dropdown: `frame.locator(".ant-select-dropdown").get_by_text(...)`.

add("CP011", "app, frame = abrir_tipo_cambio(page, paso_excel=2)", '''
filas = filas_tabla(frame)
assert filas.count() >= 2, f"Se esperaban al menos 2 filas visibles, se vieron {filas.count()}"
primera = filas.nth(0).inner_text().split("\\t")
segunda = filas.nth(1).inner_text().split("\\t")
capturar_paso(app, "listado_inicial", paso_excel=2)
meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Setiembre","Octubre","Noviembre","Diciembre"]
clave_primera = (int(primera[1]), meses.index(primera[0]) + 1)
clave_segunda = (int(segunda[1]), meses.index(segunda[0]) + 1)
assert clave_primera >= clave_segunda, f"El listado deberia estar ordenado Año/Mes descendente: {primera!r} antes de {segunda!r}"
''')

add("CP012", "app, frame = abrir_tipo_cambio(page, paso_excel=2)", '''
# Idempotencia: si "Octubre 2026" ya existe (de una corrida anterior),
# el Aceptar de mas abajo es rechazado como duplicado SIN que el script
# se entere - confirmado en vivo: la pantalla queda en modo alta
# (Aceptar/Cancelar, no Ingresar/Modificar/Eliminar) pero el assert de
# "aparece en la grilla" pasaba igual porque el dato ya estaba ahi de
# ANTES, dando un OK falso (no se registro nada en esta corrida). Se
# elimina primero para que el registro de mas abajo sea siempre real.
filas_previas = filas_tabla(frame)
ya_existe = any("Octubre" in filas_previas.nth(i).inner_text() and "2026" in filas_previas.nth(i).inner_text() for i in range(filas_previas.count()))
if ya_existe:
    for i in range(filas_previas.count()):
        if "Octubre" in filas_previas.nth(i).inner_text() and "2026" in filas_previas.nth(i).inner_text():
            filas_previas.nth(i).click()
            break
    app.wait_for_timeout(500)
    frame.get_by_role("button", name=re.compile(r"Eliminar", re.I)).click()
    app.wait_for_timeout(1000)
    dialogo_borrado = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
    dialogo_borrado.first.wait_for(state="visible", timeout=5000)
    for _intento_borrado in range(3):
        boton_aceptar_borrado = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S)).first.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$", re.I))
        if boton_aceptar_borrado.count():
            boton_aceptar_borrado.first.click()
        app.wait_for_timeout(2000)
        filas_tras_borrado = filas_tabla(frame)
        if not any("Octubre" in filas_tras_borrado.nth(i).inner_text() and "2026" in filas_tras_borrado.nth(i).inner_text() for i in range(filas_tras_borrado.count())):
            break
    confirmar_dialogo_si_aparece(app, frame, timeout_ms=4000)
    app.wait_for_timeout(500)

frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
combo_mes = frame.locator(".ant-select-selector").first
combo_mes.click()
app.wait_for_timeout(400)
frame.locator(".ant-select-dropdown").get_by_text("Octubre", exact=True).click()
app.wait_for_timeout(400)
inputs = frame.locator("input")
inputs.nth(2).fill("3.80")
capturar_paso(app, "datos_completos", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "resultado_registro", paso_excel=6)
filas = filas_tabla(frame)
encontrado = any("Octubre" in filas.nth(i).inner_text() and "2026" in filas.nth(i).inner_text() for i in range(filas.count()))
assert encontrado, f"El Tipo de Cambio Octubre 2026 deberia aparecer en el listado (mensaje visto: {mensaje!r})"
''')

add("CP013", "app, frame = abrir_tipo_cambio(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
combo_mes = frame.locator(".ant-select-selector").first
combo_mes.click()
app.wait_for_timeout(400)
frame.locator(".ant-select-dropdown").get_by_text("Agosto", exact=True).click()
app.wait_for_timeout(400)
inputs = frame.locator("input")
inputs.nth(2).fill("3.80")
capturar_paso(app, "mes_año_duplicado", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_duplicado", paso_excel=4, timeout_ms=5000)
assert "ya existe" in mensaje.lower(), f"Se esperaba el mensaje de duplicado: {mensaje!r}"
''')

add("CP014", "app, frame = abrir_tipo_cambio(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
combo_mes = frame.locator(".ant-select-selector").first
combo_mes.click()
app.wait_for_timeout(400)
frame.locator(".ant-select-dropdown").get_by_text("Marzo", exact=True).click()
app.wait_for_timeout(400)
inputs = frame.locator("input")
inputs.nth(1).fill("2040")
inputs.nth(2).fill("3.80")
capturar_paso(app, "año_fuera_de_rango", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_rango", paso_excel=4, timeout_ms=5000)
assert "año debe estar entre" in mensaje.lower(), f"Se esperaba el mensaje de rango de año: {mensaje!r}"
''')

add("CP015", "app, frame = abrir_tipo_cambio(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
combo_mes = frame.locator(".ant-select-selector").first
combo_mes.click()
app.wait_for_timeout(400)
frame.locator(".ant-select-dropdown").get_by_text("Noviembre", exact=True).click()
app.wait_for_timeout(400)
inputs = frame.locator("input")
inputs.nth(2).fill("0")
capturar_paso(app, "valor_cero", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_valor", paso_excel=4, timeout_ms=5000)
assert "mayor a cero" in mensaje.lower(), f"Se esperaba el mensaje de Valor obligatorio/mayor a cero: {mensaje!r}"
''')

add("CP016", "app, frame = abrir_tipo_cambio(page, paso_excel=2)", '''
# Registra su propio Tipo de Cambio descartable (Diciembre 2026) para
# no depender de una fila preexistente, igual patron que CP008 de RF-01.
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
combo_mes = frame.locator(".ant-select-selector").first
combo_mes.click()
app.wait_for_timeout(400)
frame.locator(".ant-select-dropdown").get_by_text("Diciembre", exact=True).click()
app.wait_for_timeout(400)
inputs = frame.locator("input")
inputs.nth(2).fill("3.80")
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
# Si Diciembre 2026 ya existia de una corrida anterior, el Aceptar fue
# rechazado como duplicado y la pantalla queda en modo alta (no vuelve
# sola a consulta) - forzar Cancelar para garantizar volver a consulta
# antes de buscar la fila y que aparezcan Modificar/Eliminar.
boton_cancelar = frame.locator("button").filter(has_text=re.compile(r"^\\s*Cancelar\\s*$", re.I))
if boton_cancelar.count() and boton_cancelar.first.is_visible():
    boton_cancelar.first.click()
    app.wait_for_timeout(800)

filas = filas_tabla(frame)
for i in range(filas.count()):
    if "Diciembre" in filas.nth(i).inner_text() and "2026" in filas.nth(i).inner_text():
        filas.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Modificar", re.I)).click()
app.wait_for_timeout(800)
inputs = frame.locator("input")
assert inputs.nth(0).is_disabled() and inputs.nth(1).is_disabled(), "Mes y Año deberian quedar bloqueados en modo Modificar (RN-19)"
assert not inputs.nth(2).is_disabled(), "El Valor deberia quedar editable en modo Modificar"
# El iframe #aplicacion queda scrolleado hacia la fila que se clickeo
# para entrar a Modificar - sin este scroll al inicio, la captura de
# evidencia sale cortada mostrando solo la grilla y los botones, SIN
# el formulario de arriba (Mes/Año/Valor) que es justo lo que este
# paso necesita evidenciar (confirmado en vivo: Mes/Año bloqueados no
# se veian en el Word pese a que el assert de arriba pasaba bien).
# Forzar el scroll del iframe al tope absoluto (no solo
# scroll_into_view_if_needed de un campo puntual, que no alcanza
# cuando el scroll necesario es grande - ver gotcha 29).
frame.locator("body").evaluate("el => el.scrollTo(0, 0)")
app.wait_for_timeout(500)
capturar_paso(app, "mes_año_bloqueados", paso_excel=3)
inputs.nth(2).fill("3.95")
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "valor_actualizado", paso_excel=5)
filas_final = filas_tabla(frame)
fila_actualizada = next((filas_final.nth(i).inner_text() for i in range(filas_final.count()) if "Diciembre" in filas_final.nth(i).inner_text() and "2026" in filas_final.nth(i).inner_text()), "")
assert "3.95" in fila_actualizada, f"El Valor deberia reflejar 3.95 tras modificar (mensaje visto: {mensaje!r}, fila: {fila_actualizada!r})"
''')

add("CP017", "app, frame = abrir_tipo_cambio(page, paso_excel=2)", '''
# Registra su propio Tipo de Cambio descartable (Enero 2027) y lo elimina.
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
combo_mes = frame.locator(".ant-select-selector").first
combo_mes.click()
app.wait_for_timeout(400)
frame.locator(".ant-select-dropdown").get_by_text("Enero", exact=True).click()
app.wait_for_timeout(400)
inputs = frame.locator("input")
inputs.nth(1).fill("2027")
inputs.nth(2).fill("3.80")
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
boton_cancelar = frame.locator("button").filter(has_text=re.compile(r"^\\s*Cancelar\\s*$", re.I))
if boton_cancelar.count() and boton_cancelar.first.is_visible():
    boton_cancelar.first.click()
    app.wait_for_timeout(800)

filas = filas_tabla(frame)
for i in range(filas.count()):
    if "Enero" in filas.nth(i).inner_text() and "2027" in filas.nth(i).inner_text():
        filas.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Eliminar", re.I)).click()
app.wait_for_timeout(1000)
capturar_paso(app, "confirmacion_eliminar", paso_excel=2)
dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
dialogo.first.wait_for(state="visible", timeout=5000)
mensaje_confirmacion = dialogo.first.inner_text()
sigue = True
for _intento in range(3):
    boton_aceptar = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S)).first.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$", re.I))
    if boton_aceptar.count():
        boton_aceptar.first.click()
    app.wait_for_timeout(2000)
    filas_final = filas_tabla(frame)
    sigue = any("Enero" in filas_final.nth(i).inner_text() and "2027" in filas_final.nth(i).inner_text() for i in range(filas_final.count()))
    if not sigue:
        break
capturar_paso(app, "registro_eliminado", paso_excel=4)
assert not sigue, f"El Tipo de Cambio Enero 2027 deberia haber desaparecido tras eliminar (mensaje de confirmacion visto: {mensaje_confirmacion!r})"
''')

add("CP018", "app, frame = abrir_tipo_cambio(page, paso_excel=2)", '''
# Registra su propio Tipo de Cambio descartable (Febrero 2027), pide
# eliminar y CANCELA - el registro debe permanecer.
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
combo_mes = frame.locator(".ant-select-selector").first
combo_mes.click()
app.wait_for_timeout(400)
frame.locator(".ant-select-dropdown").get_by_text("Febrero", exact=True).click()
app.wait_for_timeout(400)
inputs = frame.locator("input")
inputs.nth(1).fill("2027")
inputs.nth(2).fill("3.80")
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
# Si Febrero 2027 ya existia (de una corrida anterior donde se canceló
# su eliminacion a proposito), el Aceptar fue rechazado como duplicado
# y la pantalla queda en modo alta - forzar Cancelar para volver a
# consulta antes de buscar la fila.
boton_cancelar = frame.locator("button").filter(has_text=re.compile(r"^\\s*Cancelar\\s*$", re.I))
if boton_cancelar.count() and boton_cancelar.first.is_visible():
    boton_cancelar.first.click()
    app.wait_for_timeout(800)

filas = filas_tabla(frame)
for i in range(filas.count()):
    if "Febrero" in filas.nth(i).inner_text() and "2027" in filas.nth(i).inner_text():
        filas.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Eliminar", re.I)).click()
app.wait_for_timeout(1000)
capturar_paso(app, "confirmacion_abierta", paso_excel=2)
dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
dialogo.first.wait_for(state="visible", timeout=5000)
boton_no = dialogo.first.get_by_role("button", name=re.compile(r"^\\s*(No|Cancelar)\\s*$", re.I))
boton_no.first.click()
app.wait_for_timeout(1500)
capturar_paso(app, "registro_sigue_en_listado", paso_excel=4)
filas_despues = filas_tabla(frame)
sigue = any("Febrero" in filas_despues.nth(i).inner_text() and "2027" in filas_despues.nth(i).inner_text() for i in range(filas_despues.count()))
assert sigue, "El Tipo de Cambio Febrero 2027 deberia seguir en el listado tras cancelar la eliminacion"
''')

add("CP019", "app, frame = abrir_tipo_cambio(page, paso_excel=2)", '''
for ancho, alto, nombre in [(1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(1000)
    capturar_paso(app, f"responsive_{nombre}", paso_excel=2)
    desbordamiento = app.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 5")
    assert not desbordamiento, f"La pantalla se desborda horizontalmente en resolucion {nombre} ({ancho}x{alto})"
app.set_viewport_size({"width": 1600, "height": 900})
''')


# ===========================================================================
# RF-03: Mantenimiento de Seguros de Encargo
# ===========================================================================
# CONFIRMADO via Manual_RF03_Seguro.docx + exploracion en vivo
# (_exploracion/explore_3[2-4]*.py):
# - Pantalla SIN filtro, carga TODO el listado (2 paginas, 11 filas en
#   total) al abrir - RN-24: solo Encargos facturables (reg_facturacion
#   = 'S'). Los 11 Encargos facturables reales YA tenian Seguro
#   registrado al momento de escribir estos casos - NO hay ningun
#   Encargo facturable libre (a diferencia de RF-01). Decision
#   acordada con el usuario: usar el Encargo real **"0018 - AON
#   PROTECCION FINANCIERA"** como fixture compartido para
#   CP021/CP024/CP025/CP026/CP027 (el ultimo del cluster de 5 AON
#   AFFINITY con datos casi identicos/repetidos entre si, el menos
#   "unico" de los 11). CP026 se corre ANTES que CP021 (asi lo pidio
#   el usuario) para no necesitar pedir mas datos: CP026 borra el
#   Seguro real de 0018, CP021 lo vuelve a registrar con datos de
#   prueba. CP024/CP025/CP027 usan el mismo 0018 con logica
#   "asegurar que existe, registrar si falta" para ser independientes
#   del orden real de ejecucion. CP023 (duplicado) y CP022 (campo
#   obligatorio) usan el Encargo "0001 - FONAVI", que NUNCA se toca
#   (ni se borra ni se modifica) - sirve de control estable entre
#   corridas.
# - 5 campos en orden fijo tras Ingresar: [0]=Encargo (combo),
#   [1]=Nombre del Seguro, [2]=Dirección, [3]=Teléfono (OPCIONAL, no
#   obligatorio - RN-26), [4]=Póliza (se autoconvierte a MAYÚSCULAS
#   mientras se tipea).
# - Mensajes EXACTOS confirmados en vivo:
#   "La Dirección es obligatoria."
#   "El Encargo seleccionado ya tiene un Seguro asociado."
#   "Seguro guardado." / "Seguro eliminado."
#   "¿Confirma eliminar el Seguro del Encargo <código>?"

add("CP020", "app, frame = abrir_seguros(page, paso_excel=2)", '''
filas = filas_tabla(frame)
assert filas.count() >= 1, "Se esperaba al menos 1 Seguro en el listado"
codigos_grilla = set()
for i in range(filas.count()):
    codigos_grilla.add(filas.nth(i).inner_text().split("\\t")[0])
# pagina 2 si existe
paginador2 = frame.get_by_text("2", exact=True)
if paginador2.count():
    paginador2.first.click()
    app.wait_for_timeout(1200)
    filas2 = filas_tabla(frame)
    for i in range(filas2.count()):
        codigos_grilla.add(filas2.nth(i).inner_text().split("\\t")[0])
capturar_paso(app, "listado_completo", paso_excel=2)

frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
combo = frame.locator(".ant-select-selector").first
combo.click()
app.wait_for_timeout(600)
contenedor = frame.locator("cdk-virtual-scroll-viewport").first
if contenedor.count():
    for _ in range(10):
        contenedor.evaluate("el => el.scrollTo(0, el.scrollHeight)")
        app.wait_for_timeout(400)
opciones = frame.locator("nz-option-item, [role='option']")
codigos_facturables = set(opciones.nth(i).inner_text().split(" - ")[0] for i in range(opciones.count()))
assert codigos_grilla.issubset(codigos_facturables), f"Hay Encargos en el listado que no estan entre los facturables: {codigos_grilla - codigos_facturables}"
''')

add("CP021", "app, frame = abrir_seguros(page, paso_excel=2)", '''
# El Encargo 0018 debe estar LIBRE antes de esta prueba (si ya tiene
# Seguro - de una corrida anterior donde no se borro - se borra primero).
filas = filas_tabla(frame)
tiene_seguro = any(filas.nth(i).inner_text().split("\\t")[0] == "0018" for i in range(filas.count()))
if tiene_seguro:
    for i in range(filas.count()):
        if filas.nth(i).inner_text().split("\\t")[0] == "0018":
            filas.nth(i).click()
            break
    frame.get_by_role("button", name=re.compile(r"Eliminar", re.I)).click()
    app.wait_for_timeout(1000)
    dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
    dialogo.first.wait_for(state="visible", timeout=5000)
    boton_si = frame.locator("button").filter(has_text=re.compile(r"^\\s*Aceptar\\s*$", re.I))
    if boton_si.count():
        boton_si.first.click()
    app.wait_for_timeout(1500)
    confirmar_dialogo_si_aparece(app, frame, timeout_ms=3000)

frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
combo = frame.locator(".ant-select-selector").first
combo.click()
app.wait_for_timeout(600)
contenedor = frame.locator("cdk-virtual-scroll-viewport").first
if contenedor.count():
    for _ in range(10):
        contenedor.evaluate("el => el.scrollTo(0, el.scrollHeight)")
        app.wait_for_timeout(400)
frame.locator(".ant-select-dropdown").get_by_text("0018 - AON PROTECCION FINANCIERA", exact=True).click()
app.wait_for_timeout(400)
inputs = frame.locator("input")
inputs.nth(1).fill("Seguro Prueba QA")
inputs.nth(2).fill("Av. Prueba QA 123")
inputs.nth(3).fill("987654321")
inputs.nth(4).fill("pol-test-01")
capturar_paso(app, "datos_completos", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "resultado_registro", paso_excel=6)
filas_final = filas_tabla(frame)
fila_0018 = next((filas_final.nth(i).inner_text() for i in range(filas_final.count()) if filas_final.nth(i).inner_text().split("\\t")[0] == "0018"), "")
assert fila_0018, f"El Seguro de 0018 deberia aparecer en el listado (mensaje visto: {mensaje!r})"
assert "POL-TEST-01" in fila_0018, f"La Poliza deberia guardarse en MAYUSCULAS automaticamente: {fila_0018!r}"
''')

add("CP022", "app, frame = abrir_seguros(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
combo = frame.locator(".ant-select-selector").first
combo.click()
app.wait_for_timeout(600)
frame.locator(".ant-select-dropdown").get_by_text("0001 - FONAVI", exact=True).click()
app.wait_for_timeout(400)
inputs = frame.locator("input")
inputs.nth(1).fill("Seguro Prueba QA")
inputs.nth(4).fill("pol-test-02")
capturar_paso(app, "sin_direccion", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_obligatorio", paso_excel=4, timeout_ms=5000)
assert "dirección es obligatoria" in mensaje.lower(), f"Se esperaba el mensaje de Direccion obligatoria: {mensaje!r}"
''')

add("CP023", "app, frame = abrir_seguros(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
combo = frame.locator(".ant-select-selector").first
combo.click()
app.wait_for_timeout(600)
frame.locator(".ant-select-dropdown").get_by_text("0001 - FONAVI", exact=True).click()
app.wait_for_timeout(400)
inputs = frame.locator("input")
inputs.nth(1).fill("Seguro Prueba QA")
inputs.nth(2).fill("Av. Prueba QA 123")
inputs.nth(4).fill("pol-test-03")
capturar_paso(app, "encargo_ya_asegurado", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_duplicado", paso_excel=4, timeout_ms=5000)
assert "ya tiene un seguro" in mensaje.lower(), f"Se esperaba el mensaje de Encargo ya asegurado: {mensaje!r}"
''')

add("CP024", "app, frame = abrir_seguros(page, paso_excel=2)", '''
# Asegura que el Encargo 0018 tenga un Seguro (lo registra si falta)
# para no depender del orden real de ejecucion de los demas CP.
filas = filas_tabla(frame)
tiene_seguro = any(filas.nth(i).inner_text().split("\\t")[0] == "0018" for i in range(filas.count()))
if not tiene_seguro:
    frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
    app.wait_for_timeout(600)
    combo = frame.locator(".ant-select-selector").first
    combo.click()
    app.wait_for_timeout(600)
    contenedor = frame.locator("cdk-virtual-scroll-viewport").first
    if contenedor.count():
        for _ in range(10):
            contenedor.evaluate("el => el.scrollTo(0, el.scrollHeight)")
            app.wait_for_timeout(400)
    frame.locator(".ant-select-dropdown").get_by_text("0018 - AON PROTECCION FINANCIERA", exact=True).click()
    app.wait_for_timeout(400)
    inputs = frame.locator("input")
    inputs.nth(1).fill("Seguro Prueba QA")
    inputs.nth(2).fill("Av. Prueba QA 123")
    inputs.nth(4).fill("pol-test-01")
    frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
    app.wait_for_timeout(2000)
    confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
    app.wait_for_timeout(1000)

filas2 = filas_tabla(frame)
for i in range(filas2.count()):
    if filas2.nth(i).inner_text().split("\\t")[0] == "0018":
        filas2.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Modificar", re.I)).click()
app.wait_for_timeout(800)
inputs = frame.locator("input")
inputs.nth(2).fill("")
inputs.nth(2).fill("Av. Prueba QA 456 Modificado")
capturar_paso(app, "direccion_modificada", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "cambio_reflejado", paso_excel=5)
filas3 = filas_tabla(frame)
fila_0018 = next((filas3.nth(i).inner_text() for i in range(filas3.count()) if filas3.nth(i).inner_text().split("\\t")[0] == "0018"), "")
assert "456 Modificado" in fila_0018, f"La Direccion deberia reflejar el cambio (mensaje visto: {mensaje!r}, fila: {fila_0018!r})"
''')

add("CP025", "app, frame = abrir_seguros(page, paso_excel=2)", '''
filas = filas_tabla(frame)
tiene_seguro = any(filas.nth(i).inner_text().split("\\t")[0] == "0018" for i in range(filas.count()))
if not tiene_seguro:
    frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
    app.wait_for_timeout(600)
    combo = frame.locator(".ant-select-selector").first
    combo.click()
    app.wait_for_timeout(600)
    contenedor = frame.locator("cdk-virtual-scroll-viewport").first
    if contenedor.count():
        for _ in range(10):
            contenedor.evaluate("el => el.scrollTo(0, el.scrollHeight)")
            app.wait_for_timeout(400)
    frame.locator(".ant-select-dropdown").get_by_text("0018 - AON PROTECCION FINANCIERA", exact=True).click()
    app.wait_for_timeout(400)
    inputs = frame.locator("input")
    inputs.nth(1).fill("Seguro Prueba QA")
    inputs.nth(2).fill("Av. Prueba QA 123")
    inputs.nth(4).fill("pol-test-01")
    frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
    app.wait_for_timeout(2000)
    confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
    app.wait_for_timeout(1000)

filas2 = filas_tabla(frame)
for i in range(filas2.count()):
    if filas2.nth(i).inner_text().split("\\t")[0] == "0018":
        filas2.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Modificar", re.I)).click()
app.wait_for_timeout(800)
inputs = frame.locator("input")
assert inputs.nth(0).is_disabled(), "El campo Encargo deberia quedar bloqueado en modo Modificar (RN-31)"
# El iframe #aplicacion queda scrolleado hacia la fila que se clickeo
# para entrar a Modificar - sin este scroll, la captura sale cortada
# mostrando solo la grilla/botones, sin el campo Encargo de arriba que
# es justo lo que este paso necesita evidenciar (mismo bug ya visto en
# CP016, ver gotcha 29). Forzar el tope absoluto, no solo
# scroll_into_view_if_needed de un campo puntual.
frame.locator("body").evaluate("el => el.scrollTo(0, 0)")
app.wait_for_timeout(500)
capturar_paso(app, "encargo_bloqueado", paso_excel=3)
boton_cancelar = frame.locator("button").filter(has_text=re.compile(r"^\\s*Cancelar\\s*$", re.I))
if boton_cancelar.count():
    boton_cancelar.first.click()
    app.wait_for_timeout(500)
''')

add("CP026", "app, frame = abrir_seguros(page, paso_excel=2)", '''
# Si 0018 no tiene Seguro (ya se borro en una corrida anterior), se
# registra uno descartable primero para poder probar la eliminacion.
filas = filas_tabla(frame)
tiene_seguro = any(filas.nth(i).inner_text().split("\\t")[0] == "0018" for i in range(filas.count()))
if not tiene_seguro:
    frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
    app.wait_for_timeout(600)
    combo = frame.locator(".ant-select-selector").first
    combo.click()
    app.wait_for_timeout(600)
    contenedor = frame.locator("cdk-virtual-scroll-viewport").first
    if contenedor.count():
        for _ in range(10):
            contenedor.evaluate("el => el.scrollTo(0, el.scrollHeight)")
            app.wait_for_timeout(400)
    frame.locator(".ant-select-dropdown").get_by_text("0018 - AON PROTECCION FINANCIERA", exact=True).click()
    app.wait_for_timeout(400)
    inputs = frame.locator("input")
    inputs.nth(1).fill("Seguro Prueba QA")
    inputs.nth(2).fill("Av. Prueba QA 123")
    inputs.nth(4).fill("pol-test-01")
    frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
    app.wait_for_timeout(2000)
    confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
    app.wait_for_timeout(1000)

filas2 = filas_tabla(frame)
for i in range(filas2.count()):
    if filas2.nth(i).inner_text().split("\\t")[0] == "0018":
        filas2.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Eliminar", re.I)).click()
app.wait_for_timeout(1000)
capturar_paso(app, "confirmacion_eliminar", paso_excel=2)
dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
dialogo.first.wait_for(state="visible", timeout=5000)
mensaje_confirmacion = dialogo.first.inner_text()
sigue = True
for _intento in range(3):
    boton_aceptar = frame.locator("button").filter(has_text=re.compile(r"^\\s*Aceptar\\s*$", re.I))
    if boton_aceptar.count():
        boton_aceptar.first.click()
    app.wait_for_timeout(2000)
    filas_chk = filas_tabla(frame)
    sigue = any(filas_chk.nth(i).inner_text().split("\\t")[0] == "0018" for i in range(filas_chk.count()))
    if not sigue:
        break
capturar_paso(app, "seguro_eliminado", paso_excel=4)
assert not sigue, f"El Seguro de 0018 deberia haber desaparecido (mensaje de confirmacion visto: {mensaje_confirmacion!r})"
''')

add("CP027", "app, frame = abrir_seguros(page, paso_excel=2)", '''
filas = filas_tabla(frame)
tiene_seguro = any(filas.nth(i).inner_text().split("\\t")[0] == "0018" for i in range(filas.count()))
if not tiene_seguro:
    frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
    app.wait_for_timeout(600)
    combo = frame.locator(".ant-select-selector").first
    combo.click()
    app.wait_for_timeout(600)
    contenedor = frame.locator("cdk-virtual-scroll-viewport").first
    if contenedor.count():
        for _ in range(10):
            contenedor.evaluate("el => el.scrollTo(0, el.scrollHeight)")
            app.wait_for_timeout(400)
    frame.locator(".ant-select-dropdown").get_by_text("0018 - AON PROTECCION FINANCIERA", exact=True).click()
    app.wait_for_timeout(400)
    inputs = frame.locator("input")
    inputs.nth(1).fill("Seguro Prueba QA")
    inputs.nth(2).fill("Av. Prueba QA 123")
    inputs.nth(4).fill("pol-test-01")
    frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
    app.wait_for_timeout(2000)
    confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
    app.wait_for_timeout(1000)

filas2 = filas_tabla(frame)
for i in range(filas2.count()):
    if filas2.nth(i).inner_text().split("\\t")[0] == "0018":
        filas2.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Eliminar", re.I)).click()
app.wait_for_timeout(1000)
capturar_paso(app, "confirmacion_abierta", paso_excel=2)
dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
dialogo.first.wait_for(state="visible", timeout=5000)
boton_no = dialogo.first.get_by_role("button", name=re.compile(r"^\\s*(No|Cancelar)\\s*$", re.I))
boton_no.first.click()
app.wait_for_timeout(1500)
capturar_paso(app, "seguro_sigue_en_listado", paso_excel=4)
filas3 = filas_tabla(frame)
sigue = any(filas3.nth(i).inner_text().split("\\t")[0] == "0018" for i in range(filas3.count()))
assert sigue, "El Seguro de 0018 deberia seguir en el listado tras cancelar la eliminacion"
''')

add("CP028", "app, frame = abrir_seguros(page, paso_excel=2)", '''
for ancho, alto, nombre in [(1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(1000)
    capturar_paso(app, f"responsive_{nombre}", paso_excel=2)
    desbordamiento = app.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 5")
    assert not desbordamiento, f"La pantalla se desborda horizontalmente en resolucion {nombre} ({ancho}x{alto})"
app.set_viewport_size({"width": 1600, "height": 900})
''')


# ===========================================================================
# RF-04: Mantenimiento de Promotores
# ===========================================================================
# CONFIRMADO via Manual_RF04_Promotor.docx + exploracion en vivo
# (_exploracion/explore_3[6-9]*.py):
# - ~190 Promotores reales (19 paginas), tanto Activos como
#   Desactivados en abundancia (ej. "Aiza Gil"/AG, Desactivado,
#   estable en la 1ra pagina - sirve de control fijo para CP036).
# - 4 Niveles reales: "Sucursal" (codigo 1, alcance por sucursal - al
#   elegirlo se habilita el combo Sucursal y pasa a obligatorio),
#   "Fonoluz", "Campo", "Prueba QA Nivel" (residuo de pruebas de RF-05,
#   no usar). "Desactivar" es baja LOGICA (Estado Activo/Desactivado,
#   nunca desaparece de la grilla) - NO hay boton "Eliminar".
# - 4 campos en orden fijo tras Ingresar: [0]=Nombre (texto),
#   [1]=Nivel (combo), [2]=Sucursal (combo, disabled hasta elegir
#   Nivel="Sucursal"), [3]=Rol Usuario (texto max 6, solo letras,
#   mayusculas automaticas, bloqueado al Modificar).
# - Mensajes EXACTOS confirmados en vivo:
#   "El Nombre es obligatorio."
#   "Debe seleccionar la Sucursal: el Nivel elegido es de alcance por sucursal."
#   "El Rol de Usuario ya está en uso por otro Promotor." (duplicado,
#   no viene literal en el manual, solo "rechazo del servicio" - este
#   es el texto real confirmado)
#   "No se puede modificar un Promotor que se encuentra desactivado."
#   "Promotor guardado." / "Promotor desactivado."
# - CP034 (Rol que coincide con un usuario real) QUEDA BLOQUEADO: se
#   probo con Rol "DCABA" (cuenta de pruebas) y el sistema lo acepto
#   sin problema (creo un Promotor real "QA Prueba Duplicado" con ese
#   Rol) - no hay forma de adivinar que Rol pertenece a un usuario real
#   sin informacion del dominio. Ese Promotor creado por accidente en
#   la exploracion se reutiliza como fixture de CP035 (Modificar).
# - GOTCHA real confirmado: la grilla tiene ~190 Promotores en 19
#   paginas (10 por pagina), orden alfabetico por Nombre - un
#   Promotor recien registrado con Nombre que empiece con letra
#   tardia (ej. "QA ...") NO cae en la pagina 1. Usar siempre
#   `buscar_fila_en_paginas(app, frame, columna_idx, valor)` (nuevo
#   helper del HEADER_TEMPLATE) en vez de `filas_tabla(frame)` a secas
#   para verificar que un registro nuevo aparece en el listado.

add("CP029", "app, frame = abrir_promotores(page, paso_excel=2)", '''
filas = filas_tabla(frame)
assert filas.count() >= 1, "Se esperaba al menos 1 Promotor en el listado"
capturar_paso(app, "listado_inicial", paso_excel=2)
primera = filas.first.inner_text().split("\\t")
assert len(primera) == 5, f"Se esperaban 5 columnas (Nombre/Nivel/Sucursal/Rol/Estado): {primera!r}"
assert primera[4] in ("Activo", "Desactivado"), f"Estado inesperado: {primera[4]!r}"
''')

add("CP030", "app, frame = abrir_promotores(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
inputs = frame.locator("input")
inputs.nth(0).fill("QA Promotor Registro")
combos = frame.locator(".ant-select-selector")
combos.nth(0).click()
app.wait_for_timeout(400)
frame.locator(".ant-select-dropdown").get_by_text("Campo", exact=True).click()
app.wait_for_timeout(400)
inputs.nth(3).fill("qaregi")
capturar_paso(app, "datos_completos", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "resultado_registro", paso_excel=6)
fila = buscar_fila_en_paginas(app, frame, 3, "QAREGI")
assert fila, f"El Promotor QA Promotor Registro (Rol QAREGI) deberia aparecer en el listado (mensaje visto: {mensaje!r})"
assert "Activo" in fila, f"El Promotor nuevo deberia quedar Activo: {fila!r}"
''')

add("CP031", "app, frame = abrir_promotores(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
inputs = frame.locator("input")
inputs.nth(3).fill("QATEST")
capturar_paso(app, "sin_nombre", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_obligatorio", paso_excel=4, timeout_ms=5000)
assert "nombre es obligatorio" in mensaje.lower(), f"Se esperaba el mensaje de Nombre obligatorio: {mensaje!r}"
''')

add("CP032", "app, frame = abrir_promotores(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
inputs = frame.locator("input")
inputs.nth(0).fill("QA Prueba Sucursal")
combos = frame.locator(".ant-select-selector")
combos.nth(0).click()
app.wait_for_timeout(400)
frame.locator(".ant-select-dropdown").get_by_text("Sucursal", exact=True).click()
app.wait_for_timeout(400)
inputs.nth(3).fill("QASUC")
capturar_paso(app, "nivel_sucursal_sin_sucursal", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_sucursal_obligatoria", paso_excel=4, timeout_ms=5000)
assert "debe seleccionar la sucursal" in mensaje.lower(), f"Se esperaba el mensaje de Sucursal obligatoria: {mensaje!r}"
''')

add("CP033", "app, frame = abrir_promotores(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
inputs = frame.locator("input")
inputs.nth(0).fill("QA Prueba Rol Duplicado")
combos = frame.locator(".ant-select-selector")
combos.nth(0).click()
app.wait_for_timeout(400)
frame.locator(".ant-select-dropdown").get_by_text("Fonoluz", exact=True).click()
app.wait_for_timeout(400)
inputs.nth(3).fill("AG")
capturar_paso(app, "rol_duplicado", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_duplicado", paso_excel=4, timeout_ms=5000)
assert "ya está en uso" in mensaje.lower() or "ya esta en uso" in mensaje.lower(), f"Se esperaba el mensaje de Rol duplicado: {mensaje!r}"
''')

add("CP034", "app, frame = abrir_promotores(page, paso_excel=2)", '''
# Rol "MPR" confirmado en vivo como un Rol real de un usuario de la
# empresa (visto en la columna Rol de la grilla de RF-07 Comision de
# Encargos, en una Comision antigua de 2006 "En uso" - un dato real
# de produccion, no una cuenta de prueba). Resuelve el desbloqueo de
# este caso (antes se habia probado con "DCABA" sin exito, ya que esa
# es la cuenta de pruebas, no un Rol real).
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
inputs = frame.locator("input")
inputs.nth(0).fill("QA Prueba Rol Real")
combos = frame.locator(".ant-select-selector")
combos.nth(0).click()
app.wait_for_timeout(400)
frame.locator(".ant-select-dropdown").get_by_text("Fonoluz", exact=True).click()
app.wait_for_timeout(400)
inputs.nth(3).fill("MPR")
capturar_paso(app, "rol_de_usuario_real", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_rol_usuario_real", paso_excel=4, timeout_ms=5000)
assert "usuario real" in mensaje.lower(), f"Se esperaba el mensaje de Rol de un usuario real: {mensaje!r}"
''')

add("CP035", "app, frame = abrir_promotores(page, paso_excel=2)", '''
# Reutiliza el Promotor "QA Prueba Duplicado" (Rol DCABA) creado sin
# querer durante la exploracion de CP034 - si no existiera (ambiente
# nuevo), lo registra primero.
fila_dcaba = buscar_fila_en_paginas(app, frame, 3, "DCABA")
if not fila_dcaba:
    frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
    app.wait_for_timeout(600)
    inputs = frame.locator("input")
    inputs.nth(0).fill("QA Prueba Duplicado")
    combos = frame.locator(".ant-select-selector")
    combos.nth(0).click()
    app.wait_for_timeout(400)
    frame.locator(".ant-select-dropdown").get_by_text("Fonoluz", exact=True).click()
    app.wait_for_timeout(400)
    inputs.nth(3).fill("DCABA")
    frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
    app.wait_for_timeout(2000)
    confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
    app.wait_for_timeout(1000)
    fila_dcaba = buscar_fila_en_paginas(app, frame, 3, "DCABA")

filas2 = filas_tabla(frame)
for i in range(filas2.count()):
    if filas2.nth(i).inner_text().split("\\t")[3] == "DCABA":
        filas2.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Modificar", re.I)).click()
app.wait_for_timeout(800)
inputs = frame.locator("input")
assert inputs.nth(3).is_disabled(), "El Rol Usuario deberia quedar bloqueado en modo Modificar (RN-38)"
inputs.nth(0).fill("")
inputs.nth(0).fill("QA Prueba Modificado")
# El iframe #aplicacion queda scrolleado hacia la fila que se clickeo
# para entrar a Modificar (en una pagina intermedia de la grilla
# paginada, lejos del tope) - scroll_into_view_if_needed() sobre un
# campo que ya esta en el borde superior del viewport NO hace nada (ya
# esta "a la vista"), dejando igual cortado el encabezado del
# formulario por ARRIBA de ese campo. Forzar el scroll del iframe al
# tope absoluto (no solo del campo puntual) para que la captura
# muestre el formulario completo (mismo bug de CP016/CP025, ver
# gotcha 29, version reforzada tras confirmar que el scroll puntual no
# alcanza en grillas paginadas profundas).
frame.locator("body").evaluate("el => el.scrollTo(0, 0)")
app.wait_for_timeout(500)
capturar_paso(app, "nombre_modificado", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "cambio_reflejado", paso_excel=5)
fila = buscar_fila_en_paginas(app, frame, 3, "DCABA")
assert "QA Prueba Modificado" in fila, f"El Nombre deberia reflejar el cambio (mensaje visto: {mensaje!r}, fila: {fila!r})"
''')

add("CP036", "app, frame = abrir_promotores(page, paso_excel=2)", '''
# "Aiza Gil" (Rol AG) es un Promotor real ya Desactivado, estable en
# la 1ra pagina - nunca se toca en otros casos, sirve de control fijo.
filas = filas_tabla(frame)
for i in range(filas.count()):
    if filas.nth(i).inner_text().split("\\t")[3] == "AG":
        filas.nth(i).click()
        break
app.wait_for_timeout(500)
capturar_paso(app, "promotor_desactivado_seleccionado", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Modificar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_no_se_puede_modificar", paso_excel=4, timeout_ms=5000)
assert "no se puede modificar" in mensaje.lower(), f"Se esperaba el mensaje de bloqueo por Promotor desactivado: {mensaje!r}"
''')

add("CP037", "app, frame = abrir_promotores(page, paso_excel=2)", '''
# Registra su propio Promotor descartable (Rol QADESA) para
# desactivar - si ya existe de una corrida anterior (quedaria
# Desactivado, la baja es irreversible desde esta pantalla), se
# verifica directo su Estado sin intentar registrar de nuevo.
fila_existente = buscar_fila_en_paginas(app, frame, 3, "QADESA")
if not fila_existente:
    frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
    app.wait_for_timeout(600)
    inputs = frame.locator("input")
    inputs.nth(0).fill("QA Promotor Desactivar")
    combos = frame.locator(".ant-select-selector")
    combos.nth(0).click()
    app.wait_for_timeout(400)
    frame.locator(".ant-select-dropdown").get_by_text("Campo", exact=True).click()
    app.wait_for_timeout(400)
    inputs.nth(3).fill("QADESA")
    frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
    app.wait_for_timeout(2000)
    confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
    app.wait_for_timeout(1000)
    fila_existente = buscar_fila_en_paginas(app, frame, 3, "QADESA")

if "Desactivado" in fila_existente:
    capturar_paso(app, "ya_estaba_desactivado", paso_excel=4)
else:
    filas2 = filas_tabla(frame)
    for i in range(filas2.count()):
        if filas2.nth(i).inner_text().split("\\t")[3] == "QADESA":
            filas2.nth(i).click()
            break
    app.wait_for_timeout(500)
    frame.get_by_role("button", name=re.compile(r"Desactivar", re.I)).click()
    app.wait_for_timeout(1000)
    capturar_paso(app, "confirmacion_desactivar", paso_excel=2)
    dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
    dialogo.first.wait_for(state="visible", timeout=5000)
    mensaje_confirmacion = dialogo.first.inner_text()
    for _intento in range(3):
        boton_aceptar = frame.locator("button").filter(has_text=re.compile(r"^\\s*Aceptar\\s*$", re.I))
        if boton_aceptar.count():
            boton_aceptar.first.click()
        app.wait_for_timeout(2000)
        confirmar_dialogo_si_aparece(app, frame, timeout_ms=3000)
        app.wait_for_timeout(500)
        fila_chk = buscar_fila_en_paginas(app, frame, 3, "QADESA")
        if "Desactivado" in fila_chk:
            break
    capturar_paso(app, "promotor_desactivado", paso_excel=4)

fila_final = buscar_fila_en_paginas(app, frame, 3, "QADESA")
assert "Desactivado" in fila_final, f"El Promotor QADESA deberia quedar Desactivado (sin eliminarse): {fila_final!r}"
''')

add("CP038", "app, frame = abrir_promotores(page, paso_excel=2)", '''
for ancho, alto, nombre in [(1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(1000)
    capturar_paso(app, f"responsive_{nombre}", paso_excel=2)
    desbordamiento = app.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 5")
    assert not desbordamiento, f"La pantalla se desborda horizontalmente en resolucion {nombre} ({ancho}x{alto})"
app.set_viewport_size({"width": 1600, "height": 900})
''')


add("CP039", "app, frame = abrir_niveles(page, paso_excel=2)", '''
filas = filas_tabla(frame)
n = filas.count()
assert n >= 2, f"Se esperaban al menos 2 Niveles registrados, se vieron {n}"
codigos = [filas.nth(i).locator("td").first.inner_text().strip() for i in range(n)]
capturar_paso(app, "listado_niveles", paso_excel=2)
codigos_numericos = [int(c) for c in codigos if c.isdigit()]
assert codigos_numericos == sorted(codigos_numericos), f"El listado deberia estar ordenado por Codigo ascendente: {codigos}"
''')


# ===========================================================================
# RF-05: Niveles de Promotor (resto de casos, CP039/consulta ya escrito)
# ===========================================================================
# CONFIRMADO via Manual_RF05_Nivel.docx + exploracion en vivo
# (_exploracion/explore_4[3-4]*.py):
# - Solo 5 Niveles reales, 1 pagina (sin paginacion real): 1-Sucursal-N,
#   2-Fonoluz-N, 3-Campo-N, 4-LDS-S, 9-"Prueba QA Nivel"-N (residuo de
#   una exploracion anterior, reutilizado aqui como fixture de
#   CP043/CP044 en vez de dejarlo huerfano sin uso).
# - 3 campos en orden fijo tras Ingresar: [0]=Nivel/Codigo (texto max
#   6, mayusculas automaticas, bloqueado al Modificar), [1]=Descripcion
#   (texto max 50), [2]=Promotor Especial (checkbox).
# - OJO: "Eliminar" en esta pantalla es BAJA FISICA real (DELETE,
#   irreversible) - a diferencia de RF-04 (Promotores) donde es logica.
# - Mensajes EXACTOS confirmados en vivo:
#   "El Código es obligatorio."
#   "El Código de Nivel ya existe." (duplicado - no viene literal en
#   el manual, solo "rechazo del servicio")
#   "Nivel guardado." / "Nivel eliminado."
#   "¿Confirma eliminar el Nivel <código> - <descripción>? Esta acción
#   es irreversible."

add("CP040", "app, frame = abrir_niveles(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
inputs = frame.locator("input")
inputs.nth(0).fill("qatst")
inputs.nth(1).fill("Nivel QA Registro")
capturar_paso(app, "datos_completos", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "resultado_registro", paso_excel=6)
filas = filas_tabla(frame)
fila = next((filas.nth(i).inner_text() for i in range(filas.count()) if filas.nth(i).locator("td").first.inner_text().strip() == "QATST"), "")
assert fila, f"El Nivel QATST deberia aparecer en el listado (mensaje visto: {mensaje!r})"
''')

add("CP041", "app, frame = abrir_niveles(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
inputs = frame.locator("input")
inputs.nth(1).fill("Sin codigo QA")
capturar_paso(app, "sin_codigo", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_obligatorio", paso_excel=4, timeout_ms=5000)
assert "código es obligatorio" in mensaje.lower(), f"Se esperaba el mensaje de Codigo obligatorio: {mensaje!r}"
''')

add("CP042", "app, frame = abrir_niveles(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
inputs = frame.locator("input")
inputs.nth(0).fill("9")
inputs.nth(1).fill("Duplicado QA")
capturar_paso(app, "codigo_duplicado", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_duplicado", paso_excel=4, timeout_ms=5000)
assert "ya existe" in mensaje.lower(), f"Se esperaba el mensaje de Codigo duplicado: {mensaje!r}"
''')

add("CP043", "app, frame = abrir_niveles(page, paso_excel=2)", '''
# Reutiliza el Nivel 9 ("Prueba QA Nivel"), residuo de una exploracion
# anterior, como fixture para Modificar.
filas = filas_tabla(frame)
for i in range(filas.count()):
    if filas.nth(i).locator("td").first.inner_text().strip() == "9":
        filas.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Modificar", re.I)).click()
app.wait_for_timeout(800)
inputs = frame.locator("input")
inputs.nth(1).fill("")
inputs.nth(1).fill("Prueba QA Nivel Modificado")
estaba_marcado = inputs.nth(2).is_checked()
inputs.nth(2).set_checked(not estaba_marcado)
capturar_paso(app, "datos_modificados", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "cambio_reflejado", paso_excel=5)
filas2 = filas_tabla(frame)
fila = next((filas2.nth(i).inner_text() for i in range(filas2.count()) if filas2.nth(i).locator("td").first.inner_text().strip() == "9"), "")
assert "Prueba QA Nivel Modificado" in fila, f"La Descripcion deberia reflejar el cambio (mensaje visto: {mensaje!r}, fila: {fila!r})"
especial_esperado = "S" if not estaba_marcado else "N"
assert fila.split("\\t")[-1] == especial_esperado, f"El indicador Especial deberia reflejar el cambio a {especial_esperado!r}: {fila!r}"
''')

add("CP044", "app, frame = abrir_niveles(page, paso_excel=2)", '''
filas = filas_tabla(frame)
for i in range(filas.count()):
    if filas.nth(i).locator("td").first.inner_text().strip() == "9":
        filas.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Modificar", re.I)).click()
app.wait_for_timeout(800)
inputs = frame.locator("input")
assert inputs.nth(0).is_disabled(), "El campo Nivel (Codigo) deberia quedar bloqueado en modo Modificar (RN-47)"
capturar_paso(app, "codigo_bloqueado", paso_excel=3)
boton_cancelar = frame.locator("button").filter(has_text=re.compile(r"^\\s*Cancelar\\s*$", re.I))
if boton_cancelar.count():
    boton_cancelar.first.click()
    app.wait_for_timeout(500)
''')

add("CP045", "app, frame = abrir_niveles(page, paso_excel=2)", '''
# Registra su propio Nivel descartable (QADEL) para eliminar - baja
# FISICA real, irreversible (a diferencia de RF-04).
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(600)
inputs = frame.locator("input")
inputs.nth(0).fill("qadel")
inputs.nth(1).fill("Nivel a eliminar QA")
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)

filas = filas_tabla(frame)
for i in range(filas.count()):
    if filas.nth(i).locator("td").first.inner_text().strip() == "QADEL":
        filas.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Eliminar", re.I)).click()
app.wait_for_timeout(1000)
capturar_paso(app, "confirmacion_eliminar", paso_excel=2)
dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
dialogo.first.wait_for(state="visible", timeout=5000)
mensaje_confirmacion = dialogo.first.inner_text()
assert "irreversible" in mensaje_confirmacion.lower(), f"El dialogo deberia advertir que la accion es irreversible: {mensaje_confirmacion!r}"
sigue = True
for _intento in range(3):
    boton_aceptar = frame.locator("button").filter(has_text=re.compile(r"^\\s*Aceptar\\s*$", re.I))
    if boton_aceptar.count():
        boton_aceptar.first.click()
    app.wait_for_timeout(2000)
    filas_chk = filas_tabla(frame)
    sigue = any(filas_chk.nth(i).locator("td").first.inner_text().strip() == "QADEL" for i in range(filas_chk.count()))
    if not sigue:
        break
capturar_paso(app, "nivel_eliminado", paso_excel=4)
assert not sigue, f"El Nivel QADEL deberia haber desaparecido de forma definitiva (mensaje de confirmacion visto: {mensaje_confirmacion!r})"
''')

add("CP046", "app, frame = abrir_niveles(page, paso_excel=2)", '''
# Registra su propio Nivel descartable (QACAN) y CANCELA la
# eliminacion - debe permanecer.
filas_previas = filas_tabla(frame)
ya_existe = any(filas_previas.nth(i).locator("td").first.inner_text().strip() == "QACAN" for i in range(filas_previas.count()))
if not ya_existe:
    frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
    app.wait_for_timeout(600)
    inputs = frame.locator("input")
    inputs.nth(0).fill("qacan")
    inputs.nth(1).fill("Nivel cancelar eliminar QA")
    frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
    app.wait_for_timeout(2000)
    confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
    app.wait_for_timeout(1000)

filas = filas_tabla(frame)
for i in range(filas.count()):
    if filas.nth(i).locator("td").first.inner_text().strip() == "QACAN":
        filas.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Eliminar", re.I)).click()
app.wait_for_timeout(1000)
capturar_paso(app, "confirmacion_abierta", paso_excel=2)
dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
dialogo.first.wait_for(state="visible", timeout=5000)
boton_no = dialogo.first.get_by_role("button", name=re.compile(r"^\\s*(No|Cancelar)\\s*$", re.I))
boton_no.first.click()
app.wait_for_timeout(1500)
capturar_paso(app, "nivel_sigue_en_listado", paso_excel=4)
filas2 = filas_tabla(frame)
sigue = any(filas2.nth(i).locator("td").first.inner_text().strip() == "QACAN" for i in range(filas2.count()))
assert sigue, "El Nivel QACAN deberia seguir en el listado tras cancelar la eliminacion"
''')

add("CP047", "app, frame = abrir_niveles(page, paso_excel=2)", '''
for ancho, alto, nombre in [(1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(1000)
    capturar_paso(app, f"responsive_{nombre}", paso_excel=2)
    desbordamiento = app.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 5")
    assert not desbordamiento, f"La pantalla se desborda horizontalmente en resolucion {nombre} ({ancho}x{alto})"
app.set_viewport_size({"width": 1600, "height": 900})
''')


# ===========================================================================
# RF-06: Parametros de Encargo (pantalla mas compleja del proyecto)
# ===========================================================================
# CONFIRMADO via Manual_RF06_ParametroEncargo.docx + exploracion en vivo
# (_exploracion/explore_4[5-9]*.py, explore_5[0-9]*.py):
# - 21 Encargos reales (mismos de RF-01), 3 paginas. "0002 PLUZ
#   PROTECCION" es el que actualmente tiene Franja de Recibo = S
#   (exclusiva, RN-58).
# - Inputs identificados por NAME real (mas confiable que posicion):
#   codigoEncargo (max 4), nombre (max 30), razonSocial (max 30),
#   producto (max 6, con boton lupa aria-label="search" + descripcion
#   en un <span class="field-readonly">, NO un <input>), ruc (max 11),
#   cuentaCorriente (max 20). Combos por posicion: nth(0)=Concepto,
#   nth(1)=Moneda, nth(2)=Banco. Checkboxes EN ORDEN: [0]=Afiliacion
#   Manual, [1]=Rango Edades, [2]=Franja Recibo, [3]=Registra Pago,
#   [4]=Tiene Descuento Comision, [5]=Registra Facturacion,
#   [6]=Envia Archivo de Pagos. Radios [0]=Afecta Saldo,
#   [1]=No Afecta Saldo (solo se habilitan con Registra Pago marcado).
# - Conceptos reales YA asociados a un Encargo (NO usar para alta
#   nueva, solo para probar RN-55): FONAVI (FON, ENCARGO INTERNO,
#   Encargo 0001), PAGO PLUZ PROTECCION, ENCARGO TIM, etc. Conceptos
#   de prueba LIBRES confirmados: "CONCEPTO PRUEBA OAE" (FACTURACIÓN
#   EXTERNA, confirmado libre) y varios "CONCEPTO PRUEBA ???" mas sin
#   tipo confirmado - usar OAE como el conocido.
# - GOTCHA nuevo: el buscador de Producto (CU-23) usa un tipo de
#   POPOVER DISTINTO al resto de la pantalla (`.cdk-overlay-popover`,
#   NO `.ant-modal`/`nz-modal-container`) con botones
#   `.conf-btn-ok`/`.conf-btn-cancel` en vez del patron
#   get_by_role("button", name=...) habitual - necesita su propio
#   manejo. Mensaje real confirmado: "El Producto ingresado no
#   existe." (no se encontro ningun codigo de producto real valido
#   para probar el camino positivo - CP053 solo cubre el camino
#   negativo, documentado).
# - Mensajes EXACTOS confirmados en vivo:
#   "Ya existe un Encargo registrado con ese Código." (duplicado,
#   texto real - el manual no lo da literal)
#   "El Concepto seleccionado ya está asociado a otro Encargo."
#   (tambien sin texto literal en el manual)
#   "El Producto ingresado no existe."
#   "Parámetro de Encargo guardado." / "Parámetro de Encargo desactivado."

add("CP048", "app, frame = abrir_parametros_encargo(page, paso_excel=2)", '''
filas = filas_tabla(frame)
assert filas.count() >= 1, "Se esperaba al menos 1 Encargo en el listado"
capturar_paso(app, "listado_inicial", paso_excel=2)
primera = filas.first.inner_text().split("\\t")
assert len(primera) == 8, f"Se esperaban 8 columnas (Codigo/Descripcion/RUC/Tipo/Concepto/Franja/RangoEdad/Vigente): {primera!r}"
''')

add("CP049", "app, frame = abrir_parametros_encargo(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
frame.locator('input[name="codigoEncargo"]').fill("9001")
frame.locator('input[name="nombre"]').fill("QA Encargo Registro")
encontrado = elegir_opcion_combo(app, frame, 0, "CONCEPTO PRUEBA OAE")
assert encontrado, "No se encontro el Concepto de prueba CONCEPTO PRUEBA OAE en el combo"
app.wait_for_timeout(800)
elegir_opcion_combo(app, frame, 1, "NUEVOS SOLES")
app.wait_for_timeout(400)
capturar_paso(app, "datos_completos", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "resultado_registro", paso_excel=8)
fila = buscar_fila_en_paginas(app, frame, 0, "9001")
assert fila, f"El Encargo 9001 deberia aparecer en el listado (mensaje visto: {mensaje!r})"
''')

add("CP050", "app, frame = abrir_parametros_encargo(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
frame.locator('input[name="codigoEncargo"]').fill("9009")
frame.locator('input[name="nombre"]').fill("QA Sin Moneda")
elegir_opcion_combo(app, frame, 0, "CONCEPTO PRUEBA TAE")
app.wait_for_timeout(800)
capturar_paso(app, "sin_moneda", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_obligatorio", paso_excel=4, timeout_ms=5000)
assert "moneda es obligatoria" in mensaje.lower(), f"Se esperaba el mensaje de Moneda obligatoria: {mensaje!r}"
''')

add("CP051", "app, frame = abrir_parametros_encargo(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
frame.locator('input[name="codigoEncargo"]').fill("0001")
frame.locator('input[name="nombre"]').fill("QA Codigo Duplicado")
elegir_opcion_combo(app, frame, 0, "CONCEPTO PRUEBA WLL")
app.wait_for_timeout(800)
elegir_opcion_combo(app, frame, 1, "NUEVOS SOLES")
app.wait_for_timeout(400)
capturar_paso(app, "codigo_duplicado", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_duplicado", paso_excel=4, timeout_ms=5000)
assert "ya existe un encargo" in mensaje.lower(), f"Se esperaba el mensaje de Codigo duplicado: {mensaje!r}"
''')

add("CP052", "app, frame = abrir_parametros_encargo(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
frame.locator('input[name="codigoEncargo"]').fill("9005")
frame.locator('input[name="nombre"]').fill("QA Concepto Asociado")
encontrado = elegir_opcion_combo(app, frame, 0, "FONAVI")
assert encontrado, "No se encontro el Concepto FONAVI en el combo"
app.wait_for_timeout(800)
elegir_opcion_combo(app, frame, 1, "NUEVOS SOLES")
app.wait_for_timeout(400)
capturar_paso(app, "concepto_ya_asociado", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_concepto_asociado", paso_excel=4, timeout_ms=5000)
assert "ya está asociado" in mensaje.lower() or "ya esta asociado" in mensaje.lower(), f"Se esperaba el mensaje de Concepto ya asociado: {mensaje!r}"
''')

add("CP053", "app, frame = abrir_parametros_encargo(page, paso_excel=2)", '''
# Codigo de Producto REAL confirmado en vivo (13/10/2026): "6592",
# usado por 6 Encargos ya registrados (0006/0007/0008/0010/0011/0012,
# descripcion "ENCARGOS DE COBRANZAS EN SUCURSALES") - encontrado
# recorriendo los 27 Encargos existentes en modo Modificar buscando
# cual tenia el campo Producto no vacio (durante la exploracion inicial
# no se habia encontrado ninguno, por eso el 1er borrador de este caso
# solo cubria el camino negativo). Al buscar "6592" el campo Producto
# NO abre un popover de seleccion -autocompleta DIRECTO, mostrando la
# descripcion en un <span class="field-readonly"> al lado del codigo
# (no es un <input>, por eso se lee con .inner_text(), no .input_value()).
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
campo_producto = frame.locator('input[name="producto"]')
campo_producto.fill("6592")
# Forzar el scroll al tope antes de capturar - mismo bug de evidencia
# cortada ya visto en CP016/CP025/CP035/CP056 (ver gotcha 29).
frame.locator("body").evaluate("el => el.scrollTo(0, 0)")
app.wait_for_timeout(500)
capturar_paso(app, "producto_a_buscar", paso_excel=1)
boton_lupa = frame.locator('button:has([aria-label="search"])').first
boton_lupa.click()
app.wait_for_timeout(1200)
# Hay 2 elementos ".field-readonly" en la pantalla (el otro es el
# placeholder "-" de Tipo Concepto) - acotar al contenedor del campo
# Producto (misma fila ".browse-row" que el input y la lupa) para no
# agarrar el equivocado.
fila_producto = campo_producto.locator("xpath=..")
descripcion = fila_producto.locator(".field-readonly").first
descripcion.wait_for(state="visible", timeout=5000)
texto_descripcion = descripcion.inner_text().strip()
capturar_paso(app, "codigo_y_descripcion_completados", paso_excel=3)
assert campo_producto.input_value() == "6592", "El Codigo de Producto deberia permanecer completado tras la busqueda"
assert texto_descripcion, "La Descripcion del Producto deberia completarse automaticamente tras encontrar el codigo"
assert "ENCARGOS DE COBRANZAS" in texto_descripcion.upper(), f"Descripcion de Producto inesperada: {texto_descripcion!r}"
''')

add("CP054", "app, frame = abrir_parametros_encargo(page, paso_excel=2)", '''
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
encontrado = elegir_opcion_combo(app, frame, 0, "FONAVI")
assert encontrado, "No se encontro el Concepto FONAVI (ENCARGO INTERNO) en el combo"
app.wait_for_timeout(1000)
capturar_paso(app, "concepto_encargo_interno", paso_excel=2)
checks = frame.locator("input[type='checkbox']")
assert not checks.nth(3).is_disabled(), "Registra Pago deberia habilitarse con un Concepto ENCARGO INTERNO"
assert not checks.nth(5).is_disabled(), "Registra Facturacion deberia habilitarse con un Concepto ENCARGO INTERNO"
assert checks.nth(4).is_disabled(), "Tiene Descuento por Comision deberia quedar deshabilitado con ENCARGO INTERNO"
assert checks.nth(6).is_disabled(), "Envia Archivo de Pagos deberia quedar deshabilitado con ENCARGO INTERNO"

encontrado2 = elegir_opcion_combo(app, frame, 0, "CONCEPTO PRUEBA OAE")
assert encontrado2, "No se encontro el Concepto CONCEPTO PRUEBA OAE (FACTURACION EXTERNA) en el combo"
app.wait_for_timeout(1000)
capturar_paso(app, "concepto_facturacion_externa", paso_excel=2)
checks2 = frame.locator("input[type='checkbox']")
assert checks2.nth(3).is_disabled(), "Registra Pago deberia quedar deshabilitado con FACTURACION EXTERNA"
assert checks2.nth(5).is_disabled(), "Registra Facturacion deberia quedar deshabilitado con FACTURACION EXTERNA"
assert not checks2.nth(4).is_disabled(), "Tiene Descuento por Comision deberia habilitarse con FACTURACION EXTERNA"
assert not checks2.nth(6).is_disabled(), "Envia Archivo de Pagos deberia habilitarse con FACTURACION EXTERNA"
''')

add("CP055", "app, frame = abrir_parametros_encargo(page, paso_excel=2)", '''
# RN-58: "Imprime en Franja de Recibo" es exclusivo - solo 1 Encargo a
# la vez. Esto es un dato REAL de produccion (que Encargo imprime en
# el recibo fisico) - se prueba con un Encargo descartable propio
# (9010) y al final se RESTAURA el titular original para no dejar un
# cambio operativo real sin querer.
def _buscar_titular_franja():
    for _pagina in range(5):
        filas_pag = filas_tabla(frame)
        for i in range(filas_pag.count()):
            columnas = filas_pag.nth(i).inner_text().split("\\t")
            if len(columnas) > 5 and columnas[5] == "S":
                return columnas[0]
        siguiente_pag = frame.locator("li.ant-pagination-next button, .ant-pagination-next")
        if siguiente_pag.count() and not siguiente_pag.first.is_disabled():
            siguiente_pag.first.click()
            app.wait_for_timeout(700)
        else:
            break
    return None

titular_original = _buscar_titular_franja()

# Autorreparacion: si una corrida ANTERIOR de este mismo caso se corto a
# medio camino (ej. timeout) antes de restaurar, el propio fixture
# descartable (9010) puede haber quedado como "titular real" de la
# Franja - rompiendo la logica del caso (9010 no puede perder la Franja
# a manos de si mismo). Confirmado en vivo 21/10/2026: exactamente este
# escenario dejo el dato REAL de produccion mal puesto (0002 debia
# tenerla). Si se detecta, se restaura 0002 (el titular real conocido,
# ver memoria del proyecto) ANTES de arrancar la prueba.
if titular_original == "9010":
    fila_9010_reset = filas_tabla(frame)
    for i in range(fila_9010_reset.count()):
        if fila_9010_reset.nth(i).locator("td").first.inner_text().strip() == "9010":
            fila_9010_reset.nth(i).click()
            break
    app.wait_for_timeout(500)
    frame.get_by_role("button", name=re.compile(r"Modificar", re.I)).click()
    app.wait_for_timeout(800)
    checks_reset = frame.locator("input[type=\\'checkbox\\']")
    if checks_reset.nth(2).is_checked():
        try:
            checks_reset.nth(2).uncheck()
        except Exception:
            checks_reset.nth(2).click(force=True)
    frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
    app.wait_for_timeout(2000)
    confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
    app.wait_for_timeout(1000)

    fila_0002_reset = buscar_fila_en_paginas(app, frame, 0, "0002")
    if fila_0002_reset.split("\\t")[5] != "S":
        anterior_reset = frame.locator("li.ant-pagination-prev button, .ant-pagination-prev")
        for _ in range(25):
            if anterior_reset.count() and not anterior_reset.first.is_disabled():
                anterior_reset.first.click()
                app.wait_for_timeout(400)
            else:
                break
        fila_0002_sel = filas_tabla(frame)
        for i in range(fila_0002_sel.count()):
            if fila_0002_sel.nth(i).locator("td").first.inner_text().strip() == "0002":
                fila_0002_sel.nth(i).click()
                break
        app.wait_for_timeout(500)
        frame.get_by_role("button", name=re.compile(r"Modificar", re.I)).click()
        app.wait_for_timeout(800)
        checks_0002 = frame.locator("input[type=\\'checkbox\\']")
        if not checks_0002.nth(2).is_checked():
            try:
                checks_0002.nth(2).check()
            except Exception:
                checks_0002.nth(2).click(force=True)
        frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
        app.wait_for_timeout(2000)
        confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
        app.wait_for_timeout(1000)
    titular_original = "0002"

capturar_paso(app, "titular_franja_antes", paso_excel=2)
assert titular_original, "Se esperaba que algun Encargo tuviera Franja de Recibo = S antes de la prueba"

fila_9010 = buscar_fila_en_paginas(app, frame, 0, "9010")
if not fila_9010:
    frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
    app.wait_for_timeout(800)
    frame.locator('input[name="codigoEncargo"]').fill("9010")
    frame.locator('input[name="nombre"]').fill("QA Encargo Franja")
    elegir_opcion_combo(app, frame, 0, "CONCEPTO PRUEBA HIW")
    app.wait_for_timeout(800)
    elegir_opcion_combo(app, frame, 1, "NUEVOS SOLES")
    app.wait_for_timeout(400)
    frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
    app.wait_for_timeout(2000)
    confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
    app.wait_for_timeout(1000)

filas = filas_tabla(frame)
for i in range(filas.count()):
    if filas.nth(i).locator("td").first.inner_text().strip() == "9010":
        filas.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Modificar", re.I)).click()
app.wait_for_timeout(800)
checks = frame.locator("input[type='checkbox']")
if not checks.nth(2).is_checked():
    try:
        checks.nth(2).check()
    except Exception:
        checks.nth(2).click(force=True)
capturar_paso(app, "franja_marcada_en_9010", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "exclusividad_aplicada", paso_excel=5)

fila_9010_despues = buscar_fila_en_paginas(app, frame, 0, "9010")
fila_titular_despues = buscar_fila_en_paginas(app, frame, 0, titular_original)
assert fila_9010_despues.split("\\t")[5] == "S", f"9010 deberia quedar con Franja = S: {fila_9010_despues!r}"
assert fila_titular_despues.split("\\t")[5] == "N", f"El titular anterior ({titular_original}) deberia perder la Franja: {fila_titular_despues!r}"

# Restaurar: devolver la Franja al titular original.
fila_titular = filas_tabla(frame)
for i in range(fila_titular.count()):
    if fila_titular.nth(i).locator("td").first.inner_text().strip() == titular_original:
        fila_titular.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Modificar", re.I)).click()
app.wait_for_timeout(800)
checks2 = frame.locator("input[type='checkbox']")
if not checks2.nth(2).is_checked():
    try:
        checks2.nth(2).check()
    except Exception:
        checks2.nth(2).click(force=True)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "titular_restaurado", paso_excel=5)
fila_restaurada = buscar_fila_en_paginas(app, frame, 0, titular_original)
assert fila_restaurada.split("\\t")[5] == "S", f"El titular original ({titular_original}) deberia haber recuperado la Franja de Recibo: {fila_restaurada!r}"
''')

add("CP056", "app, frame = abrir_parametros_encargo(page, paso_excel=2)", '''
# Registra su propio Encargo descartable (9007) para Modificar.
fila_existente = buscar_fila_en_paginas(app, frame, 0, "9007")
if not fila_existente:
    frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
    app.wait_for_timeout(800)
    frame.locator('input[name="codigoEncargo"]').fill("9007")
    frame.locator('input[name="nombre"]').fill("QA Encargo Modificar")
    elegir_opcion_combo(app, frame, 0, "CONCEPTO PRUEBA XCM")
    app.wait_for_timeout(800)
    elegir_opcion_combo(app, frame, 1, "NUEVOS SOLES")
    app.wait_for_timeout(400)
    frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
    app.wait_for_timeout(2000)
    confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
    app.wait_for_timeout(1000)

filas = filas_tabla(frame)
for i in range(filas.count()):
    if filas.nth(i).locator("td").first.inner_text().strip() == "9007":
        filas.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Modificar", re.I)).click()
app.wait_for_timeout(800)
assert frame.locator('input[name="codigoEncargo"]').is_disabled(), "El Codigo de Encargo deberia quedar bloqueado en modo Modificar (RN-62)"
frame.locator('input[name="nombre"]').fill("")
frame.locator('input[name="nombre"]').fill("QA Encargo Modificado")
# El iframe #aplicacion queda scrolleado hacia la fila que se clickeo
# para entrar a Modificar (grilla paginada) - scroll_into_view_if_needed()
# sobre un campo que ya esta al borde superior del viewport no hace
# nada, dejando igual cortado el encabezado del formulario. Forzar el
# scroll del iframe al tope absoluto (version reforzada del gotcha 29,
# scroll puntual no alcanza en grillas paginadas profundas).
frame.locator("body").evaluate("el => el.scrollTo(0, 0)")
app.wait_for_timeout(500)
capturar_paso(app, "nombre_modificado", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "cambio_reflejado", paso_excel=5)
fila = buscar_fila_en_paginas(app, frame, 0, "9007")
assert "QA Encargo Modificado" in fila, f"El Nombre deberia reflejar el cambio (mensaje visto: {mensaje!r}, fila: {fila!r})"
''')

add("CP057", "app, frame = abrir_parametros_encargo(page, paso_excel=2)", '''
# Registra su propio Encargo descartable (9008) para Desactivar -
# baja LOGICA (sigue en la grilla con Vigente = X), igual patron que
# RF-04.
fila_existente = buscar_fila_en_paginas(app, frame, 0, "9008")
if not fila_existente or "✗" not in fila_existente:
    if not fila_existente:
        frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
        app.wait_for_timeout(800)
        frame.locator('input[name="codigoEncargo"]').fill("9008")
        frame.locator('input[name="nombre"]').fill("QA Encargo Desactivar")
        elegir_opcion_combo(app, frame, 0, "CONCEPTO PRUEBA YJD")
        app.wait_for_timeout(800)
        elegir_opcion_combo(app, frame, 1, "NUEVOS SOLES")
        app.wait_for_timeout(400)
        frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
        app.wait_for_timeout(2000)
        confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
        app.wait_for_timeout(1000)

    filas = filas_tabla(frame)
    for i in range(filas.count()):
        if filas.nth(i).locator("td").first.inner_text().strip() == "9008":
            filas.nth(i).click()
            break
    app.wait_for_timeout(500)
    frame.get_by_role("button", name=re.compile(r"Desactivar", re.I)).click()
    app.wait_for_timeout(1000)
    capturar_paso(app, "confirmacion_desactivar", paso_excel=2)
    dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
    dialogo.first.wait_for(state="visible", timeout=5000)
    mensaje_confirmacion = dialogo.first.inner_text()
    for _intento in range(3):
        boton_aceptar = frame.locator("button").filter(has_text=re.compile(r"^\\s*Aceptar\\s*$", re.I))
        if boton_aceptar.count():
            boton_aceptar.first.click()
        app.wait_for_timeout(2000)
        confirmar_dialogo_si_aparece(app, frame, timeout_ms=3000)
        app.wait_for_timeout(500)
        fila_chk = buscar_fila_en_paginas(app, frame, 0, "9008")
        if "✗" in fila_chk:
            break
    capturar_paso(app, "encargo_desactivado", paso_excel=4)

fila_final = buscar_fila_en_paginas(app, frame, 0, "9008")
assert "✗" in fila_final, f"El Encargo 9008 deberia quedar marcado como no vigente, sin eliminarse: {fila_final!r}"
''')

add("CP058", "app, frame = abrir_parametros_encargo(page, paso_excel=2)", '''
for ancho, alto, nombre in [(1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(1000)
    capturar_paso(app, f"responsive_{nombre}", paso_excel=2)
    desbordamiento = app.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 5")
    assert not desbordamiento, f"La pantalla se desborda horizontalmente en resolucion {nombre} ({ancho}x{alto})"
app.set_viewport_size({"width": 1600, "height": 900})
''')


# ===========================================================================
# RF-07: Comision de Encargos de Cobranza
# ===========================================================================
# CONFIRMADO via Manual_RF07_Comision.docx + exploracion en vivo
# (_exploracion/explore_6[2-3]*.py):
# - El combo "Descripción" solo lista Encargos con "Tiene Descuento por
#   Comisión" habilitado desde RF-06 (12 reales confirmados). Se usa
#   "TELEFONICA DEL PERU MOVILES" (Encargo 0010, vigente) como fixture
#   fijo en todos los casos.
# - HALLAZGO: ese Encargo YA TIENE una Comisión real marcada "En uso"
#   (Tipo Monto, Moneda NUEVOS SOLES, Valor 0.00, Rol "MPR En uso",
#   fecha 2006-01-02) - se reutiliza DIRECTO como fixture de CP066, sin
#   necesidad de crear nada (no hay forma de marcar una comisión
#   "En uso" desde esta pantalla, requiere una Orden de Pago real).
# - Inputs confirmados por posicion/name: radio[0]=Porcentaje del
#   Total (seleccionado por defecto), radio[1]=Monto Por Operación,
#   radio[2]=Cobranza Especial. name="valorPorcentaje" (numero),
#   name="moneda" (texto max 4, disabled salvo radio Monto),
#   name="valorMonto" (numero, disabled salvo radio Monto).
# - Sin boton Modificar (no existe, solo Ingresar/Aceptar + Eliminar).
#   Eliminar NO se deshabilita aunque la fila diga "En uso" - es
#   intencional (lo valida el backend, no el cliente) para poder ver
#   el mensaje de rechazo.
# - Mensajes EXACTOS confirmados (coinciden con el manual):
#   "El Porcentaje es obligatorio y debe ser mayor a cero."
#   "La Moneda es obligatoria para el Tipo "Monto Por Operación"."
#   "Comisión registrada." / "Comisión eliminada."

add("CP059", "app, frame = abrir_comision(page, paso_excel=2)", '''
combo = frame.locator(".ant-select-selector").first
combo.click()
app.wait_for_timeout(600)
frame.locator(".ant-select-dropdown").get_by_text("TELEFONICA DEL PERU MOVILES", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "comisiones_del_encargo", paso_excel=4)
filas = filas_tabla(frame)
assert filas.count() >= 1, "Se esperaba al menos 1 Comision para este Encargo"
primera = filas.first.inner_text().split("\\t")
assert len(primera) == 5, f"Se esperaban 5 columnas (Fecha/Tipo/Moneda/Valor/Rol): {primera!r}"
''')

add("CP060", "app, frame = abrir_comision(page, paso_excel=2)", '''
combo = frame.locator(".ant-select-selector").first
combo.click()
app.wait_for_timeout(600)
frame.locator(".ant-select-dropdown").get_by_text("TELEFONICA DEL PERU MOVILES", exact=True).click()
app.wait_for_timeout(1200)
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
frame.locator(\'input[name="valorPorcentaje"]\').fill("2.5")
capturar_paso(app, "porcentaje_valido", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "resultado_registro", paso_excel=5)
filas = filas_tabla(frame)
encontrado = any("2.50" in filas.nth(i).inner_text() and "Porcentaje" in filas.nth(i).inner_text() for i in range(filas.count()))
assert encontrado, f"La Comision de 2.5% deberia aparecer en el listado (mensaje visto: {mensaje!r})"
''')

add("CP061", "app, frame = abrir_comision(page, paso_excel=2)", '''
combo = frame.locator(".ant-select-selector").first
combo.click()
app.wait_for_timeout(600)
frame.locator(".ant-select-dropdown").get_by_text("TELEFONICA DEL PERU MOVILES", exact=True).click()
app.wait_for_timeout(1200)
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
frame.locator(\'input[name="valorPorcentaje"]\').fill("0")
capturar_paso(app, "porcentaje_cero", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_porcentaje", paso_excel=4, timeout_ms=5000)
assert "porcentaje" in mensaje.lower() and "mayor a cero" in mensaje.lower(), f"Se esperaba el mensaje de Porcentaje obligatorio/mayor a cero: {mensaje!r}"
''')

add("CP062", "app, frame = abrir_comision(page, paso_excel=2)", '''
combo = frame.locator(".ant-select-selector").first
combo.click()
app.wait_for_timeout(600)
frame.locator(".ant-select-dropdown").get_by_text("TELEFONICA DEL PERU MOVILES", exact=True).click()
app.wait_for_timeout(1200)
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
radios = frame.locator("input[type=\'radio\']")
try:
    radios.nth(1).check()
except Exception:
    radios.nth(1).click(force=True)
app.wait_for_timeout(400)
selects_ant = frame.locator(".ant-select-selector")
selects_ant.nth(1).click()
app.wait_for_timeout(600)
frame.locator(".cdk-overlay-container .ant-select-item-option").filter(has_text="DOLARES U.S.A.").first.click()
app.wait_for_timeout(400)
frame.locator(\'input[name="valorMonto"]\').fill("15")
capturar_paso(app, "monto_valido", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "resultado_registro", paso_excel=5)
filas = filas_tabla(frame)
encontrado = any("DOLARES U.S.A." in filas.nth(i).inner_text() and "15.00" in filas.nth(i).inner_text() for i in range(filas.count()))
assert encontrado, f"La Comision de 15 DOLARES U.S.A. deberia aparecer en el listado con la descripcion completa de la Moneda, no truncada (mensaje visto: {mensaje!r})"
''')

add("CP063", "app, frame = abrir_comision(page, paso_excel=2)", '''
combo = frame.locator(".ant-select-selector").first
combo.click()
app.wait_for_timeout(600)
frame.locator(".ant-select-dropdown").get_by_text("TELEFONICA DEL PERU MOVILES", exact=True).click()
app.wait_for_timeout(1200)
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
radios = frame.locator("input[type=\'radio\']")
try:
    radios.nth(1).check()
except Exception:
    radios.nth(1).click(force=True)
app.wait_for_timeout(400)
frame.locator(\'input[name="valorMonto"]\').fill("10")
capturar_paso(app, "monto_sin_moneda", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_moneda", paso_excel=4, timeout_ms=5000)
assert "moneda es obligatoria" in mensaje.lower(), f"Se esperaba el mensaje de Moneda obligatoria: {mensaje!r}"
''')

add("CP064", "app, frame = abrir_comision(page, paso_excel=2)", '''
combo = frame.locator(".ant-select-selector").first
combo.click()
app.wait_for_timeout(600)
frame.locator(".ant-select-dropdown").get_by_text("TELEFONICA DEL PERU MOVILES", exact=True).click()
app.wait_for_timeout(1200)
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
radios = frame.locator("input[type=\'radio\']")
try:
    radios.nth(2).check()
except Exception:
    radios.nth(2).click(force=True)
app.wait_for_timeout(400)
capturar_paso(app, "cobranza_especial", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)
capturar_paso(app, "resultado_registro", paso_excel=5)
filas = filas_tabla(frame)
encontrado = any("Especial" in filas.nth(i).inner_text() for i in range(filas.count()))
assert encontrado, f"La Comision de Cobranza Especial deberia aparecer en el listado (mensaje visto: {mensaje!r})"
''')

add("CP065", "app, frame = abrir_comision(page, paso_excel=2)", '''
# Registra su propia Comision descartable (Porcentaje = 99.99, valor
# distintivo para ubicarla sin ambiguedad) para eliminarla.
combo = frame.locator(".ant-select-selector").first
combo.click()
app.wait_for_timeout(600)
frame.locator(".ant-select-dropdown").get_by_text("TELEFONICA DEL PERU MOVILES", exact=True).click()
app.wait_for_timeout(1200)
frame.get_by_role("button", name=re.compile(r"Ingresar", re.I)).click()
app.wait_for_timeout(800)
frame.locator(\'input[name="valorPorcentaje"]\').fill("99.99")
frame.get_by_role("button", name=re.compile(r"Aceptar", re.I)).click()
app.wait_for_timeout(2000)
confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1000)

filas = filas_tabla(frame)
for i in range(filas.count()):
    if "99.99" in filas.nth(i).inner_text():
        filas.nth(i).click()
        break
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Eliminar", re.I)).click()
app.wait_for_timeout(1000)
capturar_paso(app, "confirmacion_eliminar", paso_excel=2)
dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
dialogo.first.wait_for(state="visible", timeout=5000)
mensaje_confirmacion = dialogo.first.inner_text()
sigue = True
for _intento in range(3):
    boton_aceptar = frame.locator("button").filter(has_text=re.compile(r"^\\s*Aceptar\\s*$", re.I))
    if boton_aceptar.count():
        boton_aceptar.first.click()
    app.wait_for_timeout(2000)
    filas_chk = filas_tabla(frame)
    sigue = any("99.99" in filas_chk.nth(i).inner_text() for i in range(filas_chk.count()))
    if not sigue:
        break
capturar_paso(app, "comision_eliminada", paso_excel=4)
assert not sigue, f"La Comision de 99.99% deberia haber desaparecido (mensaje de confirmacion visto: {mensaje_confirmacion!r})"
''')

add("CP066", "app, frame = abrir_comision(page, paso_excel=2)", '''
# Usa la Comision real YA marcada "En uso" (Tipo Monto, 2006-01-02,
# Rol "MPR En uso") - no hay forma de crear una "En uso" desde esta
# pantalla, requiere una Orden de Pago real.
combo = frame.locator(".ant-select-selector").first
combo.click()
app.wait_for_timeout(600)
frame.locator(".ant-select-dropdown").get_by_text("TELEFONICA DEL PERU MOVILES", exact=True).click()
app.wait_for_timeout(800)
spinner = frame.locator(".ant-spin")
try:
    spinner.first.wait_for(state="visible", timeout=2000)
    spinner.first.wait_for(state="hidden", timeout=15000)
except PWTimeoutError:
    pass
app.wait_for_timeout(500)
anterior = frame.locator("li.ant-pagination-prev button, .ant-pagination-prev")
for _ in range(25):
    if anterior.count() and not anterior.first.is_disabled():
        anterior.first.click()
        app.wait_for_timeout(500)
    else:
        break
fila_en_uso = None
for _ in range(25):
    filas = filas_tabla(frame)
    for i in range(filas.count()):
        if "En uso" in filas.nth(i).inner_text():
            fila_en_uso = filas.nth(i)
            break
    if fila_en_uso:
        break
    siguiente = frame.locator("li.ant-pagination-next button, .ant-pagination-next")
    if siguiente.count() and not siguiente.first.is_disabled():
        siguiente.first.click()
        app.wait_for_timeout(800)
    else:
        break
assert fila_en_uso, "Se esperaba encontrar la Comision real marcada En uso para este Encargo (recorrida toda la paginacion)"
fila_en_uso.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Eliminar", re.I)).click()
app.wait_for_timeout(1000)
capturar_paso(app, "confirmacion_eliminar_en_uso", paso_excel=2)
mensaje = confirmar_dialogo_si_aparece(app, frame, timeout_ms=5000)
app.wait_for_timeout(1500)
capturar_paso(app, "rechazo_en_uso", paso_excel=4)
filas2 = filas_tabla(frame)
sigue = any("En uso" in filas2.nth(i).inner_text() for i in range(filas2.count()))
assert sigue, f"La Comision En uso NO deberia haberse eliminado (mensaje visto: {mensaje!r})"
''')

add("CP067", "app, frame = abrir_comision(page, paso_excel=2)", '''
combo = frame.locator(".ant-select-selector").first
combo.click()
app.wait_for_timeout(600)
frame.locator(".ant-select-dropdown").get_by_text("TELEFONICA DEL PERU MOVILES", exact=True).click()
app.wait_for_timeout(1200)
for ancho, alto, nombre in [(1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(1000)
    capturar_paso(app, f"responsive_{nombre}", paso_excel=2)
    desbordamiento = app.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 5")
    assert not desbordamiento, f"La pantalla se desborda horizontalmente en resolucion {nombre} ({ancho}x{alto})"
app.set_viewport_size({"width": 1600, "height": 900})
''')


# ===========================================================================
# RF-08: Consulta de Catastro de Conexiones Electricas (pantalla de SOLO
# LECTURA, unica del sprint que no registra/modifica/elimina nada)
# ===========================================================================
# CONFIRMADO via Manual_RF08_Catastro.docx + exploracion en vivo
# (_exploracion/explore_6[7-9]*.py, explore_7[0-1]*.py):
# - Suministro real confirmado, con datos completos (Datos Generales +
#   3 Medidores + Catastros): **15** (confirmado en vivo 13/10/2026,
#   reemplaza el "1352659" inicial del manual a pedido del usuario -
#   "5" tambien es real pero sin medidores instalados, "15" es mas
#   completo). Suministro inexistente de prueba: **1** (confirmado con
#   captura de red: POST .../api/catastro/ObtenerCatastro -> HTTP 404,
#   "El Suministro ingresado no existe." - codigo HTTP correcto para
#   "no encontrado", NO es un defecto, es el comportamiento esperado).
# - Unico input real: name="numeroSuministro". Botones: "?" (Buscar
#   suministro, aria-label="Buscar suministro"), "Leer", "Limpiar",
#   "A Excel" - los 3 ultimos CON icono (usar regex sin ancla, no
#   name="Leer", exact=True).
# - RN-77: tras una consulta exitosa, numeroSuministro y "?" quedan
#   bloqueados, "Limpiar" y "A Excel" se habilitan.
# - RN-78 (suministro predefinido): confirmado en vivo que se puede
#   simular reasignando el `src` del iframe #aplicacion agregando
#   `&suministro=<numero>` a la URL real (que ya trae su propio
#   `?tokenId=...`) - la consulta se dispara sola al cargar y
#   "Limpiar" queda deshabilitado permanentemente en ese modo.
# - CP068 (buscador "?") QUEDA BLOQUEADO: el catalogo plt_query_cab
#   con codigo 'BUSCAR_SUMIN' (conexion XNEAR) NO existe en este
#   ambiente - exactamente la precondicion que el propio manual
#   advierte en su seccion 5.1. Mensaje real confirmado: "No existe
#   plt_query_cab con codigo='BUSCAR_SUMIN'." Se documenta el
#   comportamiento real (bloqueo de infraestructura, no defecto de
#   codigo) en vez de forzar un camino feliz que no es alcanzable.
# - Mensajes EXACTOS confirmados en vivo:
#   "El Número de Suministro es obligatorio."
#   "El Suministro ingresado no existe." (en un dialogo con boton
#   "Cerrar", no "Aceptar" - confirmar_dialogo_si_aparece ya lo cubre)

add("CP068", "app, frame = abrir_catastro(page, paso_excel=2)", '''
# El defecto real de IT1 (13/10/2026: catalogo BUSCAR_SUMIN faltante en
# el backend, HTTP 400) YA NO SE REPRODUCE - confirmado en vivo
# 21/10/2026 por el usuario (el buscador si abre con una lista real de
# clientes) y con captura de red propia (GET .../Sqlgui/Modal/BUSCAR_SUMIN
# -> HTTP 200 ahora). El popup de busqueda NO es un
# .ant-modal/nz-modal-container (estructura propia de esta pantalla,
# filas con clase "sm-fila") - clickear una fila habilita "Seleccionar",
# y al confirmar el Numero de Suministro se autocompleta.
frame.get_by_role("button", name="Buscar suministro").click()
app.wait_for_timeout(1500)
capturar_paso(app, "buscador_abierto", paso_excel=2)
filas_buscador = frame.locator("tbody tr")
filas_buscador.first.wait_for(state="visible", timeout=10000)
cliente_elegido = filas_buscador.first.inner_text().split("\\t")[0]
filas_buscador.first.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"^Seleccionar$", re.I)).click()
app.wait_for_timeout(1500)
capturar_paso(app, "suministro_completado", paso_excel=3)
valor_suministro = frame.locator(\'input[name="numeroSuministro"]\').input_value()
assert valor_suministro.strip() == cliente_elegido, f"El Numero de Suministro deberia autocompletarse con el cliente elegido ({cliente_elegido!r}): {valor_suministro!r}"

texto_resultado = frame.locator("body").inner_text()
assert "Datos Generales" in texto_resultado or cliente_elegido in texto_resultado, f"Se esperaba que la consulta se ejecute automaticamente mostrando los datos del suministro {cliente_elegido!r}: {texto_resultado!r}"
''')

add("CP069", "app, frame = abrir_catastro(page, paso_excel=2)", '''
frame.locator(\'input[name="numeroSuministro"]\').fill("15")
capturar_paso(app, "suministro_ingresado", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(5000)
capturar_paso(app, "resultado_consulta", paso_excel=4)
texto = frame.locator("body").inner_text()
assert "Datos Generales" in texto, f"Se esperaba el bloque Datos Generales: {texto[:300]!r}"
assert "Medidores instalados" in texto, f"Se esperaba el bloque Medidores instalados: {texto[:300]!r}"
assert "Catastros de conexión" in texto, f"Se esperaba el bloque Catastros de conexion: {texto[:300]!r}"
''')

add("CP070", "app, frame = abrir_catastro(page, paso_excel=2)", '''
capturar_paso(app, "sin_suministro", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_obligatorio", paso_excel=4, timeout_ms=5000)
assert "número de suministro es obligatorio" in mensaje.lower() or "numero de suministro es obligatorio" in mensaje.lower(), f"Se esperaba el mensaje de Suministro obligatorio: {mensaje!r}"
''')

add("CP071", "app, frame = abrir_catastro(page, paso_excel=2)", '''
# DEFECTO REAL CONFIRMADO 13/10/2026 (hallazgo del usuario): el
# mensaje de "Suministro no existe" sale en un dialogo "Error de
# Servicio" (tabs Mensaje Usuario/Mensaje Detallado, boton "Cerrar"
# rojo) en vez de la "Ventana de Validacion" normal (azul, boton
# "Aceptar") que usa el resto del proyecto para CUALQUIER otra
# validacion esperada - confirmado comparando contra CP070 (la MISMA
# pantalla, campo obligatorio, SI muestra Ventana de Validacion). Esto
# indica que el backend lanza una excepcion no controlada en vez de
# una respuesta de validacion normal (confirmado con captura de red:
# POST .../api/catastro/ObtenerCatastro -> HTTP 404) - el usuario ve
# un dialogo de "error del sistema" para lo que deberia ser un
# resultado esperado y manejado ("no se encontro el registro").
frame.locator(\'input[name="numeroSuministro"]\').fill("1")
capturar_paso(app, "suministro_inexistente", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(3000)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_no_existe", paso_excel=4, timeout_ms=5000)
assert "no existe" in mensaje.lower(), f"Se esperaba el mensaje de Suministro inexistente: {mensaje!r}"
assert "validaci" in mensaje.lower(), (
    "DEFECTO REAL: el mensaje de Suministro inexistente deberia "
    "mostrarse en una Ventana de Validacion normal (como CUALQUIER "
    "otra validacion del proyecto, ej. CP070 en esta misma pantalla), "
    "no como \\'Error de Servicio\\' (el patron reservado para "
    "excepciones no controladas del backend) - confirmado con captura "
    "de red que el backend devuelve HTTP 404 en vez de una respuesta "
    f"de validacion normal: {mensaje!r}"
)
''')

add("CP072", "app, frame = abrir_catastro(page, paso_excel=2)", '''
frame.locator(\'input[name="numeroSuministro"]\').fill("15")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(5000)
capturar_paso(app, "tras_consultar", paso_excel=2)
assert frame.locator(\'input[name="numeroSuministro"]\').is_disabled(), "El campo Numero de Suministro deberia quedar bloqueado tras consultar (RN-77)"
assert frame.get_by_role("button", name="Buscar suministro").is_disabled(), "El boton '?' deberia quedar bloqueado tras consultar (RN-77)"
''')

add("CP073", "app, frame = abrir_catastro(page, paso_excel=2)", '''
# DEFECTO REAL CONFIRMADO 13/10/2026 (hallazgo del usuario: "el
# archivo a descargar esta danado y no se puede abrir"). El 1er
# borrador de este caso solo verificaba el NOMBRE sugerido del
# archivo, nunca el contenido descargado - por eso el defecto real
# paso desapercibido. Confirmado descargando y guardando el archivo
# real: tiene cientos de ocurrencias de la secuencia UTF-8 de
# reemplazo UTF-8 (caracter Unicode U+FFFD) distribuidas por TODO
# el archivo (empezando dentro del encabezado ZIP) - mas de la mitad
# del contenido binario queda corrompido, consistente con que el
# backend trata la respuesta binaria del .xlsx como texto UTF-8 en
# algun punto del camino (cualquier byte >= 0x80 que no forma una
# secuencia UTF-8 valida se reemplaza por este marcador de 3 bytes,
# desalineando el archivo). zipfile.is_zipfile() da True (hay un
# header ZIP local valido al inicio) pero abrir el archivo real falla
# con "Bad magic number for central directory" - no abre en Excel.
frame.locator(\'input[name="numeroSuministro"]\').fill("15")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(5000)
capturar_paso(app, "antes_de_exportar", paso_excel=2)
with app.expect_download(timeout=15000) as descarga_info:
    frame.get_by_role("button", name=re.compile(r"A Excel", re.I)).click()
descarga = descarga_info.value
capturar_paso(app, "exportacion_completada", paso_excel=3)
assert descarga.suggested_filename.startswith("Catastro_"), f"Se esperaba un archivo Catastro_*.xlsx: {descarga.suggested_filename!r}"
assert descarga.suggested_filename.endswith(".xlsx"), f"Se esperaba un archivo .xlsx: {descarga.suggested_filename!r}"
ruta_descarga = EVIDENCIA / descarga.suggested_filename
descarga.save_as(str(ruta_descarga))
try:
    with zipfile.ZipFile(ruta_descarga) as z:
        primer_malo = z.testzip()
    error_zip = None if primer_malo is None else f"archivo interno dañado: {primer_malo}"
except Exception as e:
    error_zip = str(e)
assert error_zip is None, (
    "DEFECTO REAL: el archivo Excel descargado esta corrupto y no se "
    f"puede abrir ({error_zip}). El contenido binario del .xlsx llega "
    "con cientos de bytes reemplazados por el marcador UTF-8 de "
    "reemplazo (U+FFFD), consistente con que el backend trata la "
    "respuesta binaria como texto UTF-8 en algun punto del camino."
)
''')

add("CP074", "app, frame = abrir_catastro(page, paso_excel=2)", '''
capturar_paso(app, "pantalla_inicial", paso_excel=2)
assert frame.get_by_role("button", name=re.compile(r"A Excel", re.I)).is_disabled(), "El boton A Excel deberia estar deshabilitado antes de una consulta exitosa (RN-79)"
''')

add("CP075", "app, frame = abrir_catastro(page, paso_excel=2)", '''
frame.locator(\'input[name="numeroSuministro"]\').fill("15")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(5000)
capturar_paso(app, "con_resultado", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"Limpiar", re.I)).click()
app.wait_for_timeout(1500)
capturar_paso(app, "pantalla_limpia", paso_excel=3)
texto = frame.locator("body").inner_text()
assert "Datos Generales" not in texto, f"Los datos consultados deberian desaparecer tras Limpiar: {texto[:300]!r}"
assert not frame.locator(\'input[name="numeroSuministro"]\').is_disabled(), "El campo Numero de Suministro deberia volver a estar habilitado tras Limpiar"
assert frame.locator(\'input[name="numeroSuministro"]\').input_value() == "", "El campo Numero de Suministro deberia quedar vacio tras Limpiar"
''')

add("CP076", "app, frame = abrir_catastro(page, paso_excel=2)", '''
# RN-78: simular apertura con Suministro predefinido reasignando el
# src del iframe #aplicacion (confirmado en vivo que dispara la
# consulta automatica igual que un ?suministro=<nro> real).
src_actual = app.locator("#aplicacion").get_attribute("src")
nuevo_src = src_actual + ("&" if "?" in src_actual else "?") + "suministro=15"
app.evaluate("src => document.querySelector(\\'#aplicacion\\').src = src", nuevo_src)
app.wait_for_timeout(5000)
frame2 = app.locator("#aplicacion").content_frame
capturar_paso(app, "suministro_predefinido", paso_excel=2)
texto = frame2.locator("body").inner_text()
assert "Datos Generales" in texto, f"La consulta deberia ejecutarse sola con el Suministro predefinido: {texto[:300]!r}"
assert frame2.get_by_role("button", name=re.compile(r"Limpiar", re.I)).is_disabled(), "El boton Limpiar deberia estar deshabilitado con un Suministro predefinido (RN-78)"
''')

add("CP077", "app, frame = abrir_catastro(page, paso_excel=2)", '''
frame.locator(\'input[name="numeroSuministro"]\').fill("15")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(5000)
for ancho, alto, nombre in [(1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(1000)
    capturar_paso(app, f"responsive_{nombre}", paso_excel=2)
    desbordamiento = app.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 5")
    assert not desbordamiento, f"La pantalla se desborda horizontalmente en resolucion {nombre} ({ancho}x{alto})"
app.set_viewport_size({"width": 1600, "height": 900})
''')


if __name__ == "__main__":
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")
