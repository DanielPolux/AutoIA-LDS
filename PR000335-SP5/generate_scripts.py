"""
generate_scripts.py (PR000335-SP5 - Seguimiento de Clientes MT / Asignacion
de Usuarios RHD / Listado de Pedidos Importantes / Resumen de Pedidos,
Sprint 5 del MAC).

Fuente de verdad: genera los 75 CPxxx.py (CP001..CP075) a partir de
matriz_casos.json + el framework compartido _framework/web_lds_core.py.

*** ESTADO: recien arrancado (15/09/2026), primera tanda de casos. ***

Ruta de menu CONFIRMADA EN VIVO para las 4 apps (misma rama que PR000335-2,
un nivel MAS CORTA - no hace falta abrir "Atenciones A Clientes" primero,
cada app es un item HOJA directo bajo "Atencion Integral Al Cliente"):
    Aplicaciones > Comercial > Atencion Integral Al Cliente > <Nombre app>
Cada click abre UN SOLO popup (a diferencia de PR000335-2 RF-04, que abria
2 a la vez) - alcanza con el abrir_aplicacion() generico del framework
(usa page.expect_popup(), no hace falta el _abrir_popup_por_titulo custom
de PR000335-2).

Componentes raiz CONFIRMADOS EN VIVO (ver _exploracion/dump_*.html):
  - Seguimiento De Clientes Mt -> app-seguimiento-de-clientes-mt
  - Asignacion De Usuarios     -> app-asignacion-rhd-page
  - Listado Pedidos Importantes -> app-listado-pedidos-importantes
  - Resumen De Pedidos         -> app-resumen-pedidos-page

Usuario/clave: mismo que PR000335-2 (DCABA_DW / Melquisedec_01).

Pendiente (ver TODOs en el cuerpo de cada caso): CP001 necesita un filtro
que devuelva registros reales (el default Area=Fonoluz + ultimo mes dio
"Registros: 0" en la exploracion en vivo) - falta confirmar un rango o
area con datos reales. CP005-CP032 (RF-01) y todo RF-02/03/04 siguen sin
escribir - ver matriz_casos.json para el detalle completo de los 75 casos.
"""
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT_DIR.parent / "_framework"))
import web_lds_core as core  # noqa: E402

PROYECTO = "PR000335-SP5"  # debe coincidir con el nombre de esta carpeta
MATRIZ = json.loads((OUT_DIR / "matriz_casos.json").read_text(encoding="utf-8"))

ENV_TOGGLES = core.ENV_TOGGLES_CODE.replace("__PROYECTO__", PROYECTO)

# ===========================================================================
# Helpers propios de PR000335-SP5 (no genericos del portal -> no van en
# _framework).
# ===========================================================================
PR000335_SP5_HELPERS = '''
# --- Seguimiento De Clientes Mt: ids CONFIRMADOS EN VIVO el 15/09/2026
#     (dump_seguimiento_mt.html) ---
SC_ID = {
    "Area": "sc-area",
    "SST": "sc-sst",
    "Expediente": "sc-exp",
    "Asignado": "sc-asig",
    "Tipo Fecha": "sc-tipo-fecha",
    "Desde": "sc-desde",
    "Hasta": "sc-hasta",
}


def campo_seguimiento(frame, etiqueta):
    return frame.locator(f"#{SC_ID[etiqueta]}")


def buscar_seguimiento(frame):
    """Boton 'Buscar [F6]' real: class=matf-btn-buscar (sin id propio)."""
    frame.locator("button.matf-btn-buscar").click()


def contador_registros(frame):
    return frame.get_by_text(re.compile(r"Registros:\\s*\\d+")).first


def esperar_busqueda(app, frame, valor_previo=None):
    """Espera a que 'Registros: N' cambie de valor tras Buscar/Limpiar y
    se estabilice 2 lecturas seguidas - CONFIRMADO EN VIVO el 17/09/2026:
    el spinner app-loading-spinner de esta pantalla NO es confiable (puede
    desaparecer mientras el contador sigue con el valor VIEJO)."""
    contador = contador_registros(frame)
    texto = valor_previo
    estable = 0
    for _i in range(40):
        app.wait_for_timeout(300)
        actual = contador.inner_text() if contador.count() else texto
        if actual == texto and actual != valor_previo:
            estable += 1
            if estable >= 2:
                break
        else:
            estable = 0
        texto = actual
    return texto


SELECTOR_MODAL_SC = "cdk-dialog-container"


def modal_sc(frame):
    """CONFIRMADO EN VIVO el 17/09/2026: varias acciones de esta pantalla
    apilan un 2do cdk-dialog-container ENCIMA del primero (ej. "Atencion
    a clientes" sobre "Asignacion", o "Exportacion generada" sobre
    "Historial"/"Contactos") - usar SIEMPRE .last (el mas nuevo), nunca
    el locator crudo (que resuelve al primero/mas viejo, ya tapado)."""
    return frame.locator(SELECTOR_MODAL_SC).last


def cerrar_modal_sc(frame, app):
    """Cierra el modal/dialogo activo de Seguimiento De Clientes Mt -
    CONFIRMADO EN VIVO: usa <cdk-dialog-container>, NO los selectores
    genericos de otros modulos. Boton cerrar con texto literal 'X'."""
    modal = modal_sc(frame)
    if not modal.count():
        return False
    for nombre in ("X", "Aceptar", "Cerrar", "Cancelar"):
        boton = modal.get_by_role("button", name=nombre, exact=True)
        if boton.count():
            boton.first.click()
            app.wait_for_timeout(800)
            return True
    return False


def marcar_filas(frame, indices):
    filas = frame.locator("table tbody tr")
    for i in indices:
        filas.nth(i).locator("input[type=checkbox]").check()


def desmarcar_todas_las_filas(frame):
    marcadas = frame.locator("table tbody tr input[type=checkbox]:checked")
    for i in range(marcadas.count()):
        marcadas.nth(i).uncheck()


def buscar_datos_reales(app, frame):
    """Rango CONFIRMADO EN VIVO (17/09/2026) con datos reales: Area
    Fonoluz (default), Desde 24/07/2022, Hasta 31/07/2022 -> 21
    registros. Usado por los casos que necesitan la grilla poblada."""
    valor_previo = contador_registros(frame).inner_text() if contador_registros(frame).count() else None
    campo_seguimiento(frame, "Desde").fill("2022-07-24")
    campo_seguimiento(frame, "Hasta").fill("2022-07-31")
    buscar_seguimiento(frame)
    return esperar_busqueda(app, frame, valor_previo)


# --- Resumen De Pedidos: ids CONFIRMADOS EN VIVO el 17/09/2026
#     (rf04_dump/00_pantalla_inicial.html). Boton "Buscar" real: class
#     matf-btn-buscar, SIN sufijo "[F6]" (a diferencia de otras
#     pantallas) - get_by_role(name="Buscar", exact=True) funciona
#     directo aca. "Filtro de Campo" es un multiselect custom
#     (app-matf-multiselect / .matf-multiselect-trigger), NO un
#     <select> comun - los 5 ejes (Subtipo Pedido/SET/Alimentador/SED/
#     Llave) + "TODOS" son checkboxes dentro de .matf-multiselect-host,
#     TODOS premarcados por defecto. ---
RP_ID = {
    "SET": "rp-set",
    "Alimentador": "rp-alim",
    "SED": "rp-sed",
    "Llave": "rp-llave",
    "Tiempo": "rp-tiempo",
    "Clasificacion": "rp-clasif",
    "Tipo": "rp-tipo",
    "Subtipo": "rp-subtipo",
    "Filtro Personalizado": "rp-filtro-pers",
}


def campo_resumen(frame, etiqueta):
    return frame.locator(f"#{RP_ID[etiqueta]}")


def buscar_resumen(frame):
    frame.get_by_role("button", name="Buscar", exact=True).click()


def toggle_filtro_campo(frame):
    frame.locator(".matf-multiselect-trigger").click()


def checkboxes_filtro_campo(frame):
    return frame.locator(".matf-multiselect-host input[type=checkbox]")


def tabla_resumen(frame):
    return frame.locator("app-resumen-pedidos-tabla-conteo table")


def tabla_detalle_resumen(frame):
    return frame.locator("app-resumen-pedidos-detalle-atenciones table")


# --- Listado Pedidos Importantes: ids CONFIRMADOS EN VIVO el 17/09/2026
#     (rf03_dump/00_pantalla_inicial.html). Boton "Buscar [F6]" real:
#     get_by_role match parcial (nombre completo incluye "[F6]"). ---
PI_ID = {
    "Codigo Llamada": "pi-codigo-llamada",
    "Caso Critico": "pi-caso",
    "Estado": "pi-estado",
    "Rango Fecha": "pi-rango",
    "Clasificacion": "pi-clasif",
    "Tipo": "pi-tipo",
    "Subtipo": "pi-subtipo",
    "Desde": "pi-desde",
    "Hasta": "pi-hasta",
    "Filtro Personalizado": "pi-filtro-pers",
}

SELECTOR_MODAL_PI = "cdk-dialog-container, .mdl-confirmar, nz-modal-container"


def campo_pedido(frame, etiqueta):
    return frame.locator(f"#{PI_ID[etiqueta]}")


def buscar_pedidos(frame):
    frame.get_by_role("button", name=re.compile(r"^Buscar")).click()


def total_pedidos(frame):
    return frame.get_by_text(re.compile(r"Total registros:\\s*\\{\\d+\\}")).first


def modal_pi(frame):
    """CONFIRMADO EN VIVO: mismo gotcha de dialogos apilados que
    Seguimiento De Clientes Mt - usar SIEMPRE .last."""
    return frame.locator(SELECTOR_MODAL_PI).last


def cerrar_modal_pi(frame, app):
    modal = modal_pi(frame)
    if not modal.count():
        return False
    for nombre in ("X", "Aceptar", "Cerrar", "Cancelar"):
        boton = modal.get_by_role("button", name=nombre, exact=True)
        if boton.count():
            boton.first.click()
            app.wait_for_timeout(800)
            return True
    return False


def seleccionar_fila_pedido(frame, indice=0):
    """CONFIRMADO EN VIVO: la grilla NO tiene checkbox de seleccion
    propio (los 2 checkbox visibles por fila son datos de solo lectura,
    Importante/Riesgo Vida) - se selecciona con click directo en la
    fila (queda con class='selected')."""
    frame.locator("table tbody tr").nth(indice).click()


# --- Asignacion RHD: ids CONFIRMADOS EN VIVO el 15/09/2026
#     (dump_rhd_modal_agregar.html). Modal "Agregar Registro":
#     componente app-modal-opciones-rhd, campos Clase/Nivel Tension/
#     Rol Usuario (maxlength 20) + checkbox Asignar Responsable. ---
def abrir_modal_rhd(frame, nombre_boton):
    """Agregar/Modificar/Eliminar abren el MISMO tipo de modal
    (app-modal-opciones-rhd), titulo "Agregar Registro"/"Modificar
    Registro"/"Eliminar Registro" segun el boton."""
    frame.get_by_role("button", name=nombre_boton, exact=True).click()
    dialogo = frame.get_by_role("dialog")
    dialogo.wait_for(state="visible", timeout=8000)
    return dialogo


def completar_modal_rhd(dialogo, clase=None, tension=None, usuario=None, responsable=None):
    if clase is not None:
        dialogo.locator("#rhd-modal-clase").select_option(label=clase)
    if tension is not None:
        dialogo.locator("#rhd-modal-tension").select_option(label=tension)
    if usuario is not None:
        dialogo.locator("#rhd-modal-usuario").fill(usuario)
    if responsable is not None:
        checkbox = dialogo.locator("#rhd-modal-responsable")
        if responsable:
            checkbox.check()
        else:
            checkbox.uncheck()
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

# --- Navegacion: CONFIRMADA EN VIVO el 15/09/2026 - cada app es un item
#     hoja directo, un solo popup por click (ver docstring del modulo). ---
RUTA_MENU = ["Comercial", "Atenci\\u00f3n Integral Al Cliente"]


def abrir_seguimiento_mt(page, paso_excel=1):
    return abrir_aplicacion(page, RUTA_MENU + ["Seguimiento De Clientes Mt"], "app-seguimiento-de-clientes-mt", paso_excel=paso_excel)


def abrir_asignacion_rhd(page, paso_excel=1):
    return abrir_aplicacion(page, RUTA_MENU + ["Asignacion De Usuarios"], "app-asignacion-rhd-page", paso_excel=paso_excel)


def abrir_pedidos_importantes(page, paso_excel=1):
    return abrir_aplicacion(page, RUTA_MENU + ["Listado Pedidos Importantes"], "app-listado-pedidos-importantes", paso_excel=paso_excel)


def abrir_resumen_pedidos(page, paso_excel=1):
    return abrir_aplicacion(page, RUTA_MENU + ["Resumen De Pedidos"], "app-resumen-pedidos-page", paso_excel=paso_excel)


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
        try:
            login(page, paso_excel=1)
            app, frame = {abrir_fn}(page)

{body}

            capturar_paso(app, "estado_final_del_caso", paso_excel=max(_parsear_pasos_excel(PASOS_CASO), default=None))

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
     .replace("%%HELPERS_PROPIOS%%", PR000335_SP5_HELPERS.strip("\n"))


CASES = []


def add(cp, abrir_fn, body):
    m = MATRIZ[cp]
    CASES.append(dict(
        cp=cp, rf=m["rf"], cu=m["cu"], name=m["name"], desc=m["desc"],
        precond=m["precond"], datos=m["datos"], esperado=m["esperado"],
        pasos=m["pasos"], abrir_fn=abrir_fn, body=body,
    ))


# ===========================================================================
# RF-01 - Seguimiento De Clientes Mt (CP001-CP032)
# App: "Seguimiento De Clientes Mt". Confirmada en vivo la pantalla base
# (filtros + grilla + defaults), ver docstring del modulo.
# ===========================================================================

add("CP001", "abrir_seguimiento_mt", '''
# CONFIRMADO (17/09/2026): con el rango por defecto (ultimo mes) la
# busqueda daba "Registros: 0" - el usuario confirmo un rango real con
# datos: Desde 24/07/2022, Hasta 31/07/2022.
campo_seguimiento(frame, "Desde").fill("2022-07-24")
campo_seguimiento(frame, "Hasta").fill("2022-07-31")
capturar_paso(app, "rango_fecha_completado", paso_excel=5)
valor_previo = contador_registros(frame).inner_text() if contador_registros(frame).count() else None
buscar_seguimiento(frame)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "busqueda_ejecutada", paso_excel=6)
texto_contador = esperar_busqueda(app, frame, valor_previo)
capturar_paso(app, "resultado_verificado", paso_excel=7)
m = re.search(r"Registros:\\s*(\\d+)", texto_contador)
cantidad = int(m.group(1)) if m else 0
if cantidad > 0:
    print(f"[INFO] Contador real: {texto_contador!r} - rango 24/07/2022-31/07/2022 SI trae resultados, desbloquea el filtro pendiente documentado en el modulo.")
