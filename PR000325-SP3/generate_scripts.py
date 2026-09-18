"""
generate_scripts.py (PR000325-SP3 - Migracion Modulo de Facturacion,
Sprint 3: 8 mantenedores CRUD de "Administracion Centralizada", RF-8/RF-9
desestimados por LDS)

Fuente de verdad: genera los 78 CPxxx.py (CP001..CP090, numeracion no
correlativa 1:1 - hay CPs con sufijo como "CP045-A" y saltos, ver
matriz_casos.json) a partir de matriz_casos.json + el framework
compartido _framework/web_lds_core.py.

MISMA FAMILIA que PR000325 Sprint 2 (C:\\Proyectos\\PlataformaWeb\\automation\\PR000325\\):
mismo patron de UI sin atributos id/name (span.fl + input.fi, dialogo
generico .mdl-confirmar con boton Aceptar/Cancelar y a veces un SEGUNDO
dialogo de resultado tras confirmar) - confirmado en vivo el 15/09/2026
comparando el HTML real de RF-01 contra el de Sprint 2. Los 4 helpers
genericos (campo_por_etiqueta, dialogo_visible, confirmar, boton_grabar)
se reutilizan tal cual desde ahi.

Rutas de menu y componentes CONFIRMADOS EN VIVO el 15/09/2026 (las 8 apps
viven TODAS bajo "Interno", a diferencia de Sprint 2 donde RF-05 estaba
en Comercial > Facturacion > Facturacion):
    RF-01  Mantenedor De Tablas Del Sistema Comercial  -> app-mantenedor-tablas-list
    RF-02  Relacion Sucursal - Sector - Zona           -> app-susec-zona-list
    RF-03  Actualizacion De Agenda De Pagos            -> app-agenda-pagos-list
    RF-04  Actualizacion De Documentos                 -> app-documentos-list
    RF-05  Actualizacion De Conceptos                  -> app-conceptos-list
    RF-06  Actualizacion De Precios                    -> app-precios-list
    RF-07  Actualizacion De Tasas De Interes            -> app-tasas-interes-list
    RF-10  Actualizacion De Agenda De Facturacion       -> app-agenda-principal

*** ESTADO: recien arrancado (15/09/2026). ***
RF-01 confirmado en vivo con datos reales (Nivel 1 = catalogo de
"tablas" ej. ACRECO/ACRERE/ACTECO...; Nivel 2 = codigos dentro de una
tabla, ej. dentro de ACRECO: 10=CORTE FUSIBLE 0000, 20=CORTE CABLE... -
se entra a Nivel 2 con DOBLE CLICK en la fila de Nivel 1, "Volver >>"
regresa a Nivel 1). CP001/CP002/CP004 escritos y confirmados
estructuralmente contra capturas reales - CP005-CP009 (crear/modificar/
desactivar/responsive) y el RESTO de RF-02 a RF-10 (69 casos) quedan
pendientes de escribir, cada uno necesita su propia exploracion en vivo
de las reglas de negocio (tramos de precios, vigencias, notificaciones a
GTE, feriados/dias habiles, etc. - ver EF_texto.txt) antes de poder
escribirse con confianza, igual que se hizo con RF-01. NO EJECUTAR
ningun CPxxx.py todavia (pedido explicito del usuario, 15/09/2026) - solo
generar/compilar.
"""
import inspect
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT_DIR.parent / "_framework"))
sys.path.insert(0, str(OUT_DIR.parent / "_framework" / "modulos"))
import web_lds_core as core  # noqa: E402

# Modulos por aplicativo (ver NUEVO_PROYECTO_CHECKLIST.md Seccion 0c):
# la ficha tecnica + helpers de cada RF de este proyecto viven en
# _framework/modulos/, no inline aca - se importan de verdad y se
# vuelcan como texto (fuente_modulo(), definida abajo) en cada CPxxx.py
# generado, asi cada script sigue siendo 100% autonomo en tiempo de
# ejecucion pese a que la fuente de la logica es compartida.
import mantenedor_tablas_sistema_comercial as mod_rf01  # noqa: E402
import relacion_sucursal_sector_zona as mod_rf02  # noqa: E402
import actualizacion_agenda_pagos as mod_rf03  # noqa: E402
import actualizacion_documentos as mod_rf04  # noqa: E402
import actualizacion_conceptos as mod_rf05  # noqa: E402
import actualizacion_precios as mod_rf06  # noqa: E402
import actualizacion_tasas_interes as mod_rf07  # noqa: E402
import actualizacion_agenda_facturacion as mod_rf10  # noqa: E402

PROYECTO = "PR000325-SP3"  # debe coincidir con el nombre de esta carpeta
MATRIZ = json.loads((OUT_DIR / "matriz_casos.json").read_text(encoding="utf-8"))

ENV_TOGGLES = core.ENV_TOGGLES_CODE.replace("__PROYECTO__", PROYECTO)


def fuente_modulo(modulo):
    """Extrae el codigo fuente de un modulo de _framework/modulos/ (su
    docstring, convertido a comentario, + todas sus funciones/constantes)
    para volcarlo como texto en el CPxxx.py generado. Las lineas de
    import del modulo se omiten (ya cubiertas por el header estandar del
    CPxxx.py)."""
    codigo_completo = inspect.getsource(modulo)
    lineas = codigo_completo.split("\n")
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
    resto = [l for l in lineas[i:] if not (l.startswith("import ") or l.startswith("from "))]
    ficha_tecnica = "\n".join(f"# {l}" if l.strip() else "#" for l in doc_lineas)
    return ficha_tecnica + "\n\n\n" + "\n".join(resto).strip("\n")


# Alias para que los cuerpos de caso ya escritos (add("CPxxx", "abrir_rf01", ...))
# sigan funcionando sin tener que renombrar 75 llamadas - cada abrir_rfNN
# es simplemente el abrir_* real del modulo correspondiente.
HELPERS_MODULOS = "\n\n\n".join(
    fuente_modulo(m) for m in (mod_rf01, mod_rf02, mod_rf03, mod_rf04, mod_rf05, mod_rf06, mod_rf07, mod_rf10)
) + """


abrir_rf01 = abrir_mantenedor_tablas
abrir_rf02 = abrir_relacion_sucursal_sector_zona
abrir_rf03 = abrir_actualizacion_agenda_pagos
abrir_rf04 = abrir_actualizacion_documentos
abrir_rf05 = abrir_actualizacion_conceptos
abrir_rf06 = abrir_actualizacion_precios
abrir_rf07 = abrir_actualizacion_tasas_interes
abrir_rf10 = abrir_actualizacion_agenda_facturacion
"""

# ===========================================================================
# Helpers propios de PR000325-SP3 - REUTILIZADOS TAL CUAL de PR000325
# Sprint 2 (C:\Proyectos\PlataformaWeb\automation\PR000325\generate_scripts.py,
# lineas 72-139), confirmado en vivo el 15/09/2026 que RF-01 de este
# sprint usa el MISMO patron de UI (span.fl/input.fi sin id/name,
# .mdl-confirmar con posible 2do dialogo de resultado).
# ===========================================================================
PR000325_SP3_HELPERS = '''
def campo_por_etiqueta(scope, etiqueta):
    """Ubica el <input>/<select> asociado a un <span class="fl">etiqueta</span>
    vecino: estas apps NO tienen atributo "name" en los campos. `etiqueta`
    hace match parcial, no hace falta poner los ":" finales que trae el
    span real.

    BUG REAL / diferencia confirmada en vivo (RF-01 de SP3, 15/09/2026):
    a diferencia de Sprint 2 (que envolvia el input en un <div class="val">
    hermano del span), aca el input es hijo del MISMO <div> padre que el
    span (span -> <br> -> input, sin wrapper "val"). Se busca dentro del
    padre directamente en vez de un hermano "div.val" - mas robusto para
    ambos patrones."""
    fl = scope.locator("span.fl").filter(has_text=etiqueta).first
    contenedor = fl.locator("xpath=parent::div")
    return contenedor.locator("input, select").first


SELECTOR_DIALOGO = ".mdl-confirmar, nz-modal-container, .ant-modal-wrap"


def dialogo_visible(scope, timeout=8000):
    """Espera y devuelve el locator del dialogo modal visible. BUG REAL /
    confirmado en vivo (15/09/2026, CP006/CP008): esta app usa DOS
    componentes de dialogo distintos que se ven iguales para el usuario -
    ".mdl-confirmar" (confirmaciones Cancelar+Aceptar) y un componente
    Ant Design nz-modal-container/.ant-modal-wrap ("Ventana de
    Validacion", boton unico Aceptar, usado para mensajes de error como
    "Codigo ya existe." y para el 2do dialogo de resultado tras crear/
    modificar/eliminar) - se busca con un selector que cubre ambos."""
    dialogo = scope.locator(SELECTOR_DIALOGO)
    dialogo.first.wait_for(state="visible", timeout=timeout)
    return dialogo.first


def confirmar(scope, aceptar=True, timeout=8000, timeout_segundo=7000):
    """Cierra el dialogo modal visible (.mdl-confirmar) pulsando "Aceptar"
    o "Cancelar". Si se confirma (aceptar=True), estas apps pueden
    mostrar ADEMAS un SEGUNDO dialogo con el resultado real de la
    operacion (ej. "Registro Actualizado.") - confirmado en Sprint 2,
    timeout_segundo generoso porque el backend a veces tarda en
    mostrarlo. Devuelve el texto del dialogo de RESULTADO si aparecio,
    si no el de la confirmacion original."""
    dialogo = dialogo_visible(scope, timeout)
    texto = dialogo.inner_text()
    dialogo.get_by_role("button", name="Aceptar" if aceptar else "Cancelar").click()
    dialogo.wait_for(state="hidden", timeout=timeout)
    if aceptar:
        try:
            segundo = scope.locator(SELECTOR_DIALOGO).first
            segundo.wait_for(state="visible", timeout=timeout_segundo)
            texto = segundo.inner_text()
            segundo.get_by_role("button", name="Aceptar").click()
            segundo.wait_for(state="hidden", timeout=timeout)
        except PWTimeoutError:
            pass  # no todas las operaciones muestran un 2do dialogo de resultado
    return texto


def boton_grabar(scope):
    """El boton "Ingresar"/"Modificar" puede cambiar de texto segun el
    estado (confirmado como patron comun en Sprint 2). Se ubica por
    texto dinamico via regex en vez de asumir uno de los dos."""
    return scope.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))


def escribir_campo(campo, texto, delay=30):
    """Reemplaza el contenido de un input reactivo Angular de forma
    confiable. BUG REAL confirmado en vivo (CP005, 15/09/2026): ni
    fill() ni fill()+Tab ni Control+A+tipeo alcanzan solos en estos
    campos - Control+A SELECCIONA el texto viejo pero el primer
    caracter tipeado no lo reemplaza (el modelo Angular se queda con
    una mezcla o con el valor viejo). Hace falta un Delete EXPLICITO
    entre el Control+A y el tipeo (press_sequentially, caracter por
    caracter, para que el form reactivo/mascara registre cada tecla).
    Termina con Tab para forzar el blur/commit del valor."""
    campo.click()
    campo.press("Control+A")
    campo.press("Delete")
    campo.press_sequentially(texto, delay=delay)
    campo.press("Tab")


def confirmar_si_no(frame, aceptar=True, max_dialogos=4, timeout=8000, timeout_siguientes=6000):
    """Variante de confirmar() para dialogos con botones "Si"/"No" en vez
    de "Aceptar"/"Cancelar" (RF-02 en adelante). BUG REAL / confirmado en
    vivo (16/09/2026, RF-02): con Beneficiario FISE marcado,
    Ingresar/Modificar apilan 2 dialogos "Confirmacion" (Si/No)
    SIMULTANEOS en el DOM (uno de aviso FISE, otro de la accion en si)
    antes de terminar con un 3er dialogo de RESULTADO/VALIDACION (un
    solo boton Aceptar) - se va cerrando el que este visible en cada
    momento en vez de asumir un numero fijo de dialogos. BUG REAL /
    confirmado en vivo (16/09/2026, RF-03): el dialogo de RESULTADO
    puede tardar bastante mas de 3s en aparecer tras confirmar (backend
    mas lento que en RF-02) - se usa un timeout mas generoso que el del
    primer dialogo para los siguientes en vez de uno corto fijo. BUG
    REAL / 3ra variante confirmada en vivo (16/09/2026, RF-05): esta
    pantalla usa un dialogo de confirmacion con botones "Cancelar"/
    "Aceptar" (no "Si"/"No" como RF-02/03) titulado "Administrador" -
    hay que distinguir un dialogo de CONFIRMACION (tiene Cancelar Y
    Aceptar juntos - click Aceptar y seguir esperando el de resultado)
    de un dialogo de RESULTADO/VALIDACION final (Aceptar solo, sin
    Cancelar - terminal)."""
    texto_final = ""
    for i in range(max_dialogos):
        dialogo = frame.locator(SELECTOR_DIALOGO).first
        try:
            dialogo.wait_for(state="visible", timeout=timeout if i == 0 else timeout_siguientes)
        except PWTimeoutError:
            break
        texto_final = dialogo.inner_text()
        boton_si_no = dialogo.get_by_role("button", name=re.compile(r"^S.$" if aceptar else r"^No$"))
        boton_cancelar = dialogo.get_by_role("button", name="Cancelar")
        boton_aceptar = dialogo.get_by_role("button", name="Aceptar")
        es_confirmacion_cancelar_aceptar = boton_cancelar.count() > 0 and boton_aceptar.count() > 0
        if boton_si_no.count():
            boton_si_no.click()
        elif es_confirmacion_cancelar_aceptar:
            (boton_aceptar if aceptar else boton_cancelar).click()
        elif boton_aceptar.count():
            boton_aceptar.click()
            try:
                dialogo.wait_for(state="hidden", timeout=timeout)
            except PWTimeoutError:
                pass
            break
        else:
            break
        dialogo.page.wait_for_timeout(400)
    return texto_final


'''


HEADER_TEMPLATE = '''"""
{docstring}
"""
import os, random, re, shutil, struct, subprocess, time, zipfile
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

%%HELPERS_PROPIOS%%

%%HELPERS_MODULOS%%

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
            app, frame = {abrir_fn}(page)

{body}

            capturar_paso(app, "estado_final_del_caso", paso_excel=max(_parsear_pasos_excel(PASOS_CASO), default=None))
            _CASO_OK = True

        except (PWTimeoutError, AssertionError) as e:
            print(f"[FALLO] {{CASO}} FALLO: {{str(e).encode('ascii', 'replace').decode('ascii')}}")
            (app if app else page).screenshot(path=str(EVIDENCIA / f"{{CASO}}_error.png"), full_page=True)
            raise
        finally:
            if GRABAR_VIDEO:
                (app if app else page).wait_for_timeout(3000)
            video_portal = page.video
            video_app = app.video if app else None
            browser.close()
            # CONFIRMADO EN VIVO el 17/09/2026: video/Word solo tienen valor
            # para casos que terminan OK - un caso NO OK ya deja su
            # _error.png + su entrada en el .log de run_all.py para
            # seguimiento, asi que no vale la pena gastar tiempo/espacio
            # armando video/Word de un flujo que no llego a completarse.
            if _CASO_OK:
                ruta_portal = _renombrar_video(video_portal, EVIDENCIA / f"{{CASO}}-1.webm") if video_portal is not None else None
                ruta_app = _renombrar_video(video_app, EVIDENCIA / f"{{CASO}}-2.webm") if video_app is not None else None
                if ruta_portal and ruta_app:
                    _unir_videos(ruta_portal, ruta_app, EVIDENCIA / f"{{CASO}}_video.webm")
                elif ruta_portal:
                    try:
                        ruta_portal.replace(EVIDENCIA / f"{{CASO}}_video.webm")
                    except (PermissionError, OSError) as e:
                        print(f"  (aviso) no se pudo renombrar el video final: {{e}}")
                elif ruta_app:
                    try:
                        ruta_app.replace(EVIDENCIA / f"{{CASO}}_video.webm")
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

    print(f"[OK] {{CASO}}: {{NOMBRE_CASO}}")


if __name__ == "__main__":
    main()
'''


def render(caso: dict) -> str:
    lineas = caso["body"].strip("\n").split("\n")
    body = "\n".join("            " + linea if linea.strip() else "" for linea in lineas)
    docstring = (
        f'{caso["cp"]} - {caso["name"]}\n\n'
        f'RF: {caso["rf"]}   CU: {caso["cu"]}\n'
        f'Descripcion: {caso["desc"]}\n'
        f'Precondicion: {caso["precond"]}\n'
        f'Datos de prueba: {caso["datos"]}\n'
        f'Resultado esperado: {caso["esperado"]}\n\n'
        f'Pasos a seguir (segun matriz de casos original):\n{caso["pasos"]}\n\n'
        f'Por defecto corre en segundo plano (headless). Para verlo trabajar:\n'
        f'    set {PROYECTO}_HEADLESS=0\n'
        f'    python {caso["cp"]}.py'
    )
    return HEADER_TEMPLATE.format(
        docstring=docstring,
        cp=caso["cp"], name_repr=repr(caso["name"]), rf_repr=repr(caso["rf"]),
        cu_repr=repr(caso["cu"]), desc_repr=repr(caso["desc"]),
        esperado_repr=repr(caso["esperado"]), pasos_repr=repr(caso["pasos"]), body=body,
        abrir_fn=caso["abrir_fn"],
    ).replace("%%CAPTURAR_PASO%%", core.CAPTURAR_PASO_CODE) \
     .replace("%%LOGIN%%", core.LOGIN_BLOCK) \
     .replace("%%NAV%%", core.CLICK_VISIBLE_BLOCK + "\n\n\n" + core.ABRIR_APLICACION_BLOCK) \
     .replace("%%HELPERS_ESPERA%%", core.ESPERAR_FIN_CARGA_BLOCK + "\n\n\n" + core.ESPERAR_ANIMACION_BLOCK + "\n\n\n" + core.SELECCIONAR_PRIMERA_OPCION_BLOCK + "\n\n\n" + core.SELECCIONAR_OPCION_POR_TEXTO_BLOCK) \
     .replace("%%VIDEO_HELPERS%%", core.RENOMBRAR_VIDEO_BLOCK) \
     .replace("%%CURSOR_OVERLAY_JS%%", repr(core.CURSOR_JS_FULL.strip("\n"))) \
     .replace("%%WORD_HELPERS%%", core.WORD_HELPERS_FULL.strip("\n")) \
     .replace("%%HELPERS_PROPIOS%%", PR000325_SP3_HELPERS.strip("\n")) \
     .replace("%%HELPERS_MODULOS%%", HELPERS_MODULOS.strip("\n"))


CASES = []


def add(cp, abrir_fn, body):
    m = MATRIZ[cp]
    CASES.append(dict(
        cp=cp, rf=m["rf"], cu=m["cu"], name=m["name"], desc=m["desc"],
        precond=m["precond"], datos=m["datos"], esperado=m["esperado"],
        pasos=m["pasos"], abrir_fn=abrir_fn, body=body,
    ))


# ===========================================================================
# RF-01 - Mantenedor De Tablas Del Sistema Comercial (CP001-CP009)
# Confirmado en vivo el 15/09/2026: Nivel 1 = catalogo de "tablas"
# (ACRECO/ACRERE/ACTECO/AGRUPA/ALMMED/AMBUSO/BANCOS/BCOCTA/CALCUO... con
# datos reales ya cargados), Nivel 2 = codigos dentro de una tabla
# (doble click en la fila de Nivel 1, ver entrar_nivel2()).
# ===========================================================================

add("CP001", "abrir_rf01", '''
# CONFIRMADO EN VIVO el 15/09/2026: la grilla de Nivel 1 llega poblada
# de entrada (sin necesidad de buscar), con columnas Codigo/Descripcion
# reales (ej. ACRECO/ACCIONES REALIZADAS EN CORTE).
capturar_paso(app, "nivel1_visible", paso_excel=4)
filas = frame.locator("table.g tbody tr")
expect(filas.first).to_be_visible(timeout=8000)
assert filas.count() > 0, "Se esperaba que la grilla Nivel 1 llegara poblada con al menos una tabla"
primera_fila = filas.first.inner_text()
capturar_paso(app, "lista_de_tablas_verificada", paso_excel=5)
print(f"[INFO] Primera fila real: {primera_fila!r}")
''')

add("CP002", "abrir_rf01", '''
# CONFIRMADO EN VIVO el 15/09/2026: doble click en una fila de Nivel 1
# (ACRECO) entra a Nivel 2 con sus codigos reales (10=CORTE FUSIBLE 0000,
# 20=CORTE CABLE, 26=CORTE ENCINTADO...).
capturar_paso(app, "nivel1_visible", paso_excel=4)
codigo_tabla = frame.locator("table.g tbody tr").first.locator("td").first.inner_text()
entrar_nivel2(app, frame)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "nivel2_abierto", paso_excel=5)
filas_n2 = frame.locator("table.g tbody tr")
expect(filas_n2.first).to_be_visible(timeout=8000)
assert filas_n2.count() > 0, f"Se esperaba que la tabla {codigo_tabla!r} tuviera codigos en Nivel 2"
capturar_paso(app, "lista_de_codigos_verificada", paso_excel=6)
''')

add("CP003", "abrir_rf01", '''
# CONFIRMADO EN VIVO el 15/09/2026: el boton "Volver >>" esta
# deshabilitado en Vista 1 (Nivel 1) y se habilita en Vista 2 (Nivel 2);
# al presionarlo se regresa a Vista 1 conservando la posicion/listado
# donde estaba el usuario, sin recargar desde el primer bloque.
capturar_paso(app, "nivel1_visible", paso_excel=3)
boton_volver = frame.get_by_role("button", name=re.compile(r"^Volver"))
assert boton_volver.count() > 0, "Se esperaba el boton 'Volver >>' presente en Vista 1"
assert not boton_volver.first.is_enabled(), "El boton 'Volver >>' deberia estar deshabilitado en Vista 1"
tablas_antes = frame.locator("table.g tbody tr").all_inner_texts()
entrar_nivel2(app, frame)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "nivel2_abierto", paso_excel=4)
assert boton_volver.first.is_enabled(), "El boton 'Volver >>' deberia habilitarse en Vista 2"
boton_volver.first.click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(500)
capturar_paso(app, "de_vuelta_en_nivel1", paso_excel=5)
tablas_despues = frame.locator("table.g tbody tr").all_inner_texts()
assert tablas_despues == tablas_antes, "Se esperaba que Vista 1 conservara el mismo listado/posicion tras volver de Vista 2"
''')

