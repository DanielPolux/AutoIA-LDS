"""
generate_scripts.py - PR000326-SP2 (Refactorización Synergia Reclamos,
Sprint 2, módulo Manejo del Reclamo de Reclamos Comerciales).

CONFIRMADO EN VIVO 24/09/2026 (_exploracion/explore_0[1-9]*.py):

1. Esto NO es el portal "de siempre" con un menú único - es una app
   Angular INDEPENDIENTE por RF (12 apps distintas, dominio
   tk0s-web.luzdelsur.com.pe/comercial/reclamocom/... en Pruebas), pero
   el ACCESO real sigue siendo a través del portal Web LDS de siempre
   (pldsweb.luzdelsur.com.pe): navegar directo a la URL de tk0s-web da
   401 en TODAS las llamadas al backend (sin sesión OAuth válida) - hay
   que entrar por Aplicaciones > Comercial > Reclamos Comerciales >
   [nombre del módulo] del portal, que abre un POPUP con el token
   correcto (mismo mecanismo de core.abrir_aplicacion(), ya usado en
   otros proyectos - reutilizable tal cual).

2. Usuario de pruebas: SCASTI_DW (Miguel Angel Portal Romero). Rango de
   fechas por defecto para búsquedas (pedido explícito del usuario):
   01/09/2026 - 24/09/2026 (coincide, por suerte, con el default real
   del campo Fecha Inicio/Fin de RF-05).

3. Roles ya configurados para este usuario: LUZGENCON, ATNRCLM, ADARCLM
   (dan acceso a pantalla). RF-02 (Asignación) y RF-03 (Reasignación)
   estaban bloqueados por falta de jefatura - RESUELTO 24/09/2026: la
   jefatura es una fila SEPARADA en csc_rolxest (DBTECNICA, Informix),
   marcada por rol_tip=1 (no rol_vigencia). rol_cod real de SCASTI_DW:
   'SCAZ'. El chequeo de acceso general exige jefatura en una estación
   CONVENCIONAL (no ADA/CRE/JDS/SGR/APE, que son especiales) - se
   agregó `INSERT INTO csc_rolxest (rol_cod, rol_est_cod, rol_tip,
   rol_vigencia) VALUES ('SCAZ', 'ISE', 1, 1)`. Con eso, pestaña
   Estructurado funciona completo (dropdown Estación muestra "Jefe
   Sucursal" = descripción de ISE). OJO: la pestaña ADA sigue
   deshabilitada (aria-disabled) pese a que `csc_rolxest` tiene
   rol_tip=1/rol_vigencia=1 para ADA tambien (confirmado por SQL) -
   parece cache del backend, no reintentar mas de la cuenta, reintentar
   mas adelante si hace falta.

4. RF-01 (Mis Reclamos) confirmado con grilla REALMENTE VACÍA para
   SCASTI_DW ahora mismo (0 reclamos asignados a su estación) - esto es
   el escenario real de CP007 ("Carga inicial sin reclamos asignados"),
   NO un error. La mayoría del resto de casos de RF-01 (CP001 y otros
   13 "Tipo A") necesitan un pool de reclamos reales sembrado en la
   sucursal/CR de esta sesión - ver "datos" de CP001 en matriz_casos.json
   para el script Informix exacto (tabla CS_LLamada, columna
   Cod_Sucursal) - PENDIENTE, no inventar codigos de Desarrollo
   (RE000189-ESC-2026 etc, no portables a Pruebas).

5. Componentes Angular raíz confirmados (para abrir_aplicacion):
   RF-01 app-gestion-reclamo | RF-04 app-atencion-rapida-conciliacion |
   RF-05 app-main-layout | RF-06 app-consulta-del-reclamo |
   RF-07 app-resolucion | RF-08 app-acuerdos | RF-12 app-cargo-osinerg.

6. RF-06/RF-07/RF-08/RF-12 acceden bien SOLOS pero muestran su estado
   "sin reclamo cargado" (correcto, no error) cuando se entra directo
   sin pasar por RF-01/RF-05 con un reclamo real seleccionado - la
   mayoría de sus casos de fondo tambien necesitan un código de reclamo
   real (buscarlo primero con RF-05, que sí trae datos históricos reales
   sin necesitar seeding).
"""
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).parent
sys.path.insert(0, str(OUT_DIR.parent / "_framework"))
import web_lds_core as core

PROYECTO = "PR000326-SP2"
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
USUARIO = "SCASTI_DW"
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

# --- Navegacion propia de este proyecto: 1 app Angular independiente por RF ---
# CONFIRMADO EN VIVO 24/09/2026: entrar SIEMPRE por el portal
# (Aplicaciones > Comercial > Reclamos Comerciales > <modulo>), nunca
# por URL directa a tk0s-web (da 401 en todas las llamadas al backend).

def abrir_mis_reclamos(page, paso_excel=None):
    return abrir_aplicacion(page,["Comercial", "Reclamos Comerciales", "Mis Reclamos"], "app-gestion-reclamo", paso_excel=paso_excel)


def abrir_conciliacion(page, paso_excel=None):
    return abrir_aplicacion(page,["Comercial", "Reclamos Comerciales", "Atención Rápida - Conciliación De Tres Dias"], "app-atencion-rapida-conciliacion", paso_excel=paso_excel)


def abrir_busqueda(page, paso_excel=None):
    return abrir_aplicacion(page,["Comercial", "Reclamos Comerciales", "Búsqueda De Reclamos"], "app-main-layout", paso_excel=paso_excel)


def abrir_consulta(page, paso_excel=None):
    return abrir_aplicacion(page,["Comercial", "Reclamos Comerciales", "Consulta Detalle Reclamo"], "app-consulta-del-reclamo", paso_excel=paso_excel)


def abrir_resolucion(page, paso_excel=None):
    return abrir_aplicacion(page,["Comercial", "Reclamos Comerciales", "Resolución Del Reclamo"], "app-resolucion", paso_excel=paso_excel)


def abrir_acuerdos(page, paso_excel=None):
    return abrir_aplicacion(page,["Comercial", "Reclamos Comerciales", "Acuerdos Del Reclamo"], "app-acuerdos", paso_excel=paso_excel)


def abrir_cargo_osinerg(page, paso_excel=None):
    return abrir_aplicacion(page,["Comercial", "Reclamos Comerciales", "Cargo De Recepcion Osinerg"], "app-cargo-osinerg", paso_excel=paso_excel)


def abrir_asignacion(page, paso_excel=None):
    return abrir_aplicacion(page,["Comercial", "Reclamos Comerciales", "Asignacion De Reclamos"], "app-asignacion-de-reclamos", paso_excel=paso_excel)


def abrir_reasignacion(page, paso_excel=None):
    return abrir_aplicacion(page,["Comercial", "Reclamos Comerciales", "Reasignación De Reclamos"], "app-reasignacion-de-reclamos", paso_excel=paso_excel)


def abrir_gestion_reclamo(page, paso_excel=None):
    return abrir_aplicacion(page,["Comercial", "Reclamos Comerciales", "Mantenedor Gestión Reclamo"], "app-shell-layout", paso_excel=paso_excel)

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
# RF-01: Mis Reclamos (Evaluacion de Reclamos)
# ===========================================================================

add("CP007", "app, frame = abrir_mis_reclamos(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 24/09/2026: SCASTI_DW no tiene reclamos asignados
# en su estacion ahora mismo - la grilla real esta vacia, sin dialogo
# de error (a diferencia del 401 que se ve si se entra por URL directa
# sin pasar por el portal).
esperar_fin_de_carga(app, frame)
mensaje_vacio = frame.get_by_text("No se encontraron reclamos.", exact=True)
mensaje_vacio.wait_for(state="visible", timeout=15000)
capturar_paso(app, "grilla_vacia", paso_excel=3)
dialogo_error = frame.get_by_text("Error de Servicio", exact=True)
assert dialogo_error.count() == 0, "No deberia aparecer un dialogo de Error de Servicio con la grilla vacia"
''')

# CONFIRMADO EN VIVO 25/09/2026 (_exploracion/explore_76..78*.py): el
# "menu de Gestion de las Aplicaciones de Reclamos" que describen
# CP230/232/233/234 NO esta en el portal viejo - es una pantalla
# Angular propia, alcanzable por el portal como "Mantenedor Gestión
# Reclamo" (nombre distinto al de la matriz). Es un panel lateral
# ("Gestión de Reclamos") con grupos TRAMITES/CONSULTAS, caja "Buscar
# acción..." con filtro EN VIVO real, y "Cerrar sesión" al pie. Clickear
# cualquier item navega DENTRO del mismo popup/iframe (ruta Angular
# client-side, sin recargar) al modulo correspondiente - confirmado con
# "Asignación" (Tramites) y "Cargo OSINERG" (Consultas). CP234 (Cerrar
# sesión) SI se probo pero deja una pantalla gris con icono de bloqueo
# (forbidden) - mismo tipo de bug que CP127 (navegacion fuera del
# iframe #aplicacion bloqueada por el navegador) - no se escribe ese
# caso, queda pendiente igual que CP127.

add("CP230", "app, frame = abrir_gestion_reclamo(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 25/09/2026: el contenido de cada modulo carga
# dentro de un IFRAME ANIDADO (app-iframe-viewer > <iframe>) distinto
# del `frame` del panel lateral - hay que volver a entrar via
# frame.locator("iframe").content_frame para verificar el contenido
# cargado, el `frame` original solo sirve para clickear el menu.
capturar_paso(app, "menu_lateral_visible", paso_excel=3)
frame.get_by_text("Asignación", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "modulo_asignacion", paso_excel=3)
subframe = frame.locator("iframe").content_frame
assert subframe.get_by_text("Asignación de Reclamos", exact=True).count() > 0, "Deberia mostrarse el modulo de Asignacion de Reclamos"
frame.get_by_text("Cargo OSINERG", exact=True).click()
app.wait_for_timeout(1500)
capturar_paso(app, "modulo_cargo_osinerg", paso_excel=4)
subframe2 = frame.locator("iframe").content_frame
assert subframe2.get_by_text("Registro Cargo OSINERG", exact=True).count() > 0, "Deberia mostrarse el modulo de Cargo de Recepcion Osinerg"
''')

add("CP232", "app, frame = abrir_gestion_reclamo(page, paso_excel=2)", '''
campo_buscar = frame.get_by_placeholder(re.compile("Buscar", re.I))
capturar_paso(app, "menu_completo", paso_excel=3)
campo_buscar.fill("Conc")
app.wait_for_timeout(800)
capturar_paso(app, "menu_filtrado_conc", paso_excel=4)
opciones_visibles = [t.strip() for t in frame.locator("aside a, nav a, mat-sidenav a").all_inner_texts() if t.strip()]
opciones_no_logout = [o for o in opciones_visibles if "sesi" not in o.lower()]
assert opciones_no_logout == ["Conciliación"] or all("conciliaci" in o.lower() for o in opciones_no_logout), f"Se esperaba solo 'Conciliacion' visible: {opciones_no_logout}"
''')

add("CP233", "app, frame = abrir_gestion_reclamo(page, paso_excel=2)", '''
campo_buscar = frame.get_by_placeholder(re.compile("Buscar", re.I))
campo_buscar.fill("zzznoexiste")
app.wait_for_timeout(800)
capturar_paso(app, "menu_sin_coincidencias", paso_excel=3)
opciones_visibles = [t.strip() for t in frame.locator("aside a, nav a, mat-sidenav a").all_inner_texts() if t.strip()]
opciones_no_logout = [o for o in opciones_visibles if "sesi" not in o.lower()]
assert opciones_no_logout == [], f"No deberia quedar ninguna opcion visible salvo Cerrar sesion: {opciones_no_logout}"
''')


# ===========================================================================
# RF-04: Atencion Rapida - Conciliacion De Tres Dias
# ===========================================================================
# CONFIRMADO EN VIVO 25/09/2026 (_exploracion/explore_128/129/130_*.py):
# a diferencia de RF-07 (Resolucion), esta pantalla SI tiene un campo de
# busqueda directa por codigo de reclamo (no es una cola/bandeja) - se
# puede probar sin depender de a quien este asignado el reclamo.
# RE006897-ESC-2026 (confirmado con rcl_admisible=0 real, revertido en
# ronda 10 de este proyecto) da el mensaje real de precondicion no
# cumplida: "Reclamo no existe, o no tiene permiso sobre el reclamo.
# Debe estar en Primera Instancia, En Tramite y Admisible." - y el campo
# Codigo de Reclamo queda vacio despues, tal como espera la matriz.

add("CP075", "app, frame = abrir_conciliacion(page, paso_excel=2)", '''
capturar_paso(app, "pantalla_en_blanco", paso_excel=3)
boton_conciliado = frame.get_by_role("button", name="Conciliado", exact=True)
boton_registrar = frame.get_by_role("button", name="Registrar Acuerdos", exact=True)
boton_cerrar = frame.get_by_role("button", name="Cerrar", exact=True)
assert boton_conciliado.is_disabled(), "Conciliado deberia estar deshabilitado sin reclamo cargado"
assert boton_registrar.is_enabled(), "Registrar Acuerdos deberia estar habilitado"
assert boton_cerrar.is_enabled(), "Cerrar deberia estar habilitado"
''')

add("CP072", "app, frame = abrir_conciliacion(page, paso_excel=2)", '''
campo_codigo = frame.locator("input").first
campo_codigo.fill("RE006897-ESC-2026")
capturar_paso(app, "codigo_ingresado", paso_excel=3)
campo_codigo.press("Tab")
app.wait_for_timeout(2000)
capturar_paso(app, "mensaje_precondicion", paso_excel=4)
mensaje = frame.get_by_text(re.compile(r"Reclamo no existe.*Admisible", re.I))
mensaje.wait_for(state="visible", timeout=10000)
frame.locator("app-alert").get_by_role("button", name="Cerrar", exact=True).last.click()
app.wait_for_timeout(500)
capturar_paso(app, "campo_limpio", paso_excel=4)
assert frame.locator("input").first.input_value() == "", "El campo Codigo de Reclamo deberia quedar vacio tras el mensaje de precondicion no cumplida"
''')

