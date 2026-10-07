"""
generate_scripts.py de PR000325-SP7 - FUENTE DE VERDAD que genera los CPxxx.py.

Proyecto: Migracion del Modulo de Facturacion - submodulo Gestion de
Lecturas, 5 pantallas (RF-01..RF-05), 64 casos (ver matriz_casos.json).
Ver documentos/EF_texto.txt y documentos/ET_texto.txt para el detalle
funcional/tecnico completo.

Las 5 pantallas NO viven bajo "Comercial" (a diferencia de otros
proyectos Web LDS de este sprint) sino en el bucket plano
"Interno > Plataforma Web" (confirmado en vivo 06/10/2026). Componentes
Angular raiz y rutas reales confirmadas:
- RF-01 "Correccion De Lecturas Ordinarias": app-corord-list, .../corrlecordi/web/home
- RF-02 "Correccion De Demandas Leidas Historicas": app-cordem-list, .../corrdemleida/web/home
- RF-03 "Correccion De Lecturas Maximetros": app-cormax-list, .../corrlecmax/web/home
- RF-04 "Consulta De Lecturas De Maximetro": app-conmax-list, .../conslecmax/web/home
- RF-05 "Correccion De Lecturas De Facturacion": app-corfac-list, .../veriflectu/web/home

HALLAZGO 06/10/2026: SCASTI_DW (cuenta usada en otros sprints de
PR000325) NO tiene acceso a RF-05 (falta el rol INSPMAXI) - no aparece
en su menu. DCABA_DW SI tiene las 5 pantallas accesibles de entrada.
Decision del usuario: usar DCABA_DW para TODO el proyecto (no mezclar
cuentas por RF).

Cliente de prueba reusado de PR000325-SP6 (mismo ambiente de Pruebas):
numero 000100001, DV=2, Ruta Lectura=15090530, Clave Tarifa=0021 -
confirmar en vivo que sigue sirviendo para este sprint antes de asumirlo.
"""
import inspect
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
FRAMEWORK_DIR = OUT_DIR.parent / "_framework"
sys.path.insert(0, str(FRAMEWORK_DIR))
import web_lds_core as core  # noqa: E402

PROYECTO = "PR000325-SP7"  # debe coincidir con el nombre de esta carpeta
MATRIZ = json.loads((OUT_DIR / "matriz_casos.json").read_text(encoding="utf-8"))

ENV_TOGGLES = core.ENV_TOGGLES_CODE.replace("__PROYECTO__", PROYECTO)

# --- Helpers de navegacion propios de este proyecto ---
NAV_HELPERS = '''
def abrir_rf01(page, paso_excel=None):
    return abrir_aplicacion(page, ["Interno", "Plataforma Web", "Corrección De Lecturas Ordinarias"], "app-corord-list", paso_excel=paso_excel)


def abrir_rf02(page, paso_excel=None):
    return abrir_aplicacion(page, ["Interno", "Plataforma Web", "Corrección De Demandas Leídas Históricas"], "app-cordem-list", paso_excel=paso_excel)


def abrir_rf03(page, paso_excel=None):
    return abrir_aplicacion(page, ["Interno", "Plataforma Web", "Corrección De Lecturas Maxímetros"], "app-cormax-list", paso_excel=paso_excel)


def abrir_rf04(page, paso_excel=None):
    return abrir_aplicacion(page, ["Interno", "Plataforma Web", "Consulta De Lecturas De Maxímetro"], "app-conmax-list", paso_excel=paso_excel)


def abrir_rf05(page, paso_excel=None):
    return abrir_aplicacion(page, ["Interno", "Plataforma Web", "Corrección De Lecturas De Facturación"], "app-corfac-list", paso_excel=paso_excel)


def cerrar_ventana_validacion(app, frame, timeout_ms=4000):
    """Cierra el modal de validacion/confirmacion que aparezca (clase
    ".ant-modal", tolera tanto "Aceptar" como "Cerrar") y devuelve su
    texto completo. Tolerante: devuelve None si no aparece ningun modal."""
    contenedor = frame.locator(".ant-modal")
    try:
        contenedor.first.wait_for(state="visible", timeout=timeout_ms)
    except PWTimeoutError:
        return None
    texto = contenedor.first.inner_text()
    boton = contenedor.first.get_by_role("button", name=re.compile(r"^\\s*(Aceptar|Cerrar)\\s*$", re.I))
    if boton.count():
        boton.first.click()
    app.wait_for_timeout(500)
    return texto
'''
HELPERS_MODULOS = NAV_HELPERS

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