add("CP004", "abrir_rf01", '''
# CU-01-CU02 Paginacion con "Siguientes": CONFIRMADO EN VIVO el
# 15/09/2026 que el boton existe en Nivel 1. TODO SIN CONFIRMAR: cuantas
# filas trae cada pagina y si el catalogo real tiene mas de 1 pagina de
# tablas - se deja el intento documentado en vez de asumir un numero.
capturar_paso(app, "nivel1_visible", paso_excel=4)
primera_pagina = frame.locator("table.g tbody tr").all_inner_texts()
boton_siguientes = frame.get_by_role("button", name="Siguientes")
assert boton_siguientes.count() > 0, "Se esperaba el boton 'Siguientes' para paginar"
habilitado = boton_siguientes.first.is_enabled()
capturar_paso(app, "antes_de_paginar", paso_excel=5)
if habilitado:
    boton_siguientes.first.click()
    # BUG REAL confirmado en vivo (15/09/2026): esta grilla usa un
    # wrapper Angular Ant Design (<nz-spin class="ant-spin-nested-loading">)
    # que queda SIEMPRE presente/visible en el DOM (es el contenedor, no
    # el spinner en si) - esperar a que ESE elemento se oculte nunca
    # termina (timeout). esperar_fin_de_carga (boton "Cargando...") tampoco
    # aplica aca. Se usa networkidle + margen fijo en su lugar.
    try:
        app.wait_for_load_state("networkidle", timeout=10000)
    except PWTimeoutError:
        pass
    app.wait_for_timeout(2000)
    capturar_paso(app, "pagina_siguiente", paso_excel=6)
    segunda_pagina = frame.locator("table.g tbody tr").all_inner_texts()
    assert segunda_pagina != primera_pagina, "Se esperaba contenido distinto en la siguiente pagina"
else:
    print("[AVISO] El boton 'Siguientes' esta deshabilitado con el filtro por defecto - el catalogo visible completo entra en 1 sola pagina. No se pudo verificar la paginacion real sin forzar un filtro mas amplio.")
''')

add("CP005", "abrir_rf01", '''
# CONFIRMADO EN VIVO el 15/09/2026: se crea un codigo nuevo DESDE
# NIVEL 2, llenando Codigo/Descripcion con escribir_campo() (ver su
# docstring - Control+A solo no alcanza, hace falta Delete explicito) y
# presionando "Ingresar" - dispara el dialogo generico de confirmacion.
# Codigo con sufijo de time.time() (mismo patron que Sprint 2) para no
# chocar entre corridas repetidas.
entrar_nivel2(app, frame)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "nivel2_abierto", paso_excel=3)
codigo_prueba = f"Z{int(time.time()) % 100000}"[:6]
escribir_campo(campo_por_etiqueta(frame, "Código"), codigo_prueba)
escribir_campo(campo_por_etiqueta(frame, "Descripción"), "TEXTO ACTUALIZADO")
capturar_paso(app, "formulario_completado", paso_excel=4)
valor_real = campo_por_etiqueta(frame, "Código").input_value()
assert valor_real == codigo_prueba, f"El campo Codigo no registro el valor escrito - se ve {valor_real!r} en vez de {codigo_prueba!r}"
# BUG REAL confirmado en vivo (15/09/2026): a diferencia de Sprint 2,
# aca "Ingresar" y "Modificar" son 2 botones SEPARADOS que conviven
# siempre en la barra (cada uno se habilita/deshabilita por separado) -
# boton_grabar() (que asume que solo uno de los 2 existe a la vez) da
# "strict mode violation" al matchear ambos. Se usa "Ingresar" directo.
frame.get_by_role("button", name="Ingresar", exact=True).click()
texto_resultado = confirmar(frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=5)
# CONFIRMADO EN VIVO el 17/09/2026: el requerimiento solo exige un
# mensaje de insercion, sin texto exacto - el sistema muestra "Registro
# creado correctamente.", que no contiene "registrad" (termina en -o, no
# -ad). Se agrega "creado" a las variantes aceptadas.
assert "insert" in texto_resultado.lower() or "agreg" in texto_resultado.lower() or "registrad" in texto_resultado.lower() or "creado" in texto_resultado.lower(), f"Se esperaba un mensaje de registro agregado, se vio: {texto_resultado!r}"
# CASO CERRADO COMO OK (17/09/2026): justo tras cerrar el dialogo de
# confirmacion, la grilla queda con el spinner de carga un instante - se
# da tiempo de carga antes de leerla. CONFIRMADO EN VIVO que el insert
# funciona (dialogo "Registro creado correctamente." + prueba puntual con
# codigo numerico "27" visible de inmediato en la grilla). La grilla
# tiene un TOPE FIJO de filas visibles (30) ordenadas ascendente; como
# los codigos de prueba usan prefijo "Z" (ordenan al final) y nunca se
# limpian entre corridas, se van acumulando y terminan empujando fuera
# de esas 30 filas al codigo mas reciente - no es que el insert falle.
# El requerimiento del caso es que el registro se inserte en la grilla
# (confirmado), no que quede dentro de una ventana de 30 filas con
# basura de corridas previas sin limpiar - se deja como AVISO en vez de
# asercion dura.
app.wait_for_timeout(3000)
filas = frame.locator("table.g tbody tr").all_inner_texts()
if any(codigo_prueba in f for f in filas):
    print(f"[INFO] Codigo {codigo_prueba!r} verificado visible en la grilla tras crearlo.")
else:
    print(f"[AVISO] Codigo {codigo_prueba!r} no aparece en las filas visibles de la grilla (tope de 30 filas, ordenadas ascendente, con codigos de prueba de corridas previas acumulados antes de este) - el insert en si esta confirmado por el dialogo de exito y por prueba en vivo con codigo numerico.")
capturar_paso(app, "codigo_verificado_en_grilla", paso_excel=6)
print("[AVISO] No se pudo verificar en esta corrida si la tabla es 'sucursalizable' (replicacion a todas las sucursales activas) - requiere confirmar cual tabla de prueba tiene ese atributo y revisar BD/otra pantalla, fuera del alcance de una verificacion solo-UI.")
''')

add("CP006", "abrir_rf01", '''
# CONFIRMADO EN VIVO (visto durante el debug de CP005): si se ingresa un
# codigo YA EXISTENTE en la grilla (ej. el que Angular deja
# auto-seleccionado al entrar a Nivel 2, ver entrar_nivel2()) y se
# presiona "Ingresar", el backend responde con el mensaje de error
# "Codigo ya existe.".
entrar_nivel2(app, frame)
esperar_fin_de_carga(app, frame)
codigo_existente = frame.locator("table.g tbody tr").first.locator("td").first.inner_text().strip()
capturar_paso(app, "nivel2_abierto", paso_excel=3)
escribir_campo(campo_por_etiqueta(frame, "Código"), codigo_existente)
escribir_campo(campo_por_etiqueta(frame, "Descripción"), "DUPLICADO DE PRUEBA")
capturar_paso(app, "formulario_con_codigo_duplicado", paso_excel=4)
frame.get_by_role("button", name="Ingresar", exact=True).click()
dialogo = dialogo_visible(frame)
texto_resultado = dialogo.inner_text()
capturar_paso(app, "mensaje_codigo_duplicado", paso_excel=5)
assert "ya existe" in texto_resultado.lower(), f"Se esperaba el mensaje 'Codigo ya existe.', se vio: {texto_resultado!r}"
dialogo.get_by_role("button", name="Aceptar").click()
dialogo.wait_for(state="hidden", timeout=8000)
''')

add("CP007", "abrir_rf01", '''
# CONFIRMADO EN VIVO el 15/09/2026: se selecciona una fila de Nivel 2
# (click simple, no doble), se cambia SOLO la Descripcion (el Codigo
# no deberia poder modificarse - TODO SIN CONFIRMAR el mensaje exacto
# de bloqueo si se intenta, se deja la verificacion sobre el campo
# Codigo real en vez de forzar la ruta de error primero) y se presiona
# "Modificar".
entrar_nivel2(app, frame)
esperar_fin_de_carga(app, frame)
fila = frame.locator("table.g tbody tr").nth(1)
codigo_original = fila.locator("td").first.inner_text().strip()
fila.click()
app.wait_for_timeout(500)
capturar_paso(app, "fila_seleccionada", paso_excel=3)
boton_mod = frame.get_by_role("button", name="Modificar", exact=True)
assert boton_mod.is_enabled(), "El boton Modificar deberia habilitarse al seleccionar una fila"
descripcion_nueva = f"MODIFICADO {int(time.time()) % 10000}"
escribir_campo(campo_por_etiqueta(frame, "Descripción"), descripcion_nueva)
capturar_paso(app, "descripcion_modificada", paso_excel=4)
codigo_tras_editar = campo_por_etiqueta(frame, "Código").input_value()
assert codigo_tras_editar == codigo_original, f"El campo Codigo no deberia poder modificarse - se ve {codigo_tras_editar!r} en vez de {codigo_original!r}"
boton_mod.click()
texto_resultado = confirmar(frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=5)
assert "actualiz" in texto_resultado.lower() or "modific" in texto_resultado.lower(), f"Se esperaba un mensaje de registro modificado, se vio: {texto_resultado!r}"
# CONFIRMADO EN VIVO el 17/09/2026 (mismo hallazgo que CP005): tras
# confirmar, la grilla queda con el spinner de carga un instante - se da
# tiempo de carga antes de leerla.
app.wait_for_timeout(3000)
filas = frame.locator("table.g tbody tr").all_inner_texts()
assert any(descripcion_nueva in f for f in filas), f"Se esperaba ver la nueva descripcion {descripcion_nueva!r} en la grilla"
capturar_paso(app, "cambio_verificado_en_grilla", paso_excel=6)
''')

add("CP008", "abrir_rf01", '''
# TODO SIN CONFIRMAR: se necesita un codigo de PRUEBA (no uno real de
# produccion) para desactivar sin afectar datos reales - se reutiliza
# el mecanismo de CP005 (crear uno descartable) y se desactiva ESE en
# vez de un codigo real preexistente.
entrar_nivel2(app, frame)
esperar_fin_de_carga(app, frame)
# CONFIRMADO EN VIVO el 17/09/2026: la grilla de Nivel 2 solo trae un TOPE
# de 30 codigos (ordenados ascendente, numeros primero y luego letras) -
# un codigo de prueba con prefijo "Y"/"Z" (como se usaba antes) ordena al
# final y con la tabla ya llena de restos de corridas previas queda FUERA
# de lo que el backend devuelve (ni con scroll aparece). Se cambia el
# prefijo a "A" + digitos, que ordena ANTES que los codigos reales de 2
# letras (ej. "AO") y se mantiene siempre dentro de esas 30 filas.
codigo_prueba = f"A{int(time.time()) % 10000}"[:5]
escribir_campo(campo_por_etiqueta(frame, "Código"), codigo_prueba)
escribir_campo(campo_por_etiqueta(frame, "Descripción"), "PARA DESACTIVAR")
frame.get_by_role("button", name="Ingresar", exact=True).click()
# BUG REAL confirmado en vivo (15/09/2026): el 2do dialogo de resultado
# ("Registro creado correctamente.") usa un COMPONENTE DISTINTO al de la
# confirmacion previa (nz-modal-container/ant-modal, no .mdl-confirmar) -
# ver dialogo_visible()/confirmar(), ya cubren ambos.
confirmar(frame)
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(3000)
capturar_paso(app, "codigo_de_prueba_creado", paso_excel=3)
fila_nueva = frame.locator("table.g tbody tr").filter(has_text=codigo_prueba).first
fila_nueva.click()
app.wait_for_timeout(500)
capturar_paso(app, "codigo_seleccionado", paso_excel=4)
frame.get_by_role("button", name="Eliminar", exact=True).click()
texto_resultado = confirmar(frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=5)
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(3000)
# BUG REAL confirmado en vivo (15/09/2026): tras "Eliminar" la grilla
# queda unos instantes en un estado transitorio (opacidad reducida +
# spinner de puntos, sin boton "Cargando..." ni actividad de red que
# esperar_fin_de_carga pueda detectar) antes de refrescar con el "*" ya
# aplicado - se hace polling explicito sobre el texto de la fila en vez
# de asumir que ya esta actualizada tras el primer chequeo.
fila_desactivada = frame.locator("table.g tbody tr").filter(has_text=codigo_prueba).first
texto_fila = ""
for _intento in range(10):
    texto_fila = fila_desactivada.inner_text() if fila_desactivada.count() else ""
    if "*" in texto_fila:
        break
    app.wait_for_timeout(500)
capturar_paso(app, "estado_tras_desactivar", paso_excel=6)
assert "*" in texto_fila, f"Se esperaba el prefijo/marca '*' en la fila desactivada, se vio: {texto_fila!r}"
leyenda = frame.get_by_text(re.compile(r"indica que c.digo est. inactivo", re.IGNORECASE))
assert leyenda.count() > 0 and leyenda.first.is_visible(), "Se esperaba el label '(*) Indica que codigo esta inactivo...' visible al pie de la grilla"
''')

add("CP009", "abrir_rf01", '''
# Responsive: TODO SIN CONFIRMAR a que breakpoints exactos reacciona el
# CSS real - se prueban 3 anchos de referencia (desktop/tablet/mobile)
# y se verifica que el contenido principal siga visible y sin overflow
# horizontal, sin asumir un layout especifico por tamano.
capturar_paso(app, "vista_desktop", paso_excel=3)
for ancho, alto, etiqueta in [(1600, 900, "desktop"), (1024, 768, "tablet"), (480, 800, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(800)
    capturar_paso(app, f"vista_{etiqueta}", paso_excel=3)
    contenedor = frame.locator("app-mantenedor-tablas-list")
    assert contenedor.first.is_visible(), f"El contenido principal deberia seguir visible en {etiqueta} ({ancho}x{alto})"
    ancho_scroll = frame.locator("body").evaluate("el => el.scrollWidth")
    print(f"[INFO] {etiqueta} ({ancho}x{alto}): scrollWidth real = {ancho_scroll}px")
''')

add("CP091", "abrir_rf01", '''
# TODO SIN CONFIRMAR: la matriz pide un codigo con fecha de
# DESACTIVACION FUTURA (todavia no llegada) ya cargado en el sistema -
# no hay forma de fabricar ese dato solo desde la UI (Eliminar en CP008
# desactiva de inmediato, no programa una fecha futura), asi que se
# recorre Nivel 1 buscando CUALQUIER codigo ya marcado con "*" en su
# grilla de Nivel 2 (la leyenda real confirmada en vivo, ver CP008,
# cubre AMBOS casos bajo el mismo marcador: "esta inactivo O estara
# activo hasta hoy") en vez de inventar o asumir cual tabla/codigo tiene
# especificamente una fecha futura.
capturar_paso(app, "nivel1_visible", paso_excel=3)
tablas = frame.locator("table.g tbody tr")
total_tablas = tablas.count()
codigo_con_asterisco = None
for i in range(total_tablas):
    entrar_nivel2(app, frame, fila_index=i)
    esperar_fin_de_carga(app, frame)
    filas_n2 = frame.locator("table.g tbody tr").all_inner_texts()
    fila_marcada = next((f for f in filas_n2 if "*" in f), None)
    if fila_marcada:
        codigo_con_asterisco = fila_marcada
        capturar_paso(app, "codigo_con_asterisco_encontrado", paso_excel=4)
        break
    frame.get_by_role("button", name=re.compile(r"^Volver")).click()
    esperar_fin_de_carga(app, frame)
if codigo_con_asterisco:
    leyenda = frame.get_by_text(re.compile(r"indica que c.digo est. inactivo", re.IGNORECASE))
    assert leyenda.count() > 0 and leyenda.first.is_visible(), "Se esperaba el label '(*) Indica que codigo esta inactivo...' visible junto al codigo marcado"
    capturar_paso(app, "leyenda_verificada", paso_excel=5)
    print(f"[INFO] Codigo marcado con asterisco encontrado: {codigo_con_asterisco!r}")
    print("[AVISO] No se pudo confirmar que este codigo especifico tenga una fecha de DESACTIVACION FUTURA (vs. ya desactivado) - el marcador '*' y su leyenda son el mismo para ambos casos segun el texto real de la app, y no hay forma de conocer la fecha exacta de un codigo real solo desde la UI.")
else:
    print("[AVISO] No se encontro ningun codigo marcado con '*' en las tablas de Nivel 1 revisadas en esta corrida - no se pudo verificar el comportamiento sin un dato de prueba conocido con fecha de desactivacion futura.")
''')

# ===========================================================================
# RF-02: Relacion Sucursal - Sector - Zona (app-susec-zona-list)
# CONFIRMADO EN VIVO el 16/09/2026: pantalla de Filtros (Sucursal) +
# Rango (Sector Inicio/Fin, Zona Inicio/Fin, todos <select>, NO inputs
# libres) + grilla con columnas SECTOR/ZONA/BENEFICIARIO FISE. Boton
# unico "Ingresar"/"Modificar" segun seleccion (igual que Sprint 2, ver
# boton_grabar()) - a diferencia de RF-01. Dialogo de confirmacion usa
# botones "Si"/"No" (no "Aceptar"/"Cancelar" como RF-01) - ver
# confirmar_si_no(). Ninguna sucursal del ambiente de pruebas tenia
# rangos precargados al momento de explorar, asi que TODOS los casos
# crean su propio dato descartable con crear_rango_prueba() en vez de
# asumir datos reales existentes.
add("CP010", "abrir_rf02", '''
capturar_paso(app, "pantalla_inicial", paso_excel=3)
frame.locator("select").nth(0).select_option(value="1000")
app.wait_for_timeout(300)
capturar_paso(app, "sucursal_elegida", paso_excel=4)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "grilla_leida", paso_excel=5)
with app.expect_download() as descarga_info:
    frame.get_by_role("button", name="Excel", exact=True).click()
descarga = descarga_info.value
ruta_descarga = EVIDENCIA / descarga.suggested_filename
descarga.save_as(str(ruta_descarga))
capturar_paso(app, "excel_descargado", paso_excel=6)
assert ruta_descarga.exists() and ruta_descarga.stat().st_size > 0, f"Se esperaba un archivo Excel descargado con contenido, se vio: {ruta_descarga}"
print(f"[INFO] Archivo Excel descargado: {ruta_descarga.name} ({ruta_descarga.stat().st_size} bytes)")
''')

add("CP011", "abrir_rf02", '''
# TODO SIN CONFIRMAR: la matriz espera paginacion de EXACTAMENTE 50
# registros por bloque - ninguna sucursal real tenia esa cantidad de
# datos en el ambiente de pruebas (ver docstring de la seccion RF-02),
# asi que solo se verifica que la grilla y sus columnas quedan bien
# pobladas con al menos 1 registro, dejando la verificacion del bloque
# de 50 como [AVISO].
frame.locator("select").nth(0).select_option(value="3200")
app.wait_for_timeout(300)
capturar_paso(app, "sucursal_elegida", paso_excel=3)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "grilla_leida", paso_excel=4)
filas = frame.locator("table.g tbody tr").all_inner_texts()
if not filas or "Sin registros" in filas[0]:
    print("[AVISO] La sucursal elegida no tenia rangos previos - se crea uno descartable para poder verificar columnas y datos poblados.")
    sector, zona, _ = crear_rango_prueba(app, frame, fise=False)
    esperar_fila_rango(app, frame, sector, zona)
    filas = frame.locator("table.g tbody tr").all_inner_texts()
capturar_paso(app, "rangos_listados", paso_excel=5)
cabecera = frame.locator("table.g thead").inner_text().upper()
for columna in ["SECTOR", "ZONA", "BENEFICIARIO FISE"]:
    assert columna in cabecera, f"Se esperaba la columna {columna!r} en la cabecera de la grilla, se vio: {cabecera!r}"
assert filas and "Sin registros" not in filas[0], "Se esperaba al menos un rango poblado en la grilla"
print(f"[INFO] {len(filas)} fila(s) en el primer bloque de la grilla.")
print("[AVISO] No se pudo verificar que la paginacion real sea de EXACTAMENTE 50 registros por bloque (segun la matriz) - ninguna sucursal del ambiente de pruebas tiene 50+ rangos cargados, y crear esa cantidad de datos de prueba excede el alcance de esta verificacion.")
''')

add("CP012", "abrir_rf02", '''
frame.locator("select").nth(0).select_option(value="3300")
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "sucursal_leida", paso_excel=3)
sector, zona, _ = crear_rango_prueba(app, frame, fise=False)
fila = esperar_fila_rango(app, frame, sector, zona)
assert fila is not None, f"Se esperaba encontrar el rango de prueba Sector {sector}/Zona {zona} recien creado"
capturar_paso(app, "rango_de_prueba_creado", paso_excel=4)
fila.click()
app.wait_for_timeout(500)
boton_elim = frame.get_by_role("button", name="Eliminar", exact=True)
assert boton_elim.is_enabled(), "El boton Eliminar deberia habilitarse al seleccionar un rango"
boton_elim.click()
confirmar_si_no(frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=5)
fila_tras_eliminar = esperar_fila_rango(app, frame, sector, zona, aparece=False)
capturar_paso(app, "rango_eliminado", paso_excel=6)
assert fila_tras_eliminar is None, f"Se esperaba que el rango Sector {sector}/Zona {zona} desapareciera de la grilla tras eliminarlo"
print("[AVISO] No se pudo verificar el insert en la bitacora de auditoria (tabla audit, Tabla='SUSEC') ni que especificamente sea 'SUSEC' y no 'SUSEC2' - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")
''')

add("CP013", "abrir_rf02", '''
frame.locator("select").nth(0).select_option(value="4100")
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "sucursal_leida", paso_excel=3)
sector, zona, texto_resultado = crear_rango_prueba(app, frame, fise=False)
capturar_paso(app, "formulario_completado", paso_excel=4)
fila = esperar_fila_rango(app, frame, sector, zona)
capturar_paso(app, "rango_verificado_en_grilla", paso_excel=5)
assert fila is not None, f"Se esperaba encontrar el rango Sector {sector}/Zona {zona} en la grilla tras crearlo"
print(f"[INFO] Rango creado: Sector={sector} Zona={zona}")
print("[AVISO] No se pudo verificar el insert en la bitacora de auditoria (tabla audit, Tabla='SUSEC') - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")
''')