# CONFIRMADO EN VIVO 25/09/2026 (query directa a cs_operador): SCAZ
# tiene nivel='N' (operador SIN nivel amplio) y zona VACIA - con esa
# combinacion, NINGUN reclamo de NINGUNA sucursal puede coincidir con
# la suya nunca, asi que cualquier reclamo real admisible/primera
# instancia/en tramite (que ya pasaria las otras 2 condiciones) cae
# exactamente en el escenario de CP078 ("reclamo de otra sucursal,
# operador sin nivel amplio"). Reutiliza el mismo mensaje generico ya
# confirmado varias veces con RE006893/896/898/899/900/901.
add("CP078", "app, frame = abrir_conciliacion(page, paso_excel=2)", '''
campo_codigo = frame.locator("input").first
campo_codigo.fill("RE006893-WEB-2026")
capturar_paso(app, "codigo_ingresado", paso_excel=3)
campo_codigo.press("Tab")
app.wait_for_timeout(2000)
capturar_paso(app, "mensaje_precondicion", paso_excel=4)
mensaje = frame.get_by_text(re.compile(r"Reclamo no existe.*Admisible", re.I))
mensaje.wait_for(state="visible", timeout=10000)
frame.locator("app-alert").get_by_role("button", name="Cerrar", exact=True).last.click()
app.wait_for_timeout(500)
capturar_paso(app, "campo_limpio", paso_excel=4)
assert frame.locator("input").first.input_value() == "", "El campo Codigo de Reclamo deberia quedar vacio tras el mensaje de precondicion no cumplida"
''')


# ===========================================================================
# RF-05: Busqueda De Reclamos
# ===========================================================================
# CONFIRMADO EN VIVO 24/09/2026 (_exploracion/explore_1[01]*.py): el rango
# de fechas por defecto (01/09/2026-24/09/2026, el mismo que pidio el
# usuario) SI trae datos reales sin sembrar nada - 2 reclamos reales
# encontrados (RE006896-WEB-2026, RE006893-WEB-2026). "Traer Todos" NO
# se usa (se probo y quedo colgado, parece traer TODO el historico sin
# limite - muy lento/no confiable). Los campos Fecha Inicio/Fin son
# <input type="date"> nativos (gotcha ya conocido: llenar con ISO
# yyyy-mm-dd, NUNCA dd/mm/aaaa aunque se vea asi en pantalla). Opciones
# reales confirmadas del combo Instancia: "Todas", "APELACION",
# "RECONSIDERACION", "JUDICIAL", "PRIMERA INSTANCIA" (OJO: el nombre del
# caso CP097 dice "Instancia = Primera" pero la opcion real del combo es
# "PRIMERA INSTANCIA", no "Primera" a secas).

add("CP093", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
campo_fecha_ini = frame.get_by_label(re.compile("Fecha Inicio", re.I))
campo_fecha_fin = frame.get_by_label(re.compile("Fecha Fin", re.I))
campo_fecha_ini.fill("2026-09-01")
campo_fecha_fin.fill("2026-09-24")
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_busqueda", paso_excel=4)
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 reclamo real en el rango 01/09-24/09/2026"
for i in range(filas.count()):
    texto_fila = filas.nth(i).inner_text()
    if not texto_fila.strip():
        continue
    m = re.search(r"\\bRE\\S*-\\d{4}\\b", texto_fila)
    assert m, f"No se encontro un codigo de reclamo con prefijo R en la fila: {texto_fila!r}"
    assert "DESCARTADO" not in texto_fila.upper(), f"No deberia haber reclamos Descartados: {texto_fila!r}"
''')

add("CP097", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
# Opcion real del combo: "PRIMERA INSTANCIA" (no "Primera" como dice el
# nombre del caso en la matriz - confirmado en vivo).
campo_instancia = frame.get_by_label(re.compile("Instancia", re.I))
campo_instancia.click()
app.wait_for_timeout(500)
frame.get_by_role("option", name="PRIMERA INSTANCIA", exact=True).click()
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_filtrado", paso_excel=4)
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 reclamo en Primera Instancia en el rango de fechas default"
for i in range(filas.count()):
    texto_fila = filas.nth(i).inner_text()
    if texto_fila.strip():
        assert "PRIMERA INSTANCIA" in texto_fila.upper(), f"Fila fuera de Primera Instancia: {texto_fila!r}"
''')

add("CP100", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 24/09/2026: rango 1990-01-01/1990-01-02 (sin
# actividad real) da el mensaje esperado y deshabilita ambos botones de
# exportar - un rango "reciente sin datos" (ej. un mes cualquiera de
# 2020) SI tenia reclamos reales, no sirve para este caso.
campo_fecha_ini = frame.get_by_label(re.compile("Fecha Inicio", re.I))
campo_fecha_fin = frame.get_by_label(re.compile("Fecha Fin", re.I))
campo_fecha_ini.fill("1990-01-01")
campo_fecha_fin.fill("1990-01-02")
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "grilla_vacia", paso_excel=4)
mensaje = frame.get_by_text("No se encontraron reclamos con los filtros indicados.", exact=True)
mensaje.wait_for(state="visible", timeout=10000)
boton_pdf = frame.get_by_role("button", name="Exportar PDF", exact=True)
boton_excel = frame.get_by_role("button", name="Exportar Excel", exact=True)
assert boton_pdf.is_disabled(), "Exportar PDF deberia estar deshabilitado sin resultados"
assert boton_excel.is_disabled(), "Exportar Excel deberia estar deshabilitado sin resultados"
''')

add("CP098", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
# Opcion real confirmada: "EN PROCESO" (existe tambien "PENDIENTES/EN
# PROCESO", distinta - usar el texto exacto).
campo_estado = frame.get_by_label(re.compile("^Estado$", re.I))
campo_estado.click()
app.wait_for_timeout(500)
frame.get_by_role("option", name="EN PROCESO", exact=True).click()
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_filtrado", paso_excel=4)
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 reclamo en estado En Proceso en el rango de fechas default"
for i in range(filas.count()):
    texto_fila = filas.nth(i).inner_text()
    if texto_fila.strip():
        assert "DESCARTADO" not in texto_fila.upper(), f"No deberia haber reclamos Descartados: {texto_fila!r}"
''')

add("CP110", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
campo_fecha_ini = frame.get_by_label(re.compile("Fecha Inicio", re.I))
campo_fecha_fin = frame.get_by_label(re.compile("Fecha Fin", re.I))
assert not campo_fecha_ini.is_disabled(), "Fecha Inicio deberia estar habilitada al inicio"
checkbox_traer_todos = frame.get_by_role("checkbox", name="Traer Todos")
capturar_paso(app, "antes_de_marcar", paso_excel=3)
checkbox_traer_todos.click()
app.wait_for_timeout(500)
capturar_paso(app, "traer_todos_marcado", paso_excel=3)
assert campo_fecha_ini.is_disabled(), "Fecha Inicio deberia deshabilitarse al marcar Traer Todos"
assert campo_fecha_fin.is_disabled(), "Fecha Fin deberia deshabilitarse al marcar Traer Todos"
checkbox_traer_todos.click()
app.wait_for_timeout(500)
capturar_paso(app, "traer_todos_desmarcado", paso_excel=4)
assert not campo_fecha_ini.is_disabled(), "Fecha Inicio deberia rehabilitarse al desmarcar Traer Todos"
assert not campo_fecha_fin.is_disabled(), "Fecha Fin deberia rehabilitarse al desmarcar Traer Todos"
''')

add("CP109", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 24/09/2026: con los 2 reclamos reales conocidos
# (ambos Primera Instancia), Apelacion + Solo Notif. Electronica no
# matchea ninguno - resultado vacio esperado y valido (no hay reclamos
# reales en Apelacion con notif. electronica en el rango de fechas
# default ahora mismo).
campo_instancia = frame.get_by_label(re.compile("Instancia", re.I))
campo_instancia.click()
app.wait_for_timeout(500)
frame.get_by_role("option", name="APELACION", exact=True).click()
app.wait_for_timeout(300)
checkbox_notif = frame.get_by_role("checkbox", name=re.compile("Solo Notif", re.I))
checkbox_notif.click()
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_combinado", paso_excel=4)
filas = frame.locator("table tbody tr")
mensaje_vacio_texto = "No se encontraron reclamos con los filtros indicados."
for i in range(filas.count()):
    texto_fila = filas.nth(i).inner_text()
    # CONFIRMADO EN VIVO 08/10/2026: con 0 resultados reales la grilla
    # renderiza 1 sola <tr> placeholder con este mensaje exacto (no una
    # fila vacia) - hay que excluirla del chequeo o el assert de abajo
    # falla siempre que el resultado real es 0, aunque sea el escenario
    # valido que este caso espera.
    if texto_fila.strip() and texto_fila.strip() != mensaje_vacio_texto:
        assert "APELACION" in texto_fila.upper(), f"Fila fuera de Apelacion con ambos filtros combinados: {texto_fila!r}"
''')