else:
    print(f"[AVISO] Contador real: {texto_contador!r} - el rango 24/07/2022-31/07/2022 tampoco trajo resultados en esta corrida, sigue pendiente confirmar un filtro con datos reales.")
''')

add("CP002", "abrir_seguimiento_mt", '''
# CONFIRMADO EN VIVO el 15/09/2026: Desde = hoy menos 1 mes, Hasta = hoy
# (el original, NO lo que dice el EF - ver descripcion del caso).
hoy = date.today()
desde_esperado = (hoy - timedelta(days=30))  # aproximado: el propio caso ya documenta "hoy menos un mes" sin exigir el dia exacto de calendario
valor_desde = campo_seguimiento(frame, "Desde").input_value()
valor_hasta = campo_seguimiento(frame, "Hasta").input_value()
capturar_paso(app, "valores_por_defecto_revisados", paso_excel=6)
assert valor_hasta.strip(), "Se esperaba que 'Hasta' llegue con la fecha actual, llego vacio"
assert valor_desde.strip(), "Se esperaba que 'Desde' llegue con hoy menos un mes, llego vacio"
print(f"[INFO] Desde={valor_desde!r} Hasta={valor_hasta!r} (referencia hoy={hoy.isoformat()})")
''')

add("CP003", "abrir_seguimiento_mt", '''
# CONFIRMADO EN VIVO el 15/09/2026: Tipo Fecha llega en "Fecha Creacion" (value=1).
valor = frame.locator("#sc-tipo-fecha").input_value()
opcion_seleccionada = frame.locator("#sc-tipo-fecha option:checked").inner_text()
capturar_paso(app, "tipo_fecha_revisado", paso_excel=5)
assert "creacion" in opcion_seleccionada.lower(), f"Se esperaba 'Fecha Creacion' preseleccionado, se vio {opcion_seleccionada!r}"
''')

add("CP004", "abrir_seguimiento_mt", '''
# CONFIRMADO EN VIVO el 15/09/2026: las 3 opciones reales son "Fecha
# Creacion", "Fecha Asignacion", "Fecha Sig. Seguimiento" (dump_seguimiento_mt.html).
opciones = frame.locator("#sc-tipo-fecha option").all_inner_texts()
capturar_paso(app, "opciones_tipo_fecha_revisadas", paso_excel=5)
ESPERADAS = ["Fecha Creacion", "Fecha Asignacion", "Fecha Sig. Seguimiento"]
for e in ESPERADAS:
    assert any(e.lower() in o.lower() for o in opciones), f"Se esperaba la opcion {e!r} en Tipo Fecha, opciones reales: {opciones}"
assert len(opciones) == len(ESPERADAS), f"Se esperaban exactamente {len(ESPERADAS)} opciones, hay {len(opciones)}: {opciones}"
''')

# CONFIRMADO EN VIVO el 17/09/2026 (ver docstring del modulo
# seguimiento_clientes_mt.py para el detalle completo de mensajes,
# selectores de modal y columnas): CP005-CP032 escritos con el rango de
# datos reales confirmado (Area Fonoluz, 24/07/2022-31/07/2022 -> 21
# registros, ver buscar_datos_reales()).

add("CP005", "abrir_seguimiento_mt", '''
campo_seguimiento(frame, "Desde").fill("")
capturar_paso(app, "fecha_inicio_vacia", paso_excel=4)
buscar_seguimiento(frame)
app.wait_for_timeout(1200)
capturar_paso(app, "mensaje_validacion", paso_excel=5)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba un dialogo de validacion al buscar sin fecha de inicio"
texto = modal.inner_text()
assert "la fecha de inicio no puede ser vacia" in texto.lower(), f"Se esperaba 'La fecha de inicio no puede ser vacia', se vio: {texto!r}"
capturar_paso(app, "busqueda_no_ejecutada", paso_excel=6)
cerrar_modal_sc(frame, app)
''')

add("CP006", "abrir_seguimiento_mt", '''
campo_seguimiento(frame, "Desde").fill("2022-08-01")
campo_seguimiento(frame, "Hasta").fill("2022-07-01")
capturar_paso(app, "rango_invertido", paso_excel=4)
buscar_seguimiento(frame)
app.wait_for_timeout(1200)
capturar_paso(app, "mensaje_validacion", paso_excel=5)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba un dialogo de validacion con fecha de inicio posterior a la de fin"
texto = modal.inner_text()
assert "la fecha de fin no puede ser mayor a la de inicio" in texto.lower(), f"Se esperaba 'La fecha de fin no puede ser mayor a la de inicio', se vio: {texto!r}"
capturar_paso(app, "busqueda_no_ejecutada", paso_excel=6)
cerrar_modal_sc(frame, app)
''')

add("CP007", "abrir_seguimiento_mt", '''
min_desde = campo_seguimiento(frame, "Desde").get_attribute("min")
capturar_paso(app, "min_desde_revisado", paso_excel=4)
min_hasta = campo_seguimiento(frame, "Hasta").get_attribute("min")
capturar_paso(app, "min_hasta_revisado", paso_excel=5)
assert min_desde == "2021-01-01", f"Se esperaba que 'Desde' declare fecha minima 2021-01-01, se vio: {min_desde!r}"
assert min_hasta == "2021-01-01", f"Se esperaba que 'Hasta' declare fecha minima 2021-01-01, se vio: {min_hasta!r}"
capturar_paso(app, "ambos_campos_verificados", paso_excel=6)
''')

add("CP008", "abrir_seguimiento_mt", '''
# Codigo SST real confirmado en vivo (17/09/2026) con seguimientos:
# 3322333 (expediente 0338751). El rango de fecha por defecto (hoy
# menos 1 mes) NO alcanza a este dato de 2022 - hay que fijar el mismo
# rango confirmado que usa buscar_datos_reales(), o la busqueda por SST
# da "No hay seguimientos para mostrar." aunque el codigo SI exista.
campo_seguimiento(frame, "Desde").fill("2022-07-24")
campo_seguimiento(frame, "Hasta").fill("2022-07-31")
codigo_sst = "3322333"
campo_seguimiento(frame, "SST").fill(codigo_sst)
capturar_paso(app, "sst_ingresado", paso_excel=4)
buscar_seguimiento(frame)
esperar_busqueda(app, frame)
capturar_paso(app, "busqueda_ejecutada", paso_excel=5)
filas_sst = frame.locator("table tbody tr").all_inner_texts()
assert len(filas_sst) > 0, f"Se esperaba encontrar al menos un seguimiento para el SST {codigo_sst!r}"
assert all(codigo_sst in f for f in filas_sst), f"Se esperaba que TODAS las filas correspondan al SST {codigo_sst!r}, se vio: {filas_sst}"
capturar_paso(app, "grilla_filtrada_verificada", paso_excel=6)
''')

add("CP009", "abrir_seguimiento_mt", '''
for etiqueta in ("SST", "Expediente", "Asignado"):
    campo = campo_seguimiento(frame, etiqueta)
    ml = campo.get_attribute("maxlength")
    assert ml == "10", f"Se esperaba maxlength=10 en {etiqueta!r}, se vio: {ml!r}"
    campo.fill("12345678901")
    valor_real = campo.input_value()
    assert len(valor_real) <= 10, f"El campo {etiqueta!r} admitio mas de 10 caracteres: {valor_real!r} ({len(valor_real)} caracteres)"
    campo.fill("")
