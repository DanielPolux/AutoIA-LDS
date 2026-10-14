"""
generate_scripts.py - PR000349-SP7 (Migracion modulo EncargoCobra:
auditoria de afiliaciones, relacion cliente-encargo/cliente-proyecto,
transferencia de archivos, encargos de cobranza, promociones,
afiliaciones por promotor especial, resumen periodico de afiliacion).

CONFIRMADO EN VIVO 13/10/2026 (_exploracion/explore_0[1-3]*.py):

1. 8 RF, 53 casos (MCP_PR000349_Sprint7.xlsx).

2. Usuario de pruebas: DCABA_DW / Melquisedec_01 - ve las 8 pantallas.

3. Navegacion: Aplicaciones > Comercial > <Nombre exacto>, DIRECTO (2
   niveles, sin categoria intermedia). Mismo mecanismo de siempre
   (popup con iframe #aplicacion).

4. Framework ant-design/ng-zorro confirmado (71 ocurrencias "ant-", 26
   "nz-" en el HTML de RF-01) - MISMO framework que PR000349-SP6, se
   reusan los helpers ya probados ahi (filas_tabla, confirmar_dialogo_
   si_aparece, capturar_mensaje_dialogo, elegir_opcion_combo) como
   punto de partida.

5. Las 8 pantallas y sus componentes Angular raiz, confirmados
   abriendo cada una con DCABA_DW:
   RF-01 Auditoria De Afiliaciones          -> app-afilia            (9 casos)
   RF-02 Mantenimiento De Clientes De Encargos -> app-cliente-encargo (6 casos)
   RF-03 Consulta De Proyectos De Encargos  -> app-proyecto          (7 casos)
   RF-04 Restaura Y Transfiere A Proceso    -> app-traslado          (5 casos)
   RF-05 Encargos De Cobranza               -> app-lisafi            (8 casos)
   RF-06 Promocion De Afiliados             -> app-promocion         (6 casos)
   RF-07 Afiliaciones Por Promotores Especiales -> app-afiliacion-especial (6 casos)
   RF-08 Resumen De Afiliacion              -> app-resumen-afiliacion (6 casos)

6. RF-01 (la pantalla mas grande, "mantenedor principal") inspeccionada
   visualmente (_exploracion/dump/RF01_pantalla.png): filtro "Encargo
   de Cobranza" (combo) + "N. de Cliente" (con boton "..." - probable
   buscador generico de clientes, ver EF linea 130) + "Nombre" +
   "Documento" + boton "Leer". Grilla "Titulares" (Correlativo/Nombre/
   Estado) a la izquierda. Formulario con 2 tabs ("Datos del Titular"/
   "Beneficiarios") con muchos campos (N. Solicitud, Familia, Fecha de
   Nacimiento, Nombres, Apellidos, Documento Tipo/Nro, Domicilio, Plan,
   Responsable en caso de Desamparo, Nivel y Promocion, checkboxes
   Afiliacion por FAX/Habilitar Promocion). Botones: Ingresar/
   Modificar/Afiliar/Desafiliar/Cerrar + "Historial de Auditoria..."
   (abre pantalla secundaria, ver RN-21 del EF).

7. Manuales de usuario para RF-01 y RF-06 agregados por el usuario son
   PLACEHOLDERS VACIOS (solo titulo "pendiente de reemplazo", sin
   contenido real) - no aportan nada mas alla de confirmar los codigos
   de sistema legado AFILIA/AUDITAFI (RF-01) y PROMOAFI (RF-06). Usar
   el EF/ET + exploracion en vivo como fuente real.

8. OJO - la matriz trae precondiciones con INSERTs SQL reales para
   generar datos de prueba faltantes (ej. CP001 necesita un afiliado
   real en el encargo 0002, cliente 926226, corr_afiliado 1) - antes
   de escribir los casos de RF-01 en adelante, confirmar con el
   usuario si hace falta preparar datos via BD (ver
   reference_db_informix_dbeaver.md en memoria) o si ya existen datos
   reales utilizables, para no quedar bloqueados como paso en otros
   proyectos (PR000325-SP6 RF-01, PR000326-SP2 RF-01/RF-11).

9. Sin explorar todavia en este pase: estructura interna completa de
   cada pantalla (selectores de campo exactos por name, mensajes
   reales de validacion, combos y sus opciones reales, estructura de
   grillas) - Paso 2 completo pendiente POR PANTALLA antes de escribir
   el cuerpo real de cada CP, igual que en PR000349-SP6.
"""
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT_DIR.parent / "_framework"))
import web_lds_core as core  # noqa: E402

PROYECTO = "PR000349-SP7"
MATRIZ = json.loads((OUT_DIR / "matriz_casos.json").read_text(encoding="utf-8"))

ENV_TOGGLES = core.ENV_TOGGLES_CODE.replace("__PROYECTO__", PROYECTO)