def add(cp, body, usuario="DCABA_DW", password="Melquisedec_01"):
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

# RF-01: Correccion De Lecturas Ordinarias. Selectores reales confirmados
# 06/10/2026: inputs por aria-label (sin id) - "Ruta de Lectura (9 digitos)"
# + "DV Ruta", o "N° Cliente (8 digitos)" + "DV Cliente"; boton "Leer";
# grilla de resultados con un UNICO boton "Seleccionar" global (debajo de
# la tabla, no uno por fila - hay que clickear la fila para resaltarla
# primero); formulario de correccion con combo "Clave Lectura" (catalogo
# ~40 opciones), Lectura Anterior/Actual, Dda. Leida FP/HP, botones
# Modificar/Cancelar/Ver Auditoria/Demandas Facturadas.
#
# GOTCHA real confirmado 06/10/2026: la grilla "vacia" (sin resultados)
# SIGUE mostrando 1 <tr> en el DOM con el texto placeholder "Ingrese un
# criterio de busqueda y presione Leer." - un assert ingenuo de
# filas.count() > 0 (o texto_fila.strip()) da un FALSO OK con este
# placeholder. Excluir explicitamente ese texto. Tambien hace falta
# esperar el indicador "Buscando..." (2 fases: visible primero, despues
# hidden - mismo patron ya confirmado en otro proyecto de esta sesion)
# antes de leer la grilla, o se lee a mitad de carga.
#
# Cliente real con suministro real confirmado via SQL (tabla lectu,
# schema clientes): numero_cliente=1495133 (8 digitos con cero relleno:
# "01495133"), DV=4 (tabla cliente.dv_numero_cliente), medidor 6794944,
# tipo_libro='C', sector=16, tiene_maximetro='N' - sector normal, no
# bloqueado. El cliente generico 00100001/DV=2 reusado de SP6 NO tiene
# suministros en ESTA pantalla especifica (0 filas reales) - descartado.
CUERPOS_REALES["CP001"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
frame.locator('input[aria-label^="N° Cliente"]').fill("01495133")
frame.locator('input[aria-label="DV Cliente"]').fill("4")
app.wait_for_timeout(500)
capturar_paso(app, "cliente_ingresado", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
buscando = frame.get_by_text("Buscando...")
try:
    buscando.first.wait_for(state="visible", timeout=5000)
except Exception:
    pass
try:
    buscando.first.wait_for(state="hidden", timeout=15000)
except Exception:
    pass
app.wait_for_timeout(500)

filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 suministro en la grilla de resultados"
texto_fila = filas.first.inner_text()
assert texto_fila.strip() and "ingrese un criterio" not in texto_fila.lower(), (
    f"La grilla no muestra suministros reales (placeholder de busqueda vacia): {texto_fila!r}"
)
assert "6794944" in texto_fila, f"No se encontro el medidor esperado en la fila: {texto_fila!r}"
capturar_paso(app, "grilla_con_suministros", paso_excel=5)
'''

CUERPOS_REALES["CP047"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
frame.locator('input[aria-label^="Ruta de Lectura"]').fill("12345")
app.wait_for_timeout(500)
capturar_paso(app, "ruta_corta_ingresada", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=6000)
assert resultado and "ruta debe ser de 9" in resultado.lower(), (
    f"No se vio el mensaje esperado 'Ruta debe ser de 9 digitos.': {resultado!r}"
)
capturar_paso(app, "mensaje_ruta_invalida", paso_excel=5)
'''

CUERPOS_REALES["CP008"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
capturar_paso(app, "desktop_1920x1080", paso_excel=3)

app.set_viewport_size({"width": 768, "height": 1024})
app.wait_for_timeout(1000)
scroll_x = app.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
assert scroll_x <= 5, f"La pantalla desborda horizontalmente en tablet (768x1024): {scroll_x}px de scroll"
assert frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).is_visible(), "El boton Leer deberia seguir visible en tablet"
capturar_paso(app, "tablet_768x1024", paso_excel=4)

app.set_viewport_size({"width": 375, "height": 667})
app.wait_for_timeout(1000)
scroll_x_mobile = app.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
assert scroll_x_mobile <= 5, f"La pantalla desborda horizontalmente en mobile (375x667): {scroll_x_mobile}px de scroll"
assert frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).is_visible(), "El boton Leer deberia seguir visible en mobile"
capturar_paso(app, "mobile_375x667", paso_excel=6)
'''

# CP002: misma orden real de CP001 (cliente 1495133/medidor 6794944) pero
# buscada por Ruta Lectura en vez de N Cliente. Ruta = sector(16) +
# zona(353) + correlativo_ruta(0205) = "163530205", DV ruta = "0"
# (confirmado via SQL sobre lectu y en vivo 06/10/2026).
CUERPOS_REALES["CP002"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
frame.locator('input[aria-label^="Ruta de Lectura"]').fill("163530205")
frame.locator('input[aria-label="DV Ruta"]').fill("0")
app.wait_for_timeout(500)
capturar_paso(app, "ruta_ingresada", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
buscando = frame.get_by_text("Buscando...")
try:
    buscando.first.wait_for(state="visible", timeout=5000)
except Exception:
    pass
try:
    buscando.first.wait_for(state="hidden", timeout=15000)
except Exception:
    pass
app.wait_for_timeout(500)

filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 suministro en la grilla de resultados"
texto_fila = filas.first.inner_text()
assert texto_fila.strip() and "ingrese un criterio" not in texto_fila.lower(), (
    f"La grilla no muestra suministros reales: {texto_fila!r}"
)
assert "6794944" in texto_fila, f"No se encontro el medidor esperado en la fila: {texto_fila!r}"
capturar_paso(app, "grilla_con_suministros_por_ruta", paso_excel=5)
'''

# RF-02: Correccion De Demandas Leidas Historicas. Criterio de busqueda
# via 2 radio buttons (Ruta Lectura / Numero Cliente, input[type=radio]
# nth 0/1) en vez de 2 campos paralelos como RF-01. Campos reales:
# aria-label "Numero de Cliente (8 digitos)" + "Digito verificador"
# (distinto de "DV Cliente" de RF-01), o "Ruta de Lectura (9 digitos)"
# (sin campo DV Ruta separado aqui). NO hay grid de resultados.
#
# GOTCHA real confirmado 06/10/2026: "Fecha de Lectura" esta HABILITADO
# DESDE EL INICIO, sin importar si hubo busqueda (confirmado con
# is_enabled()==True incluso antes de cualquier Leer) - un assert sobre
# su habilitacion es un falso positivo trivial, NO prueba que la
# busqueda funciono. La senal real de busqueda EXITOSA es que los
# CAMPOS DE BUSQUEDA (Numero Cliente/DV o Ruta, y el boton Leer) quedan
# BLOQUEADOS/deshabilitados tras encontrar el suministro (confirmado
# visualmente: se ven grises con el valor repoblado) - al reves de lo
# que dice la matriz textualmente, pero es lo unico que efectivamente
# cambia en el DOM. Demanda FP/HP SI estan genuinamente deshabilitados
# por defecto (disabled="" real en el HTML).
#
# Mismo cliente real de RF-01: 1495133/DV=4, ruta 163530205/DV=0
# (confirmado en vivo que SI tiene suministro reconocido por
# BuscarSuministro, aunque sea otro dominio de datos que el grid de RF-01).
CUERPOS_REALES["CP010"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
radios = frame.locator('input[type="radio"]')
radios.nth(1).click(force=True)
app.wait_for_timeout(500)
campo_cli = frame.locator('input[aria-label^="Número de Cliente"]')
campo_dv = frame.locator('input[aria-label="Dígito verificador"]')
boton_leer = frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$"))
campo_cli.fill("01495133")
campo_dv.fill("4")
app.wait_for_timeout(500)
capturar_paso(app, "cliente_ingresado", paso_excel=3)

boton_leer.click()
buscando = frame.get_by_text("Buscando...")
try:
    buscando.first.wait_for(state="visible", timeout=5000)
except Exception:
    pass
try:
    buscando.first.wait_for(state="hidden", timeout=15000)
except Exception:
    pass
app.wait_for_timeout(500)

assert not campo_cli.is_enabled(), "Se esperaba que el campo Numero de Cliente quede bloqueado tras la busqueda exitosa"
assert not boton_leer.is_enabled(), "Se esperaba que el boton Leer quede deshabilitado tras la busqueda exitosa"
campo_fp = frame.locator('input[aria-label^="Demanda Leída Fuera de Punta"]')
campo_hp = frame.locator('input[aria-label^="Demanda Leída Hora de Punta"]')
assert not campo_fp.is_enabled(), "Demanda FP deberia seguir deshabilitado hasta ingresar una fecha"
assert not campo_hp.is_enabled(), "Demanda HP deberia seguir deshabilitado hasta ingresar una fecha"
capturar_paso(app, "busqueda_exitosa_campos_bloqueados", paso_excel=5)
'''

CUERPOS_REALES["CP009"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
campo_ruta = frame.locator('input[aria-label^="Ruta de Lectura"]')
boton_leer = frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$"))
campo_ruta.fill("163530205")
app.wait_for_timeout(500)
capturar_paso(app, "ruta_ingresada", paso_excel=3)

boton_leer.click()
buscando = frame.get_by_text("Buscando...")
try:
    buscando.first.wait_for(state="visible", timeout=5000)
except Exception:
    pass
try:
    buscando.first.wait_for(state="hidden", timeout=15000)
except Exception:
    pass
app.wait_for_timeout(500)

assert not campo_ruta.is_enabled(), "Se esperaba que el campo Ruta de Lectura quede bloqueado tras la busqueda exitosa"
assert not boton_leer.is_enabled(), "Se esperaba que el boton Leer quede deshabilitado tras la busqueda exitosa"
campo_fp = frame.locator('input[aria-label^="Demanda Leída Fuera de Punta"]')
campo_hp = frame.locator('input[aria-label^="Demanda Leída Hora de Punta"]')
assert not campo_fp.is_enabled() and not campo_hp.is_enabled(), "Demanda FP/HP deberian seguir deshabilitados"
capturar_paso(app, "busqueda_exitosa_por_ruta", paso_excel=5)
'''

CUERPOS_REALES["CP011"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
radios = frame.locator('input[type="radio"]')
radios.nth(1).click(force=True)
app.wait_for_timeout(500)
campo_cli = frame.locator('input[aria-label^="Número de Cliente"]')
boton_leer = frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$"))
campo_cli.fill("09999999")
frame.locator('input[aria-label="Dígito verificador"]').fill("9")
app.wait_for_timeout(500)
capturar_paso(app, "cliente_inexistente_ingresado", paso_excel=3)

boton_leer.click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=10000)
assert resultado, "Se esperaba un mensaje de error para un suministro inexistente"
capturar_paso(app, "mensaje_error_suministro_inexistente", paso_excel=5)

# Tras una busqueda FALLIDA, los campos de busqueda NO deben quedar
# bloqueados (a diferencia de una busqueda exitosa, ver CP009/CP010) -
# esta es la senal real de que el suministro no se encontro.
assert campo_cli.is_enabled(), "El campo Numero de Cliente deberia seguir habilitado tras una busqueda fallida"
assert boton_leer.is_enabled(), "El boton Leer deberia seguir habilitado tras una busqueda fallida"
campo_fp = frame.locator('input[aria-label^="Demanda Leída Fuera de Punta"]')
campo_hp = frame.locator('input[aria-label^="Demanda Leída Hora de Punta"]')
assert not campo_fp.is_enabled() and not campo_hp.is_enabled(), "Demanda FP/HP NO deberian habilitarse tras una busqueda fallida"
capturar_paso(app, "campos_de_busqueda_siguen_habilitados", paso_excel=6)
'''

CUERPOS_REALES["CP017"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
capturar_paso(app, "desktop_1920x1080", paso_excel=3)

app.set_viewport_size({"width": 768, "height": 1024})
app.wait_for_timeout(1000)
scroll_x = app.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
assert scroll_x <= 5, f"La pantalla desborda horizontalmente en tablet (768x1024): {scroll_x}px de scroll"
assert frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).is_visible(), "El boton Leer deberia seguir visible en tablet"
capturar_paso(app, "tablet_768x1024", paso_excel=4)

app.set_viewport_size({"width": 375, "height": 667})
app.wait_for_timeout(1000)
scroll_x_mobile = app.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
assert scroll_x_mobile <= 5, f"La pantalla desborda horizontalmente en mobile (375x667): {scroll_x_mobile}px de scroll"
assert frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).is_visible(), "El boton Leer deberia seguir visible en mobile"
capturar_paso(app, "mobile_375x667", paso_excel=6)
'''

CUERPOS_REALES["CP051"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
radios = frame.locator('input[type="radio"]')
radios.nth(1).click(force=True)
app.wait_for_timeout(500)
campo_cli = frame.locator('input[aria-label^="Número de Cliente"]')
campo_dv = frame.locator('input[aria-label="Dígito verificador"]')

campo_cli.fill("01495133")
campo_dv.fill("9")
campo_dv.blur()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=8000)
assert resultado and "d" in resultado.lower() and "verificador" in resultado.lower() and "no corresponde" in resultado.lower(), (
    f"No se vio el mensaje esperado de DV incorrecto: {resultado!r}"
)
app.wait_for_timeout(500)
assert campo_dv.input_value() == "", f"Se esperaba que el campo DV quedara limpio: {campo_dv.input_value()!r}"
capturar_paso(app, "dv_incorrecto_limpiado", paso_excel=3)

campo_cli.fill("01495133")
app.wait_for_timeout(300)
boton_leer = frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$"))
boton_leer.click()
resultado2 = cerrar_ventana_validacion(app, frame, timeout_ms=8000)
assert resultado2 and "ingrese d" in resultado2.lower() and "verificador" in resultado2.lower(), (
    f"No se vio el mensaje esperado de DV vacio: {resultado2!r}"
)
# Si la busqueda NO se ejecuto, el campo Cliente/boton Leer siguen
# habilitados (misma senal usada en CP009/CP010/CP011: una busqueda
# exitosa es la UNICA que bloquea estos campos).
assert campo_cli.is_enabled() and boton_leer.is_enabled(), "No deberia haberse ejecutado la busqueda con DV vacio"
capturar_paso(app, "dv_vacio_sin_busqueda", paso_excel=4)
'''

# RF-03: Correccion De Lecturas Maximetros. Mismo patron de selectores
# que RF-01 (aria-label "N° Cliente (8 dígitos)" + "DV Cliente", grid
# con boton "Seleccionar" global que tampoco se habilita aqui - mismo
# bloqueo sin resolver que RF-01, ver memoria del proyecto). Cliente
# real maximetro confirmado 06/10/2026: 2390020/DV=3 (sector 30,
# tiene_maximetro='S', clave_tarifa=0031) - grid real de 4 filas
# (medidor 55624401 con sub-filas C/D, 55624402, 55624403). Cliente NO
# maximetro para CP019: mismo 1495133/DV=4 de RF-01/02.
CUERPOS_REALES["CP018"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
frame.locator('input[aria-label^="N° Cliente"]').fill("02390020")
frame.locator('input[aria-label="DV Cliente"]').fill("3")
app.wait_for_timeout(500)
capturar_paso(app, "cliente_maximetro_ingresado", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
buscando = frame.get_by_text("Buscando...")
try:
    buscando.first.wait_for(state="visible", timeout=5000)
except Exception:
    pass
try:
    buscando.first.wait_for(state="hidden", timeout=15000)
except Exception:
    pass
app.wait_for_timeout(500)

filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 lectura en la grilla de resultados"
texto_fila = filas.first.inner_text()
assert texto_fila.strip() and "ingrese un criterio" not in texto_fila.lower(), (
    f"La grilla no muestra lecturas reales: {texto_fila!r}"
)
assert "55624401" in texto_fila, f"No se encontro el medidor esperado en la fila: {texto_fila!r}"
capturar_paso(app, "grilla_con_lecturas_maximetro", paso_excel=5)
'''

CUERPOS_REALES["CP019"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
frame.locator('input[aria-label^="N° Cliente"]').fill("01495133")
frame.locator('input[aria-label="DV Cliente"]').fill("4")
app.wait_for_timeout(500)
capturar_paso(app, "cliente_no_maximetro_ingresado", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=10000)
assert resultado and "no es de tipo" in resultado.lower() and "maximetro" in resultado.lower(), (
    f"No se vio el mensaje esperado de cliente no maximetro: {resultado!r}"
)
capturar_paso(app, "mensaje_cliente_no_maximetro", paso_excel=5)
'''

CUERPOS_REALES["CP025"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
capturar_paso(app, "desktop_1920x1080", paso_excel=3)

app.set_viewport_size({"width": 768, "height": 1024})
app.wait_for_timeout(1000)
scroll_x = app.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
assert scroll_x <= 5, f"La pantalla desborda horizontalmente en tablet (768x1024): {scroll_x}px de scroll"
assert frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).is_visible(), "El boton Leer deberia seguir visible en tablet"
capturar_paso(app, "tablet_768x1024", paso_excel=4)

app.set_viewport_size({"width": 375, "height": 667})
app.wait_for_timeout(1000)
scroll_x_mobile = app.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
assert scroll_x_mobile <= 5, f"La pantalla desborda horizontalmente en mobile (375x667): {scroll_x_mobile}px de scroll"
assert frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).is_visible(), "El boton Leer deberia seguir visible en mobile"
capturar_paso(app, "mobile_375x667", paso_excel=6)
'''

# RF-04: Consulta De Lecturas De Maximetro. Boton "Buscar" (no "Leer"
# como el resto), aria-labels distintos: "N.° de Cliente" + "DV"
# (ambiguo, hay 2 campos DV en el DOM - usar .first para el de
# cliente), "Ruta de Lectura" + "DV Ruta". Mismo cliente maximetro real
# de RF-03: 2390020/DV=3, mismo grid de 4 filas (55624401 C/D,
# 55624402, 55624403).
CUERPOS_REALES["CP026"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator('input[aria-label="N.° de Cliente"]').fill("02390020")
frame.locator('input[aria-label="DV"]').first.fill("3")
app.wait_for_timeout(500)
capturar_paso(app, "cliente_maximetro_ingresado", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Buscar\\s*$")).click()
buscando = frame.get_by_text("Buscando...")
try:
    buscando.first.wait_for(state="visible", timeout=5000)
except Exception:
    pass
try:
    buscando.first.wait_for(state="hidden", timeout=15000)
except Exception:
    pass
app.wait_for_timeout(500)

filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 lectura en la grilla de resultados"
texto_fila = filas.first.inner_text()
assert texto_fila.strip() and "ingrese un criterio" not in texto_fila.lower(), (
    f"La grilla no muestra lecturas reales: {texto_fila!r}"
)
assert "55624401" in texto_fila, f"No se encontro el medidor esperado en la fila: {texto_fila!r}"
capturar_paso(app, "grilla_con_lecturas_maximetro", paso_excel=5)
'''

CUERPOS_REALES["CP058"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
capturar_paso(app, "pantalla_sin_datos", paso_excel=2)

frame.get_by_role("button", name=re.compile(r"^\\s*Buscar\\s*$")).click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=8000)
assert resultado and "ingrese n" in resultado.lower() and "cliente" in resultado.lower() and "ruta de lectura" in resultado.lower(), (
    f"No se vio el mensaje esperado de criterio obligatorio: {resultado!r}"
)
capturar_paso(app, "mensaje_criterio_obligatorio", paso_excel=4)
'''

# --- Un add() por cada uno de los 64 casos de matriz_casos.json, en orden ---
for _cp in sorted(MATRIZ, key=lambda x: int(x[2:])):
    _m = MATRIZ[_cp]
    _body = CUERPOS_REALES.get(_cp) or _body_pendiente(_cp, _m["rf"], _m["name"])
    add(_cp, _body)


if __name__ == "__main__":
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")