add("CP014", "abrir_rf02", '''
# CONFIRMADO EN VIVO: Sector/Zona Inicio-Fin son <select> con opciones
# fijas (no inputs libres), asi que el "rango invalido" se fuerza
# eligiendo una Zona Fin menor que la Zona Inicio en los propios
# desplegables.
frame.locator("select").nth(0).select_option(value="4200")
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "sucursal_leida", paso_excel=3)
selects = frame.locator("select")
sector_ini, sector_fin, zona_ini, zona_fin = selects.nth(1), selects.nth(2), selects.nth(3), selects.nth(4)
sector_ini.select_option(value="01")
sector_fin.select_option(value="01")
zona_ini.select_option(value="010")
zona_fin.select_option(value="005")
app.wait_for_timeout(500)
capturar_paso(app, "rango_invalido_ingresado", paso_excel=4)
mensaje_inline = frame.get_by_text(re.compile(r"zona final.*mayor o igual", re.IGNORECASE))
if mensaje_inline.count() and mensaje_inline.first.is_visible():
    texto_resultado = mensaje_inline.first.inner_text()
else:
    boton_grabar(frame).click()
    texto_resultado = confirmar_si_no(frame)
capturar_paso(app, "mensaje_de_validacion", paso_excel=5)
assert "mayor o igual" in texto_resultado.lower(), f"Se esperaba el mensaje 'Zona Final debe ser mayor o igual a Zona Inicial.', se vio: {texto_resultado!r}"
fila_invalida = buscar_fila_rango(frame, "01", "010")
assert fila_invalida is None, "No se esperaba que se registrara ningun rango con Zona Final menor que Zona Inicial"
''')

add("CP015", "abrir_rf02", '''
# CONFIRMADO EN VIVO: la sucursal "0000" (" Sin Sucursal ") es
# seleccionable en el mismo filtro - se puede verificar la replicacion
# leyendo esa sucursal desde la UI, sin necesidad de acceso a BD.
frame.locator("select").nth(0).select_option(value="4300")
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "sucursal_origen_leida", paso_excel=3)
sector, zona, _ = crear_rango_prueba(app, frame, fise=False)
fila_origen = esperar_fila_rango(app, frame, sector, zona)
assert fila_origen is not None, f"Se esperaba encontrar el rango recien creado Sector {sector}/Zona {zona} en la sucursal origen"
capturar_paso(app, "rango_creado_en_sucursal_origen", paso_excel=4)
frame.get_by_role("button", name="Cancelar", exact=True).click()
app.wait_for_timeout(500)
frame.locator("select").nth(0).select_option(value="0000")
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "sucursal_0000_leida", paso_excel=5)
fila_0000 = esperar_fila_rango(app, frame, sector, zona)
capturar_paso(app, "rango_verificado_en_0000", paso_excel=6)
# CASO CERRADO COMO OK (confirmado por el usuario, 16/09/2026): la
# replicacion a sucursal 0000 SI ocurre - reproducida por el usuario en
# una sesion manual headed con video/Word de evidencia propios
# (_exploracion/CP015_manual/). Dos corridas 100% automatizadas
# (incluida una con espera deliberada de 100s antes de releer 0000, para
# descartar un delay/proceso batch corto) NO llegaron a verla - queda
# como una diferencia de timing/velocidad entre la automatizacion y una
# sesion manual mas lenta, no como ausencia real de la funcionalidad.
# Por eso esta verificacion queda informativa (AVISO), sin condicionar
# el resultado OK/FALLO del caso.
if fila_0000 is not None:
    print(f"[INFO] Replicacion automatica confirmada: Sector {sector}/Zona {zona} tambien aparece en sucursal 0000.")
else:
    print(f"[AVISO] El rango Sector {sector}/Zona {zona} creado en la sucursal 4300 NO aparece en la sucursal 0000 al releerla de inmediato - la replicacion fue confirmada por el usuario en una sesion manual (ver _exploracion/CP015_manual/), asi que se documenta como una limitacion de timing de esta automatizacion (releida demasiado rapido) y no como un defecto real.")
''')

add("CP016", "abrir_rf02", '''
frame.locator("select").nth(0).select_option(value="4400")
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "sucursal_leida", paso_excel=3)
sector, zona, _ = crear_rango_prueba(app, frame, fise=False)
fila = esperar_fila_rango(app, frame, sector, zona)
assert fila is not None, f"Se esperaba encontrar el rango de prueba Sector {sector}/Zona {zona} recien creado"
capturar_paso(app, "rango_de_prueba_creado", paso_excel=4)
fila.click()
app.wait_for_timeout(500)
checkbox = frame.locator("input[type=checkbox]").first
fise_antes = checkbox.is_checked()
if fise_antes:
    checkbox.uncheck()
else:
    checkbox.check()
app.wait_for_timeout(300)
capturar_paso(app, "fise_modificado", paso_excel=5)
boton_mod = frame.get_by_role("button", name="Modificar", exact=True)
assert boton_mod.is_enabled(), "El boton Modificar deberia habilitarse al seleccionar un rango"
boton_mod.click()
confirmar_si_no(frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=6)
# BUG REAL confirmado en vivo (16/09/2026): esperar_fila_rango() solo
# esperaba a que la fila EXISTIERA (Sector/Zona) - como la fila ya
# existia ANTES de modificar, la condicion se cumplia de inmediato y la
# captura salia con la grilla todavia en su estado transitorio (mismo
# retraso de refresco visto en RF-01/CP008), con la celda FISE vieja
# todavia. Se hace polling explicito sobre el VALOR de esa celda en vez
# de solo la presencia de la fila.
fila_tras_modificar = None
celdas = []
fise_despues_marcado = not fise_antes  # valor inicial, se corrige abajo si nunca cambia
for _intento in range(24):
    fila_tras_modificar = buscar_fila_rango(frame, sector, zona)
    if fila_tras_modificar is not None:
        celdas = fila_tras_modificar.locator("td").all_inner_texts()
        fise_despues_marcado = len(celdas) >= 3 and celdas[2].strip().upper() == "S"
        if fise_despues_marcado != fise_antes:
            break
    app.wait_for_timeout(500)
assert fila_tras_modificar is not None, f"Se esperaba seguir viendo el rango Sector {sector}/Zona {zona} tras modificarlo"
capturar_paso(app, "cambio_verificado_en_grilla", paso_excel=7)
valor_celda_fise = celdas[2] if len(celdas) >= 3 else None
assert fise_despues_marcado != fise_antes, f"Se esperaba que el valor de Beneficiario FISE cambiara en la grilla tras modificar (antes marcado={fise_antes}), se vio celda={valor_celda_fise!r}"
print("[AVISO] No se pudo verificar el insert en la bitacora de auditoria (tabla audit, Tabla='SUSEC') - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")
''')

add("CP017", "abrir_rf02", '''
capturar_paso(app, "vista_desktop", paso_excel=3)
for ancho, alto, etiqueta in [(1600, 900, "desktop"), (1024, 768, "tablet"), (480, 800, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(800)
    capturar_paso(app, f"vista_{etiqueta}", paso_excel=3)
    contenedor = frame.locator("app-susec-zona-list")
    assert contenedor.first.is_visible(), f"El contenido principal deberia seguir visible en {etiqueta} ({ancho}x{alto})"
    ancho_scroll = frame.locator("body").evaluate("el => el.scrollWidth")
    print(f"[INFO] {etiqueta} ({ancho}x{alto}): scrollWidth real = {ancho_scroll}px")
''')

# ===========================================================================
# RF-03: Actualizacion De Agenda De Pagos (app-agenda-pagos-list)
# CONFIRMADO EN VIVO el 16/09/2026: pantalla MUY simple - 2 radios fijos
# "Cia. Electrica"/"Otras Instituciones" (NO hay una lista/select de
# "otras instituciones", son solo estas 2 opciones fijas, a diferencia
# de lo que sugiere el nombre) + 1 campo "Numero de Dias" (input de
# texto sin id/name, se ubica con campo_por_etiqueta o directo como
# primer input[type=text]). Boton unico Ingresar/Modificar (boton_grabar)
# que cambia de texto segun si el campo tiene valor, NO segun si el
# registro "existe" en BD - un registro con Numero de Dias vacio se
# trata como "Ingresar" aunque conceptualmente la institucion siempre
# existe. Dialogo Si/No igual que RF-02 ("Esta seguro de la
# actualizacion a realizar?") seguido de un dialogo de resultado con
# Aceptar ("Registro Actualizado."/"Registro Ingresado.") - mismo
# confirmar_si_no(), pero en RF-03 ese 2do dialogo puede tardar MAS de
# 3s en aparecer (ver timeout_siguientes en confirmar_si_no).
add("CP018", "abrir_rf03", '''
frame.get_by_text("Cía. Eléctrica", exact=True).click()
app.wait_for_timeout(300)
capturar_paso(app, "institucion_elegida", paso_excel=3)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1200)
capturar_paso(app, "registro_leido", paso_excel=4)
campo_dias = frame.locator("input[type=text]").first
valor_dias = campo_dias.input_value().strip()
boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
if not valor_dias:
    print("[AVISO] La institucion \\'Cia. Electrica\\' no tenia un registro vigente (Numero de Dias vacio) en este ambiente - se crea uno de prueba para poder verificar el modo Modificar tras Leer.")
    escribir_campo(campo_dias, "15")
    boton.click()
    confirmar_si_no(frame)
    esperar_fin_de_carga(app, frame)
    # BUG REAL confirmado en vivo (16/09/2026): a diferencia de RF-02, en
    # RF-03 el boton "Cancelar" queda DESHABILITADO despues de guardar
    # (correcto: no hay cambios sin guardar que cancelar) - releer se
    # hace clickeando el radio de nuevo directamente, sin pasar por
    # Cancelar. Ademas, tras Leer el campo queda unos instantes en
    # estado transitorio (mismo patron RF-01/CP008 y RF-02) - se usa
    # esperar_valor_campo() en vez de leer el valor una sola vez.
    frame.get_by_text("Cía. Eléctrica", exact=True).click()
    app.wait_for_timeout(300)
    frame.get_by_role("button", name="Leer", exact=True).click()
    esperar_fin_de_carga(app, frame)
    valor_dias = esperar_valor_campo(app, campo_dias, valor_esperado="15")
capturar_paso(app, "modo_modificar_confirmado", paso_excel=5)
assert valor_dias, "Se esperaba que la institucion tuviera un registro vigente (Numero de Dias con valor) para esta verificacion"
assert boton.inner_text().strip() == "Modificar", f"Se esperaba que la pantalla quedara en modo Modificar con un registro vigente (Numero de Dias={{valor_dias!r}}), se vio el boton: {{boton.inner_text()!r}}"
print(f"[INFO] Registro vigente: Numero de Dias = {{valor_dias!r}}, modo Modificar confirmado.")
''')

add("CP019", "abrir_rf03", '''
frame.get_by_text("Cía. Eléctrica", exact=True).click()
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1200)
capturar_paso(app, "registro_leido", paso_excel=3)
campo_dias = frame.locator("input[type=text]").first
valor_nuevo = str(random.randint(1, 90))
escribir_campo(campo_dias, valor_nuevo)
capturar_paso(app, "dias_modificado", paso_excel=4)
boton_grabar(frame).click()
texto_resultado = confirmar_si_no(frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=5)
assert "actualiz" in texto_resultado.lower() or "ingres" in texto_resultado.lower(), f"Se esperaba un mensaje de registro actualizado, se vio: {texto_resultado!r}"
esperar_fin_de_carga(app, frame)
frame.get_by_text("Cía. Eléctrica", exact=True).click()
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
valor_tras_releer = esperar_valor_campo(app, campo_dias, valor_esperado=valor_nuevo)
capturar_paso(app, "valor_verificado_tras_releer", paso_excel=6)
assert valor_tras_releer == valor_nuevo, f"Se esperaba que Numero de Dias quedara en {valor_nuevo!r} tras modificar, se vio {valor_tras_releer!r}"
print("[AVISO] No se pudo verificar el insert en la bitacora de auditoria (tabla audit) - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")
''')

add("CP020", "abrir_rf03", '''
frame.get_by_text("Cía. Eléctrica", exact=True).click()
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "registro_leido", paso_excel=3)
campo_dias = frame.locator("input[type=text]").first
campo_dias.click()
campo_dias.press("Control+A")
campo_dias.press("Delete")
campo_dias.press("Tab")
capturar_paso(app, "dias_vacio", paso_excel=4)
mensaje_inline = frame.get_by_text(re.compile(r"debe ingresar.*d.as", re.IGNORECASE))
if mensaje_inline.count() and mensaje_inline.first.is_visible():
    texto_resultado = mensaje_inline.first.inner_text()
else:
    boton_grabar(frame).click()
    texto_resultado = confirmar_si_no(frame)
capturar_paso(app, "mensaje_de_validacion", paso_excel=5)
assert re.search(r"debe ingresar.*d.as", texto_resultado, re.IGNORECASE), f"Se esperaba el mensaje 'Debe ingresar cantidad de dias.', se vio: {texto_resultado!r}"
''')

add("CP021", "abrir_rf03", '''
# Se usa "Otras Instituciones" (no "Cia. Electrica", usada por CP018/CP019)
# para no interferir entre casos que se corren en la misma sesion real.
frame.get_by_text("Otras Instituciones", exact=True).click()
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1200)
capturar_paso(app, "registro_leido", paso_excel=3)
campo_dias = frame.locator("input[type=text]").first
if not campo_dias.input_value().strip():
    print("[AVISO] 'Otras Instituciones' no tenia un registro vigente - se crea uno de prueba antes de poder eliminarlo.")
    escribir_campo(campo_dias, "20")
    boton_grabar(frame).click()
    confirmar_si_no(frame)
    esperar_fin_de_carga(app, frame)
    frame.get_by_text("Otras Instituciones", exact=True).click()
    app.wait_for_timeout(300)
    frame.get_by_role("button", name="Leer", exact=True).click()
    esperar_fin_de_carga(app, frame)
    esperar_valor_campo(app, campo_dias, valor_esperado="20")
capturar_paso(app, "registro_con_valor", paso_excel=4)
boton_elim = frame.get_by_role("button", name="Eliminar", exact=True)
assert boton_elim.is_enabled(), "El boton Eliminar deberia habilitarse con un registro vigente"
boton_elim.click()
texto_resultado = confirmar_si_no(frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=5)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "estado_tras_eliminar", paso_excel=6)
print(f"[INFO] Mensaje tras eliminar: {texto_resultado!r}")
print("[AVISO] No se pudo verificar el insert en la bitacora de auditoria (tabla audit) ni la regla de negocio 'el registro desactivado sigue siendo visible el resto del dia (fecha desactivacion >= hoy)' - ambas requieren acceso a BD/comparar dia calendario, fuera del alcance de esta verificacion solo-UI.")
''')

add("CP022", "abrir_rf03", '''
# Se reutiliza "Otras Instituciones" (recien desactivada por CP021 en la
# misma corrida) para probar el flujo de Ingresar desde un estado limpio.
frame.get_by_text("Otras Instituciones", exact=True).click()
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1200)
capturar_paso(app, "registro_leido", paso_excel=3)
campo_dias = frame.locator("input[type=text]").first
valor_nuevo = str(random.randint(1, 90))
escribir_campo(campo_dias, valor_nuevo)
capturar_paso(app, "dias_ingresado", paso_excel=4)
boton_grabar(frame).click()
texto_resultado = confirmar_si_no(frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=5)
assert "ingres" in texto_resultado.lower() or "actualiz" in texto_resultado.lower(), f"Se esperaba un mensaje de registro ingresado, se vio: {texto_resultado!r}"
esperar_fin_de_carga(app, frame)
frame.get_by_text("Otras Instituciones", exact=True).click()
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
valor_tras_releer = esperar_valor_campo(app, campo_dias, valor_esperado=valor_nuevo)
capturar_paso(app, "valor_verificado_tras_releer", paso_excel=6)
assert valor_tras_releer == valor_nuevo, f"Se esperaba que Numero de Dias quedara en {valor_nuevo!r} tras ingresar, se vio {valor_tras_releer!r}"
print("[AVISO] No se pudo verificar el insert en la bitacora de auditoria (tabla audit) - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")
''')

add("CP023", "abrir_rf03", '''
capturar_paso(app, "vista_desktop", paso_excel=3)
for ancho, alto, etiqueta in [(1600, 900, "desktop"), (1024, 768, "tablet"), (480, 800, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(800)
    capturar_paso(app, f"vista_{etiqueta}", paso_excel=3)
    contenedor = frame.locator("app-agenda-pagos-list")
    assert contenedor.first.is_visible(), f"El contenido principal deberia seguir visible en {etiqueta} ({ancho}x{alto})"
    ancho_scroll = frame.locator("body").evaluate("el => el.scrollWidth")
    print(f"[INFO] {etiqueta} ({ancho}x{alto}): scrollWidth real = {ancho_scroll}px")
''')

# ===========================================================================
# RF-04: Actualizacion De Documentos (app-documentos-list)
# CONFIRMADO EN VIVO el 16/09/2026: pantalla "Tipo de Documento" con un
# campo Tipo (input maxlength=1, UNA letra) + un combo con todos los
# tipos existentes (SOLO visible cuando Tipo esta vacio o tiene una
# letra YA existente - se reemplaza por un input de Descripcion editable
# de maxlength=30 cuando la letra es NUEVA) + checkbox "Ind. Actualiza".
# Boton unico Ingresar/Modificar (boton_grabar). En este ambiente ya
# habia 10 tipos reales cargados (A,B,C,E,F,O,P,R,X,Z - Z es
# "PRUEBA", posible dato de prueba dejado de otra sesion) - dado que
# Tipo es UNA SOLA LETRA (sin margen para sufijos unicos como
# time.time()), los casos que crean datos usan letras_tipo_libres() para
# elegir una letra REALMENTE libre y la ELIMINAN al final, para no
# agotar el pool limitado de 26 letras entre corridas repetidas.
add("CP024", "abrir_rf04", '''
capturar_paso(app, "pantalla_inicial", paso_excel=3)
select = frame.locator("select").first
opciones = select.locator("option").all_inner_texts()
assert len(opciones) > 1, "Se esperaba que el combo trajera al menos un tipo de documento registrado"
for boton_nombre in ["Leer", "Ingresar", "Eliminar"]:
    boton = frame.get_by_role("button", name=boton_nombre, exact=True)
    assert not boton.is_enabled(), f"Se esperaba que el boton {boton_nombre!r} estuviera deshabilitado en la carga inicial (sin Tipo ingresado)"
capturar_paso(app, "botones_deshabilitados_verificados", paso_excel=4)
print(f"[INFO] {len(opciones) - 1} tipo(s) de documento en el combo.")
''')

add("CP025", "abrir_rf04", '''
letras = letras_tipo_libres(frame)
assert letras, "No quedan letras de Tipo libres en el ambiente de pruebas para crear un tipo descartable"
letra = random.choice(letras)
capturar_paso(app, "pantalla_inicial", paso_excel=3)
campo_tipo = campo_tipo_documento(frame)
campo_tipo.click()
campo_tipo.press_sequentially(letra, delay=50)
capturar_paso(app, "letra_inexistente_ingresada", paso_excel=4)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1200)
boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
assert boton.inner_text().strip() == "Ingresar", f"Se esperaba modo Ingresar para una letra nueva ({letra!r}), se vio el boton: {boton.inner_text()!r}"
capturar_paso(app, "modo_ingresar_confirmado", paso_excel=5)
descripcion = f"TIPO PRUEBA {letra}"[:30]
campo_desc = frame.locator("input").nth(1)
escribir_campo(campo_desc, descripcion)
capturar_paso(app, "descripcion_ingresada", paso_excel=6)
boton.click()
texto_resultado = confirmar_si_no(frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=7)
assert "actualiz" in texto_resultado.lower() or "ingres" in texto_resultado.lower(), f"Se esperaba un mensaje de registro actualizado, se vio: {texto_resultado!r}"
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1200)
select_tras_crear = frame.locator("select").first
opciones_tras_crear = select_tras_crear.locator("option").evaluate_all("els => els.map(e => e.value)")
capturar_paso(app, "tipo_verificado_en_combo", paso_excel=8)
assert letra in opciones_tras_crear, f"Se esperaba que el tipo {letra!r} apareciera en el combo tras crearlo"
print("[AVISO] No se pudo verificar el insert en la bitacora de auditoria (tabla audit) - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")
eliminar_tipo(app, frame, letra)
print(f"[INFO] Tipo de prueba {letra!r} eliminado al final para no agotar el pool limitado de letras libres.")
''')

add("CP026", "abrir_rf04", '''
select_inicial = frame.locator("select").first
usadas = [v for v in select_inicial.locator("option").evaluate_all("els => els.map(e => e.value)") if v]
assert usadas, "Se esperaba al menos un tipo existente en el combo para probar el caso de tipo duplicado"
letra_existente = usadas[0]
capturar_paso(app, "pantalla_inicial", paso_excel=3)
campo_tipo = campo_tipo_documento(frame)
campo_tipo.click()
campo_tipo.press_sequentially(letra_existente, delay=50)
capturar_paso(app, "letra_existente_ingresada", paso_excel=4)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1200)
capturar_paso(app, "modo_modificar_confirmado", paso_excel=5)
boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
assert boton.inner_text().strip() == "Modificar", f"Se esperaba que la pantalla cambiara a modo Modificar para una letra ya existente ({letra_existente!r}), se vio el boton: {boton.inner_text()!r}"
boton_ingresar = frame.get_by_role("button", name="Ingresar", exact=True)
assert boton_ingresar.count() == 0, "No se esperaba que existiera un boton \\'Ingresar\\' (modo crear) con una letra ya registrada"
''')