add("CP111", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 24/09/2026: con menos de 1000 resultados (rango
# default, 2 reclamos), el boton "Mas Resultados" NO SE RENDERIZA en
# absoluto (count()==0), no solo queda deshabilitado - se tolera
# cualquiera de los 2 casos.
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_menos_de_1000", paso_excel=4)
filas = frame.locator("table tbody tr")
assert 0 < filas.count() < 1000, f"Se esperaba un resultado real pero menor a 1000 filas, se vieron {filas.count()}"
boton_mas = frame.get_by_role("button", name=re.compile("M.s Resultados", re.I))
assert boton_mas.count() == 0 or boton_mas.is_disabled(), "Mas Resultados no deberia estar habilitado con menos de 1000 coincidencias"
''')

# CONFIRMADO EN VIVO 25/09/2026 (_exploracion/explore_109_busqueda_re006900.py,
# explore_125_doble_clic_re006893.py): a diferencia de lo documentado en
# rondas anteriores de este proyecto (el doble clic no abria nada, ni
# popup ni navegacion), ahora SI navega correctamente dentro del mismo
# frame hacia Consulta del Reclamo, con Anterior/Siguiente habilitado -
# probado 2 veces, en 2 reclamos reales distintos (RE006900, RE006893).

add("CP103", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
campo_fecha_ini = frame.get_by_label(re.compile("Fecha Inicio", re.I))
campo_fecha_fin = frame.get_by_label(re.compile("Fecha Fin", re.I))
campo_fecha_ini.fill("2026-09-01")
campo_fecha_fin.fill("2026-09-24")
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 reclamo real en el rango"
codigo_original = re.search(r"RE\\S*-\\d{4}", filas.first.inner_text()).group()
capturar_paso(app, "antes_del_doble_clic", paso_excel=3)
filas.first.dblclick()
app.wait_for_timeout(2000)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "consulta_abierta", paso_excel=4)
texto_pantalla = frame.locator("body").inner_text()
assert "Consulta del Reclamo" in texto_pantalla, "Deberia navegar a Consulta del Reclamo tras el doble clic"
assert codigo_original in texto_pantalla, f"Deberia preseleccionar el reclamo {codigo_original}"
boton_siguiente = frame.get_by_role("button", name="Siguiente", exact=True).first
boton_anterior = frame.get_by_role("button", name="Anterior", exact=True).first
assert boton_siguiente.is_enabled() or boton_anterior.is_enabled(), "Se esperaba navegacion Anterior/Siguiente habilitada"
''')

add("CP118", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
campo_fecha_ini = frame.get_by_label(re.compile("Fecha Inicio", re.I))
campo_fecha_fin = frame.get_by_label(re.compile("Fecha Fin", re.I))
campo_fecha_ini.fill("2026-09-01")
campo_fecha_fin.fill("2026-09-24")
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
filas = frame.locator("table tbody tr")
assert filas.count() >= 2, f"Se esperaban al menos 2 reclamos reales para navegar Anterior/Siguiente, se vieron {filas.count()}"
capturar_paso(app, "listado_origen", paso_excel=3)
filas.first.dblclick()
app.wait_for_timeout(2000)
esperar_fin_de_carga(app, frame)
codigo_1 = re.search(r"RE\\S*-\\d{4}", frame.locator("body").inner_text()).group()
capturar_paso(app, "primer_reclamo", paso_excel=4)
frame.get_by_role("button", name="Siguiente", exact=True).first.click()
app.wait_for_timeout(1500)
esperar_fin_de_carga(app, frame)
texto_tras_siguiente = frame.locator("body").inner_text()
assert "Consulta del Reclamo" in texto_tras_siguiente, "Siguiente no deberia volver a la pantalla de Busqueda"
codigo_2 = re.search(r"RE\\S*-\\d{4}", texto_tras_siguiente).group()
assert codigo_2 != codigo_1, f"Siguiente deberia cargar un reclamo distinto: {codigo_1!r} vs {codigo_2!r}"
capturar_paso(app, "segundo_reclamo", paso_excel=4)
frame.get_by_role("button", name="Anterior", exact=True).first.click()
app.wait_for_timeout(1500)
esperar_fin_de_carga(app, frame)
texto_tras_anterior = frame.locator("body").inner_text()
assert "Consulta del Reclamo" in texto_tras_anterior, "Anterior no deberia volver a la pantalla de Busqueda"
codigo_3 = re.search(r"RE\\S*-\\d{4}", texto_tras_anterior).group()
assert codigo_3 == codigo_1, f"Anterior deberia volver al reclamo original: {codigo_1!r} vs {codigo_3!r}"
''')

add("CP127", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
campo_fecha_ini = frame.get_by_label(re.compile("Fecha Inicio", re.I))
campo_fecha_fin = frame.get_by_label(re.compile("Fecha Fin", re.I))
campo_fecha_ini.fill("2026-09-01")
campo_fecha_fin.fill("2026-09-24")
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
filas = frame.locator("table tbody tr")
filas_antes = filas.count()
assert filas_antes > 0, "Se esperaba al menos 1 reclamo real en el rango"
codigo_original = re.search(r"RE\\S*-\\d{4}", filas.first.inner_text()).group()
filas.first.dblclick()
app.wait_for_timeout(2000)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "consulta_abierta", paso_excel=3)
frame.get_by_role("button", name="Cerrar", exact=True).first.click()
app.wait_for_timeout(2000)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "regreso_al_listado", paso_excel=4)
texto_tras_cerrar = frame.locator("body").inner_text()
assert "Consulta del Reclamo" not in texto_tras_cerrar, "Cerrar deberia regresar a Busqueda de Reclamos, no quedarse en Consulta"
filas_despues = frame.locator("table tbody tr")
assert filas_despues.count() == filas_antes, f"El listado de origen deberia conservarse: antes {filas_antes}, despues {filas_despues.count()}"
assert codigo_original in texto_tras_cerrar, "El reclamo original deberia seguir visible en el listado conservado"
''')

# CONFIRMADO EN VIVO 24/09/2026 (_exploracion/explore_39_rf05_restantes.py,
# explore_41_semaforo_clase.py): con los 2 reclamos reales conocidos (ambos
# Primera Instancia / EN PROCESO), Instancia=APELACION da 0 resultados
# (igual que ya confirmaba CP109) y "Solo Notif. Electronica" solo tambien
# da 0 - ninguno de los 2 tiene notificacion electronica configurada. El
# semaforo real usa spans "punto verde"/"punto amarillo"/"punto rojo" con
# atributo title "Plazo total: N dias" - los 2 reclamos conocidos siempre
# dan verde (30/23 y 13/6 dias, ninguno vencido ni proximo a vencer) asi
# que solo CP106 (verde) es reproducible con datos reales; CP104 (rojo,
# vencido) y CP105 (amarillo, 1-3 dias) necesitan un reclamo real en esa
# condicion especifica, no disponible - quedan pendientes.

add("CP106", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
campo_fecha_ini = frame.get_by_label(re.compile("Fecha Inicio", re.I))
campo_fecha_fin = frame.get_by_label(re.compile("Fecha Fin", re.I))
campo_fecha_ini.fill("2026-09-01")
campo_fecha_fin.fill("2026-09-24")
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_con_semaforos", paso_excel=4)
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 reclamo real"
puntos_verdes = frame.locator("table tbody tr .punto.verde")
assert puntos_verdes.count() > 0, "Se esperaba al menos 1 punto de semaforo verde (plazo suficiente)"
''')

add("CP107", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
campo_fecha_ini = frame.get_by_label(re.compile("Fecha Inicio", re.I))
campo_fecha_fin = frame.get_by_label(re.compile("Fecha Fin", re.I))
campo_fecha_ini.fill("2026-09-01")
campo_fecha_fin.fill("2026-09-24")
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_codigos", paso_excel=4)
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 reclamo real"
for i in range(filas.count()):
    codigo = filas.nth(i).locator("td").nth(1).inner_text().strip()
    assert codigo.startswith("R"), f"Todo codigo de reclamo deberia iniciar con R: {codigo!r}"
''')

add("CP104", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 25/09/2026 (_exploracion/explore_104_cp104_rango_angosto.py):
# los 2 reclamos reales conocidos en el rango default del proyecto
# siempre dan semaforo verde (plazo sobrado) - CP104 necesita un
# reclamo realmente vencido, que SI existe en la base historica real
# pero fuera del rango default. Un rango amplio (2024-2026, 1000+
# resultados) resulta INESTABLE - el backend tira "Error de Servicio"
# ~2 de cada 3 intentos con ese volumen (ver hallazgo de inestabilidad
# documentado en la memoria del proyecto). Un rango angosto alrededor
# de un reclamo vencido puntual (RE017344-ESC-2023, Plazo total: -972
# dias) SI es estable y reproducible (534 filas, sin error).
campo_fecha_ini = frame.get_by_label(re.compile("Fecha Inicio", re.I))
campo_fecha_fin = frame.get_by_label(re.compile("Fecha Fin", re.I))
campo_fecha_ini.fill("2023-12-25")
campo_fecha_fin.fill("2024-01-10")
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_con_vencidos", paso_excel=4)
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 reclamo real en el rango angosto de diciembre 2023/enero 2024"
puntos_rojos = frame.locator("table tbody tr .punto.rojo")
assert puntos_rojos.count() > 0, "Se esperaba al menos 1 punto de semaforo rojo (plazo vencido)"
titulo = puntos_rojos.first.get_attribute("title") or ""
assert "-" in titulo, f"El titulo del semaforo rojo deberia mostrar dias negativos: {titulo!r}"
''')

add("CP099", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 24/09/2026: ninguno de los 2 reclamos reales
# conocidos tiene notificacion electronica configurada - "Solo Notif.
# Electronica" sola da grilla vacia, comportamiento valido y esperado.
checkbox_notif = frame.get_by_role("checkbox", name=re.compile("Solo Notif", re.I))
capturar_paso(app, "antes_de_marcar", paso_excel=3)
checkbox_notif.click()
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_filtrado", paso_excel=4)
filas = frame.locator("table tbody tr")
for i in range(filas.count()):
    texto_fila = filas.nth(i).inner_text()
    if texto_fila.strip() and "No se encontraron" not in texto_fila:
        assert re.search(r"\\bRE\\S*-\\d{4}\\b", texto_fila), f"Fila inesperada sin codigo real: {texto_fila!r}"
''')

add("CP095", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 24/09/2026: Instancia=APELACION da 0 resultados con
# los datos reales actuales (igual que CP109) - se valida igual que la
# combinacion AND no traiga nada fuera de Apelacion (vacio es un
# resultado valido: 0 interseccion con Estado=EN PROCESO tambien).
campo_instancia = frame.get_by_label(re.compile("Instancia", re.I))
campo_instancia.click()
app.wait_for_timeout(400)
frame.get_by_role("option", name="APELACION", exact=True).click()
capturar_paso(app, "filtro_instancia", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
filas_apelacion = frame.locator("table tbody tr")
for i in range(filas_apelacion.count()):
    texto_fila = filas_apelacion.nth(i).inner_text()
    if texto_fila.strip() and "No se encontraron" not in texto_fila:
        assert "APELACION" in texto_fila.upper(), f"Fila fuera de Apelacion: {texto_fila!r}"

campo_instancia.click()
app.wait_for_timeout(400)
frame.get_by_role("option", name="Todas", exact=True).click()
campo_estado = frame.get_by_label(re.compile("^Estado$", re.I))
campo_estado.click()
app.wait_for_timeout(400)
frame.get_by_role("option", name="EN PROCESO", exact=True).click()
capturar_paso(app, "filtro_estado", paso_excel=4)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_estado", paso_excel=4)
filas_estado = frame.locator("table tbody tr")
assert filas_estado.count() > 0, "Se esperaba al menos 1 reclamo real en estado En Proceso"
for i in range(filas_estado.count()):
    texto_fila = filas_estado.nth(i).inner_text()
    if texto_fila.strip():
        assert "DESCARTADO" not in texto_fila.upper(), f"No deberia haber Descartados: {texto_fila!r}"
''')

add("CP096", "app, frame = abrir_busqueda(page, paso_excel=2)", '''
campo_fecha_ini = frame.get_by_label(re.compile("Fecha Inicio", re.I))
campo_fecha_fin = frame.get_by_label(re.compile("Fecha Fin", re.I))
campo_fecha_ini.fill("2026-09-01")
campo_fecha_fin.fill("2026-09-24")
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_cargado", paso_excel=3)
with app.expect_download(timeout=10000) as info_pdf:
    frame.get_by_role("button", name="Exportar PDF", exact=True).click()
descarga_pdf = info_pdf.value
capturar_paso(app, "pdf_exportado", paso_excel=4)
assert descarga_pdf.suggested_filename.lower().endswith(".pdf"), f"Se esperaba un PDF: {descarga_pdf.suggested_filename!r}"
with app.expect_download(timeout=10000) as info_excel:
    frame.get_by_role("button", name="Exportar Excel", exact=True).click()
descarga_excel = info_excel.value
capturar_paso(app, "excel_exportado", paso_excel=5)
assert descarga_excel.suggested_filename.lower().endswith(".xlsx"), f"Se esperaba un XLSX: {descarga_excel.suggested_filename!r}"
''')


# CP103 (doble clic abre Consulta del Reclamo) - PENDIENTE, 24/09/2026:
# el doble clic sobre la fila NO abre un popup nuevo (app.context.expect_page
# dio timeout) ni parece navegar dentro del mismo frame (app-consulta-del-reclamo
# nunca aparece). Necesita mas exploracion en vivo (¿hay que hacer click en
# una celda especifica en vez de la fila? ¿el doble click esta deshabilitado
# en este build de Pruebas?) antes de escribir el caso - no adivinar mas.


# ===========================================================================
# RF-06: Consulta Detalle Reclamo
# ===========================================================================
# CONFIRMADO EN VIVO 24/09/2026: el UNICO <input> de la pantalla es el
# campo Codigo del Reclamo (no tiene placeholder/aria-label util, usar
# frame.locator("input").first). Con el codigo real RE006896-WEB-2026,
# Anterior y Siguiente quedan AMBOS deshabilitados (logico: se entro
# directo por el menu, sin una lista de origen) y la pestana "Primera
# Instancia" existe como role="tab". CP112 (expediente completo con
# datos del cliente) NO se escribio todavia: la pantalla se quedo
# cargando (spinner) mas alla de la espera de red inicial en la
# exploracion - falta confirmar el tiempo de carga real antes de armar
# asserts sobre datos de cliente/tipos/seguimiento.

add("CP120", "app, frame = abrir_consulta(page, paso_excel=2)", '''
campo_codigo = frame.locator("input").first
campo_codigo.fill("RE006896-WEB-2026")
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "consulta_cargada", paso_excel=3)
boton_anterior = frame.get_by_role("button", name="Anterior", exact=True)
boton_siguiente = frame.get_by_role("button", name="Siguiente", exact=True)
assert boton_anterior.is_disabled(), "Anterior deberia estar deshabilitado al entrar directo sin listado de origen"
assert boton_siguiente.is_disabled(), "Siguiente deberia estar deshabilitado al entrar directo sin listado de origen"
''')

add("CP121", "app, frame = abrir_consulta(page, paso_excel=2)", '''
campo_codigo = frame.locator("input").first
campo_codigo.fill("RE006896-WEB-2026")
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
pestana_primera = frame.get_by_role("tab", name="Primera Instancia", exact=True)
pestana_primera.wait_for(state="visible", timeout=10000)
capturar_paso(app, "antes_de_seleccionar_pestana", paso_excel=3)
pestana_primera.click()
app.wait_for_timeout(500)
capturar_paso(app, "pestana_primera_instancia", paso_excel=4)
assert "true" == pestana_primera.get_attribute("aria-selected"), "La pestana Primera Instancia deberia quedar seleccionada"
''')

# CONFIRMADO EN VIVO 24/09/2026: el primer intento de CP112 fallo porque
# la espera de red no alcanzaba - la cabecera (CLIENTE, tipos, seguimiento)
# tarda mas en poblarse que el resto de la pantalla. Con polling activo
# (reintentar hasta que el texto de la cabecera ya no muestre "-" en
# NUMERO/NOMBRE/etc.) si carga completo.
add("CP112", "app, frame = abrir_consulta(page, paso_excel=2)", '''
campo_codigo = frame.locator("input").first
campo_codigo.fill("RE006896-WEB-2026")
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
campo_nombre_cliente = frame.get_by_text("LOURDES SOFFIA VASQUEZ CABANILLAS", exact=True)
campo_nombre_cliente.wait_for(state="visible", timeout=20000)
capturar_paso(app, "expediente_cargado", paso_excel=4)
for nombre_pestana in ("Primera Instancia", "Reconsideración", "Apelación", "Citaciones", "Audiencias"):
    pestana = frame.get_by_role("tab", name=nombre_pestana, exact=True)
    assert pestana.count() == 1, f"Deberia existir la pestana {nombre_pestana!r}"
texto_pantalla = frame.locator("body").inner_text()
assert "tipos del reclamo" in texto_pantalla.lower(), "Deberia mostrarse la grilla de Tipos de Reclamo"
assert "seguimiento" in texto_pantalla.lower(), "Deberia mostrarse la grilla de Seguimiento"
assert "análisis de" in texto_pantalla.lower() or "ingresado" in texto_pantalla.lower(), "Se esperaba al menos un movimiento real en el Seguimiento"
''')

add("CP115", "app, frame = abrir_consulta(page, paso_excel=2)", '''
campo_codigo = frame.locator("input").first
campo_codigo.fill("RE006896-WEB-2026")
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.get_by_text("LOURDES SOFFIA VASQUEZ CABANILLAS", exact=True).wait_for(state="visible", timeout=20000)
capturar_paso(app, "antes_de_ver_documentos", paso_excel=3)
frame.get_by_role("button", name="Ver Documentos", exact=True).click()
app.wait_for_timeout(1000)
capturar_paso(app, "modal_documentos", paso_excel=4)
modal_titulo = frame.get_by_text("Documentos", exact=False).first
modal_titulo.wait_for(state="visible", timeout=10000)
filas_docs = frame.locator("table tbody tr")
assert filas_docs.count() > 0, "Se esperaba al menos 1 documento adjunto vigente"
assert frame.locator("img[src*='pdf'], mat-icon:has-text('pdf')").count() > 0 or "pdf" in filas_docs.first.inner_text().lower(), "Se esperaba ver el icono/extension del archivo (pdf)"
''')

# CONFIRMADO EN VIVO 24/09/2026 (_exploracion/explore_42_rf06_descargas.py):
# el reclamo real RE006896-WEB-2026 (ya usado en CP112/CP115) tiene 2
# documentos adjuntos reales descargables dentro del modal "Ver
# Documentos" (Ficha de Registro + Documento relacionado, ambos .pdf).
# El boton "Descargar PDF" de la pantalla principal (no el modal) genera
# el PDF del expediente completo con el nombre real
# "Reclamo_<codigo>_<fecha-ISO>.pdf" - formato confirmado exacto.

add("CP117", "app, frame = abrir_consulta(page, paso_excel=2)", '''
campo_codigo = frame.locator("input").first
campo_codigo.fill("RE006896-WEB-2026")
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.get_by_text("LOURDES SOFFIA VASQUEZ CABANILLAS", exact=True).wait_for(state="visible", timeout=20000)
capturar_paso(app, "expediente_cargado", paso_excel=3)
with app.expect_download(timeout=10000) as info_descarga:
    frame.get_by_role("button", name="Descargar PDF", exact=True).click()
descarga = info_descarga.value
capturar_paso(app, "pdf_expediente_descargado", paso_excel=4)
assert re.match(r"^Reclamo_RE006896-WEB-2026_\\d{4}-\\d{2}-\\d{2}\\.pdf$", descarga.suggested_filename), f"Nombre de archivo inesperado: {descarga.suggested_filename!r}"
''')

add("CP116", "app, frame = abrir_consulta(page, paso_excel=2)", '''
campo_codigo = frame.locator("input").first
campo_codigo.fill("RE006896-WEB-2026")
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.get_by_text("LOURDES SOFFIA VASQUEZ CABANILLAS", exact=True).wait_for(state="visible", timeout=20000)
frame.get_by_role("button", name="Ver Documentos", exact=True).click()
app.wait_for_timeout(1000)
fila_documento = frame.locator("tr", has_text=".pdf").first
fila_documento.wait_for(state="visible", timeout=10000)
capturar_paso(app, "documento_seleccionado", paso_excel=3)
boton_descargar = fila_documento.locator("button:has(mat-icon:text('download')), button[aria-label*='escargar' i]")
with app.expect_download(timeout=10000) as info_descarga:
    boton_descargar.first.click()
descarga = info_descarga.value
capturar_paso(app, "documento_descargado", paso_excel=4)
assert descarga.suggested_filename.lower().endswith(".pdf"), f"Se esperaba un PDF: {descarga.suggested_filename!r}"
''')

add("CP122", "app, frame = abrir_consulta(page, paso_excel=2)", '''
campo_codigo = frame.locator("input").first
campo_codigo.fill("RE006896-WEB-2026")
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
pestana_reconsideracion = frame.get_by_role("tab", name="Reconsideración", exact=True)
pestana_reconsideracion.wait_for(state="visible", timeout=15000)
capturar_paso(app, "pestana_reconsideracion", paso_excel=3)
assert pestana_reconsideracion.get_attribute("aria-disabled") == "true", "La pestana Reconsideracion deberia estar deshabilitada para un reclamo solo con Primera Instancia"
''')

add("CP126", "app, frame = abrir_consulta(page, paso_excel=2)", '''
campo_codigo = frame.locator("input").first
campo_codigo.fill("RE006896-WEB-2026")
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.get_by_text("LOURDES SOFFIA VASQUEZ CABANILLAS", exact=True).wait_for(state="visible", timeout=20000)
boton_prueba_tecnica = frame.get_by_role("button", name="Prueba Técnica", exact=True)
capturar_paso(app, "boton_prueba_tecnica", paso_excel=3)
assert boton_prueba_tecnica.is_disabled(), "Prueba Tecnica deberia estar deshabilitado sin prueba tecnica vinculada"
''')


# ===========================================================================
# RF-08: Acuerdos Del Reclamo
# ===========================================================================
# CONFIRMADO EN VIVO 24/09/2026: el pestaña Consulta tiene 1 solo
# <input> visible (N Reclamo - Estado es un combo/select, no <input>).
# Tanto un codigo real SIN acuerdos como un codigo INEXISTENTE dan el
# mismo resultado (grilla vacia, "No se encontraron acuerdos.", 0 de 0,
# sin dialogo de error) - comportamiento consistente y correcto en
# ambos casos.

add("CP140", "app, frame = abrir_acuerdos(page, paso_excel=2)", '''
campo_reclamo = frame.locator("input").first
campo_reclamo.fill("RE006896-WEB-2026")
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_busqueda", paso_excel=4)
mensaje = frame.get_by_text("No se encontraron acuerdos.", exact=True)
mensaje.wait_for(state="visible", timeout=10000)
dialogo_error = frame.get_by_text("Error de Servicio", exact=True)
assert dialogo_error.count() == 0, "No deberia aparecer un dialogo de error al consultar por un reclamo real sin acuerdos"
''')

add("CP151", "app, frame = abrir_acuerdos(page, paso_excel=2)", '''
campo_reclamo = frame.locator("input").first
campo_reclamo.fill("RE999999-WEB-2026")
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "grilla_vacia", paso_excel=4)
mensaje = frame.get_by_text("No se encontraron acuerdos.", exact=True)
mensaje.wait_for(state="visible", timeout=10000)
dialogo_error = frame.get_by_text("Error de Servicio", exact=True)
assert dialogo_error.count() == 0, "Un codigo inexistente no deberia mostrar un dialogo de error, solo la grilla vacia"
''')


# ===========================================================================
# RF-12: Cargo De Recepcion Osinerg
# ===========================================================================
# CONFIRMADO EN VIVO 24/09/2026: 3 <input> en la pantalla, en orden:
# [0] Codigo de Reclamo, [1] N Resolucion OSINERG, [2] Fecha de Cargo.
# Con campo vacio, "Verificar" esta deshabilitado (CP214). Con el
# reclamo real RE006896-WEB-2026 (Primera Instancia, no Apelacion), el
# mensaje EXACTO es "El reclamo no corresponde a una Apelación." -
# CP215 en la matriz pide probar TAMBIEN "Apelacion pero no Admisible" y
# "Admisible pero no enviado a OSINERG", que no se pudieron confirmar
# (no hay un reclamo real en esos estados a mano) - este caso solo cubre
# el primer sub-escenario, confirmado en vivo. Con un codigo BIEN
# FORMADO pero inexistente (RE999999-WEB-2026), el mensaje real es
# "No se encontró el reclamo 'RE999999-WEB-2026'." (la matriz dice
# generico "Codigo no encontrado" pero el texto real es mas especifico -
# se usa el texto real confirmado en vivo, no el de la matriz).

add("CP214", "app, frame = abrir_cargo_osinerg(page, paso_excel=2)", '''
boton_verificar = frame.get_by_role("button", name="Verificar", exact=True)
capturar_paso(app, "campo_vacio", paso_excel=3)
assert boton_verificar.is_disabled(), "Verificar deberia estar deshabilitado con el campo de codigo vacio"
''')

add("CP215", "app, frame = abrir_cargo_osinerg(page, paso_excel=2)", '''
campo_codigo = frame.locator("input").first
campo_codigo.fill("RE006896-WEB-2026")
capturar_paso(app, "antes_de_verificar", paso_excel=3)
frame.get_by_role("button", name="Verificar", exact=True).click()
app.wait_for_timeout(1500)
dialogo = frame.get_by_text("El reclamo no corresponde a una Apelación.", exact=True)
dialogo.wait_for(state="visible", timeout=10000)
capturar_paso(app, "mensaje_no_apelacion", paso_excel=4)
tarjeta_cargo = frame.get_by_text("Cargo ya registrado", exact=True)
assert tarjeta_cargo.count() == 0, "No deberia mostrarse la tarjeta de datos del cargo cuando el reclamo no cumple precondiciones"
frame.get_by_role("button", name="Cerrar", exact=True).last.click()
''')

add("CP222", "app, frame = abrir_cargo_osinerg(page, paso_excel=2)", '''
campo_codigo = frame.locator("input").first
campo_codigo.fill("RE999999-WEB-2026")
capturar_paso(app, "antes_de_verificar", paso_excel=3)
frame.get_by_role("button", name="Verificar", exact=True).click()
app.wait_for_timeout(1500)
mensaje = frame.get_by_text("No se encontró el reclamo 'RE999999-WEB-2026'.", exact=True)
mensaje.wait_for(state="visible", timeout=10000)
capturar_paso(app, "codigo_no_encontrado", paso_excel=4)
# CONFIRMADO EN VIVO 08/10/2026: el boton del dialogo de error ya no se
# llama "Aceptar" - ahora dice "Cerrar" (cambio real de UI, el mensaje
# de error en si no cambio). Ademas, el locator scoped a "app-alert"
# nunca se vuelve visible (hay una instancia de ese tag en el DOM que
# no es la que realmente se ve en pantalla, probable overlay/portal
# fuera de ese contenedor) - se busca el boton directo en el frame. OJO:
# get_by_role("button", name="Cerrar") da "strict mode violation" -
# matchea TANTO el boton real de texto "Cerrar" COMO el icono "X" de
# cerrar la esquina (que tiene aria-label="Cerrar" pero sin texto
# visible) - se usa get_by_text para matchear solo el boton de texto.
frame.get_by_text("Cerrar", exact=True).click()
''')

# CONFIRMADO EN VIVO 24/09/2026 (_exploracion/explore_43_rf12_restantes.py,
# explore_44_rf12_verificar_error.py, explore_45_rf12_cancelar.py):
# - El boton "Acuerdos" (esquina superior) se habilita/deshabilita
#   SOLO en base a si el campo Codigo de Reclamo tiene texto - no
#   necesita Verificar exitoso, es un chequeo de formulario simple.
# - Normalizacion real de codigo: "RE006896-WEB-2026" (completo) y
#   "6896" (solo numero) SI normalizan al mismo reclamo real (mismo
#   mensaje "no corresponde a una Apelacion"). "RE6896-WEB-2026" (sin
#   ceros de relleno) NO es un formato soportado - da "No se encontro
#   el reclamo" - contradice la idea de "formato alterno" de la matriz,
#   asi que el caso se escribe solo con los 2 formatos confirmados.
# - "Cancelar" limpia Codigo de Reclamo y N Resolucion (ambos vuelven a
#   estar vacios) sin necesidad de haber verificado antes.

add("CP218", "app, frame = abrir_cargo_osinerg(page, paso_excel=2)", '''
boton_acuerdos = frame.get_by_role("button", name="Acuerdos", exact=True)
capturar_paso(app, "sin_codigo", paso_excel=3)
assert boton_acuerdos.is_disabled(), "Acuerdos deberia estar deshabilitado sin codigo de reclamo"
campo_codigo = frame.locator("input").first
campo_codigo.fill("RE006896-WEB-2026")
app.wait_for_timeout(500)
capturar_paso(app, "con_codigo", paso_excel=4)
assert boton_acuerdos.is_enabled(), "Acuerdos deberia habilitarse con un codigo ingresado"
campo_codigo.fill("")
app.wait_for_timeout(500)
capturar_paso(app, "codigo_limpiado", paso_excel=5)
assert boton_acuerdos.is_disabled(), "Acuerdos deberia volver a deshabilitarse al limpiar el codigo"
''')

add("CP219", "app, frame = abrir_cargo_osinerg(page, paso_excel=2)", '''
campo_codigo = frame.locator("input").first
for formato in ("RE006896-WEB-2026", "6896"):
    campo_codigo.fill(formato)
    capturar_paso(app, f"verificar_{formato}", paso_excel=3)
    frame.get_by_role("button", name="Verificar", exact=True).click()
    app.wait_for_timeout(1500)
    dialogo = frame.get_by_text("El reclamo no corresponde a una Apelación.", exact=True)
    dialogo.wait_for(state="visible", timeout=10000)
    capturar_paso(app, f"normalizado_{formato}", paso_excel=4)
    assert dialogo.count() > 0, f"El formato {formato!r} deberia normalizar al mismo reclamo real"
    frame.get_by_role("button", name="Cerrar", exact=True).last.click()
    app.wait_for_timeout(500)
    campo_codigo.fill("")
''')

add("CP229", "app, frame = abrir_cargo_osinerg(page, paso_excel=2)", '''
inputs = frame.locator("input")
campo_codigo = inputs.nth(0)
campo_resolucion = inputs.nth(1)
campo_codigo.fill("RE006896-WEB-2026")
campo_resolucion.fill("N 1234-2026-OS/JARU")
capturar_paso(app, "datos_ingresados", paso_excel=3)
frame.get_by_role("button", name="Cancelar", exact=True).click()
app.wait_for_timeout(1000)
capturar_paso(app, "tras_cancelar", paso_excel=4)
assert campo_codigo.input_value() == "", "El codigo de reclamo deberia quedar vacio tras Cancelar"
assert campo_resolucion.input_value() == "", "El N de Resolucion deberia quedar vacio tras Cancelar"
''')


# ===========================================================================
# RF-02: Asignacion De Reclamos
# ===========================================================================
# CONFIRMADO EN VIVO 24/09/2026: con jefatura en ISE (estacion
# convencional, descripcion real "Jefe Sucursal"), la pestana
# Estructurado carga completa. La pestana ADA sigue deshabilitada pese
# a tener jefatura confirmada en BD (posible cache del backend, ver
# docstring del archivo) - los casos de ADA (CP022/037/039/040) NO se
# escribieron todavia. El dropdown Estacion solo muestra "Jefe
# Sucursal" (=ISE, tu unica estacion convencional con jefatura) - ADA
# nunca aparece ahi (confirma CP030). La estacion ISE no tiene
# reclamos sin asignar ahora mismo -> "No se encontraron reclamos."

# CONFIRMADO EN VIVO 24/09/2026 (_exploracion/explore_50_cp029_sin_jefatura.py):
# usuario DCABA_DW (Michelle Kaori Alicie Manco Godinez) SI tiene acceso
# base a Reclamos Comerciales (el link "Asignacion De Reclamos" SI
# aparece en el menu - no cumple la alternativa "no aparece en el
# menu"), pero al abrir el popup el componente app-asignacion-de-reclamos
# muestra un candado con el mensaje real "No tiene perfil de jefe en
# ninguna estacion. Contacte al administrador." (misma redaccion que ya
# se via para SCASTI_DW antes de tener jefatura en ISE). El link
# "Salir" tiene 2 copias en el DOM (mismo patron de duplicado que el
# resto del menu) - usar la visible; abre un modal de confirmacion
# "Desea salir de la aplicacion? Si/No" antes de volver al form de
# login (la URL NO cambia, sigue en la misma SPA route - no usar
# "Login" in page.url como senal, esperar a que el campo Usuario
# reaparezca).

add("CP029", "pass", '''
candidatos_salir = page.locator("a, button").filter(has_text=re.compile(r"^\\s*Salir\\s*$"))
enlace_salir = None
for i in range(candidatos_salir.count()):
    if candidatos_salir.nth(i).is_visible():
        enlace_salir = candidatos_salir.nth(i)
        break
assert enlace_salir is not None, "No se encontro un enlace Salir visible"
capturar_paso(page, "sesion_scasti_dw", paso_excel=1)
enlace_salir.click()
page.wait_for_timeout(1000)
page.get_by_role("button", name=re.compile("^Si$", re.I)).click()
page.get_by_role("textbox", name="Usuario").wait_for(state="visible", timeout=15000)
page.get_by_role("textbox", name="Usuario").click()
page.get_by_role("textbox", name="Usuario").fill("DCABA_DW")
page.get_by_role("textbox", name="Usuario").press("Tab")
page.get_by_role("textbox", name="Contraseña").fill("Melquisedec_01")
page.wait_for_timeout(1000)
page.get_by_role("button", name="Ingresar ").click()
page.wait_for_load_state("networkidle", timeout=20000)
page.wait_for_timeout(1000)
capturar_paso(page, "sesion_dcaba_dw", paso_excel=1)
app, frame = abrir_asignacion(page, paso_excel=2)
capturar_paso(app, "acceso_sin_jefatura", paso_excel=3)
texto = frame.locator("body").inner_text()
assert "No tiene perfil de jefe" in texto, f"Se esperaba el mensaje de acceso denegado por falta de jefatura: {texto!r}"
''')

add("CP020", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
pestana_estructurado = frame.get_by_role("tab", name="Estructurado", exact=True)
pestana_ada = frame.get_by_role("tab", name="ADA", exact=True)
capturar_paso(app, "pantalla_cargada", paso_excel=3)
assert pestana_estructurado.count() == 1, "Deberia existir la pestana Estructurado"
assert pestana_ada.count() == 1, "Deberia existir la pestana ADA (aunque pueda estar deshabilitada por cache, ver docstring)"
dialogo_error = frame.get_by_text("No tiene perfil de jefe", exact=False)
assert dialogo_error.count() == 0, "No deberia aparecer el mensaje de acceso denegado para un jefe con estacion convencional"
''')

