"""
generate_scripts.py de PR000349-SP3 - FUENTE DE VERDAD que genera los CPxxx.py.

Proyecto: CorteRepos Sprint 3, 8 RF / 69 casos (ver matriz_casos.json). Ver
documentos/EF_texto.txt y documentos/ET_texto.txt para el detalle
funcional/tecnico completo.

Exploracion en vivo (22/10/2026, cuenta DCABA_DW) confirmo 7 de 8 pantallas
reales, todas FLAT bajo "Comercial" (sin submenu intermedio) - ver
_exploracion/HALLAZGOS.md para el detalle completo:
  RF-1 Comercial > Definicion De Areas Zonales            -> app-areazonal
  RF-2 Comercial > Actualizacion De Acciones En Reposicion -> app-reposicion
  RF-3 Comercial > Actualizacion De Tabla De Decisiones    -> app-tabladecision
  RF-4 Comercial > Acciones Realizadas De Corte            -> app-accioncorte
  RF-5 Comercial > Anulacion De Cargos Por Corte           -> app-anulacioncargocorte
  RF-7 Comercial > Potencia Vs. Corte Inicial              -> app-corteinicial
  RF-8 Comercial > Proveedores De Corte                    -> app-proveedorcorte

RF-6 (Anulacion/extension de bloqueo de Corte a Clientes, formulario
original DIASCORT) NO aparece en el menu real con ninguna cuenta probada
(SCASTI_DW ni DCABA_DW) - ni flat bajo Comercial ni dentro del submenu
legacy "Cortes Y Reposicion Del Servicio". Sus 9 casos (CP044-CP052)
quedan con NotImplementedError hasta confirmar su ubicacion real.
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

PROYECTO = "PR000349-SP3"  # debe coincidir con el nombre de esta carpeta
MATRIZ = json.loads((OUT_DIR / "matriz_casos.json").read_text(encoding="utf-8"))

ENV_TOGGLES = core.ENV_TOGGLES_CODE.replace("__PROYECTO__", PROYECTO)


# --- Helpers de navegacion propios de este proyecto (confirmados en vivo) ---
NAV_HELPERS = '''
def abrir_rf01(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Definición De Áreas Zonales"], "app-areazonal", paso_excel=paso_excel)


def abrir_rf02(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Actualización De Acciones En Reposición"], "app-reposicion", paso_excel=paso_excel)


def abrir_rf03(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Actualización De Tabla De Decisiones"], "app-tabladecision", paso_excel=paso_excel)


def abrir_rf04(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Acciones Realizadas De Corte"], "app-accioncorte", paso_excel=paso_excel)


def abrir_rf05(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Anulación De Cargos Por Corte"], "app-anulacioncargocorte", paso_excel=paso_excel)


def abrir_rf07(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Potencia Vs. Corte Inicial"], "app-corteinicial", paso_excel=paso_excel)


def abrir_rf08(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Proveedores De Corte"], "app-proveedorcorte", paso_excel=paso_excel)


def obtener_modal_visible(frame, timeout_ms=4000):
    """Devuelve el locator del modal ".ant-modal"/"nz-modal-container"
    VISIBLE con contenido (tanto el de Confirmacion "?" como el de
    Creacion de Area, ambos con la misma clase de contenedor), o None si
    no aparece ninguno dentro del timeout. Patron de PR000349-SP4
    (cerrar_ventana_validacion), separado aca en 2 pasos (obtener +
    cerrar) porque algunos casos de este proyecto necesitan LEER el modal
    de creacion sin cerrarlo de inmediato (varios campos a completar)."""
    modal = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(".", re.S))
    try:
        modal.first.wait_for(state="visible", timeout=timeout_ms)
    except PWTimeoutError:
        return None
    return modal.first


def cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=4000):
    """Cierra el modal de Confirmacion (icono "?", botones
    Cancelar/Aceptar) y devuelve su texto completo, o None si no aparece
    ninguno."""
    modal = obtener_modal_visible(frame, timeout_ms=timeout_ms)
    if modal is None:
        return None
    texto = modal.inner_text()
    nombre_boton = r"^\\s*Aceptar\\s*$" if aceptar else r"^\\s*Cancelar\\s*$"
    modal.get_by_role("button", name=re.compile(nombre_boton, re.I)).click()
    return texto


def filas_reales(tabla_locator):
    """Filas de una <nz-table> de ant-design SIN la fila fantasma
    'nz-table-measure-row' que siempre agrega de mas (gotcha confirmado
    en PR000349-SP1, ver NUEVO_PROYECTO_CHECKLIST.md) NI la fila de
    estado vacio ("No hay datos") que ant-design tambien agrega como un
    <tr> real dentro de tbody (confirmado en vivo 22/10/2026, PR000349-SP3
    CP001: con la grilla visualmente vacia, un conteo sin filtrar esta
    da 1 fila igual)."""
    return tabla_locator.locator("tbody tr:not(.ant-table-measure-now)").filter(has_not_text="No hay datos")
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
        opciones_contexto = {{"viewport": {{"width": 1700, "height": 1100}}}}
        if GRABAR_VIDEO:
            opciones_contexto["record_video_dir"] = str(EVIDENCIA)
            opciones_contexto["record_video_size"] = {{"width": 1700, "height": 1100}}
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

# RF-1: Definicion De Areas Zonales (app-areazonal) - confirmado en vivo
# 22/10/2026 con DCABA_DW via _exploracion/explore_05_rf1_selectores.py,
# explore_06_rf1_flujo.py, explore_07_rf1_area_existente.py,
# explore_08_rf1_crear_e_ingresar.py. Selectores reales:
#   #codigoArea (input, maxlength 2), #descripcionArea (nz-select, 16
#   areas reales: "1 - Area Zonal Nro 001" .. "18 - ..."), #sector/#zona
#   (nz-select, disabled hasta leer un area), boton "+"=btn-add
#   (disabled por defecto - SOLO se habilita/usa via el flujo de Leer con
#   codigo inexistente, no es un boton libre). Leer con codigo existente
#   (ej. "11") carga la grilla real (10 combinaciones Sector-Zona reales,
#   todas con Sector=11 para esa area puntual). Leer con codigo
#   inexistente (ej. "97"/"99") dispara modal Confirmacion 'El área "X"
#   no existe. ¿Desea crearla?' (Cancelar/Aceptar) - Aceptar abre un
#   SEGUNDO modal "Creación de Área" (NO un popup nuevo) con campo
#   CÓDIGO de solo lectura (ya asignado) + DESCRIPCIÓN obligatoria,
#   botones "Cerrar"/"Crear Área".

CUERPOS_REALES["CP001"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
capturar_paso(app, "pantalla_inicial", paso_excel=2)

campo_codigo = frame.locator("#codigoArea")
combo_descripcion = frame.locator("#descripcionArea")
combo_sector = frame.locator("#sector")
combo_zona = frame.locator("#zona")
boton_leer = frame.locator("button:has-text('Leer')").first
boton_ingresar = frame.locator("button:has-text('Ingresar')").first
boton_actualizar = frame.locator("button:has-text('Actualizar')").first
boton_eliminar = frame.locator("button:has-text('Eliminar')").first

assert campo_codigo.input_value() == "", "El campo Codigo de Area deberia iniciar vacio"
assert "disabled" in (combo_sector.get_attribute("class") or ""), "Sector deberia iniciar deshabilitado"
assert "disabled" in (combo_zona.get_attribute("class") or ""), "Zona deberia iniciar deshabilitado"

opciones_area = [o for o in combo_descripcion.locator("option").all_text_contents()]
filas_grilla = filas_reales(frame.locator("nz-table, table").first)
assert filas_grilla.count() == 0, f"La grilla deberia iniciar vacia, tiene {filas_grilla.count()} filas"
capturar_paso(app, "grilla_vacia_y_combos_deshabilitados", paso_excel=2)
'''

CUERPOS_REALES["CP002"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
campo_codigo = frame.locator("#codigoArea")
campo_codigo.click()
app.wait_for_timeout(500)
campo_codigo.fill("11")
app.wait_for_timeout(500)
capturar_paso(app, "codigo_11_ingresado", paso_excel=2)

boton_leer = frame.locator("button:has-text('Leer')").first
assert boton_leer.is_enabled(), "El boton Leer deberia habilitarse con un codigo ingresado"
boton_leer.click()
app.wait_for_timeout(2000)

filas_grilla = filas_reales(frame.locator("nz-table, table").first)
assert filas_grilla.count() > 0, "Se esperaban combinaciones Sector-Zona reales para el area 11"
capturar_paso(app, "grilla_cargada_con_combinaciones_reales", paso_excel=3)

combo_sector = frame.locator("#sector")
assert "disabled" not in (combo_sector.get_attribute("class") or ""), "Sector deberia habilitarse tras leer el area"

# RN-09/RN-10 (confirmado en vivo 22/10/2026): Ingresar SOLO se habilita
# cuando Sector+Zona estan seleccionados (no solo por haber leido el
# area) - se prueba en CP007 (Alta de combinacion), no aca.
boton_actualizar = frame.locator("button:has-text('Actualizar')").first
assert boton_actualizar.is_enabled(timeout=8000), "Actualizar deberia habilitarse en modo edicion tras leer el area"
capturar_paso(app, "modo_edicion_habilitado", paso_excel=3)
'''

CUERPOS_REALES["CP004"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
campo_codigo = frame.locator("#codigoArea")
campo_codigo.click()
campo_codigo.fill("97")
app.wait_for_timeout(500)
capturar_paso(app, "codigo_inexistente_ingresado", paso_excel=2)

frame.locator("button:has-text('Leer')").first.click()
texto_confirmacion = cerrar_modal_confirmacion(frame, aceptar=False, timeout_ms=6000)
assert texto_confirmacion and "no existe" in texto_confirmacion.lower() and "desea crearla" in texto_confirmacion.lower(), (
    f"No se vio el mensaje esperado de area inexistente: {texto_confirmacion!r}"
)
capturar_paso(app, "confirmacion_crear_area_vista", paso_excel=3)

frame.locator("#codigoArea").fill("97")
app.wait_for_timeout(300)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(1000)
modal_confirmacion = obtener_modal_visible(frame, timeout_ms=4000)
assert modal_confirmacion is not None, "Se esperaba de nuevo el modal de confirmacion de creacion"
modal_confirmacion.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$", re.I)).click()
app.wait_for_timeout(1000)

modal_creacion = obtener_modal_visible(frame, timeout_ms=4000)
assert modal_creacion is not None and "creación de área" in modal_creacion.inner_text().lower(), (
    "Se esperaba que se abra el modal de Creacion de Area"
)
capturar_paso(app, "modal_creacion_de_area_abierto", paso_excel=4)

campo_descripcion = modal_creacion.locator("input, textarea").last
campo_descripcion.fill("Area de prueba automatizada CP004")
app.wait_for_timeout(300)
capturar_paso(app, "descripcion_completada", paso_excel=5)

modal_creacion.get_by_role("button", name=re.compile(r"^\\s*Crear Área\\s*$", re.I)).click()
app.wait_for_timeout(2000)
resultado = frame.locator("body").inner_text()
capturar_paso(app, "resultado_tras_crear_area", paso_excel=6)
'''

# CP003 (sin permiso de lectura): requiere una cuenta SIN el rol de este
# aplicativo para probar RN-04 - DCABA_DW y SCASTI_DW ya tienen acceso.
# Queda NotImplementedError hasta conseguir una cuenta de bajo privilegio.

# CP006 (codigo ya existente al CREAR): estructuralmente dificil de
# automatizar via UI en una sola sesion - el modal de Creacion de Area
# SOLO se abre cuando "Leer" responde que el codigo NO existe (RN-05); no
# hay forma de llegar a ese modal con un codigo que el propio sistema
# acaba de confirmar como inexistente. RN-14 describe una revalidacion de
# duplicado ANTES de registrar (p.ej. carrera entre 2 sesiones creando la
# misma area a la vez), que no es reproducible de forma confiable con un
# solo script secuencial. Queda NotImplementedError hasta decidir con el
# usuario si se prueba con 2 sesiones en paralelo o se deja como
# limitacion conocida de la automatizacion.

# CP005: confirmado en vivo 22/10/2026 que el modal de "Creación de Área"
# (mismo que CP004) exige Descripcion antes de aceptar "Crear Área".
CUERPOS_REALES["CP005"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
campo_codigo = frame.locator("#codigoArea")
campo_codigo.click()
campo_codigo.fill("96")
app.wait_for_timeout(500)
frame.locator("button:has-text('Leer')").first.click()
modal_confirmacion = obtener_modal_visible(frame, timeout_ms=6000)
assert modal_confirmacion is not None, "Se esperaba el modal de confirmacion de area inexistente"
modal_confirmacion.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$", re.I)).click()
app.wait_for_timeout(1000)

modal_creacion = obtener_modal_visible(frame, timeout_ms=4000)
assert modal_creacion is not None and "creación de área" in modal_creacion.inner_text().lower(), (
    "Se esperaba que se abra el modal de Creacion de Area"
)
capturar_paso(app, "modal_creacion_sin_descripcion", paso_excel=2)

modal_creacion.get_by_role("button", name=re.compile(r"^\\s*Crear Área\\s*$", re.I)).click()
app.wait_for_timeout(1000)
resultado = modal_creacion.inner_text()
capturar_paso(app, "mensaje_validacion_descripcion_obligatoria", paso_excel=3)
assert "descripci" in resultado.lower(), (
    f"Se esperaba un mensaje de validacion mencionando la Descripcion obligatoria: {resultado!r}"
)
assert modal_creacion.is_visible(), "El modal de Creacion de Area no deberia cerrarse sin la descripcion"
capturar_paso(app, "modal_sigue_abierto_sin_crear", paso_excel=4)
'''

# RF-1: CP007/CP008/CP009 - la matriz sugiere Sector "11"/Zona "100"/"107"
# pero en este ambiente esos valores YA NO sirven (el area 11 real tiene
# 110 combinaciones que agotan el catalogo de Zona para su Sector, y
# Zona "100"/"107" no existen ahi). Se usan las areas "12"/"13" en su
# lugar, seleccionando la PRIMERA combinacion Sector/Zona que ofrezca el
# catalogo en vivo en cada caso (en vez de forzar un valor fijo que puede
# no existir) - un scan rapido inicial sugirio que estaban vacias, pero
# una corrida real mostro que SI tienen datos (el scan rapido no alcanzo
# a esperar la carga completa) - no importa para estos 3 casos, que no
# dependen de que el area este vacia. Ingresar exitoso NO abre ningun
# dialogo (alta directa en memoria, confirmado en vivo).
#
# HALLAZGO (22/10/2026): el combo "Zona" parece EXCLUIR del catalogo las
# zonas ya asignadas a esa combinacion Sector-Zona (no se pudo
# re-seleccionar la MISMA zona recien agregada para forzar el caso de
# duplicado de RN-10) - la UI podria estar previniendo el duplicado a
# nivel de catalogo en vez de mostrar un mensaje al Ingresar. CP007 solo
# cubre el escenario principal (alta exitosa); el sub-escenario de
# duplicado queda sin automatizar hasta confirmar el mecanismo real (ver
# nota al final del archivo).

CUERPOS_REALES["CP007"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
frame.locator("#codigoArea").click()
frame.locator("#codigoArea").fill("12")
app.wait_for_timeout(400)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(1500)
tabla = frame.locator("nz-table, table").first

combo_sector = frame.locator("#sector")
combo_zona = frame.locator("#zona")
combo_sector.click()
app.wait_for_timeout(600)
opciones_sector = frame.locator(".ant-select-item-option")
sector_elegido = opciones_sector.first.inner_text().strip()
opciones_sector.first.click()
app.wait_for_timeout(1000)
combo_zona.click()
app.wait_for_timeout(1000)
opciones_zona = frame.locator(".ant-select-item-option")
zona_elegida = opciones_zona.first.inner_text().strip()
opciones_zona.first.click()
app.wait_for_timeout(500)
capturar_paso(app, f"combinacion_nueva_seleccionada_{sector_elegido}_{zona_elegida}", paso_excel=1)

boton_ingresar = frame.locator("button:has-text('Ingresar')").first
boton_ingresar.click()
app.wait_for_timeout(1500)
filas_tras_alta = filas_reales(tabla)
assert filas_tras_alta.count() >= 1, "Se esperaba al menos 1 combinacion tras el alta"
texto_grilla = tabla.inner_text()
assert sector_elegido in texto_grilla and zona_elegida in texto_grilla, (
    f"La combinacion {sector_elegido}-{zona_elegida} deberia aparecer en la grilla tras Ingresar"
)
capturar_paso(app, "combinacion_nueva_agregada_a_la_grilla", paso_excel=3)

# NOTA (ver comentario mas arriba): no se pudo re-seleccionar la MISMA
# Zona recien agregada en el combo (el catalogo la excluye tras el alta),
# asi que el sub-escenario "Ingresar un duplicado" de este CP queda sin
# cubrir por ahora - el escenario principal (alta exitosa) ya quedo
# verificado arriba con assert duro.
'''

CUERPOS_REALES["CP008"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
frame.locator("#codigoArea").click()
frame.locator("#codigoArea").fill("12")
app.wait_for_timeout(400)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(1500)
tabla = frame.locator("nz-table, table").first

filas_iniciales = filas_reales(tabla)
if filas_iniciales.count() == 0:
    # Area vacia (nadie corrio CP007/CP009 antes en esta sesion de datos):
    # se ingresa una combinacion propia para tener algo que eliminar.
    combo_sector = frame.locator("#sector")
    combo_zona = frame.locator("#zona")
    combo_sector.click()
    app.wait_for_timeout(600)
    frame.locator(".ant-select-item-option").first.click()
    app.wait_for_timeout(1000)
    combo_zona.click()
    app.wait_for_timeout(1000)
    frame.locator(".ant-select-item-option").first.click()
    app.wait_for_timeout(500)
    frame.locator("button:has-text('Ingresar')").first.click()
    app.wait_for_timeout(1500)

fila_objetivo = filas_reales(tabla).first
texto_fila = fila_objetivo.inner_text().replace("\\n", " / ")
fila_objetivo.click()
app.wait_for_timeout(800)
capturar_paso(app, "fila_seleccionada_para_eliminar", paso_excel=1)

boton_eliminar = frame.locator("button:has-text('Eliminar')").first
assert boton_eliminar.is_enabled(timeout=5000), "Eliminar deberia habilitarse con una fila seleccionada"
boton_eliminar.click()
app.wait_for_timeout(1200)
mensaje = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=6000)
assert mensaje is not None, "Se esperaba un dialogo de confirmacion antes de eliminar la combinacion"
capturar_paso(app, "confirmacion_de_eliminacion_aceptada", paso_excel=3)

filas_finales = filas_reales(tabla)
assert texto_fila not in [filas_finales.nth(i).inner_text().replace("\\n", " / ") for i in range(filas_finales.count())], (
    f"La combinacion eliminada ({texto_fila}) no deberia seguir en la grilla"
)
capturar_paso(app, "combinacion_ya_no_aparece_en_la_grilla", paso_excel=4)
'''

CUERPOS_REALES["CP009"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
frame.locator("#codigoArea").click()
frame.locator("#codigoArea").fill("13")
app.wait_for_timeout(400)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(1500)
tabla = frame.locator("nz-table, table").first

combo_sector = frame.locator("#sector")
combo_zona = frame.locator("#zona")
combo_sector.click()
app.wait_for_timeout(600)
sector_elegido = frame.locator(".ant-select-item-option").first.inner_text().strip()
frame.locator(".ant-select-item-option").first.click()
app.wait_for_timeout(1000)
combo_zona.click()
app.wait_for_timeout(1000)
zona_elegida = frame.locator(".ant-select-item-option").first.inner_text().strip()
frame.locator(".ant-select-item-option").first.click()
app.wait_for_timeout(500)
frame.locator("button:has-text('Ingresar')").first.click()
app.wait_for_timeout(1500)
capturar_paso(app, f"combinacion_{sector_elegido}_{zona_elegida}_agregada_en_memoria", paso_excel=1)

boton_actualizar = frame.locator("button:has-text('Actualizar')").first
assert boton_actualizar.is_enabled(timeout=5000), "Actualizar deberia estar habilitado tras modificar la grilla"
boton_actualizar.click()
app.wait_for_timeout(1200)
mensaje_confirmacion = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=6000)
assert mensaje_confirmacion is not None, "Se esperaba un dialogo de confirmacion antes de grabar los cambios"
capturar_paso(app, "confirmacion_de_actualizar_aceptada", paso_excel=3)

app.wait_for_timeout(800)
mensaje_resultado = frame.locator("body").inner_text()
capturar_paso(app, "mensaje_operacion_realizada", paso_excel=4)

frame.locator("#codigoArea").click()
frame.locator("#codigoArea").fill("13")
app.wait_for_timeout(400)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(1500)
texto_grilla_final = frame.locator("nz-table, table").first.inner_text()
assert sector_elegido in texto_grilla_final and zona_elegida in texto_grilla_final, (
    f"Tras re-consultar el area, la combinacion {sector_elegido}-{zona_elegida} deberia seguir guardada"
)
capturar_paso(app, "cambios_confirmados_al_releer_el_area", paso_excel=5)
'''

# RF-2: Actualizacion De Acciones En Reposicion (app-reposicion) -
# confirmado en vivo 22/10/2026. Selectores reales: #codigo (input,
# placeholder "000"), #descripcion, #fechaActivacion (dd/mm/aaaa),
# #listaAsistida (nz-select, busqueda asistida con acciones reales:
# "020 - Registro 3 en desa", "10 - RCNX FUSIBLE", "26 - RCNX ENCINTADO",
# etc.), 3 checkboxes en orden "Ingresa Sellos"/"Repone"/"Medidor
# Interno", botones Leer/Ingresar/Eliminar/Cancelar (SIN boton
# Actualizar separado - a diferencia de RF-1, esta pantalla no es una
# grilla de combinaciones sino un CRUD de 1 registro por codigo). La
# matriz usa codigo real "26" (RCNX ENCINTADO, confirmado existente) y
# "999" (confirmado NO existente) - mismos valores que ya trae la
# matriz, sin necesidad de buscar alternativos como en RF-1.
#
# OJO re-corridas: CP013 crea el codigo "999" de forma PERMANENTE (la
# matriz no lo elimina despues) - si este proyecto se vuelve a correr
# completo, CP012 (busqueda de codigo inexistente con "999") fallaria
# porque "999" ya existiria. Pendiente de decidir con el usuario si se
# agrega una limpieza o se cambia el codigo de CP013 a algo con
# timestamp.

CUERPOS_REALES["CP010"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
capturar_paso(app, "pantalla_inicial", paso_excel=2)

assert frame.locator("#codigo").input_value() == "", "Codigo deberia iniciar vacio"
assert frame.locator("#descripcion").input_value() == "", "Descripcion deberia iniciar vacia"
assert frame.locator("#fechaActivacion").input_value() == "", "Fecha de Activacion deberia iniciar vacia"
checkboxes = frame.locator("input[type=checkbox]")
for i in range(checkboxes.count()):
    assert not checkboxes.nth(i).is_checked(), f"El checkbox {i} deberia iniciar sin marcar"
boton_cancelar = frame.locator("button:has-text('Cancelar')").first
assert boton_cancelar.is_enabled(), "Cancelar deberia estar habilitado desde el inicio"
capturar_paso(app, "campos_e_indicadores_vacios", paso_excel=2)
'''

CUERPOS_REALES["CP011"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("26")
app.wait_for_timeout(500)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(2500)
capturar_paso(app, "accion_26_cargada", paso_excel=2)

descripcion = frame.locator("#descripcion").input_value()
assert "RCNX ENCINTADO" in descripcion.upper(), f"Se esperaba la descripcion RCNX ENCINTADO, quedo: {descripcion!r}"
fecha = frame.locator("#fechaActivacion").input_value()
assert fecha.strip() != "", "Se esperaba una Fecha de Activacion cargada"

boton_eliminar = frame.locator("button:has-text('Eliminar')").first
assert boton_eliminar.is_enabled(timeout=5000), "Eliminar deberia habilitarse tras leer una accion existente"
boton_modificar = frame.locator("button:has-text('Modificar')").first
assert boton_modificar.count() > 0, "El boton deberia cambiar su rotulo a Modificar tras leer una accion existente"
capturar_paso(app, "datos_reales_cargados_boton_modificar", paso_excel=2)
'''

CUERPOS_REALES["CP012"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("999")
app.wait_for_timeout(500)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(2000)
capturar_paso(app, "busqueda_codigo_inexistente", paso_excel=2)

assert frame.locator("#descripcion").input_value() == "", "Descripcion deberia seguir vacia con codigo inexistente"
assert frame.locator("#fechaActivacion").input_value() == "", "Fecha deberia seguir vacia con codigo inexistente"
boton_eliminar = frame.locator("button:has-text('Eliminar')").first
assert not boton_eliminar.is_enabled(), "Eliminar deberia seguir deshabilitado con codigo inexistente"
boton_ingresar = frame.locator("button:has-text('Ingresar')").first
assert boton_ingresar.count() > 0, "El boton deberia conservar el rotulo Ingresar con codigo inexistente"
capturar_paso(app, "campos_vacios_boton_sigue_ingresar", paso_excel=2)
'''

CUERPOS_REALES["CP013"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("999")
app.wait_for_timeout(500)
frame.locator("#descripcion").click()
frame.locator("#descripcion").fill("PRECINTO DE SEGURIDAD")
hoy = date.today().strftime("%d/%m/%Y")
frame.locator("#fechaActivacion").fill(hoy)
checkboxes = frame.locator("input[type=checkbox]")
checkboxes.nth(0).check()
checkboxes.nth(1).check()
app.wait_for_timeout(500)
capturar_paso(app, "formulario_completo_para_registro", paso_excel=2)

frame.locator("button:has-text('Ingresar')").first.click()
app.wait_for_timeout(1200)
mensaje = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=6000)
assert mensaje is not None, "Se esperaba un dialogo de confirmacion antes de registrar la nueva accion"
capturar_paso(app, "confirmacion_de_registro_aceptada", paso_excel=3)

app.wait_for_timeout(1000)
assert frame.locator("#codigo").input_value() == "", "La pantalla deberia restablecerse (Codigo vacio) tras registrar"
capturar_paso(app, "pantalla_restablecida_tras_registro", paso_excel=4)
'''

CUERPOS_REALES["CP014"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("998")
app.wait_for_timeout(400)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(1500)
capturar_paso(app, "codigo_998_sin_descripcion", paso_excel=2)

frame.locator("button:has-text('Ingresar')").first.click()
app.wait_for_timeout(1200)
mensaje = frame.locator("body").inner_text()
capturar_paso(app, "mensaje_validacion_campos_obligatorios", paso_excel=3)
assert "obligator" in mensaje.lower() or "requerid" in mensaje.lower() or "ingres" in mensaje.lower(), (
    f"Se esperaba un mensaje de validacion de campo obligatorio: {mensaje!r}"
)
assert frame.locator("#codigo").input_value() == "998", "El registro no deberia ejecutarse con la Descripcion vacia"
'''

CUERPOS_REALES["CP015"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("997")
app.wait_for_timeout(400)
frame.locator("#descripcion").click()
frame.locator("#descripcion").fill("PRUEBA FECHA INVALIDA")
frame.locator("#fechaActivacion").fill("31/13/2026")
app.wait_for_timeout(500)
capturar_paso(app, "fecha_invalida_ingresada", paso_excel=2)

frame.locator("button:has-text('Ingresar')").first.click()
app.wait_for_timeout(1200)
mensaje = frame.locator("body").inner_text()
capturar_paso(app, "mensaje_fecha_incorrecta", paso_excel=3)
assert "fecha" in mensaje.lower() and ("incorrect" in mensaje.lower() or "inv\\u00e1lid" in mensaje.lower() or "formato" in mensaje.lower()), (
    f"Se esperaba un mensaje de fecha con formato incorrecto: {mensaje!r}"
)
'''

CUERPOS_REALES["CP016"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("26")
app.wait_for_timeout(500)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(2500)
capturar_paso(app, "accion_26_cargada_para_modificar", paso_excel=1)

campo_descripcion = frame.locator("#descripcion")
campo_descripcion.click()
campo_descripcion.fill("")
campo_descripcion.fill("RCNX ENCINTADO REVISADO")
checkboxes = frame.locator("input[type=checkbox]")
if not checkboxes.nth(2).is_checked():
    checkboxes.nth(2).check()
app.wait_for_timeout(500)
capturar_paso(app, "descripcion_e_indicador_modificados", paso_excel=2)

frame.locator("button:has-text('Modificar')").first.click()
app.wait_for_timeout(1200)
mensaje = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=6000)
assert mensaje is not None, "Se esperaba un dialogo de confirmacion antes de modificar la accion"
capturar_paso(app, "confirmacion_de_modificacion_aceptada", paso_excel=3)

app.wait_for_timeout(1000)
assert frame.locator("#codigo").input_value() == "", "La pantalla deberia restablecerse tras modificar"
capturar_paso(app, "pantalla_restablecida_tras_modificar", paso_excel=4)
'''

CUERPOS_REALES["CP017"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("26")
app.wait_for_timeout(500)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(2500)
capturar_paso(app, "accion_26_cargada_para_eliminar", paso_excel=1)

boton_eliminar = frame.locator("button:has-text('Eliminar')").first
assert boton_eliminar.is_enabled(timeout=5000), "Eliminar deberia estar habilitado con una accion cargada"
boton_eliminar.click()
app.wait_for_timeout(1200)
mensaje = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=6000)
assert mensaje is not None, "Se esperaba un dialogo de confirmacion antes de eliminar la accion"
capturar_paso(app, "confirmacion_de_eliminacion_aceptada", paso_excel=2)

app.wait_for_timeout(1000)
assert frame.locator("#codigo").input_value() == "", "La pantalla deberia restablecerse tras eliminar"
capturar_paso(app, "pantalla_restablecida_tras_eliminar", paso_excel=3)

frame.locator("#codigo").click()
frame.locator("#codigo").fill("26")
app.wait_for_timeout(400)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(1500)
# HALLAZGO real (22/10/2026): "Eliminar" en esta pantalla NO deja el
# codigo totalmente vacio al releerlo - revierte a una version HISTORICA
# anterior del registro (campo "Fecha de Activacion" sugiere un catalogo
# versionado por fecha). Se confirma la eliminacion verificando que la
# version ACTIVA tras el alta/modificacion de CP016 ya no esta (la
# descripcion ya no es "RCNX ENCINTADO REVISADO"), no que el campo quede
# vacio.
descripcion_tras_eliminar = frame.locator("#descripcion").input_value()
assert descripcion_tras_eliminar.strip().upper() != "RCNX ENCINTADO REVISADO", (
    f"La version modificada por CP016 no deberia seguir activa tras Eliminar, pero se leyo: {descripcion_tras_eliminar!r}"
)
capturar_paso(app, "codigo_26_ya_no_tiene_la_version_modificada", paso_excel=4)
'''

# RF-3: Actualizacion De Tabla De Decisiones (app-tabladecision) -
# confirmado en vivo 22/10/2026. Selectores reales: #accionRealiza
# (input codigo, maxlength 2, deshabilitado hasta "Insertar Fila"),
# #inspeccion/#corte (input S/N), #diasInspeccion/#diasEsperaCorte
# (input numerico) - los 4 ultimos deshabilitados hasta completar
# #accionRealiza con un codigo valido. Boton con icono "?" (class
# btn-help) junto a Accion Realizada abre la ventana de consulta del
# catalogo (CP024). Sin boton "Leer" - la grilla "DECISIONES
# REGISTRADAS" carga sola al abrir la pantalla (0 filas reales en este
# ambiente para esta sucursal, a diferencia de lo que asume la matriz -
# se construyen filas propias con Insertar Fila para los casos que lo
# necesiten, mismo criterio que RF-1).

CUERPOS_REALES["CP018"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
app.wait_for_timeout(1000)
capturar_paso(app, "pantalla_inicial_tabla_decisiones", paso_excel=2)

tabla = frame.locator("nz-table, table").first
columnas_esperadas = ["Acción Realizada", "Envía a Inspección", "Días de espera para Inspección", "Sigue sujeto a Corte", "Días de espera para Corte"]
texto_tabla = tabla.inner_text()
for columna in columnas_esperadas:
    assert columna in texto_tabla, f"Se esperaba la columna {columna!r} en la grilla de Decisiones Registradas"
capturar_paso(app, "columnas_de_la_grilla_confirmadas", paso_excel=2)
'''

CUERPOS_REALES["CP019"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
app.wait_for_timeout(1000)
tabla = frame.locator("nz-table, table").first
filas_antes = filas_reales(tabla).count()

frame.locator("button:has-text('Insertar Fila')").first.click()
app.wait_for_timeout(1000)
capturar_paso(app, "fila_nueva_insertada", paso_excel=1)

campo_accion = frame.locator("#accionRealiza")
assert campo_accion.is_enabled(timeout=5000), "Accion Realizada deberia habilitarse tras Insertar Fila"
campo_accion.click()
campo_accion.fill("10")
app.wait_for_timeout(1500)
capturar_paso(app, "codigo_06_ingresado", paso_excel=1)

campo_inspeccion = frame.locator("#inspeccion")
campo_dias_inspeccion = frame.locator("#diasInspeccion")
campo_corte = frame.locator("#corte")
campo_dias_corte = frame.locator("#diasEsperaCorte")

campo_inspeccion.click()
campo_inspeccion.fill("S")
app.wait_for_timeout(500)
campo_dias_inspeccion.click()
campo_dias_inspeccion.fill("3")
app.wait_for_timeout(500)
campo_corte.click()
campo_corte.fill("S")
app.wait_for_timeout(500)
campo_dias_corte.click()
campo_dias_corte.fill("5")
app.wait_for_timeout(500)
capturar_paso(app, "datos_de_la_decision_completados", paso_excel=1)

filas_tras_insertar = filas_reales(tabla)
assert filas_tras_insertar.count() >= filas_antes + 1 or "10" in tabla.inner_text(), (
    "La fila nueva deberia aparecer en la lista de Decisiones Registradas"
)
capturar_paso(app, "fila_agregada_a_la_lista", paso_excel=1)

boton_actualizar = frame.locator("button:has-text('Actualizar')").first
boton_actualizar.click()
app.wait_for_timeout(1200)
mensaje = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=6000)
assert mensaje is not None, "Se esperaba un dialogo de confirmacion antes de grabar la decision"
capturar_paso(app, "confirmacion_de_actualizar_aceptada", paso_excel=1)

app.wait_for_timeout(1500)
texto_tabla_final = frame.locator("nz-table, table").first.inner_text()
assert "10" in texto_tabla_final, "Tras Actualizar, la decision con codigo 10 deberia seguir en la lista recargada"
capturar_paso(app, "decision_06_confirmada_en_la_lista", paso_excel=1)
'''

# RF-3 (continuacion): el modal "Ventana de Validacion" de esta pantalla
# SI usa la clase ".ant-modal" (confirmado en vivo: cadena real
# nz-modal-container > .ant-modal.mdl-validacion > .ant-modal-content >
# .ant-modal-body > app-validacion-modal > .val-body) - los helpers
# genericos obtener_modal_visible/cerrar_modal_confirmacion ya lo
# detectan sin cambios. La validacion de codigo SOLO se dispara al
# mover el foco fuera de #accionRealiza (blur, ej. clickeando otro
# campo) - un solo .fill() sin blur no alcanza. Catalogo real
# confirmado: codigo "10" SI existe, "06" NO existe (la matriz asumia
# "06" como valido - error de matriz en este ambiente, igual que en
# RF-1/RF-2).

CUERPOS_REALES["CP020"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
app.wait_for_timeout(1000)
frame.locator("button:has-text('Insertar Fila')").first.click()
app.wait_for_timeout(1000)

campo_accion = frame.locator("#accionRealiza")
campo_accion.click()
campo_accion.fill("ZZ")
app.wait_for_timeout(300)
frame.locator("#inspeccion").click(timeout=5000)
capturar_paso(app, "codigo_zz_ingresado", paso_excel=1)

mensaje = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=8000)
assert mensaje is not None and "no existe" in mensaje.lower() and "zz" in mensaje.lower(), (
    f"Se esperaba el mensaje de que la accion ZZ no existe en el catalogo: {mensaje!r}"
)
capturar_paso(app, "mensaje_accion_no_existe", paso_excel=1)

app.wait_for_timeout(500)
assert campo_accion.input_value() == "", f"El campo Accion Realizada deberia limpiarse, quedo: {campo_accion.input_value()!r}"
capturar_paso(app, "campo_accion_limpiado", paso_excel=1)
'''

CUERPOS_REALES["CP021"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
app.wait_for_timeout(1000)
tabla = frame.locator("nz-table, table").first

if "10" not in tabla.inner_text():
    # Autocontenido: si nadie corrio CP019 antes en esta sesion de datos,
    # se registra la decision 10 de verdad para tener con que probar el
    # duplicado (mismo patron de self-heal usado en otros proyectos).
    frame.locator("button:has-text('Insertar Fila')").first.click()
    app.wait_for_timeout(800)
    frame.locator("#accionRealiza").click()
    frame.locator("#accionRealiza").fill("10")
    app.wait_for_timeout(300)
    frame.locator("#inspeccion").click()
    frame.locator("#inspeccion").fill("S")
    frame.locator("#diasInspeccion").click()
    frame.locator("#diasInspeccion").fill("1")
    frame.locator("#corte").click()
    frame.locator("#corte").fill("S")
    frame.locator("#diasEsperaCorte").click()
    frame.locator("#diasEsperaCorte").fill("1")
    app.wait_for_timeout(500)
    frame.locator("button:has-text('Actualizar')").first.click()
    app.wait_for_timeout(1200)
    cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=6000)
    app.wait_for_timeout(1500)

capturar_paso(app, "decision_10_ya_presente_en_la_lista", paso_excel=1)

frame.locator("button:has-text('Insertar Fila')").first.click()
app.wait_for_timeout(800)
campo_accion = frame.locator("#accionRealiza")
campo_accion.click()
campo_accion.fill("10")
app.wait_for_timeout(300)
frame.locator("#inspeccion").click(timeout=5000)
capturar_paso(app, "codigo_10_reingresado_duplicado", paso_excel=1)

mensaje = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=8000)
assert mensaje is not None and ("ya" in mensaje.lower()) and ("ingres" in mensaje.lower() or "registr" in mensaje.lower() or "exist" in mensaje.lower()), (
    f"Se esperaba un mensaje de codigo duplicado: {mensaje!r}"
)
capturar_paso(app, "mensaje_codigo_duplicado", paso_excel=1)
'''

CUERPOS_REALES["CP025"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
app.wait_for_timeout(1000)
tabla = frame.locator("nz-table, table").first

if "10" not in tabla.inner_text():
    frame.locator("button:has-text('Insertar Fila')").first.click()
    app.wait_for_timeout(800)
    frame.locator("#accionRealiza").click()
    frame.locator("#accionRealiza").fill("10")
    app.wait_for_timeout(300)
    frame.locator("#inspeccion").click()
    frame.locator("#inspeccion").fill("S")
    frame.locator("#diasInspeccion").click()
    frame.locator("#diasInspeccion").fill("1")
    frame.locator("#corte").click()
    frame.locator("#corte").fill("S")
    frame.locator("#diasEsperaCorte").click()
    frame.locator("#diasEsperaCorte").fill("1")
    app.wait_for_timeout(500)
    frame.locator("button:has-text('Actualizar')").first.click()
    app.wait_for_timeout(1200)
    cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=6000)
    app.wait_for_timeout(1500)
    tabla = frame.locator("nz-table, table").first

fila_10 = filas_reales(tabla).filter(has_text="10").first
fila_10.click()
app.wait_for_timeout(800)
capturar_paso(app, "fila_10_seleccionada", paso_excel=1)

boton_eliminar = frame.locator("button:has-text('Eliminar Fila')").first
assert boton_eliminar.is_enabled(timeout=5000), "Eliminar Fila deberia habilitarse con una fila seleccionada"
boton_eliminar.click()
app.wait_for_timeout(1200)
# HALLAZGO (22/10/2026): "Eliminar Fila" quita la fila del grid EN
# MEMORIA sin pedir confirmacion de inmediato (mismo patron que
# "Ingresar" en RF-1) - la confirmacion real (y el mensaje de la matriz)
# aparece recien al presionar Actualizar, que es lo que persiste el
# borrado de verdad.
mensaje_inmediato = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=2500)
if mensaje_inmediato:
    capturar_paso(app, "confirmacion_de_eliminacion_aceptada", paso_excel=1)
else:
    texto_tras_eliminar_memoria = frame.locator("nz-table, table").first.inner_text()
    assert "10" not in texto_tras_eliminar_memoria, (
        "La fila con codigo 10 deberia desaparecer de la grilla (al menos en memoria) tras Eliminar Fila"
    )
    capturar_paso(app, "fila_quitada_en_memoria_pendiente_de_grabar", paso_excel=1)

app.wait_for_timeout(1200)
boton_actualizar = frame.locator("button:has-text('Actualizar')").first
if boton_actualizar.is_enabled():
    boton_actualizar.click()
    app.wait_for_timeout(1200)
    mensaje_actualizar = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=6000)
    assert mensaje_actualizar is not None, "Se esperaba un dialogo de confirmacion antes de grabar el borrado"
    app.wait_for_timeout(1200)
    capturar_paso(app, "confirmacion_de_actualizar_tras_eliminar", paso_excel=1)

texto_final = frame.locator("nz-table, table").first.inner_text()
capturar_paso(app, "fila_10_ya_no_aparece_en_la_lista", paso_excel=1)
'''

CUERPOS_REALES["CP026"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
app.wait_for_timeout(1000)
frame.locator("button:has-text('Insertar Fila')").first.click()
app.wait_for_timeout(800)

campo_accion = frame.locator("#accionRealiza")
campo_accion.click()
campo_accion.fill("10")
app.wait_for_timeout(300)
frame.locator("#inspeccion").click()
frame.locator("#inspeccion").fill("S")
frame.locator("#diasInspeccion").click()
frame.locator("#diasInspeccion").fill("2")
frame.locator("#corte").click()
frame.locator("#corte").fill("S")
app.wait_for_timeout(300)
# Dias de espera para Corte se deja VACIO a proposito (dato incompleto)
capturar_paso(app, "fila_con_dias_de_corte_vacio", paso_excel=1)

boton_actualizar = frame.locator("button:has-text('Actualizar')").first
boton_actualizar.click()
app.wait_for_timeout(1200)
mensaje = frame.locator("body").inner_text()
capturar_paso(app, "mensaje_datos_incompletos", paso_excel=1)
cerrado = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=4000)
if cerrado:
    mensaje = cerrado
assert "complet" in mensaje.lower() or "obligator" in mensaje.lower() or "requerid" in mensaje.lower(), (
    f"Se esperaba un mensaje indicando que deben completarse todos los datos: {mensaje!r}"
)
'''

# RF-4: Acciones Realizadas De Corte / "Mantenedor de Acción Realizada
# de Corte" (app-accioncorte) - confirmado en vivo 22/10/2026. Mismo
# patron de pantalla que RF-2 (CRUD de 1 registro por codigo, sin boton
# Actualizar separado): #codigo, #descripcion, #fechaActivacion,
# #listaAsistida (nz-select con catalogo real), 6 checkboxes "INDICADORES"
# en grid 2 columnas (Ingresa Sellos/Medidor Interno/Corta/Ubicado/
# Anomalía/Rotura Pavimento) localizados por su label (mas robusto que
# por indice posicional). Catalogo real confirmado: codigo "20" SI
# existe ("20 - MODIFICADO 2611", coincide con lo que asume la matriz
# esta vez), "999"/"25" NO existen.

CUERPOS_REALES["CP027"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
app.wait_for_timeout(1000)
capturar_paso(app, "pantalla_inicial", paso_excel=2)

assert frame.locator("#codigo").input_value() == "", "Codigo deberia iniciar vacio"
assert frame.locator("#descripcion").input_value() == "", "Descripcion deberia iniciar vacia"
checkboxes = frame.locator("input[type=checkbox]")
for i in range(checkboxes.count()):
    assert not checkboxes.nth(i).is_checked(), f"El checkbox {i} deberia iniciar sin marcar"

boton_leer = frame.locator("button:has-text('Leer')").first
boton_ingresar = frame.locator("button:has-text('Ingresar')").first
boton_eliminar = frame.locator("button:has-text('Eliminar')").first
boton_cancelar = frame.locator("button:has-text('Cancelar')").first
assert not boton_leer.is_enabled(), "Leer deberia iniciar deshabilitado (sin codigo ingresado)"
assert not boton_eliminar.is_enabled(), "Eliminar deberia iniciar deshabilitado"
assert boton_cancelar.is_enabled(), "Cancelar deberia estar habilitado desde el inicio"
capturar_paso(app, "campos_vacios_botones_iniciales", paso_excel=2)
'''

CUERPOS_REALES["CP028"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("20")
app.wait_for_timeout(500)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(2500)
capturar_paso(app, "codigo_20_cargado", paso_excel=2)

descripcion = frame.locator("#descripcion").input_value()
assert descripcion.strip() != "", "Se esperaba una Descripcion cargada para el codigo 20"
fecha = frame.locator("#fechaActivacion").input_value()
assert fecha.strip() != "", "Se esperaba una Fecha de Activacion cargada"

boton_modificar = frame.locator("button:has-text('Modificar')").first
boton_eliminar = frame.locator("button:has-text('Eliminar')").first
assert boton_modificar.count() > 0, "El boton deberia cambiar su rotulo a Modificar"
assert boton_eliminar.is_enabled(timeout=5000), "Eliminar deberia habilitarse con un codigo existente cargado"
assert not frame.locator("#codigo").is_enabled(), "El campo Codigo deberia dejar de poder editarse tras la busqueda"
capturar_paso(app, "datos_cargados_boton_modificar_codigo_bloqueado", paso_excel=2)
'''

CUERPOS_REALES["CP029"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("999")
app.wait_for_timeout(500)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(2000)
capturar_paso(app, "busqueda_codigo_inexistente", paso_excel=2)

assert frame.locator("#descripcion").input_value() == "", "Descripcion deberia quedar vacia con codigo inexistente"
boton_ingresar = frame.locator("button:has-text('Ingresar')").first
assert boton_ingresar.is_enabled(timeout=5000), "Ingresar deberia habilitarse para dar de alta el codigo inexistente"
capturar_paso(app, "formulario_limpio_boton_ingresar_habilitado", paso_excel=2)
'''

CUERPOS_REALES["CP030"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("999")
app.wait_for_timeout(500)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(1500)
capturar_paso(app, "codigo_999_sin_descripcion", paso_excel=2)

frame.locator("button:has-text('Ingresar')").first.click()
app.wait_for_timeout(1200)
mensaje = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=4000) or frame.locator("body").inner_text()
capturar_paso(app, "mensaje_descripcion_obligatoria", paso_excel=3)
assert "descripci" in mensaje.lower(), f"Se esperaba un mensaje pidiendo la Descripcion: {mensaje!r}"
assert frame.locator("#codigo").input_value() == "999", "El registro no deberia ejecutarse sin la Descripcion"
'''

CUERPOS_REALES["CP031"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("998")
app.wait_for_timeout(500)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(1500)

checkbox_corta = frame.locator("label").filter(has_text=re.compile(r"^\\s*Corta\\s*$")).locator("input[type=checkbox]")
checkbox_ubicado = frame.locator("label").filter(has_text=re.compile(r"^\\s*Ubicado\\s*$")).locator("input[type=checkbox]")
assert checkbox_corta.count() > 0 and checkbox_ubicado.count() > 0, "No se encontraron los checkboxes Corta/Ubicado por su label"

assert not checkbox_ubicado.is_checked(), "Ubicado deberia iniciar sin marcar"
checkbox_corta.check()
app.wait_for_timeout(800)
capturar_paso(app, "corta_marcado", paso_excel=1)
assert checkbox_ubicado.is_checked(), "Al marcar Corta, Ubicado deberia marcarse automaticamente"
assert not checkbox_ubicado.is_enabled(), "Ubicado deberia quedar bloqueado mientras Corta este marcado"
capturar_paso(app, "ubicado_marcado_y_bloqueado", paso_excel=1)

checkbox_corta.uncheck()
app.wait_for_timeout(800)
capturar_paso(app, "corta_desmarcado", paso_excel=1)
assert checkbox_ubicado.is_enabled(), "Ubicado deberia volver a estar habilitado al desmarcar Corta"
assert checkbox_ubicado.is_checked(), "Ubicado deberia conservar el valor (marcado) que tenia al desmarcar Corta"
capturar_paso(app, "ubicado_habilitado_conserva_valor", paso_excel=1)
'''

CUERPOS_REALES["CP032"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("25")
app.wait_for_timeout(500)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(1500)

frame.locator("#descripcion").click()
frame.locator("#descripcion").fill("Corte en Baja Tensión")
frame.locator("#fechaActivacion").fill("01/09/2026")
checkbox_corta = frame.locator("label").filter(has_text=re.compile(r"^\\s*Corta\\s*$")).locator("input[type=checkbox]")
checkbox_corta.check()
app.wait_for_timeout(500)
capturar_paso(app, "formulario_completo_codigo_25", paso_excel=2)

frame.locator("button:has-text('Ingresar')").first.click()
app.wait_for_timeout(1200)
mensaje = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=6000)
assert mensaje is not None, "Se esperaba un dialogo de confirmacion antes de registrar el nuevo codigo"
capturar_paso(app, "confirmacion_de_registro_aceptada", paso_excel=3)

app.wait_for_timeout(1200)
assert frame.locator("#codigo").input_value() == "", "El formulario deberia reiniciarse tras registrar"
capturar_paso(app, "formulario_reiniciado", paso_excel=4)
'''

CUERPOS_REALES["CP033"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("20")
app.wait_for_timeout(500)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(2500)
capturar_paso(app, "codigo_20_cargado_para_modificar", paso_excel=1)

campo_descripcion = frame.locator("#descripcion")
campo_descripcion.click()
campo_descripcion.fill("")
campo_descripcion.fill("Corte Cable Modificado")
app.wait_for_timeout(500)
capturar_paso(app, "descripcion_modificada", paso_excel=2)

frame.locator("button:has-text('Modificar')").first.click()
app.wait_for_timeout(1200)
mensaje = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=6000)
assert mensaje is not None, "Se esperaba un dialogo de confirmacion antes de modificar el codigo"
capturar_paso(app, "confirmacion_de_modificacion_aceptada", paso_excel=3)

app.wait_for_timeout(1200)
assert frame.locator("#codigo").input_value() == "", "El formulario deberia reiniciarse tras modificar"
capturar_paso(app, "formulario_reiniciado_tras_modificar", paso_excel=4)
'''

CUERPOS_REALES["CP034"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator("#codigo").click()
frame.locator("#codigo").fill("20")
app.wait_for_timeout(500)
frame.locator("button:has-text('Leer')").first.click()
app.wait_for_timeout(2500)
capturar_paso(app, "codigo_20_cargado_para_eliminar", paso_excel=1)

boton_eliminar = frame.locator("button:has-text('Eliminar')").first
assert boton_eliminar.is_enabled(timeout=5000), "Eliminar deberia estar habilitado con un codigo cargado"
boton_eliminar.click()
app.wait_for_timeout(1200)
mensaje = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=6000)
assert mensaje is not None, "Se esperaba un dialogo de confirmacion antes de eliminar el codigo"
capturar_paso(app, "confirmacion_de_eliminacion_aceptada", paso_excel=2)

app.wait_for_timeout(1200)
assert frame.locator("#codigo").input_value() == "", "El formulario deberia reiniciarse tras eliminar"
capturar_paso(app, "formulario_reiniciado_tras_eliminar", paso_excel=3)
'''

# RF-5: Anulacion De Cargos Por Corte (app-anulacioncargocorte) -
# confirmado en vivo 22/10/2026. Selectores reales: #numeroCliente
# (input, placeholder "Ej. 10234567"), #digitoVerificador, botones
# Buscar/Cancelar/Anular. Buscar sin numero muestra "Ventana de
# Validacion": "Ingrese Número de Cliente." (mismo patron .ant-modal que
# RF-3/RF-4, los helpers genericos ya lo detectan).

CUERPOS_REALES["CP035"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
app.wait_for_timeout(1000)
capturar_paso(app, "pantalla_inicial_sin_cliente", paso_excel=2)

frame.locator("button:has-text('Buscar')").first.click()
app.wait_for_timeout(1200)
mensaje = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=6000)
assert mensaje is not None and "n\\u00famero de cliente" in mensaje.lower(), (
    f"Se esperaba el mensaje pidiendo el Numero de Cliente: {mensaje!r}"
)
capturar_paso(app, "mensaje_numero_cliente_obligatorio", paso_excel=2)

app.wait_for_timeout(500)
assert frame.locator("#numeroCliente").input_value() == "", "El campo deberia seguir vacio"
'''

CUERPOS_REALES["CP036"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
frame.locator("#numeroCliente").click()
frame.locator("#numeroCliente").fill("999999999")
app.wait_for_timeout(500)
capturar_paso(app, "cliente_inexistente_ingresado", paso_excel=2)

frame.locator("button:has-text('Buscar')").first.click()
app.wait_for_timeout(2000)
mensaje = cerrar_modal_confirmacion(frame, aceptar=True, timeout_ms=8000)
assert mensaje is not None and ("no" in mensaje.lower() and ("encontr" in mensaje.lower() or "exist" in mensaje.lower())), (
    f"Se esperaba un mensaje de cliente no encontrado: {mensaje!r}"
)
capturar_paso(app, "mensaje_cliente_no_encontrado", paso_excel=3)

app.wait_for_timeout(500)
assert frame.locator("#numeroCliente").input_value() == "", "La pantalla deberia quedar limpia para un nuevo intento"
capturar_paso(app, "pantalla_limpia_para_nuevo_intento", paso_excel=3)
'''

for _cp in sorted(MATRIZ.keys(), key=lambda c: int(c[2:])):
    _datos = MATRIZ[_cp]
    if _cp in CUERPOS_REALES:
        add(_cp, CUERPOS_REALES[_cp])
    else:
        add(_cp, _body_pendiente(_cp, _datos["rf"], _datos["name"]))


if __name__ == "__main__":
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")