HEADER_TEMPLATE = '''"""
{docstring_con_ficha_del_caso}
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

%%NAV%%

%%HELPERS_ESPERA%%

%%VIDEO_HELPERS%%

# --- Navegacion propia de este proyecto: Aplicaciones > Comercial > <pantalla>, directo ---
# CONFIRMADO EN VIVO 13/10/2026: 2 niveles de menu (sin categoria
# intermedia), entrar SIEMPRE por el portal.

def abrir_afiliaciones(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Auditoria De Afiliaciones"], "app-afilia", paso_excel=paso_excel)


def abrir_cliente_encargo(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Mantenimiento De Clientes De Encargos"], "app-cliente-encargo", paso_excel=paso_excel)


def abrir_proyectos(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Consulta De Proyectos De Encargos"], "app-proyecto", paso_excel=paso_excel)


def abrir_traslado(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Restaura Y Transfiere A Proceso"], "app-traslado", paso_excel=paso_excel)


def abrir_encargos_cobranza(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Encargos De Cobranza"], "app-lisafi", paso_excel=paso_excel)


def abrir_promocion(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Promocion De Afiliados"], "app-promocion", paso_excel=paso_excel)


def abrir_afiliacion_especial(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Afiliaciones Por Promotores Especiales"], "app-afiliacion-especial", paso_excel=paso_excel)


def abrir_resumen_afiliacion(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Resumen De Afiliacion"], "app-resumen-afiliacion", paso_excel=paso_excel)


# Las 8 pantallas confirmadas con DCABA_DW (ver docstring del modulo).

def filas_tabla(frame):
    """Las grillas de PR000349-SP7 NO usan ant-table (confirmado en
    vivo 14/10/2026, grilla Titulares de RF-01): cuando estan vacias
    muestran una fila placeholder propia `<tr><td class="empty">Sin
    titulares. Presione Leer.</td></tr>` (colspan completo, sin
    ninguna clase tipo ant-table-placeholder) - filtrarla por
    `td.empty` para que count() refleje filas de datos reales. Tambien
    se excluyen por compatibilidad los patrones ant-table de
    PR000349-SP6 (ant-table-measure-now/ant-table-placeholder) por si
    alguna otra pantalla de este proyecto SI los usa."""
    return frame.locator("tbody tr:not(.ant-table-measure-now):not(.ant-table-placeholder):not(:has(td.empty))")


def fila_por_codigo(frame, columna_idx, codigo):
    """Busca la fila cuya celda en `columna_idx` (separando por tabs
    en inner_text()) sea exactamente `codigo` (recorriendo en Python,
    no con has_text=regex: confirmado en vivo en PR000349-SP6 que el
    \\b de Playwright no matchea contra el texto real de las filas de
    estas tablas)."""
    filas = filas_tabla(frame)
    for i in range(filas.count()):
        columnas = filas.nth(i).inner_text().split("\\t")
        if len(columnas) > columna_idx and columnas[columna_idx].strip() == codigo:
            return filas.nth(i)
    raise AssertionError(f"No se encontro ninguna fila con columna[{{columna_idx}}] = {{codigo!r}}")


def buscar_fila_en_paginas(app, frame, columna_idx, valor, max_paginas=25):
    """Recorre las paginas de la grilla (boton 'Siguiente' de
    ant-design) buscando una fila cuya columna `columna_idx` (separada
    por tabs en inner_text()) sea exactamente `valor`. SIEMPRE reinicia
    a la pagina 1 antes de buscar (clickeando 'Anterior' repetidas
    veces). Devuelve el texto completo de la fila, o "" si no se
    encontro en `max_paginas` paginas."""
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
    falta. Devuelve True si la encontro y clickeo, False si no, SIN
    lanzar excepcion (el caller decide si eso es un error)."""
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
    Devuelve el texto del dialogo si aparecio, o None.

    OJO (gotcha de PR000349-SP6): este helper lee+cierra en la MISMA
    llamada - NO usar si el paso necesita EVIDENCIAR visualmente el
    mensaje (usar capturar_mensaje_dialogo en ese caso)."""
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
    MIENTRAS SIGUE ABIERTO - usar SIEMPRE que el paso deba evidenciar
    visualmente un mensaje de error/validacion (nunca
    confirmar_dialogo_si_aparece + capturar_paso por separado, que
    cierra el modal antes de la captura - bug real confirmado en
    PR000349-SP6, 22 casos afectados). Devuelve el texto del dialogo,
    o el texto de toda la pantalla si no aparecio ningun dialogo
    dentro de `timeout_ms`."""
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


def ir_al_tope(frame):
    """Forzar el scroll del iframe al tope absoluto antes de capturar
    un formulario - necesario cuando un paso previo clickeo una fila
    mas abajo en una grilla (deja el iframe scrolleado) y el paso
    actual necesita evidenciar el formulario completo, no solo la
    parte baja de la pantalla (bug real confirmado en PR000349-SP6,
    CP016/CP025/CP035/CP053/CP056 - scroll_into_view_if_needed() de un
    campo puntual NO alcanza si el scroll necesario es grande)."""
    frame.locator("body").evaluate("el => el.scrollTo(0, 0)")

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
                # garantizado completo - esperar antes del glob de abajo.
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
                # suelto se confirmo en vivo (PR000349-SP6) que puede ser
                # un artefacto EN BLANCO o un DUPLICADO de contenido ya
                # incluido - nunca footage realmente perdido, pero
                # verificar antes de asumir en vez de borrar a ciegas si
                # aparece reiteradamente.
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
# TODO: escribir los add("CPxxx", ...) de cada RF aca, uno por uno, DESPUES
# de explorar en vivo la pantalla correspondiente (Paso 2 del checklist) -
# no escribir a ciegas solo mirando la matriz. Ver PR000349-SP6/
# generate_scripts.py como referencia de la profundidad de exploracion
# esperada antes de escribir cada bloque de RF.
# ===========================================================================

# ===========================================================================
# RF-01: Auditoria de Afiliaciones (_exploracion/explore_0[3-4]*.py)
# ===========================================================================
# - Combo "Encargo de Cobranza" es un <select> NATIVO (id="selEncargo"),
#   NO ant-design - manejar con select_option(value=...). 4 opciones
#   reales: 0002=PLUZ PROTECCION, 0005=PLUZ SALUD, 0009=PLUZ EMERGENCIA,
#   0013=PLUZ SEPELIO.
# - Filtro superior sin name: inputs.nth(0)=N. de Cliente, nth(1)=Nombre
#   (calculado), nth(2)=Documento (calculado).
# - Grilla "Titulares" SI es ant-table (filas_tabla() funciona).
# - Dato de prueba confirmado en vivo 13/10/2026 (ver
#   Documentos/datos_prueba_RF01.sql, bloque 1.1): cliente 926226,
#   encargo 0002 tiene 2 titulares reales: corr_afiliado=1 "LUIS ERNESTO
#   DE OLAZAVAL TEJADA" (Desafiliado, dato real preexistente) y
#   corr_afiliado=2 (mismo cliente, estado Afiliado, agregado via SQL
#   para destrabar CP001/CP005/CP007/CP008/CP009).

add("CP001", "app, frame = abrir_afiliaciones(page, paso_excel=2)", '''
frame.locator("#selEncargo").select_option(value="0002")
app.wait_for_timeout(500)
inputs = frame.locator("input")
inputs.nth(0).fill("926226")
capturar_paso(app, "cliente_ingresado", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2500)
ir_al_tope(frame)
capturar_paso(app, "titulares_mostrados", paso_excel=4)
dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
assert dialogo.count() == 0 or not dialogo.first.is_visible(), f"No se esperaba ningun dialogo de rechazo para el cliente 926226 (elegible, sin restricciones): {dialogo.first.inner_text() if dialogo.count() else None!r}"
filas = filas_tabla(frame)
assert filas.count() >= 1, f"Se esperaba al menos 1 titular del cliente 926226 en la grilla, se vieron {filas.count()}"
texto_grilla = " | ".join(filas.nth(i).inner_text().replace("\\n", " ") for i in range(filas.count()))
assert "Afiliado" in texto_grilla, f"Se esperaba ver al menos un titular en estado Afiliado: {texto_grilla!r}"
''')

# Cliente real con tarifa BT6 confirmado en vivo 14/10/2026 (consulta
# directa a la BD, tabla cliente/columna tarifa): 22340 (otros
# candidatos: 1416825, 7153, 1279198, 7132). Mensaje real confirmado:
# "No se puede afiliar cliente con tipo de tarifa BT6." en una Ventana
# de Validacion normal (no Error de Servicio).
add("CP002", "app, frame = abrir_afiliaciones(page, paso_excel=2)", '''
frame.locator("#selEncargo").select_option(value="0002")
app.wait_for_timeout(500)
inputs = frame.locator("input")
inputs.nth(0).fill("22340")
capturar_paso(app, "cliente_bt6_ingresado", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2000)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_restriccion", paso_excel=4, timeout_ms=5000)
assert "bt6" in mensaje.lower(), f"Se esperaba el mensaje de restriccion por tarifa BT6: {mensaje!r}"
filas = filas_tabla(frame)
assert filas.count() == 0, f"El cliente con tarifa BT6 NO deberia cargar titulares, se vieron {filas.count()}"
''')

# Plan "PLAN FAMILIAR" de la matriz NO EXISTE: confirmado en vivo
# 14/10/2026 que el Encargo 0002 solo tiene 3 planes reales (A/B/C,
# sin descripcion) tanto en esta pantalla (API ObtenerPlanesPorEncargo:
# [{"codigoPlan":"A","monto":2.48},{"B",1.49},{"C",0.99}], sin campo de
# nombre) como en la pantalla analoga "Administracion De Planes De
# Encargo" de PR000349-SP6 (misma data real, columna Descripcion vacia
# para los 3). Se usa Plan "A". Nivel "General" para evitar necesitar
# un Promotor o Rol de Promotor Especial real (el combo Promotor no
# tiene opciones cargadas en el ambiente).
# Mensajes EXACTOS confirmados por el manual real (RF-01, seccion 3.4/
# 3.6): "Titular registrado correctamente." tras Grabar.
add("CP003", "app, frame = abrir_afiliaciones(page, paso_excel=2)", '''
frame.locator("#selEncargo").select_option(value="0002")
app.wait_for_timeout(500)
inputs = frame.locator("input")
inputs.nth(0).fill("926226")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2500)
frame.get_by_role("button", name=re.compile(r"^Ingresar$", re.I)).click()
app.wait_for_timeout(1000)
frame.locator('input[name="fechaNacimiento"]').fill("1990-05-20")
frame.locator('input[name="nombres"]').fill("JUAN CARLOS")
frame.locator('input[name="apellidos"]').fill("GARCIA PEREZ")
frame.locator("#selTipoDoc").select_option(value="005")
frame.locator('input[name="numeroDocumento"]').fill("08945612")
frame.locator('input[name="domicilio"]').fill("AV PRUEBA QA 123")
frame.locator("#selPlan").select_option(value="A")
frame.locator("#selNivel").select_option(value="GENERAL")
app.wait_for_timeout(500)
hoy = date.today().isoformat()
frame.locator('input[name="fechaAfiliacion"]').fill(hoy)
ir_al_tope(frame)
capturar_paso(app, "datos_completos", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Grabar", re.I)).click()
app.wait_for_timeout(2500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_registro", paso_excel=4, timeout_ms=5000)
assert "registrado correctamente" in mensaje.lower(), f"Se esperaba el mensaje de titular registrado: {mensaje!r}"
ir_al_tope(frame)
capturar_paso(app, "titular_en_grilla", paso_excel=4)
filas = filas_tabla(frame)
texto_grilla = " | ".join(filas.nth(i).inner_text().replace("\\n", " ") for i in range(filas.count()))
assert "GARCIA PEREZ" in texto_grilla, f"Se esperaba ver al nuevo titular JUAN CARLOS GARCIA PEREZ en la grilla: {texto_grilla!r}"
''')

# Cliente 926226 ya tiene 3 afiliaciones ACTIVAS reales (corr_afiliado
# 2/4/5 - el corr=3 original del bloque 1.2 quedo tomado por el alta
# real de CP003, asi que el bloque uso 4 y 5 en su lugar; igual suman 3
# activas) con el parametro PARSEG/MCLIAF=3 ya sembrado (ver
# Documentos/datos_prueba_RF01.sql bloques 1.2/1.3). Confirmado en vivo
# 14/10/2026 (ver _exploracion/dump/cp004_tras_ingresar.png): el rechazo
# ocurre DE INMEDIATO al presionar "Ingresar" (antes de habilitar el
# formulario) - no hace falta llenar ni Grabar nada, el limite es por
# CLIENTE (cuenta todas sus afiliaciones activas sin importar el
# documento), no por documento como se asumio originalmente. Mensaje
# real: "El cliente alcanzó el máximo de 3 afiliación(es) activas
# permitidas."
add("CP004", "app, frame = abrir_afiliaciones(page, paso_excel=2)", '''
frame.locator("#selEncargo").select_option(value="0002")
app.wait_for_timeout(500)
inputs = frame.locator("input")
inputs.nth(0).fill("926226")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2500)
filas_antes = filas_tabla(frame).count()
capturar_paso(app, "cliente_en_el_limite", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"^Ingresar$", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_limite", paso_excel=4, timeout_ms=5000)
assert "maximo" in mensaje.lower() or "m\\u00e1ximo" in mensaje.lower(), f"Se esperaba el mensaje de limite de afiliaciones alcanzado: {mensaje!r}"
assert "afiliaci" in mensaje.lower(), f"Se esperaba que el mensaje mencione 'afiliaciones': {mensaje!r}"
app.wait_for_timeout(500)
filas_despues = filas_tabla(frame).count()
assert filas_despues == filas_antes, f"No debio agregarse ningun titular nuevo: antes={filas_antes} despues={filas_despues}"
''')


# Titular corr_afiliado=2 (cliente 926226, encargo 0002, bloque 1.1 de
# datos_prueba_RF01.sql) - mismo usado en CP001/CP004. Domicilio
# original 'UNO', se cambia a 'AV. LOS ANGELES 452 DPTO 302' (dato de
# la matriz). fecha_nacimiento tuvo que completarse aparte (estaba en
# blanco incluso en el titular real original corr=1 - ver memoria del
# proyecto) porque Modificar la exige (RN no documentada en la matriz).
# Confirmado en vivo 14/10/2026: tras Grabar, el boton "Historial de
# Auditoria..." abre un MODAL dentro del mismo frame (no una ventana
# nueva) con columnas Cambio/Dato Anterior/Dato Modificado/Rol/Fecha -
# fila real vista: "Domicilio | UNO | AV. LOS ANGELES 452 DPTO 302 |
# DACD | 14/10/2026".
add("CP005", "app, frame = abrir_afiliaciones(page, paso_excel=2)", '''
frame.locator("#selEncargo").select_option(value="0002")
app.wait_for_timeout(500)
inputs = frame.locator("input")
inputs.nth(0).fill("926226")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2500)
fila_titular = fila_por_codigo(frame, 0, "2")
fila_titular.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"^Modificar$", re.I)).click()
app.wait_for_timeout(1000)
nuevo_domicilio = "AV. LOS ANGELES 452 DPTO 302"
frame.locator(\'input[name="domicilio"]\').fill(nuevo_domicilio)
ir_al_tope(frame)
capturar_paso(app, "domicilio_cambiado", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Grabar", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_modificado", paso_excel=4, timeout_ms=5000)
assert "modificado correctamente" in mensaje.lower(), f"Se esperaba confirmacion de modificacion: {mensaje!r}"
fila_titular = fila_por_codigo(frame, 0, "2")
fila_titular.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Historial de Auditor", re.I)).click()
app.wait_for_timeout(1500)
capturar_paso(app, "historial_auditoria", paso_excel=5)
texto_historial = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S)).first.inner_text()
assert "Domicilio" in texto_historial, f"El historial deberia registrar el cambio de Domicilio: {texto_historial!r}"
assert nuevo_domicilio in texto_historial, f"El historial deberia mostrar el nuevo domicilio: {texto_historial!r}"
boton_cerrar = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S)).first.get_by_role("button", name=re.compile(r"^Cerrar$", re.I))
if boton_cerrar.count():
    boton_cerrar.first.click()