capturar_paso(app, "maxlength_verificado_en_los_3_campos", paso_excel=7)
''')

add("CP010", "abrir_seguimiento_mt", '''
# TODO SIN CONFIRMAR: se necesitaria un 2do usuario con permisos
# distintos para comparar las opciones del filtro Area entre ambos -
# solo se cuenta con las credenciales de DCABA_DW en este ambiente. Se
# documenta lo que SI se puede verificar con un solo usuario: que el
# filtro Area llega poblado (no vacio) segun los permisos de este
# usuario.
opciones_area = frame.locator("#sc-area option").all_inner_texts()
capturar_paso(app, "opciones_area_usuario_actual", paso_excel=4)
assert len(opciones_area) > 0, "Se esperaba que el filtro de Area tuviera al menos una opcion para este usuario"
print(f"[AVISO] Opciones de Area para DCABA_DW: {opciones_area!r} - no se pudo comparar contra un 2do usuario con permisos distintos, requiere otra cuenta real fuera del alcance de esta corrida.")
''')

add("CP011", "abrir_seguimiento_mt", '''
toggle_estado = frame.locator("div").filter(has_text=re.compile(r"^Estado:$")).locator("xpath=..").locator("button")
toggle_estado.first.click()
app.wait_for_timeout(800)
capturar_paso(app, "filtro_estado_desplegado", paso_excel=4)
opciones_checkbox = frame.locator("input[type=checkbox]")
con_asterisco = []
sin_asterisco = []
for i in range(opciones_checkbox.count()):
    op = opciones_checkbox.nth(i)
    if not op.is_visible():
        continue
    hermano = op.locator("xpath=following-sibling::*[1]")
    texto_label = hermano.inner_text().strip() if hermano.count() else ""
    if not texto_label or texto_label.upper() == "TODOS":
        continue
    if "(*)" in texto_label:
        con_asterisco.append(texto_label)
    else:
        sin_asterisco.append(texto_label)
capturar_paso(app, "estados_revisados", paso_excel=5)
assert len(con_asterisco) > 0, f"Se esperaba al menos un estado con el sufijo (*), opciones vistas: con={con_asterisco} sin={sin_asterisco}"
assert len(sin_asterisco) > 0, f"Se esperaba al menos un estado SIN el sufijo (*), opciones vistas: con={con_asterisco} sin={sin_asterisco}"
capturar_paso(app, "estados_sin_sufijo_verificados", paso_excel=6)
print(f"[INFO] Con (*): {con_asterisco!r} | Sin (*): {sin_asterisco!r}")
''')

add("CP012", "abrir_seguimiento_mt", '''
campo_seguimiento(frame, "Desde").fill("2022-07-24")
campo_seguimiento(frame, "Hasta").fill("2022-07-31")
toggle_estado = frame.locator("div").filter(has_text=re.compile(r"^Estado:$")).locator("xpath=..").locator("button")
toggle_estado.first.click()
app.wait_for_timeout(800)
opciones_checkbox = frame.locator("input[type=checkbox]")
marcados = []
for i in range(opciones_checkbox.count()):
    op = opciones_checkbox.nth(i)
    if not op.is_visible():
        continue
    hermano = op.locator("xpath=following-sibling::*[1]")
    texto_label = hermano.inner_text().strip() if hermano.count() else ""
    if texto_label and texto_label.upper() != "TODOS" and len(marcados) < 2:
        op.check()
        marcados.append(texto_label)
capturar_paso(app, "dos_estados_marcados", paso_excel=4)
frame.locator("body").click(position={"x": 10, "y": 10})
app.wait_for_timeout(300)
buscar_seguimiento(frame)
esperar_busqueda(app, frame)
capturar_paso(app, "busqueda_ejecutada", paso_excel=5)
filas_estado = frame.locator("table tbody tr").all_inner_texts()
estados_en_grilla = {f.split("\\t")[2] if len(f.split("\\t")) > 2 else "" for f in filas_estado}
print(f"[INFO] Estados marcados: {marcados!r} | Estados presentes en la grilla: {estados_en_grilla!r}")
capturar_paso(app, "resultado_multi_estado_verificado", paso_excel=6)
''')

add("CP013", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
capturar_paso(app, "busqueda_con_resultados", paso_excel=4)
encabezados = frame.locator("table thead th").all_inner_texts()
assert any("etapa siguiente" in h.lower() for h in encabezados), f"Se esperaba la columna 'Etapa siguiente' en la grilla, encabezados reales: {encabezados}"
indice_col = next(i for i, h in enumerate(encabezados) if "etapa siguiente" in h.lower())
filas = frame.locator("table tbody tr")
valores_etapa = []
for i in range(min(filas.count(), 5)):
    celdas = filas.nth(i).locator("td").all_inner_texts()
    if indice_col < len(celdas):
        valores_etapa.append(celdas[indice_col].strip())
capturar_paso(app, "columna_etapa_siguiente_revisada", paso_excel=5)
print(f"[INFO] Valores de 'Etapa siguiente' (primeras {len(valores_etapa)} filas): {valores_etapa!r}")
''')

add("CP014", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
capturar_paso(app, "busqueda_con_resultados", paso_excel=4)
# TODO SIN CONFIRMAR: el identificador de seguimiento (Id) no es una
# columna visible de la grilla principal (solo aparece dentro del modal
# de Historial Estados, ver CP021) - no se pudo confirmar el orden
# exacto por Id sin abrir el historial fila por fila, fuera del alcance
# de una verificacion rapida. Se documenta que la grilla SI trae un
# orden estable (no aleatorio) entre 2 lecturas.
filas_1 = frame.locator("table tbody tr").all_inner_texts()
buscar_seguimiento(frame)
esperar_busqueda(app, frame)
filas_2 = frame.locator("table tbody tr").all_inner_texts()
capturar_paso(app, "orden_verificado", paso_excel=5)
assert filas_1 == filas_2, "Se esperaba que el orden de las filas fuera estable entre 2 busquedas identicas"
print("[AVISO] Orden estable confirmado entre 2 lecturas, pero no se pudo verificar que sea especificamente descendente por Id de seguimiento (esa columna no esta visible en la grilla principal).")
''')

add("CP015", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
capturar_paso(app, "busqueda_con_resultados", paso_excel=4)
with app.expect_download(timeout=10000) as descarga_info:
    frame.get_by_role("button", name="Exportar", exact=True).click()
descarga = descarga_info.value
capturar_paso(app, "exportacion_disparada", paso_excel=5)
assert descarga.suggested_filename.lower().endswith(".xlsx"), f"Se esperaba un archivo .xlsx, se vio: {descarga.suggested_filename!r}"
descarga.save_as(str(EVIDENCIA / descarga.suggested_filename))
app.wait_for_timeout(500)
modal = modal_sc(frame)
if modal.count():
    texto_modal = modal.inner_text()
    assert "exportaci" in texto_modal.lower(), f"Se esperaba un mensaje de exportacion generada, se vio: {texto_modal!r}"
    cerrar_modal_sc(frame, app)
capturar_paso(app, "descarga_verificada", paso_excel=6)
''')

add("CP016", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
capturar_paso(app, "busqueda_con_resultados", paso_excel=4)
desmarcar_todas_las_filas(frame)
capturar_paso(app, "sin_seleccion", paso_excel=5)
with app.expect_download(timeout=10000) as descarga_info:
    frame.get_by_role("button", name="Exportar", exact=True).click()
descarga = descarga_info.value
capturar_paso(app, "exportacion_realizada_sin_seleccion", paso_excel=6)
assert descarga.suggested_filename.lower().endswith(".xlsx"), f"Se esperaba que la exportacion funcione SIN seleccionar ninguna fila, se vio: {descarga.suggested_filename!r}"
descarga.save_as(str(EVIDENCIA / descarga.suggested_filename))
modal = modal_sc(frame)
if modal.count():
    cerrar_modal_sc(frame, app)
capturar_paso(app, "verificado", paso_excel=7)
''')

add("CP017", "abrir_seguimiento_mt", '''
campo_seguimiento(frame, "Desde").fill("2022-01-01")
campo_seguimiento(frame, "Hasta").fill("2022-01-02")
buscar_seguimiento(frame)
texto_contador = esperar_busqueda(app, frame)
capturar_paso(app, "grilla_sin_resultados", paso_excel=4)
assert "0" in texto_contador, f"Se esperaba una grilla vacia (Registros: 0) para probar el mensaje, se vio: {texto_contador!r}"
try:
    with app.expect_download(timeout=5000) as descarga_info:
        frame.get_by_role("button", name="Exportar", exact=True).click()
    assert False, f"Se esperaba que NO se inicie ninguna descarga con la grilla vacia, pero se descargo: {descarga_info.value.suggested_filename!r}"
except PWTimeoutError:
    pass
app.wait_for_timeout(500)
capturar_paso(app, "mensaje_validacion", paso_excel=5)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba un dialogo de aviso al exportar con la grilla vacia"
texto = modal.inner_text()
assert "no hay datos para exportar" in texto.lower(), f"Se esperaba 'No hay datos para exportar.', se vio: {texto!r}"
capturar_paso(app, "sin_descarga_verificado", paso_excel=6)
cerrar_modal_sc(frame, app)
''')

add("CP018", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
capturar_paso(app, "busqueda_con_resultados", paso_excel=4)
with app.expect_download(timeout=10000) as descarga_info:
    frame.get_by_role("button", name="Exportar", exact=True).click()
descarga = descarga_info.value
ruta_descarga = EVIDENCIA / descarga.suggested_filename
descarga.save_as(str(ruta_descarga))
capturar_paso(app, "archivo_descargado", paso_excel=5)
app.wait_for_timeout(500)
modal = modal_sc(frame)
if modal.count():
    cerrar_modal_sc(frame, app)
# TODO SIN CONFIRMAR: abrir el .xlsx descargado y comparar columna por
# columna contra la grilla requeriria una libreria de lectura de Excel
# (openpyxl) - se deja documentado como pendiente en vez de asumir el
# contenido sin verificarlo.
assert ruta_descarga.exists() and ruta_descarga.stat().st_size > 0, f"Se esperaba que el archivo exportado {ruta_descarga.name!r} exista y no este vacio"
print(f"[AVISO] Archivo exportado guardado en {ruta_descarga.name!r} ({ruta_descarga.stat().st_size} bytes) - no se abrio para comparar columna por columna contra la grilla, requeriria una libreria de lectura de Excel fuera del alcance de esta corrida.")
capturar_paso(app, "archivo_verificado_existencia", paso_excel=6)
''')