# CONFIRMADO EN VIVO 25/09/2026 (_exploracion/explore_92_ada_asignacion_y_ordenar.py,
# explore_94_ada_asignacion_dom_y_rango.py): el blocker de cache de ADA
# tambien se resolvio en Asignacion (aria-disabled paso de "true" a
# "false"). A diferencia de Reasignacion, esta pestana SI tiene Instancia
# + Desde/Hasta editables (type=date nativo, ISO) y boton Buscar - pero
# el rango se autocompleta ayer-hoy y la busqueda se dispara sola al
# entrar, sin pulsar Buscar. Con el rango automatico (y tambien con un
# rango ampliado 2000-01-01 a 2026-09-25) la grilla da "No se encontraron
# reclamos." - no hay NINGUN reclamo real sin asignar en la estacion ADA
# ahora mismo (a diferencia de Reasignacion, que si tiene 5 reales ya
# asignados) - CP039 (Exportar PDF con columnas propias de ADA) queda
# BLOQUEADO por esto: el boton quedo confirmado disabled="true" sin
# resultados (mismo patron que CP070), no se fuerza sin datos reales.

add("CP022", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
pestana_ada = frame.get_by_role("tab", name="ADA", exact=True)
assert pestana_ada.get_attribute("aria-disabled") == "false", "La pestana ADA deberia estar habilitada"
pestana_ada.click()
esperar_fin_de_carga(app, frame)
hoy = date.today()
ayer = hoy - timedelta(days=1)
campo_desde = frame.get_by_label(re.compile("^Desde$", re.I))
campo_hasta = frame.get_by_label(re.compile("^Hasta$", re.I))
capturar_paso(app, "rango_automatico", paso_excel=3)
assert campo_desde.input_value() == ayer.isoformat(), f"Desde deberia autocompletarse con ayer ({ayer.isoformat()}): {campo_desde.input_value()!r}"
assert campo_hasta.input_value() == hoy.isoformat(), f"Hasta deberia autocompletarse con hoy ({hoy.isoformat()}): {campo_hasta.input_value()!r}"
filas = frame.locator("table tbody tr")
filas.first.wait_for(state="visible", timeout=15000)
capturar_paso(app, "resultado_automatico", paso_excel=4)
assert filas.count() > 0, "La grilla deberia mostrar un resultado (con datos o el mensaje de vacio) sin pulsar Buscar"
''')

add("CP037", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
frame.get_by_role("tab", name="ADA", exact=True).click()
esperar_fin_de_carga(app, frame)
campo_ordenar = frame.get_by_label(re.compile("^Ordenar por$", re.I))
campo_ordenar.click()
app.wait_for_timeout(500)
capturar_paso(app, "combo_ordenar_por_abierto", paso_excel=3)
opciones = frame.locator("mat-option, .mat-mdc-option, [role='option']")
assert opciones.count() > 0, "Se esperaba al menos 1 opcion en Ordenar por"
for i in range(opciones.count()):
    texto_opcion = opciones.nth(i).inner_text().strip()
    assert texto_opcion != "Tipo de Reclamo", f"'Tipo de Reclamo' no deberia figurar en el desplegable de la pestana ADA: {texto_opcion!r}"
app.keyboard.press("Escape")
''')

