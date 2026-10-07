"""
generate_scripts.py de PR000325-SP5 - FUENTE DE VERDAD que genera los CPxxx.py.

Proyecto: migracion del modulo de Facturacion, 5 pantallas (RF-01..RF-05),
45 casos (ver matriz_casos.json). Ver documentos/EF_texto.txt y
documentos/ET_texto.txt para el detalle funcional/tecnico completo.

Roles funcionales necesarios por RF (confirmados en la precondicion de
cada CP de la matriz, no en el ET que trae una lista mas amplia):
RF-01 JEFEOPCO (CP001-007) / ANDESE1 (CP042-043)
RF-02 JEFESUCU (CP008-015) / ANDESE1 (CP044)
RF-03 SUPEFACT (CP016-023) / MANSEC (CP024-026)
RF-04 JEFESUCU (CP027-036) / ANDESE1 (CP045)
RF-05 ANDESE1 (CP037-041)
Ninguna cuenta de prueba conocida (SCASTI_DW/DCABA_DW) tiene JEFEOPCO,
JEFESUCU, SUPEFACT ni MANSEC confirmado. DCABA_DW SI tiene ANDESE1, pero
aun asi RF-02 (CP008) fallo con un error real de CORS al abrir la
pantalla (ver casos_fallidos_confirmados.json) - probable configuracion
de backend pendiente para este modulo recien migrado.
"""
import inspect
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
FRAMEWORK_DIR = OUT_DIR.parent / "_framework"
sys.path.insert(0, str(FRAMEWORK_DIR))
sys.path.insert(0, str(FRAMEWORK_DIR / "modulos"))
import web_lds_core as core  # noqa: E402

PROYECTO = "PR000325-SP5"  # debe coincidir con el nombre de esta carpeta
MATRIZ = json.loads((OUT_DIR / "matriz_casos.json").read_text(encoding="utf-8"))

ENV_TOGGLES = core.ENV_TOGGLES_CODE.replace("__PROYECTO__", PROYECTO)


def fuente_modulo(modulo, saltar=("PWTimeoutError",)):
    """Extrae el codigo fuente de un modulo de _framework/modulos/ (su
    docstring + todas sus funciones) para volcarlo como texto en el
    CPxxx.py generado. Ver patron ya usado en PR000349-SP1/SP2."""
    codigo_completo = inspect.getsource(modulo)
    lineas = codigo_completo.split("\n")
    dentro_docstring = False
    doc_lineas = []
    i = 0
    if lineas[0].strip().startswith('"""'):
        dentro_docstring = True
        doc_lineas.append(lineas[0].strip().lstrip('"'))
        i = 1
    while dentro_docstring and i < len(lineas):
        if lineas[i].strip().endswith('"""'):
            doc_lineas.append(lineas[i].rstrip().rstrip('"'))
            dentro_docstring = False
            i += 1
            break
        doc_lineas.append(lineas[i])
        i += 1
    resto = lineas[i:]
    salida = [l for l in resto if not (l.startswith("import ") or l.startswith("from "))]
    ficha_tecnica = "\n".join(f"# {l}" if l.strip() else "#" for l in doc_lineas)
    fuente = ficha_tecnica + "\n\n\n" + "\n".join(salida).strip("\n")
    return fuente.replace("{", "{{").replace("}", "}}")


HELPERS_MODULOS = ""  # se van agregando modulos de _framework/modulos/ a medida que se confirmen pantallas en vivo

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
USUARIO = {usuario_repr}
PASSWORD = {password_repr}

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

''' + HELPERS_MODULOS + '''


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


def _indentar(texto: str, espacios: int = 12) -> str:
    prefijo = " " * espacios
    return "\n".join((prefijo + linea if linea.strip() else "") for linea in texto.strip("\n").splitlines())


