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
    """nz-table de ant-design siempre trae una fila oculta extra
    tr.ant-table-measure-now de uso interno - filtrarla siempre (ver
    NUEVO_PROYECTO_CHECKLIST.md, gotchas PR000349-SP1/SP6). Cuando la
    grilla esta vacia, ant-design agrega ademas una fila placeholder
    real (tr.ant-table-placeholder, texto "No hay datos") que NO es un
    registro - filtrarla tambien para que count() refleje filas de
    datos reales."""
    return frame.locator("tbody tr:not(.ant-table-measure-now):not(.ant-table-placeholder)")


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