add("CP040", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
assert frame.get_by_role("button", name="Buscar", exact=True).count() == 1, "La pestana ADA de Asignacion si deberia tener boton Buscar (a diferencia de Reasignacion)"
pestana_ada = frame.get_by_role("tab", name="ADA", exact=True)
pestana_ada.click()
filas = frame.locator("table tbody tr")
filas.first.wait_for(state="visible", timeout=20000)
capturar_paso(app, "ada_cargada_sin_pulsar_buscar", paso_excel=3)
assert filas.count() > 0, "La grilla ADA deberia mostrar un resultado automaticamente, sin que el usuario pulse Buscar"
''')

add("CP028", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
capturar_paso(app, "pantalla_cargada", paso_excel=3)
pestana_estructurado = frame.get_by_role("tab", name="Estructurado", exact=True)
pestana_ada = frame.get_by_role("tab", name="ADA", exact=True)
assert pestana_estructurado.is_visible(), "La pestana Estructurado deberia estar visible"
assert pestana_ada.is_visible(), "La pestana ADA deberia estar visible (aunque este deshabilitada por cache)"
''')

add("CP021", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 24/09/2026: la estacion ISE (Jefe Sucursal) SI
# tiene un reclamo real sin operador asignado (RE000430-ESC-2022) - no
# es el escenario "sin resultados" que se asumio al principio.
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_con_reclamos", paso_excel=4)
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 reclamo real sin asignar en la estacion ISE"
''')

# EJECUTADO EN VIVO 24/09/2026 CON CONFIRMACION EXPLICITA DEL USUARIO
# (escritura real e irreversible, autorizada tras preguntar). Operadores
# reales de la estacion ISE (modal Seleccion de Operador): CSU (Claudia
# Suarez, x2 filas duplicadas + una fila "[OPERADOR]"), HTA (Hugo
# Tenorio Alarcon), MSBA (Manuel Sotil Bartra), SCAZ (Sergio Castillon -
# el propio SCASTI_DW), VOCH (Vanessa Cueva). Se eligio HTA (0 reclamos
# pendientes en ese momento) para no auto-asignarse. Ejecutado y
# confirmado exitoso via _exploracion/explore_47_cp025_ejecutar_real.py
# (evidencia en _exploracion/dump/47a-47e*.png): dialogo real "Se
# asignaron 1 reclamo(s) al operador HTA en la estacion JDS." y la
# grilla de ISE quedo vacia ("No se encontraron reclamos.") tras
# re-buscar. IMPORTANTE: esto consume el UNICO reclamo real sin asignar
# que tenia ISE (RE000430-ESC-2022) - CP021 (que asume "al menos 1
# reclamo sin asignar en ISE") FALLARA en una proxima corrida hasta que
# aparezca un reclamo nuevo sin asignar en esa estacion. El paso 6 de la
# matriz (verificar en "Mis Reclamos" con la sesion del operador HTA)
# NO se pudo validar - no se cuenta con credenciales de ese usuario.

add("CP025", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
filas_antes = frame.locator("table tbody tr")
capturar_paso(app, "reclamo_sin_asignar", paso_excel=3)
assert filas_antes.count() > 0, "Se esperaba al menos 1 reclamo real sin asignar en la estacion ISE"
checkbox_fila = frame.locator("table tbody tr mat-checkbox").first
checkbox_fila.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Asignar seleccionados")).click()
app.wait_for_timeout(1000)
fila_operador = frame.get_by_text("HUGO TENORIO ALARCON", exact=True)
fila_operador.wait_for(state="visible", timeout=15000)
capturar_paso(app, "modal_operadores", paso_excel=4)
fila_operador.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name="Seleccionar", exact=True).click()
app.wait_for_timeout(2000)
capturar_paso(app, "confirmacion_asignacion", paso_excel=5)
mensaje = frame.get_by_text(re.compile(r"Se asignaron \\d+ reclamo\\(s\\) al operador", re.I))
mensaje.wait_for(state="visible", timeout=10000)
frame.locator("app-alert").get_by_role("button", name="Aceptar", exact=True).click()
app.wait_for_timeout(1000)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "grilla_actualizada", paso_excel=6)
filas_despues = frame.locator("table tbody tr")
mensaje_vacio = frame.get_by_text("No se encontraron reclamos.", exact=True)
assert mensaje_vacio.count() > 0 or filas_despues.count() < filas_antes.count(), "El reclamo asignado deberia desaparecer de la grilla de sin-asignar"
''')

add("CP030", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
campo_estacion = frame.locator("mat-select").first
campo_estacion.click()
app.wait_for_timeout(500)
capturar_paso(app, "combo_estacion_abierto", paso_excel=3)
opciones = frame.locator("mat-option, .mat-mdc-option, [role='option']")
assert opciones.count() > 0, "Se esperaba al menos 1 estacion convencional en el combo"
for i in range(opciones.count()):
    texto_opcion = opciones.nth(i).inner_text().upper()
    assert texto_opcion != "ADA", f"ADA no deberia figurar en el desplegable de la pestana Estructurado: {texto_opcion!r}"
app.keyboard.press("Escape")
''')

# CONFIRMADO EN VIVO 24/09/2026 (_exploracion/explore_32_casos_restantes.py):
# antes de pulsar Buscar la grilla de Estructurado muestra literalmente
# "No se encontraron reclamos." (CP041) y no aparece ningun dialogo/toast
# extra al buscar (CP035 - "transparente para el jefe" se cumple).

add("CP041", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
mensaje_vacio = frame.get_by_text("No se encontraron reclamos.", exact=True)
mensaje_vacio.wait_for(state="visible", timeout=10000)
capturar_paso(app, "grilla_vacia_antes_de_buscar", paso_excel=3)
filas = frame.locator("table tbody tr")
assert filas.count() <= 1, f"La grilla no deberia tener reclamos reales antes de pulsar Buscar: {filas.count()} filas"
''')

add("CP035", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
dialogos = []
app.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_sin_avisos", paso_excel=4)
assert dialogos == [], f"No deberia aparecer ningun dialogo nativo al cargar los reclamos: {dialogos}"
aviso_registro = frame.get_by_text(re.compile("registro de apertura", re.I))
assert aviso_registro.count() == 0, "No deberia aparecer ningun aviso relacionado con el registro de apertura"
''')

add("CP042", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 24/09/2026: Exportar PDF con la estacion ISE
# seleccionada y busqueda aplicada descarga "Reclamos_Estructurado_<fecha>.pdf".
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "filtros_aplicados", paso_excel=3)
with app.expect_download(timeout=10000) as info_descarga:
    frame.get_by_role("button", name=re.compile("Exportar", re.I)).click()
descarga = info_descarga.value
capturar_paso(app, "pdf_exportado", paso_excel=4)
assert descarga.suggested_filename.lower().endswith(".pdf"), f"Se esperaba un PDF, se descargo: {descarga.suggested_filename!r}"
''')


# ===========================================================================
# RF-03: Reasignacion De Reclamos
# ===========================================================================
# Mismo patron que RF-02 (misma jefatura ISE, mismo problema de cache
# con ADA). A diferencia de RF-02, la pestana Estructurado de RF-03 NO
# tiene el campo Instancia (confirmado por EF: "Estacion, Ordenar por,
# Desde y Hasta" solamente).

add("CP045", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
pestana_estructurado = frame.get_by_role("tab", name="Estructurado", exact=True)
pestana_ada = frame.get_by_role("tab", name="ADA", exact=True)
capturar_paso(app, "pantalla_cargada", paso_excel=3)
assert pestana_estructurado.count() == 1, "Deberia existir la pestana Estructurado"
assert pestana_ada.count() == 1, "Deberia existir la pestana ADA"
dialogo_error = frame.get_by_text("No tiene perfil de jefe", exact=False)
assert dialogo_error.count() == 0, "No deberia aparecer el mensaje de acceso denegado para un jefe con estacion convencional"
''')

add("CP053", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
campo_estacion = frame.locator("mat-select").first
campo_estacion.click()
app.wait_for_timeout(500)
capturar_paso(app, "combo_estacion_abierto", paso_excel=3)
opciones = frame.locator("mat-option, .mat-mdc-option, [role='option']")
assert opciones.count() > 0, "Se esperaba al menos 1 estacion convencional en el combo"
for i in range(opciones.count()):
    texto_opcion = opciones.nth(i).inner_text().upper()
    assert texto_opcion != "ADA", f"ADA no deberia figurar en el desplegable de la pestana Estructurado: {texto_opcion!r}"
app.keyboard.press("Escape")
''')