def render(caso: dict) -> str:
    docstring = (
        f"{caso['cp']} - {caso['name']}\n\n"
        f"RF: {caso['rf']}  |  CU: {caso['cu']}\n"
        f"Descripcion: {caso['desc']}\n"
        f"Precondiciones: {caso['precond']}\n"
        f"Datos: {caso['datos']}\n"
        f"Resultado esperado: {caso['esperado']}\n\n"
        f"Pasos a seguir:\n{caso['pasos']}"
    )
    body = _indentar(caso["body"])
    return HEADER_TEMPLATE.format(
        docstring=docstring.replace('"""', "'''"),
        cp=caso["cp"], name_repr=repr(caso["name"]), rf_repr=repr(caso["rf"]),
        cu_repr=repr(caso["cu"]), desc_repr=repr(caso["desc"]),
        esperado_repr=repr(caso["esperado"]), pasos_repr=repr(caso["pasos"]),
        usuario_repr=repr(caso["usuario"]), password_repr=repr(caso["password"]),
        body=body,
    ).replace("%%CAPTURAR_PASO%%", core.CAPTURAR_PASO_CODE) \
     .replace("%%LOGIN%%", core.LOGIN_BLOCK) \
     .replace("%%NAV%%", core.CLICK_VISIBLE_BLOCK + "\n\n\n" + core.ABRIR_APLICACION_BLOCK) \
     .replace("%%HELPERS_ESPERA%%", core.ESPERAR_FIN_CARGA_BLOCK + "\n\n\n" + core.ESPERAR_ANIMACION_BLOCK + "\n\n\n" + core.SELECCIONAR_PRIMERA_OPCION_BLOCK + "\n\n\n" + core.SELECCIONAR_OPCION_POR_TEXTO_BLOCK) \
     .replace("%%VIDEO_HELPERS%%", core.RENOMBRAR_VIDEO_BLOCK) \
     .replace("%%CURSOR_OVERLAY_JS%%", repr(core.CURSOR_JS_FULL.strip("\n"))) \
     .replace("%%WORD_HELPERS%%", core.WORD_HELPERS_FULL.strip("\n"))


CASES = []


def add(cp, body, usuario="SCASTI_DW", password="Soporte2025$5"):
    m = MATRIZ[cp]
    CASES.append(dict(
        cp=cp, rf=m["rf"], cu=m["cu"], name=m["name"], desc=m["desc"],
        precond=m["precond"], datos=m["datos"], esperado=m["esperado"],
        pasos=m["pasos"], body=body, usuario=usuario, password=password,
    ))


def _body_pendiente(cp, rf, name):
    mensaje = f"{cp} ({rf} - {name}): falta escribir el body real - falta exploracion en vivo."
    return f"raise NotImplementedError({mensaje!r})"


CUERPOS_REALES = {}

# RF-02 "Mantenedor de Estados de Comprobantes de Pago" (CP008-015, CP044)
# - BLOQUEADO completo 01/10/2026: la pantalla no abre, error CORS real
# confirmado en consola al llamar LanzarAplicativoDebug (ver
# _exploracion/explore_04_rf02_detalle.py). Modulo recien migrado -
# probable configuracion de backend pendiente para esta app nueva, no un
# problema de la automatizacion. Corrido con SCASTI_DW (rol JEFESUCU no
# confirmado en esa cuenta - igual no importa, el bloqueo es anterior a
# cualquier chequeo de rol: la app ni abre).

_MOTIVO_BLOQUEO_RF02_CORS = (
    "BLOQUEADO: la pantalla 'Mantenedor De Estados De Comprobantes De Pago' "
    "no abre - error CORS real confirmado en consola al llamar "
    "LanzarAplicativoDebug ('Access to XMLHttpRequest ... blocked by CORS "
    "policy: No Access-Control-Allow-Origin header is present'). El iframe "
    "#aplicacion nunca se crea. Modulo recien migrado (primera vez que se "
    "abre esta app en Pruebas) - probable configuracion de CORS pendiente "
    "en el backend para esta app nueva, no un defecto de la automatizacion "
    "ni falta de rol (el bloqueo ocurre ANTES de cualquier chequeo de rol)."
)

for _cp_rf02, _nombre_rf02 in (
    ("CP008", "Consultar comprobantes por n\\u00famero de cliente"),
    ("CP009", "Consultar comprobantes con acceso total configurado"),
    ("CP010", "Anular un comprobante vigente"),
    ("CP011", "Anular comprobante ya anulado"),
    ("CP012", "Anular pago a cuenta con sucursal ya transmitida"),
    ("CP013", "Anular pago a cuenta con comprobantes asociados"),
    ("CP014", "Exportar resultado de consulta"),
    ("CP015", "Validar comportamiento responsive de la pantalla"),
    ("CP044", "Anular comprobante de pago a cuenta no generado hoy"),
):
    CUERPOS_REALES[_cp_rf02] = f'''
raise NotImplementedError("{_cp_rf02} (RF-02 - {_nombre_rf02}): {_MOTIVO_BLOQUEO_RF02_CORS}")
'''

# --- Un add() por cada uno de los 45 casos de matriz_casos.json, en orden ---
for _cp in sorted(MATRIZ, key=lambda x: int(x[2:])):
    _m = MATRIZ[_cp]
    _body = CUERPOS_REALES.get(_cp) or _body_pendiente(_cp, _m["rf"], _m["name"])
    add(_cp, _body)


if __name__ == "__main__":
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")