app.wait_for_timeout(500)
''')


# Cliente 52124 (sin necesidad de SQL - confirmado en vivo 14/10/2026
# que ya tiene 2 titulares reales en estado Desafiliado). El rechazo
# ocurre de inmediato al presionar Modificar (igual patron que CP004
# con Ingresar), sin necesitar llenar ni Grabar nada.
add("CP006", "app, frame = abrir_afiliaciones(page, paso_excel=2)", '''
frame.locator("#selEncargo").select_option(value="0002")
app.wait_for_timeout(500)
inputs = frame.locator("input")
inputs.nth(0).fill("52124")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2500)
fila_titular = fila_por_codigo(frame, 0, "1")
fila_titular.click()
app.wait_for_timeout(500)
capturar_paso(app, "titular_desafiliado_seleccionado", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"^Modificar$", re.I)).click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_rechazo", paso_excel=4, timeout_ms=5000)
assert "no se puede modificar" in mensaje.lower(), f"Se esperaba el mensaje de rechazo por estado Desafiliado: {mensaje!r}"
assert "desafiliado" in mensaje.lower(), f"Se esperaba que el mensaje mencione el estado Desafiliado: {mensaje!r}"
campo_nombres = frame.locator(\'input[name="nombres"]\')
assert campo_nombres.get_attribute("disabled") is not None, "El formulario NO debio habilitarse para edicion tras el rechazo"
''')


# Reusa el titular Preafiliado REAL creado por CP003 (corr_afiliado=3,
# GARCIA PEREZ JUAN CARLOS, cliente 926226) en vez del INSERT de la
# matriz - la propia matriz admite que su INSERT no sirve para esto
# ("Pruebas no tiene filas en estado P, asi que el caso parte del
# titular activo del bloque 1.1" - su plantilla pone estado='A', no
# 'P'). DEPENDE de que CP003 se haya corrido antes (orden alfabetico
# normal de run_all.py) - si se corre CP007 aislado sin CP003 previo,
# fallara por no encontrar un Preafiliado.
add("CP007", "app, frame = abrir_afiliaciones(page, paso_excel=2)", '''
frame.locator("#selEncargo").select_option(value="0002")
app.wait_for_timeout(500)
inputs = frame.locator("input")
inputs.nth(0).fill("926226")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2500)
fila_titular = fila_por_codigo(frame, 0, "3")
fila_titular.click()
app.wait_for_timeout(500)
capturar_paso(app, "titular_preafiliado_seleccionado", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"^Afiliar$", re.I)).click()
app.wait_for_timeout(1000)
mensaje_confirmacion = capturar_mensaje_dialogo(app, frame, "confirmacion_afiliar", paso_excel=4, timeout_ms=5000)
assert "seguro" in mensaje_confirmacion.lower() and "afiliar" in mensaje_confirmacion.lower(), f"Se esperaba la confirmacion de afiliar: {mensaje_confirmacion!r}"
app.wait_for_timeout(1000)
mensaje_exito = capturar_mensaje_dialogo(app, frame, "mensaje_afiliado", paso_excel=5, timeout_ms=5000)
assert "afiliado correctamente" in mensaje_exito.lower(), f"Se esperaba confirmacion de afiliacion exitosa: {mensaje_exito!r}"
app.wait_for_timeout(500)
fila_actualizada = fila_por_codigo(frame, 0, "3")
assert "Afiliado" in fila_actualizada.inner_text(), f"El titular deberia quedar en estado Afiliado: {fila_actualizada.inner_text()!r}"
''')


# Cliente 1291599, titular corr_afiliado=2 clonado por SQL (ver
# Documentos/datos_prueba_RF01.sql bloque 1.3-B - el INSERT original de
# la matriz apuntaba por error a 926226, no a este cliente) + agenda
# sector 1/zona 140 en estado 'X' (bloque 1.4). El rechazo ocurre tras
# la confirmacion "Si" (2 dialogos en secuencia, igual patron que
# CP007 pero terminando en rechazo en vez de exito).
add("CP008", "app, frame = abrir_afiliaciones(page, paso_excel=2)", '''
frame.locator("#selEncargo").select_option(value="0002")
app.wait_for_timeout(500)
inputs = frame.locator("input")
inputs.nth(0).fill("1291599")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2500)
fila_titular = fila_por_codigo(frame, 0, "2")
fila_titular.click()
app.wait_for_timeout(500)
capturar_paso(app, "titular_afiliado_en_facturacion", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"^Desafiliar$", re.I)).click()
app.wait_for_timeout(1000)
mensaje_confirmacion = capturar_mensaje_dialogo(app, frame, "confirmacion_desafiliar", paso_excel=4, timeout_ms=5000)
assert "seguro" in mensaje_confirmacion.lower() and "desafiliar" in mensaje_confirmacion.lower(), f"Se esperaba la confirmacion de desafiliar: {mensaje_confirmacion!r}"
app.wait_for_timeout(1000)
mensaje_rechazo = capturar_mensaje_dialogo(app, frame, "mensaje_rechazo_facturacion", paso_excel=5, timeout_ms=5000)
assert "facturaci" in mensaje_rechazo.lower(), f"Se esperaba el mensaje de rechazo por facturacion: {mensaje_rechazo!r}"
app.wait_for_timeout(500)
fila_final = fila_por_codigo(frame, 0, "2")
assert "Afiliado" in fila_final.inner_text() and "Desafiliado" not in fila_final.inner_text(), f"El titular NO debio desafiliarse: {fila_final.inner_text()!r}"
''')


# Titular corr_afiliado=2 (cliente 926226, mismo reusado en
# CP001/CP004/CP005). Confirmado en vivo 14/10/2026: el limite de
# beneficiarios esta FIJO en 5 en el codigo actual, NO conectado al
# catalogo PARSEG/MBENAF que documenta el ET (se probo sembrar
# MBENAF=2 y no tuvo ningun efecto - hallazgo real, ver memoria del
# proyecto). "Agregar Beneficiario" graba de inmediato en el servidor
# (no es un borrador local que recien se persiste con Grabar) - por
# eso el caso agrega y LUEGO borra los 5 beneficiarios de prueba, para
# no dejar basura en el titular que reusan otros casos de RF-01.
add("CP009", "app, frame = abrir_afiliaciones(page, paso_excel=2)", '''
frame.locator("#selEncargo").select_option(value="0002")
app.wait_for_timeout(500)
inputs = frame.locator("input")
inputs.nth(0).fill("926226")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2500)
fila_titular = fila_por_codigo(frame, 0, "2")
fila_titular.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"^Modificar$", re.I)).click()
app.wait_for_timeout(1000)
frame.get_by_text("Beneficiarios", exact=True).click()
app.wait_for_timeout(800)

