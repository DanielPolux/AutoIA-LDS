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
import json, os, re, shutil, struct, subprocess, time, zipfile
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

# Un caso listado en casos_fallidos_confirmados.json es un DEFECTO REAL ya
# verificado (no un bug de automatizacion) - el FALLO en si es la prueba
# del defecto, asi que igual merece video/Word completos (patron ya usado
# en PR000349-SP4 CP018, ver memoria del framework).
_CASOS_FALLIDOS_CONFIRMADOS_PATH = Path(__file__).resolve().parent / "casos_fallidos_confirmados.json"
_ES_DEFECTO_CONFIRMADO = False
if _CASOS_FALLIDOS_CONFIRMADOS_PATH.exists():
    try:
        _ES_DEFECTO_CONFIRMADO = CASO in json.loads(_CASOS_FALLIDOS_CONFIRMADOS_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass

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
            if _CASO_OK or _ES_DEFECTO_CONFIRMADO:
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

# CP006 ES UN DEFECTO CONFIRMADO (ver casos_fallidos_confirmados.json):
# ListarAuditoria responde SIEMPRE HTTP 500, probado con los 3 criterios
# (Fecha/Numero de Cliente/Rol). El selector real del campo de valor es
# `input[aria-label="Valor de búsqueda"]` (compartido por los 3 criterios,
# cambia de type="date" a type="text" segun cual este seleccionado) -
# NO usar cerrar_ventana_validacion() aca porque hay 2 nz-modal-container
# apilados tras el error (el modal de busqueda + el modal "Error de
# Servicio"), hay que cerrar el segundo explicitamente.
CUERPOS_REALES["CP006"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
frame.get_by_role("button", name=re.compile(r"^\\s*Ver Auditor.a\\s*$")).click()
app.wait_for_timeout(1500)
capturar_paso(app, "modal_auditoria_abierto_criterio_fecha", paso_excel=4)

campo_valor = frame.locator(\'input[aria-label="Valor de búsqueda"]\')
campo_valor.fill("2026-09-30")
app.wait_for_timeout(300)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).last.click()
app.wait_for_timeout(2000)
modal_error_fecha = frame.locator("nz-modal-container").nth(1)
assert modal_error_fecha.is_visible(), "Se esperaba el modal de Error de Servicio tras buscar por Fecha (defecto confirmado)"
resultado_fecha = modal_error_fecha.inner_text()
capturar_paso(app, "DEFECTO_error_500_busqueda_por_fecha", paso_excel=6)
assert "error al consultar" in resultado_fecha.lower(), f"No se vio el mensaje de error esperado: {resultado_fecha!r}"
modal_error_fecha.get_by_role("button", name=re.compile(r"^\\s*Cerrar\\s*$")).click()
app.wait_for_timeout(500)

radios = frame.locator("input[type=\\'radio\\']")
radios.nth(1).click(force=True)
app.wait_for_timeout(500)
campo_valor2 = frame.locator(\'input[aria-label="Valor de búsqueda"]\')
assert campo_valor2.input_value() == "", "Al cambiar de criterio, el valor de busqueda deberia quedar vacio"
campo_valor2.fill("1495133")
app.wait_for_timeout(300)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).last.click()
app.wait_for_timeout(2000)
modal_error_cliente = frame.locator("nz-modal-container").nth(1)
assert modal_error_cliente.is_visible(), "Se esperaba el modal de Error de Servicio tras buscar por Numero de Cliente (defecto confirmado)"
capturar_paso(app, "DEFECTO_error_500_busqueda_por_cliente", paso_excel=10)
modal_error_cliente.get_by_role("button", name=re.compile(r"^\\s*Cerrar\\s*$")).click()
app.wait_for_timeout(500)

radios.nth(2).click(force=True)
app.wait_for_timeout(500)
campo_valor3 = frame.locator(\'input[aria-label="Valor de búsqueda"]\')
assert campo_valor3.input_value() == "", "Al cambiar de criterio, el valor de busqueda deberia quedar vacio"
campo_valor3.fill("DACD")
app.wait_for_timeout(300)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).last.click()
app.wait_for_timeout(2000)
modal_error_rol = frame.locator("nz-modal-container").nth(1)
capturar_paso(app, "DEFECTO_error_500_busqueda_por_rol", paso_excel=14)
resultado_rol = modal_error_rol.inner_text() if modal_error_rol.is_visible() else None
assert not modal_error_rol.is_visible(), (
    "DEFECTO CONFIRMADO (ver casos_fallidos_confirmados.json): se esperaba que la grilla de auditoria "
    "mostrara solo los registros del Rol indicado, pero ListarAuditoria responde HTTP 500 para los 3 "
    f"criterios (Fecha/Cliente/Rol) - el modal de Ver Auditoria de RF-01 esta roto en el backend. Mensaje real: {resultado_rol!r}"
)
'''

# CP044 y CP045 son DEFECTOS CONFIRMADOS (ver casos_fallidos_confirmados.json),
# mismo origen que CP006: ListarAuditoria responde HTTP 500 siempre, asi que
# ninguno de los 2 puede llegar a su "esperado" real (descargar PDF / comparar
# grilla con y sin Sector-Zona) porque el paso previo (que la busqueda
# devuelva al menos 1 registro) nunca se completa.
CUERPOS_REALES["CP044"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
frame.get_by_role("button", name=re.compile(r"^\\s*Ver Auditor.a\\s*$")).click()
app.wait_for_timeout(1500)

radios = frame.locator("input[type=\\'radio\\']")
radios.nth(1).click(force=True)
app.wait_for_timeout(500)
campo_valor = frame.locator(\'input[aria-label="Valor de búsqueda"]\')
campo_valor.fill("1495133")
app.wait_for_timeout(300)
capturar_paso(app, "criterio_cliente_con_registro_conocido_ingresado", paso_excel=4)

boton_descargar_antes = frame.get_by_role("button", name=re.compile(r"^\\s*Descargar PDF\\s*$"))
assert not boton_descargar_antes.is_enabled(), "Descargar PDF no deberia estar habilitado antes de una busqueda exitosa"

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).last.click()
app.wait_for_timeout(2000)
modal_error = frame.locator("nz-modal-container").nth(1)
capturar_paso(app, "DEFECTO_error_500_bloquea_busqueda_previa_a_pdf", paso_excel=5)
resultado = modal_error.inner_text() if modal_error.is_visible() else None
assert not modal_error.is_visible(), (
    "DEFECTO CONFIRMADO (ver casos_fallidos_confirmados.json): se esperaba que la busqueda devolviera "
    "al menos 1 registro para poder presionar Descargar PDF, pero ListarAuditoria responde HTTP 500 - "
    f"nunca se llega a habilitar Descargar PDF. Mensaje real: {resultado!r}"
)
'''

CUERPOS_REALES["CP045"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
frame.get_by_role("button", name=re.compile(r"^\\s*Ver Auditor.a\\s*$")).click()
app.wait_for_timeout(1500)

radios = frame.locator("input[type=\\'radio\\']")
radios.nth(1).click(force=True)
app.wait_for_timeout(500)
campo_valor = frame.locator(\'input[aria-label="Valor de búsqueda"]\')
campo_valor.fill("1495133")
frame.locator(\'input[aria-label="Sector"]\').fill("16")
frame.locator(\'input[aria-label="Zona"]\').fill("353")
app.wait_for_timeout(300)
capturar_paso(app, "criterio_cliente_con_sector_zona_de_ruta_real", paso_excel=5)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).last.click()
app.wait_for_timeout(2000)
modal_error = frame.locator("nz-modal-container").nth(1)
capturar_paso(app, "DEFECTO_error_500_bloquea_busqueda_con_filtro_sector_zona", paso_excel=6)
resultado = modal_error.inner_text() if modal_error.is_visible() else None
assert not modal_error.is_visible(), (
    "DEFECTO CONFIRMADO (ver casos_fallidos_confirmados.json): se esperaba que la grilla mostrara solo "
    "los registros del Sector/Zona filtrado, pero ListarAuditoria responde HTTP 500 incluso con el filtro "
    f"opcional Sector/Zona aplicado - nunca se puede comparar contra la busqueda sin filtro. Mensaje real: {resultado!r}"
)
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

# GOTCHA real confirmado 07/10/2026 (RF-02): el campo "Fecha de lectura"
# NO queda correctamente evaluado contra el historial con solo fill()+Tab
# (ObtenerHistoria SI se llama automaticamente tras Leer, pero el chequeo
# de fecha en el frontend no lo refleja hasta que se hace click en
# "Historia..." al menos una vez - no documentado en el manual, confirmado
# reproducible 2/2). Receta real: fill(fecha) + Tab, LUEGO click en
# "Historia...", y RECIEN AHI Dda. Leida FP/HP reflejan el estado real
# (poblado+habilitado si existe HISDE, vacio+habilitado si no existe).
# Los campos de demanda tienen una directiva Angular "appnumerico" que
# necesita presionar_secuencialmente (press_sequentially), NO fill() -
# con fill() el valor no se reconoce como numerico valido al confirmar.
#
# Candidato SIN HISDE para ninguna fecha (CP012/CP014): 1495133/DV=4,
# fecha real con HISCO pero sin HISDE: "2026-06-23" (fila mas reciente
# del historial, 197 filas, TODAS sin demanda - confirmado en vivo).
CUERPOS_REALES["CP012"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
radios = frame.locator(\'input[type="radio"]\')
radios.nth(1).click(force=True)
app.wait_for_timeout(400)
frame.locator(\'input[aria-label^="Número de Cliente"]\').fill("01495133")
frame.locator(\'input[aria-label="Dígito verificador"]\').fill("4")
app.wait_for_timeout(300)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(1500)

campo_fecha = frame.locator(\'input[aria-label="Fecha de lectura"]\')
campo_fp = frame.locator(\'input[aria-label^="Demanda Leída Fuera de Punta"]\')
campo_hp = frame.locator(\'input[aria-label^="Demanda Leída Hora de Punta"]\')
boton_modificar = frame.get_by_role("button", name=re.compile(r"^\\s*Modificar\\s*$"))

campo_fecha.fill("2026-06-23")
campo_fecha.press("Tab")
app.wait_for_timeout(800)
frame.get_by_role("button", name=re.compile(r"^\\s*Historia\\.\\.\\.\\s*$")).click()
app.wait_for_timeout(1500)
capturar_paso(app, "fecha_sin_hisde_campos_habilitados_vacios", paso_excel=5)

assert campo_fp.is_enabled() and campo_fp.input_value() == "", "Demanda FP deberia quedar HABILITADA y vacia (existe HISCO, sin HISDE)"
assert campo_hp.is_enabled() and campo_hp.input_value() == "", "Demanda HP deberia quedar HABILITADA y vacia (existe HISCO, sin HISDE)"
assert boton_modificar.is_enabled(), "Modificar deberia habilitarse aunque no exista demanda historica todavia"

campo_fp.press_sequentially("100.00", delay=60)
campo_hp.press_sequentially("50.00", delay=60)
app.wait_for_timeout(300)
capturar_paso(app, "valores_ingresados_antes_de_modificar", paso_excel=6)

boton_modificar.click()
modal_confirma = frame.locator("nz-modal-container").last
modal_confirma.wait_for(state="visible", timeout=6000)
modal_confirma.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$")).click()
app.wait_for_timeout(1500)
modal_final = frame.locator("nz-modal-container").last
resultado = modal_final.inner_text()
capturar_paso(app, "mensaje_rechazo_no_existe_demanda_historica", paso_excel=7)
assert "no existe demanda hist" in resultado.lower() and "corrija" in resultado.lower(), (
    f"No se vio el mensaje esperado de rechazo: {resultado!r}"
)
'''

# Candidato CON HISDE real (CP013): 14699/DV=4, fecha "2026-06-30" con
# Dda. Leida FP=384.72, HP=375.56 ya registrados (confirmado en vivo).
CUERPOS_REALES["CP013"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
radios = frame.locator(\'input[type="radio"]\')
radios.nth(1).click(force=True)
app.wait_for_timeout(400)
frame.locator(\'input[aria-label^="Número de Cliente"]\').fill("00014699")
frame.locator(\'input[aria-label="Dígito verificador"]\').fill("4")
app.wait_for_timeout(300)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(1500)

campo_fecha = frame.locator(\'input[aria-label="Fecha de lectura"]\')
campo_fp = frame.locator(\'input[aria-label^="Demanda Leída Fuera de Punta"]\')
campo_hp = frame.locator(\'input[aria-label^="Demanda Leída Hora de Punta"]\')
boton_modificar = frame.get_by_role("button", name=re.compile(r"^\\s*Modificar\\s*$"))

campo_fecha.fill("2026-06-30")
campo_fecha.press("Tab")
app.wait_for_timeout(800)
frame.get_by_role("button", name=re.compile(r"^\\s*Historia\\.\\.\\.\\s*$")).click()
app.wait_for_timeout(1500)
capturar_paso(app, "fecha_con_registro_existente_precargado", paso_excel=3)

valor_fp_original = campo_fp.input_value()
assert valor_fp_original not in ("", "0.00", "0,00"), (
    f"Se esperaba un valor de Demanda FP ya registrado para esta fecha: {valor_fp_original!r}"
)

campo_fp.fill("")
campo_fp.press_sequentially("395.50", delay=60)
campo_hp.fill("")
campo_hp.press_sequentially("380.25", delay=60)
app.wait_for_timeout(300)
capturar_paso(app, "nuevos_valores_ingresados", paso_excel=4)

boton_modificar.click()
modal_confirma = frame.locator("nz-modal-container").last
modal_confirma.wait_for(state="visible", timeout=6000)
modal_confirma.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$")).click()
app.wait_for_timeout(1500)
modal_final = frame.locator("nz-modal-container").last
resultado = modal_final.inner_text()
capturar_paso(app, "registro_actualizado_confirmado", paso_excel=6)
assert "registro actualizado" in resultado.lower(), f"No se vio el mensaje esperado de actualizacion: {resultado!r}"

# Al aceptar, la pantalla vuelve a su estado inicial (equivale a
# "Cancelar", segun el manual) - para verificar que NO se duplico el
# registro hay que volver a buscar el mismo suministro desde cero y
# revisar la historia otra vez.
modal_final.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$")).click()
app.wait_for_timeout(1000)

radios.nth(1).click(force=True)
app.wait_for_timeout(400)
frame.locator(\'input[aria-label^="Número de Cliente"]\').fill("00014699")
frame.locator(\'input[aria-label="Dígito verificador"]\').fill("4")
app.wait_for_timeout(300)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(1500)
frame.get_by_role("button", name=re.compile(r"^\\s*Historia\\.\\.\\.\\s*$")).click()
app.wait_for_timeout(1500)

filas_fecha = frame.locator("table tbody tr", has_text="30/06/2026")
assert filas_fecha.count() == 1, f"Se esperaba una unica fila para 30/06/2026 tras actualizar (sin duplicar): {filas_fecha.count()}"
assert "395.50" in filas_fecha.first.inner_text(), f"Se esperaba el nuevo valor (395.50) persistido en la fila: {filas_fecha.first.inner_text()!r}"
capturar_paso(app, "sin_registro_duplicado_valor_persistido", paso_excel=7)
'''

# Mismo escenario tecnico que CP012 (HISCO sin HISDE), con precondicion
# redactada distinto en la matriz ("consumo historico sin demanda
# corregida" en vez de "existe HISCO, sin HISDE") - misma condicion real,
# otra fecha del mismo cliente para no depender de que CP012 no haya
# corrido antes.
CUERPOS_REALES["CP014"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
radios = frame.locator(\'input[type="radio"]\')
radios.nth(1).click(force=True)
app.wait_for_timeout(400)
frame.locator(\'input[aria-label^="Número de Cliente"]\').fill("01495133")
frame.locator(\'input[aria-label="Dígito verificador"]\').fill("4")
app.wait_for_timeout(300)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(1500)

campo_fecha = frame.locator(\'input[aria-label="Fecha de lectura"]\')
campo_fp = frame.locator(\'input[aria-label^="Demanda Leída Fuera de Punta"]\')
campo_hp = frame.locator(\'input[aria-label^="Demanda Leída Hora de Punta"]\')
boton_modificar = frame.get_by_role("button", name=re.compile(r"^\\s*Modificar\\s*$"))

campo_fecha.fill("2026-05-25")
campo_fecha.press("Tab")
app.wait_for_timeout(800)
frame.get_by_role("button", name=re.compile(r"^\\s*Historia\\.\\.\\.\\s*$")).click()
app.wait_for_timeout(1500)
capturar_paso(app, "fecha_con_consumo_sin_demanda_corregida", paso_excel=4)

campo_fp.press_sequentially("75.00", delay=60)
campo_hp.press_sequentially("25.00", delay=60)
app.wait_for_timeout(300)

boton_modificar.click()
modal_confirma = frame.locator("nz-modal-container").last
modal_confirma.wait_for(state="visible", timeout=6000)
modal_confirma.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$")).click()
app.wait_for_timeout(1500)
modal_final = frame.locator("nz-modal-container").last
resultado = modal_final.inner_text()
capturar_paso(app, "mensaje_rechazo_sistema_nunca_crea", paso_excel=6)
assert "no existe demanda hist" in resultado.lower() and "corrija" in resultado.lower(), (
    f"No se vio el mensaje esperado de rechazo: {resultado!r}"
)
'''

CUERPOS_REALES["CP015"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
radios = frame.locator(\'input[type="radio"]\')
radios.nth(1).click(force=True)
app.wait_for_timeout(400)
frame.locator(\'input[aria-label^="Número de Cliente"]\').fill("01495133")
frame.locator(\'input[aria-label="Dígito verificador"]\').fill("4")
app.wait_for_timeout(300)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(1500)

boton_historia = frame.get_by_role("button", name=re.compile(r"^\\s*Historia\\.\\.\\.\\s*$"))
boton_historia.click()
app.wait_for_timeout(1500)

encabezados = frame.locator("table thead th")
textos_encabezado = [encabezados.nth(i).inner_text() for i in range(encabezados.count())]
texto_completo = " ".join(textos_encabezado)
assert "Fecha" in texto_completo and "FP" in texto_completo and "HP" in texto_completo, (
    f"No se encontraron las columnas esperadas de la historia: {textos_encabezado!r}"
)
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 fila en la historia desplegada"
capturar_paso(app, "historia_desplegada_inline", paso_excel=5)

assert not boton_historia.is_enabled(), "El boton Historia... deberia quedar deshabilitado tras la primera apertura"
capturar_paso(app, "boton_historia_deshabilitado", paso_excel=6)
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

CUERPOS_REALES["CP059"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
frame.locator('input[aria-label^="Ruta de Lectura"]').fill("12345")
app.wait_for_timeout(500)
capturar_paso(app, "ruta_corta_ingresada", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=8000)
assert resultado and "ruta debe ser de 9" in resultado.lower(), (
    f"No se vio el mensaje esperado 'Ruta debe ser de 9 Digitos.': {resultado!r}"
)
capturar_paso(app, "mensaje_ruta_invalida", paso_excel=5)
'''

# Cliente real 1399107 dado directo por la matriz: da el mismo mensaje
# especifico "Cliente no es de tipo de lectura Maximetro" que CP019 (no
# un generico "no encontrado") - eso es justamente lo que CP060 pide
# confirmar (que el backend clasifica el caso, no lo trata como 404).
CUERPOS_REALES["CP060"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
frame.locator('input[aria-label^="N° Cliente"]').fill("01399107")
app.wait_for_timeout(500)
capturar_paso(app, "cliente_1399107_ingresado", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=10000)
assert resultado and "no es de tipo" in resultado.lower() and "maximetro" in resultado.lower(), (
    f"Se esperaba el mensaje especifico de 'no es tipo maximetro' (no un generico de no-encontrado): {resultado!r}"
)
capturar_paso(app, "mensaje_clasificado_no_generico", paso_excel=5)
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

# CONFIRMADO 07/10/2026: a diferencia de RF-01/03, "Seleccionar" de RF-04
# NO tiene ninguna condicion de "apto" (tal como documenta el manual) - se
# habilita con solo marcar una fila, sin importar el cliente. Candidato
# maximetro real 2390020/DV=3 funciona de punta a punta (grid + detalle).
CUERPOS_REALES["CP027"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator('input[aria-label="N.° de Cliente"]').fill("02390020")
frame.locator('input[aria-label="DV"]').first.fill("3")
app.wait_for_timeout(500)
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
capturar_paso(app, "grilla_cargada", paso_excel=3)

frame.locator("table tbody tr").first.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"^\\s*Seleccionar\\s*$")).click()
cargando = frame.get_by_text("Cargando...")
try:
    cargando.first.wait_for(state="visible", timeout=5000)
except Exception:
    pass
try:
    cargando.first.wait_for(state="hidden", timeout=15000)
except Exception:
    pass
app.wait_for_timeout(800)
capturar_paso(app, "detalle_solo_lectura_cargado", paso_excel=5)

boton_modificar = frame.get_by_role("button", name=re.compile(r"^\\s*Modificar\\s*$"))
assert boton_modificar.count() == 0, "El boton Modificar NO deberia existir en esta pantalla de solo consulta"
datos_medidor = frame.locator("text=Datos del Medidor")
assert datos_medidor.is_visible(), "Se esperaba el panel 'Datos del Medidor' con la lectura seleccionada"
capturar_paso(app, "modificar_no_presente", paso_excel=6)
'''

CUERPOS_REALES["CP028"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator('input[aria-label="N.° de Cliente"]').fill("02390020")
frame.locator('input[aria-label="DV"]').first.fill("3")
app.wait_for_timeout(500)
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
frame.locator("table tbody tr").first.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"^\\s*Seleccionar\\s*$")).click()
cargando = frame.get_by_text("Cargando...")
try:
    cargando.first.wait_for(state="visible", timeout=5000)
except Exception:
    pass
try:
    cargando.first.wait_for(state="hidden", timeout=15000)
except Exception:
    pass
app.wait_for_timeout(800)
capturar_paso(app, "detalle_cargado_antes_de_cancelar", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Cancelar\\s*$")).first.click()
app.wait_for_timeout(1000)
campo_cli = frame.locator('input[aria-label="N.° de Cliente"]')
boton_buscar = frame.get_by_role("button", name=re.compile(r"^\\s*Buscar\\s*$"))
assert campo_cli.is_enabled() and campo_cli.input_value() == "", "El campo Cliente deberia quedar vacio y habilitado tras Cancelar"
assert boton_buscar.is_enabled(), "El boton Buscar deberia quedar habilitado tras Cancelar (grilla disponible para nueva seleccion)"
capturar_paso(app, "panel_limpio_grilla_disponible", paso_excel=6)
'''

CUERPOS_REALES["CP030"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator('input[aria-label="N.° de Cliente"]').fill("02390020")
frame.locator('input[aria-label="DV"]').first.fill("3")
app.wait_for_timeout(500)
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
frame.locator("table tbody tr").first.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"^\\s*Seleccionar\\s*$")).click()
cargando = frame.get_by_text("Cargando...")
try:
    cargando.first.wait_for(state="visible", timeout=5000)
except Exception:
    pass
try:
    cargando.first.wait_for(state="hidden", timeout=15000)
except Exception:
    pass
app.wait_for_timeout(800)
capturar_paso(app, "desktop_1920x1080_con_datos", paso_excel=4)

app.set_viewport_size({"width": 768, "height": 1024})
app.wait_for_timeout(1000)
scroll_x = app.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
assert scroll_x <= 5, f"La pantalla desborda horizontalmente en tablet (768x1024): {scroll_x}px de scroll"
assert frame.get_by_text("Datos del Medidor").is_visible(), "El panel de detalle deberia seguir visible en tablet"
capturar_paso(app, "tablet_768x1024_con_datos", paso_excel=5)

app.set_viewport_size({"width": 375, "height": 667})
app.wait_for_timeout(1000)
scroll_x_mobile = app.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
assert scroll_x_mobile <= 5, f"La pantalla desborda horizontalmente en mobile (375x667): {scroll_x_mobile}px de scroll"
assert frame.get_by_text("Datos del Medidor").is_visible(), "El panel de detalle deberia seguir visible en mobile"
capturar_paso(app, "mobile_375x667_con_datos", paso_excel=6)
'''

# Mensaje real confirmado con cliente inexistente (09999999) - distinto de
# lo que sugiere el nombre del caso ("no es tipo maximetro"): en RF-04 la
# pantalla acepta CUALQUIER tipo de medidor sin filtrar por maximetro (un
# cliente normal como 1495133 carga perfecto, sin rechazo) - el mensaje
# real aplica quien NO tiene NINGUN registro en lectu.
CUERPOS_REALES["CP054"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator('input[aria-label="N.° de Cliente"]').fill("09999999")
frame.locator('input[aria-label="DV"]').first.fill("9")
app.wait_for_timeout(500)
capturar_paso(app, "cliente_inexistente_ingresado", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Buscar\\s*$")).click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=8000)
assert resultado and "no se encontr" in resultado.lower() and "lectu" in resultado.lower(), (
    f"No se vio el mensaje esperado de registro no encontrado: {resultado!r}"
)
capturar_paso(app, "mensaje_no_encontrado_en_lectu", paso_excel=5)

boton_seleccionar = frame.get_by_role("button", name=re.compile(r"^\\s*Seleccionar\\s*$"))
assert not boton_seleccionar.is_enabled(), "No deberia poder continuar con la seleccion tras este rechazo"
'''

CUERPOS_REALES["CP057"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
campo_cli = frame.locator('input[aria-label="N.° de Cliente"]')
campo_dv_cli = frame.locator('input[aria-label="DV"]')
campo_ruta = frame.locator('input[aria-label="Ruta de Lectura"]')
campo_dv_ruta = frame.locator('input[aria-label="DV Ruta"]')

campo_cli.fill("1495133")
app.wait_for_timeout(500)
assert not campo_ruta.is_enabled() and not campo_dv_ruta.is_enabled(), "Ruta de Lectura y su DV deberian deshabilitarse al escribir en N Cliente"
capturar_paso(app, "ruta_deshabilitada_al_escribir_cliente", paso_excel=3)

campo_cli.fill("")
app.wait_for_timeout(500)
campo_ruta.fill("163530205")
app.wait_for_timeout(500)
assert not campo_cli.is_enabled() and not campo_dv_cli.is_enabled(), "N Cliente y su DV deberian deshabilitarse al escribir en Ruta de Lectura"
capturar_paso(app, "cliente_deshabilitado_al_escribir_ruta", paso_excel=4)

campo_dv_ruta.fill("0")
app.wait_for_timeout(300)
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
app.wait_for_timeout(600)
assert not campo_cli.is_enabled() and not campo_dv_cli.is_enabled() and not campo_ruta.is_enabled() and not campo_dv_ruta.is_enabled(), (
    "Los 4 campos de busqueda deberian quedar deshabilitados tras una busqueda exitosa"
)
capturar_paso(app, "los_4_campos_bloqueados_tras_busqueda", paso_excel=6)

frame.get_by_role("button", name=re.compile(r"^\\s*Cancelar\\s*$")).first.click()
app.wait_for_timeout(800)
assert campo_cli.is_enabled() and campo_cli.input_value() == "" and campo_ruta.is_enabled() and campo_ruta.input_value() == "", (
    "Los 4 campos deberian volver a estar habilitados y vacios tras Cancelar"
)
capturar_paso(app, "los_4_campos_habilitados_y_vacios", paso_excel=7)
'''

# RF-05: Verificacion De Lecturas De Facturacion. Unico campo de busqueda
# es "Suministro" (frame.locator("input").first), boton "Leer". Candidatos
# reales confirmados 07/10/2026 via SQL (cliente.tiene_cambio_medid='S'):
# - estado_facturacion='0' -> busqueda EXITOSA real: 15254 FENIX POWER PERU
#   S.A. (orden 3235263, 3 medidores reales con accion "P = REPROGRAMACION").
# - estado_facturacion='S' -> bloqueo real "Suministro en facturacion":
#   4470 METSO PERU S.A.
# Ver _exploracion/explore_01_rf05_buscar_suministro.py y memoria del
# proyecto para el resto de candidatos reusables.
CUERPOS_REALES["CP031"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
frame.locator("input").first.fill("15254")
app.wait_for_timeout(500)
capturar_paso(app, "suministro_con_cambio_medidor_ingresado", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(2500)

texto = frame.locator("body").inner_text()
assert "3235263" in texto, f"No se cargo el Nro. Orden real esperado del evento: {texto[-400:]!r}"
assert "55095741" in texto, f"No se cargaron los medidores reales del evento en la grilla: {texto[-400:]!r}"
assert "ACTICOME" in texto, f"No se cargo el Origen real esperado del evento: {texto[-400:]!r}"
capturar_paso(app, "tres_secciones_cargadas_con_evento_real", paso_excel=5)
'''

CUERPOS_REALES["CP032"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
frame.locator("input").first.fill("4470")
app.wait_for_timeout(500)
capturar_paso(app, "suministro_en_facturacion_ingresado", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
modal = frame.locator(".ant-modal")
modal.first.wait_for(state="visible", timeout=8000)
resultado = modal.first.inner_text()
capturar_paso(app, "mensaje_bloqueo_en_facturacion", paso_excel=5)
assert resultado and "facturaci" in resultado.lower() and "no podr" in resultado.lower(), (
    f"No se vio el mensaje esperado de bloqueo por facturacion: {resultado!r}"
)
modal.first.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$")).click()
app.wait_for_timeout(500)

boton_actualizar = frame.get_by_role("button", name=re.compile(r"^\\s*Actualizar\\s*$"))
assert not boton_actualizar.is_enabled(), "El boton Actualizar no deberia habilitarse: el formulario no debe habilitarse con un suministro bloqueado"
capturar_paso(app, "formulario_no_habilitado", paso_excel=6)
'''

# Selectores reales confirmados 07/10/2026 (_exploracion/explore_04_rf05_campos_editables.py)
# con el candidato 15254 (Accion="P"=Promedio): el input de "Lectura de
# Retiro {Tipo}" tiene aria-label propio y clase "fi" (editable); el de
# "Lect. Inicial {Tipo}" tiene clase "fi ro" (read-only) - la presencia de
# la clase "ro" es la señal real de no-editable en esta pantalla (NO el
# atributo HTML disabled, que Playwright reporta False en ambos casos).
CUERPOS_REALES["CP034"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
frame.locator("input").first.fill("15254")
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(2500)
capturar_paso(app, "suministro_cargado_antes_de_editar", paso_excel=3)

campo_lectura_retiro = frame.locator('input[aria-label="Lectura de Retiro Activa"]')
tabla_facturacion = frame.locator("table").nth(2)
cons_recuperado_antes = tabla_facturacion.locator("tbody tr").first.locator("td").nth(2).inner_text().strip()
assert cons_recuperado_antes in ("0.00", "0,00"), f"Se esperaba Cons. Recuperado en 0 antes de editar: {cons_recuperado_antes!r}"

campo_lectura_retiro.fill("5750,00")
campo_lectura_retiro.press("Tab")
app.wait_for_timeout(800)
capturar_paso(app, "lectura_de_retiro_ingresada", paso_excel=4)

cons_recuperado_despues = tabla_facturacion.locator("tbody tr").first.locator("td").nth(2).inner_text().strip()
assert cons_recuperado_despues not in ("0.00", "0,00", ""), (
    f"Se esperaba que Consumo Recuperado se recalculara automaticamente al salir del campo, sigue en: {cons_recuperado_despues!r}"
)
capturar_paso(app, "consumo_recuperado_calculado_automaticamente", paso_excel=5)
'''

CUERPOS_REALES["CP037"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
frame.locator("input").first.fill("15254")
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(2500)
capturar_paso(app, "desktop_1920x1080", paso_excel=4)

app.set_viewport_size({"width": 768, "height": 1024})
app.wait_for_timeout(1000)
scroll_x = app.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
assert scroll_x <= 5, f"La pantalla desborda horizontalmente en tablet (768x1024): {scroll_x}px de scroll"
capturar_paso(app, "tablet_768x1024", paso_excel=5)

app.set_viewport_size({"width": 375, "height": 667})
app.wait_for_timeout(1000)
scroll_x_mobile = app.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
assert scroll_x_mobile <= 5, f"La pantalla desborda horizontalmente en mobile (375x667): {scroll_x_mobile}px de scroll"
capturar_paso(app, "mobile_375x667", paso_excel=6)
'''

CUERPOS_REALES["CP056"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
peticiones_modificar = []
app.on("request", lambda r: peticiones_modificar.append(r.url) if "ModificarLecturaFacturacion" in r.url else None)

frame.locator("input").first.fill("15254")
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(2500)
capturar_paso(app, "suministro_cargado_sin_modificar_nada", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Actualizar\\s*$")).click()
modal = frame.locator(".ant-modal")
modal.first.wait_for(state="visible", timeout=8000)
resultado = modal.first.inner_text()
capturar_paso(app, "mensaje_sin_modificaciones", paso_excel=5)
assert resultado and "no ha habido modificaciones" in resultado.lower(), (
    f"No se vio el mensaje esperado de sin modificaciones: {resultado!r}"
)
modal.first.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$")).click()
app.wait_for_timeout(500)

assert not peticiones_modificar, f"No deberia haberse llamado al endpoint de actualizacion, pero se llamo: {peticiones_modificar!r}"
'''

# Candidato sin cambio de medidor confirmado 07/10/2026 (cliente.tiene_cambio_medid='N',
# estado_facturacion='0'): suministro "3" (TAMAYO LOREDO MARIA JUDITH AMANDA).
CUERPOS_REALES["CP033"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
frame.locator("input").first.fill("3")
app.wait_for_timeout(500)
capturar_paso(app, "suministro_sin_cambio_medidor_ingresado", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
modal = frame.locator(".ant-modal")
modal.first.wait_for(state="visible", timeout=8000)
resultado = modal.first.inner_text()
capturar_paso(app, "mensaje_sin_cambio_medidor", paso_excel=5)
assert resultado and "no ha tenido cambio" in resultado.lower(), (
    f"No se vio el mensaje esperado de ausencia de cambio de medidor: {resultado!r}"
)
modal.first.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$")).click()
app.wait_for_timeout(500)

boton_actualizar = frame.get_by_role("button", name=re.compile(r"^\\s*Actualizar\\s*$"))
assert not boton_actualizar.is_enabled(), "El boton Actualizar no deberia habilitarse: las secciones de correccion no deben habilitarse sin un evento de cambio de medidor"
capturar_paso(app, "secciones_no_habilitadas", paso_excel=6)
'''

# Candidato con Accion='C' (Cambio) confirmado 07/10/2026
# (_exploracion/explore_05_cp033_y_acciones.py): 24869 ORYGEN PERU S.A.A.,
# sus 3 tipos de medidor (Activa/Activa HP/Reactiva) traen Accion='C'.
# Contraste con 15254 (Accion='P'=Promedio), ya confirmado de solo lectura
# en CP034/exploracion. La clase CSS "ro" es la señal real de no-editable
# en esta pantalla (ver nota en CP034 mas arriba).
CUERPOS_REALES["CP035"] = '''
app, frame = abrir_rf05(page, paso_excel=1)

frame.locator("input").first.fill("15254")
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(2500)
capturar_paso(app, "suministro_accion_promedio_cargado", paso_excel=3)

campos_no_editables = frame.locator("table").nth(1).locator("tbody tr").first.locator("input")
for i in range(1, campos_no_editables.count()):
    clase = campos_no_editables.nth(i).get_attribute("class") or ""
    assert "ro" in clase.split(), f"El campo de solo lectura (indice {i}) de Medidores a Instalar deberia tener clase ro: {clase!r}"

lect_inicial_promedio = frame.locator('input[aria-label="Lect. Inicial Activa"]')
clase_promedio = lect_inicial_promedio.get_attribute("class") or ""
assert "ro" in clase_promedio.split(), (
    f"Con Accion=Promedio (P), Lect. Inicial deberia permanecer en solo lectura, clase real: {clase_promedio!r}"
)
capturar_paso(app, "lect_inicial_solo_lectura_con_promedio", paso_excel=6)

frame.get_by_role("button", name=re.compile(r"^\\s*Cancelar\\s*$")).click()
app.wait_for_timeout(800)

frame.locator("input").first.fill("24869")
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(2500)
capturar_paso(app, "suministro_accion_cambio_cargado", paso_excel=5)

lect_inicial_cambio = frame.locator('input[aria-label="Lect. Inicial Activa"]')
clase_cambio = lect_inicial_cambio.get_attribute("class") or ""
assert "ro" not in clase_cambio.split(), (
    f"Con Accion=Cambio (C), Lect. Inicial deberia habilitarse para edicion, clase real: {clase_cambio!r}"
)
capturar_paso(app, "lect_inicial_editable_con_cambio", paso_excel=6)
'''

# CP036 ESCRIBE DATOS REALES (autorizado por el usuario 07/10/2026): usa
# 15254, que YA tiene una correccion previa vigente (Rol Ultima
# Modificacion="FPGP", confirmado en CP031/034) - cumple la precondicion
# de la matriz "suministro con correcciones previas" sin necesitar otro
# candidato. El nuevo valor de Lectura de Retiro se calcula EN VIVO
# (vigente + 50) en vez de hardcodear un numero fijo - asi el caso sigue
# siendo idempotente en corridas futuras, sin importar que valor haya
# quedado vigente de una corrida anterior. Aplica el patron de
# captura-antes-de-cerrar (gotcha #11) para evidenciar el modal real
# antes de que cerrar_ventana_validacion lo haria desaparecer.
CUERPOS_REALES["CP036"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
frame.locator("input").first.fill("15254")
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(2500)
capturar_paso(app, "suministro_con_correccion_previa_cargado", paso_excel=3)

campo_lectura_retiro = frame.locator('input[aria-label="Lectura de Retiro Activa"]')
valor_anterior = campo_lectura_retiro.input_value()
numero_anterior = float(valor_anterior.replace(".", "").replace(",", "."))
nuevo_valor = f"{numero_anterior + 50:.2f}".replace(".", ",")
campo_lectura_retiro.fill(nuevo_valor)
campo_lectura_retiro.press("Tab")
app.wait_for_timeout(800)
capturar_paso(app, "nuevo_valor_lectura_retiro_ingresado", paso_excel=4)

frame.get_by_role("button", name=re.compile(r"^\\s*Actualizar\\s*$")).click()
modal = frame.locator(".ant-modal")
modal.first.wait_for(state="visible", timeout=10000)
resultado = modal.first.inner_text()
capturar_paso(app, "mensaje_lectura_corregida_registros_historicos", paso_excel=5)
assert resultado and "corregida correctamente" in resultado.lower() and "marcados como" in resultado.lower(), (
    f"No se vio el mensaje esperado de correccion guardada con historicos: {resultado!r}"
)
modal.first.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$")).click()
app.wait_for_timeout(2500)

campo_lectura_retiro_recargado = frame.locator('input[aria-label="Lectura de Retiro Activa"]')
valor_recargado = campo_lectura_retiro_recargado.input_value()
assert valor_recargado.strip() == nuevo_valor, (
    f"Tras la recarga automatica, se esperaba que Lectura de Retiro quede en el valor recien ingresado ({nuevo_valor}) como registro vigente: {valor_recargado!r} (anterior: {valor_anterior!r})"
)
capturar_paso(app, "registro_vigente_confirmado_tras_recarga", paso_excel=6)
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