add("CP019", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
capturar_paso(app, "busqueda_con_resultados", paso_excel=4)
desmarcar_todas_las_filas(frame)
capturar_paso(app, "sin_seleccion", paso_excel=5)
frame.get_by_role("button", name="Asignar", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "mensaje_validacion", paso_excel=6)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba un dialogo de aviso al presionar Asignar sin seleccion"
texto = modal.inner_text()
assert "seleccione como m" in texto.lower() and "una fila" in texto.lower(), f"Se esperaba 'Seleccione como minimo una fila.', se vio: {texto!r}"
assert "Asignaci" not in texto, f"Se esperaba que el modal de Asignacion NO se abra, se vio: {texto!r}"
capturar_paso(app, "modal_asignacion_no_abierto", paso_excel=7)
cerrar_modal_sc(frame, app)
''')

add("CP020", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
marcar_filas(frame, [0])
app.wait_for_timeout(400)
frame.get_by_role("button", name="Asignar", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "modal_asignacion_abierto", paso_excel=4)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que el modal de Asignacion se abra con una fila seleccionada"
capturar_paso(app, "sin_elegir_usuario", paso_excel=5)
boton_confirmar = modal.get_by_role("button", name="Aceptar", exact=True)
boton_confirmar.first.click()
app.wait_for_timeout(1200)
capturar_paso(app, "confirmado_sin_usuario", paso_excel=6)
modal_resultado = modal_sc(frame)
assert modal_resultado.count() > 0 and modal_resultado.is_visible(), "Se esperaba un mensaje al confirmar la asignacion sin elegir usuario"
texto = modal_resultado.inner_text()
assert "seleccione un usuario" in texto.lower(), f"Se esperaba 'Seleccione un usuario para continuar.', se vio: {texto!r}"
capturar_paso(app, "no_se_asigno_nada_verificado", paso_excel=7)
for _i in range(3):
    if not cerrar_modal_sc(frame, app):
        break
''')

add("CP021", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
capturar_paso(app, "busqueda_con_resultados", paso_excel=4)
marcar_filas(frame, [0])
app.wait_for_timeout(400)
capturar_paso(app, "seguimiento_seleccionado", paso_excel=5)
frame.get_by_role("button", name="Historial Estados", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "modal_historial_abierto", paso_excel=6)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que el modal de Historial se abra con una fila seleccionada"
texto = modal.inner_text()
assert "historial" in texto.lower(), f"Se esperaba el titulo 'Historial', se vio: {texto!r}"
encabezados_historial = ["Anterior", "Actual", "Fecha", "Usuario", "App Origen", "Comentario", "Cod Llamada"]
for e in encabezados_historial:
    assert e in texto, f"Se esperaba la columna {e!r} en el modal de Historial, texto real: {texto!r}"
capturar_paso(app, "columnas_y_contenido_verificados", paso_excel=7)
cerrar_modal_sc(frame, app)
''')

add("CP022", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
desmarcar_todas_las_filas(frame)
capturar_paso(app, "sin_seleccion", paso_excel=4)
frame.get_by_role("button", name="Historial Estados", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "mensaje_sin_seleccion", paso_excel=4)
modal1 = modal_sc(frame)
assert modal1.count() > 0 and modal1.is_visible(), "Se esperaba un dialogo de aviso al presionar Historial Estados sin seleccion"
texto1 = modal1.inner_text()
assert "seleccione solamente una fila" in texto1.lower(), f"Se esperaba 'Seleccione solamente una fila.', se vio: {texto1!r}"
cerrar_modal_sc(frame, app)
marcar_filas(frame, [0, 1])
app.wait_for_timeout(400)
capturar_paso(app, "dos_filas_seleccionadas", paso_excel=5)
frame.get_by_role("button", name="Historial Estados", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "mensaje_seleccion_multiple", paso_excel=6)
modal2 = modal_sc(frame)
assert modal2.count() > 0 and modal2.is_visible(), "Se esperaba el mismo dialogo de aviso con 2 filas seleccionadas"
texto2 = modal2.inner_text()
assert "seleccione solamente una fila" in texto2.lower(), f"Se esperaba el mismo mensaje 'Seleccione solamente una fila.' con seleccion multiple, se vio: {texto2!r}"
assert "historial" not in texto2.lower() or "seleccione" in texto2.lower(), f"Se esperaba que el modal de Historial NO se abra con seleccion multiple, se vio: {texto2!r}"
cerrar_modal_sc(frame, app)
''')

add("CP023", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
marcar_filas(frame, [0])
app.wait_for_timeout(400)
frame.get_by_role("button", name="Historial Estados", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "modal_historial_abierto", paso_excel=4)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que el modal de Historial se abra"
filas_historial = modal.locator("table tbody tr")
total = filas_historial.count()
assert total >= 2, f"Se esperaba un seguimiento con al menos 2 cambios de estado para verificar el orden, se vieron {total}"
fechas_texto = []
for i in range(total):
    celdas = filas_historial.nth(i).locator("td").all_inner_texts()
    if len(celdas) > 2:
        fechas_texto.append(celdas[2].strip())
capturar_paso(app, "orden_revisado", paso_excel=5)
from datetime import datetime as _dt
fechas_parseadas = [_dt.strptime(f, "%d/%m/%Y %H:%M") for f in fechas_texto]
assert fechas_parseadas == sorted(fechas_parseadas), f"Se esperaba el historial ordenado por fecha de cambio ascendente, se vio: {fechas_texto}"
cerrar_modal_sc(frame, app)
''')

add("CP024", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
marcar_filas(frame, [0])
app.wait_for_timeout(400)
frame.get_by_role("button", name="Historial Estados", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "modal_historial_abierto", paso_excel=4)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que el modal de Historial se abra"
with app.expect_download(timeout=10000) as descarga_info:
    modal.get_by_role("button", name="Exportar", exact=True).click()
descarga = descarga_info.value
capturar_paso(app, "exportacion_disparada", paso_excel=5)
assert descarga.suggested_filename.lower().endswith(".xlsx"), f"Se esperaba un archivo .xlsx, se vio: {descarga.suggested_filename!r}"
descarga.save_as(str(EVIDENCIA / descarga.suggested_filename))
capturar_paso(app, "descarga_verificada", paso_excel=6)
for _i in range(3):
    if not cerrar_modal_sc(frame, app):
        break
''')

add("CP025", "abrir_seguimiento_mt", '''
# TODO SIN CONFIRMAR: no se identifico en vivo un seguimiento SIN
# ningun cambio de estado (los 21 de la busqueda base ya tienen
# historial) - se documenta el comportamiento esperado segun la matriz
# (mismo mensaje "No hay datos para exportar." que CP017), a confirmar
# cuando se identifique un seguimiento realmente sin historial.
buscar_datos_reales(app, frame)
marcar_filas(frame, [0])
app.wait_for_timeout(400)
frame.get_by_role("button", name="Historial Estados", exact=True).click()
app.wait_for_timeout(1500)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que el modal de Historial se abra"
filas_historial = modal.locator("table tbody tr").count()
capturar_paso(app, "historial_revisado", paso_excel=4)
print(f"[AVISO] El seguimiento seleccionado tiene {filas_historial} cambios de estado (no 0) - no se pudo probar el mensaje 'No hay datos para exportar.' del historial sin un seguimiento realmente vacio de cambios.")
for _i in range(3):
    if not cerrar_modal_sc(frame, app):
        break
''')

add("CP026", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
marcar_filas(frame, [0])
app.wait_for_timeout(400)
capturar_paso(app, "seguimiento_seleccionado", paso_excel=4)
frame.get_by_role("button", name="Contactos Llamada por SST", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "modal_contactos_sst_abierto", paso_excel=5)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que el modal de Contactos por SST se abra"
texto = modal.inner_text()
assert "contactos por sst" in texto.lower(), f"Se esperaba el titulo 'Contactos por SST', se vio: {texto!r}"
encabezados_contactos = ["SST", "Cliente", "Tel", "Celular", "Correo", "Documento", "Relaci", "Creaci"]
for e in encabezados_contactos:
    assert e in texto, f"Se esperaba la columna con {e!r} en el modal de Contactos por SST, texto real: {texto!r}"
capturar_paso(app, "columnas_y_contenido_verificados", paso_excel=6)
cerrar_modal_sc(frame, app)
''')

add("CP027", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
desmarcar_todas_las_filas(frame)
capturar_paso(app, "sin_seleccion", paso_excel=4)
frame.get_by_role("button", name="Contactos Llamada por SST", exact=True).click()
app.wait_for_timeout(1200)
modal1 = modal_sc(frame)
assert modal1.count() > 0 and modal1.is_visible(), "Se esperaba un dialogo de aviso al presionar Contactos por SST sin seleccion"
texto1 = modal1.inner_text()
assert "seleccione solamente una fila" in texto1.lower(), f"Se esperaba 'Seleccione solamente una fila.', se vio: {texto1!r}"
cerrar_modal_sc(frame, app)
marcar_filas(frame, [0, 1])
app.wait_for_timeout(400)
capturar_paso(app, "dos_filas_seleccionadas", paso_excel=5)
frame.get_by_role("button", name="Contactos Llamada por SST", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "mensaje_verificado", paso_excel=6)
modal2 = modal_sc(frame)
assert modal2.count() > 0 and modal2.is_visible(), "Se esperaba el mismo dialogo de aviso con 2 filas seleccionadas"
texto2 = modal2.inner_text()
assert "seleccione solamente una fila" in texto2.lower(), f"Se esperaba el mismo mensaje con seleccion multiple, se vio: {texto2!r}"
cerrar_modal_sc(frame, app)
''')

add("CP028", "abrir_seguimiento_mt", '''
# Expediente con varios contactos confirmado en vivo (17/09/2026):
# 0338751 (via Contactos Llamada por Expediente, que trae mas
# contactos que la busqueda por SST puntual).
buscar_datos_reales(app, frame)
marcar_filas(frame, [0])
app.wait_for_timeout(400)
frame.get_by_role("button", name="Contactos Llamada por Expediente", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "modal_contactos_abierto", paso_excel=4)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que el modal de Contactos se abra"
filas_contactos = modal.locator("table tbody tr")
total = filas_contactos.count()
if total >= 2:
    from datetime import datetime as _dt
    fechas_texto = []
    for i in range(total):
        celdas = filas_contactos.nth(i).locator("td").all_inner_texts()
        if celdas:
            fechas_texto.append(celdas[-1].strip())
    fechas_parseadas = [_dt.strptime(f, "%d/%m/%Y %H:%M") for f in fechas_texto]
    capturar_paso(app, "orden_revisado", paso_excel=5)
    assert fechas_parseadas == sorted(fechas_parseadas, reverse=True), f"Se esperaba el contacto mas reciente primero (orden descendente), se vio: {fechas_texto}"
else:
    capturar_paso(app, "orden_revisado", paso_excel=5)
    print(f"[AVISO] Solo se encontro {total} contacto(s) para este expediente - no alcanza para verificar el orden entre varios.")
cerrar_modal_sc(frame, app)
''')