add("CP056", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 24/09/2026: la estacion ISE (Jefe Sucursal) SI
# tiene reclamos reales ya asignados en proceso (RCL-0035331,
# RCL-0058715) - no es el escenario "sin resultados" que se asumio.
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_con_reclamos", paso_excel=4)
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "Se esperaba al menos 1 reclamo real asignado en la estacion ISE"
''')

add("CP070", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 24/09/2026: ISE siempre tiene reclamos reales, asi
# que para el escenario "sin resultados" hace falta un rango de fechas
# realmente vacio (mismo patron que CP100 de RF-05: un rango antiguo
# sin actividad, 1990).
campo_desde = frame.get_by_label(re.compile("^Desde$", re.I))
campo_hasta = frame.get_by_label(re.compile("^Hasta$", re.I))
campo_desde.fill("1990-01-01")
campo_hasta.fill("1990-01-02")
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_sin_reclamos", paso_excel=4)
filas = frame.locator("table tbody tr")
boton_pdf = frame.get_by_role("button", name="Exportar PDF", exact=True)
assert boton_pdf.is_disabled(), "Exportar PDF deberia estar deshabilitado sin resultados"
''')

# CONFIRMADO EN VIVO 24/09/2026 (_exploracion/explore_32_casos_restantes.py):
# - Sin fechas la estacion ISE trae los 2 reclamos reales conocidos
#   (RCL-0035331, RCL-0058715); con el mismo rango 01/09-24/09/2026 del
#   proyecto siguen apareciendo ambos (caen dentro del rango).
# - La pestana Estructurado de Reasignacion NO tiene campo Instancia
#   (labels reales: Estacion, Ordenar por, Desde, Hasta) - confirma lo
#   que ya decia el docstring de la seccion.
# - Ordenar por "N Reclamo" deja la grilla ascendente por codigo.
# - Exportar PDF descarga "Reclamos_Estructurado_<fecha>.pdf" igual que
#   en Asignacion.
# - Ningun dialogo/aviso nativo aparece al buscar (CP066, analogo a CP035).
# - El modal que abre "Reasignar seleccionados" se llama "Seleccion de
#   Operador" y tiene boton "Cancelar" real (ademas de "Seleccionar" para
#   confirmar) - cancelar no deja cambios, mismo patron que CP026/CP064.