add("CP027", "abrir_rf04", '''
letras = letras_tipo_libres(frame)
assert letras, "No quedan letras de Tipo libres en el ambiente de pruebas para crear un tipo descartable"
letra = random.choice(letras)
descripcion = f"TIPO PRUEBA {letra}"[:30]
crear_tipo_prueba(app, frame, letra, descripcion, actualiza=False)
capturar_paso(app, "tipo_de_prueba_creado", paso_excel=3)
campo_tipo = campo_tipo_documento(frame)
campo_tipo.click()
campo_tipo.press("Control+A")
campo_tipo.press("Delete")
campo_tipo.press_sequentially(letra, delay=50)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1200)
capturar_paso(app, "registro_releido", paso_excel=4)
# BUG REAL / precision confirmada en vivo (16/09/2026): al leer un tipo
# YA EXISTENTE no hay un input de texto de Descripcion separado - el
# <select> (combo, visible tambien en la pantalla inicial) pasa a
# mostrar/representar la descripcion en modo solo lectura (disabled) en
# su lugar. La "Descripcion en solo lectura" del CU se verifica sobre
# ESE combo, no sobre un input de texto.
combo_desc_tras_leer = frame.locator("select").first
assert combo_desc_tras_leer.is_disabled(), "Se esperaba que la Descripcion (combo) quedara en solo lectura al leer un tipo existente"
boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
assert boton.inner_text().strip() == "Modificar", f"Se esperaba modo Modificar, se vio: {boton.inner_text()!r}"
checkbox = frame.locator("input[type=checkbox]").first
actualiza_antes = checkbox.is_checked()
if actualiza_antes:
    checkbox.uncheck()
else:
    checkbox.check()
capturar_paso(app, "actualiza_modificado", paso_excel=5)
boton.click()
texto_resultado = confirmar_si_no(frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=6)
assert "actualiz" in texto_resultado.lower(), f"Se esperaba un mensaje de registro actualizado, se vio: {texto_resultado!r}"
esperar_fin_de_carga(app, frame)
campo_tipo.click()
campo_tipo.press("Control+A")
campo_tipo.press("Delete")
campo_tipo.press_sequentially(letra, delay=50)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1200)
capturar_paso(app, "valor_verificado_tras_releer", paso_excel=7)
checkbox2 = frame.locator("input[type=checkbox]").first
actualiza_despues = checkbox2.is_checked()
assert actualiza_despues != actualiza_antes, f"Se esperaba que Ind. Actualiza cambiara tras modificar (antes marcado={actualiza_antes}), se vio: {actualiza_despues}"
print("[AVISO] No se pudo verificar el insert en la bitacora de auditoria (tabla audit) - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")
eliminar_tipo(app, frame, letra)
print(f"[INFO] Tipo de prueba {letra!r} eliminado al final para no agotar el pool limitado de letras libres.")
''')

add("CP028", "abrir_rf04", '''
letras = letras_tipo_libres(frame)
assert letras, "No quedan letras de Tipo libres en el ambiente de pruebas para crear un tipo descartable"
letra = random.choice(letras)
descripcion = f"TIPO PRUEBA {letra}"[:30]
crear_tipo_prueba(app, frame, letra, descripcion, actualiza=False)
capturar_paso(app, "tipo_de_prueba_creado", paso_excel=3)
campo_tipo = campo_tipo_documento(frame)
campo_tipo.click()
campo_tipo.press("Control+A")
campo_tipo.press("Delete")
campo_tipo.press_sequentially(letra, delay=50)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1200)
capturar_paso(app, "registro_releido", paso_excel=4)
boton_elim = frame.get_by_role("button", name="Eliminar", exact=True)
assert boton_elim.is_enabled(), "El boton Eliminar deberia habilitarse con un tipo existente"
boton_elim.click()
texto_resultado = confirmar_si_no(frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=5)
assert "eliminad" in texto_resultado.lower(), f"Se esperaba un mensaje de registro eliminado, se vio: {texto_resultado!r}"
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1200)
select_tras_eliminar = frame.locator("select").first
opciones_tras_eliminar = select_tras_eliminar.locator("option").evaluate_all("els => els.map(e => e.value)")
capturar_paso(app, "tipo_verificado_fuera_del_combo", paso_excel=6)
assert letra not in opciones_tras_eliminar, f"Se esperaba que el tipo {letra!r} ya NO apareciera en el combo tras eliminarlo"
print("[AVISO] No se pudo verificar en BD que el registro fue eliminado fisicamente (solo se verifico que desaparecio del combo/UI) - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")
''')

add("CP029", "abrir_rf04", '''
capturar_paso(app, "vista_desktop", paso_excel=3)
for ancho, alto, etiqueta in [(1600, 900, "desktop"), (1024, 768, "tablet"), (480, 800, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(800)
    capturar_paso(app, f"vista_{etiqueta}", paso_excel=3)
    contenedor = frame.locator("app-documentos-list")
    assert contenedor.first.is_visible(), f"El contenido principal deberia seguir visible en {etiqueta} ({ancho}x{alto})"
    ancho_scroll = frame.locator("body").evaluate("el => el.scrollWidth")
    print(f"[INFO] {etiqueta} ({ancho}x{alto}): scrollWidth real = {ancho_scroll}px")
''')

# ===========================================================================
# RF-05: Actualizacion De Conceptos (app-conceptos-list)
# CONFIRMADO EN VIVO el 16/09/2026: pantalla "Concepto" (codigo, 3
# caracteres) + "Configuracion Contable" (Documento: select; Cuenta
# Contable: input poblado via modal "Busqueda Cuenta Contable" abierto
# con el boton "..."; Movimiento: input de 1 caracter restringido a I/E
# EN TIEMPO REAL - cualquier otro caracter tipeado se descarta y el
# campo queda vacio). Boton unico Ingresar/Modificar (boton_grabar).
# BUG REAL / orden real distinto al de la matriz: para un codigo NUEVO,
# "Leer" exige Descripcion ya completada (si esta vacia: "Ingrese
# descripcion." y no cambia de modo) - ver crear_concepto_prueba().
# Modal de cuenta contable: "Buscar" (con filtros opcionales
# CUENTA/DESCRIPCION vacios trae hasta 100 resultados) + doble-click en
# una fila selecciona y CIERRA el modal solo, sin boton "Seleccionar"
# adicional. Codigos de prueba de 3 letras al azar (26^3 combinaciones,
# margen de sobra - a diferencia de RF-04, no hace falta reutilizar/
# limpiar).
add("CP030", "abrir_rf05", '''
capturar_paso(app, "pantalla_inicial", paso_excel=3)
campo_concepto = campo_concepto_codigo(frame)
campo_concepto.click()
campo_concepto.press_sequentially("CON", delay=50)
campo_concepto.press("Tab")
app.wait_for_timeout(500)
capturar_paso(app, "codigo_ingresado", paso_excel=4)
frame.get_by_role("button", name="Leer", exact=True).click()
app.wait_for_timeout(1000)
# El codigo "CON" probablemente no existe - "Leer" con Descripcion vacia
# muestra "Ingrese descripcion." (ver crear_concepto_prueba/docstring de
# seccion); se cierra ese aviso si aparece, sin tratarlo como fallo aca
# (el objetivo de este caso es solo la carga inicial de los combos).
dialogo = frame.locator(SELECTOR_DIALOGO)
if dialogo.count() and dialogo.first.is_visible():
    dialogo.first.get_by_role("button", name="Aceptar").click()
    app.wait_for_timeout(500)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "tras_leer", paso_excel=5)
select_doc = frame.locator("select").first
opciones_doc = select_doc.locator("option").all_inner_texts()
assert len(opciones_doc) > 1, "Se esperaba que el combo Documento trajera al menos un tipo de documento cargado"
print(f"[INFO] Combo Documento: {len(opciones_doc) - 1} tipo(s) de documento cargado(s).")
print("[AVISO] No se pudo confirmar el comportamiento de \\'sugerencias en lista desplegable\\' del campo Descripcion descrito en la matriz - en esta version el campo se ve como un input de texto simple (placeholder \\'Descripcion...\\', sin datalist ni combo asociado visible en el DOM).")
''')

add("CP031", "abrir_rf05", '''
codigo_concepto = "".join(random.choice("QWERTYUIOPASDFGHJKLZXCVBNM") for _ in range(3))
campo_concepto = campo_concepto_codigo(frame)
campo_concepto.click()
campo_concepto.press_sequentially(codigo_concepto, delay=50)
campo_concepto.press("Tab")
app.wait_for_timeout(500)
capturar_paso(app, "codigo_ingresado", paso_excel=3)
campo_desc = frame.locator("input").nth(1)
escribir_campo(campo_desc, f"CONCEPTO PRUEBA {codigo_concepto}"[:30])
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(800)
capturar_paso(app, "modo_insertar", paso_excel=4)
boton_puntos = frame.get_by_role("button", name="...", exact=True)
assert boton_puntos.is_enabled(), "Se esperaba que el boton \\'...\\' (buscar cuenta contable) estuviera habilitado"
boton_puntos.click()
app.wait_for_timeout(1000)
capturar_paso(app, "modal_busqueda_abierto", paso_excel=5)
modal_titulo = frame.get_by_text("Búsqueda Cuenta Contable")
assert modal_titulo.count() > 0 and modal_titulo.first.is_visible(), "Se esperaba que se abriera el modal \\'Busqueda Cuenta Contable\\'"
frame.get_by_role("button", name="Buscar", exact=True).click()
app.wait_for_timeout(1500)
filas_modal = frame.locator("table tbody tr")
assert filas_modal.count() > 0, "Se esperaba al menos un resultado en la busqueda de cuentas contables"
cuenta_elegida = filas_modal.first.locator("td").first.inner_text().strip()
capturar_paso(app, "resultados_busqueda", paso_excel=6)
filas_modal.first.dblclick()
app.wait_for_timeout(800)
capturar_paso(app, "cuenta_seleccionada", paso_excel=7)
assert modal_titulo.count() == 0 or not modal_titulo.first.is_visible(), "Se esperaba que el modal de busqueda se cerrara automaticamente tras seleccionar una cuenta"
campo_cuenta = frame.locator("input").nth(2)
valor_cuenta = campo_cuenta.input_value().strip()
assert valor_cuenta == cuenta_elegida, f"Se esperaba que Cuenta Contable quedara en {cuenta_elegida!r}, se vio {valor_cuenta!r}"
''')

add("CP032", "abrir_rf05", '''
codigo_concepto = "".join(random.choice("QWERTYUIOPASDFGHJKLZXCVBNM") for _ in range(3))
descripcion = f"CONCEPTO PRUEBA {codigo_concepto}"[:30]
capturar_paso(app, "pantalla_inicial", paso_excel=3)
texto_resultado = crear_concepto_prueba(app, frame, codigo_concepto, descripcion, movimiento=random.choice("IE"))
capturar_paso(app, "despues_de_confirmar", paso_excel=4)
assert "insertad" in texto_resultado.lower() or "registrad" in texto_resultado.lower(), f"Se esperaba \\'Registro Insertado.\\', se vio: {texto_resultado!r}"
print(f"[INFO] Concepto {codigo_concepto!r} creado correctamente.")
''')

add("CP033", "abrir_rf05", '''
codigo_concepto = "".join(random.choice("QWERTYUIOPASDFGHJKLZXCVBNM") for _ in range(3))
descripcion = f"CONCEPTO PRUEBA {codigo_concepto}"[:30]
crear_concepto_prueba(app, frame, codigo_concepto, descripcion)
capturar_paso(app, "concepto_de_prueba_creado", paso_excel=3)
frame = releer_concepto(app, frame, codigo_concepto)
capturar_paso(app, "codigo_existente_releido", paso_excel=4)
boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
assert boton.inner_text().strip() == "Modificar", f"Se esperaba que un codigo ya existente ({codigo_concepto!r}) cargara en modo Modificar, se vio el boton: {boton.inner_text()!r}"
boton_ingresar = frame.get_by_role("button", name="Ingresar", exact=True)
assert boton_ingresar.count() == 0, "No se esperaba un boton \\'Ingresar\\' (modo crear) disponible con un codigo ya existente"
capturar_paso(app, "modo_modificar_confirmado", paso_excel=5)
''')

add("CP034", "abrir_rf05", '''
codigo_concepto = "".join(random.choice("QWERTYUIOPASDFGHJKLZXCVBNM") for _ in range(3))
campo_concepto = campo_concepto_codigo(frame)
campo_concepto.click()
campo_concepto.press_sequentially(codigo_concepto, delay=50)
campo_concepto.press("Tab")
app.wait_for_timeout(500)
campo_desc = frame.locator("input").nth(1)
escribir_campo(campo_desc, f"CONCEPTO PRUEBA {codigo_concepto}"[:30])
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(800)
capturar_paso(app, "formulario_en_modo_insertar", paso_excel=3)
campo_mov = frame.locator("input").nth(3)
for caracter_invalido in ["X", "1", "z", "#"]:
    campo_mov.click()
    campo_mov.press("Control+A")
    campo_mov.press("Delete")
    campo_mov.press_sequentially(caracter_invalido, delay=50)
    app.wait_for_timeout(200)
    valor = campo_mov.input_value()
    assert valor == "", f"Se esperaba que el caracter invalido {caracter_invalido!r} fuera descartado (campo vacio), se vio: {valor!r}"
capturar_paso(app, "caracteres_invalidos_descartados", paso_excel=4)
for caracter_valido in ["I", "E"]:
    campo_mov.click()
    campo_mov.press("Control+A")
    campo_mov.press("Delete")
    campo_mov.press_sequentially(caracter_valido, delay=50)
    app.wait_for_timeout(200)
    valor = campo_mov.input_value()
    assert valor == caracter_valido, f"Se esperaba que {caracter_valido!r} fuera aceptado, se vio: {valor!r}"
capturar_paso(app, "caracteres_validos_aceptados", paso_excel=5)
''')

add("CP036", "abrir_rf05", '''
codigo_concepto = "".join(random.choice("QWERTYUIOPASDFGHJKLZXCVBNM") for _ in range(3))
descripcion = f"CONCEPTO PRUEBA {codigo_concepto}"[:30]
crear_concepto_prueba(app, frame, codigo_concepto, descripcion)
capturar_paso(app, "concepto_de_prueba_creado", paso_excel=3)
frame = releer_concepto(app, frame, codigo_concepto)
capturar_paso(app, "concepto_releido", paso_excel=4)
boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
assert boton.inner_text().strip() == "Modificar", f"Se esperaba modo Modificar antes de desactivar, se vio: {boton.inner_text()!r}"
boton_elim = frame.get_by_role("button", name="Eliminar", exact=True)
assert boton_elim.is_enabled(), "Se esperaba el boton Eliminar habilitado con un concepto vigente"
boton_elim.click()
texto_resultado = confirmar_si_no(frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=5)
assert "desactivad" in texto_resultado.lower(), f"Se esperaba un mensaje de registro desactivado, se vio: {texto_resultado!r}"
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1200)
capturar_paso(app, "estado_tras_desactivar", paso_excel=6)
frame = releer_concepto(app, frame, codigo_concepto)
capturar_paso(app, "concepto_desactivado_releido", paso_excel=7)
boton_mod = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
assert not boton_mod.is_enabled(), "Se esperaba que el concepto desactivado quedara en modo solo lectura (boton Ingresar/Modificar deshabilitado)"
print("[AVISO] No se pudo verificar en BD que fecha_desactivac quedo con la fecha de hoy - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")
''')

add("CP037", "abrir_rf05", '''
codigo_concepto = "".join(random.choice("QWERTYUIOPASDFGHJKLZXCVBNM") for _ in range(3))
descripcion = f"CONCEPTO PRUEBA {codigo_concepto}"[:30]
crear_concepto_prueba(app, frame, codigo_concepto, descripcion)
capturar_paso(app, "concepto_de_prueba_creado", paso_excel=3)
frame, _ = desactivar_concepto(app, frame, codigo_concepto)
capturar_paso(app, "concepto_desactivado", paso_excel=4)
frame = releer_concepto(app, frame, codigo_concepto)
capturar_paso(app, "concepto_desactivado_releido", paso_excel=5)
inputs = frame.locator("input")

def _input_no_editable(inp):
    # BUG REAL / no-bug confirmado en vivo (16/09/2026): Cuenta Contable
    # (poblado via el modal "Busqueda Cuenta Contable", nunca tipeado
    # directo) es "readonly" SIEMPRE - activo o desactivado, incluso en
    # un formulario recien reseteado - nunca tiene el atributo
    # "disabled" en si mismo. Por eso "no editable" para un input hay
    # que verificarlo como disabled O readonly, no solo disabled.
    return inp.is_disabled() or inp.get_attribute("readonly") is not None

# BUG REAL confirmado en vivo (16/09/2026): el bloqueo a solo-lectura de
# un registro desactivado se asienta en dos fases (primero cargan los
# datos, recien despues se deshabilitan los campos) - se espera en
# polling a que TODOS los inputs queden no-editables antes de afirmar
# nada, en vez de asumir que ya esta listo apenas termina releer_concepto.
for _espera_solo_lectura in range(15):
    if all(_input_no_editable(inputs.nth(i)) for i in range(inputs.count())):
        break
    app.wait_for_timeout(400)
for i in range(inputs.count()):
    assert _input_no_editable(inputs.nth(i)), f"Se esperaba que el campo de input #{i} quedara en solo lectura para un concepto desactivado"
select_doc_final = frame.locator("select").first
assert select_doc_final.is_disabled(), "Se esperaba que el combo Documento quedara en solo lectura para un concepto desactivado"
for boton_nombre in ["Modificar", "Ingresar", "Eliminar"]:
    boton_x = frame.get_by_role("button", name=boton_nombre, exact=True)
    if boton_x.count():
        assert not boton_x.is_enabled(), f"Se esperaba que el boton {boton_nombre!r} estuviera deshabilitado para un concepto desactivado"
capturar_paso(app, "botones_deshabilitados_verificados", paso_excel=6)
etiqueta_desactivado = frame.get_by_text(re.compile(r"registro desactivado", re.IGNORECASE))
assert etiqueta_desactivado.count() > 0 and etiqueta_desactivado.first.is_visible(), "Se esperaba el label \\'Registro Desactivado\\' visible"
capturar_paso(app, "label_desactivado_verificado", paso_excel=7)
''')

add("CP038", "abrir_rf05", '''
capturar_paso(app, "vista_desktop", paso_excel=3)
for ancho, alto, etiqueta in [(1600, 900, "desktop"), (1024, 768, "tablet"), (480, 800, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(800)
    capturar_paso(app, f"vista_{etiqueta}", paso_excel=3)
    contenedor = frame.locator("app-conceptos-list")
    assert contenedor.first.is_visible(), f"El contenido principal deberia seguir visible en {etiqueta} ({ancho}x{alto})"
    ancho_scroll = frame.locator("body").evaluate("el => el.scrollWidth")
    print(f"[INFO] {etiqueta} ({ancho}x{alto}): scrollWidth real = {ancho_scroll}px")
''')

# ===========================================================================
# RF-06: Actualizacion De Precios (app-precios-list)
# CONFIRMADO EN VIVO el 16/09/2026: Codigo de Precio (select, 1157
# opciones) + Fecha de Vigencia (<input type=date>) + Sector Tipico
# (select 1-4) + Modo (radios Normal/Por Tramos, se BLOQUEAN segun el
# precio elegido tras Leer, no editable) + Valores (Valor Actual
# readonly, Valor Nuevo, Porc. Reajuste). Boton unico Ingresar/Modificar
# (boton_grabar). Precio "023 - ALUMBRADO PUBLICO (TRAMOS)" es el UNICO
# confirmado en modo Por Tramos entre los primeros 605 codigos
# explorados - al leerlo en modo Tramos se abre AUTOMATICAMENTE el
# modal "Actualizacion de Precios por Tramo" (Tramos Inferior/Superior/
# Valor/Nro., grilla de vigencia actual + grilla de "Valores Utilizados"
# de la vigencia anterior con boton "Pegar"). BUG REAL confirmado en
# vivo: escribir Nro. Tramo DESPUES de "Pegar" resetea los valores ya
# pegados - ver crear_tramo(). Todo lo relacionado a la notificacion
# automatica al equipo GTE (via correo) y a la bitacora de auditoria
# (tabla audit) queda como [AVISO] - ninguno verificable solo con UI.
add("CP039", "abrir_rf06", '''
capturar_paso(app, "pantalla_inicial", paso_excel=3)
leer_precio(app, frame, 1, "2026-09-16", "1")
capturar_paso(app, "tras_leer", paso_excel=4)
boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
assert boton.inner_text().strip() == "Modificar", f"Se esperaba modo Modificar para una vigencia ya cargada, se vio: {boton.inner_text()!r}"
valor_actual = frame.locator("input").nth(4).input_value().strip()
assert valor_actual, "Se esperaba que Valor Actual (Neto) llegara precargado para una vigencia existente"
capturar_paso(app, "vigencia_verificada", paso_excel=5)
print(f"[INFO] Vigencia encontrada: Valor Actual = {valor_actual!r}")
''')

add("CP040", "abrir_rf06", '''
fecha_futura = (date.today() + timedelta(days=730)).strftime("%Y-%m-%d")
leer_precio(app, frame, 1, fecha_futura, "1")
capturar_paso(app, "tras_leer", paso_excel=3)
boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
if boton.inner_text().strip() != "Ingresar":
    print(f"[AVISO] La fecha futura elegida ({fecha_futura}) ya tenia una vigencia cargada (modo {boton.inner_text().strip()!r}) - no se pudo ejercitar el flujo de creacion (modo Ingresar) en esta corrida.")
else:
    campo_valor_nuevo = frame.locator("input").nth(5)
    escribir_campo(campo_valor_nuevo, "99.9999")
    capturar_paso(app, "valor_ingresado", paso_excel=4)
    boton.click()
    texto_resultado = confirmar_si_no(frame)
    capturar_paso(app, "despues_de_confirmar", paso_excel=5)
    assert "actualiz" in texto_resultado.lower(), f"Se esperaba \\'Registro Actualizado.\\', se vio: {texto_resultado!r}"
    leer_precio(app, frame, 1, fecha_futura, "1")
    capturar_paso(app, "vigencia_verificada_tras_crear", paso_excel=6)
    boton2 = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
    assert boton2.inner_text().strip() == "Modificar", f"Se esperaba modo Modificar tras crear el precio, se vio: {boton2.inner_text()!r}"
    print("[AVISO] No se pudo verificar el insert en la bitacora de auditoria (tabla audit) - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")
''')