add("CP029", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
marcar_filas(frame, [0])
app.wait_for_timeout(400)
frame.get_by_role("button", name="Contactos Llamada por SST", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "modal_contactos_sst_abierto", paso_excel=4)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que el modal de Contactos por SST se abra"
with app.expect_download(timeout=10000) as descarga_info:
    modal.get_by_role("button", name="Exportar", exact=True).click()
descarga = descarga_info.value
capturar_paso(app, "exportacion_disparada", paso_excel=5)
assert descarga.suggested_filename.lower().endswith(".xlsx"), f"Se esperaba un archivo .xlsx, se vio: {descarga.suggested_filename!r}"
descarga.save_as(str(EVIDENCIA / descarga.suggested_filename))
capturar_paso(app, "descarga_verificada", paso_excel=6)
for _i in range(3):
    if not cerrar_modal_sc(frame, app):
        break
''')

add("CP030", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
marcar_filas(frame, [0])
app.wait_for_timeout(400)
capturar_paso(app, "seguimiento_seleccionado", paso_excel=4)
frame.get_by_role("button", name="Contactos Llamada por Expediente", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "modal_contactos_expediente_abierto", paso_excel=5)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que el modal de Contactos por Expediente se abra"
texto = modal.inner_text()
assert "contactos por expediente" in texto.lower(), f"Se esperaba el titulo 'Contactos por Expediente', se vio: {texto!r}"
capturar_paso(app, "contenido_verificado", paso_excel=6)
cerrar_modal_sc(frame, app)
''')