boton_agregar = frame.locator("button", has_text="Agregar Beneficiario")
dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
beneficiarios_prueba = [
    ("ANA", "LIMITE BENEF UNO", "2010-01-15", "20"),
    ("LUIS", "LIMITE BENEF DOS", "2011-02-20", "20"),
    ("CARLOS", "LIMITE BENEF TRES", "2012-03-25", "20"),
    ("MARIA", "LIMITE BENEF CUATRO", "2013-04-30", "20"),
    ("JOSE", "LIMITE BENEF CINCO", "2014-05-10", "20"),
]
for nombres, apellidos, fecha_nac, porcentaje in beneficiarios_prueba:
    frame.locator(\'input[name="benNombres"]\').fill(nombres)
    frame.locator(\'input[name="benApellidos"]\').fill(apellidos)
    frame.locator("#selBenParentesco").select_option(value="02")
    frame.locator(\'input[name="benFechaNacimiento"]\').fill(fecha_nac)
    frame.locator(\'input[name="benPorcentaje"]\').fill(porcentaje)
    boton_agregar.first.click()
    app.wait_for_timeout(1200)
    assert not dialogo.count(), f"No se esperaba rechazo agregando el beneficiario {nombres!r} (debajo del limite): {dialogo.first.inner_text() if dialogo.count() else \'\'}"

capturar_paso(app, "limite_de_beneficiarios_alcanzado", paso_excel=3)
frame.locator(\'input[name="benNombres"]\').fill("PEDRO")
frame.locator(\'input[name="benApellidos"]\').fill("LIMITE BENEF SEIS")
frame.locator("#selBenParentesco").select_option(value="02")
frame.locator(\'input[name="benFechaNacimiento"]\').fill("2015-06-15")
frame.locator(\'input[name="benPorcentaje"]\').fill("20")
boton_agregar.first.click()
app.wait_for_timeout(1500)
mensaje = capturar_mensaje_dialogo(app, frame, "mensaje_limite_beneficiarios", paso_excel=4, timeout_ms=5000)
assert "maximo" in mensaje.lower() or "m\\u00e1ximo" in mensaje.lower(), f"Se esperaba el mensaje de limite de beneficiarios alcanzado: {mensaje!r}"
assert "beneficiari" in mensaje.lower(), f"Se esperaba que el mensaje mencione \'beneficiarios\': {mensaje!r}"

# Limpieza: borrar los 5 beneficiarios de prueba para no dejar basura
# en el titular que reusan CP001/CP004/CP005. Tolerante a la animacion
# ant-spin que aparece brevemente tras cada Borrar (confirmado en vivo:
# puede interceptar un click aunque el borrado anterior ya haya
# terminado del lado servidor) - cada intento va envuelto en try/except
# para no abortar el caso completo por una carrera cosmetica.
boton_borrar = frame.locator("button", has_text="Borrar Beneficiario")
for _ in range(10):
    filas_benef = frame.locator("tbody tr").filter(has_text=re.compile(r"LIMITE BENEF"))
    if filas_benef.count() == 0:
        break
    try:
        filas_benef.first.click(timeout=8000)
        app.wait_for_timeout(500)
        boton_borrar.first.click(timeout=8000)
        app.wait_for_timeout(1200)
        for _reintento in range(2):
            if dialogo.count():
                boton_ok = dialogo.first.get_by_role("button", name=re.compile(r"Aceptar", re.I))
                if boton_ok.count():
                    boton_ok.first.click(timeout=5000)
                    app.wait_for_timeout(1200)
    except PWTimeoutError:
        app.wait_for_timeout(1000)
app.wait_for_timeout(500)
filas_restantes = frame.locator("tbody tr").filter(has_text=re.compile(r"LIMITE BENEF"))
assert filas_restantes.count() == 0, f"Quedaron beneficiarios de prueba sin limpiar: {filas_restantes.count()}"
''')



# ============================================================================
# RF-02 Mantenimiento de Clientes de Encargos (app-cliente-encargo).
# A diferencia de RF-01, esta pantalla SI usa ant-design (.ant-select-
# selector) para los combos Encargo y Descripcion del Proyecto.
# Inputs reales confirmados por name: numeroCliente, numeroCuotas,
# valorCuota. Nombre del Cliente y Codigo de Proyecto son readonly SIN
# name (posicion fija en el DOM, documentado en cada caso). Estado se
# lee de span.estado-tag.
# ============================================================================

# Cliente 4016918 YA tiene relacion vigente real en el encargo 0001
# (proyecto 930591, 19 cuotas) - sin necesitar SQL.
add("CP010", "app, frame = abrir_cliente_encargo(page, paso_excel=2)", '''
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(500)
frame.locator("nz-option-item, [role=\\'option\\']").filter(has_text="0001").first.click()
app.wait_for_timeout(500)
frame.locator(\'input[name="numeroCliente"]\').fill("4016918")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2000)
ir_al_tope(frame)
capturar_paso(app, "relacion_vigente", paso_excel=3)
estado = frame.locator("span.estado-tag").inner_text().strip()
assert estado == "Vigente", f"Se esperaba estado Vigente: {estado!r}"
cuotas = frame.locator("#numeroCuotas input").input_value()
assert cuotas.strip() != "", f"Se esperaba un N. de Cuotas visible: {cuotas!r}"
''')


# Cliente 1200017 CONFIRMADO en vivo 14/10/2026 sin relacion previa
# (boton "Ingresar" en vez de "Modificar" tras Leer). Este mismo
# cliente queda como fixture real Vigente para que CP015 lo revoque
# despues - no se usa SQL en ningun momento. OJO: en esta pantalla
# "Ingresar" ES el boton de submit (no un mero cambio de modo como en
# RF-01) - los campos ya estan editables apenas carga un cliente
# nuevo, sin necesitar un primer clic en Ingresar para "entrar en modo
# edicion".
add("CP011", "app, frame = abrir_cliente_encargo(page, paso_excel=2)", '''
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(500)
frame.locator("nz-option-item, [role=\\'option\\']").filter(has_text="0001").first.click()
app.wait_for_timeout(500)
frame.locator(\'input[name="numeroCliente"]\').fill("1200017")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2000)
frame.locator(".ant-select-selector").nth(1).click()
app.wait_for_timeout(500)
frame.locator(".cdk-overlay-container .ant-select-item-option").filter(has_text="880390").first.click()
app.wait_for_timeout(500)
frame.locator("#numeroCuotas input").fill("12")
frame.locator("#valorCuota input").fill("45.50")
capturar_paso(app, "datos_completos", paso_excel=3)
frame.locator("button", has_text="Ingresar").click()
app.wait_for_timeout(1200)
mensaje_confirmacion = capturar_mensaje_dialogo(app, frame, "confirmacion_registro", paso_excel=4, timeout_ms=5000)
assert "registrar" in mensaje_confirmacion.lower(), f"Se esperaba la confirmacion de registro: {mensaje_confirmacion!r}"
# Confirmado en vivo 14/10/2026: esta pantalla NO muestra un segundo
# dialogo de "exito" tras confirmar (a diferencia de RF-01) - la unica
# evidencia de que el registro funciono es que la grilla/Estado pasa
# directo a "Vigente" y los botones cambian a Modificar/Revocar.
app.wait_for_timeout(1500)
capturar_paso(app, "relacion_registrada", paso_excel=5)
estado = frame.locator("span.estado-tag").inner_text().strip()
assert estado == "Vigente", f"La relacion deberia quedar Vigente: {estado!r}"
''')


# Cliente 1200001, encargo 0001, relacion vigente real con proyecto
# 880390 (ver Documentos/datos_prueba_RF01.sql - bloque de RF-02,
# INSERT manual en encarg_cli). A diferencia del Plan de RF-01, aqui
# el combo Descripcion del Proyecto SI muestra su descripcion real
# (sin hueco de datos) y queda editable sin necesitar un primer clic
# en Modificar.
add("CP012", "app, frame = abrir_cliente_encargo(page, paso_excel=2)", '''
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(500)
frame.locator("nz-option-item, [role=\\'option\\']").filter(has_text="0001").first.click()
app.wait_for_timeout(500)
frame.locator(\'input[name="numeroCliente"]\').fill("1200001")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2000)
frame.locator(".ant-select-selector").nth(1).click()
app.wait_for_timeout(500)
frame.locator(".cdk-overlay-container .ant-select-item-option").filter(has_text="930612").first.click()
app.wait_for_timeout(500)
capturar_paso(app, "proyecto_distinto_seleccionado", paso_excel=3)
frame.locator("button", has_text="Modificar").click()
app.wait_for_timeout(1200)
mensaje_confirmacion = capturar_mensaje_dialogo(app, frame, "confirmacion_modificar", paso_excel=4, timeout_ms=5000)
assert "modificar" in mensaje_confirmacion.lower(), f"Se esperaba la confirmacion de modificar: {mensaje_confirmacion!r}"
app.wait_for_timeout(1000)
mensaje_rechazo = capturar_mensaje_dialogo(app, frame, "mensaje_rechazo_proyecto", paso_excel=5, timeout_ms=5000)
assert "otro proyecto" in mensaje_rechazo.lower(), f"Se esperaba el rechazo por proyecto duplicado: {mensaje_rechazo!r}"
app.wait_for_timeout(1000)
# El combo queda mostrando localmente la seleccion del usuario (930612)
# aunque el backend haya rechazado el cambio - hay que Cerrar y volver
# a Leer desde cero para confirmar el estado REAL guardado en el
# servidor, no confiar en lo que la UI muestra tras el rechazo.
frame.locator("button", has_text="Cerrar").click()
app.wait_for_timeout(1000)
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(500)
frame.locator("nz-option-item, [role=\\'option\\']").filter(has_text="0001").first.click()
app.wait_for_timeout(500)
frame.locator(\'input[name="numeroCliente"]\').fill("1200001")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2000)
capturar_paso(app, "proyecto_original_conservado", paso_excel=6)
combo_proyecto_final = frame.locator(".ant-select-selector").nth(1).inner_text()
assert "880390" in combo_proyecto_final, f"El proyecto original debia conservarse (880390): {combo_proyecto_final!r}"
''')


# Mismo cliente 1200001 de CP012 (sigue Vigente, proyecto 880390 -
# CP012 no le cambio nada realmente). Confirmado en vivo: tampoco hay
# un segundo dialogo de exito tras Modificar (igual que CP011/CP012) -
# se verifica recargando con Cerrar+Leer, no confiando en los valores
# que la UI muestra justo despues de confirmar.
add("CP013", "app, frame = abrir_cliente_encargo(page, paso_excel=2)", '''
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(500)
frame.locator("nz-option-item, [role=\\'option\\']").filter(has_text="0001").first.click()
app.wait_for_timeout(500)
frame.locator(\'input[name="numeroCliente"]\').fill("1200001")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2000)
frame.locator("#numeroCuotas input").fill("10")
frame.locator("#valorCuota input").fill("50.00")
capturar_paso(app, "cuotas_modificadas", paso_excel=3)
frame.locator("button", has_text="Modificar").click()
app.wait_for_timeout(1200)
mensaje_confirmacion = capturar_mensaje_dialogo(app, frame, "confirmacion_modificar", paso_excel=4, timeout_ms=5000)
assert "modificar" in mensaje_confirmacion.lower(), f"Se esperaba la confirmacion de modificar: {mensaje_confirmacion!r}"
app.wait_for_timeout(1500)
frame.locator("button", has_text="Cerrar").click()
app.wait_for_timeout(1000)
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(500)
frame.locator("nz-option-item, [role=\\'option\\']").filter(has_text="0001").first.click()
app.wait_for_timeout(500)
frame.locator(\'input[name="numeroCliente"]\').fill("1200001")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2000)
capturar_paso(app, "cuotas_confirmadas", paso_excel=5)
cuotas_final = frame.locator("#numeroCuotas input").input_value()
valor_final = frame.locator("#valorCuota input").input_value()
assert cuotas_final.strip() == "10", f"Se esperaba N. de Cuotas = 10: {cuotas_final!r}"
assert "50" in valor_final, f"Se esperaba Valor de Cuota = 50.00: {valor_final!r}"
''')


# Mismo cliente 1200001 (sigue Vigente tras CP013). Por su propio
# precond, CP014 REVOCA la relacion el mismo (no depende de que otro
# caso lo haya hecho antes) y luego confirma que Modificar queda
# bloqueado - 100% autonomo. estado='C' es "Revocado" en la BD real
# (confirmado en vivo), no 'R'.
add("CP014", "app, frame = abrir_cliente_encargo(page, paso_excel=2)", '''
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(500)
frame.locator("nz-option-item, [role=\\'option\\']").filter(has_text="0001").first.click()
app.wait_for_timeout(500)
frame.locator(\'input[name="numeroCliente"]\').fill("1200001")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2000)
estado_antes = frame.locator("span.estado-tag").inner_text().strip()
assert estado_antes == "Vigente", f"Se esperaba partir de una relacion Vigente: {estado_antes!r}"
capturar_paso(app, "relacion_vigente_antes_de_revocar", paso_excel=3)
frame.locator("button", has_text="Revocar").click()
app.wait_for_timeout(1200)
mensaje_confirmacion = capturar_mensaje_dialogo(app, frame, "confirmacion_revocar", paso_excel=4, timeout_ms=5000)
assert "revocada" in mensaje_confirmacion.lower(), f"Se esperaba la confirmacion de revocar: {mensaje_confirmacion!r}"
app.wait_for_timeout(1500)
frame.locator("button", has_text="Cerrar").click()
app.wait_for_timeout(1000)
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(500)
frame.locator("nz-option-item, [role=\\'option\\']").filter(has_text="0001").first.click()
app.wait_for_timeout(500)
frame.locator(\'input[name="numeroCliente"]\').fill("1200001")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2000)
estado_despues = frame.locator("span.estado-tag").inner_text().strip()
assert estado_despues == "Revocado", f"La relacion deberia quedar Revocado: {estado_despues!r}"
capturar_paso(app, "modificar_bloqueado", paso_excel=5)
boton_modificar = frame.locator("button", has_text="Modificar")
assert not boton_modificar.is_enabled(), "El boton Modificar NO debio quedar habilitado sobre una relacion Revocado"
''')


# Revoca el cliente 1200017 que CP011 dejo Vigente (NO el cliente real
# 4016918 de CP010, para no tocar produccion real). Mismo patron de
# Cerrar+Leer para confirmar el estado real tras revocar.
add("CP015", "app, frame = abrir_cliente_encargo(page, paso_excel=2)", '''
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(500)
frame.locator("nz-option-item, [role=\\'option\\']").filter(has_text="0001").first.click()
app.wait_for_timeout(500)
frame.locator(\'input[name="numeroCliente"]\').fill("1200017")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2000)
estado_antes = frame.locator("span.estado-tag").inner_text().strip()
assert estado_antes == "Vigente", f"Se esperaba partir de una relacion Vigente: {estado_antes!r}"
capturar_paso(app, "relacion_vigente_antes_de_revocar", paso_excel=3)
frame.locator("button", has_text="Revocar").click()
app.wait_for_timeout(1200)
mensaje_confirmacion = capturar_mensaje_dialogo(app, frame, "confirmacion_revocar", paso_excel=4, timeout_ms=5000)
assert "revocada" in mensaje_confirmacion.lower(), f"Se esperaba la confirmacion de revocar: {mensaje_confirmacion!r}"
app.wait_for_timeout(1500)
frame.locator("button", has_text="Cerrar").click()
app.wait_for_timeout(1000)
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(500)
frame.locator("nz-option-item, [role=\\'option\\']").filter(has_text="0001").first.click()
app.wait_for_timeout(500)
frame.locator(\'input[name="numeroCliente"]\').fill("1200017")
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2000)
capturar_paso(app, "relacion_revocada", paso_excel=5)
estado_despues = frame.locator("span.estado-tag").inner_text().strip()
assert estado_despues == "Revocado", f"La relacion deberia quedar Revocado: {estado_despues!r}"
''')


# ============================================================================
# RF-03 Consulta de Proyectos de Encargos (app-proyecto). Tambien
# ant-design. Encargo y Descripcion de Proyecto son combos
# .ant-select-selector (indices 0 y 1) - el combo Proyecto carga sus
# opciones via API tras elegir el Encargo, puede tardar >1s, esperar
# el primer .ant-select-item-option visible antes de buscar por texto.
# Tras un Leer exitoso el boton cambia de "Leer" a "Sgtes" (paginacion
# real, NO hacen falta los 30 clientes descartables del bloque 3.2 -
# el proyecto 930612 YA supera una pagina con datos reales).
# ============================================================================

# 4 clientes descartables (9900018-21) sembrados en el proyecto 930612
# del encargo 0001 (ver Documentos, bloque 3.1) - confirmados en vivo
# en la grilla real junto a ~26 clientes reales preexistentes.
add("CP016", "app, frame = abrir_proyectos(page, paso_excel=2)", '''
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(800)
frame.locator(".cdk-overlay-container .ant-select-item-option").filter(has_text="0001").first.click()
app.wait_for_timeout(2000)
frame.locator(".ant-select-selector").nth(1).click()
opciones = frame.locator(".cdk-overlay-container .ant-select-item-option")
opciones.first.wait_for(state="visible", timeout=10000)
app.wait_for_timeout(500)
opciones.filter(has_text="930612").first.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2500)
ir_al_tope(frame)
capturar_paso(app, "primera_pagina_clientes", paso_excel=3)
filas = filas_tabla(frame)
assert filas.count() > 0, "Se esperaba al menos 1 cliente en la primera pagina del proyecto"
texto_grilla = frame.locator("tbody").inner_text()
for cliente_descartable in ["9900018", "9900019", "9900020", "9900021"]:
    assert cliente_descartable in texto_grilla, f"Se esperaba ver el cliente {cliente_descartable} en la grilla"
''')


# Confirmado en vivo: con solo los 4 clientes del bloque 3.1, la
# pagina 2 salia VACIA (el proyecto 930612 no superaba una pagina por
# si solo, contra lo que se asumio al escribir CP016) - hizo falta
# sembrar tambien el bloque 3.2 (30 clientes descartables 9900101-130)
# para que CP017 tenga algo real que paginar.
add("CP017", "app, frame = abrir_proyectos(page, paso_excel=2)", '''
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(800)
frame.locator(".cdk-overlay-container .ant-select-item-option").filter(has_text="0001").first.click()
app.wait_for_timeout(2000)
frame.locator(".ant-select-selector").nth(1).click()
opciones = frame.locator(".cdk-overlay-container .ant-select-item-option")
opciones.first.wait_for(state="visible", timeout=10000)
app.wait_for_timeout(500)
opciones.filter(has_text="930612").first.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2500)
filas1 = filas_tabla(frame)
clientes_pagina1 = set()
for i in range(filas1.count()):
    cols = filas1.nth(i).inner_text().split("\\t")
    if len(cols) > 1 and cols[1].strip():
        clientes_pagina1.add(cols[1].strip())
assert len(clientes_pagina1) > 0, "Se esperaba al menos 1 cliente en la primera pagina"
ir_al_tope(frame)
capturar_paso(app, "primera_pagina", paso_excel=3)
frame.locator("button", has_text="Sgtes").click()
app.wait_for_timeout(2500)
ir_al_tope(frame)
capturar_paso(app, "segunda_pagina", paso_excel=4)
filas2 = filas_tabla(frame)
clientes_pagina2 = set()
for i in range(filas2.count()):
    cols = filas2.nth(i).inner_text().split("\\t")
    if len(cols) > 1 and cols[1].strip():
        clientes_pagina2.add(cols[1].strip())
assert len(clientes_pagina2) > 0, "Se esperaba al menos 1 cliente en la segunda pagina"
interseccion = clientes_pagina1 & clientes_pagina2
assert not interseccion, f"La pagina 2 NO debio repetir clientes de la pagina 1: {interseccion}"
''')


# Cliente 9900018 (bloque 3.1, mismo del proyecto 930612). Campos de
# Datos de Cuota confirmados por id real: #in-numero-cuotas,
# #in-valor-cuota (nz-input-number, apuntar al "input" interno).
add("CP018", "app, frame = abrir_proyectos(page, paso_excel=2)", '''
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(800)
frame.locator(".cdk-overlay-container .ant-select-item-option").filter(has_text="0001").first.click()
app.wait_for_timeout(2000)
frame.locator(".ant-select-selector").nth(1).click()
opciones = frame.locator(".cdk-overlay-container .ant-select-item-option")
opciones.first.wait_for(state="visible", timeout=10000)
app.wait_for_timeout(500)
opciones.filter(has_text="930612").first.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2500)
fila_cliente = fila_por_codigo(frame, 1, "9900018")
fila_cliente.click()
app.wait_for_timeout(800)
frame.locator("#in-numero-cuotas input").fill("10")
frame.locator("#in-valor-cuota input").fill("40.00")
capturar_paso(app, "cuotas_modificadas", paso_excel=3)
frame.locator("button", has_text="Modificar").click()
app.wait_for_timeout(1200)
mensaje_confirmacion = capturar_mensaje_dialogo(app, frame, "confirmacion_modificar", paso_excel=4, timeout_ms=5000)
assert "cuota" in mensaje_confirmacion.lower() or "modificar" in mensaje_confirmacion.lower(), f"Se esperaba la confirmacion de modificar cuotas: {mensaje_confirmacion!r}"
app.wait_for_timeout(1500)
# El boton "Leer" se vuelve "Sgtes" tras la 1ra consulta (igual que en
# CP016/CP017) - hay que Cerrar y rearmar Encargo+Proyecto+Leer para
# confirmar el estado real, no solo re-clickear "Leer".
frame.locator("button", has_text="Cerrar").click()
app.wait_for_timeout(1000)
frame.locator(".ant-select-selector").first.click()
app.wait_for_timeout(800)
frame.locator(".cdk-overlay-container .ant-select-item-option").filter(has_text="0001").first.click()
app.wait_for_timeout(2000)
frame.locator(".ant-select-selector").nth(1).click()
opciones2 = frame.locator(".cdk-overlay-container .ant-select-item-option")
opciones2.first.wait_for(state="visible", timeout=10000)
app.wait_for_timeout(500)
opciones2.filter(has_text="930612").first.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Leer", re.I)).click()
app.wait_for_timeout(2500)
capturar_paso(app, "cuotas_confirmadas", paso_excel=5)
fila_final = fila_por_codigo(frame, 1, "9900018")
fila_final.click()
app.wait_for_timeout(800)
cuotas_final = frame.locator("#in-numero-cuotas input").input_value()
valor_final = frame.locator("#in-valor-cuota input").input_value()
assert cuotas_final.strip() == "10", f"Se esperaba N. de Cuotas = 10: {cuotas_final!r}"
assert "40" in valor_final, f"Se esperaba Valor de Cuota = 40.00: {valor_final!r}"
''')


def render_all():
    if not CASES:
        raise SystemExit(
            "CASES esta vacio todavia - agregar add(\"CPxxx\", ...) por cada "
            "caso antes de correr esto (ver TODO arriba)."
        )
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")


if __name__ == "__main__":
    render_all()