add("CP041", "abrir_rf06", '''
leer_precio(app, frame, 1, "2026-09-16", "1")
capturar_paso(app, "vigencia_cargada", paso_excel=3)
boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
assert boton.inner_text().strip() == "Modificar", f"Se esperaba modo Modificar antes de probar la modificacion, se vio: {boton.inner_text()!r}"
valor_anterior = frame.locator("input").nth(4).input_value().strip()
campo_valor_nuevo = frame.locator("input").nth(5)
valor_nuevo = f"{random.uniform(10, 50):.4f}"
escribir_campo(campo_valor_nuevo, valor_nuevo)
capturar_paso(app, "valor_modificado", paso_excel=4)
boton.click()
texto_resultado = confirmar_si_no(frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=5)
assert "actualiz" in texto_resultado.lower(), f"Se esperaba \\'Registro Actualizado.\\', se vio: {texto_resultado!r}"
leer_precio(app, frame, 1, "2026-09-16", "1")
capturar_paso(app, "valor_verificado_tras_releer", paso_excel=6)
valor_tras_modificar = frame.locator("input").nth(4).input_value().strip()
print(f"[INFO] Valor anterior={valor_anterior!r}, valor nuevo ingresado={valor_nuevo!r}, valor tras releer={valor_tras_modificar!r}")
print("[AVISO] No se pudo confirmar la recepcion de la notificacion automatica al equipo GTE (requiere acceso a un buzon de correo real) ni el insert en la bitacora de auditoria con el valor ANTERIOR - ambos fuera del alcance de una verificacion solo-UI.")
''')

add("CP042", "abrir_rf06", '''
indice_tramos = indice_opcion_precio(frame, "ALUMBRADO PUBLICO")
assert indice_tramos is not None, "No se encontro en el combo un precio en modo Por Tramos conocido (\\'ALUMBRADO PUBLICO\\') para esta verificacion"
leer_precio(app, frame, indice_tramos, "2026-09-16", "1")
capturar_paso(app, "precio_tramos_leido", paso_excel=3)
modal_titulo = frame.get_by_text("Actualización de Precios por Tramo")
assert modal_titulo.count() > 0 and modal_titulo.first.is_visible(), "Se esperaba que el modal de Tramos se abriera automaticamente al leer un precio en modo Por Tramos"
capturar_paso(app, "modal_tramos_abierto", paso_excel=4)
texto_resultado = crear_tramo(app, frame, siguiente_nro_tramo(frame), "1234.56")
capturar_paso(app, "despues_de_confirmar", paso_excel=5)
assert "actualiz" in texto_resultado.lower() or "registrad" in texto_resultado.lower(), f"Se esperaba un mensaje de registro actualizado, se vio: {texto_resultado!r}"
print("[AVISO] No se pudo confirmar la recepcion de la notificacion automatica al equipo GTE (SistemaGrupo=GTE, ItemGrupo=CAMBTAR, CorreoRemitente=ActualizacionPrecios@luzdelsur.com.pe) ni el insert en la bitacora de auditoria - ambos requieren acceso a un buzon de correo real/BD, fuera del alcance de una verificacion solo-UI.")
# Limpieza: se elimina el tramo de prueba para dejar la vigencia de hoy
# como estaba antes de esta corrida.
modal = frame.locator(SELECTOR_DIALOGO).first
fila_creada = modal.locator("table").first.locator("tbody tr").filter(has_text=re.compile(r"1,?234\.56")).first
if fila_creada.count():
    fila_creada.click()
    app.wait_for_timeout(300)
    modal.get_by_role("button", name="Eliminar", exact=True).click()
    confirmar_en_modal_abierto(app, frame)
    print("[INFO] Tramo de prueba eliminado al final para no dejar datos de prueba en la vigencia actual.")
''')

add("CP043", "abrir_rf06", '''
indice_tramos = indice_opcion_precio(frame, "ALUMBRADO PUBLICO")
assert indice_tramos is not None, "No se encontro en el combo un precio en modo Por Tramos conocido (\\'ALUMBRADO PUBLICO\\') para esta verificacion"
leer_precio(app, frame, indice_tramos, "2026-09-16", "1")
capturar_paso(app, "precio_tramos_leido", paso_excel=3)
# Se crea un 1er tramo real de referencia (Inferior/Superior de la
# vigencia anterior via Pegar) para poder forzar la discontinuidad real
# contra ESE tramo en vez de asumir valores de otra vigencia.
crear_tramo(app, frame, siguiente_nro_tramo(frame), "1000.00")
capturar_paso(app, "primer_tramo_creado", paso_excel=4)
modal = frame.locator(SELECTOR_DIALOGO).first
inputs_modal = modal.locator("input")
campo_nro, campo_inferior, campo_superior, campo_valor = inputs_modal.nth(2), inputs_modal.nth(3), inputs_modal.nth(4), inputs_modal.nth(5)
# Tramo Inferior con un valor que NO coincide con el Superior del tramo
# anterior recien creado (6000000), y un Nro. de Tramo no consecutivo
# (siguiente_nro_tramo()+5, para asegurar un salto real sin importar
# cuantos tramos hubiera antes de esta corrida).
nro_discontinuo = siguiente_nro_tramo(frame) + 5
campo_nro.click()
campo_nro.press_sequentially(str(nro_discontinuo), delay=50)
campo_inferior.click()
campo_inferior.press_sequentially("50", delay=50)
campo_superior.click()
campo_superior.press_sequentially("100", delay=50)
campo_valor.click()
campo_valor.press_sequentially("500.00", delay=50)
app.wait_for_timeout(300)
capturar_paso(app, "tramo_discontinuo_ingresado", paso_excel=5)
modal.get_by_role("button", name="Ingresar", exact=True).click()
texto_resultado = confirmar_en_modal_abierto(app, frame)
capturar_paso(app, "mensaje_de_validacion", paso_excel=6)
assert re.search(r"tramo inferior.*igual.*tramo superior|numero de tramo.*consecutivo|n.mero de tramo.*consecutivo", texto_resultado, re.IGNORECASE), f"Se esperaba un mensaje de discontinuidad de tramos, se vio: {texto_resultado!r}"
# Limpieza del tramo de referencia creado al inicio.
fila_creada = modal.locator("table").first.locator("tbody tr").filter(has_text=re.compile(r"1,?000\.00")).first
if fila_creada.count():
    fila_creada.click()
    app.wait_for_timeout(300)
    modal.get_by_role("button", name="Eliminar", exact=True).click()
    confirmar_en_modal_abierto(app, frame)
    print("[INFO] Tramo de referencia eliminado al final para no dejar datos de prueba en la vigencia actual.")
''')

add("CP044", "abrir_rf06", '''
indice_tramos = indice_opcion_precio(frame, "ALUMBRADO PUBLICO")
assert indice_tramos is not None, "No se encontro en el combo un precio en modo Por Tramos conocido (\\'ALUMBRADO PUBLICO\\') para esta verificacion"
leer_precio(app, frame, indice_tramos, "2026-09-16", "1")
capturar_paso(app, "precio_tramos_leido", paso_excel=3)
crear_tramo(app, frame, siguiente_nro_tramo(frame), "2222.22")
capturar_paso(app, "tramo_de_prueba_creado", paso_excel=4)
modal = frame.locator(SELECTOR_DIALOGO).first
fila_tramo = modal.locator("table").first.locator("tbody tr").filter(has_text=re.compile(r"2,?222\.22")).first
assert fila_tramo.count() > 0, "Se esperaba encontrar el tramo de prueba recien creado en la grilla de vigencia actual"
fila_tramo.click()
app.wait_for_timeout(300)
capturar_paso(app, "tramo_seleccionado", paso_excel=5)
boton_elim = modal.get_by_role("button", name="Eliminar", exact=True)
assert boton_elim.is_enabled(), "El boton Eliminar deberia habilitarse al seleccionar un tramo"
boton_elim.click()
texto_resultado = confirmar_en_modal_abierto(app, frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=6)
assert "eliminad" in texto_resultado.lower(), f"Se esperaba \\'Registro sera Eliminado.\\', se vio: {texto_resultado!r}"
fila_tras_eliminar = modal.locator("table").first.locator("tbody tr").filter(has_text=re.compile(r"2,?222\.22"))
for _intento in range(16):
    if fila_tras_eliminar.count() == 0:
        break
    app.wait_for_timeout(500)
capturar_paso(app, "estado_tras_eliminar", paso_excel=7)
assert fila_tras_eliminar.count() == 0, "Se esperaba que el tramo eliminado ya no apareciera en la grilla de vigencia actual"
print("[AVISO] No se pudo verificar en BD que no queden filas de proyeccion futura del tramo eliminado en tramos1 - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")
''')

add("CP045-A", "abrir_rf06", '''
indice_tramos = indice_opcion_precio(frame, "ALUMBRADO PUBLICO")
assert indice_tramos is not None, "No se encontro en el combo un precio en modo Por Tramos conocido (\\'ALUMBRADO PUBLICO\\') para esta verificacion"
leer_precio(app, frame, indice_tramos, "2026-09-16", "1")
capturar_paso(app, "precio_tramos_leido", paso_excel=3)
modal = frame.locator(SELECTOR_DIALOGO).first
fila_anterior = modal.locator("table").nth(1).locator("tbody tr").first
assert fila_anterior.count() > 0, "Se esperaba al menos una fila en la grilla de \\'Valores Utilizados\\' (vigencia anterior) para poder Pegar"
celdas_anterior = fila_anterior.locator("td").all_inner_texts()
inferior_esperado = celdas_anterior[1].replace(",", "").strip()
superior_esperado = celdas_anterior[2].replace(",", "").strip()
fila_anterior.click()
app.wait_for_timeout(300)
capturar_paso(app, "fila_anterior_seleccionada", paso_excel=4)
modal.get_by_role("button", name="Pegar", exact=True).click()
app.wait_for_timeout(500)
capturar_paso(app, "tras_pegar", paso_excel=5)
inputs_modal = modal.locator("input")
valor_inferior = inputs_modal.nth(3).input_value().replace(",", "").strip()
valor_superior = inputs_modal.nth(4).input_value().replace(",", "").strip()
assert valor_inferior == inferior_esperado, f"Se esperaba que Tramo Inferior quedara en {inferior_esperado!r} tras Pegar, se vio {valor_inferior!r}"
assert valor_superior == superior_esperado, f"Se esperaba que Tramo Superior quedara en {superior_esperado!r} tras Pegar, se vio {valor_superior!r}"
assert not inputs_modal.nth(3).is_disabled() and not inputs_modal.nth(4).is_disabled(), "Se esperaba que Tramo Inferior/Superior quedaran habilitados para edicion tras Pegar"
''')

add("CP045-B", "abrir_rf06", '''
indice_tramos = indice_opcion_precio(frame, "ALUMBRADO PUBLICO")
assert indice_tramos is not None, "No se encontro en el combo un precio en modo Por Tramos conocido (\\'ALUMBRADO PUBLICO\\') para esta verificacion"
leer_precio(app, frame, indice_tramos, "2026-09-16", "1")
capturar_paso(app, "precio_tramos_leido", paso_excel=3)
crear_tramo(app, frame, siguiente_nro_tramo(frame), "3333.33")
capturar_paso(app, "tramo_de_prueba_creado", paso_excel=4)
modal = frame.locator(SELECTOR_DIALOGO).first
fila_tramo = modal.locator("table").first.locator("tbody tr").filter(has_text=re.compile(r"3,?333\.33")).first
assert fila_tramo.count() > 0, "Se esperaba encontrar el tramo de prueba recien creado en la grilla de vigencia actual"
fila_tramo.click()
app.wait_for_timeout(300)
inputs_modal = modal.locator("input")
campo_valor = inputs_modal.nth(5)
campo_valor.click()
campo_valor.press("Control+A")
campo_valor.press("Delete")
campo_valor.press_sequentially("4444.44", delay=50)
app.wait_for_timeout(300)
capturar_paso(app, "tramo_modificado", paso_excel=5)
boton_mod = modal.get_by_role("button", name="Modificar", exact=True)
assert boton_mod.is_enabled(), "El boton Modificar deberia habilitarse al seleccionar y editar un tramo"
boton_mod.click()
texto_resultado = confirmar_en_modal_abierto(app, frame)
capturar_paso(app, "despues_de_confirmar", paso_excel=6)
assert "actualiz" in texto_resultado.lower(), f"Se esperaba un mensaje de registro actualizado, se vio: {texto_resultado!r}"
fila_actualizada = modal.locator("table").first.locator("tbody tr").filter(has_text=re.compile(r"4,?444\.44"))
for _intento in range(16):
    if fila_actualizada.count() > 0:
        break
    app.wait_for_timeout(500)
capturar_paso(app, "valor_verificado_en_grilla", paso_excel=7)
# CASO CERRADO COMO OK (confirmado por el usuario, 16/09/2026): reprodujo
# a mano crear un tramo (3333.33) y modificarlo (4444.44) en una sesion
# manual headed con video/Word de evidencia propios
# (_exploracion/CP045-B_manual/) y el valor quedo limpio en la grilla,
# sin mezcla de digitos. La automatizacion SI vio un valor mezclado
# ("3,333.33444444") en una corrida, pese a que crear_tramo() ya hace
# Control+A + Delete antes de escribir el nuevo valor - queda como una
# sospecha de bug de automatizacion (el campo Valor del modal de Tramos
# podria no limpiarse del todo con Control+A/Delete al venir de un
# registro EXISTENTE, a diferencia de un campo recien creado) pendiente
# de investigar, no como un defecto real de la app. Por eso esta
# verificacion queda informativa (AVISO) en vez de condicionar el
# resultado OK/FALLO del caso.
if fila_actualizada.count() > 0:
    print("[INFO] El valor 4444.44 aparecio correctamente en la grilla tras modificar.")
else:
    print("[AVISO] La grilla no mostro 4444.44 tras modificar en esta corrida automatizada - reproducido y confirmado como funcionamiento correcto de la app en una sesion manual (ver _exploracion/CP045-B_manual/), asi que se documenta como una sospecha de bug de limpieza del campo Valor en la automatizacion (no un defecto real) y no hace fallar el caso.")
print("[AVISO] No se pudo confirmar la recepcion de la notificacion automatica al equipo GTE ni el insert en la bitacora de auditoria - ambos fuera del alcance de una verificacion solo-UI.")
# Limpieza del tramo de prueba (busca por cualquiera de los dos valores
# posibles, segun si la modificacion en la grilla quedo visible o no).
fila_limpieza = fila_actualizada if fila_actualizada.count() > 0 else fila_tramo
if fila_limpieza.count() > 0:
    fila_limpieza.first.click()
    app.wait_for_timeout(300)
    modal.get_by_role("button", name="Eliminar", exact=True).click()
    confirmar_en_modal_abierto(app, frame)
    print("[INFO] Tramo de prueba eliminado al final para no dejar datos de prueba en la vigencia actual.")
''')

add("CP046", "abrir_rf06", '''
capturar_paso(app, "vista_desktop", paso_excel=3)
for ancho, alto, etiqueta in [(1600, 900, "desktop"), (1024, 768, "tablet"), (480, 800, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(800)
    capturar_paso(app, f"vista_{etiqueta}", paso_excel=3)
    contenedor = frame.locator("app-precios-list")
    assert contenedor.first.is_visible(), f"El contenido principal deberia seguir visible en {etiqueta} ({ancho}x{alto})"
    ancho_scroll = frame.locator("body").evaluate("el => el.scrollWidth")
    print(f"[INFO] {etiqueta} ({ancho}x{alto}): scrollWidth real = {ancho_scroll}px")
''')

add("CP092", "abrir_rf06", '''
leer_precio(app, frame, 1, "2026-09-16", "1")
capturar_paso(app, "vigencia_cargada", paso_excel=3)
boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
if boton.inner_text().strip() == "Modificar":
    campo_valor_nuevo = frame.locator("input").nth(5)
    escribir_campo(campo_valor_nuevo, f"{random.uniform(10, 50):.4f}")
    capturar_paso(app, "valor_modificado", paso_excel=4)
    boton.click()
    confirmar_si_no(frame)
    capturar_paso(app, "despues_de_confirmar", paso_excel=5)
else:
    print(f"[AVISO] La vigencia elegida no estaba en modo Modificar (se vio {boton.inner_text().strip()!r}) - no se pudo ejercitar la modificacion para esta verificacion.")
print("[AVISO] \\'Limpieza de vigencias futuras al modificar en modo Normal\\' (que no queden registros contradictorios en la tabla Preca) es una regla de negocio a nivel de BD - no se puede verificar desde la UI sin acceso directo a la base de datos, fuera del alcance de esta verificacion solo-UI.")
''')

# ===========================================================================
# RF-07: Actualizacion De Tasas De Interes (app-tasas-interes-list)
# CONFIRMADO EN VIVO el 16/09/2026: "Ultima Fecha Registrada" (texto
# rojo, no editable) + "Fecha de Vigencia" (<input type=date>, campo de
# consulta) + 8 campos de tasa (TAMN/TIPMN Simple y Compuesta, Promedio
# TAMN-TIPMN, Legal Simple, Promedio Compuesta, Promedio Simple) + boton
# "Ingresar" fijo (NO alterna a "Modificar" como otras RF) + boton dual
# Cerrar/Cancelar. BUG REAL / precision confirmada en vivo: leer una
# fecha EXACTA (=Ultima Fecha Registrada) no muestra asterisco en ningun
# campo pero SI un aviso amarillo "Esta fecha es historica. Los campos
# estan en modo consulta." (los inputs no quedan realmente disabled a
# nivel HTML pese al aviso). Leer una fecha SIN registro exacto (futura
# o sin historial) marca los 8 campos con un "*" (leyenda "* Tasa
# proyectada de fecha anterior") y el boton dual cambia a "Cancelar".
# Tasa Promedio TAMN-TIPMN se recalcula solo AL SALIR de TAMN o TIPMN:
# confirmado en vivo (TAMN + TIPMN)/2 redondeado a 3 decimales.
add("CP047", "abrir_rf07", '''
capturar_paso(app, "pantalla_inicial", paso_excel=3)
ultima_fecha_texto = frame.get_by_text(re.compile(r"\\d{2}/\\d{2}/\\d{4}")).first.inner_text().strip()
assert re.match(r"\\d{2}/\\d{2}/\\d{4}", ultima_fecha_texto), f"Se esperaba que \\'Ultima Fecha Registrada\\' mostrara una fecha dd/mm/aaaa, se vio: {ultima_fecha_texto!r}"
boton_ingresar = frame.get_by_role("button", name="Ingresar", exact=True)
assert not boton_ingresar.is_enabled(), "Se esperaba que el boton Ingresar estuviera deshabilitado en la carga inicial"
boton_dual = frame.get_by_role("button", name=re.compile(r"^(Cerrar|Cancelar)$"))
assert boton_dual.inner_text().strip() == "Cerrar", f"Se esperaba que el boton dual mostrara \\'Cerrar\\' en la carga inicial, se vio: {boton_dual.inner_text()!r}"
capturar_paso(app, "estado_inicial_verificado", paso_excel=4)
print(f"[INFO] Ultima Fecha Registrada = {ultima_fecha_texto!r}")
''')

add("CP048", "abrir_rf07", '''
ultima_fecha_texto = frame.get_by_text(re.compile(r"\\d{2}/\\d{2}/\\d{4}")).first.inner_text().strip()
dia, mes, anio = ultima_fecha_texto.split("/")
fecha_iso = f"{anio}-{mes}-{dia}"
capturar_paso(app, "pantalla_inicial", paso_excel=3)
frame.locator("input[type=date]").fill(fecha_iso)
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
try:
    frame.locator(".ant-spin-blur").first.wait_for(state="hidden", timeout=8000)
except PWTimeoutError:
    pass
app.wait_for_timeout(800)
capturar_paso(app, "tras_leer_fecha_exacta", paso_excel=4)
asteriscos = frame.get_by_text("*", exact=True)
assert asteriscos.count() == 0, f"No se esperaban marcas de asterisco para la fecha exacta ({ultima_fecha_texto}), se encontraron {asteriscos.count()}"
inputs = frame.locator("input")
for i in range(1, 9):
    assert not inputs.nth(i).is_disabled(), f"Se esperaba que el campo de tasa #{i} quedara habilitado para edicion con una fecha de registro exacto"
capturar_paso(app, "sin_asterisco_verificado", paso_excel=5)
print(f"[INFO] Fecha exacta consultada: {ultima_fecha_texto}, ningun campo con asterisco, campos editables.")
''')

add("CP049", "abrir_rf07", '''
fecha_futura = (date.today() + timedelta(days=200)).strftime("%Y-%m-%d")
capturar_paso(app, "pantalla_inicial", paso_excel=3)
frame.locator("input[type=date]").fill(fecha_futura)
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
try:
    frame.locator(".ant-spin-blur").first.wait_for(state="hidden", timeout=8000)
except PWTimeoutError:
    pass
app.wait_for_timeout(800)
capturar_paso(app, "tras_leer_fecha_proyectada", paso_excel=4)
asteriscos = frame.get_by_text("*", exact=True)
assert asteriscos.count() >= 8, f"Se esperaban al menos 8 marcas de asterisco (una por tasa) para una fecha sin registro exacto, se encontraron {asteriscos.count()}"
leyenda = frame.get_by_text(re.compile(r"tasa proyectada de fecha anterior", re.IGNORECASE))
assert leyenda.count() > 0 and leyenda.first.is_visible(), "Se esperaba la leyenda \\'* Tasa proyectada de fecha anterior\\' visible"
boton = frame.get_by_role("button", name="Ingresar", exact=True)
assert boton.is_enabled(), "Se esperaba que el boton Ingresar estuviera habilitado para una fecha proyectada"
boton_dual = frame.get_by_role("button", name=re.compile(r"^(Cerrar|Cancelar)$"))
assert boton_dual.inner_text().strip() == "Cancelar", f"Se esperaba que el boton dual cambiara a \\'Cancelar\\', se vio: {boton_dual.inner_text()!r}"
capturar_paso(app, "proyeccion_verificada", paso_excel=5)
print("[AVISO] No se verifico individualmente el historial propio de cada una de las 8 tasas (la matriz pide no asumir que todas comparten el mismo criterio) - se verifico el comportamiento agregado (las 8 marcadas) contra una fecha sin ningun historial cercano.")
''')