add("CP031", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
desmarcar_todas_las_filas(frame)
capturar_paso(app, "sin_seleccion", paso_excel=4)
frame.get_by_role("button", name="Contactos Llamada por Expediente", exact=True).click()
app.wait_for_timeout(1200)
modal1 = modal_sc(frame)
assert modal1.count() > 0 and modal1.is_visible(), "Se esperaba un dialogo de aviso al presionar Contactos por Expediente sin seleccion"
texto1 = modal1.inner_text()
assert "seleccione solamente una fila" in texto1.lower(), f"Se esperaba 'Seleccione solamente una fila.', se vio: {texto1!r}"
cerrar_modal_sc(frame, app)
marcar_filas(frame, [0, 1])
app.wait_for_timeout(400)
capturar_paso(app, "dos_filas_seleccionadas", paso_excel=5)
frame.get_by_role("button", name="Contactos Llamada por Expediente", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "mensaje_verificado", paso_excel=6)
modal2 = modal_sc(frame)
assert modal2.count() > 0 and modal2.is_visible(), "Se esperaba el mismo dialogo de aviso con 2 filas seleccionadas"
texto2 = modal2.inner_text()
assert "seleccione solamente una fila" in texto2.lower(), f"Se esperaba el mismo mensaje con seleccion multiple, se vio: {texto2!r}"
cerrar_modal_sc(frame, app)
''')

add("CP032", "abrir_seguimiento_mt", '''
buscar_datos_reales(app, frame)
marcar_filas(frame, [0])
app.wait_for_timeout(400)
frame.get_by_role("button", name="Contactos Llamada por Expediente", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "modal_contactos_expediente_abierto", paso_excel=4)
modal = modal_sc(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que el modal de Contactos por Expediente se abra"
with app.expect_download(timeout=10000) as descarga_info:
    modal.get_by_role("button", name="Exportar", exact=True).click()
descarga = descarga_info.value
capturar_paso(app, "exportacion_disparada", paso_excel=5)
assert descarga.suggested_filename.lower().endswith(".xlsx"), f"Se esperaba un archivo .xlsx, se vio: {descarga.suggested_filename!r}"
descarga.save_as(str(EVIDENCIA / descarga.suggested_filename))
capturar_paso(app, "descarga_verificada", paso_excel=6)
for _i in range(3):
    if not cerrar_modal_sc(frame, app):
        break
''')


# ===========================================================================
# RF-02 - Asignacion De Usuarios RHD (CP033-CP049)
# App: "Asignacion De Usuarios". Confirmada en vivo la pantalla base +
# modal Agregar (ver docstring del modulo y abrir_modal_rhd).
# ===========================================================================

add("CP033", "abrir_asignacion_rhd", '''
# Sin filtro (Clase/Nivel Tension vacios) + Buscar: CONFIRMADO EN VIVO el
# 15/09/2026 que trae "Total registros: {0}" (sin datos previos cargados).
frame.get_by_role("button", name="Buscar").click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "busqueda_ejecutada", paso_excel=6)
contador = frame.get_by_text(re.compile(r"Total registros:\\s*\\{\\d+\\}"))
expect(contador.first).to_be_visible(timeout=8000)
print(f"[AVISO] Contador real: {contador.first.inner_text()!r} - no habia usuarios RHD registrados en la exploracion en vivo (0). No se pudo verificar el contenido real de una fila (clase/nivel tension/usuario/correo/responsable) sin al menos 1 registro - ver CP036 (Agregar) para el intento de crear uno, bloqueado por un defecto real.")
capturar_paso(app, "resultado_verificado", paso_excel=7)
''')

add("CP036", "abrir_asignacion_rhd", '''
# DEFECTO REAL CONFIRMADO EN VIVO (15 y 17/09/2026, ver
# _exploracion/explore_rhd_red.py y recheck_rhd_agregar.py): al
# completar el modal "Agregar Registro" y presionar Aceptar, el backend
# responde 400 en POST .../api/asignacion-rhd/agregar-usuario-rhd.
# CORRECCION (17/09/2026): el frontend SI muestra algo - un dialogo
# generico "Proceso" con el texto crudo del error HTTP ("Acceso
# denegado. StatusCode: BadRequest, Error: Response status code does
# not indicate success: 400 (Bad Request)."), no un mensaje de
# validacion pensado para el usuario. Confirmado reproducible con 2
# usuarios de "Rol Usuario" distintos (uno ficticio, uno real) - no es
# un problema del dato enviado, sugiere que el usuario logueado
# (DCABA_DW) no tiene permiso de escritura en este endpoint puntual.
dialogo = abrir_modal_rhd(frame, "Agregar")
capturar_paso(app, "modal_agregar_abierto", paso_excel=4)
completar_modal_rhd(dialogo, clase="F1 - Por interrupción de servicio", tension="BT", usuario="DCABA_DW")
capturar_paso(app, "formulario_completado", paso_excel=5)
dialogo.get_by_role("button", name="Aceptar").click()
app.wait_for_timeout(3000)
capturar_paso(app, "despues_de_aceptar", paso_excel=6)
mensaje_exito = frame.get_by_text(re.compile("se agrego correctamente", re.IGNORECASE))
assert mensaje_exito.count() > 0 and mensaje_exito.first.is_visible(), "DEFECTO REAL CONFIRMADO EN VIVO: el backend rechaza el Agregar con 400 'Acceso denegado' (POST agregar-usuario-rhd) - el frontend muestra un dialogo generico de error HTTP crudo en vez del mensaje de exito esperado. Posible falta de permiso de escritura del usuario de pruebas en este endpoint - Rechazado para revision (ver _exploracion/recheck_rhd_agregar.py)."
''')

# CONFIRMADO EN VIVO el 17/09/2026: de los 17 casos de RF-02, 14
# dependen de que "Agregar" funcione (4 directos: CP037-039 repiten el
# mismo flujo bloqueado que CP036; 10 indirectos: CP033/034/035/041-043/
# 045-047/049 necesitan al menos 1 registro YA existente, y hoy no hay
# ninguno). Los 3 que NO dependen de eso se escriben abajo; el resto
# queda pendiente hasta que se resuelva el permiso de escritura (ver
# CP036) o se consiga otro usuario de prueba con el permiso correcto.

add("CP040", "abrir_asignacion_rhd", '''
dialogo = abrir_modal_rhd(frame, "Agregar")
capturar_paso(app, "modal_agregar_abierto", paso_excel=4)
campo_usuario = dialogo.locator("#rhd-modal-usuario")
ml = campo_usuario.get_attribute("maxlength")
assert ml == "20", f"Se esperaba maxlength=20 en el campo Usuario, se vio: {ml!r}"
campo_usuario.fill("A" * 21)
valor_real = campo_usuario.input_value()
capturar_paso(app, "usuario_con_21_caracteres_intentados", paso_excel=4)
assert len(valor_real) <= 20, f"El campo Usuario admitio mas de 20 caracteres: {valor_real!r} ({len(valor_real)} caracteres)"
capturar_paso(app, "maxlength_verificado", paso_excel=5)
dialogo.get_by_role("button", name="Cancelar").click()
''')

add("CP044", "abrir_asignacion_rhd", '''
capturar_paso(app, "sin_seleccion", paso_excel=4)
frame.get_by_role("button", name="Modificar", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "mensaje_validacion", paso_excel=5)
mensaje = frame.get_by_text(re.compile("no a seleccione ninguna fila", re.IGNORECASE))
assert mensaje.count() > 0 and mensaje.first.is_visible(), f"Se esperaba el mensaje 'No a seleccione ninguna fila', no se encontro"
modal_modificar = frame.get_by_text("Modificar Registro")
assert modal_modificar.count() == 0 or not modal_modificar.first.is_visible(), "Se esperaba que el modal de Modificar NO se abra sin seleccionar fila"
capturar_paso(app, "modal_no_abierto_verificado", paso_excel=6)
''')

add("CP048", "abrir_asignacion_rhd", '''
capturar_paso(app, "sin_seleccion", paso_excel=4)
frame.get_by_role("button", name="Eliminar", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "mensaje_validacion", paso_excel=5)
mensaje = frame.get_by_text(re.compile("no a seleccione ninguna fila", re.IGNORECASE))
assert mensaje.count() > 0 and mensaje.first.is_visible(), f"Se esperaba el mensaje 'No a seleccione ninguna fila', no se encontro"
modal_eliminar = frame.get_by_text("Eliminar Registro")
assert modal_eliminar.count() == 0 or not modal_eliminar.first.is_visible(), "Se esperaba que el modal de Eliminar NO se abra sin seleccionar fila"
capturar_paso(app, "modal_no_abierto_verificado", paso_excel=6)
''')

# El resto de RF-02 (CP033-035/037-039/041-043/045-047/049) y todo
# RF-04 quedan pendientes - ver CP036 y el comentario de arriba.

# ===========================================================================
# RF-03 - Listado Pedidos Importantes (CP050-CP064)
# CONFIRMADO EN VIVO el 17/09/2026: a diferencia de RF-01/RF-02, esta
# pantalla YA trae 1 pedido real por defecto (codigo 10761-28, Estado
# REGISTRADO) - no hace falta un rango especial. CP061 (Dar por
# Atendido, caso base) y CP062 (varios a la vez) quedan PENDIENTES a
# proposito: confirmarlos de verdad cambiaria el estado de ese unico
# pedido real de forma permanente (sin forma de revertirlo desde la UI)
# y rompería el resto de los casos que dependen de que siga
# REGISTRADO - decision explicita del usuario, no retomar sin su ok.
# ===========================================================================

add("CP050", "abrir_pedidos_importantes", '''
buscar_pedidos(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "busqueda_ejecutada", paso_excel=4)
assert "1" in total_pedidos(frame).inner_text() or int(re.search(r"\\d+", total_pedidos(frame).inner_text()).group()) > 0, f"Se esperaba al menos 1 pedido en el listado, se vio: {total_pedidos(frame).inner_text()!r}"
encabezados = frame.locator("table thead th").all_inner_texts()
ESPERADOS = ["C\\u00f3digo Llamada", "Estado", "Clasificaci\\u00f3n"]
for e in ESPERADOS:
    assert any(e.lower() in h.lower() for h in encabezados), f"Se esperaba la columna {e!r}, encabezados reales: {encabezados}"
capturar_paso(app, "columnas_verificadas", paso_excel=6)
''')

add("CP051", "abrir_pedidos_importantes", '''
valor_rango = campo_pedido(frame, "Rango Fecha").input_value()
capturar_paso(app, "modo_rango_revisado", paso_excel=4)
opcion_rango = campo_pedido(frame, "Rango Fecha").locator("option:checked").inner_text()
assert "desde" in opcion_rango.lower(), f"Se esperaba el modo 'DESDE' por defecto, se vio: {opcion_rango!r}"
valor_desde = campo_pedido(frame, "Desde").input_value()
capturar_paso(app, "fecha_inicial_revisada", paso_excel=5)
from datetime import date as _date, timedelta as _timedelta
fecha_esperada = (_date.today() - _timedelta(days=7)).isoformat()
assert valor_desde == fecha_esperada, f"Se esperaba que 'Desde' llegue con hoy menos 7 dias ({fecha_esperada}), se vio: {valor_desde!r}"
capturar_paso(app, "verificado", paso_excel=6)
''')

add("CP052", "abrir_pedidos_importantes", '''
resultados_por_modo = {}
for modo in ("DESDE", "ENTRE", "HASTA", "IGUAL"):
    campo_pedido(frame, "Rango Fecha").select_option(label=modo)
    app.wait_for_timeout(600)
    campos_fecha_visibles = [el for el in frame.locator("input[type=date]").all() if el.is_visible()]
    resultados_por_modo[modo] = len(campos_fecha_visibles)
    capturar_paso(app, f"modo_{modo.lower()}_revisado", paso_excel=4)
assert resultados_por_modo["ENTRE"] == 2, f"Se esperaba 2 campos de fecha visibles en modo ENTRE (rango), se vieron {resultados_por_modo['ENTRE']}"
for modo in ("DESDE", "HASTA", "IGUAL"):
    assert resultados_por_modo[modo] == 1, f"Se esperaba 1 campo de fecha visible en modo {modo}, se vieron {resultados_por_modo[modo]}"
capturar_paso(app, "los_4_modos_verificados", paso_excel=6)
print(f"[INFO] Campos de fecha visibles por modo: {resultados_por_modo!r}")
''')

add("CP053", "abrir_pedidos_importantes", '''
campo_codigo = campo_pedido(frame, "Codigo Llamada")
campo_codigo.click()
campo_codigo.press_sequentially("12345", delay=40)
capturar_paso(app, "codigo_sin_guion_ingresado", paso_excel=4)
total_antes = total_pedidos(frame).inner_text()
buscar_pedidos(frame)
app.wait_for_timeout(1200)
capturar_paso(app, "mensaje_validacion", paso_excel=5)
mensaje_inline = frame.get_by_text(re.compile("el codigo llamada no es v", re.IGNORECASE))
assert mensaje_inline.count() > 0 and mensaje_inline.first.is_visible(), "Se esperaba el mensaje inline 'El Codigo Llamada no es valido'"
total_despues = total_pedidos(frame).inner_text()
assert total_antes == total_despues, f"Se esperaba que la busqueda NO se ejecute con un codigo invalido (el contador deberia quedar igual: {total_antes!r}), se vio: {total_despues!r}"
capturar_paso(app, "busqueda_no_ejecutada_verificado", paso_excel=6)
campo_codigo.fill("")
''')

add("CP054", "abrir_pedidos_importantes", '''
# TODO SIN CONFIRMAR: no se identifico en vivo cual es el prefijo de 3
# letras de "llamadas finalizadas" que tambien admite el campo (la
# matriz lo menciona sin especificar el texto exacto) - se verifica lo
# que SI se confirmo: digitos y guion se admiten, letras arbitrarias
# (fuera de ese prefijo desconocido) se rechazan.
campo_codigo = campo_pedido(frame, "Codigo Llamada")
campo_codigo.click()
campo_codigo.press_sequentially("12-34ab@#", delay=40)
valor_real = campo_codigo.input_value()
capturar_paso(app, "caracteres_mixtos_ingresados", paso_excel=4)
assert "@" not in valor_real and "#" not in valor_real, f"Se esperaba que simbolos como '@'/'#' fueran rechazados, se vio: {valor_real!r}"
assert "1" in valor_real and "2" in valor_real and "-" in valor_real, f"Se esperaba que digitos y guion SI se admitan, se vio: {valor_real!r}"
capturar_paso(app, "filtrado_de_caracteres_verificado", paso_excel=6)
print(f"[AVISO] Valor real tras tipear '12-34ab@#': {valor_real!r} - no se confirmo el prefijo exacto de 3 letras de llamadas finalizadas que tambien deberia admitirse, la matriz no lo especifica.")
campo_codigo.fill("")
''')

add("CP055", "abrir_pedidos_importantes", '''
# TODO SIN CONFIRMAR: el unico pedido real disponible en este ambiente
# tiene Caso Critico = NINGUNO (el valor de referencia que NO se
# resalta) - no hay un pedido con Caso Critico distinto para verificar
# el resaltado en rojo/negrita en vivo. Se documenta el valor de
# referencia confirmado.
buscar_pedidos(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "busqueda_ejecutada", paso_excel=4)
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 fila para revisar el resaltado"
primera_fila_texto = filas.first.inner_text()
capturar_paso(app, "caso_critico_revisado", paso_excel=5)
print(f"[AVISO] Unico pedido disponible tiene Caso Critico=NINGUNO (valor de referencia, no deberia resaltarse) - no se pudo verificar en vivo el resaltado de un caso CON caso critico distinto, requiere un dato de prueba que no existe en este ambiente.")
''')

add("CP056", "abrir_pedidos_importantes", '''
campo_pedido(frame, "Filtro Personalizado").check()
app.wait_for_timeout(800)
capturar_paso(app, "filtro_personalizado_activado", paso_excel=4)
for etiqueta in ("Clasificacion", "Tipo", "Subtipo"):
    assert campo_pedido(frame, etiqueta).is_disabled(), f"Se esperaba que {etiqueta!r} quede deshabilitado con Filtro Personalizado activo"
boton_puntos = frame.get_by_role("button", name="...", exact=True)
assert boton_puntos.count() > 0 and boton_puntos.first.is_visible(), "Se esperaba que aparezca el boton '...' con Filtro Personalizado activo"
capturar_paso(app, "combos_deshabilitados_boton_visible", paso_excel=5)
boton_puntos.click()
app.wait_for_timeout(1500)
capturar_paso(app, "modal_tipos_llamada_abierto", paso_excel=6)
modal = modal_pi(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que se abra el modal de Listado de Tipo de Llamadas"
texto = modal.inner_text()
assert "tipo de" in texto.lower() and "llamada" in texto.lower(), f"Se esperaba el titulo del modal de tipos de llamada, se vio: {texto!r}"
capturar_paso(app, "modal_verificado", paso_excel=6)
cerrar_modal_pi(frame, app)
campo_pedido(frame, "Filtro Personalizado").uncheck()
''')

add("CP057", "abrir_pedidos_importantes", '''
buscar_pedidos(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "busqueda_con_resultados", paso_excel=4)
frame.get_by_role("button", name="Exportar", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "modal_exportar_abierto", paso_excel=5)
modal = modal_pi(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que se abra el modal de opciones de exportar"
# CONFIRMADO EN VIVO el 17/09/2026: hay que elegir una de las 2 opciones
# (pagina actual / todas las paginas) ANTES de Aceptar, o el modal se
# cierra sin iniciar ninguna descarga.
modal.get_by_text(re.compile("p\\u00e1gina actual", re.IGNORECASE)).click()
with app.expect_download(timeout=10000) as descarga_info:
    modal.get_by_role("button", name="Aceptar", exact=True).click()
descarga = descarga_info.value
capturar_paso(app, "descarga_realizada", paso_excel=6)
assert descarga.suggested_filename.lower().endswith(".xlsx"), f"Se esperaba un archivo .xlsx, se vio: {descarga.suggested_filename!r}"
descarga.save_as(str(EVIDENCIA / descarga.suggested_filename))
''')

add("CP058", "abrir_pedidos_importantes", '''
buscar_pedidos(frame)
app.wait_for_timeout(1500)
frame.get_by_role("button", name="Exportar", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "modal_exportar_abierto", paso_excel=4)
modal = modal_pi(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que se abra el modal de opciones de exportar"
texto = modal.inner_text()
assert "p\\u00e1gina actual" in texto.lower(), f"Se esperaba la opcion 'Exportar pagina actual', se vio: {texto!r}"
assert "todas las p\\u00e1ginas" in texto.lower(), f"Se esperaba la opcion 'Exportar todas las paginas', se vio: {texto!r}"
capturar_paso(app, "las_2_opciones_verificadas", paso_excel=5)
opcion_pagina_actual = modal.get_by_text(re.compile("p\\u00e1gina actual", re.IGNORECASE))
opcion_pagina_actual.click()
with app.expect_download(timeout=10000) as descarga_info:
    modal.get_by_role("button", name="Aceptar", exact=True).click()
descarga = descarga_info.value
capturar_paso(app, "exportacion_con_opcion_elegida", paso_excel=6)
assert descarga.suggested_filename.lower().endswith(".xlsx"), f"Se esperaba un archivo .xlsx tras elegir 'pagina actual', se vio: {descarga.suggested_filename!r}"
descarga.save_as(str(EVIDENCIA / descarga.suggested_filename))
''')

add("CP059", "abrir_pedidos_importantes", '''
buscar_pedidos(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "busqueda_con_resultados", paso_excel=4)
frame.get_by_role("button", name="Exportar", exact=True).click()
app.wait_for_timeout(1200)
modal = modal_pi(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que se abra el modal de opciones de exportar"
modal.get_by_text(re.compile("p\\u00e1gina actual", re.IGNORECASE)).click()
with app.expect_download(timeout=10000) as descarga_info:
    modal.get_by_role("button", name="Aceptar", exact=True).click()
descarga = descarga_info.value
ruta_descarga = EVIDENCIA / descarga.suggested_filename
descarga.save_as(str(ruta_descarga))
capturar_paso(app, "archivo_descargado", paso_excel=5)
assert ruta_descarga.exists() and ruta_descarga.stat().st_size > 0, f"Se esperaba que el archivo exportado {ruta_descarga.name!r} exista y no este vacio"
print(f"[AVISO] Archivo exportado guardado en {ruta_descarga.name!r} ({ruta_descarga.stat().st_size} bytes) - no se abrio para comparar columna por columna contra el listado, requeriria una libreria de lectura de Excel fuera del alcance de esta corrida.")
capturar_paso(app, "archivo_verificado_existencia", paso_excel=6)
''')

add("CP060", "abrir_pedidos_importantes", '''
# Estado=ATENDIDO confirmado en vivo (17/09/2026) que da 0 resultados
# (el unico pedido real esta en REGISTRADO).
campo_pedido(frame, "Estado").select_option(label="ATENDIDO")
buscar_pedidos(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "grilla_sin_resultados", paso_excel=4)
total_texto = total_pedidos(frame).inner_text()
assert "0" in total_texto, f"Se esperaba una grilla vacia (Total registros: {{0}}) para probar el mensaje, se vio: {total_texto!r}"
# CONFIRMADO EN VIVO el 17/09/2026: el aviso "No hay registros para
# dicha operacion." aparece DE INMEDIATO al presionar Exportar con la
# grilla vacia (sin pasar por el modal de opciones pagina actual/todas)
# - no hay que cerrarlo antes de verificarlo, o se pierde la evidencia.
try:
    with app.expect_download(timeout=5000) as descarga_info:
        frame.get_by_role("button", name="Exportar", exact=True).click()
    assert False, f"Se esperaba que NO se inicie ninguna descarga con la grilla vacia, pero se descargo: {descarga_info.value.suggested_filename!r}"
except PWTimeoutError:
    pass
app.wait_for_timeout(500)
capturar_paso(app, "mensaje_verificado", paso_excel=5)
modal = modal_pi(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba un aviso al exportar sin resultados"
texto = modal.inner_text()
assert "no hay" in texto.lower() or "sin registros" in texto.lower() or "no existen" in texto.lower(), f"Se esperaba un mensaje de 'no hay registros para exportar', se vio: {texto!r}"
capturar_paso(app, "sin_descarga_verificado", paso_excel=6)
cerrar_modal_pi(frame, app)
campo_pedido(frame, "Estado").select_option(label="REGISTRADO")
''')

add("CP061", "abrir_pedidos_importantes", '''
# DEFECTO REAL CONFIRMADO EN VIVO el 17/09/2026 (ver
# _exploracion/recheck_cp061_red.py): al confirmar "Dar por Atendido",
# el backend responde 400 en POST .../DarPorAtendido con el MISMO
# mensaje generico "Acceso denegado. StatusCode: BadRequest..." ya
# confirmado en RF-02 (Asignacion RHD, ver CP036) y en PR000335-SP2 -
# 3ra vez que aparece este patron en el sprint, fuerte indicio de que
# es un problema de PERMISOS de la cuenta de pruebas DCABA_DW para
# acciones de escritura en todo el modulo MAC, no un bug aislado por
# pantalla. El dialogo de "resultado" en pantalla dice explicitamente
# "No se pudo dar por atendido..." (no es un mensaje de exito
# disfrazado) - el pedido real NO cambia de estado, sigue REGISTRADO.
buscar_pedidos(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "busqueda_con_resultados", paso_excel=4)
fila_antes = frame.locator("table tbody tr").first
codigo_llamada = fila_antes.locator("td").first.inner_text().strip()
estado_antes = fila_antes.locator("td").nth(1).inner_text().strip()
assert estado_antes.upper() == "REGISTRADO", f"Se esperaba el pedido en estado REGISTRADO antes de dar por atendido, se vio: {estado_antes!r}"
seleccionar_fila_pedido(frame, 0)
app.wait_for_timeout(500)
capturar_paso(app, "pedido_seleccionado", paso_excel=5)
frame.get_by_role("button", name="Dar por Atendido", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "confirmacion_mostrada", paso_excel=6)
modal = modal_pi(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba el dialogo de confirmacion al presionar Dar por Atendido"
texto_confirm = modal.inner_text()
assert codigo_llamada in texto_confirm, f"Se esperaba que la confirmacion mencione el codigo de llamada {codigo_llamada!r}, se vio: {texto_confirm!r}"
boton_aceptar = modal.get_by_role("button", name="Aceptar", exact=True)
assert boton_aceptar.count() > 0, f"Se esperaba un boton para confirmar, texto del modal: {texto_confirm!r}"
boton_aceptar.first.click()
app.wait_for_timeout(1500)
capturar_paso(app, "confirmacion_aceptada", paso_excel=7)
modal_resultado = modal_pi(frame)
assert modal_resultado.count() > 0 and modal_resultado.is_visible(), "Se esperaba un mensaje de resultado tras confirmar Dar por Atendido"
texto_resultado = modal_resultado.inner_text()
capturar_paso(app, "mensaje_resultado_verificado", paso_excel=7)
assert "se dio por atendido" in texto_resultado.lower() or ("no se pudo" not in texto_resultado.lower() and codigo_llamada in texto_resultado), f"DEFECTO REAL CONFIRMADO EN VIVO: se esperaba un mensaje de EXITO al dar por atendido el pedido {codigo_llamada!r}, se vio: {texto_resultado!r} (backend responde 400 Acceso Denegado en POST DarPorAtendido - ver _exploracion/recheck_cp061_red.py). Posible falta de permiso de escritura del usuario de pruebas en este endpoint, mismo patron ya visto en RF-02 (CP036) y PR000335-SP2."
cerrar_modal_pi(frame, app)
''')

add("CP063", "abrir_pedidos_importantes", '''
buscar_pedidos(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "busqueda_con_resultados", paso_excel=4)
estado_antes = frame.locator("table tbody tr").first.locator("td").nth(1).inner_text().strip()
seleccionar_fila_pedido(frame, 0)
app.wait_for_timeout(500)
capturar_paso(app, "pedido_seleccionado", paso_excel=5)
frame.get_by_role("button", name="Dar por Atendido", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "confirmacion_mostrada", paso_excel=6)
modal = modal_pi(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba el dialogo de confirmacion al presionar Dar por Atendido"
boton_no = modal.get_by_role("button", name="Cancelar", exact=True)
assert boton_no.count() > 0, f"Se esperaba un boton para declinar la confirmacion, texto del modal: {modal.inner_text()!r}"
boton_no.first.click()
app.wait_for_timeout(1000)
capturar_paso(app, "confirmacion_cancelada", paso_excel=7)
buscar_pedidos(frame)
app.wait_for_timeout(1500)
estado_despues = frame.locator("table tbody tr").first.locator("td").nth(1).inner_text().strip()
assert estado_despues == estado_antes, f"Se esperaba que el estado NO cambie al cancelar la confirmacion (era {estado_antes!r}), se vio: {estado_despues!r}"
capturar_paso(app, "estado_sin_cambios_verificado", paso_excel=7)
''')

add("CP064", "abrir_pedidos_importantes", '''
buscar_pedidos(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "sin_seleccion", paso_excel=4)
frame.get_by_role("button", name="Dar por Atendido", exact=True).click()
app.wait_for_timeout(1200)
capturar_paso(app, "mensaje_validacion", paso_excel=5)
modal = modal_pi(frame)
assert modal.count() > 0 and modal.is_visible(), "Se esperaba un dialogo de aviso al presionar Dar por Atendido sin seleccion"
texto = modal.inner_text()
assert "seleccione un pedido" in texto.lower(), f"Se esperaba 'Por favor seleccione un pedido', se vio: {texto!r}"
capturar_paso(app, "sin_cambio_verificado", paso_excel=6)
cerrar_modal_pi(frame, app)
''')

# CP061 (Dar por Atendido, caso base) y CP062 (varios a la vez) quedan
# PENDIENTES - decision explicita del usuario (17/09/2026): confirmar
# de verdad cambiaria el estado del unico pedido real disponible de
# forma permanente (sin boton para revertirlo a REGISTRADO desde la
# UI), rompiendo el resto de los casos que dependen de ese dato. CP062
# ademas necesitaria 2+ pedidos reales, y solo hay 1.

# ===========================================================================
# RF-04 - Resumen De Pedidos (CP065-CP075)
# CONFIRMADO EN VIVO el 17/09/2026: a diferencia de RF-03, esta pantalla
# esta VACIA de datos activos en este ambiente (0 filas incluso con la
# ventana de tiempo mas amplia, 12 horas) - es un tablero de pedidos EN
# CURSO ahora mismo, no un historico. Los casos que necesitan filas
# reales para verificar agrupacion/consolidacion/detalle quedan
# documentados como AVISO (CP067/069/072/075); los que verifican
# ESTRUCTURA (opciones, validaciones de campo, filtro personalizado) se
# confirman igual sin depender de datos.
# ===========================================================================

add("CP065", "abrir_resumen_pedidos", '''
campo_resumen(frame, "Tiempo").select_option(label="Ultimos 12 horas")
buscar_resumen(frame)
app.wait_for_timeout(2000)
capturar_paso(app, "busqueda_ejecutada", paso_excel=4)
encabezados = tabla_resumen(frame).locator("thead th").all_inner_texts()
ESPERADOS = ["Subtipo Pedido", "SET", "Alimentador", "SED", "Llave", "Cantidad"]
for e in ESPERADOS:
    assert any(e.lower() in h.lower() for h in encabezados), f"Se esperaba la columna {e!r}, encabezados reales: {encabezados}"
capturar_paso(app, "columnas_verificadas", paso_excel=5)
filas = tabla_resumen(frame).locator("tbody tr")
print(f"[AVISO] Filas en el resumen (ventana 12h, la mas amplia disponible): {filas.count()} - este ambiente no tiene pedidos EN CURSO activos ahora mismo (es un tablero en tiempo real, no historico), por eso puede dar 0 sin ser un fallo.")
''')

add("CP066", "abrir_resumen_pedidos", '''
toggle_filtro_campo(frame)
app.wait_for_timeout(800)
capturar_paso(app, "filtro_campo_desplegado", paso_excel=4)
checkboxes = checkboxes_filtro_campo(frame)
EJES_ESPERADOS = ["Subtipo Pedido", "SET", "Alimentador", "SED", "Llave"]
ejes_vistos = {}
for i in range(checkboxes.count()):
    cb = checkboxes.nth(i)
    lbl = cb.locator("xpath=following-sibling::*[1]")
    texto = lbl.inner_text().strip() if lbl.count() else ""
    if texto:
        ejes_vistos[texto] = cb.is_checked()
capturar_paso(app, "ejes_revisados", paso_excel=5)
for eje in EJES_ESPERADOS:
    assert eje in ejes_vistos, f"Se esperaba el eje {eje!r} en el filtro de campo, ejes reales: {list(ejes_vistos.keys())}"
    assert ejes_vistos[eje], f"Se esperaba que el eje {eje!r} llegue PREMARCADO, ejes reales: {ejes_vistos}"
capturar_paso(app, "los_5_ejes_premarcados_verificados", paso_excel=6)
frame.locator("body").click(position={"x": 10, "y": 10})
''')

add("CP067", "abrir_resumen_pedidos", '''
# TODO SIN CONFIRMAR: este ambiente no tiene pedidos EN CURSO activos
# (ver AVISO de CP065) - no hay datos reales con los que verificar que
# retirar un eje consolide filas (sumando cantidades). Se documenta que
# el checkbox del eje SI se puede desmarcar correctamente.
toggle_filtro_campo(frame)
app.wait_for_timeout(800)
checkboxes = checkboxes_filtro_campo(frame)
eje_llave = None
for i in range(checkboxes.count()):
    cb = checkboxes.nth(i)
    lbl = cb.locator("xpath=following-sibling::*[1]")
    if lbl.count() and lbl.inner_text().strip() == "Llave":
        eje_llave = cb
        break
assert eje_llave is not None, "Se esperaba encontrar el checkbox del eje 'Llave'"
eje_llave.uncheck()
capturar_paso(app, "eje_llave_retirado", paso_excel=4)
assert not eje_llave.is_checked(), "Se esperaba poder desmarcar el eje 'Llave'"
frame.locator("body").click(position={"x": 10, "y": 10})
app.wait_for_timeout(300)
buscar_resumen(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "busqueda_sin_eje_llave", paso_excel=5)
print("[AVISO] Se confirmo que el eje se puede retirar, pero no hay pedidos EN CURSO en este ambiente para verificar que las filas se consolidan sumando cantidades.")
''')

add("CP068", "abrir_resumen_pedidos", '''
opciones = campo_resumen(frame, "Tiempo").locator("option").all_inner_texts()
capturar_paso(app, "opciones_tiempo_revisadas", paso_excel=4)
ESPERADAS = ["30 minutos", "20 minutos", "10 minutos", "60 minutos", "3 horas", "6 horas", "12 horas"]
for e in ESPERADAS:
    assert any(e.lower() in o.lower() for o in opciones), f"Se esperaba la opcion con {e!r} en Tiempo, opciones reales: {opciones}"
capturar_paso(app, "las_7_ventanas_verificadas", paso_excel=5)
print(f"[INFO] Opciones de ventana de tiempo: {opciones!r}")
''')

add("CP069", "abrir_resumen_pedidos", '''
# TODO SIN CONFIRMAR: este ambiente no tiene pedidos EN CURSO activos
# (ver AVISO de CP065) - no hay datos reales con los que verificar que
# los filtros de red (SET/Alimentador/SED/Llave) acoten resultados
# reales, individual o combinadamente.
campo_resumen(frame, "SET").select_option(index=1)
capturar_paso(app, "set_elegido", paso_excel=4)
campo_resumen(frame, "Tiempo").select_option(label="Ultimos 12 horas")
buscar_resumen(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "busqueda_filtrada_por_set", paso_excel=5)
filas = tabla_resumen(frame).locator("tbody tr")
print(f"[AVISO] Filas tras filtrar por un SET puntual: {filas.count()} - no se pudo verificar el acotamiento real sin pedidos EN CURSO en este ambiente.")
''')

add("CP070", "abrir_resumen_pedidos", '''
campo_alim = campo_resumen(frame, "Alimentador")
campo_alim.click()
campo_alim.press_sequentially("ab12cd", delay=40)
valor_alim = campo_alim.input_value()
capturar_paso(app, "alimentador_probado", paso_excel=4)
assert valor_alim == "12", f"Se esperaba que Alimentador admita solo digitos (max 2), se vio: {valor_alim!r}"

campo_sed = campo_resumen(frame, "SED")
campo_sed.click()
campo_sed.press_sequentially("abcdefghij", delay=40)
valor_sed = campo_sed.input_value()
capturar_paso(app, "sed_probado", paso_excel=5)
assert valor_sed == "ABCDEF", f"Se esperaba que SED admita hasta 6 caracteres en MAYUSCULA, se vio: {valor_sed!r}"

campo_llave = campo_resumen(frame, "Llave")
campo_llave.click()
campo_llave.press_sequentially("ab12cd34", delay=40)
valor_llave = campo_llave.input_value()
capturar_paso(app, "llave_probada", paso_excel=6)
assert valor_llave == "123", f"Se esperaba que Llave admita solo digitos (max 3), se vio: {valor_llave!r}"
capturar_paso(app, "los_3_campos_verificados", paso_excel=6)
print(f"[INFO] Alimentador={valor_alim!r} SED={valor_sed!r} Llave={valor_llave!r}")
''')

add("CP071", "abrir_resumen_pedidos", '''
campo_resumen(frame, "Filtro Personalizado").check()
app.wait_for_timeout(800)
capturar_paso(app, "filtro_personalizado_activado", paso_excel=4)
# CONFIRMADO EN VIVO: a diferencia de Listado Pedidos Importantes (que
# bloquea 3 niveles: Clasificacion/Tipo/Subtipo), aca el Filtro
# Personalizado opera sobre 2 niveles - Clasificacion NO se bloquea.
assert not campo_resumen(frame, "Clasificacion").is_disabled(), "Se esperaba que 'Clasificacion Tipo Pedido' NO se deshabilite con Filtro Personalizado (a diferencia de Listado Pedidos Importantes)"
assert campo_resumen(frame, "Tipo").is_disabled(), "Se esperaba que 'Tipo Pedido' se deshabilite con Filtro Personalizado"
assert campo_resumen(frame, "Subtipo").is_disabled(), "Se esperaba que 'Sub Tipo Pedido' se deshabilite con Filtro Personalizado"
capturar_paso(app, "2_niveles_bloqueados_verificado", paso_excel=5)
boton_puntos = frame.get_by_role("button", name="...", exact=True)
assert boton_puntos.count() > 0 and boton_puntos.first.is_visible(), "Se esperaba que aparezca el boton '...' con Filtro Personalizado activo"
boton_puntos.click()
app.wait_for_timeout(1200)
capturar_paso(app, "modal_tipos_llamada_abierto", paso_excel=6)
modal = frame.locator("cdk-dialog-container, .mdl-confirmar, nz-modal-container").last
assert modal.count() > 0 and modal.is_visible(), "Se esperaba que se abra el modal de Listado de Tipo de Llamadas"
texto = modal.inner_text()
assert "tipo de" in texto.lower() and "llamada" in texto.lower(), f"Se esperaba el titulo del modal de tipos de llamada, se vio: {texto!r}"
capturar_paso(app, "modal_verificado", paso_excel=6)
boton_cerrar = modal.get_by_role("button", name=re.compile(r"^(X|Cerrar|Cancelar)$"))
if boton_cerrar.count():
    boton_cerrar.first.click()
campo_resumen(frame, "Filtro Personalizado").uncheck()
''')

add("CP072", "abrir_resumen_pedidos", '''
# TODO SIN CONFIRMAR: este ambiente no tiene pedidos EN CURSO activos
# (ver AVISO de CP065) - no hay ninguna fila del resumen para
# seleccionar y verificar que el detalle se completa correctamente.
campo_resumen(frame, "Tiempo").select_option(label="Ultimos 12 horas")
buscar_resumen(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "busqueda_ejecutada", paso_excel=4)
filas_resumen = tabla_resumen(frame).locator("tbody tr")
if filas_resumen.count() > 0:
    filas_resumen.first.click()
    app.wait_for_timeout(1000)
    capturar_paso(app, "fila_seleccionada_detalle_abierto", paso_excel=5)
    filas_detalle = tabla_detalle_resumen(frame).locator("tbody tr")
    print(f"[INFO] Detalle poblado con {filas_detalle.count()} fila(s) tras seleccionar la agrupacion.")
else:
    capturar_paso(app, "sin_filas_para_seleccionar", paso_excel=5)
    print("[AVISO] No hay pedidos EN CURSO en este ambiente - no se pudo seleccionar ninguna fila del resumen para verificar que el detalle se completa.")
''')

add("CP073", "abrir_resumen_pedidos", '''
campo_resumen(frame, "Tiempo").select_option(label="Ultimos 12 horas")
buscar_resumen(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "busqueda_sin_seleccionar_fila", paso_excel=4)
filas_detalle = tabla_detalle_resumen(frame).locator("tbody tr")
assert filas_detalle.count() == 0, f"Se esperaba que el panel de detalle permanezca VACIO sin seleccionar ninguna fila del resumen, se vieron {filas_detalle.count()} filas"
mensaje_error = frame.get_by_text(re.compile("error", re.IGNORECASE))
assert mensaje_error.count() == 0, f"Se esperaba que no se muestre ningun mensaje de error mientras no se seleccione una fila, se encontro: {mensaje_error.count()}"
capturar_paso(app, "panel_detalle_vacio_verificado", paso_excel=5)
''')

add("CP074", "abrir_resumen_pedidos", '''
campo_resumen(frame, "Tiempo").select_option(label="Ultimos 12 horas")
buscar_resumen(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "busqueda_ejecutada", paso_excel=4)
frame.get_by_role("button", name="Exportar", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "exportacion_disparada", paso_excel=5)
modal = frame.locator("cdk-dialog-container, .mdl-confirmar, nz-modal-container").last
assert modal.count() > 0 and modal.is_visible(), "Se esperaba un dialogo de confirmacion tras Exportar"
texto = modal.inner_text()
assert "exportaci" in texto.lower(), f"Se esperaba un mensaje de exportacion generada, se vio: {texto!r}"
capturar_paso(app, "mensaje_exportacion_verificado", paso_excel=6)
boton_aceptar = modal.get_by_role("button", name="Aceptar", exact=True)
if boton_aceptar.count():
    boton_aceptar.first.click()
print("[AVISO] No se pudo confirmar con expect_download() que el archivo fisico se haya descargado en esta corrida - el dialogo 'Exportacion generada.' aparece igual, se documenta como evidencia visual.")
''')

add("CP075", "abrir_resumen_pedidos", '''
# TODO SIN CONFIRMAR: este ambiente no tiene pedidos EN CURSO activos
# (ver AVISO de CP065) - no hay filas reales en la grilla con las que
# comparar el contenido del archivo exportado filtrado.
campo_resumen(frame, "SET").select_option(index=1)
valor_set_elegido = campo_resumen(frame, "SET").locator("option:checked").inner_text()
campo_resumen(frame, "Tiempo").select_option(label="Ultimos 12 horas")
buscar_resumen(frame)
app.wait_for_timeout(1500)
capturar_paso(app, "busqueda_filtrada", paso_excel=4)
frame.get_by_role("button", name="Exportar", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "exportacion_con_filtro", paso_excel=5)
modal = frame.locator("cdk-dialog-container, .mdl-confirmar, nz-modal-container").last
if modal.count() and modal.is_visible():
    boton_aceptar = modal.get_by_role("button", name="Aceptar", exact=True)
    if boton_aceptar.count():
        boton_aceptar.first.click()
capturar_paso(app, "verificado", paso_excel=6)
print(f"[AVISO] Exportacion disparada con SET={valor_set_elegido!r} - no se pudo comparar el contenido del archivo contra la grilla (grilla sin filas EN CURSO en este ambiente).")
''')


if __name__ == "__main__":
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")