add("CP046", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 08/10/2026 (_exploracion/explore_157_cp046_filtro_fechas.py,
# capturando la respuesta real de ListarReclamosParaReasignar): el filtro
# de fechas SI funciona correctamente (filtra por F. Registro real) - la
# estacion por defecto ("Coordinación Reclamos") trae reclamos reales con
# fechas desde 2004 hasta hoy, y un rango 1990-2026 los cubre a TODOS por
# igual (de ahi que antes pareciera "igual sin filtrar", quedo confirmado
# que es el comportamiento correcto, no un bug). Patron de codigo
# ampliado (RCL-/RE.../REC...) aplicado consistente en las 3 comparaciones,
# mismo fix que CP038/CP068.
patron_codigo = re.compile(r"\\b(?:RCL-\\d+|RE[A-Z]?\\d+-[A-Z]+-\\d{4})\\b")
capturar_paso(app, "antes_de_buscar_sin_fechas", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_sin_fechas", paso_excel=3)
codigos_sin_fechas = set(patron_codigo.findall(frame.locator("table tbody").inner_text()))
assert len(codigos_sin_fechas) > 0, "Se esperaba al menos 1 reclamo real sin filtrar por fechas"
campo_desde = frame.get_by_label(re.compile("^Desde$", re.I))
campo_hasta = frame.get_by_label(re.compile("^Hasta$", re.I))
campo_desde.fill("1990-01-01")
campo_hasta.fill("2026-09-24")
capturar_paso(app, "antes_de_buscar_rango_amplio", paso_excel=5)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_rango_amplio", paso_excel=6)
codigos_rango_amplio = set(patron_codigo.findall(frame.locator("table tbody").inner_text()))
assert codigos_rango_amplio == codigos_sin_fechas, f"Con un rango que cubre 1990-2026 deberian seguir los mismos reclamos: {codigos_rango_amplio} vs {codigos_sin_fechas}"
campo_desde.fill("2020-01-01")
campo_hasta.fill("2026-09-24")
capturar_paso(app, "antes_de_buscar_rango_reciente", paso_excel=5)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_rango_reciente_sin_datos", paso_excel=6)
# CONFIRMADO EN VIVO 08/10/2026: con la estacion por defecto, un rango
# 2020-2026 NO da vacio (SI hay reclamos reales de 2021/2022) - el
# assert original asumia "vacio" porque se escribio pensando solo en los
# 2 reclamos viejos de ISE (2001/2003). Tampoco sirve comparar el SET
# COMPLETO contra "sin fechas": la grilla pagina a 10 filas, asi que al
# excluirse los viejos del lado del servidor, otros reclamos recientes
# que antes estaban en la pagina 2 entran a la pagina 1 y rompen una
# comparacion de conjuntos completos (confirmado en vivo con una corrida
# real: mismo tamaño 10 en ambos casos, pero no exactamente el mismo
# conjunto, por pura paginacion). Chequeo robusto: los 2 reclamos viejos
# conocidos (RCL-0083049/2004, REC07137-ESC-2019) NO deben aparecer en
# el rango reciente, sin importar paginacion del resto.
codigos_rango_reciente = set(patron_codigo.findall(frame.locator("table tbody").inner_text()))
assert len(codigos_rango_reciente) > 0, "Se esperaba al menos 1 reclamo real en el rango reciente (2020-2026)"
codigos_viejos_conocidos = {"RCL-0083049", "REC07137-ESC-2019"}
interseccion = codigos_rango_reciente & codigos_viejos_conocidos
assert not interseccion, f"El rango reciente (2020-2026) no deberia incluir estos reclamos viejos: {interseccion}"
''')

add("CP048", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
campo_ordenar = frame.get_by_label(re.compile("^Ordenar por$", re.I))
campo_ordenar.click()
app.wait_for_timeout(500)
frame.get_by_role("option", name=re.compile(r"N.\\s?Reclamo", re.I)).click()
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_ordenado", paso_excel=4)
# CONFIRMADO EN VIVO 08/10/2026: patron ampliado, ver nota en CP038.
patron_codigo = re.compile(r"\\b(?:RCL-\\d+|RE[A-Z]?\\d+-[A-Z]+-\\d{4})\\b")
codigos = patron_codigo.findall(frame.locator("table tbody").inner_text())
assert len(codigos) > 0, "Se esperaba al menos 1 reclamo real"
assert codigos == sorted(codigos), f"La grilla deberia quedar ordenada ascendente por N Reclamo: {codigos}"
''')

add("CP052", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "listado_cargado", paso_excel=3)
with app.expect_download(timeout=10000) as info_descarga:
    frame.get_by_role("button", name=re.compile("Exportar", re.I)).click()
descarga = info_descarga.value
capturar_paso(app, "pdf_exportado", paso_excel=4)
assert descarga.suggested_filename.lower().endswith(".pdf"), f"Se esperaba un PDF, se descargo: {descarga.suggested_filename!r}"
''')

add("CP055", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
capturar_paso(app, "panel_de_filtros", paso_excel=3)
campo_instancia = frame.get_by_label(re.compile("^Instancia$", re.I))
assert campo_instancia.count() == 0, "La pestana Estructurado de Reasignacion no deberia tener campo Instancia"
assert frame.get_by_label(re.compile("^Estaci", re.I)).count() > 0, "Deberia existir el campo Estacion"
assert frame.get_by_label(re.compile("^Ordenar por$", re.I)).count() > 0, "Deberia existir el campo Ordenar por"
assert frame.get_by_label(re.compile("^Desde$", re.I)).count() > 0, "Deberia existir el campo Desde"
assert frame.get_by_label(re.compile("^Hasta$", re.I)).count() > 0, "Deberia existir el campo Hasta"
''')

add("CP066", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
dialogos = []
app.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_sin_avisos", paso_excel=4)
assert dialogos == [], f"No deberia aparecer ningun dialogo nativo al cargar los reclamos: {dialogos}"
aviso_registro = frame.get_by_text(re.compile("registro de apertura", re.I))
assert aviso_registro.count() == 0, "No deberia aparecer ningun aviso relacionado con el registro de apertura"
''')

add("CP058", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 24/09/2026 (_exploracion/explore_34_estilo_dias_negativos.py):
# los 2 reclamos reales de ISE estan vencidos hace anios (dias rest.
# -6608 / -6106) y las celdas de Dias Rest. Total/Est. tienen la clase
# CSS real "vencido" (ademas de "is-center col-dias") - esa clase es la
# que aplica el rojo/negrita via CSS, no un estilo inline.
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_con_reclamos", paso_excel=3)
celdas_vencido = frame.locator("table tbody tr td.vencido")
assert celdas_vencido.count() > 0, "Se esperaba al menos 1 celda de dias restantes con la clase 'vencido'"
for i in range(celdas_vencido.count()):
    texto_celda = celdas_vencido.nth(i).inner_text().strip()
    assert texto_celda.startswith("-"), f"La celda marcada como vencido deberia mostrar un valor negativo: {texto_celda!r}"
capturar_paso(app, "dias_vencidos_resaltados", paso_excel=4)
''')

add("CP065", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
checkbox_fila = frame.locator("table tbody tr mat-checkbox").first
checkbox_fila.click()
app.wait_for_timeout(500)
capturar_paso(app, "antes_de_abrir_modal", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Reasignar seleccionados")).click()
app.wait_for_timeout(1000)
capturar_paso(app, "modal_abierto", paso_excel=4)
texto_modal = frame.locator("body").inner_text().lower()
assert "operador" in texto_modal, f"Se esperaba el modal Seleccion de Operador, texto visible: {texto_modal[:300]!r}"
frame.get_by_role("button", name="Cancelar", exact=True).click()
app.wait_for_timeout(1000)
capturar_paso(app, "modal_cancelado", paso_excel=5)
boton_reasignar = frame.get_by_role("button", name=re.compile(r"Reasignar seleccionados"))
assert "1" in boton_reasignar.inner_text(), "La seleccion original deberia seguir intacta tras cancelar el modal"
''')

# CONFIRMADO EN VIVO 25/09/2026 (_exploracion/explore_91_ada_reasignacion.py,
# explore_92_ada_asignacion_y_ordenar.py, explore_93_dom_panel_ada_reasignacion.py):
# el bloqueo de cache de la pestana ADA quedo RESUELTO (aria-disabled paso
# de "true" a "false") - se confirmo con 5 reclamos reales ya asignados
# cargados automaticamente (REC00999-WEB-2009, REC00001-TEL-,
# RE002917-ESC-2026, RE005999-ESC-2026, RE006654-WEB-2026, todos vencidos
# hace anios). El panel de filtros de ADA (Reasignacion) solo tiene 2
# campos: Estacion (input readonly, aria-label real "Estacion (fija en
# ADA)", valor fijo "ADA") y Ordenar por (mat-select, mismas 4 opciones que
# Estructurado: Dias Rest. Total/Dias Rest. Estacion/N Reclamo/Tipo
# Cliente, sin "Tipo de Reclamo"). No hay boton Buscar en ADA (solo
# Recargar/Limpiar/Exportar PDF/Reasignar seleccionados) - los reclamos
# cargan solos al entrar a la pestana.

add("CP047", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
pestana_ada = frame.get_by_role("tab", name="ADA", exact=True)
assert pestana_ada.get_attribute("aria-disabled") == "false", "La pestana ADA deberia estar habilitada"
pestana_ada.click()
esperar_fin_de_carga(app, frame)
assert frame.get_by_role("button", name="Buscar", exact=True).count() == 0, "La pestana ADA no deberia tener boton Buscar"
filas = frame.locator("table tbody tr")
filas.first.wait_for(state="visible", timeout=15000)
capturar_paso(app, "ada_cargada_automaticamente", paso_excel=3)
assert filas.count() > 0, "Se esperaba que la grilla ADA cargue reclamos reales automaticamente, sin pulsar ningun boton"
''')

add("CP054", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("tab", name="ADA", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "panel_de_filtros_ada", paso_excel=3)
assert frame.get_by_label(re.compile("^Instancia$", re.I)).count() == 0, "La pestana ADA no deberia tener campo Instancia"
assert frame.get_by_label(re.compile("^Desde$", re.I)).count() == 0, "La pestana ADA no deberia tener campo Desde"
assert frame.get_by_label(re.compile("^Hasta$", re.I)).count() == 0, "La pestana ADA no deberia tener campo Hasta"
campo_estacion = frame.get_by_label(re.compile(r"^Estaci.n \\(fija en ADA\\)$", re.I))
assert campo_estacion.count() == 1, "Deberia existir el campo Estacion fijo en ADA"
assert campo_estacion.get_attribute("readonly") is not None, "El campo Estacion deberia ser de solo lectura"
assert campo_estacion.input_value() == "ADA", f"El campo Estacion deberia mostrar el valor fijo ADA: {campo_estacion.input_value()!r}"
assert frame.get_by_label(re.compile("^Ordenar por$", re.I)).count() == 1, "Deberia existir el campo Ordenar por"
''')

add("CP067", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("tab", name="ADA", exact=True).click()
esperar_fin_de_carga(app, frame)
campo_ordenar = frame.get_by_label(re.compile("^Ordenar por$", re.I))
campo_ordenar.click()
app.wait_for_timeout(500)
capturar_paso(app, "combo_ordenar_por_abierto", paso_excel=3)
opciones = frame.locator("mat-option, .mat-mdc-option, [role='option']")
assert opciones.count() > 0, "Se esperaba al menos 1 opcion en Ordenar por"
for i in range(opciones.count()):
    texto_opcion = opciones.nth(i).inner_text().strip()
    assert texto_opcion != "Tipo de Reclamo", f"'Tipo de Reclamo' no deberia figurar en el desplegable de la pestana ADA: {texto_opcion!r}"
app.keyboard.press("Escape")
''')

add("CP069", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("tab", name="ADA", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
capturar_paso(app, "listado_ada_cargado", paso_excel=3)
with app.expect_download(timeout=10000) as info_descarga:
    frame.get_by_role("button", name=re.compile("Exportar", re.I)).click()
descarga = info_descarga.value
capturar_paso(app, "pdf_exportado", paso_excel=4)
assert descarga.suggested_filename.lower().endswith(".pdf"), f"Se esperaba un PDF, se descargo: {descarga.suggested_filename!r}"
''')


add("CP024", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
boton_asignar = frame.get_by_role("button", name=re.compile(r"Asignar seleccionados"))
assert boton_asignar.is_disabled(), "Asignar deberia estar deshabilitado sin ninguna fila marcada"
capturar_paso(app, "antes_de_marcar", paso_excel=3)
checkbox_fila = frame.locator("table tbody tr").first.locator("input[type='checkbox'], mat-checkbox")
checkbox_fila.first.click()
app.wait_for_timeout(500)
capturar_paso(app, "fila_marcada", paso_excel=4)
assert boton_asignar.is_enabled(), "Asignar deberia habilitarse con al menos 1 fila marcada"
assert "1" in boton_asignar.inner_text(), f"El contador deberia mostrar 1, boton: {boton_asignar.inner_text()!r}"
''')

add("CP026", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
filas_antes = frame.locator("table tbody tr").count()
checkbox_fila = frame.locator("table tbody tr").first.locator("input[type='checkbox'], mat-checkbox")
checkbox_fila.first.click()
app.wait_for_timeout(500)
capturar_paso(app, "antes_de_asignar", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Asignar seleccionados")).click()
app.wait_for_timeout(1000)
capturar_paso(app, "modal_abierto", paso_excel=4)
frame.get_by_role("button", name="Cancelar", exact=True).click()
app.wait_for_timeout(1000)
capturar_paso(app, "modal_cancelado", paso_excel=5)
filas_despues = frame.locator("table tbody tr").count()
assert filas_despues == filas_antes, "Los reclamos deberian seguir en la grilla tras cancelar"
''')

add("CP049", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
boton_reasignar = frame.get_by_role("button", name=re.compile(r"Reasignar seleccionados"))
assert boton_reasignar.is_disabled(), "Reasignar deberia estar deshabilitado sin ninguna fila marcada"
capturar_paso(app, "antes_de_marcar", paso_excel=3)
checkbox_fila = frame.locator("table tbody tr").first.locator("input[type='checkbox'], mat-checkbox")
checkbox_fila.first.click()
app.wait_for_timeout(500)
capturar_paso(app, "fila_marcada", paso_excel=4)
assert boton_reasignar.is_enabled(), "Reasignar deberia habilitarse con al menos 1 fila marcada"
assert "1" in boton_reasignar.inner_text(), f"El contador deberia mostrar 1, boton: {boton_reasignar.inner_text()!r}"
''')

# EJECUTADO EN VIVO 24/09/2026 CON CONFIRMACION EXPLICITA DEL USUARIO
# (escritura real e irreversible, autorizada tras preguntar, mismo dia
# que CP025). Se reasigno RCL-0035331 (estacion ISE) de su operador
# original a MSBA (Manuel Sotil Bartra, 0 reclamos pendientes en ese
# momento - se evito elegir HTA porque ya tenia el reclamo de CP025).
# Ejecutado y confirmado exitoso via
# _exploracion/explore_49_cp050_ejecutar_real2.py (evidencia en
# _exploracion/dump/49a-49e*.png): dialogo real "Se reasignaron 1
# reclamo(s) al operador MSBA en estacion JDS." y el historial de
# Seguimiento en Consulta del Reclamo (RCL-0035331) SI registra un
# movimiento con "REASIGNADO" tras la reasignacion - confirmado
# buscando el texto en la pantalla completa (ver
# _exploracion/dump/49e_historial_consulta.png). NO se encadeno esa
# verificacion dentro del cuerpo del caso: reabrir "Aplicaciones" en el
# mismo `page` cuando el arbol de menu ya quedo expandido por
# abrir_reasignacion() lo COLAPSA en vez de reabrirlo (toggle), y
# _click_visible("Comercial") revienta porque ya no esta visible - bug
# de encadenar 2 abrir_aplicacion() sobre el mismo `page`, no probado
# en ningun otro caso del proyecto. El caso se deja solo con lo que SI
# se puede verificar de forma confiable dentro de Reasignacion. A
# diferencia de CP025, el
# reclamo reasignado SIGUE apareciendo en la grilla de Reasignacion
# (que lista todos los asignados de la estacion, no solo los de "mi"
# operador), asi que no hace falta re-sembrar nada para volver a correr
# casos de solo-lectura sobre RCL-0035331/RCL-0058715 en esta estacion.

add("CP050", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 08/10/2026: la estacion por defecto de esta
# pantalla ya NO es "Jefe Sucursal" (cambio de la jefatura de SCAZ en
# csc_rolxest, pendiente de restaurar - ver memoria del proyecto), asi
# que hay que seleccionarla a mano para seguir viendo RCL-0035331.
campo_estacion = frame.locator("mat-select").first
campo_estacion.click()
app.wait_for_timeout(500)
frame.get_by_role("option", name=re.compile("Sucursal", re.I)).click()
app.wait_for_timeout(500)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
fila_objetivo = frame.locator("table tbody tr", has_text="RCL-0035331")
fila_objetivo.wait_for(state="visible", timeout=15000)
capturar_paso(app, "reclamo_a_reasignar", paso_excel=3)
checkbox_fila = fila_objetivo.locator("mat-checkbox")
checkbox_fila.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Reasignar seleccionados")).click()
app.wait_for_timeout(1000)
fila_operador = frame.get_by_text("MANUEL SOTIL BARTRA", exact=True)
fila_operador.wait_for(state="visible", timeout=15000)
capturar_paso(app, "modal_operadores", paso_excel=4)
fila_operador.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name="Seleccionar", exact=True).click()
app.wait_for_timeout(2000)
capturar_paso(app, "confirmacion_reasignacion", paso_excel=5)
mensaje = frame.get_by_text(re.compile(r"Se reasignaron \\d+ reclamo\\(s\\) al operador", re.I))
mensaje.wait_for(state="visible", timeout=10000)
frame.locator("app-alert").get_by_role("button", name="Aceptar", exact=True).click()
app.wait_for_timeout(1000)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "grilla_actualizada", paso_excel=6)
''')

add("CP051", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
# CONFIRMADO EN VIVO 08/10/2026: patron ampliado, ver nota en CP038.
patron_codigo = re.compile(r"\\b(?:RCL-\\d+|RE[A-Z]?\\d+-[A-Z]+-\\d{4})\\b")
codigos_antes = set()
for _ in range(20):
    codigos_antes = set(patron_codigo.findall(frame.locator("table tbody").first.inner_text()))
    if codigos_antes:
        break
    app.wait_for_timeout(1000)
assert len(codigos_antes) > 0, "Se esperaba al menos 1 codigo de reclamo real antes de cancelar"
checkbox_fila = frame.locator("table tbody tr").first.locator("input[type='checkbox'], mat-checkbox")
checkbox_fila.first.click()
app.wait_for_timeout(500)
capturar_paso(app, "antes_de_reasignar", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Reasignar seleccionados")).click()
app.wait_for_timeout(1000)
capturar_paso(app, "modal_abierto", paso_excel=4)
frame.get_by_role("button", name="Cancelar", exact=True).click()
app.wait_for_timeout(1000)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "modal_cancelado", paso_excel=5)
codigos_despues = set(patron_codigo.findall(frame.locator("table tbody").first.inner_text()))
assert codigos_despues == codigos_antes, f"Los mismos reclamos deberian seguir en la grilla tras cancelar (antes={{codigos_antes}}, despues={{codigos_despues}})"
''')

add("CP059", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
capturar_paso(app, "sin_seleccion", paso_excel=3)
boton_reasignar = frame.get_by_role("button", name=re.compile(r"Reasignar seleccionados"))
assert boton_reasignar.is_disabled(), "Reasignar deberia estar deshabilitado sin seleccion"
''')


add("CP031", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
capturar_paso(app, "grilla_cargada", paso_excel=3)
primera_fila = frame.locator("table tbody tr").first
celda_semaforo_html = primera_fila.locator("td").nth(1).inner_html()
assert celda_semaforo_html.count("span") >= 2 or celda_semaforo_html.lower().count("circle") >= 2, f"Se esperaban 2 circulos de color en la celda de Semaforo: {celda_semaforo_html!r}"
''')

add("CP027", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
capturar_paso(app, "antes_de_exportar", paso_excel=3)
with app.expect_download(timeout=15000) as descarga_info:
    frame.get_by_role("button", name="Exportar PDF", exact=True).click()
descarga = descarga_info.value
ruta_descarga = EVIDENCIA / f"{CASO}_listado.pdf"
descarga.save_as(str(ruta_descarga))
capturar_paso(app, "pdf_descargado", paso_excel=4)
assert ruta_descarga.exists() and ruta_descarga.stat().st_size > 0, "El PDF exportado deberia existir y no estar vacio"
''')

add("CP033", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
checkbox_fila = frame.locator("table tbody tr").first.locator("input[type='checkbox'], mat-checkbox")
checkbox_fila.first.click()
app.wait_for_timeout(500)
capturar_paso(app, "fila_marcada", paso_excel=3)
boton_asignar = frame.get_by_role("button", name=re.compile(r"Asignar seleccionados"))
assert boton_asignar.is_enabled(), "Deberia haber quedado 1 fila marcada antes de cambiar el filtro"
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(500)
capturar_paso(app, "tras_nueva_busqueda", paso_excel=4)
assert boton_asignar.is_disabled(), "La seleccion previa deberia limpiarse al volver a buscar"
''')

add("CP057", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
capturar_paso(app, "grilla_cargada", paso_excel=3)
primera_fila = frame.locator("table tbody tr").first
celda_semaforo_html = primera_fila.locator("td").nth(1).inner_html()
assert celda_semaforo_html.count("span") >= 2 or celda_semaforo_html.lower().count("circle") >= 2, f"Se esperaban 2 circulos de color en la celda de Semaforo: {celda_semaforo_html!r}"
''')

add("CP060", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO: la estacion ISE tiene 2 reclamos reales
# (RCL-0035331, RCL-0058715), no 3 como sugiere el ejemplo de la
# matriz - se adapta el mismo comportamiento con 2: marcar ambos
# (contador a 2), desmarcar 1 (contador a 1).
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
checkboxes = frame.locator("table tbody tr mat-checkbox")
boton_reasignar = frame.get_by_role("button", name=re.compile(r"Reasignar seleccionados"))
checkboxes.nth(0).click()
app.wait_for_timeout(400)
checkboxes.nth(1).click()
app.wait_for_timeout(400)
capturar_paso(app, "dos_marcados", paso_excel=3)
assert "2" in boton_reasignar.inner_text(), f"Contador deberia mostrar 2: {boton_reasignar.inner_text()!r}"
checkboxes.nth(0).click()
app.wait_for_timeout(400)
capturar_paso(app, "uno_desmarcado", paso_excel=4)
assert "1" in boton_reasignar.inner_text(), f"Contador deberia mostrar 1: {boton_reasignar.inner_text()!r}"
''')

add("CP061", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
app.wait_for_timeout(1500)
capturar_paso(app, "antes_de_marcar_todos", paso_excel=3)
checkbox_encabezado = frame.locator("thead").get_by_role("checkbox").first
if checkbox_encabezado.count() == 0:
    checkbox_encabezado = frame.locator("thead input[type='checkbox']").first
checkbox_encabezado.click()
app.wait_for_timeout(500)
capturar_paso(app, "todos_marcados", paso_excel=4)
total_filas = frame.locator("table tbody tr").count()
boton_reasignar = frame.get_by_role("button", name=re.compile(r"Reasignar seleccionados"))
assert str(total_filas) in boton_reasignar.inner_text(), f"El contador deberia reflejar el total de filas ({total_filas}): {boton_reasignar.inner_text()!r}"
''')

add("CP062", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
checkbox_encabezado = frame.locator("thead").get_by_role("checkbox").first
if checkbox_encabezado.count() == 0:
    checkbox_encabezado = frame.locator("thead input[type='checkbox']").first
checkbox_encabezado.click()
app.wait_for_timeout(500)
capturar_paso(app, "todos_marcados", paso_excel=3)
checkbox_encabezado.click()
app.wait_for_timeout(500)
capturar_paso(app, "todos_desmarcados", paso_excel=4)
boton_reasignar = frame.get_by_role("button", name=re.compile(r"Reasignar seleccionados"))
assert boton_reasignar.is_disabled(), "Reasignar deberia quedar deshabilitado tras desmarcar todos desde el encabezado"
''')

add("CP063", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
checkbox_fila = frame.locator("table tbody tr").first.locator("input[type='checkbox'], mat-checkbox")
checkbox_fila.first.click()
app.wait_for_timeout(500)
capturar_paso(app, "fila_marcada", paso_excel=3)
boton_reasignar = frame.get_by_role("button", name=re.compile(r"Reasignar seleccionados"))
assert boton_reasignar.is_enabled(), "Deberia haber quedado 1 fila marcada antes de cambiar el filtro"
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(500)
capturar_paso(app, "tras_nueva_busqueda", paso_excel=4)
assert boton_reasignar.is_disabled(), "La seleccion previa deberia limpiarse al volver a buscar"
''')

add("CP064", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
checkbox_fila = frame.locator("table tbody tr").first.locator("input[type='checkbox'], mat-checkbox")
checkbox_fila.first.click()
app.wait_for_timeout(500)
capturar_paso(app, "antes_de_reasignar", paso_excel=3)
frame.get_by_role("button", name=re.compile(r"Reasignar seleccionados")).click()
app.wait_for_timeout(1000)
capturar_paso(app, "modal_selector_operadores", paso_excel=4)
texto_modal = frame.locator("body").inner_text().lower()
assert "operador" in texto_modal, f"Se esperaba el modal Selector de Operadores, texto visible: {texto_modal[:300]!r}"
frame.get_by_role("button", name="Cancelar", exact=True).click()
''')


# CONFIRMADO EN VIVO 24/09/2026: el doble clic en una fila de
# Asignacion/Reasignacion NO abre un popup nuevo (a diferencia de lo
# que se penso para CP103 de RF-05/Busqueda) - navega DENTRO DEL MISMO
# frame/popup a la Consulta del Reclamo. En RF-03 (2 reclamos reales)
# ademas trae el contexto "Anterior/Siguiente" poblado (1 de 2).

add("CP038", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 08/10/2026: la estacion por defecto ("Coordinación
# Reclamos") muestra reclamos LEGACY formato "RCL-NNNNNNN" (ej.
# RCL-0082942), no el formato "RE...-TIPO-AAAA" que se asumio al
# escribir este caso (valido en ese momento con otra estacion/dataset).
# El patron se amplia para cubrir ambos formatos reales vistos, y se
# recorre TODA la grilla (no solo la 1ra fila) por si la fila 0
# justo no matchea pero otra si.
patron_codigo = re.compile(r"\\b(?:RCL-\\d+|RE[A-Z]?\\d+-[A-Z]+-\\d{4})\\b")
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
fila_objetivo = None
codigo_esperado = None
for _ in range(20):
    filas_candidatas = frame.locator("table tbody tr")
    for i in range(filas_candidatas.count()):
        m = patron_codigo.search(filas_candidatas.nth(i).inner_text())
        if m:
            fila_objetivo = filas_candidatas.nth(i)
            codigo_esperado = m.group()
            break
    if fila_objetivo:
        break
    app.wait_for_timeout(1000)
assert fila_objetivo, "Se esperaba al menos 1 reclamo real con codigo en la grilla"
capturar_paso(app, "antes_de_doble_clic", paso_excel=3)
fila_objetivo.dblclick()
app.wait_for_timeout(1500)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "consulta_abierta", paso_excel=4)
frame.locator("app-consulta-del-reclamo").wait_for(timeout=15000)
assert codigo_esperado in frame.locator("body").inner_text(), f"Se esperaba ver el codigo {codigo_esperado!r} en la Consulta del Reclamo"
''')

add("CP068", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 08/10/2026: ver nota en CP038 - la estacion por
# defecto trae una mezcla de formatos de codigo (RCL-NNNNNNN, y
# tambien RE.../REC...-TIPO-AAAA), no solo "RCL-". Mismo fix: patron
# ampliado + recorrer toda la grilla, no solo la 1ra fila.
patron_codigo = re.compile(r"\\b(?:RCL-\\d+|RE[A-Z]?\\d+-[A-Z]+-\\d{4})\\b")
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
fila_objetivo = None
codigo_esperado = None
for _ in range(20):
    filas_candidatas = frame.locator("table tbody tr")
    for i in range(filas_candidatas.count()):
        m = patron_codigo.search(filas_candidatas.nth(i).inner_text())
        if m:
            fila_objetivo = filas_candidatas.nth(i)
            codigo_esperado = m.group()
            break
    if fila_objetivo:
        break
    app.wait_for_timeout(1000)
assert fila_objetivo, "Se esperaba al menos 1 reclamo real con codigo en la grilla"
capturar_paso(app, "antes_de_doble_clic", paso_excel=3)
fila_objetivo.dblclick()
app.wait_for_timeout(1500)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "consulta_abierta", paso_excel=4)
frame.locator("app-consulta-del-reclamo").wait_for(timeout=15000)
assert codigo_esperado in frame.locator("body").inner_text(), f"Se esperaba ver el codigo {codigo_esperado!r} en la Consulta del Reclamo"
''')


add("CP023", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 24/09/2026: las opciones reales de "Ordenar por"
# son "Dias Rest. Total, Dias Rest. Estacion, N Reclamo, Tipo Cliente"
# - NO existe "Tipo de Reclamo" como sugiere el ejemplo de la matriz,
# se usa "N Reclamo" en su lugar (opcion real valida).
campo_instancia = frame.get_by_label(re.compile("^Instancia$", re.I))
campo_instancia.click()
app.wait_for_timeout(500)
frame.get_by_role("option", name="PRIMERA INSTANCIA", exact=True).click()
app.wait_for_timeout(300)
campo_ordenar = frame.get_by_label(re.compile("^Ordenar por$", re.I))
campo_ordenar.click()
app.wait_for_timeout(500)
frame.get_by_role("option", name=re.compile(r"N.\\s?Reclamo", re.I)).click()
capturar_paso(app, "antes_de_buscar", paso_excel=3)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
filas = None
for _ in range(20):
    filas = frame.locator("table tbody tr")
    if filas.count() > 0 and re.search(r"\\bRE\\S*-\\d{4}\\b", filas.first.inner_text()):
        break
    app.wait_for_timeout(1000)
capturar_paso(app, "resultado_filtrado_y_ordenado", paso_excel=4)
assert filas.count() > 0, "Se esperaba al menos 1 reclamo en Primera Instancia"
for i in range(filas.count()):
    texto_fila = filas.nth(i).inner_text()
    if texto_fila.strip():
        assert "PRIMERA INSTANCIA" in texto_fila.upper(), f"Fila fuera de Primera Instancia: {texto_fila!r}"
''')


# ===========================================================================
# RF-06 (cont.): navegacion Anterior/Siguiente/Cerrar cuando se abre
# desde un LISTADO real (via el doble clic de RF-03, unico camino
# confirmado hasta ahora - CP103 de RF-05 sigue sin resolver).
# CONFIRMADO EN VIVO 24/09/2026: existen 2 pares de botones
# Anterior/Siguiente en el DOM simultaneamente - el PRIMERO (indice 0,
# tooltip "Reclamo anterior/siguiente de la lista") es el real y
# funcional; el SEGUNDO (tooltip "Disponible al abrir desde un listado
# de reclamos") es un placeholder que queda SIEMPRE deshabilitado. Usar
# siempre .first (indice 0), nunca el locator sin filtrar (da "strict
# mode violation: resolved to 2 elements").

add("CP124", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
app.wait_for_timeout(1000)
frame.locator("table tbody tr").first.dblclick()
app.wait_for_timeout(1500)
esperar_fin_de_carga(app, frame)
boton_anterior = frame.get_by_role("button", name="Anterior", exact=True).first
capturar_paso(app, "primer_reclamo_de_la_lista", paso_excel=3)
assert boton_anterior.is_disabled(), "Anterior deberia estar deshabilitado en el primer reclamo del listado"
''')

add("CP125", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
app.wait_for_timeout(1000)
frame.locator("table tbody tr").first.dblclick()
app.wait_for_timeout(1500)
esperar_fin_de_carga(app, frame)
boton_siguiente = frame.get_by_role("button", name="Siguiente", exact=True).first
assert boton_siguiente.is_enabled(), "Siguiente deberia estar habilitado en el primer reclamo (hay un segundo en la lista)"
capturar_paso(app, "antes_de_siguiente", paso_excel=3)
boton_siguiente.click()
app.wait_for_timeout(1500)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "ultimo_reclamo_de_la_lista", paso_excel=4)
assert boton_siguiente.is_disabled(), "Siguiente deberia estar deshabilitado en el ultimo reclamo del listado"
''')

# CP127 (Cerrar regresa al listado de origen) - PENDIENTE, 24/09/2026:
# tanto "Cerrar" como "Volver" dejan la pantalla en blanco (screenshot
# gris solido) en vez de volver al listado de Reasignacion - parece que
# navega FUERA del iframe #aplicacion (quizas hasta el contenedor
# "NuevaPestana" del portal). Necesita mas exploracion en vivo (¿hay
# que esperar mas? ¿el iframe se destruye y frame queda stale? ¿existe
# otro boton real de "volver"?) antes de escribir el caso - no adivinar
# mas.


# ===========================================================================
# RF-09: Seleccion de Operador (modal, se abre desde el boton "Asignar
# seleccionados"/"Reasignar seleccionados" de RF-02/RF-03 - ya
# confirmado funcional en CP026/CP051/CP064).

add("CP165", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
checkbox_fila = frame.locator("table tbody tr mat-checkbox").first
checkbox_fila.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Asignar seleccionados")).click()
app.wait_for_timeout(1000)
capturar_paso(app, "modal_selector_operadores", paso_excel=3)
texto_modal_antes = frame.locator("body").inner_text()
assert "operador" in texto_modal_antes.lower(), "Se esperaba el modal Selector de Operadores"
frame.get_by_role("button", name="Cancelar", exact=True).click()
app.wait_for_timeout(1000)
capturar_paso(app, "modal_cancelado", paso_excel=4)
boton_asignar = frame.get_by_role("button", name=re.compile(r"Asignar seleccionados"))
assert "1" in boton_asignar.inner_text(), f"La seleccion original (1 reclamo) deberia seguir intacta: {boton_asignar.inner_text()!r}"
''')

add("CP173", "app, frame = abrir_asignacion(page, paso_excel=2)", '''
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
frame.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)
checkbox_fila = frame.locator("table tbody tr mat-checkbox").first
checkbox_fila.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Asignar seleccionados")).click()
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(1500)
capturar_paso(app, "modal_sin_seleccionar_operador", paso_excel=3)
# CONFIRMADO EN VIVO: el boton real del modal es "Seleccionar", no
# "Aceptar" como generaliza la matriz.
boton_seleccionar = frame.get_by_role("button", name="Seleccionar", exact=True)
boton_seleccionar.wait_for(state="visible", timeout=15000)
boton_seleccionar.click(force=True)
app.wait_for_timeout(1000)
capturar_paso(app, "modal_sigue_abierto", paso_excel=4)
texto_modal = frame.locator("body").inner_text()
assert "Selecci" in texto_modal, "El modal Selector de Operadores deberia seguir abierto sin ningun operador marcado"
frame.get_by_role("button", name="Cancelar", exact=True).click()
''')

# EJECUTADOS EN VIVO 25/09/2026 CON CONFIRMACION EXPLICITA DEL USUARIO
# (escrituras reales, mismo patron que CP025/CP050). Ya no queda ningun
# reclamo sin asignar en ISE (CP025 consumio el unico) - la matriz pide
# estos 2 casos via "Asignacion de Reclamos", pero al no haber dato
# disponible ahi se sustituyo por "Reasignacion de Reclamos" (mismo
# componente Selector de Operador de RF-09, misma mecanica de
# confirmar). A diferencia de CP025, Reasignacion es repetible sin
# consumir el pool (confirmado con CP050) asi que ambos corren por el
# pipeline oficial normalmente.
# CP163 (Seleccionar): RCL-0058715 -> VOCH. Mensaje real confirmado:
# "Se reasignaron 1 reclamo(s) al operador VOCH en estacion JDS."
# CP164 (doble clic, sin click en Seleccionar): RCL-0035331 -> HTA.
# Mensaje real confirmado: "Se reasignaron 1 reclamo(s) al operador HTA
# en estacion JDS." - el doble clic solo, sin tocar el boton
# Seleccionar, SI confirma y cierra el modal (confirmado en vivo antes
# de escribir el caso).

add("CP163", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 08/10/2026: ver nota en CP050 - la estacion por
# defecto ya no es "Jefe Sucursal", hay que seleccionarla a mano.
campo_estacion = frame.locator("mat-select").first
campo_estacion.click()
app.wait_for_timeout(500)
frame.get_by_role("option", name=re.compile("Sucursal", re.I)).click()
app.wait_for_timeout(500)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
fila_objetivo = frame.locator("table tbody tr", has_text="RCL-0058715")
fila_objetivo.wait_for(state="visible", timeout=15000)
capturar_paso(app, "reclamo_a_reasignar", paso_excel=3)
checkbox_fila = fila_objetivo.locator("mat-checkbox")
checkbox_fila.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Reasignar seleccionados")).click()
app.wait_for_timeout(1000)
fila_operador = frame.get_by_text("VANESSA ODETTE CUEVA HERRERA DE SUCLUPE", exact=True)
fila_operador.wait_for(state="visible", timeout=15000)
capturar_paso(app, "modal_operadores", paso_excel=4)
fila_operador.click()
app.wait_for_timeout(500)
boton_seleccionar = frame.get_by_role("button", name="Seleccionar", exact=True)
boton_seleccionar.click()
app.wait_for_timeout(2500)
capturar_paso(app, "confirmacion_asignacion", paso_excel=5)
mensaje = frame.get_by_text(re.compile(r"Se reasignaron \\d+ reclamo\\(s\\) al operador", re.I))
mensaje.wait_for(state="visible", timeout=10000)
frame.locator("app-alert").get_by_role("button", name="Aceptar", exact=True).click()
''')

add("CP164", "app, frame = abrir_reasignacion(page, paso_excel=2)", '''
# CONFIRMADO EN VIVO 08/10/2026: ver nota en CP050 - la estacion por
# defecto ya no es "Jefe Sucursal", hay que seleccionarla a mano.
campo_estacion = frame.locator("mat-select").first
campo_estacion.click()
app.wait_for_timeout(500)
frame.get_by_role("option", name=re.compile("Sucursal", re.I)).click()
app.wait_for_timeout(500)
frame.get_by_role("button", name="Buscar", exact=True).click()
esperar_fin_de_carga(app, frame)
fila_objetivo = frame.locator("table tbody tr", has_text="RCL-0035331")
fila_objetivo.wait_for(state="visible", timeout=15000)
capturar_paso(app, "reclamo_a_reasignar", paso_excel=3)
checkbox_fila = fila_objetivo.locator("mat-checkbox")
checkbox_fila.click()
app.wait_for_timeout(500)
frame.get_by_role("button", name=re.compile(r"Reasignar seleccionados")).click()
app.wait_for_timeout(1000)
fila_operador = frame.get_by_text("HUGO TENORIO ALARCON", exact=True)
fila_operador.wait_for(state="visible", timeout=15000)
capturar_paso(app, "modal_antes_doble_clic", paso_excel=4)
fila_operador.dblclick()
app.wait_for_timeout(2500)
capturar_paso(app, "confirmacion_tras_doble_clic", paso_excel=5)
mensaje = frame.get_by_text(re.compile(r"Se reasignaron \\d+ reclamo\\(s\\) al operador", re.I))
mensaje.wait_for(state="visible", timeout=10000)
frame.locator("app-alert").get_by_role("button", name="Aceptar", exact=True).click()
''')


if __name__ == "__main__":
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")