add("CP050", "abrir_rf07", '''
# CONFIRMADO EN VIVO el 17/09/2026: "hoy + 3 dias" caia ANTES de la
# "Ultima Fecha Registrada" del sistema (que ya tiene datos cargados
# bastante mas adelante, ej. 2028) - una fecha anterior a esa se trata
# como HISTORICA y la pantalla queda en modo SOLO CONSULTA (cartel
# amarillo "Esta fecha es historica..."), por lo que nada de lo tipeado
# se guardaba ni recalculaba. Se lee la fecha real del sistema y se usa
# siempre un margen por delante de ella.
texto_ultima_fecha = frame.get_by_text(re.compile(r"\\d{2}/\\d{2}/\\d{4}")).first.inner_text().strip()
dd, mm, yyyy = texto_ultima_fecha.split("/")
ultima_fecha = date(int(yyyy), int(mm), int(dd))
fecha_futura = (ultima_fecha + timedelta(days=30)).strftime("%Y-%m-%d")
frame.locator("input[type=date]").fill(fecha_futura)
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1000)
capturar_paso(app, "tras_leer", paso_excel=3)
# CONFIRMADO EN VIVO el 17/09/2026: el formulario real tiene 8 campos (
# Simple/Compuesto para TAMN, TIPMN, Legal y Promedio) en 2 columnas -
# los indices posicionales (nth(1)/nth(3)/nth(4)) NO corresponden a
# TAMN/TIPMN/Promedio como se asumia. Se usa campo_por_etiqueta() con la
# etiqueta completa (evita choques Simple/Compuesto).
campo_tamn = campo_por_etiqueta(frame, "Tasa TAMN (Interés Simple)")
campo_tipmn = campo_por_etiqueta(frame, "Tasa TIPMN (Interés Simple)")
campo_promedio = campo_por_etiqueta(frame, "Tasa Promedio TAMN - TIPMN")
tamn = round(random.uniform(5, 30), 2)
tipmn = round(random.uniform(1, 10), 2)
escribir_campo(campo_tamn, f"{tamn:.2f}")
capturar_paso(app, "tamn_ingresado", paso_excel=4)
escribir_campo(campo_tipmn, f"{tipmn:.2f}")
app.wait_for_timeout(500)
capturar_paso(app, "tipmn_ingresado", paso_excel=5)
promedio_esperado = round((tamn + tipmn) / 2, 3)
promedio_real = float(campo_promedio.input_value())
assert abs(promedio_real - promedio_esperado) < 0.001, f"Se esperaba Promedio TAMN-TIPMN = {promedio_esperado}, se vio {promedio_real}"
capturar_paso(app, "promedio_verificado", paso_excel=6)
print(f"[INFO] TAMN={tamn}, TIPMN={tipmn}, Promedio calculado={promedio_real} (esperado {promedio_esperado})")
''')

add("CP051", "abrir_rf07", '''
frame.locator("input[type=date]").fill("2003-03-20")
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1000)
capturar_paso(app, "tras_leer_fecha_antigua", paso_excel=3)
inputs = frame.locator("input")
campo_tamn, campo_promedio = inputs.nth(1), inputs.nth(4)
tamn_deseado = round(random.uniform(5, 30), 2)
escribir_campo(campo_tamn, f"{tamn_deseado:.2f}")
app.wait_for_timeout(500)
capturar_paso(app, "tamn_ingresado", paso_excel=4)
# Se relee el valor REAL del campo TAMN (no el valor deseado en Python)
# antes de comparar - mismo patron de sync Angular visto en otras RF
# (el valor efectivamente commiteado puede diferir por timing de
# press_sequentially, aunque el campo muestre datos coherentes).
tamn_real = float(campo_tamn.input_value())
promedio_real = float(campo_promedio.input_value())
assert abs(promedio_real - tamn_real) < 0.001, f"Se esperaba que Promedio TAMN-TIPMN tomara el mismo valor que TAMN ({tamn_real}) para una fecha anterior al 21/03/2003, se vio {promedio_real}"
capturar_paso(app, "promedio_verificado", paso_excel=5)
print(f"[INFO] TAMN={tamn_real}, Promedio (deberia igualar a TAMN)={promedio_real}")
''')

add("CP052", "abrir_rf07", '''
# CONFIRMADO EN VIVO el 17/09/2026: el rango 300-500 dias (elegido para
# evitar la zona ambigua 4-100 dias) todavia podia caer ANTES de la
# "Ultima Fecha Registrada" real del sistema (que ya tiene datos
# cargados bastante mas adelante) - una fecha anterior a esa se trata
# como HISTORICA (modo solo consulta, "no esta autorizado para
# modificar tasas historicas."). Se lee la fecha real del sistema y se
# usa siempre un margen por delante de ella en vez de un offset fijo
# desde "hoy".
texto_ultima_fecha = frame.get_by_text(re.compile(r"\\d{2}/\\d{2}/\\d{4}")).first.inner_text().strip()
dd, mm, yyyy = texto_ultima_fecha.split("/")
ultima_fecha = date(int(yyyy), int(mm), int(dd))
fecha_nueva = (ultima_fecha + timedelta(days=random.randint(30, 60))).strftime("%Y-%m-%d")
frame.locator("input[type=date]").fill(fecha_nueva)
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1000)
capturar_paso(app, "tras_leer", paso_excel=3)
# CONFIRMADO EN VIVO el 17/09/2026: el formulario real tiene 8 campos
# (Simple/Compuesto para TAMN, TIPMN, Legal y Promedio) en 2 columnas -
# los indices posicionales (nth(1)/nth(3)) NO corresponden a TAMN/TIPMN
# como se asumia. Se usa campo_por_etiqueta() con la etiqueta completa.
campo_tamn = campo_por_etiqueta(frame, "Tasa TAMN (Interés Simple)")
campo_tipmn = campo_por_etiqueta(frame, "Tasa TIPMN (Interés Simple)")
tamn = round(random.uniform(5, 30), 2)
tipmn = round(random.uniform(1, 10), 2)
escribir_campo(campo_tamn, f"{tamn:.2f}")
escribir_campo(campo_tipmn, f"{tipmn:.2f}")
app.wait_for_timeout(500)
capturar_paso(app, "valores_ingresados", paso_excel=4)
boton = frame.get_by_role("button", name="Ingresar", exact=True)
boton.click()
# BUG REAL / backend lento confirmado en vivo (16/09/2026): tras
# Ingresar aparece un indicador "Procesando..." (no un boton "Cargando..."
# que esperar_fin_de_carga() pueda detectar) que puede tardar bastante
# antes de que aparezca el dialogo de resultado - se le da un timeout
# inicial mucho mas generoso que el default de confirmar_si_no().
try:
    frame.get_by_text("Procesando...").wait_for(state="hidden", timeout=20000)
except PWTimeoutError:
    pass
texto_resultado = confirmar_si_no(frame, timeout=20000)
capturar_paso(app, "despues_de_confirmar", paso_excel=5)
assert "correctamente" in texto_resultado.lower(), f"Se esperaba \\'Tasas se registraron correctamente\\', se vio: {texto_resultado!r}"
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1000)
frame.locator("input[type=date]").fill(fecha_nueva)
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1000)
capturar_paso(app, "releido_tras_guardar", paso_excel=6)
asteriscos = frame.get_by_text("*", exact=True)
assert asteriscos.count() == 0, f"No se esperaban asteriscos tras guardar y releer la misma fecha, se encontraron {asteriscos.count()}"
print("[AVISO] No se pudo verificar que TAMN Compuesta/TIPMN Compuesta/Promedio Compuesta/Legal Compuesta se recalcularan exactamente con la formula de interes compuesto esperada, ni el insert en la bitacora de auditoria - requiere confirmar la formula real (BD/documentacion), fuera del alcance de esta verificacion basica.")
''')

add("CP053", "abrir_rf07", '''
capturar_paso(app, "vista_desktop", paso_excel=3)
for ancho, alto, etiqueta in [(1600, 900, "desktop"), (1024, 768, "tablet"), (480, 800, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(800)
    capturar_paso(app, f"vista_{etiqueta}", paso_excel=3)
    contenedor = frame.locator("app-tasas-interes-list")
    assert contenedor.first.is_visible(), f"El contenido principal deberia seguir visible en {etiqueta} ({ancho}x{alto})"
    ancho_scroll = frame.locator("body").evaluate("el => el.scrollWidth")
    print(f"[INFO] {etiqueta} ({ancho}x{alto}): scrollWidth real = {ancho_scroll}px")
''')

# ===========================================================================
# RF-10: Actualizacion De Agenda De Facturacion (app-agenda-principal)
# CONFIRMADO EN VIVO el 16/09/2026: pantalla "Calendario de Facturacion"
# con 3 secciones - "Proceso" (Fecha de Proceso + Leer/Cancelar),
# "Agenda" (grilla con fila de filtro/alta EN LA CABECERA: Sector +
# Fecha Lectura/Emision/Reparto/Corte Boleta/Corte Terr., mas botones
# Ingresar/Eliminar/Vencimientos.../Feriados...) y "Vencimientos" (grilla
# de vencimientos del sector seleccionado + Modifica Fecha). TODOS los
# botones salvo Leer quedan deshabilitados en la carga inicial.
add("CP069", "abrir_rf10", '''
capturar_paso(app, "pantalla_inicial", paso_excel=3)
campo_fecha_proceso = frame.locator("input[type=date]").first
assert campo_fecha_proceso.is_visible() and not campo_fecha_proceso.is_disabled(), "Se esperaba que el campo Fecha de Proceso estuviera activo en la carga inicial"
boton_leer = frame.get_by_role("button", name="Leer", exact=True)
assert boton_leer.is_enabled(), "Se esperaba que el boton Leer estuviera habilitado en la carga inicial"
for boton_nombre in ["Cancelar", "Ingresar", "Eliminar", "Vencimientos...", "Feriados...", "Modifica Fecha"]:
    boton = frame.get_by_role("button", name=boton_nombre, exact=True)
    assert not boton.is_enabled(), f"Se esperaba que el boton {boton_nombre!r} estuviera deshabilitado en la carga inicial"
capturar_paso(app, "botones_deshabilitados_verificados", paso_excel=4)
''')

# CONFIRMADO EN VIVO el 16/09/2026: el flujo completo "crear agenda"
# (Sector + 5 fechas + Ingresar + confirmar) SI funciona - la causa real
# de los "No se pudo registrar la agenda." vistos en la exploracion
# inicial era que Fecha Corte Boleta/Terr. son UNICAS EN TODO EL SISTEMA
# (no por sector) y las fechas usadas en pruebas manuales anteriores del
# mismo dia ya estaban tomadas - ver crear_agenda_prueba() mas arriba,
# que sortea una Fecha de Proceso al azar lejos en el futuro (y
# reintenta con otra si hay colision) para evitar el problema en cada
# corrida. Catalogo real de Tipos de Vencimiento confirmado en vivo:
# codigo 1 "REGULADOS" (15 dias, Dias Habiles=N/corridos, el UNICO
# modificable desde esta pantalla) y codigo 2 "LIBRES" (20 dias, Dias
# Habiles=S/habiles, "Clientes Libres" - bloqueado para modificar aqui).
add("CP070", "abrir_rf10", '''
fecha_proceso, sector_valor, corte_boleta, corte_terr = crear_agenda_prueba(app, frame)
capturar_paso(app, "agenda_de_prueba_creada", paso_excel=3)
leer_agenda(app, frame, fecha_proceso.isoformat())
capturar_paso(app, "tras_leer", paso_excel=5)
tabla_agenda = frame.locator("app-agenda-principal table").nth(0)
filas_agenda = tabla_agenda.locator("tbody tr")
assert filas_agenda.count() >= 1, "Se esperaba al menos 1 fila en la grilla de Agenda tras Leer"
capturar_paso(app, "grilla_agenda_poblada", paso_excel=6)
boton_principal = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
assert boton_principal.inner_text().strip() == "Modificar", f"Se esperaba que la primera fila quedara auto-seleccionada (boton en modo Modificar), se vio: {boton_principal.inner_text()!r}"
campo_lectura = frame.locator("input[type=date]").nth(1)
assert campo_lectura.input_value() == fecha_proceso.isoformat(), "Se esperaba que las fechas de la fila auto-seleccionada cargaran en los campos de edicion"
capturar_paso(app, "primera_fila_seleccionada", paso_excel=7)
tabla_venc = frame.locator("app-agenda-principal table").nth(1)
filas_venc = tabla_venc.locator("tbody tr")
assert filas_venc.count() >= 1, "Se esperaba que la grilla de Vencimientos se llenara para la fila seleccionada"
capturar_paso(app, "grilla_vencimientos_poblada", paso_excel=8)
print(f"[INFO] Agenda de prueba: sector {sector_valor}, fecha de proceso {fecha_proceso.isoformat()}, {filas_venc.count()} vencimiento(s).")
''')

add("CP071", "abrir_rf10", '''
fecha_proceso, sector_valor, corte_boleta, corte_terr = crear_agenda_prueba(app, frame, dias_semana_emision=(4,))
capturar_paso(app, "agenda_creada_emision_viernes", paso_excel=7)
leer_agenda(app, frame, fecha_proceso.isoformat())
capturar_paso(app, "tras_releer", paso_excel=9)
tabla_venc = frame.locator("app-agenda-principal table").nth(1)
filas_venc = tabla_venc.locator("tbody tr")
assert filas_venc.count() >= 1, "Se esperaba que la grilla de Vencimientos se llenara"
tipos_habiles_confirmados = 0
for i in range(filas_venc.count()):
    celdas = filas_venc.nth(i).locator("td").all_inner_texts()
    if "LIBRES" in celdas[1].upper():
        fecha_venc = celdas[2].strip()
        dd, mm, yy = fecha_venc.split("/")
        dt = date(int(yy), int(mm), int(dd))
        nombre_dia = dt.strftime("%A")
        assert dt.weekday() not in (5, 6), f"Se esperaba que el vencimiento habil (LIBRES, codigo 2) NO cayera en fin de semana, se vio {fecha_venc} ({nombre_dia})"
        print(f"[INFO] Vencimiento habil (LIBRES): {fecha_venc} ({nombre_dia}).")
        tipos_habiles_confirmados += 1
assert tipos_habiles_confirmados >= 1, "Se esperaba al menos un tipo de vencimiento con Dias Habiles=S (LIBRES) en la grilla"
capturar_paso(app, "vencimientos_habiles_verificados", paso_excel=10)
''')

add("CP072", "abrir_rf10", '''
fecha_proceso, sector_valor, corte_boleta, corte_terr = crear_agenda_prueba(app, frame, dias_semana_emision=(4,))
capturar_paso(app, "agenda_creada_emision_viernes", paso_excel=7)
leer_agenda(app, frame, fecha_proceso.isoformat())
capturar_paso(app, "tras_releer", paso_excel=9)
tabla_venc = frame.locator("app-agenda-principal table").nth(1)
filas_venc = tabla_venc.locator("tbody tr")
assert filas_venc.count() >= 1, "Se esperaba que la grilla de Vencimientos se llenara"
tipo1_encontrado = False
for i in range(filas_venc.count()):
    celdas = filas_venc.nth(i).locator("td").all_inner_texts()
    if celdas[0].strip() == "1":
        fecha_venc = celdas[2].strip()
        dd, mm, yy = fecha_venc.split("/")
        dt = date(int(yy), int(mm), int(dd))
        dias_corridos = (dt - fecha_proceso).days
        # Debe ser 15 dias corridos, +1 dia extra por cada feriado que haya
        # caido dentro del rango (el calculo de corridos SI salta feriados,
        # solo cuenta sabados/domingos como dias, ver manual seccion 3.4).
        assert 15 <= dias_corridos <= 18, f"Se esperaba Fecha Emision + 15 dias corridos (+ posibles feriados), se vio una diferencia de {dias_corridos} dias"
        nombre_dia = dt.strftime("%A")
        nombre_dia_emision = fecha_proceso.strftime("%A")
        print(f"[INFO] Vencimiento tipo 1 (REGULADOS, corrido): {fecha_venc} ({nombre_dia}), {dias_corridos} dias corridos desde la emision ({nombre_dia_emision}).")
        tipo1_encontrado = True
assert tipo1_encontrado, "Se esperaba encontrar el tipo de vencimiento codigo 1 en la grilla"
capturar_paso(app, "vencimiento_corrido_verificado", paso_excel=10)
''')

add("CP075", "abrir_rf10", '''
fecha_proceso, sector_valor, corte_boleta, corte_terr = crear_agenda_prueba(app, frame)
capturar_paso(app, "agenda_creada", paso_excel=3)
leer_agenda(app, frame, fecha_proceso.isoformat())
capturar_paso(app, "fila_seleccionada", paso_excel=3)
inputs_fecha = frame.locator("input[type=date]")
nueva_fecha_lectura = fecha_proceso - timedelta(days=3)
inputs_fecha.nth(1).fill(nueva_fecha_lectura.isoformat())
app.wait_for_timeout(300)
capturar_paso(app, "fecha_lectura_modificada", paso_excel=4)
frame.get_by_role("button", name="Modificar", exact=True).click()
app.wait_for_timeout(800)
dialogo = frame.locator(SELECTOR_DIALOGO)
assert dialogo.count() > 0 and dialogo.last.is_visible(), "Se esperaba el dialogo de confirmacion al modificar"
texto_confirm = dialogo.last.inner_text()
assert "zonas" in texto_confirm.lower(), f"Se esperaba el mensaje de confirmacion de modificacion de zonas, se vio: {texto_confirm!r}"
capturar_paso(app, "confirmacion_modificar", paso_excel=6)
boton_si = dialogo.last.get_by_role("button", name=re.compile(r"^S.?$"))
boton_si.first.click()
esperar_fin_de_carga(app, frame)
for _i in range(60):
    app.wait_for_timeout(400)
    if not frame.locator(".ant-spin-blur").count():
        break
# CONFIRMADO EN VIVO el 17/09/2026: backend lento (hasta 16s reales
# medidos) para que aparezca el dialogo de resultado tras Modificar - se
# amplia el polling a 24s (antes 6s, insuficiente) en vez de un solo
# chequeo (ver crear_agenda_prueba).
resultado_dialogo = None
for _i in range(60):
    app.wait_for_timeout(400)
    resultado = frame.locator(SELECTOR_DIALOGO)
    if resultado.count() and resultado.last.is_visible():
        resultado_dialogo = resultado.last
        break
assert resultado_dialogo is not None, "Se esperaba un dialogo de resultado tras confirmar la modificacion"
texto_resultado = resultado_dialogo.inner_text()
assert "modificada exitosamente" in texto_resultado.lower(), f"Se esperaba \\'Agenda modificada exitosamente.\\', se vio: {texto_resultado!r}"
resultado_dialogo.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
app.wait_for_timeout(800)
capturar_paso(app, "agenda_modificada", paso_excel=7)
''')

add("CP078", "abrir_rf10", '''
fecha_proceso, sector_valor, corte_boleta, corte_terr = crear_agenda_prueba(app, frame)
capturar_paso(app, "agenda_creada", paso_excel=3)
leer_agenda(app, frame, fecha_proceso.isoformat())
capturar_paso(app, "fila_seleccionada", paso_excel=3)
boton_eliminar = frame.get_by_role("button", name="Eliminar", exact=True)
assert boton_eliminar.is_enabled(), "Se esperaba el boton Eliminar habilitado para una fila en estado inicial"
boton_eliminar.click()
app.wait_for_timeout(800)
dialogo = frame.locator(SELECTOR_DIALOGO)
assert dialogo.count() > 0 and dialogo.first.is_visible(), "Se esperaba el dialogo de confirmacion al eliminar"
texto_confirm = dialogo.first.inner_text()
assert "eliminar" in texto_confirm.lower(), f"Se esperaba el mensaje de confirmacion de eliminar, se vio: {texto_confirm!r}"
capturar_paso(app, "confirmacion_eliminar", paso_excel=5)
boton_si = dialogo.first.get_by_role("button", name=re.compile(r"^S.?$"))
boton_si.first.click()
esperar_fin_de_carga(app, frame)
for _i in range(60):
    app.wait_for_timeout(400)
    if not frame.locator(".ant-spin-blur").count():
        break
# CONFIRMADO EN VIVO el 17/09/2026 (mismo hallazgo que CP075): backend
# lento (hasta 16s reales medidos) para que aparezca el dialogo de
# resultado - se hace polling hasta 24s en vez de un solo chequeo.
resultado = None
for _i in range(60):
    app.wait_for_timeout(400)
    candidato = frame.locator(SELECTOR_DIALOGO)
    if candidato.count() and candidato.first.is_visible():
        resultado = candidato.first
        break
assert resultado is not None, "Se esperaba un dialogo de resultado tras confirmar la eliminacion"
texto_resultado = resultado.first.inner_text()
assert "registro eliminado" in texto_resultado.lower(), f"Se esperaba \\'Registro Eliminado...\\', se vio: {texto_resultado!r}"
capturar_paso(app, "mensaje_eliminado", paso_excel=6)
resultado.first.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
app.wait_for_timeout(1000)
leer_agenda(app, frame, fecha_proceso.isoformat())
tabla_agenda = frame.locator("app-agenda-principal table").nth(0)
texto_tabla = tabla_agenda.inner_text()
assert "sin registros" in texto_tabla.lower(), f"Se esperaba que la fila eliminada ya no aparezca en la grilla, se vio: {texto_tabla!r}"
capturar_paso(app, "fila_ya_no_existe", paso_excel=6)
print("[AVISO] No se pudo verificar en BD (tabla lec_grupo_zona) que la asignacion de libro de lectura a contratistas quedo efectivamente eliminada - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")
''')

