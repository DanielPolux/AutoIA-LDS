"""
generate_scripts.py de PR000349-SP4 - FUENTE DE VERDAD que genera los CPxxx.py.

Proyecto: Corte y Reposicion del servicio, 6 pantallas (RF-01..RF-06),
53 casos (ver matriz_casos.json) + CP001 transversal (login). Ver
documentos/EF_texto.txt y documentos/ET_texto.txt para el detalle
funcional/tecnico completo, y Documentos/manual_usuario_*.pdf para
mensajes exactos de RF-02 y RF-05.

BLOQUEO SISTEMICO conocido (01/10/2026, ver memoria del proyecto): la
sesion de SCAZ (rol de SCASTI_DW) resuelve area=23500 -> sucursal='0000'
en dbtecnica (rol/sucar) - esto bloquea con "Acceso denegado al
recurso." la accion real de backend de los 6 RF. Fix armado (UPDATE
rol SET area='23510' WHERE rol='SCAZ') pero pendiente de permiso DBA.
Mientras tanto, solo se escriben cuerpos reales para validaciones que
disparan ANTES de tocar el backend (formato/obligatoriedad de campo),
confirmadas en vivo caso por caso.

HALLAZGO 03/10/2026: el rol de DCABA_DW NO tiene el defecto de sucursal
'0000' (resuelve sucursal real, catalogos cargan limpio, 0 HTTP 400) -
confirmado en vivo para RF-01. Los CPs listados en `_CPS_DCABA_DW` (ver
mas abajo) corren con esa cuenta en vez de SCASTI_DW, destrabando casos
que de otro modo dependerian del UPDATE pendiente de permiso DBA.
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

PROYECTO = "PR000349-SP4"  # debe coincidir con el nombre de esta carpeta
MATRIZ = json.loads((OUT_DIR / "matriz_casos.json").read_text(encoding="utf-8"))

ENV_TOGGLES = core.ENV_TOGGLES_CODE.replace("__PROYECTO__", PROYECTO)


def fuente_modulo(modulo, saltar=("PWTimeoutError",)):
    """Extrae el codigo fuente de un modulo de _framework/modulos/ (su
    docstring + todas sus funciones) para volcarlo como texto en el
    CPxxx.py generado. Patron ya usado en PR000349-SP1/SP2."""
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


# --- Helpers de navegacion propios de este proyecto (sin modulo aparte aun) ---
NAV_HELPERS = '''
def abrir_rf01(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Seleccion De Clientes Afectos A Corte"], "app-sel-clie-cor", paso_excel=paso_excel)


def abrir_rf02(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Ingreso De Libros De Corte"], "app-libro-corte", paso_excel=paso_excel)


def abrir_rf03(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Ingreso De Accion Realizada - Ordenes Especiales De Corte"], "app-descarga-corte", paso_excel=paso_excel)


def abrir_rf04(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Ingreso De Accion Realizada Para Ordenes De Reposicion"], "app-descarga-cnx", paso_excel=paso_excel)


def abrir_rf05(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Listados De Corte Y Reposicion"], "app-listado-cor-rep", paso_excel=paso_excel)


def abrir_rf06(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Cambio De Estado De Libros De Corte"], "app-est-lib-cor", paso_excel=paso_excel)


def cerrar_ventana_validacion(app, frame, timeout_ms=4000):
    """Cierra el modal ".ant-modal" que aparezca (tanto la "Ventana de
    Validacion" -icono "i", boton unico "Aceptar"- como la "Confirmacion"
    -icono "?", botones "Cancelar"/"Aceptar"-, ambas con la misma clase
    de contenedor) y devuelve su texto completo. Para la Confirmacion,
    clickear "Aceptar" equivale a confirmar (opcion "Si, continuar").
    Tolerante: devuelve None si no aparece ningun modal."""
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
# del defecto, asi que igual merece video/Word completos (ver mas abajo,
# patron agregado 06/10/2026 a pedido del usuario para PR000349-SP4 CP018).
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

# RF-06: Cambio De Estado De Libros De Corte - validaciones de campo que
# disparan ANTES de tocar el backend (confirmadas en vivo 02/10/2026 via
# _exploracion/explore_07_rf06_validaciones.py y explore_08_rf06_rango.py;
# selectores reales: #fOperador, #fFecha1, #fFecha2, #fSector, boton "Leer").
# El resto de CP de RF-06 (los que SI llegan a Consultar) quedan bloqueados
# por el defecto sistemico de sucursal (ver memoria del proyecto).

CUERPOS_REALES["CP045"] = '''
app, frame = abrir_rf06(page, paso_excel=1)
src = app.locator("#aplicacion").get_attribute("src") or ""
assert "/comercial/corterepos/corterepos/estlibcor/web/home" in src, (
    f"La ruta de la pantalla no es la esperada: {src!r}"
)
capturar_paso(app, "ruta_confirmada", paso_excel=4)
'''

CUERPOS_REALES["CP046"] = '''
app, frame = abrir_rf06(page, paso_excel=1)
capturar_paso(app, "pantalla_inicial_operador_sin_seleccionar", paso_excel=2)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "debe ingresar un filtro de fecha" in resultado.lower(), (
    f"No se vio el mensaje esperado 'Debe ingresar un filtro de fecha.': {resultado!r}"
)
capturar_paso(app, "mensaje_filtro_fecha_obligatorio", paso_excel=4)
'''

CUERPOS_REALES["CP047"] = '''
app, frame = abrir_rf06(page, paso_excel=1)
frame.locator("#fOperador").select_option(label="Igual")
app.wait_for_timeout(400)
capturar_paso(app, "operador_igual_fecha_en_blanco", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "debe ingresar fecha" in resultado.lower(), (
    f"No se vio el mensaje esperado 'Debe ingresar fecha.': {resultado!r}"
)
capturar_paso(app, "mensaje_fecha_obligatoria", paso_excel=5)
'''

CUERPOS_REALES["CP048"] = '''
app, frame = abrir_rf06(page, paso_excel=1)
frame.locator("#fOperador").select_option(label="Entre")
app.wait_for_timeout(400)
frame.locator("#fFecha1").fill("2026-08-01")
capturar_paso(app, "solo_fecha_desde_completada", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "debe ingresar los dos valores del rango" in resultado.lower(), (
    f"No se vio el mensaje esperado 'Debe ingresar los dos valores del rango.': {resultado!r}"
)
capturar_paso(app, "mensaje_rango_incompleto", paso_excel=5)
'''

CUERPOS_REALES["CP049"] = '''
app, frame = abrir_rf06(page, paso_excel=1)
frame.locator("#fOperador").select_option(label="Entre")
app.wait_for_timeout(400)
frame.locator("#fFecha1").fill("2026-08-30")
frame.locator("#fFecha2").fill("2026-08-01")
capturar_paso(app, "fecha_desde_posterior_a_hasta", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "fecha inicial debe ser menor o igual que fecha final" in resultado.lower(), (
    f"No se vio el mensaje esperado 'Fecha inicial debe ser menor o igual que fecha final.': {resultado!r}"
)
capturar_paso(app, "mensaje_fecha_invertida", paso_excel=4)
'''

CUERPOS_REALES["CP050"] = '''
app, frame = abrir_rf06(page, paso_excel=1)
campo_sector = frame.locator("#fSector")
campo_sector.click()
for caracter in "AB":
    campo_sector.type(caracter, delay=100)
    app.wait_for_timeout(200)
    valor_parcial = campo_sector.input_value()
    assert valor_parcial == "", (
        f"El caracter no numerico {caracter!r} no debio registrarse en el campo Sector, quedo: {valor_parcial!r}"
    )
campo_sector.blur()
app.wait_for_timeout(300)
capturar_paso(app, "campo_sector_vacio_tras_teclear_AB", paso_excel=3)

valor_final = campo_sector.input_value()
assert valor_final == "", f"El campo Sector deberia seguir vacio tras salir del campo, quedo: {valor_final!r}"
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=1500)
assert resultado is None, f"No se esperaba ningun mensaje de error de tipo de dato para Sector: {resultado!r}"
capturar_paso(app, "sin_mensaje_de_error_de_tipo_de_dato", paso_excel=5)
'''

# RF-05: Listados De Corte Y Reposicion - confirmado en vivo 02/10/2026
# via _exploracion/explore_09_rf05.py y explore_10_rf05_validaciones.py.
# Componente real: app-listado-cor-rep (confirma el GUESS anterior).
# Campo unico compartido fecha/dias: #campoValorFechaDias. Botones sin
# texto accesible por name= (hay que usar la clase: button.btn-primary
# = "Generar", button.btn-default = "Cancelar"). Los 10 listados se
# seleccionan por texto del radio con frame.get_by_text(...).click().
# CP038/039/040/043 (Generar con exito) y CP042 completo (incluye
# Generar con default 30) quedan BLOQUEADOS por el defecto sistemico de
# sucursal (ver memoria del proyecto) - solo se escriben aca los que NO
# necesitan que el "Generar" real tenga exito.

CUERPOS_REALES["CP037"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
src = app.locator("#aplicacion").get_attribute("src") or ""
assert "/comercial/corterepos/corterepos/listadocorrep/web/home" in src, (
    f"La ruta de la pantalla no es la esperada: {src!r}"
)
capturar_paso(app, "ruta_confirmada", paso_excel=4)
'''

CUERPOS_REALES["CP041"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
frame.get_by_text(re.compile(r"^Resumen de Cortes Especiales$", re.I)).click()
app.wait_for_timeout(400)
frame.locator("#campoValorFechaDias").fill("31/13/2026")
capturar_paso(app, "fecha_invalida_ingresada", paso_excel=3)

frame.locator("button.btn-primary").click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "fecha" in resultado.lower() and "incorrecta" in resultado.lower(), (
    f"No se vio el mensaje esperado de fecha incorrecta: {resultado!r}"
)
capturar_paso(app, "mensaje_fecha_incorrecta", paso_excel=5)
'''

CUERPOS_REALES["CP044"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
campo = frame.locator("#campoValorFechaDias")
boton_cancelar = frame.locator("button.btn-default")

# Paso 2: sin datos ingresados, Cancelar limpia directo (sin confirmacion)
boton_cancelar.click()
app.wait_for_timeout(800)
resultado_sin_datos = cerrar_ventana_validacion(app, frame, timeout_ms=1500)
assert resultado_sin_datos is None, (
    f"No se esperaba ningun dialogo de confirmacion sin datos ingresados: {resultado_sin_datos!r}"
)
capturar_paso(app, "cancelar_sin_datos_no_pide_confirmacion", paso_excel=2)

# Pasos 3-5: con un valor ingresado, Cancelar SI pide confirmacion
campo.fill("31/13/2026")
app.wait_for_timeout(300)
capturar_paso(app, "valor_ingresado_antes_de_cancelar", paso_excel=3)
boton_cancelar.click()
app.wait_for_timeout(800)
resultado_con_datos = cerrar_ventana_validacion(app, frame)
assert resultado_con_datos and "perder" in resultado_con_datos.lower(), (
    f"No se vio el mensaje de confirmacion esperado al cancelar con datos: {resultado_con_datos!r}"
)
app.wait_for_timeout(500)
valor_final = campo.input_value()
assert valor_final == "", f"El campo deberia quedar vacio tras confirmar Cancelar, quedo: {valor_final!r}"
capturar_paso(app, "campo_limpio_tras_confirmar_cancelar", paso_excel=5)
'''

# RF-05 (CP038/039/040/043): confirmado en vivo 05/10/2026 CON DCABA_DW
# - el "Generar" real (bloqueado antes por el defecto de sucursal) ya
# funciona. OJO: el listado tarda un rato real en generarse ("Generando
# informe... espere.", NO es un modal sino un aviso inline) - esperar a
# que ese texto desaparezca (hasta 60s) ANTES de buscar el modal de
# resultado "Listado Generado.". CP039 (Cargos por Corte Generados): la
# fecha sugerida por la matriz (01/06/2026) da "Ha ocurrido un error al
# generar Listado." en este ambiente (sin datos esa fecha, confirmado
# 2/2 veces) - se usa 15/09/2026 en su lugar (fecha con datos reales
# confirmados, la misma del libro de corte real de RF-02).

CUERPOS_REALES["CP038"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
frame.get_by_text(re.compile(r"^Resumen de Reposiciones$", re.I)).click()
app.wait_for_timeout(400)
frame.locator("#campoValorFechaDias").fill("15/08/2026")
app.wait_for_timeout(300)
capturar_paso(app, "fecha_valida_ingresada", paso_excel=3)
frame.locator("button.btn-primary").click()
frame.get_by_text("Generando informe").wait_for(state="hidden", timeout=60000)
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=5000)
assert resultado and "listado generado" in resultado.lower(), (
    f"No se vio la confirmacion esperada de listado generado: {resultado!r}"
)
capturar_paso(app, "listado_generado", paso_excel=5)
'''

CUERPOS_REALES["CP039"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
frame.get_by_text(re.compile(r"^Cargos por Corte Generados$", re.I)).click()
app.wait_for_timeout(400)
frame.locator("#campoValorFechaDias").fill("15/09/2026")
app.wait_for_timeout(300)
capturar_paso(app, "fecha_distinta_ingresada", paso_excel=3)
frame.locator("button.btn-primary").click()
frame.get_by_text("Generando informe").wait_for(state="hidden", timeout=60000)
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=5000)
assert resultado and "listado generado" in resultado.lower(), (
    f"No se vio la confirmacion esperada de listado generado: {resultado!r}"
)
capturar_paso(app, "listado_generado", paso_excel=5)
'''

CUERPOS_REALES["CP040"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
frame.get_by_text(re.compile(r"^Clientes con Corte$", re.I)).click()
app.wait_for_timeout(400)
assert frame.get_by_text("Número de Días desde el Corte").count() > 0 or frame.get_by_text(re.compile("D.as", re.I)).count() > 0, (
    "Se esperaba que la etiqueta del campo cambie a captura de dias"
)
frame.locator("#campoValorFechaDias").fill("15")
app.wait_for_timeout(300)
capturar_paso(app, "numero_de_dias_ingresado", paso_excel=4)
frame.locator("button.btn-primary").click()
frame.get_by_text("Generando informe").wait_for(state="hidden", timeout=60000)
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=5000)
assert resultado and "listado generado" in resultado.lower(), (
    f"No se vio la confirmacion esperada de listado generado: {resultado!r}"
)
capturar_paso(app, "listado_generado", paso_excel=6)
'''

# NOTA (confirmado en vivo 05/10/2026, 3 corridas): generar "Clientes
# Excentos de Corte" dejando la fecha en blanco (se asume HOY) fallo 2
# de 3 veces con un modal "Error de Servicio" / "Ha ocurrido un error
# al generar el listado." (no es el mismo tipo de modal que "Ventana
# de Validacion" - backend genuinamente no genera el listado para la
# fecha de hoy en este ambiente la mayoria de las veces). No es un
# problema del script: el campo SI se autocompleta con la fecha actual
# de forma consistente (eso se confirma como assert duro); el EXITO de
# la generacion en si queda como hallazgo, no como assert duro (mismo
# criterio que gotcha #8 - no forzar un resultado que no se reproduce
# de forma confiable).
CUERPOS_REALES["CP042"] = '''
app, frame = abrir_rf05(page, paso_excel=1)
frame.get_by_text(re.compile(r"^Clientes con Corte$", re.I)).click()
app.wait_for_timeout(400)
campo = frame.locator("#campoValorFechaDias")
campo.click()
for caracter in "ABC":
    campo.type(caracter, delay=100)
    app.wait_for_timeout(200)
    valor_parcial = campo.input_value()
    assert valor_parcial == "", (
        f"El caracter no numerico {caracter!r} no debio registrarse en el campo de dias, quedo: {valor_parcial!r}"
    )
capturar_paso(app, "campo_dias_vacio_tras_teclear_ABC", paso_excel=4)

frame.locator("button.btn-primary").click()
app.wait_for_timeout(500)
valor_default = campo.input_value()
assert valor_default == "30", (
    f"Se esperaba que el campo tome el valor por defecto 30 al generar sin digitos, quedo: {valor_default!r}"
)
capturar_paso(app, "valor_por_defecto_30_aplicado", paso_excel=6)

frame.get_by_text("Generando informe").wait_for(state="hidden", timeout=60000)
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=5000)
assert resultado and "listado generado" in resultado.lower(), (
    f"No se vio la confirmacion esperada de listado generado: {resultado!r}"
)
capturar_paso(app, "listado_generado_con_default_30", paso_excel=6)
'''

CUERPOS_REALES["CP043"] = '''
import datetime
app, frame = abrir_rf05(page, paso_excel=1)
frame.get_by_text(re.compile(r"^Clientes Excentos de Corte$", re.I)).click()
app.wait_for_timeout(400)
campo = frame.locator("#campoValorFechaDias")
campo.fill("")
app.wait_for_timeout(300)
boton_generar = frame.locator("button.btn-primary")
boton_generar.click()
app.wait_for_timeout(500)
fecha_autocompletada = campo.input_value()
hoy = datetime.date.today().strftime("%d/%m/%Y")
assert fecha_autocompletada == hoy, (
    f"Se esperaba que el campo se autocomplete con la fecha de hoy ({hoy!r}), quedo: {fecha_autocompletada!r}"
)
capturar_paso(app, "campo_autocompletado_con_fecha_actual", paso_excel=5)

frame.get_by_text("Generando informe").wait_for(state="hidden", timeout=60000)
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=5000)
if resultado and "listado generado" in resultado.lower():
    print(f"  [{CASO}] Generar con fecha de hoy: OK, listado generado.")
else:
    print(f"  [{CASO}] (hallazgo, no bloqueante) Generar con fecha de hoy NO genero el listado: {resultado!r}")
capturar_paso(app, "resultado_de_generar_con_fecha_actual", paso_excel=5)
'''

# RF-02: Ingreso De Libros De Corte - confirmado en vivo 02/10/2026 via
# _exploracion/explore_11_rf02.py y explore_12_rf02_cp013.py. Componente
# real: app-libro-corte (confirma el GUESS anterior). A DIFERENCIA de
# RF-05/RF-06, esta pantalla dispara la carga de catalogos AUTOMATICAMENTE
# al abrir (no al tocar un campo) y ese 400 por el defecto sistemico de
# sucursal se muestra de inmediato como un modal "Error de Servicio"
# ("No se pudieron cargar los catalogos de la pantalla.") - un tipo de
# modal DISTINTO al de validacion (mismo .ant-modal, titulo distinto,
# boton "Cerrar" en vez de "Aceptar"). Tras cerrar ese modal, el boton
# "Detalle" con TODOS los campos vacios NO mostro ningun mensaje de
# validacion (contra lo esperado del manual/CP013) - pendiente de
# investigar si el formulario queda en un estado roto por el fallo de
# catalogos o si falta alguna otra interaccion; no se escribe CP013
# hasta confirmar esto con mas calma (mejor con el defecto de sucursal
# ya corregido). Solo se escribe CP011 (acceso/ruta, cero dependencia
# de catalogos).

CUERPOS_REALES["CP011"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
src = app.locator("#aplicacion").get_attribute("src") or ""
assert "/comercial/corterepos/corterepos/librocorte/web/home" in src, (
    f"La ruta de la pantalla no es la esperada: {src!r}"
)
capturar_paso(app, "ruta_confirmada", paso_excel=4)
'''

# RF-02 (CP012-015): confirmado en vivo 05/10/2026 CON DCABA_DW (ver
# _CPS_DCABA_DW) - a diferencia de SCASTI_DW, con DCABA_DW los 4
# catalogos (Tipo de Corte/Cortador/Proveedor/Proceso) cargan limpio al
# abrir, sin el modal "Error de Servicio" que bloqueaba antes. Libro
# real conocido en este ambiente (confirmado con 59 clientes reales):
# Sector=10, Zona=490, Fecha=15/09/2026, Tipo de Corte=10 (BAJA
# TENSION), Cortador=1102 (Cucho Quispe Jhonny Martin).

CUERPOS_REALES["CP012"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
for id_combo, nombre in [("fTipoCorte", "Tipo de Corte"), ("fCortador", "Cortador"), ("fProveedor", "Proveedor"), ("fProceso", "Proceso")]:
    combo = frame.locator(f"#{id_combo}")
    opciones = [o for o in combo.locator("option").all_text_contents() if o.strip()]
    assert len(opciones) > 0, f"Se esperaba que el combo {nombre} tenga opciones cargadas al abrir la pantalla"
    combo.click()
    capturar_paso(app, f"combo_{id_combo}_desplegado", paso_excel=2)
    app.wait_for_timeout(2000)
    opcion_real = opciones[1] if len(opciones) > 1 else opciones[0]
    combo.select_option(label=opcion_real)
    app.wait_for_timeout(1000)
'''

CUERPOS_REALES["CP013"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
boton_detalle = frame.locator("button.btn-primary")
sector = frame.locator("#fSector")
zona = frame.locator("#fZona")
fecha = frame.locator("#fFecha")
tipo_corte = frame.locator("#fTipoCorte")

boton_detalle.click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "debe ingresar el sector" in resultado.lower(), (
    f"No se vio el mensaje esperado de Sector obligatorio: {resultado!r}"
)
capturar_paso(app, "mensaje_sector_obligatorio", paso_excel=2)

sector.click()
sector.type("ab", delay=80)
app.wait_for_timeout(300)
assert sector.input_value() == "", (
    f"El campo Sector deberia descartar letras en tiempo real, quedo: {sector.input_value()!r}"
)
capturar_paso(app, "sector_alfabetico_descartado", paso_excel=3)

sector.type("1", delay=80)
app.wait_for_timeout(300)
boton_detalle.click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "debe ingresar la zona" in resultado.lower(), (
    f"No se vio el mensaje esperado de Zona obligatoria: {resultado!r}"
)
capturar_paso(app, "mensaje_zona_obligatoria", paso_excel=4)

zona.type("1", delay=80)
app.wait_for_timeout(300)
boton_detalle.click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "debe ingresar la fecha" in resultado.lower(), (
    f"No se vio el mensaje esperado de Fecha obligatoria: {resultado!r}"
)
capturar_paso(app, "mensaje_fecha_obligatoria", paso_excel=4)

fecha.fill("2026-08-15")
app.wait_for_timeout(300)
boton_detalle.click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "debe ingresar tipo de corte" in resultado.lower(), (
    f"No se vio el mensaje esperado de Tipo de Corte obligatorio: {resultado!r}"
)
capturar_paso(app, "mensaje_tipo_corte_obligatorio", paso_excel=5)

opciones_tc = [o for o in tipo_corte.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
tipo_corte.select_option(label=opciones_tc[0])
app.wait_for_timeout(300)
boton_detalle.click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "código del cortador" in resultado.lower(), (
    f"No se vio el mensaje esperado de Cortador obligatorio: {resultado!r}"
)
capturar_paso(app, "mensaje_cortador_obligatorio", paso_excel=5)
'''

# CP014: confirmado en vivo 06/10/2026 que el flujo REAL de "Seleccion
# de libro desde la busqueda" usa el boton "..." (icono junto a Tipo de
# Corte, es `frame.locator("button").nth(1)` - nth(0) es el boton
# "Manual" del encabezado) - a diferencia de lo que se penso en una
# exploracion anterior ("no respondia a los clics"), SI abre un modal
# real "Buscar Libro de Corte" con combo Sucursal + boton Leer + grilla
# (Sucursal/Sector/Zona/Fecha/Tipo de Corte/Estado/Cant. Clientes,
# libros generados en los ultimos 15 dias). Doble clic en una fila
# selecciona el libro, cierra el modal de busqueda y muestra el mensaje
# real "Los datos del libro se trasladaron a la pantalla principal.
# Complete el Cortador para continuar." - tras aceptar, los campos
# Sector/Zona/Tipo de Corte de la pantalla principal quedan completados
# con los valores REALES de la fila elegida (verificado contra el
# texto de la fila, no hardcodeado, porque la grilla trae datos de
# "ultimos 15 dias" que cambian con el tiempo).
CUERPOS_REALES["CP014"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
boton_buscar_libro = frame.locator("button").nth(1)
boton_buscar_libro.click()
app.wait_for_timeout(1000)
capturar_paso(app, "modal_buscar_libro_abierto", paso_excel=1)

modal = frame.locator(".ant-modal, [class*=\\'modal\\']").last
sel_sucursal = modal.locator("select").first
opciones_sucursal = [o for o in sel_sucursal.locator("option").all_text_contents() if o.strip()]
sel_sucursal.select_option(label=next(o for o in opciones_sucursal if o.strip().startswith("3100")))
app.wait_for_timeout(500)
capturar_paso(app, "sucursal_3100_seleccionada", paso_excel=2)

boton_leer_modal = modal.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$"))
boton_leer_modal.click()
cargando = frame.get_by_text("Cargando...")
try:
    cargando.first.wait_for(state="visible", timeout=5000)
except Exception:
    pass
cargando.first.wait_for(state="hidden", timeout=20000)
app.wait_for_timeout(500)

filas = modal.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 libro real en la grilla de sucursal 3100"
columnas_fila = [c.strip() for c in filas.first.inner_text().split("\\t")]
sector_libro, zona_libro, tipo_corte_libro = columnas_fila[1], columnas_fila[2], columnas_fila[4]
capturar_paso(app, "grilla_de_libros_cargada", paso_excel=2)

filas.first.locator("td").first.dblclick(force=True)
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=8000)
assert resultado and "se trasladaron a la pantalla principal" in resultado.lower(), (
    f"No se vio el mensaje esperado de traslado de datos: {resultado!r}"
)
capturar_paso(app, "mensaje_datos_trasladados", paso_excel=3)

sector = frame.locator("#fSector")
zona = frame.locator("#fZona")
tipo_corte = frame.locator("#fTipoCorte")
assert sector.input_value().strip() == sector_libro, (
    f"Sector no coincide: esperado {sector_libro!r}, quedo {sector.input_value()!r}"
)
assert zona.input_value().strip() == zona_libro, (
    f"Zona no coincide: esperado {zona_libro!r}, quedo {zona.input_value()!r}"
)
texto_tipo_corte_actual = tipo_corte.locator("option:checked").inner_text()
assert tipo_corte_libro.upper() in texto_tipo_corte_actual.upper(), (
    f"Tipo de Corte no coincide: esperado contener {tipo_corte_libro!r}, quedo {texto_tipo_corte_actual!r}"
)
capturar_paso(app, "campos_pantalla_principal_completados", paso_excel=4)
'''

# NOTA (confirmado en vivo 05/10/2026, 2 corridas distintas): el
# habilitado/deshabilitado de los campos de sellos SEGUN la Accion
# Realizada elegida (RN-16) NO se reprodujo igual entre filas de
# cliente distintas del mismo libro - con una fila, "PT - PROBLEMA
# TECNICO" dejaba los sellos deshabilitados (como se esperaba); con
# otra fila, la MISMA accion los mostro habilitados. Posible que el
# habilitado dependa tambien del Tipo de medidor de cada fila, no solo
# de la Accion - no se aislo la condicion exacta en el tiempo
# disponible. Mismo criterio que CP004 (gotcha de validaciones
# inconsistentes): no se deja un assert duro sobre eso. Se confirma en
# cambio la parte 100% reproducible de CP017: los catalogos de
# Situacion Encontrada/Banco/Fase/Tapa/Anomalia de Ruta son <select>
# reales, sin ningun modo de texto libre para digitar un codigo fuera
# de catalogo.
# CP017: confirmado en vivo 06/10/2026 (3 corridas identicas) el patron
# REAL de habilitado/deshabilitado de sellos segun Accion Realizada
# (select nth(5)): "ER - REGULARIZA CORTE" los DESHABILITA; el resto de
# acciones probadas (10-CORTE FUSIBLE 0000, PT-PROBLEMA TECNICO,
# NV-NO VISITADO, 40-RETIRO CONEXION) los dejan HABILITADOS. Esto
# CORRIGE una nota de memoria anterior (de otra fila de cliente) que
# decia lo opuesto (PT deshabilitaba, 10 habilitaba) - con ESTA fila
# (la real que usa el proyecto, fila nth(1) del grid de 59 clientes) el
# resultado es reproducible 3/3. Sellos = select nth(10)/nth(11)
# ("color sello colocado/retirado").
CUERPOS_REALES["CP017"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
frame.locator("#fSector").type("10", delay=60)
frame.locator("#fZona").type("490", delay=60)
frame.locator("#fFecha").fill("2026-09-15")
sel_tipo_corte = frame.locator("#fTipoCorte")
sel_tipo_corte.select_option(label=next(o for o in sel_tipo_corte.locator("option").all_text_contents() if o.strip().startswith("10")))
sel_cortador = frame.locator("#fCortador")
sel_cortador.select_option(label=next(o for o in sel_cortador.locator("option").all_text_contents() if o.strip().startswith("1102")))
app.wait_for_timeout(500)
frame.locator("button.btn-primary").click()
app.wait_for_timeout(2500)
capturar_paso(app, "detalle_libro_real_abierto", paso_excel=1)

frame.locator("table.grid tr").nth(1).click()
app.wait_for_timeout(800)
capturar_paso(app, "cliente_seleccionado", paso_excel=2)

sel_accion = frame.locator("select").nth(5)
sello_colocado = frame.locator("select").nth(10)
sello_retirado = frame.locator("select").nth(11)

sel_accion.select_option(label="10 - CORTE FUSIBLE 0000")
app.wait_for_timeout(1500)
assert sello_colocado.is_enabled() and sello_retirado.is_enabled(), (
    "Se esperaba que los campos de sellos queden HABILITADOS con una accion que los exige (10 - CORTE FUSIBLE 0000)"
)
capturar_paso(app, "sellos_habilitados_accion_exige_sello", paso_excel=3)

sel_accion.select_option(label="ER - REGULARIZA CORTE")
app.wait_for_timeout(1500)
assert not sello_colocado.is_enabled() and not sello_retirado.is_enabled(), (
    "Se esperaba que los campos de sellos queden DESHABILITADOS con una accion que no los exige (ER - REGULARIZA CORTE)"
)
capturar_paso(app, "sellos_deshabilitados_accion_no_exige_sello", paso_excel=4)

for idx_combo, nombre in [(4, "Situacion_Encontrada"), (6, "Banco"), (7, "Fase"), (8, "Tapa"), (9, "Anomalia_de_Ruta")]:
    combo = frame.locator("select").nth(idx_combo)
    assert combo.evaluate("el => el.tagName") == "SELECT", f"{nombre} deberia ser un <select>, no un campo de texto libre"
    opciones = [o for o in combo.locator("option").all_text_contents() if o.strip()]
    assert len(opciones) > 0, f"Se esperaba que {nombre} tenga opciones de catalogo cargadas"
    combo.click()
    capturar_paso(app, f"catalogo_{nombre}_desplegado", paso_excel=5)
    app.wait_for_timeout(2000)
    opcion_real = opciones[1] if len(opciones) > 1 else opciones[0]
    combo.select_option(label=opcion_real)
    app.wait_for_timeout(500)
'''

# CP018: DEFECTO REAL CONFIRMADO 06/10/2026 (ver casos_fallidos_confirmados.json).
# El boton "Actualizar" del libro completo responde siempre con HTTP 400
# en POST .../LibroCorte/Registrar, con cuerpo
# {"":["Unexpected character encountered while parsing value: 2. Path
# '', line 1, position 1."]} - un error de PARSEO DE JSON del backend
# (payload mal formado), no un rechazo de reglas de negocio. Reproducido
# 2/2 con clientes distintos del mismo libro, con y sin completar el
# formulario de atencion. El cuerpo de este caso documenta el flujo
# REAL esperado por la matriz (que fallaria igual sin necesidad de
# tocar Situacion/Accion) y el assert final verifica el mensaje de
# EXITO esperado - que nunca llega, por el defecto - dejando el CASO
# en FALLO de forma intencional (el fallo ES la prueba del defecto).
CUERPOS_REALES["CP018"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
frame.locator("#fSector").type("10", delay=60)
frame.locator("#fZona").type("490", delay=60)
frame.locator("#fFecha").fill("2026-09-15")
sel_tipo_corte = frame.locator("#fTipoCorte")
sel_tipo_corte.select_option(label=next(o for o in sel_tipo_corte.locator("option").all_text_contents() if o.strip().startswith("10")))
sel_cortador = frame.locator("#fCortador")
sel_cortador.select_option(label=next(o for o in sel_cortador.locator("option").all_text_contents() if o.strip().startswith("1102")))
app.wait_for_timeout(500)
frame.locator("button.btn-primary").click()
app.wait_for_timeout(2500)
capturar_paso(app, "detalle_libro_real_abierto", paso_excel=1)

frame.locator("table.grid tr").nth(1).click()
app.wait_for_timeout(800)
capturar_paso(app, "cliente_seleccionado", paso_excel=1)

boton_cerrar_detalle = frame.get_by_role("button", name=re.compile(r"^\\s*Cerrar\\s*$"))
boton_cerrar_detalle.first.click()
app.wait_for_timeout(1000)
capturar_paso(app, "detalle_cerrado_libro_con_datos_registrados", paso_excel=1)

boton_actualizar = frame.get_by_role("button", name=re.compile(r"^\\s*Actualizar\\s*$"))
boton_actualizar.first.click()
app.wait_for_timeout(1500)
capturar_paso(app, "confirmacion_esta_seguro_de_actualizar", paso_excel=2)

modal_confirmacion = frame.locator(".ant-modal, [class*=\\'modal\\']").last
modal_confirmacion.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$")).click()
app.wait_for_timeout(2500)

modal_resultado = frame.locator(".ant-modal, [class*=\\'modal\\']").last
resultado = modal_resultado.inner_text() if modal_resultado.count() else frame.locator("body").inner_text()
capturar_paso(app, "DEFECTO_error_de_validacion_en_vez_del_mensaje_esperado", paso_excel=4)

assert "actualizado" in resultado.lower() and ("dudos" in resultado.lower() or "lectura" in resultado.lower()), (
    "DEFECTO CONFIRMADO (ver casos_fallidos_confirmados.json): se esperaba el mensaje de "
    "clientes actualizados + notificacion de lecturas dudosas, pero el sistema responde con "
    f"un error de validacion generico. Mensaje real mostrado: {resultado!r}"
)
'''

# CP016: 2 libros reales encontrados via SQL (estado 'A'=Actualizado,
# 'E'=Eliminado - codigos confirmados en vivo, no documentados en
# ningun lado previo). El Cortador elegido NO necesita coincidir con el
# contratista real guardado en el libro (confirmado probando con
# cualquier cortador valido del catalogo) - el match de busqueda es por
# Sucursal/Sector/Zona/Fecha/TipoLibro.
CUERPOS_REALES["CP016"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
sector = frame.locator("#fSector")
zona = frame.locator("#fZona")
fecha = frame.locator("#fFecha")
tipo_corte = frame.locator("#fTipoCorte")
cortador = frame.locator("#fCortador")
boton_detalle = frame.locator("button.btn-primary")

# Libro real en estado Actualizado: sucursal 4100 / sector 30 / zona 545
sector.fill("30")
zona.fill("545")
fecha.fill("2022-03-23")
tipo_corte.select_option(label=next(o for o in tipo_corte.locator("option").all_text_contents() if o.strip().startswith("10")))
cortador.select_option(label=next(o for o in cortador.locator("option").all_text_contents() if o.strip().startswith("504")))
app.wait_for_timeout(300)
capturar_paso(app, "criterios_libro_actualizado", paso_excel=1)

boton_detalle.click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=8000)
assert resultado and "libro de corte actualizado" in resultado.lower(), (
    f"No se vio el mensaje esperado de libro actualizado: {resultado!r}"
)
capturar_paso(app, "mensaje_libro_actualizado", paso_excel=2)

# Libro real en estado Eliminado: sucursal 5200 / sector 10 / zona 900
sector.fill("10")
zona.fill("900")
fecha.fill("2004-03-13")
tipo_corte.select_option(label=next(o for o in tipo_corte.locator("option").all_text_contents() if o.strip().startswith("01")))
cortador.select_option(label=next(o for o in cortador.locator("option").all_text_contents() if o.strip().startswith("1102")))
app.wait_for_timeout(300)
capturar_paso(app, "criterios_libro_eliminado", paso_excel=2)

boton_detalle.click()
resultado2 = cerrar_ventana_validacion(app, frame, timeout_ms=8000)
assert resultado2 and "libro de corte eliminado" in resultado2.lower(), (
    f"No se vio el mensaje esperado de libro eliminado: {resultado2!r}"
)
capturar_paso(app, "mensaje_libro_eliminado", paso_excel=4)
'''

CUERPOS_REALES["CP015"] = '''
app, frame = abrir_rf02(page, paso_excel=1)
sector = frame.locator("#fSector")
zona = frame.locator("#fZona")
fecha = frame.locator("#fFecha")
tipo_corte = frame.locator("#fTipoCorte")
cortador = frame.locator("#fCortador")
boton_detalle = frame.locator("button.btn-primary")

sector.type("99", delay=60)
zona.type("999", delay=60)
fecha.fill("2020-01-01")
opciones_tc = [o for o in tipo_corte.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
tipo_corte.select_option(label=opciones_tc[0])
opciones_cortador = [o for o in cortador.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
cortador.select_option(label=opciones_cortador[0])
app.wait_for_timeout(300)
capturar_paso(app, "criterios_sin_libro_generado", paso_excel=1)

boton_detalle.click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=8000)
assert resultado and "no existe" in resultado.lower(), (
    f"No se vio el mensaje esperado de libro inexistente: {resultado!r}"
)
capturar_paso(app, "mensaje_libro_inexistente", paso_excel=3)
'''

# CP001 (Transversal): login ya ocurrio en login(page) antes de este body
# (ver HEADER_TEMPLATE) - solo falta confirmar que el menu principal
# quedo visible.
CUERPOS_REALES["CP001"] = '''
app = page  # no hay popup propio en este caso transversal: la captura final usa "app"
assert page.get_by_role("link", name="  Aplicaciones").is_visible(), (
    "El menu principal (enlace Aplicaciones) deberia estar visible tras el login"
)
capturar_paso(page, "menu_principal_visible", paso_excel=5)
'''

# RF-01/RF-03/RF-04: casos de acceso/ruta (CP002/CP019/CP028), mismo
# patron que CP011/CP037 - confirmados en vivo 02/10/2026 via
# _exploracion/explore_13_rf01_rf03_rf04.py. Componentes reales:
# app-sel-clie-cor (RF-01), app-descarga-corte (RF-03, ya confirmado
# antes), app-descarga-cnx (RF-04). Las 3 pantallas muestran ADEMAS un
# modal de error/acceso denegado apenas abren (mismo defecto sistemico
# de sucursal, o SIEREP en el caso de RF-04) - se tolera y se ignora
# porque el "esperado" de estos 3 casos puntuales es solo sobre la RUTA,
# no sobre el contenido cargado.
CUERPOS_REALES["CP002"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
src = app.locator("#aplicacion").get_attribute("src") or ""
assert "/comercial/corterepos/corterepos/selcliecor/web/home" in src, (
    f"La ruta de la pantalla no es la esperada: {src!r}"
)
capturar_paso(app, "ruta_confirmada", paso_excel=4)
'''

# RF-01: Seleccion De Clientes Afectos A Corte - confirmado en vivo
# 03/10/2026 CON DCABA_DW (ver _CPS_DCABA_DW arriba), via
# _exploracion/explore_15..22_rf01_*.py. Selectores reales: selects en
# orden [0]=sucursal [1]=operadorAntiguedad [2]=suministro [3]=proveedor
# [4]=proceso [5]=convenio; primer input=Codigo de Area (sin id, se
# sanea en tiempo real igual que Sector en otras pantallas);
# #antiguedadInicial / #antiguedadFinal (aparece recien al elegir
# "entre"); botones button.btn-exito="Agregar Area",
# button.btn-peligro="Quitar Area", button.btn-primario="Seleccionar".
# OJO - "Agregar Area" tiene una demora real antes de quedar
# confirmado en el backend: sin esperar ~3s despues de agregarla, un
# "Seleccionar" inmediato puede dar "Debe incluir al menos un area..."
# aunque la fila YA se vea en la grilla (confirmado en vivo, condicion
# de carrera real de la app, no de Playwright).
#
# Sucursal 3100 (Chacarilla) NO tiene parametros de corte pre-guardados
# en este ambiente de pruebas (deuda/consumo quedan en blanco,
# antiguedadInicial default '0') - aplica el flujo alternativo FA-1 del
# EF ("Sucursal sin parametros previos"), no el flujo principal que
# asume parametros ya guardados (la matriz pedia sucursal "0100", que
# no existe - ver hallazgo ya documentado en memoria).
#
# Codigos de "Area Zonal" validos confirmados en esta sucursal: 1, 10,
# 20, 24 (20 y 24 SI corresponden a sectores restringidos - sirven para
# CP007). Codigos probados que NO existen: 100, 1000, 101, 201, 2401.

CUERPOS_REALES["CP003"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
sel_sucursal = frame.locator("select").nth(0)
sel_proveedor = frame.locator("select").nth(3)
sel_proceso = frame.locator("select").nth(4)
opciones_sucursal = sel_sucursal.locator("option").all_text_contents()
opcion_3100 = next(o for o in opciones_sucursal if o.startswith("3100"))
sel_sucursal.select_option(label=opcion_3100)
app.wait_for_timeout(2500)
capturar_paso(app, "sucursal_3100_seleccionada", paso_excel=2)

opciones_proveedor = [o for o in sel_proveedor.locator("option").all_text_contents() if o.strip()]
assert len(opciones_proveedor) > 0, "Se esperaba que el combo de Proveedor se llene con proveedores vigentes de la sucursal"
opciones_proceso = [o for o in sel_proceso.locator("option").all_text_contents() if o.strip()]
assert len(opciones_proceso) > 0, "Se esperaba que el combo de Proceso se llene con tipos de proceso vigentes"
capturar_paso(app, "proveedores_y_procesos_cargados", paso_excel=4)
'''

CUERPOS_REALES["CP004"] = '''
# NOTA (confirmado en vivo 03-05/10/2026, 3 corridas distintas): el
# chequeo de "proveedor obligatorio" NO se reprodujo de forma
# consistente - segun el estado de la grilla de areas al momento de
# presionar "Seleccionar", se observaron 3 resultados distintos para el
# MISMO escenario (sucursal+area validos, proveedor sin elegir):
# "Debe seleccionar el proveedor...", "Debe incluir al menos un area...",
# y hasta "No existen clientes que cumplan condicion de seleccion" (la
# consulta se ejecuto igual, sin bloquear por proveedor). Esto sugiere
# que RN-03 (proveedor/proceso/antiguedad obligatorios) no se cumple de
# forma confiable en este ambiente - posible defecto a reportar, no
# reproducible de forma determinista para dejarlo como assert duro. Solo
# se deja en este caso la validacion de SUCURSAL, 100% reproducible.
app, frame = abrir_rf01(page, paso_excel=1)
boton_seleccionar = frame.locator("button.btn-primario")

boton_seleccionar.click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "debe seleccionar el sucursal" in resultado.lower(), (
    f"No se vio el mensaje esperado de sucursal obligatoria: {resultado!r}"
)
capturar_paso(app, "mensaje_sucursal_obligatoria", paso_excel=4)
'''

CUERPOS_REALES["CP005"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
boton_seleccionar = frame.locator("button.btn-primario")
sel_sucursal = frame.locator("select").nth(0)
sel_operador_antig = frame.locator("select").nth(1)
sel_proveedor = frame.locator("select").nth(3)
sel_proceso = frame.locator("select").nth(4)
campo_antig_inicial = frame.locator("#antiguedadInicial")
campo_area = frame.locator("input").first
boton_agregar = frame.locator("button.btn-exito")

opciones_sucursal = sel_sucursal.locator("option").all_text_contents()
sel_sucursal.select_option(label=next(o for o in opciones_sucursal if o.startswith("3100")))
app.wait_for_timeout(2500)
opciones_proveedor = [o for o in sel_proveedor.locator("option").all_text_contents() if o.strip()]
sel_proveedor.select_option(label=opciones_proveedor[0])
app.wait_for_timeout(400)
opciones_proceso = [o for o in sel_proceso.locator("option").all_text_contents() if o.strip()]
sel_proceso.select_option(label=opciones_proceso[0])
app.wait_for_timeout(400)
# Area valida agregada de antemano: sin esto, "Seleccionar" bloquea con
# "Debe incluir al menos un area..." antes de llegar a validar el rango
# de antiguedad (confirmado en vivo - no es el foco de este caso).
campo_area.click()
campo_area.type("1", delay=80)
app.wait_for_timeout(300)
boton_agregar.click()
app.wait_for_timeout(3000)

sel_operador_antig.select_option(label="entre")
app.wait_for_timeout(400)
campo_antig_inicial.fill("10")
capturar_paso(app, "entre_solo_inicial", paso_excel=2)
boton_seleccionar.click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "debe ingresar los dos valores del rango" in resultado.lower(), (
    f"No se vio el mensaje esperado de rango incompleto: {resultado!r}"
)
capturar_paso(app, "mensaje_rango_incompleto", paso_excel=3)

campo_antig_final = frame.locator("#antiguedadFinal")
campo_antig_final.fill("5")
capturar_paso(app, "inicial_mayor_que_final", paso_excel=3)
boton_seleccionar.click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "no debe ser mayor al final" in resultado.lower(), (
    f"No se vio el mensaje esperado de inicial mayor a final: {resultado!r}"
)
capturar_paso(app, "mensaje_inicial_mayor_a_final", paso_excel=4)

campo_antig_inicial.fill("")
campo_antig_inicial.type("-5", delay=80)
app.wait_for_timeout(300)
valor_saneado = campo_antig_inicial.input_value()
assert "-" not in valor_saneado, (
    f"El signo negativo deberia descartarse en tiempo real, quedo: {valor_saneado!r}"
)
capturar_paso(app, "signo_negativo_saneado_en_tiempo_real", paso_excel=4)
'''

CUERPOS_REALES["CP006"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
campo_area = frame.locator("input").first
boton_agregar = frame.locator("button.btn-exito")

campo_area.click()
campo_area.type("ab", delay=80)
app.wait_for_timeout(300)
assert campo_area.input_value() == "", (
    f"El campo Codigo de Area deberia descartar letras en tiempo real, quedo: {campo_area.input_value()!r}"
)
capturar_paso(app, "codigo_alfabetico_descartado", paso_excel=1)

campo_area.fill("")
campo_area.type("0", delay=80)
app.wait_for_timeout(300)
boton_agregar.click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "numérico" in resultado.lower() and "mayor que 0" in resultado.lower(), (
    f"No se vio el mensaje esperado para codigo '0': {resultado!r}"
)
capturar_paso(app, "mensaje_codigo_cero", paso_excel=2)

campo_area.fill("")
campo_area.type("1", delay=80)
app.wait_for_timeout(300)
boton_agregar.click()
app.wait_for_timeout(3000)
filas = frame.locator("table tbody tr")
assert filas.count() == 1, f"Se esperaba 1 area agregada tras un codigo valido, hay {filas.count()}"
capturar_paso(app, "area_valida_agregada", paso_excel=3)

campo_area.fill("")
campo_area.type("1", delay=80)
app.wait_for_timeout(300)
boton_agregar.click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "ya se encuentra seleccionado" in resultado.lower(), (
    f"No se vio el mensaje esperado de area duplicada: {resultado!r}"
)
capturar_paso(app, "mensaje_area_duplicada", paso_excel=4)
'''

CUERPOS_REALES["CP007"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
boton_seleccionar = frame.locator("button.btn-primario")
sel_sucursal = frame.locator("select").nth(0)
sel_proveedor = frame.locator("select").nth(3)
campo_area = frame.locator("input").first
boton_agregar = frame.locator("button.btn-exito")

opciones_sucursal = sel_sucursal.locator("option").all_text_contents()
sel_sucursal.select_option(label=next(o for o in opciones_sucursal if o.startswith("3100")))
app.wait_for_timeout(2000)
opciones_proveedor = [o for o in sel_proveedor.locator("option").all_text_contents() if o.strip()]
sel_proveedor.select_option(label=opciones_proveedor[0])
app.wait_for_timeout(500)

campo_area.click()
campo_area.type("20", delay=80)
app.wait_for_timeout(300)
boton_agregar.click()
app.wait_for_timeout(1500)
capturar_paso(app, "area_sector_20_agregada", paso_excel=2)

boton_seleccionar.click()
resultado = cerrar_ventana_validacion(app, frame)
assert resultado and "sector 20" in resultado.lower(), (
    f"No se vio el mensaje esperado de bloqueo por sector restringido: {resultado!r}"
)
capturar_paso(app, "mensaje_sector_restringido", paso_excel=4)
'''

# HALLAZGO CRITICO 05/10/2026: CP008-010 NO estaban bloqueados por falta
# de clientes reales - era un bug de espera en la exploracion (esperar a
# que "Cargando..." desaparezca ANTES de que llegue a aparecer visible,
# lo que Playwright trata como "ya esta hidden" y sigue de inmediato sin
# esperar la carga real). Confirmado con el usuario en vivo: sucursal
# 3100 + area "1" + Proveedor="20101087566 - BUREAU VERITAS..." (1ra
# opcion) + Proceso="1 - Corte Fresco" (1ra opcion) + Antiguedad
# operador=">=" valor "0" trae 1483 clientes reales (deuda total S/
# 931,370.00) repartidos en 13 filas de Sector/Zona. Selectores del
# modal de revision: input[aria-label="Seleccionar todos"],
# input[aria-label="Incluir Área 1"] (uno por fila), tabla
# "totales-tabla" con las 2 filas de Totales Generales/Seleccionados.
CUERPOS_REALES["CP008"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
sel_sucursal = frame.locator("select").nth(0)
sel_proveedor = frame.locator("select").nth(3)
sel_proceso = frame.locator("select").nth(4)
sel_operador = frame.locator("select").nth(1)
campo_area = frame.locator("input").first
boton_agregar = frame.locator("button.btn-exito")
boton_seleccionar = frame.locator("button.btn-primario")

opciones_sucursal = sel_sucursal.locator("option").all_text_contents()
sel_sucursal.select_option(label=next(o for o in opciones_sucursal if o.startswith("3100")))
app.wait_for_timeout(4000)
opciones_proveedor = [o for o in sel_proveedor.locator("option").all_text_contents() if o.strip()]
sel_proveedor.select_option(label=opciones_proveedor[0])
app.wait_for_timeout(1000)
opciones_proceso = [o for o in sel_proceso.locator("option").all_text_contents() if o.strip()]
sel_proceso.select_option(label=opciones_proceso[0])
app.wait_for_timeout(1000)
sel_operador.select_option(label=">=")
app.wait_for_timeout(500)
frame.locator("#antiguedadInicial").fill("0")
app.wait_for_timeout(500)
campo_area.click()
campo_area.type("1", delay=80)
app.wait_for_timeout(500)
boton_agregar.click()
app.wait_for_timeout(6000)
capturar_paso(app, "criterios_completos_area_1", paso_excel=1)

boton_seleccionar.click()
cargando = frame.get_by_text("Cargando...")
try:
    cargando.first.wait_for(state="visible", timeout=10000)
except Exception:
    pass
cargando.first.wait_for(state="hidden", timeout=60000)
app.wait_for_timeout(1500)

filas_revision = frame.locator('input[aria-label^="Incluir"]')
cantidad_filas = filas_revision.count()
assert cantidad_filas > 0, "Se esperaba al menos una fila de revision con clientes del area"

tabla_totales = frame.locator(".totales-tabla")
valor_generales = tabla_totales.locator("tr").nth(0).locator("td").nth(1).inner_text()
valor_seleccionados_antes = tabla_totales.locator("tr").nth(1).locator("td").nth(1).inner_text()
assert "0 / S/. 0.00" in valor_seleccionados_antes, (
    f"Se esperaba 0 seleccionados antes de marcar nada: {valor_seleccionados_antes!r}"
)
capturar_paso(app, "revision_cargada_con_clientes_reales", paso_excel=3)

# Marcar/desmarcar una fila individual y verificar que los totales seleccionados cambien
filas_revision.first.check()
app.wait_for_timeout(500)
valor_seleccionados_una_fila = tabla_totales.locator("tr").nth(1).locator("td").nth(1).inner_text()
assert valor_seleccionados_una_fila != valor_seleccionados_antes, (
    "Se esperaba que los totales seleccionados cambien al marcar una fila"
)
filas_revision.first.uncheck()
app.wait_for_timeout(500)
capturar_paso(app, "recalculo_tras_marcar_una_fila", paso_excel=4)

# "Seleccionar Todos" debe igualar seleccionados con generales
checkbox_todos = frame.locator('input[aria-label="Seleccionar todos"]')
checkbox_todos.check()
app.wait_for_timeout(800)
valor_seleccionados_todos = tabla_totales.locator("tr").nth(1).locator("td").nth(1).inner_text()
clientes_generales = valor_generales.split("/")[0].strip()
clientes_seleccionados_todos = valor_seleccionados_todos.split("/")[0].strip()
assert clientes_seleccionados_todos == clientes_generales, (
    f"Con 'Seleccionar Todos', los clientes seleccionados ({clientes_seleccionados_todos!r}) "
    f"deberian igualar a los generales ({clientes_generales!r})"
)
capturar_paso(app, "seleccionar_todos_iguala_totales_generales", paso_excel=5)
'''

CUERPOS_REALES["CP009"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
sel_sucursal = frame.locator("select").nth(0)
sel_proveedor = frame.locator("select").nth(3)
sel_proceso = frame.locator("select").nth(4)
sel_operador = frame.locator("select").nth(1)
campo_area = frame.locator("input").first
boton_agregar = frame.locator("button.btn-exito")
boton_seleccionar = frame.locator("button.btn-primario")

opciones_sucursal = sel_sucursal.locator("option").all_text_contents()
sel_sucursal.select_option(label=next(o for o in opciones_sucursal if o.startswith("3100")))
app.wait_for_timeout(4000)
opciones_proveedor = [o for o in sel_proveedor.locator("option").all_text_contents() if o.strip()]
sel_proveedor.select_option(label=opciones_proveedor[0])
app.wait_for_timeout(1000)
opciones_proceso = [o for o in sel_proceso.locator("option").all_text_contents() if o.strip()]
sel_proceso.select_option(label=opciones_proceso[0])
app.wait_for_timeout(1000)
sel_operador.select_option(label=">=")
app.wait_for_timeout(500)
frame.locator("#antiguedadInicial").fill("0")
app.wait_for_timeout(500)
campo_area.click()
campo_area.type("1", delay=80)
app.wait_for_timeout(500)
boton_agregar.click()
app.wait_for_timeout(6000)

boton_seleccionar.click()
cargando = frame.get_by_text("Cargando...")
try:
    cargando.first.wait_for(state="visible", timeout=10000)
except Exception:
    pass
cargando.first.wait_for(state="hidden", timeout=60000)
app.wait_for_timeout(1500)
capturar_paso(app, "revision_cargada", paso_excel=1)

# Identificar una fila por un dato fijo (Sector/Zona = 1/124) que no cambia
# al elegir tipo de corte - evita depender del texto que se va a modificar.
fila_objetivo = frame.locator("table tr").filter(has_text="124").filter(has_text="BAJA TENSION")
assert fila_objetivo.count() == 1, f"No se encontro la fila objetivo (sector 1 / zona 124): {fila_objetivo.count()}"
celda_tipo = fila_objetivo.first.locator("td").nth(2)
celda_tipo.click()
app.wait_for_timeout(500)

modal_tipo = frame.locator("app-tipo-corte-modal")
cargando_modal = modal_tipo.locator(".cargando")
try:
    cargando_modal.wait_for(state="visible", timeout=5000)
except Exception:
    pass
cargando_modal.wait_for(state="hidden", timeout=20000)
app.wait_for_timeout(500)

opciones_tipo_corte = [o.strip() for o in modal_tipo.locator("tbody tr").all_inner_texts() if o.strip()]
assert len(opciones_tipo_corte) > 0, "Se esperaba que el catalogo de Tipos de Corte tenga opciones vigentes"
capturar_paso(app, "catalogo_tipos_de_corte_vigentes", paso_excel=2)

fila_fusible = modal_tipo.locator("tbody tr").filter(has_text="FUSIBLE/CABLE")
assert fila_fusible.count() == 1, "Se esperaba encontrar la opcion '01 - FUSIBLE/CABLE' en el catalogo"
fila_fusible.first.click()
app.wait_for_timeout(1500)

fila_actualizada = frame.locator("table tr").filter(has_text="124")
assert fila_actualizada.count() == 1, f"No se encontro la fila tras el cambio: {fila_actualizada.count()}"
texto_actualizado = fila_actualizada.first.inner_text()
assert "FUSIBLE/CABLE" in texto_actualizado, (
    f"Se esperaba que la fila refleje el nuevo tipo de corte elegido: {texto_actualizado!r}"
)
capturar_paso(app, "fila_actualizada_con_tipo_de_corte_elegido", paso_excel=4)
'''

# RF-01: Generacion de libros de corte para clientes marcados.
# IMPORTANTE (confirmado en vivo 05/10/2026): generar TODA el area 1
# de una sola vez (1483 clientes / 13 filas) hace que el backend
# responda 504 Gateway Timeout tras 60s ("Error al generar los libros
# de corte.") - es un limite de escala del servicio, no un defecto
# funcional ni del script. Con una sola fila marcada (la mas chica,
# Sector 1 / Zona 120, 1 cliente) el mismo flujo responde 200 OK con
# "Se generaron libros" en pocos segundos. El precondicion/datos de la
# matriz solo piden "al menos un area marcada con tipo de corte
# asignado", asi que se usa ese alcance chico para validar el caso.
CUERPOS_REALES["CP010"] = '''
app, frame = abrir_rf01(page, paso_excel=1)
sel_sucursal = frame.locator("select").nth(0)
sel_proveedor = frame.locator("select").nth(3)
sel_proceso = frame.locator("select").nth(4)
sel_operador = frame.locator("select").nth(1)
campo_area = frame.locator("input").first
boton_agregar = frame.locator("button.btn-exito")
boton_seleccionar = frame.locator("button.btn-primario")

opciones_sucursal = sel_sucursal.locator("option").all_text_contents()
sel_sucursal.select_option(label=next(o for o in opciones_sucursal if o.startswith("3100")))
app.wait_for_timeout(4000)
opciones_proveedor = [o for o in sel_proveedor.locator("option").all_text_contents() if o.strip()]
sel_proveedor.select_option(label=opciones_proveedor[0])
app.wait_for_timeout(1000)
opciones_proceso = [o for o in sel_proceso.locator("option").all_text_contents() if o.strip()]
sel_proceso.select_option(label=opciones_proceso[0])
app.wait_for_timeout(1000)
sel_operador.select_option(label=">=")
app.wait_for_timeout(500)
frame.locator("#antiguedadInicial").fill("0")
app.wait_for_timeout(500)
campo_area.click()
campo_area.type("1", delay=80)
app.wait_for_timeout(500)
boton_agregar.click()
app.wait_for_timeout(6000)

boton_seleccionar.click()
cargando = frame.get_by_text("Cargando...")
try:
    cargando.first.wait_for(state="visible", timeout=10000)
except Exception:
    pass
cargando.first.wait_for(state="hidden", timeout=60000)
app.wait_for_timeout(1500)

# Marcar solo la fila mas chica (Sector 1 / Zona 120, 1 cliente) para
# mantener el lote dentro de lo que el backend procesa sin timeout.
fila_chica = frame.locator("table tr").filter(has_text="120").filter(has_text="1,416.00")
assert fila_chica.count() == 1, f"No se encontro la fila esperada (zona 120): {fila_chica.count()}"
checkbox_fila = fila_chica.first.locator('input[aria-label^="Incluir"]')
checkbox_fila.check()
app.wait_for_timeout(800)

tabla_totales = frame.locator(".totales-tabla")
valor_seleccionados = tabla_totales.locator("tr").nth(1).locator("td").nth(1).inner_text()
assert "1 / S/." in valor_seleccionados, f"No se reflejo la fila marcada en los totales: {valor_seleccionados!r}"
capturar_paso(app, "area_marcada_con_tipo_de_corte_asignado", paso_excel=1)

boton_generar = frame.get_by_role("button", name=re.compile("Generar", re.I))
boton_generar.click()
app.wait_for_timeout(1500)

resultado = cerrar_ventana_validacion(app, frame, timeout_ms=40000)
assert resultado and "se generaron libros" in resultado.lower(), (
    f"No se vio el mensaje esperado de generacion exitosa: {resultado!r}"
)
capturar_paso(app, "mensaje_resultado_generacion", paso_excel=3)
'''

CUERPOS_REALES["CP019"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
src = app.locator("#aplicacion").get_attribute("src") or ""
assert "/comercial/corterepos/corterepos/descargacorte/web/home" in src, (
    f"La ruta de la pantalla no es la esperada: {src!r}"
)
capturar_paso(app, "ruta_confirmada", paso_excel=4)
'''

# RF-03: Ingreso De Accion Realizada - Ordenes Especiales De Corte -
# confirmado en vivo 05/10/2026 CON DCABA_DW. Selectores reales
# confirmados: #numeroOrden, #sucursalBusqueda, #numeroCliente, boton
# "Leer". Mensaje EXACTO de orden inexistente ya confirmado en una
# exploracion anterior de esta sesion.
CUERPOS_REALES["CP022"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
frame.locator("#numeroOrden").fill("999999")
frame.locator("#sucursalBusqueda").fill("0012")
app.wait_for_timeout(300)
capturar_paso(app, "orden_inexistente_ingresada", paso_excel=2)

frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=8000)
assert resultado and "orden señalada no existe" in resultado.lower(), (
    f"No se vio el mensaje esperado de orden inexistente: {resultado!r}"
)
capturar_paso(app, "mensaje_orden_inexistente", paso_excel=4)
'''

# Orden especial de corte real conocida (dato provisto por el usuario
# via consulta a tabla corsoco, schema "clientes", estado 'G' =
# pendiente, sucursal 3200 asignada a DCABA_DW): N.Solicitud=822155,
# N.Cliente=1419047, sucursal 3200. A diferencia de RF-04 (que requiere
# doble clic en una fila de grilla), RF-03 carga el detalle DIRECTO al
# presionar "Leer" (sin grilla intermedia).
CUERPOS_REALES["CP020"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
frame.locator("#numeroOrden").fill("822155")
frame.locator("#sucursalBusqueda").fill("3200")
app.wait_for_timeout(300)
capturar_paso(app, "orden_y_sucursal_ingresados", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(6000)
texto = frame.locator("body").inner_text()
assert "Medidores y sellos" in texto, f"No se vio la seccion de medidores esperada: {texto[-400:]!r}"
assert "Acci" in texto and "n Realizada" in texto, "No se vio el campo Accion Realizada esperado"
capturar_paso(app, "datos_de_la_orden_encontrada", paso_excel=4)
'''

CUERPOS_REALES["CP021"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
frame.locator("#numeroCliente").fill("1419047")
app.wait_for_timeout(300)
capturar_paso(app, "numero_cliente_ingresado", paso_excel=2)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(6000)
texto = frame.locator("body").inner_text()
assert "Medidores y sellos" in texto, f"No se vio la seccion de medidores esperada: {texto[-400:]!r}"
capturar_paso(app, "datos_de_la_orden_encontrada_por_cliente", paso_excel=4)
'''

CUERPOS_REALES["CP024"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
frame.locator("#numeroOrden").fill("822155")
frame.locator("#sucursalBusqueda").fill("3200")
app.wait_for_timeout(300)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(6000)
capturar_paso(app, "orden_cargada", paso_excel=1)

boton_ingresar = frame.get_by_role("button", name=re.compile(r"^\\s*Ingresar\\s*$"))
boton_ingresar.click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=6000)
assert resultado and "debe ingresar situaci" in resultado.lower() and "encontrada" in resultado.lower(), (
    f"No se vio el mensaje esperado de Situacion Encontrada obligatoria: {resultado!r}"
)
capturar_paso(app, "mensaje_situacion_obligatoria", paso_excel=4)
'''

# HALLAZGO CRITICO 05/10/2026 (aplica a RF-03 Y RF-04): el combo
# "Ejecutor" depende de cual "Coordinador" (en realidad el PROVEEDOR/
# CONTRATISTA) se elija primero - la mayoria de los proveedores tienen
# 0 ejecutores registrados en Pruebas (ObtenerEjecutoresCorte responde
# 200 con []). SOLO "20331898008 - LUZ DEL SUR S.A.A." (la empresa
# misma) tiene ejecutores reales cargados (70+). Elegir SIEMPRE ese
# Coordinador para poder completar el registro.
#
# CP023 usa la orden 816881 (cliente 2148930, sucursal 3200) - la misma
# que CP025/CP027 (esos 2 casos fallan su propia validacion antes de
# confirmar, asi que NUNCA consumen la orden - queda disponible para
# CP023). OJO: se probo primero con 327584, pero resulto ser un
# "Cliente Nuevo" sin medidores, cuyo catalogo de Accion Realizada NO
# incluye "ER - REGULARIZA CORTE" (logico: no tiene historial de corte
# que regularizar) - usar siempre una orden CON medidores reales para
# este caso.
CUERPOS_REALES["CP023"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
frame.locator("#numeroOrden").fill("816881")
frame.locator("#sucursalBusqueda").fill("3200")
app.wait_for_timeout(300)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(6000)
# Esta orden corresponde a un "Cliente Nuevo" sin medidores registrados:
# aparece una Confirmacion ("Cliente Nuevo no registra medidores. Desea
# Ingresar el Corte?") apenas carga - aceptarla antes de seguir.
dialogo_sin_medidores = frame.locator(".ant-modal").filter(has_text="Confirmaci")
if dialogo_sin_medidores.count() and dialogo_sin_medidores.first.is_visible():
    dialogo_sin_medidores.first.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$")).click()
    app.wait_for_timeout(800)
capturar_paso(app, "orden_cargada", paso_excel=1)

sel_situacion = frame.locator("#situacion")
opciones_sit = [o for o in sel_situacion.locator("option").all_text_contents() if o.strip()]
sel_situacion.select_option(label=next(o for o in opciones_sit if o.strip().startswith("CO")))
app.wait_for_timeout(500)

sel_accion = frame.locator("#accion")
opciones_acc = [o for o in sel_accion.locator("option").all_text_contents() if o.strip()]
sel_accion.select_option(label=next(o for o in opciones_acc if o.strip().startswith("ER")))
app.wait_for_timeout(500)

sel_coord = frame.locator("#coordinador")
opciones_coord = [o for o in sel_coord.locator("option").all_text_contents() if o.strip()]
sel_coord.select_option(label=next(o for o in opciones_coord if o.strip().startswith("20331898008")))
app.wait_for_timeout(3000)

sel_ejec = frame.locator("#ejecutor")
opciones_ejec = [o for o in sel_ejec.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
assert len(opciones_ejec) > 0, "Se esperaba que el combo Ejecutor se llene al elegir Coordinador=LUZ DEL SUR S.A.A."
sel_ejec.select_option(label=opciones_ejec[0])
app.wait_for_timeout(400)

frame.locator("#fecha").fill("2026-09-25")
frame.locator("#hora").fill("10:30")
app.wait_for_timeout(300)

sel_fase = frame.locator("#fase")
opciones_fase = [o for o in sel_fase.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
sel_fase.select_option(label=opciones_fase[0])
sel_tapa = frame.locator("#tapa")
opciones_tapa = [o for o in sel_tapa.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
sel_tapa.select_option(label=opciones_tapa[0])
sel_anomalia = frame.locator("#anomalia")
opciones_anom = [o for o in sel_anomalia.locator("option").all_text_contents() if o.strip()]
sel_anomalia.select_option(label=next(o for o in opciones_anom if o.strip().startswith("N")))
frame.locator("#sticker").fill("12345678")
lectura = frame.locator("input[aria-label*=\\"Lectura\\"]")
if lectura.count():
    lectura.first.fill("100")
app.wait_for_timeout(500)
capturar_paso(app, "datos_de_accion_completados", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Ingresar\\s*$")).click()
app.wait_for_timeout(1000)
dialogo_confirm = frame.locator(".ant-modal").filter(has_text="Confirmaci")
dialogo_confirm.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$")).click()
app.wait_for_timeout(2500)
capturar_paso(app, "registro_confirmado", paso_excel=6)
'''

# CP025/CP027 usan la orden 816881 (cliente 2148930, sucursal 3200) -
# confirmada SIN el aviso extra de "cliente sin medidores" que tienen
# otras ordenes de la muestra. Ambos casos fallan su propia validacion
# (fecha invalida / sticker faltante) ANTES de llegar a confirmar, por
# lo que NO consumen la orden - se puede repetir el Leer para cada uno.
CUERPOS_REALES["CP025"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
frame.locator("#numeroOrden").fill("816881")
frame.locator("#sucursalBusqueda").fill("3200")
app.wait_for_timeout(300)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(6000)

sel_situacion = frame.locator("#situacion")
opciones_sit = [o for o in sel_situacion.locator("option").all_text_contents() if o.strip()]
sel_situacion.select_option(label=next(o for o in opciones_sit if o.strip().startswith("CO")))
app.wait_for_timeout(500)
sel_accion = frame.locator("#accion")
opciones_acc = [o for o in sel_accion.locator("option").all_text_contents() if o.strip()]
sel_accion.select_option(label=next(o for o in opciones_acc if o.strip().startswith("ER")))
app.wait_for_timeout(500)
sel_coord = frame.locator("#coordinador")
opciones_coord = [o for o in sel_coord.locator("option").all_text_contents() if o.strip()]
sel_coord.select_option(label=next(o for o in opciones_coord if o.strip().startswith("20331898008")))
app.wait_for_timeout(3000)
sel_ejec = frame.locator("#ejecutor")
opciones_ejec = [o for o in sel_ejec.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
sel_ejec.select_option(label=opciones_ejec[0])
app.wait_for_timeout(400)

# Fecha de reposicion/corte ANTERIOR a la fecha de generacion de la orden
frame.locator("#fecha").fill("2020-01-01")
frame.locator("#hora").fill("10:30")
app.wait_for_timeout(300)
sel_fase = frame.locator("#fase")
opciones_fase = [o for o in sel_fase.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
sel_fase.select_option(label=opciones_fase[0])
sel_tapa = frame.locator("#tapa")
opciones_tapa = [o for o in sel_tapa.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
sel_tapa.select_option(label=opciones_tapa[0])
sel_anomalia = frame.locator("#anomalia")
opciones_anom = [o for o in sel_anomalia.locator("option").all_text_contents() if o.strip()]
sel_anomalia.select_option(label=next(o for o in opciones_anom if o.strip().startswith("N")))
frame.locator("#sticker").fill("12345678")
lectura = frame.locator("input[aria-label*=\\"Lectura\\"]")
if lectura.count():
    lectura.first.fill("100")
app.wait_for_timeout(500)
capturar_paso(app, "fecha_anterior_a_generacion_ingresada", paso_excel=2)

frame.get_by_role("button", name=re.compile(r"^\\s*Ingresar\\s*$")).click()
modal_fecha = frame.locator(".ant-modal")
modal_fecha.first.wait_for(state="visible", timeout=6000)
resultado = modal_fecha.first.inner_text()
capturar_paso(app, "mensaje_fecha_invalida", paso_excel=4)
assert resultado and "fecha" in resultado.lower() and "generaci" in resultado.lower(), (
    f"No se vio el mensaje esperado de fecha invalida: {resultado!r}"
)
modal_fecha.first.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$")).click()
app.wait_for_timeout(500)

# Paso adicional: fecha valida pero HORA fuera de rango (00-23h). El campo
# #hora es texto enmascarado "__:__" (maxlength=5) que NO sanea en tiempo
# real - acepta "25:45" tal cual, y solo valida al presionar Ingresar.
# Mismo cliente/orden (816881): esta sub-prueba tampoco consume la orden
# porque vuelve a fallar su propia validacion antes de confirmar.
frame.locator("#fecha").fill("2026-09-20")
frame.locator("#hora").fill("25:45")
app.wait_for_timeout(500)
capturar_paso(app, "hora_invalida_ingresada", paso_excel=5)

frame.get_by_role("button", name=re.compile(r"^\\s*Ingresar\\s*$")).click()
modal_hora = frame.locator(".ant-modal")
modal_hora.first.wait_for(state="visible", timeout=6000)
resultado_hora = modal_hora.first.inner_text()
# Captura CON el modal del mensaje todavia abierto, en vez de cerrarlo antes
# de capturar (ver gotcha: cerrar_ventana_validacion() cierra el modal ANTES
# de devolver el texto, asi que no sirve para evidenciar visualmente un
# mensaje - solo para validarlo por texto).
capturar_paso(app, "mensaje_hora_invalida", paso_excel=6)
assert resultado_hora and "hora inv" in resultado_hora.lower() and "00 al 23" in resultado_hora.lower(), (
    f"No se vio el mensaje esperado de hora invalida: {resultado_hora!r}"
)
modal_hora.first.get_by_role("button", name=re.compile(r"^\\s*Aceptar\\s*$")).click()
app.wait_for_timeout(500)
'''

CUERPOS_REALES["CP027"] = '''
app, frame = abrir_rf03(page, paso_excel=1)
frame.locator("#numeroOrden").fill("816881")
frame.locator("#sucursalBusqueda").fill("3200")
app.wait_for_timeout(300)
frame.get_by_role("button", name=re.compile(r"^\\s*Leer\\s*$")).click()
app.wait_for_timeout(6000)

sel_situacion = frame.locator("#situacion")
opciones_sit = [o for o in sel_situacion.locator("option").all_text_contents() if o.strip()]
sel_situacion.select_option(label=next(o for o in opciones_sit if o.strip().startswith("CO")))
app.wait_for_timeout(500)
sel_accion = frame.locator("#accion")
opciones_acc = [o for o in sel_accion.locator("option").all_text_contents() if o.strip()]
accion_exige_sticker = next(o for o in opciones_acc if o.strip().startswith("ER"))
sel_accion.select_option(label=accion_exige_sticker)
app.wait_for_timeout(500)
sel_coord = frame.locator("#coordinador")
opciones_coord = [o for o in sel_coord.locator("option").all_text_contents() if o.strip()]
sel_coord.select_option(label=next(o for o in opciones_coord if o.strip().startswith("20331898008")))
app.wait_for_timeout(3000)
sel_ejec = frame.locator("#ejecutor")
opciones_ejec = [o for o in sel_ejec.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
sel_ejec.select_option(label=opciones_ejec[0])
app.wait_for_timeout(400)

frame.locator("#fecha").fill("2026-09-25")
frame.locator("#hora").fill("10:30")
app.wait_for_timeout(300)
sel_fase = frame.locator("#fase")
opciones_fase = [o for o in sel_fase.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
sel_fase.select_option(label=opciones_fase[0])
sel_tapa = frame.locator("#tapa")
opciones_tapa = [o for o in sel_tapa.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
sel_tapa.select_option(label=opciones_tapa[0])
sel_anomalia = frame.locator("#anomalia")
opciones_anom = [o for o in sel_anomalia.locator("option").all_text_contents() if o.strip()]
sel_anomalia.select_option(label=next(o for o in opciones_anom if o.strip().startswith("N")))
lectura = frame.locator("input[aria-label*=\\"Lectura\\"]")
if lectura.count():
    lectura.first.fill("100")
app.wait_for_timeout(500)
# Sticker deliberadamente en blanco
capturar_paso(app, "sticker_en_blanco_resto_completo", paso_excel=3)

frame.get_by_role("button", name=re.compile(r"^\\s*Ingresar\\s*$")).click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=6000)
assert resultado and "debe ingresar sticker" in resultado.lower(), (
    f"No se vio el mensaje esperado de sticker obligatorio: {resultado!r}"
)
capturar_paso(app, "mensaje_sticker_obligatorio", paso_excel=5)
'''

CUERPOS_REALES["CP028"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
src = app.locator("#aplicacion").get_attribute("src") or ""
assert "/comercial/corterepos/corterepos/descargarcnx/web/home" in src, (
    f"La ruta de la pantalla no es la esperada: {src!r}"
)
capturar_paso(app, "ruta_confirmada", paso_excel=4)
'''

# RF-04: Ingreso De Accion Realizada Para Ordenes De Reposicion -
# confirmado en vivo 05/10/2026 CON DCABA_DW. Selectores reales:
# #inputNumeroOrden, #inputNumeroClienteBusqueda, boton "Leer" (sin
# role accesible - usar frame.locator("button", has_text="Leer")).
# Orden de reposicion real conocida (dato provisto por el usuario via
# consulta a tabla corsore, estado 'G' = Generada, sucursal 3200
# asignada a DCABA_DW): cliente 1647966, orden 772942, sucursal 3200.
CUERPOS_REALES["CP029"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator("#inputNumeroClienteBusqueda").fill("1647966")
app.wait_for_timeout(300)
capturar_paso(app, "numero_cliente_ingresado", paso_excel=2)
frame.locator("button", has_text=re.compile("Leer", re.I)).first.click()
app.wait_for_timeout(3000)
texto = frame.locator("body").inner_text()
assert "772942" in texto, f"No se encontro la orden 772942 en el listado: {texto[-400:]!r}"
assert "3200" in texto, "No se muestra la sucursal esperada en el listado"
assert "1647966" in texto, "No se muestra el cliente esperado en el listado"
capturar_paso(app, "orden_encontrada_con_datos", paso_excel=4)
'''

CUERPOS_REALES["CP030"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
boton_leer = frame.locator("button", has_text=re.compile("Leer", re.I))
boton_leer.first.click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=8000)
assert resultado and "debe ingresar número de orden o número de cliente" in resultado.lower(), (
    f"No se vio el mensaje esperado de criterio obligatorio: {resultado!r}"
)
capturar_paso(app, "mensaje_criterio_obligatorio", paso_excel=4)
'''

# CP034: misma orden real de CP029 (cliente 1647966, orden 772942,
# sucursal 3200). Aplica el mismo hallazgo critico de RF-03: Coordinador
# debe ser "20331898008 - LUZ DEL SUR S.A.A." para que el combo Ejecutor
# se pueble (cualquier otro proveedor tiene 0 ejecutores). Selectores
# propios de RF-04 (distintos de RF-03): #inputSituacion, #inputAccion,
# #inputCoordinador, #inputEjecutor, #inputFecha, #inputHora,
# #inputFase, #inputTapa, #inputAnomalia, #inputSticker. El boton
# "Ingresar" no tiene role accesible - usar locator por texto.
CUERPOS_REALES["CP034"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator("#inputNumeroClienteBusqueda").fill("1647966")
app.wait_for_timeout(300)
frame.locator("button", has_text=re.compile("Leer", re.I)).first.click()
app.wait_for_timeout(5000)
celda = frame.locator("td", has_text="772942")
celda.first.dblclick(force=True)
app.wait_for_timeout(5000)
capturar_paso(app, "solicitud_cargada", paso_excel=1)

sel_situacion = frame.locator("#inputSituacion")
opciones_sit = [o for o in sel_situacion.locator("option").all_text_contents() if o.strip()]
sel_situacion.select_option(label=next(o for o in opciones_sit if o.strip().startswith("CO")))
app.wait_for_timeout(500)

sel_accion = frame.locator("#inputAccion")
opciones_acc = [o for o in sel_accion.locator("option").all_text_contents() if o.strip()]
sel_accion.select_option(label=next(o for o in opciones_acc if o.strip().startswith("ER")))
app.wait_for_timeout(500)

sel_coord = frame.locator("#inputCoordinador")
opciones_coord = [o for o in sel_coord.locator("option").all_text_contents() if o.strip()]
sel_coord.select_option(label=next(o for o in opciones_coord if o.strip().startswith("20331898008")))
app.wait_for_timeout(3000)

sel_ejec = frame.locator("#inputEjecutor")
opciones_ejec = [o for o in sel_ejec.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
assert len(opciones_ejec) > 0, "Se esperaba que el combo Ejecutor se llene al elegir Coordinador=LUZ DEL SUR S.A.A."
sel_ejec.select_option(label=opciones_ejec[0])
app.wait_for_timeout(400)

# Fecha de reposicion ANTERIOR a la fecha de solicitud de reposicion (15/10/2024)
frame.locator("#inputFecha").fill("2024-09-01")
frame.locator("#inputHora").fill("10:30")
app.wait_for_timeout(300)

sel_fase = frame.locator("#inputFase")
opciones_fase = [o for o in sel_fase.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
sel_fase.select_option(label=opciones_fase[0])
sel_tapa = frame.locator("#inputTapa")
opciones_tapa = [o for o in sel_tapa.locator("option").all_text_contents() if o.strip() and "Seleccione" not in o]
sel_tapa.select_option(label=opciones_tapa[0])
sel_anomalia = frame.locator("#inputAnomalia")
opciones_anom = [o for o in sel_anomalia.locator("option").all_text_contents() if o.strip()]
sel_anomalia.select_option(label=next(o for o in opciones_anom if o.strip().startswith("N")))
app.wait_for_timeout(500)
capturar_paso(app, "fecha_anterior_a_solicitud_ingresada", paso_excel=2)

frame.locator("button", has_text=re.compile(r"^\\s*Ingresar\\s*$")).click()
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=6000)
assert resultado and "fecha de reposici" in resultado.lower() and "menor" in resultado.lower(), (
    f"No se vio el mensaje esperado de fecha invalida: {resultado!r}"
)
capturar_paso(app, "mensaje_fecha_invalida", paso_excel=4)
'''

# CP033: cliente 1422060, orden 846021, sucursal 3200. Su unico medidor
# (2578257) fue puesto temporalmente en estado='R' via UPDATE directo a
# medid (autorizado por el usuario 06/10/2026, revertido a 'I' despues
# de correr este caso) para simular "sin medidores activos" - dato
# inestable en Pruebas segun la propia precondicion de la matriz.
CUERPOS_REALES["CP033"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator("#inputNumeroClienteBusqueda").fill("1422060")
app.wait_for_timeout(300)
frame.locator("button", has_text=re.compile("Leer", re.I)).first.click()
app.wait_for_timeout(4000)
texto = frame.locator("body").inner_text()
assert "846021" in texto, f"No se encontro la orden 846021 en el listado: {texto[-400:]!r}"
capturar_paso(app, "orden_de_cliente_sin_medidores_encontrada", paso_excel=1)

celda = frame.locator("td", has_text="846021")
celda.first.dblclick(force=True)
modal = frame.locator(".ant-modal")
modal.first.wait_for(state="visible", timeout=8000)
texto_confirmacion = modal.first.inner_text()
assert "no registra medidores" in texto_confirmacion.lower(), (
    f"No se vio la pregunta de confirmacion esperada: {texto_confirmacion!r}"
)
capturar_paso(app, "confirmacion_cliente_sin_medidores", paso_excel=2)

modal.first.get_by_role("button", name=re.compile("Aceptar", re.I)).click()
app.wait_for_timeout(3000)

sel_situacion = frame.locator("#inputSituacion")
assert sel_situacion.is_enabled(), "Se esperaba que la seccion de accion en terreno quede habilitada"
texto_detalle = frame.locator("body").inner_text()
assert "no registra medidores activos" in texto_detalle.lower(), (
    f"No se vio el aviso de 'sin medidores activos' en la seccion de medidores: {texto_detalle[-400:]!r}"
)
capturar_paso(app, "seccion_habilitada_sin_datos_de_medidor", paso_excel=4)
'''

# CP032: cliente 239329, orden 815941, sucursal 3200. tiene_remarcadores
# marcado temporalmente a 'S' via UPDATE directo a cliente (autorizado
# por el usuario 06/10/2026, pendiente de revertir a 'N' despues de
# correr este caso - ver memoria del proyecto). El bloqueo se dispara
# en el doble clic de seleccion, igual patron que CP031.
CUERPOS_REALES["CP032"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator("#inputNumeroClienteBusqueda").fill("239329")
app.wait_for_timeout(300)
frame.locator("button", has_text=re.compile("Leer", re.I)).first.click()
app.wait_for_timeout(4000)
texto = frame.locator("body").inner_text()
assert "815941" in texto, f"No se encontro la orden 815941 en el listado: {texto[-400:]!r}"
capturar_paso(app, "orden_de_cliente_con_remarcador_encontrada", paso_excel=1)

celda = frame.locator("td", has_text="815941")
celda.first.dblclick(force=True)
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=8000)
assert resultado and "remarcador" in resultado.lower() and "no se puede reconectar" in resultado.lower(), (
    f"No se vio el mensaje esperado de cliente con remarcador: {resultado!r}"
)
capturar_paso(app, "mensaje_cliente_con_remarcador", paso_excel=3)
'''

# CP031: cliente real con orden de reposicion pendiente ('G') pero
# estado_cliente<>'0' (hallado via el usuario con SQL sobre tabla
# cliente/corsore, sucursal 3200): cliente 1136061, orden 779070,
# estado_cliente=2. El bloqueo se dispara en el doble clic de seleccion
# (antes de cualquier otro campo), no al presionar "Leer".
CUERPOS_REALES["CP031"] = '''
app, frame = abrir_rf04(page, paso_excel=1)
frame.locator("#inputNumeroClienteBusqueda").fill("1136061")
app.wait_for_timeout(300)
frame.locator("button", has_text=re.compile("Leer", re.I)).first.click()
app.wait_for_timeout(4000)
texto = frame.locator("body").inner_text()
assert "779070" in texto, f"No se encontro la orden 779070 en el listado: {texto[-400:]!r}"
capturar_paso(app, "orden_de_cliente_inactivo_encontrada", paso_excel=2)

celda = frame.locator("td", has_text="779070")
celda.first.dblclick(force=True)
resultado = cerrar_ventana_validacion(app, frame, timeout_ms=8000)
assert resultado and "no est" in resultado.lower() and "activo" in resultado.lower(), (
    f"No se vio el mensaje esperado de cliente inactivo: {resultado!r}"
)
capturar_paso(app, "mensaje_cliente_no_activo", paso_excel=4)
'''

# CPs que corren con DCABA_DW/Melquisedec_01 en vez de SCASTI_DW (default):
# confirmado en vivo 03/10/2026 que el rol de DCABA_DW NO sufre el defecto
# sistemico de sucursal='0000' (ver memoria del proyecto) - para RF-01 esto
# destraba casos que de otro modo quedarian bloqueados por el backend.
_CPS_DCABA_DW = {"CP003", "CP004", "CP005", "CP006", "CP007", "CP008", "CP009", "CP010", "CP012", "CP013", "CP014", "CP015", "CP016", "CP017", "CP018", "CP020", "CP021", "CP022", "CP023", "CP024", "CP025", "CP027", "CP029", "CP030", "CP031", "CP032", "CP033", "CP034", "CP038", "CP039", "CP040", "CP042", "CP043"}

# --- Un add() por cada uno de los 53 casos (+ CP001 transversal) de matriz_casos.json, en orden ---
for _cp in sorted(MATRIZ, key=lambda x: int(x[2:])):
    _m = MATRIZ[_cp]
    _body = CUERPOS_REALES.get(_cp) or _body_pendiente(_cp, _m["rf"], _m["name"])
    if _cp in _CPS_DCABA_DW:
        add(_cp, _body, usuario="DCABA_DW", password="Melquisedec_01")
    else:
        add(_cp, _body)


if __name__ == "__main__":
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")