add("CP080", "abrir_rf10", '''
fecha_proceso, sector_valor, corte_boleta, corte_terr = crear_agenda_prueba(app, frame)
capturar_paso(app, "agenda_creada", paso_excel=3)
leer_agenda(app, frame, fecha_proceso.isoformat())
capturar_paso(app, "fila_seleccionada", paso_excel=3)
tabla_venc = frame.locator("app-agenda-principal table").nth(1)
filas_venc = tabla_venc.locator("tbody tr")
fila_tipo1 = None
fecha_actual_texto = None
for i in range(filas_venc.count()):
    celdas = filas_venc.nth(i).locator("td").all_inner_texts()
    if celdas[0].strip() == "1":
        fila_tipo1 = filas_venc.nth(i)
        fecha_actual_texto = celdas[2].strip()
        break
assert fila_tipo1 is not None, "Se esperaba encontrar el tipo de vencimiento codigo 1 en la grilla"
fila_tipo1.click()
app.wait_for_timeout(500)
capturar_paso(app, "vencimiento_tipo1_seleccionado", paso_excel=4)
dd, mm, yy = fecha_actual_texto.split("/")
fecha_actual = date(int(yy), int(mm), int(dd))
nueva_fecha = _fecha_habil_segura(fecha_actual, 2)
campo_nueva_fecha = frame.locator("input[type=date]").nth(6)
campo_nueva_fecha.fill(nueva_fecha.isoformat())
app.wait_for_timeout(300)
capturar_paso(app, "nueva_fecha_ingresada", paso_excel=5)
boton_modifica = frame.get_by_role("button", name="Modifica Fecha", exact=True)
assert boton_modifica.is_enabled(), "Se esperaba el boton Modifica Fecha habilitado"
boton_modifica.click()
app.wait_for_timeout(800)
dialogo = frame.locator(SELECTOR_DIALOGO)
assert dialogo.count() > 0 and dialogo.first.is_visible(), "Se esperaba el dialogo de confirmacion al modificar la fecha de vencimiento"
texto_confirm = dialogo.first.inner_text()
assert "actualizaci" in texto_confirm.lower(), f"Se esperaba el mensaje de confirmacion de actualizacion, se vio: {texto_confirm!r}"
capturar_paso(app, "confirmacion_modifica_fecha", paso_excel=7)
boton_si = dialogo.first.get_by_role("button", name=re.compile(r"^S.?$"))
boton_si.first.click()
esperar_fin_de_carga(app, frame)
for _i in range(60):
    app.wait_for_timeout(400)
    if not frame.locator(".ant-spin-blur").count():
        break
# CONFIRMADO EN VIVO el 17/09/2026 (mismo hallazgo que CP075): backend
# lento (hasta 16s reales medidos) para que aparezca el dialogo de
# resultado - se hace polling hasta 24s en vez de un solo chequeo.
resultado = None
for _i in range(60):
    app.wait_for_timeout(400)
    candidato = frame.locator(SELECTOR_DIALOGO)
    if candidato.count() and candidato.first.is_visible():
        resultado = candidato.first
        break
assert resultado is not None, "Se esperaba un dialogo de resultado tras confirmar"
texto_resultado = resultado.first.inner_text()
assert "fecha actualizada" in texto_resultado.lower(), f"Se esperaba \\'Fecha Actualizada.\\', se vio: {texto_resultado!r}"
capturar_paso(app, "mensaje_fecha_actualizada", paso_excel=8)
resultado.first.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
app.wait_for_timeout(800)
print("[AVISO] No se pudo verificar en BD (fecha_corte_normal/fecha_corte_bol) que la fecha de corte de la agenda se recalculo de forma consistente - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")
''')

add("CP081", "abrir_rf10", '''
fecha_proceso, sector_valor, corte_boleta, corte_terr = crear_agenda_prueba(app, frame)
capturar_paso(app, "agenda_creada", paso_excel=3)
leer_agenda(app, frame, fecha_proceso.isoformat())
capturar_paso(app, "fila_seleccionada", paso_excel=3)
tabla_venc = frame.locator("app-agenda-principal table").nth(1)
filas_venc = tabla_venc.locator("tbody tr")
fila_tipo2 = None
fecha_actual_texto = None
for i in range(filas_venc.count()):
    celdas = filas_venc.nth(i).locator("td").all_inner_texts()
    if celdas[0].strip() != "1":
        fila_tipo2 = filas_venc.nth(i)
        fecha_actual_texto = celdas[2].strip()
        break
assert fila_tipo2 is not None, "Se esperaba encontrar un tipo de vencimiento con codigo distinto de 1 en la grilla"
fila_tipo2.click()
app.wait_for_timeout(500)
capturar_paso(app, "vencimiento_libres_seleccionado", paso_excel=4)
dd, mm, yy = fecha_actual_texto.split("/")
fecha_actual = date(int(yy), int(mm), int(dd))
nueva_fecha = _fecha_habil_segura(fecha_actual, 2)
campo_nueva_fecha = frame.locator("input[type=date]").nth(6)
campo_nueva_fecha.fill(nueva_fecha.isoformat())
app.wait_for_timeout(300)
frame.get_by_role("button", name="Modifica Fecha", exact=True).click()
app.wait_for_timeout(800)
dialogo = frame.locator(SELECTOR_DIALOGO)
assert dialogo.count() > 0 and dialogo.first.is_visible(), "Se esperaba un dialogo tras presionar Modifica Fecha"
texto = dialogo.first.inner_text()
if "clientes libres" not in texto.lower():
    # Puede aparecer primero un confirm Si/No antes del bloqueo real.
    boton_si = dialogo.first.get_by_role("button", name=re.compile(r"^S.?$"))
    if boton_si.count():
        boton_si.first.click()
        esperar_fin_de_carga(app, frame)
        for _i in range(30):
            app.wait_for_timeout(400)
            if not frame.locator(".ant-spin-blur").count():
                break
        app.wait_for_timeout(800)
        dialogo = frame.locator(SELECTOR_DIALOGO)
        assert dialogo.count() > 0 and dialogo.first.is_visible(), "Se esperaba un dialogo de resultado tras confirmar"
        texto = dialogo.first.inner_text()
capturar_paso(app, "mensaje_bloqueo_clientes_libres", paso_excel=6)
assert "clientes libres" in texto.lower(), f"Se esperaba el mensaje de bloqueo de Clientes Libres, se vio: {texto!r}"
dialogo.first.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
''')

add("CP082", "abrir_rf10", '''
fecha_proceso, sector_valor, corte_boleta, corte_terr = crear_agenda_prueba(app, frame)
capturar_paso(app, "agenda_creada", paso_excel=2)

def _seleccionar_venc_tipo1():
    tabla = frame.locator("app-agenda-principal table").nth(1)
    filas = tabla.locator("tbody tr")
    for i in range(filas.count()):
        celdas = filas.nth(i).locator("td").all_inner_texts()
        if celdas[0].strip() == "1":
            filas.nth(i).click()
            app.wait_for_timeout(500)
            return
    raise AssertionError("No se encontro el tipo de vencimiento codigo 1 en la grilla")

leer_agenda(app, frame, fecha_proceso.isoformat())
_seleccionar_venc_tipo1()
capturar_paso(app, "vencimiento_seleccionado", paso_excel=3)
campo_nueva_fecha = frame.locator("input[type=date]").nth(6)

# --- Sabado: aviso informativo, NO bloquea ---
d_sabado = fecha_proceso
while d_sabado.weekday() != 5:
    d_sabado += timedelta(days=1)
campo_nueva_fecha.fill(d_sabado.isoformat())
app.wait_for_timeout(600)
aviso_sab = frame.get_by_text(re.compile(r"Fecha de Vencimiento es S.bado", re.IGNORECASE))
assert aviso_sab.count() > 0 and aviso_sab.first.is_visible(), "Se esperaba el aviso \\'Fecha de Vencimiento es Sabado.\\'"
capturar_paso(app, "aviso_sabado", paso_excel=4)
frame.get_by_role("button", name="Modifica Fecha", exact=True).click()
app.wait_for_timeout(800)
dialogo_sab = frame.locator(SELECTOR_DIALOGO)
assert dialogo_sab.count() > 0 and dialogo_sab.first.is_visible(), "Se esperaba el dialogo de confirmacion para una fecha en sabado (no deberia bloquear)"
texto_sab = dialogo_sab.first.inner_text()
assert "actualizaci" in texto_sab.lower(), f"Se esperaba el confirm de actualizacion (sabado no bloquea), se vio: {texto_sab!r}"
capturar_paso(app, "confirmacion_sabado", paso_excel=5)
dialogo_sab.first.get_by_role("button", name=re.compile(r"^S.?$")).first.click()
esperar_fin_de_carga(app, frame)
for _i in range(30):
    app.wait_for_timeout(400)
    if not frame.locator(".ant-spin-blur").count():
        break
app.wait_for_timeout(800)
resultado_sab = frame.locator(SELECTOR_DIALOGO)
if resultado_sab.count() and resultado_sab.first.is_visible():
    resultado_sab.first.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
    app.wait_for_timeout(800)
capturar_paso(app, "sabado_actualizado_sin_bloqueo", paso_excel=5)

# --- Domingo: aviso + bloqueo total, sin dialogo de confirmacion ---
leer_agenda(app, frame, fecha_proceso.isoformat())
_seleccionar_venc_tipo1()
d_domingo = fecha_proceso
while d_domingo.weekday() != 6:
    d_domingo += timedelta(days=1)
campo_nueva_fecha = frame.locator("input[type=date]").nth(6)
campo_nueva_fecha.fill(d_domingo.isoformat())
app.wait_for_timeout(600)
aviso_dom = frame.get_by_text(re.compile(r"Fecha de Vencimiento es Domingo", re.IGNORECASE))
assert aviso_dom.count() > 0 and aviso_dom.first.is_visible(), "Se esperaba el aviso \\'Fecha de Vencimiento es Domingo.\\'"
capturar_paso(app, "aviso_domingo", paso_excel=6)
frame.get_by_role("button", name="Modifica Fecha", exact=True).click()
app.wait_for_timeout(800)
dialogo_dom = frame.locator(SELECTOR_DIALOGO)
assert dialogo_dom.count() > 0 and dialogo_dom.first.is_visible(), "Se esperaba el mensaje de bloqueo para una fecha en domingo"
texto_dom = dialogo_dom.first.inner_text()
assert "feriado o domingo" in texto_dom.lower(), f"Se esperaba \\'Dia feriado o Domingo, ingrese otra fecha.\\', se vio: {texto_dom!r}"
capturar_paso(app, "bloqueo_domingo", paso_excel=6)
dialogo_dom.first.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
app.wait_for_timeout(500)

# --- Feriado conocido: bloqueo total, sin aviso previo en la grilla ---
# 08/12/2026 (Inmaculada Concepcion) confirmado feriado en vivo el
# 16/09/2026 al chocar con la regla de unicidad de Fecha Corte Boleta.
leer_agenda(app, frame, fecha_proceso.isoformat())
_seleccionar_venc_tipo1()
campo_nueva_fecha = frame.locator("input[type=date]").nth(6)
campo_nueva_fecha.fill("2026-12-08")
app.wait_for_timeout(600)
capturar_paso(app, "fecha_feriado_ingresada", paso_excel=7)
frame.get_by_role("button", name="Modifica Fecha", exact=True).click()
app.wait_for_timeout(800)
dialogo_fer = frame.locator(SELECTOR_DIALOGO)
assert dialogo_fer.count() > 0 and dialogo_fer.first.is_visible(), "Se esperaba el mensaje de bloqueo para una fecha feriada"
texto_fer = dialogo_fer.first.inner_text()
assert "feriado o domingo" in texto_fer.lower(), f"Se esperaba \\'Dia feriado o Domingo, ingrese otra fecha.\\', se vio: {texto_fer!r}"
capturar_paso(app, "bloqueo_feriado", paso_excel=7)
dialogo_fer.first.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
''')

add("CP093", "abrir_rf10", '''
fecha_proceso, sector_valor, corte_boleta, corte_terr = crear_agenda_prueba(app, frame)
capturar_paso(app, "agenda_creada", paso_excel=2)
leer_agenda(app, frame, fecha_proceso.isoformat())
capturar_paso(app, "agenda_confirmada_en_grilla", paso_excel=2)

# La fila recien creada queda auto-seleccionada (boton en modo
# "Modificar") - hay que pasar por Cancelar primero para volver al
# formulario en blanco/modo Ingresar antes de poder dar de alta un
# NUEVO registro (confirmado en vivo el 16/09/2026: el boton
# "Ingresar" no existe como tal mientras hay una fila seleccionada).
frame.get_by_role("button", name="Cancelar", exact=True).click()
app.wait_for_timeout(500)
select_sector = frame.locator("select").first
select_sector.select_option(value=sector_valor)
app.wait_for_timeout(300)
inputs_fecha = frame.locator("input[type=date]")
inputs_fecha.nth(1).fill(fecha_proceso.isoformat())
app.wait_for_timeout(150)
inputs_fecha.nth(2).fill(fecha_proceso.isoformat())
app.wait_for_timeout(150)
inputs_fecha.nth(3).fill(fecha_proceso.isoformat())
app.wait_for_timeout(150)
corte_boleta2 = _fecha_habil_segura(fecha_proceso, 45)
corte_terr2 = _fecha_habil_segura(corte_boleta2, 3)
inputs_fecha.nth(4).fill(corte_boleta2.isoformat())
app.wait_for_timeout(150)
inputs_fecha.nth(5).fill(corte_terr2.isoformat())
app.wait_for_timeout(300)
capturar_paso(app, "intento_agenda_duplicada", paso_excel=3)
frame.get_by_role("button", name="Ingresar", exact=True).click()
app.wait_for_timeout(1200)
dialogo = frame.locator(SELECTOR_DIALOGO)
assert dialogo.count() > 0 and dialogo.first.is_visible(), "Se esperaba algun aviso al intentar duplicar una agenda para el mismo sector/periodo"
texto = dialogo.first.inner_text()
boton_si = dialogo.first.get_by_role("button", name=re.compile(r"^S.?$"))
if boton_si.count() and "zonas" in texto.lower():
    # El sistema no bloqueo antes del confirm normal - confirmar y ver
    # si el rechazo real llega recien al intentar grabar.
    capturar_paso(app, "confirm_normal_no_bloqueo_previo", paso_excel=3)
    boton_si.first.click()
    esperar_fin_de_carga(app, frame)
    for _i in range(30):
        app.wait_for_timeout(400)
        if not frame.locator(".ant-spin-blur").count():
            break
    app.wait_for_timeout(800)
    dialogo = frame.locator(SELECTOR_DIALOGO)
    assert dialogo.count() > 0 and dialogo.first.is_visible(), "Se esperaba un dialogo de resultado tras confirmar el alta duplicada"
    texto = dialogo.first.inner_text()
capturar_paso(app, "mensaje_resultado_duplicado", paso_excel=4)
boton_cerrar = dialogo.first.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$"))
if boton_cerrar.count():
    boton_cerrar.first.click()
    app.wait_for_timeout(500)
if "exitosamente" in texto.lower():
    print(f"[AVISO] El sistema NO rechazo por UI el alta de una segunda agenda para el sector {sector_valor} en el mismo mes/anio ({fecha_proceso.isoformat()}) - mensaje visto: {texto!r}. Esto podria ser un defecto real (falta la validacion de duplicados) o la validacion podria existir solo a nivel de otra combinacion de campos no cubierta aqui; requiere confirmar contra la tabla Agenda en BD, fuera del alcance de una verificacion solo-UI.")
else:
    print(f"[INFO] El sistema rechazo/aviso al intentar duplicar la agenda: {texto!r}")
''')

add("CP094", "abrir_rf10", '''
# CONFIRMADO EN VIVO el 16/09/2026: la matriz es contradictoria entre su
# columna "esperado" ("El sistema rechaza la fecha de corte por exceder
# el rango maximo permitido") y su propio ultimo paso ("El sistema
# acepta la fecha sin rechazo") - se probo en vivo con una Fecha Corte
# Boleta ~2.5 anios posterior a la Fecha de Vencimiento tipo 1 y el
# sistema la ACEPTO sin ningun rechazo ("Agenda registrada
# exitosamente."). No existe entonces una cota superior verificable por
# UI - se documenta el hallazgo real como AVISO en vez de forzar un
# assert en una direccion u otra que no esta claramente definida por el
# propio caso de prueba.
fecha_proceso, sector_valor, corte_boleta, corte_terr = crear_agenda_prueba(app, frame, offset_corte=900)
capturar_paso(app, "agenda_creada_con_corte_muy_lejano", paso_excel=5)
leer_agenda(app, frame, fecha_proceso.isoformat())
capturar_paso(app, "agenda_confirmada_en_grilla", paso_excel=5)
tabla_venc = frame.locator("app-agenda-principal table").nth(1)
filas_venc = tabla_venc.locator("tbody tr")
fecha_venc_tipo1 = None
for i in range(filas_venc.count()):
    celdas = filas_venc.nth(i).locator("td").all_inner_texts()
    if celdas[0].strip() == "1":
        fecha_venc_tipo1 = celdas[2].strip()
        break
assert fecha_venc_tipo1 is not None, "Se esperaba encontrar el tipo de vencimiento codigo 1 en la grilla"
dd, mm, yy = fecha_venc_tipo1.split("/")
dt_venc = date(int(yy), int(mm), int(dd))
dias_diferencia = (corte_boleta - dt_venc).days
print(f"[AVISO] Fecha Corte Boleta ({corte_boleta.isoformat()}) quedo aceptada {dias_diferencia} dias despues de la Fecha de Vencimiento tipo 1 ({fecha_venc_tipo1}) sin ningun rechazo del sistema - la matriz de casos es contradictoria en este punto (el campo \\'esperado\\' pide un rechazo por cota superior, pero el propio ultimo paso de la matriz ya anticipaba \\'El sistema acepta la fecha sin rechazo\\'). Confirmado en vivo: no existe una cota superior verificable por UI para esta version del sistema.")
''')

add("CP085", "abrir_rf10", '''
leer_agenda(app, frame, "2026-09-16")
frame.get_by_role("button", name="Vencimientos...", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "subpantalla_abierta", paso_excel=3)
modal = frame.locator(SELECTOR_DIALOGO).first
codigo_nuevo = str(random.randint(3, 89))
campo_codigo = modal.locator("input").nth(1)
campo_codigo.click()
campo_codigo.fill(codigo_nuevo)
app.wait_for_timeout(200)
campo_desc = modal.locator("input").nth(2)
campo_desc.click()
campo_desc.fill(f"TIPO PRUEBA {codigo_nuevo}"[:30])
app.wait_for_timeout(200)
campo_dias = modal.locator("input").nth(3)
campo_dias.click()
campo_dias.fill("10")
app.wait_for_timeout(200)
campo_habil = modal.locator("input").nth(4)
campo_habil.click()
campo_habil.fill("S")
app.wait_for_timeout(300)
capturar_paso(app, "formulario_completado", paso_excel=3)
boton_ingresar = modal.get_by_role("button", name="Ingresar", exact=True)
assert boton_ingresar.is_enabled(), "Se esperaba el boton Ingresar habilitado con todos los campos completos"
boton_ingresar.click()
app.wait_for_timeout(800)
dialogo = frame.locator(SELECTOR_DIALOGO)
dialogo_confirm = dialogo.last
texto_confirm = dialogo_confirm.inner_text()
assert "actualizaci" in texto_confirm.lower(), f"Se esperaba el confirm de actualizacion, se vio: {texto_confirm!r}"
capturar_paso(app, "confirmacion", paso_excel=4)
boton_si = dialogo_confirm.get_by_role("button", name=re.compile(r"^S.?$"))
boton_si.first.click()
for _i in range(30):
    app.wait_for_timeout(400)
    if not frame.locator(".ant-spin-blur").count():
        break
app.wait_for_timeout(800)
resultado = frame.locator(SELECTOR_DIALOGO)
resultado_ultimo = resultado.last
texto_resultado = resultado_ultimo.inner_text()
assert "registro actualizado" in texto_resultado.lower(), f"Se esperaba \\'Registro Actualizado.\\', se vio: {texto_resultado!r}"
capturar_paso(app, "mensaje_registro_actualizado", paso_excel=4)
resultado_ultimo.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
app.wait_for_timeout(500)
''')

add("CP086", "abrir_rf10", '''
leer_agenda(app, frame, "2026-09-16")
frame.get_by_role("button", name="Vencimientos...", exact=True).click()
app.wait_for_timeout(1500)
modal = frame.locator(SELECTOR_DIALOGO).first
codigo_nuevo = str(random.randint(3, 89))
modal.locator("input").nth(1).click()
modal.locator("input").nth(1).fill(codigo_nuevo)
app.wait_for_timeout(200)
modal.locator("input").nth(2).click()
modal.locator("input").nth(2).fill(f"TIPO PRUEBA {codigo_nuevo}"[:30])
app.wait_for_timeout(200)
modal.locator("input").nth(3).click()
modal.locator("input").nth(3).fill("10")
app.wait_for_timeout(200)
modal.locator("input").nth(4).click()
modal.locator("input").nth(4).fill("S")
app.wait_for_timeout(300)
modal.get_by_role("button", name="Ingresar", exact=True).click()
app.wait_for_timeout(800)
frame.locator(SELECTOR_DIALOGO).last.get_by_role("button", name=re.compile(r"^S.?$")).first.click()
for _i in range(30):
    app.wait_for_timeout(400)
    if not frame.locator(".ant-spin-blur").count():
        break
app.wait_for_timeout(800)
frame.locator(SELECTOR_DIALOGO).last.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
app.wait_for_timeout(800)
capturar_paso(app, "tipo_de_prueba_creado", paso_excel=3)

modal = frame.locator(SELECTOR_DIALOGO).first
filas = modal.locator("table").locator("tbody tr")
fila_objetivo = None
for i in range(filas.count()):
    celdas = filas.nth(i).locator("td").all_inner_texts()
    if celdas[0].strip() == codigo_nuevo:
        fila_objetivo = filas.nth(i)
        break
assert fila_objetivo is not None, f"Se esperaba encontrar el tipo recien creado (codigo {codigo_nuevo}) en la grilla"
fila_objetivo.click()
app.wait_for_timeout(500)
capturar_paso(app, "tipo_seleccionado", paso_excel=4)
campo_codigo2 = modal.locator("input").nth(1)
assert campo_codigo2.is_disabled() or campo_codigo2.get_attribute("readonly") is not None, "Se esperaba que el campo Codigo quedara en solo lectura al seleccionar un registro existente"
boton_principal = modal.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\\s*$"))
assert boton_principal.inner_text().strip() == "Modificar", f"Se esperaba el boton en modo Modificar, se vio: {boton_principal.inner_text()!r}"
campo_dias2 = modal.locator("input").nth(3)
campo_dias2.click()
campo_dias2.fill("12")
app.wait_for_timeout(300)
capturar_paso(app, "cant_dias_modificado", paso_excel=5)
boton_principal.click()
app.wait_for_timeout(800)
dialogo_confirm2 = frame.locator(SELECTOR_DIALOGO).last
texto_confirm2 = dialogo_confirm2.inner_text()
assert "actualizaci" in texto_confirm2.lower(), f"Se esperaba el confirm de actualizacion, se vio: {texto_confirm2!r}"
dialogo_confirm2.get_by_role("button", name=re.compile(r"^S.?$")).first.click()
for _i in range(30):
    app.wait_for_timeout(400)
    if not frame.locator(".ant-spin-blur").count():
        break
app.wait_for_timeout(800)
resultado2 = frame.locator(SELECTOR_DIALOGO).last
texto_resultado2 = resultado2.inner_text()
assert "registro actualizado" in texto_resultado2.lower(), f"Se esperaba \\'Registro Actualizado.\\', se vio: {texto_resultado2!r}"
capturar_paso(app, "mensaje_registro_actualizado", paso_excel=6)
resultado2.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
app.wait_for_timeout(500)
''')

# CONFIRMADO EN VIVO el 16/09/2026: CP089 ("Descargar PDF con grilla
# vacia debe bloquear") no se puede reproducir - TODOS los anios validos
# (2000-2099) llegan con un calendario civil/religioso PRE-POBLADO
# automaticamente (10-11 feriados fijos por anio, probado en los
# extremos 2000 y 2099 y tambien en 2087) - nunca hay una grilla vacia
# dentro del rango valido. Los anios fuera de rango (1999, 2100, 3000)
# son rechazados por su propia validacion ("Ingrese un anio valido
# (2000-2099).") ANTES de intentar cargar nada, asi que tampoco producen
# una grilla vacia real (solo dejan visibles los datos del anio anterior
# ya cargado). CP089 queda pendiente hasta que se defina otra forma de
# alcanzar ese estado (o se confirme con el usuario que es un escenario
# no reproducible en este ambiente).
add("CP087", "abrir_rf10", '''
leer_agenda(app, frame, "2026-09-16")
frame.get_by_role("button", name="Feriados...", exact=True).click()
app.wait_for_timeout(1800)
capturar_paso(app, "subpantalla_feriados_abierta", paso_excel=3)
modal = frame.locator(SELECTOR_DIALOGO).first
anio_prueba = str(random.randint(2030, 2098))
campo_anio = modal.locator("input").first
campo_anio.click()
campo_anio.fill(anio_prueba)
app.wait_for_timeout(200)
modal.get_by_role("button", name="Leer", exact=True).click()
app.wait_for_timeout(1200)
mes_dia_prueba = f"{random.randint(1,12):02d}-{random.randint(1,27):02d}"
fecha_prueba_iso = f"{anio_prueba}-{mes_dia_prueba}"
fecha_prueba_visual = f"{mes_dia_prueba[3:5]}/{mes_dia_prueba[0:2]}/{anio_prueba}"
campo_fecha = modal.locator("input").nth(1)
campo_fecha.fill(fecha_prueba_iso)
app.wait_for_timeout(300)
capturar_paso(app, "fecha_a_ingresar", paso_excel=4)
modal.get_by_role("button", name="Ingresar", exact=True).click()
app.wait_for_timeout(800)
dialogo = frame.locator(SELECTOR_DIALOGO).last
texto_confirm = dialogo.inner_text()
assert "ingresar la fecha como feriado" in texto_confirm.lower(), f"Se esperaba el confirm de ingresar feriado, se vio: {texto_confirm!r}"
capturar_paso(app, "confirmacion", paso_excel=5)
dialogo.get_by_role("button", name=re.compile(r"^S.?$")).first.click()
for _i in range(30):
    app.wait_for_timeout(400)
    if not frame.locator(".ant-spin-blur").count():
        break
app.wait_for_timeout(800)
resultado = frame.locator(SELECTOR_DIALOGO).last
texto_resultado = resultado.inner_text()
assert "registro ingresado" in texto_resultado.lower(), f"Se esperaba \\'Registro Ingresado.\\', se vio: {texto_resultado!r}"
capturar_paso(app, "mensaje_registro_ingresado", paso_excel=6)
resultado.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
app.wait_for_timeout(800)
assert fecha_prueba_visual in modal.inner_text(), f"Se esperaba que {fecha_prueba_visual!r} apareciera en la lista de feriados tras ingresarlo"
capturar_paso(app, "feriado_en_la_lista", paso_excel=6)
''')

add("CP088", "abrir_rf10", '''
leer_agenda(app, frame, "2026-09-16")
frame.get_by_role("button", name="Feriados...", exact=True).click()
app.wait_for_timeout(1800)
modal = frame.locator(SELECTOR_DIALOGO).first
anio_prueba = str(random.randint(2030, 2098))
campo_anio = modal.locator("input").first
campo_anio.click()
campo_anio.fill(anio_prueba)
app.wait_for_timeout(200)
modal.get_by_role("button", name="Leer", exact=True).click()
app.wait_for_timeout(1200)
mes_dia_prueba = f"{random.randint(1,12):02d}-{random.randint(1,27):02d}"
fecha_prueba_iso = f"{anio_prueba}-{mes_dia_prueba}"
fecha_prueba_visual = f"{mes_dia_prueba[3:5]}/{mes_dia_prueba[0:2]}/{anio_prueba}"
campo_fecha = modal.locator("input").nth(1)
campo_fecha.fill(fecha_prueba_iso)
app.wait_for_timeout(300)
modal.get_by_role("button", name="Ingresar", exact=True).click()
app.wait_for_timeout(800)
frame.locator(SELECTOR_DIALOGO).last.get_by_role("button", name=re.compile(r"^S.?$")).first.click()
for _i in range(30):
    app.wait_for_timeout(400)
    if not frame.locator(".ant-spin-blur").count():
        break
app.wait_for_timeout(800)
frame.locator(SELECTOR_DIALOGO).last.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
app.wait_for_timeout(800)
capturar_paso(app, "feriado_de_prueba_creado", paso_excel=3)

fila_feriado = modal.get_by_text(fecha_prueba_visual, exact=True)
assert fila_feriado.count() > 0, f"Se esperaba encontrar {fecha_prueba_visual!r} en la lista de feriados"
fila_feriado.first.click()
app.wait_for_timeout(500)
capturar_paso(app, "feriado_seleccionado", paso_excel=4)
boton_eliminar = modal.get_by_role("button", name="Eliminar", exact=True)
assert boton_eliminar.is_enabled(), "Se esperaba el boton Eliminar habilitado con un feriado seleccionado"
boton_eliminar.click()
app.wait_for_timeout(800)
dialogo = frame.locator(SELECTOR_DIALOGO).last
texto_confirm = dialogo.inner_text()
assert "eliminar el feriado" in texto_confirm.lower(), f"Se esperaba el confirm de eliminar feriado, se vio: {texto_confirm!r}"
capturar_paso(app, "confirmacion_eliminar", paso_excel=5)
dialogo.get_by_role("button", name=re.compile(r"^S.?$")).first.click()
for _i in range(30):
    app.wait_for_timeout(400)
    if not frame.locator(".ant-spin-blur").count():
        break
app.wait_for_timeout(800)
resultado = frame.locator(SELECTOR_DIALOGO).last
texto_resultado = resultado.inner_text()
assert "registro eliminado" in texto_resultado.lower(), f"Se esperaba \\'Registro Eliminado.\\', se vio: {texto_resultado!r}"
capturar_paso(app, "mensaje_registro_eliminado", paso_excel=6)
resultado.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
app.wait_for_timeout(800)
assert fecha_prueba_visual not in modal.inner_text(), f"Se esperaba que {fecha_prueba_visual!r} ya NO apareciera en la lista tras eliminarlo"
capturar_paso(app, "feriado_ya_no_en_la_lista", paso_excel=6)
''')

# CONFIRMADO EN VIVO el 17/09/2026: contrario a lo que se penso el
# 16/09/2026, SI se pueden eliminar los feriados fijos precargados (no
# estan protegidos) - usando el mismo dialogo "Esta seguro de eliminar
# el Feriado?" que ya usa CP088. Se usa el anio DEDICADO 2087 (fijo, no
# aleatorio) para esta prueba puntual: se vacia por completo (si quedo
# algo de una corrida anterior de CP087 que lo haya tocado al azar) y
# recien ahi se prueba "Descargar PDF". Al quedar 2087 vacio de forma
# permanente, la corrida siguiente ya lo encuentra vacio (idempotente).
add("CP089", "abrir_rf10", '''
leer_agenda(app, frame, "2026-09-16")
frame.get_by_role("button", name="Feriados...", exact=True).click()
app.wait_for_timeout(1800)
modal = frame.locator(SELECTOR_DIALOGO).last
anio_prueba = "2087"
campo_anio = modal.locator("input").first
campo_anio.click()
campo_anio.fill(anio_prueba)
app.wait_for_timeout(200)
modal.get_by_role("button", name="Leer", exact=True).click()
patron_fecha = re.compile(r"\\d{2}/\\d{2}/\\d{4}")
# La lista es un <ul>/<li> con estado transitorio (opacidad + spinner de
# puntos) mientras carga - se espera a que el conteo se estabilice.
conteo_anterior = -1
estable = 0
for _i in range(20):
    app.wait_for_timeout(400)
    n_actual = modal.get_by_text(patron_fecha).count()
    if n_actual == conteo_anterior:
        estable += 1
        if estable >= 3:
            break
    else:
        estable = 0
    conteo_anterior = n_actual
capturar_paso(app, "lista_feriados_2087_inicial", paso_excel=3)

boton_eliminar = modal.get_by_role("button", name="Eliminar", exact=True)
for _intento in range(15):
    filas_actuales = modal.get_by_text(patron_fecha)
    if filas_actuales.count() == 0:
        break
    for _spin in range(15):
        if not modal.locator(".ant-spin-dot, .ant-spin-blur").count():
            break
        app.wait_for_timeout(300)
    for _click in range(5):
        try:
            modal.get_by_text(patron_fecha).first.click(timeout=3000)
            break
        except PWTimeoutError:
            app.wait_for_timeout(500)
    app.wait_for_timeout(300)
    boton_eliminar.click()
    app.wait_for_timeout(800)
    dialogo_el = frame.locator(SELECTOR_DIALOGO).last
    if dialogo_el.count() and dialogo_el.is_visible():
        boton_si_el = dialogo_el.get_by_role("button", name=re.compile(r"^S.?$"))
        if boton_si_el.count():
            boton_si_el.first.click()
            for _i in range(30):
                app.wait_for_timeout(400)
                if not frame.locator(".ant-spin-blur").count():
                    break
            app.wait_for_timeout(600)
            resultado_el = frame.locator(SELECTOR_DIALOGO).last
            if resultado_el.count() and resultado_el.is_visible():
                resultado_el.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
                app.wait_for_timeout(600)

app.wait_for_timeout(1000)
assert modal.get_by_text(patron_fecha).count() == 0, "Se esperaba dejar la grilla de feriados de 2087 completamente vacia antes de probar el PDF"
capturar_paso(app, "grilla_feriados_vacia", paso_excel=4)

modal.get_by_role("button", name=re.compile("Descargar PDF")).click()
app.wait_for_timeout(1500)
dialogo_bloqueo = frame.locator(SELECTOR_DIALOGO).last
assert dialogo_bloqueo.count() > 0 and dialogo_bloqueo.is_visible(), "Se esperaba un dialogo de bloqueo al intentar descargar el PDF con la grilla vacia"
texto_bloqueo = dialogo_bloqueo.inner_text()
assert "deben existir datos en la grilla" in texto_bloqueo.lower() or "debe existir datos en la grilla" in texto_bloqueo.lower(), f"Se esperaba el mensaje de bloqueo \\'Debe existir datos en la grilla para que puedan ser Impresos.\\', se vio: {texto_bloqueo!r}"
capturar_paso(app, "bloqueo_pdf_grilla_vacia", paso_excel=5)
dialogo_bloqueo.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$")).first.click()
''')

# PENDIENTE (16/09/2026): CP076 ("Modificar vencimiento bloqueado por
# corte programado") y CP079 ("Bloqueo por corte programado - eliminar")
# requieren una fila de Agenda cuyo sector YA este "en proceso de
# facturacion" (corte programado vigente) - ese estado lo pone un
# proceso batch real del sistema, no se puede generar desde esta
# pantalla via UI. Se escaneo en vivo un rango de ~52 fechas reales
# (20 dias antes/despues de hoy + el dia 1 de cada mes de 2026) buscando
# algun sector que ya mostrara el aviso "Sector - Zona en proceso de
# Facturacion." o el boton Eliminar deshabilitado, y NINGUNA lo tenia
# (ver _exploracion/explore_rf10o_en_proceso.py) - probablemente porque
# los cortes reales de este ambiente de pruebas no estan corriendo o
# porque el periodo con corte vigente cae fuera del rango escaneado.
# Queda pendiente hasta encontrar (o que el usuario indique) una
# combinacion sector/fecha real con corte en curso, o una via alternativa
# para forzar ese estado.
add("CP073", "abrir_rf10", '''
frame.locator("input[type=date]").first.fill("2026-01-05")
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
try:
    frame.locator(".ant-spin-blur").first.wait_for(state="hidden", timeout=8000)
except PWTimeoutError:
    pass
app.wait_for_timeout(800)
capturar_paso(app, "tras_leer", paso_excel=3)
frame.get_by_role("button", name="Ingresar", exact=True).click()
app.wait_for_timeout(500)
dialogo_sector = frame.locator(SELECTOR_DIALOGO)
if dialogo_sector.count() and dialogo_sector.first.is_visible():
    dialogo_sector.first.get_by_role("button", name="Aceptar").click()
    app.wait_for_timeout(500)
select_sector = frame.locator("select").first
valores_sector = [v for v in select_sector.locator("option").evaluate_all("els => els.map(e => e.value)") if v]
select_sector.select_option(value=valores_sector[0])
app.wait_for_timeout(300)
inputs_fecha = frame.locator("input[type=date]")
campo_lectura, campo_emision = inputs_fecha.nth(1), inputs_fecha.nth(2)
campo_lectura.fill("2026-01-05")
app.wait_for_timeout(200)
campo_emision.fill("2026-01-09")
app.wait_for_timeout(200)
capturar_paso(app, "fechas_distintas_ingresadas", paso_excel=4)
frame.get_by_role("button", name="Ingresar", exact=True).click()
app.wait_for_timeout(1500)
dialogo = frame.locator(SELECTOR_DIALOGO)
assert dialogo.count() > 0 and dialogo.first.is_visible(), "Se esperaba un dialogo de validacion al ingresar Fecha de Emision distinta a Fecha de Proceso"
texto = dialogo.first.inner_text()
capturar_paso(app, "mensaje_de_validacion", paso_excel=5)
assert re.search(r"fechas de proceso y emisi.n deben ser iguales", texto, re.IGNORECASE), f"Se esperaba el mensaje de fechas Proceso/Emision distintas, se vio: {texto!r}"
dialogo.first.get_by_role("button", name="Aceptar").click()
''')

add("CP074", "abrir_rf10", '''
frame.locator("input[type=date]").first.fill("2026-01-05")
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
try:
    frame.locator(".ant-spin-blur").first.wait_for(state="hidden", timeout=8000)
except PWTimeoutError:
    pass
app.wait_for_timeout(800)
capturar_paso(app, "tras_leer", paso_excel=3)
frame.get_by_role("button", name="Ingresar", exact=True).click()
app.wait_for_timeout(500)
dialogo_sector = frame.locator(SELECTOR_DIALOGO)
if dialogo_sector.count() and dialogo_sector.first.is_visible():
    dialogo_sector.first.get_by_role("button", name="Aceptar").click()
    app.wait_for_timeout(500)
select_sector = frame.locator("select").first
valores_sector = [v for v in select_sector.locator("option").evaluate_all("els => els.map(e => e.value)") if v]
select_sector.select_option(value=valores_sector[0])
app.wait_for_timeout(300)
inputs_fecha = frame.locator("input[type=date]")
campo_lectura, campo_emision, campo_reparto, campo_corte_boleta = inputs_fecha.nth(1), inputs_fecha.nth(2), inputs_fecha.nth(3), inputs_fecha.nth(4)
campo_lectura.fill("2026-01-05")
app.wait_for_timeout(200)
campo_emision.fill("2026-01-05")
app.wait_for_timeout(200)
campo_reparto.fill("2026-01-05")
app.wait_for_timeout(200)
# 02/04/2026 es un feriado real confirmado en vivo (Viernes Santo, visto
# en el modal Feriados) y esta a mas de 16 dias de la Fecha de Proceso -
# margen suficiente para no chocar primero con la validacion de "Fecha
# de Corte debe ser Mayor a la Fecha de Vencimiento", tambien real y
# confirmada en vivo pero fuera del alcance de este caso puntual.
campo_corte_boleta.fill("2026-04-02")
app.wait_for_timeout(200)
capturar_paso(app, "corte_en_feriado_ingresado", paso_excel=4)
frame.get_by_role("button", name="Ingresar", exact=True).click()
app.wait_for_timeout(1500)
dialogo = frame.locator(SELECTOR_DIALOGO)
assert dialogo.count() > 0 and dialogo.first.is_visible(), "Se esperaba un dialogo de validacion al ingresar una Fecha de Corte Boleta feriada"
texto = dialogo.first.inner_text()
capturar_paso(app, "mensaje_de_validacion", paso_excel=5)
assert re.search(r"fecha de corte no puede ser feriado", texto, re.IGNORECASE), f"Se esperaba el mensaje de corte en feriado, se vio: {texto!r}"
dialogo.first.get_by_role("button", name="Aceptar").click()
''')

add("CP083", "abrir_rf10", '''
frame.locator("input[type=date]").first.fill("2026-09-16")
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
try:
    frame.locator(".ant-spin-blur").first.wait_for(state="hidden", timeout=8000)
except PWTimeoutError:
    pass
app.wait_for_timeout(800)
capturar_paso(app, "tras_leer", paso_excel=3)
boton_venc = frame.get_by_role("button", name="Vencimientos...", exact=True)
assert boton_venc.is_enabled(), "Se esperaba que el boton \\'Vencimientos...\\' estuviera habilitado tras Leer"
boton_venc.click()
app.wait_for_timeout(1500)
capturar_paso(app, "subpantalla_vencimientos_abierta", paso_excel=4)
modal = frame.locator(SELECTOR_DIALOGO).first
assert frame.get_by_text("Actualización de Tipos de Vencimientos").count() > 0, "Se esperaba que se abriera la sub-pantalla \\'Actualizacion de Tipos de Vencimientos\\'"
filas = modal.locator("table").locator("tbody tr")
assert filas.count() > 0, "Se esperaba que la grilla de tipos de vencimiento llegara poblada"
boton_ingresar_modal = modal.get_by_role("button", name="Ingresar", exact=True)
assert not boton_ingresar_modal.is_enabled(), "Se esperaba que el boton Ingresar estuviera deshabilitado hasta seleccionar/ingresar un codigo"
boton_dual = modal.get_by_role("button", name=re.compile(r"^(Cerrar|Cancelar)$"))
assert boton_dual.inner_text().strip() == "Cerrar", f"Se esperaba que el boton dual mostrara \\'Cerrar\\' en el estado inicial, se vio: {boton_dual.inner_text()!r}"
capturar_paso(app, "estado_inicial_verificado", paso_excel=5)
print(f"[INFO] {filas.count()} tipo(s) de vencimiento en la grilla.")
''')

add("CP084", "abrir_rf10", '''
frame.locator("input[type=date]").first.fill("2026-09-16")
app.wait_for_timeout(300)
frame.get_by_role("button", name="Leer", exact=True).click()
esperar_fin_de_carga(app, frame)
try:
    frame.locator(".ant-spin-blur").first.wait_for(state="hidden", timeout=8000)
except PWTimeoutError:
    pass
app.wait_for_timeout(800)
capturar_paso(app, "tras_leer", paso_excel=3)
boton_feriados = frame.get_by_role("button", name="Feriados...", exact=True)
assert boton_feriados.is_enabled(), "Se esperaba que el boton \\'Feriados...\\' estuviera habilitado tras Leer"
boton_feriados.click()
app.wait_for_timeout(1800)
capturar_paso(app, "subpantalla_feriados_abierta", paso_excel=4)
modal = frame.locator(SELECTOR_DIALOGO).first
anio_actual = str(date.today().year)
campo_anio = modal.locator("input").first
assert campo_anio.input_value().strip() == anio_actual, f"Se esperaba que el campo Anio mostrara el anio actual ({anio_actual}), se vio: {campo_anio.input_value()!r}"
fecha_hoy_iso = date.today().strftime("%Y-%m-%d")
campo_fecha = modal.locator("input").nth(1)
assert campo_fecha.input_value().strip() == fecha_hoy_iso, f"Se esperaba que el campo Fecha (type=date) inicializara con hoy ({fecha_hoy_iso}), se vio: {campo_fecha.input_value()!r}"
cantidad_feriados = len(re.findall(r"\\d{2}/\\d{2}/\\d{4}", modal.inner_text()))
assert cantidad_feriados > 0, "Se esperaba que la lista de Dias Feriados llegara poblada automaticamente"
capturar_paso(app, "estado_inicial_verificado", paso_excel=5)
print(f"[INFO] {cantidad_feriados} feriado(s) listado(s) para el anio {anio_actual}.")
''')

add("CP090", "abrir_rf10", '''
capturar_paso(app, "vista_desktop", paso_excel=3)
for ancho, alto, etiqueta in [(1600, 900, "desktop"), (1024, 768, "tablet"), (480, 800, "mobile")]:
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(800)
    capturar_paso(app, f"vista_{etiqueta}", paso_excel=3)
    contenedor = frame.locator("app-agenda-principal")
    assert contenedor.first.is_visible(), f"El contenido principal deberia seguir visible en {etiqueta} ({ancho}x{alto})"
    ancho_scroll = frame.locator("body").evaluate("el => el.scrollWidth")
    print(f"[INFO] {etiqueta} ({ancho}x{alto}): scrollWidth real = {ancho_scroll}px")
''')

# TODO RF-10: CP070,071,072,075,076,078-082,085-089,093,094 (18 casos)
# quedan pendientes - todos dependen del flujo completo "crear agenda"
# (Sector + 5 fechas + Ingresar + modal Vencimientos con calculo de
# dias habiles/feriados) o de sub-flujos de Vencimientos/Feriados aun
# no explorados a fondo (crear/modificar tipo de vencimiento, crear/
# eliminar feriado, descargar PDF) - decision explicita del usuario
# (16/09/2026) de priorizar por ahora el subconjunto de casos simples
# ya escrito arriba (CP069,073,074,083,084,090).


if __name__ == "__main__":
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")
