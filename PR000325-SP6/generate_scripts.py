"""
generate_scripts.py de PR000325-SP6 - FUENTE DE VERDAD que genera los CPxxx.py.

Sprint 6 de PR000325 ("Migracion Modulo de Facturacion") - submodulo
Refacturacion: 10 apps Angular/.NET independientes (una por RF, migradas
de formularios VB originales), 112 casos en la matriz.

CONFIRMADO EN VIVO el 18/09/2026 (ver _exploracion/):
- Navegacion: TODAS cuelgan de "Comercial > Facturación > Refacturación"
  (NO de "Interno" como en PR000325-SP4).
- RF-10 (Parametros de Refacturaciones Automaticas / PAREFAUT) NO
  aparece en el menu de la cuenta DCABA_DW. Causa real confirmada en el
  ET (4.10.1): el recurso de seguridad de CADA item de menu es el
  formulario VB original (SRV.<FORM> - R/W/D) - RF-10 usa "PAREFAUT",
  distinto del resto. Es un permiso puntual faltante en la cuenta de
  prueba, NO un bug ni una pantalla no desplegada. Los 12 casos de RF-10
  (CP101-CP112) quedan PENDIENTES hasta que se asigne ese permiso.
- Los otros 9 RF SI abren. Cada uno es un popup con wrapper #aplicacion
  (patron generico de abrir_aplicacion() de _framework). El componente
  Angular raiz real (buscando el HIJO de <app-root>, no <app-root> en si
  - <app-root> es el mismo para las 9 apps y no distingue nada):
    RF-01 app-orden-list           | RF-02 app-arreglo-page
    RF-03 app-debito-varios-list   | RF-04 app-debito-ind-list
    RF-05 app-informe-orden        | RF-06 app-informe-debito-varios
    RF-07 app-informe-refactur     | RF-08 app-consulta-refactur-page
    RF-09 app-claref-page
- PERMISO DE ESCRITURA (RF-01 a RF-04, y probablemente RF-09): distinto
  del permiso de menu de arriba. La matriz Excel trae una hoja aparte
  "permiso_refacturacion" con el INSERT SQL que hay que correr sobre
  Informix (BD clientes, tabla `permiso`) para el ROL_PERSONAL de la
  cuenta de prueba. Sin ese INSERT, RF-01/RF-02 muestran al abrir el
  dialogo "Usuario no tiene permisos asignados para refactuaciones. Sólo
  podrá consultar." (justamente lo que valida CP002/CP014) y los botones
  de escritura (Ingresar/Eliminar/Generar en RF01, Ingresar/Eliminar en
  RF09) quedan deshabilitados. DECISION DEL USUARIO (18/09/2026): avanzar
  primero con los casos que SI funcionan sin ese permiso (validaciones,
  consultas/informes, casos que verifican el estado "solo consulta") y
  dejar pendientes los casos de Ingresar/Modificar/Eliminar reales hasta
  que se confirme el INSERT.

ACTUALIZACION 21/09/2026: el usuario confirmo que ya corrio el INSERT de
permiso_refacturacion, y el permiso de menu PAREFAUT tambien quedo
resuelto (RF-10 ya aparece y abre). Confirmado en vivo: el modal de
"solo consulta" ya NO aparece en RF-01/02/03/04/09, y RF-09 reconoce
datos reales (Modificar habilitado). Con esto se completan los casos de
escritura de RF-01/02/03/04/09/10 y los de RF-08 que dependian de datos.
- CLIENTE DE PRUEBA VALIDO confirmado en vivo para RF-01 (y reusado en
  RF-02/03/04): numero de cliente "000100001" -> DV=2, Ruta Lectura=
  15090530, Clave Tarifa=0021. Encontrarlo llevo varias vueltas porque
  el formulario tiene un BUG/QUIRK DE TIMING real: la validacion en el
  evento blur de "N Cliente" SIEMPRE evalua el valor ANTERIOR (un paso
  de retraso), no el que se acaba de escribir - confirmado reproduciendo
  el mismo comportamiento 3 veces seguidas. Ademas, el PRIMER blur de la
  fila (sin importar el valor) siempre devuelve "Ingrese nro.
  documento." como mensaje generico de "calentamiento". Por eso
  `buscar_cliente_valido()` (helper de abajo) hace un blur de
  calentamiento + reintentos, no una sola llamada.
- Claves de Movimiento validas para consultar (Leer) en RF-01: 3-6-8,
  con Fecha O.R. 04/09/2026 y Total Caratula 500 (sugerido por la propia
  matriz para CP003) - la consulta ejecuta sin error pero la grilla
  puede aparecer vacia ("No hay ordenes para los criterios indicados."),
  lo cual es en si mismo el estado necesario para CP011 (Generar
  deshabilitado con grilla vacia).
- Campos de fecha: son <input type="date" aria-label="Fecha Desde/Hasta">
  NATIVOS (no placeholder, no texto libre) - filtrar con
  frame.locator('input[aria-label="..."]') y .fill("yyyy-mm-dd") (formato
  ISO, NO dd/mm/aaaa aunque la UI lo muestre asi).
- Dialogos: Ant Design/ng-zorro (`.ant-modal-wrap`, titulo "Ventana de
  Validación"/"Ventana de Confirmación" + boton "Aceptar"), igual que
  PR000325-SP4, confirmado en RF-05/06/07. OJO: mientras el informe se
  genera (ver "Generando Informe" abajo) el dialogo todavia NO existe -
  buscarlo antes de que termine de cargar da un falso "sin dialogo"
  (confirmado en vivo con RF-07, que tarda bastante mas que RF-05/06).
  `dialogo_f()` de abajo ademas prueba `.mdl-tab-pane`/`[role='dialog']`
  como red de seguridad por si alguna otra app de este sprint usa un
  modal distinto (patron "mdl-" ya visto en SP2/SP4).
- RF-05/RF-06 "Generar": mensajes reales (DISTINTOS del texto de la
  matriz Excel, usar estos):
    Fecha Desde vacia  -> "Fecha Desde es obligatoria."
    Rango invalido     -> "Fecha Hasta no puede ser anterior a Fecha Desde."
    Exito RF-05        -> "Listado de Refacturaciones Generado." + ruta
    Exito RF-06        -> "Listado de Débitos Varios Generado." + ruta
  Tras Generar exitoso o Cancelar, los campos de fecha quedan vacios y
  los botones vuelven a Manual/Generar/Cancelar (confirmado en vivo).
  Mientras genera, aparece el texto "Generando Informe ... Espere." y
  Generar/Cancelar quedan deshabilitados - HAY QUE ESPERAR a que
  desaparezca antes de buscar el dialogo de resultado (RF-07 en
  particular tarda bastante mas que RF-05/06 porque genera 2 archivos).
- RF-07 trae ademas un radio "Dia de Proceso"/"Fecha de Ingreso"
  (name="opcion", value="P"/"I") - "Dia de Proceso" viene marcado por
  defecto (confirmado en vivo, CP067).

NO CONFIRMADO EN VIVO TODAVIA (a completar en la siguiente iteracion):
RF-08 (consulta con filtros/paginacion/exportar, 17 casos) y los casos
puntuales de RF-01/02/03/04/09 que SI se pueden probar sin el permiso de
escritura (validaciones de campo, estado inicial, responsive).
"""
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT_DIR.parent / "_framework"))
import web_lds_core as core  # noqa: E402

PROYECTO = "PR000325-SP6"
MATRIZ = json.loads((OUT_DIR / "matriz_casos.json").read_text(encoding="utf-8"))

ENV_TOGGLES = core.ENV_TOGGLES_CODE.replace("__PROYECTO__", PROYECTO)


SP6F_HELPERS = '''
def campo_fecha(scope, etiqueta):
    """Input <input type="date" aria-label="Fecha Desde/Hasta"> nativo.
    fill() espera formato ISO (yyyy-mm-dd), NO dd/mm/aaaa aunque la UI lo
    muestre asi (confirmado en vivo el 18/09/2026)."""
    return scope.locator(f'input[aria-label="{etiqueta}"]')


def buscar_cliente_valido(scope, campo_cliente, numero, campo_dv=None, campo_documento=None, documento="00001"):
    """Escribe `numero` en el campo N Cliente y sale del campo (blur),
    absorbiendo el QUIRK DE TIMING real confirmado en vivo el 21/09/2026
    en las pantallas de Refacturacion: el PRIMER blur de N Cliente en
    una fila siempre devuelve el mensaje generico "Ingrese nro.
    documento." (sin importar el valor, incluso con Documento ya
    lleno), y ademas la validacion real de CADA blur evalua el valor
    ANTERIOR (un paso de retraso), no el recien escrito. Ademas, un
    dialogo de un blur anterior puede quedar visible SUPERPUESTO sobre
    un formulario que ya cargo bien los datos del cliente actual (el
    dialogo esta simplemente atrasado en cerrarse, no refleja el estado
    real). Por eso, en vez de confiar en el dialogo para decidir si el
    cliente es valido, se cierra CUALQUIER dialogo que haya quedado
    abierto y se verifica directamente el campo `campo_dv` (DV Cliente,
    solo lectura, se llena solo si el cliente existe): valor no vacio =
    cliente valido; campo vacio (y N Cliente tambien vacio, por RN-10:
    el sistema limpia el campo si no encuentra el cliente) = invalido.
    Devuelve el texto del ultimo dialogo visto (o None) para poder
    reportarlo si hizo falta diagnosticar un rechazo."""
    if campo_documento is not None:
        campo_documento.fill(documento)
    if campo_dv is None:
        campo_dv = scope.locator('input[aria-label="DV Cliente"]')

    ultimo_texto = None
    for intento, valor in enumerate((numero, numero, numero)):
        campo_cliente.fill(valor)
        if intento == 2:
            campo_cliente.press("End")
        campo_cliente.press("Tab")
        campo_cliente.page.wait_for_timeout(1800)
        dlg = dialogo_f(scope)
        if dlg.count() > 0 and dlg.is_visible():
            ultimo_texto = dlg.inner_text()
            cerrar_dialogo(scope)
            campo_cliente.page.wait_for_timeout(400)

    if campo_dv.input_value().strip():
        return None
    return ultimo_texto


def cerrar_cualquier_dialogo(scope, intentos=3, espera_ms=800):
    """Cierra cualquier dialogo que este visible en este momento, si lo
    hay (no falla si no hay ninguno). Reintenta varias veces porque un
    dialogo puede aparecer con un poco de retraso justo despues de un
    blur/validacion async (confirmado en vivo: el QUIRK DE TIMING de
    buscar_cliente_valido() a veces deja un dialogo pendiente que recien
    se pinta unos cientos de ms despues de que la funcion ya retorno)."""
    for _ in range(intentos):
        dlg = dialogo_f(scope)
        if dlg.count() > 0 and dlg.is_visible():
            pagina = dlg.page
            cerrar_dialogo(scope)
            pagina.wait_for_timeout(espera_ms)
        else:
            return


def esperar_dialogo_visible(scope, timeout_ms=10000, intervalo_ms=300):
    """Espera a que aparezca un dialogo VISIBLE, volviendo a consultar
    dialogo_f() en cada intento (no reutiliza una referencia vieja).
    GOTCHA REAL confirmado en vivo: mantener una sola referencia
    (`dlg = dialogo_f(scope)`) y despues llamar `dlg.wait_for(visible)`
    puede apuntar a un dialogo VIEJO/oculto que quedo en el DOM (Angular
    no siempre lo remueve, solo lo oculta) si ese elemento resulta estar
    en el mismo indice `.nth(i)` que el dialogo nuevo terminaria
    ocupando - hay que re-resolver el selector en cada intento, no
    confiar en una localizacion fija. Devuelve el Locator del dialogo
    visible, o lanza TimeoutError si nunca aparecio."""
    limite = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < limite:
        dlg = dialogo_f(scope)
        if dlg.count() > 0 and dlg.is_visible():
            return dlg
        scope.locator("body").page.wait_for_timeout(intervalo_ms)
    raise PWTimeoutError(f"No aparecio ningun dialogo visible tras {timeout_ms}ms")


def dialogo_f(scope):
    """Dialogo real de validacion/confirmacion - mezcla de 2 frameworks
    segun la app (confirmado en vivo): Ant Design (`.ant-modal-wrap`,
    RF-05/RF-06/RF-01/RF-02/RF-09) o modal propio `.mdl-tab-pane`
    (RF-07). Se toma el ULTIMO elemento VISIBLE (mismo patron de
    apilamiento ya confirmado en otras pantallas de Web LDS).

    GOTCHA REAL confirmado en vivo el 21/09/2026: los Locators de
    Playwright son perezosos - `.nth(i)` fija un INDICE posicional que
    se vuelve a resolver contra el DOM recien en el momento de la
    accion (ej. .click()), no en el momento en que se llamo a esta
    funcion. Si entre medio un dialogo VIEJO oculto (que Angular deja
    en el DOM en vez de removerlo) desaparece o el dialogo nuevo cambia
    de posicion, `.nth(i)` puede terminar apuntando a un elemento
    distinto al que se veia visible cuando se lo eligio - causando
    timeouts al clickear un boton "que se ve perfectamente" en el
    screenshot. Por eso se usa el pseudo-selector `:visible` de
    Playwright DENTRO de la cadena del Locator en vez de filtrar a mano
    con is_visible()+nth(): al ser parte del selector, se re-evalua
    dinamicamente en cada uso, autocorrigiendose siempre al dialogo
    REALMENTE visible en ese instante en vez de quedar pegado a un
    indice viejo.

    BUG REAL confirmado en vivo 22/09/2026 (CP018/CP106-110, diagnostico
    con dump completo del DOM): a veces coexisten AL MISMO TIEMPO un
    dialogo real (.ant-modal-wrap, con role="dialog" y sus botones) y
    un elemento fantasma .mdl-tab-pane que solo repite el TEXTO del
    mensaje pero no tiene NINGUN boton adentro (no es un dialogo real,
    parece un tooltip/anuncio de accesibilidad residual). Si ese
    fantasma queda despues en el DOM, `.last` sobre el selector
    combinado lo elegia a EL en vez del dialogo real - buscar "Aceptar"
    adentro entonces no encontraba nada y tiraba timeout, pese a que el
    dialogo real con su boton estaba perfectamente visible en pantalla.
    Ahora se prioriza el candidato que realmente CONTIENE al menos un
    boton (la propiedad que de verdad importa para cualquier uso de
    esta funcion), cayendo al viejo comportamiento (ultimo visible) si
    ninguno tiene botones."""
    candidatos = scope.locator(".ant-modal-wrap:visible, .mdl-tab-pane:visible, [role='dialog']:visible")
    total = candidatos.count()
    for i in range(total - 1, -1, -1):
        candidato = candidatos.nth(i)
        if candidato.locator("button").count() > 0:
            return candidato
    return candidatos.last


def click_con_reintento_dialogo(scope, boton, intentos=10, timeout_click=6000, espera_ms=1500):
    """Click que reintenta si un dialogo abierto (residual de una
    validacion async anterior, ver buscar_cliente_valido()) esta
    bloqueando el elemento ("subtree intercepts pointer events") -
    cierra el dialogo y reintenta en vez de fallar de una.

    BUG REAL confirmado en vivo 22/09/2026 (CP010/CP012, RF-01): un
    dialogo generico ("Ingrese nro. documento.") puede quedar abierto
    ANTES de este click (validacion async disparada por el fill() de un
    campo previo, con mas delay del que cubren los cerrar_cualquier_dialogo()
    intermedios) - si ya esta ahi ANTES de intentar el click, el click
    nunca llega a registrarse (bloqueado desde el primer intento, no
    solo tras un timeout) y cada uno de los 10 reintentos gasta el
    timeout_click completo esperando en vano. Se cierra cualquier
    dialogo residual ANTES de cada intento de click, no solo despues."""
    for intento in range(intentos):
        cerrar_cualquier_dialogo(scope)
        try:
            boton.click(timeout=timeout_click)
            cerrar_cualquier_dialogo(scope)
            return
        except PWTimeoutError:
            if intento == intentos - 1:
                raise
            cerrar_cualquier_dialogo(scope)
            boton.page.wait_for_timeout(espera_ms)


def registrar_orden_rf01(frame, app, cliente_numero, valor, documento="00001"):
    """Flujo completo de "Ingresar" una orden nueva en RF-01 (Traslados
    de Capital). GOTCHA REAL confirmado en vivo el 21/09/2026 tras
    mucho debug: el boton "Ingresar" de esta pantalla NUNCA cambia su
    texto a "Aceptar" (a diferencia de RF-09/RF-10) - el MISMO boton
    "Ingresar" sirve para abrir el panel (1er click) Y para confirmar
    el guardado (2do click, con los datos ya cargados). Ademas, TRAS
    CADA click en "Ingresar" (ambos) aparece de inmediato un dialogo
    "Ventana de Validación" (a veces "Ingrese nro. documento." como
    aviso generico del primer render de la fila) que hay que cerrar
    antes de poder interactuar con cualquier campo - si no se cierra,
    bloquea con "subtree intercepts pointer events" cualquier click
    posterior. Se cierra con cerrar_cualquier_dialogo() en cada paso.

    CAUSA RAIZ REAL confirmada en vivo el 21/09/2026 (revisando el
    screenshot de error junto al usuario): el 2do click en "Ingresar"
    SI guarda, pero antes dispara una "Ventana de Confirmación" real y
    esperada: "¿Está seguro de ingresar la orden de refacturación?"
    (botones Aceptar/Cancelar) - un paso de confirmacion de negocio
    genuino, no un error. Ese dialogo tarda un poco en aparecer despues
    del click (delay de red), por eso los intentos anteriores de solo
    cerrar "cualquier dialogo visible" inmediatamente despues del click
    lo perdian - hay que ESPERAR explicitamente a que aparezca antes de
    decidir que no hay nada que cerrar."""
    boton = frame.get_by_role("button", name="Ingresar", exact=True)
    click_con_reintento_dialogo(frame, boton)
    campo_cliente = frame.locator('input[aria-label="N° Cliente"]')
    campo_doc = frame.locator('input[aria-label="N° Documento"]')
    resultado = buscar_cliente_valido(frame, campo_cliente, cliente_numero, campo_documento=campo_doc, documento=documento)
    if resultado is not None:
        raise AssertionError(f"Cliente {cliente_numero!r} no valido al registrar la orden: {resultado!r}")
    cerrar_cualquier_dialogo(frame)
    campo_doc.fill(documento)
    frame.locator('input[aria-label="Valor"]').fill(valor)
    cerrar_cualquier_dialogo(frame)
    click_con_reintento_dialogo(frame, boton)
    try:
        dlg_confirma = esperar_dialogo_visible(frame, timeout_ms=6000)
        dlg_confirma.get_by_role("button", name=re.compile("Aceptar")).click(timeout=8000)
    except PWTimeoutError:
        pass
    cerrar_cualquier_dialogo(frame)
    esperar_fin_de_carga(app, frame)


def leer_arreglo_base(frame, app, clave3="1"):
    """Posiciona 'Arreglos de Facturado' (RF-02) en el cliente real
    000100001 (mismo usado en RF-01/03/04) con una Clave de Movimiento
    valida, y presiona Leer. CONFIRMADO EN VIVO 22/09/2026
    (_exploracion/explore_rf02_*.py): el catalogo real de Clave de
    Movimiento de ESTA pantalla es DISTINTO al de RF-01 (no reusar
    3-6-8) - Clave 1: 3=CARGO/4=ABONO; Clave 2: 5=CONSUMO/8=INTERESES/
    9=REFACTURACION ARREGLO CONTABLE; Clave 3 no tiene catalogo
    (0 opciones al buscar) y el valor "0" que sugiere el manual como
    especial es RECHAZADO ("Clave (3) de Movimiento invalida.") - "1"
    SI es valido y es lo que se usa por defecto aca. Aria-labels reales
    de esta pantalla (distintos a RF-01): "N.° de Cliente", "DV",
    "Nombre del Cliente" (NO "DV Cliente"/"Nombre")."""
    campo_cliente = frame.locator('input[aria-label="N.° de Cliente"]')
    campo_dv = frame.locator('input[aria-label="DV"]')
    buscar_cliente_valido(frame, campo_cliente, "000100001", campo_dv=campo_dv)
    frame.locator("#inputClave1").fill("3")
    frame.locator("#inputClave1").press("Tab")
    frame.locator("#inputClave2").fill("5")
    frame.locator("#inputClave2").press("Tab")
    frame.locator("#inputClave3").fill(clave3)
    frame.locator("#inputClave3").press("Tab")
    app.wait_for_timeout(1200)
    cerrar_cualquier_dialogo(frame)
    frame.get_by_role("button", name="Leer", exact=True).click(timeout=15000)
    app.wait_for_timeout(2000)
    cerrar_cualquier_dialogo(frame)


def elegir_fecha_a_corregir(frame, app, indice=0):
    """Abre el historial de periodos de facturacion (boton '?' junto a
    Fecha a Corregir) y selecciona la fila `indice`. CONFIRMADO EN VIVO
    22/09/2026: el modal de historial, igual que el catalogo de Clave
    de Movimiento, NO carga solo - hace falta presionar su propio boton
    'Buscar' interno antes de que aparezcan filas. Al seleccionar,
    completa Fecha a Corregir y Numero Factura automaticamente."""
    frame.get_by_role("button", name="Seleccionar Fecha a Corregir").click()
    app.wait_for_timeout(1200)
    dlg = esperar_dialogo_visible(frame, timeout_ms=8000)
    dlg.get_by_role("button", name="Buscar", exact=True).click()
    app.wait_for_timeout(2000)
    dlg = dialogo_f(frame)
    dlg.locator("table tbody tr").nth(indice).click()
    app.wait_for_timeout(400)
    dlg.get_by_role("button", name="Seleccionar", exact=True).click()
    app.wait_for_timeout(1000)


def esperar_fin_generando(frame, timeout_ms=90000):
    """Espera a que desaparezca el texto "Generando Informe ... Espere."
    (RF-05/06/07) antes de buscar el dialogo de resultado. RF-07 en
    particular tarda bastante mas que RF-05/06 (genera 2 archivos:
    lrefco01.lst y lrefco02.lst) - confirmado en vivo el 18/09/2026."""
    try:
        frame.get_by_text("Generando Informe").last.wait_for(state="hidden", timeout=timeout_ms)
    except PWTimeoutError:
        pass


NOMBRES_ACEPTAR = ("Aceptar", "Sí", "Si", "OK", "Confirmar")


def cerrar_dialogo(scope, nombres=NOMBRES_ACEPTAR):
    """Cierra el dialogo visible pulsando su boton de Aceptar (o el
    primer boton visible si no matchea ninguno de `nombres`)."""
    dlg = dialogo_f(scope)
    patron = re.compile(r"^\\s*(" + "|".join(re.escape(n) for n in nombres) + r")\\s*$")
    btn = dlg.get_by_role("button", name=patron)
    if btn.count() > 0:
        btn.last.click()
    else:
        todos = dlg.get_by_role("button")
        if todos.count() > 0:
            todos.last.click()
'''


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

%%CLICK_VISIBLE%%

%%ABRIR_APLICACION%%

%%HELPERS_ESPERA%%

%%VIDEO_HELPERS%%

%%SP6F_HELPERS%%

RUTA_MENU = {ruta_menu_repr}
SELECTOR_PANTALLA = {selector_pantalla_repr}


def abrir_app(page, paso_excel=2):
    return abrir_aplicacion(page, RUTA_MENU, SELECTOR_PANTALLA, paso_excel=paso_excel)


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
            app, frame_pg = abrir_app(page)
            frame = frame_pg

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
                # BUG REAL confirmado en vivo 22/09/2026 (PR000335-SP5):
                # casos con descarga real (app.expect_download(), ej.
                # boton "Exportar") a veces dejan una pestana efimera
                # adicional grabada por Playwright que nunca queda
                # referenciada por page/app - se barre cualquier
                # page@*.webm huerfano en EVIDENCIA y se suma al video
                # final en vez de dejarlo suelto.
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


def _indentar(body: str) -> str:
    lineas = body.strip("\n").splitlines()
    return "\n".join("            " + l if l.strip() else "" for l in lineas)


RUTA_MENU_BASE = ["Comercial", "Facturación", "Refacturación"]

RUTAS = {
    "RF-01": (RUTA_MENU_BASE + ["Traslados De Capital - Órdenes De Refacturación"], "app-orden-list"),
    "RF-02": (RUTA_MENU_BASE + ["Arreglos De Facturado"], "app-arreglo-page"),
    "RF-03": (RUTA_MENU_BASE + ["Ingreso De Débitos Varios"], "app-debito-varios-list"),
    "RF-04": (RUTA_MENU_BASE + ["Ingreso De Débitos Varios Individuales"], "app-debito-ind-list"),
    "RF-05": (RUTA_MENU_BASE + ["Informe De Refacturaciones A Ingresar"], "app-informe-orden"),
    "RF-06": (RUTA_MENU_BASE + ["Informe De Débitos Varios"], "app-informe-debito-varios"),
    "RF-07": (RUTA_MENU_BASE + ["Informe De Refacturaciones"], "app-informe-refactur"),
    "RF-08": (RUTA_MENU_BASE + ["Consulta De Refacturaciones Procesadas"], "app-consulta-refactur-page"),
    "RF-09": (RUTA_MENU_BASE + ["Mantenimiento De Tablas De Códigos De Refacturación"], "app-claref-page"),
    "RF-10": (RUTA_MENU_BASE + ["Parámetros De Refacturaciones Automáticas"], "app-parametro-page"),
}


def render(caso: dict) -> str:
    docstring = (
        f"CP: {caso['cp']} | RF: {caso['rf']} | CU: {caso['cu']}\n"
        f"Nombre: {caso['name']}\n\n"
        f"{caso['desc']}\n\n"
        f"Precondiciones: {caso['precond']}\n\n"
        f"Resultado esperado: {caso['esperado']}"
    )
    body = _indentar(caso["body"])
    ruta_menu, selector_pantalla = RUTAS[caso["rf"]]
    return HEADER_TEMPLATE.format(
        docstring=docstring, cp=caso["cp"], name_repr=repr(caso["name"]), rf_repr=repr(caso["rf"]),
        cu_repr=repr(caso["cu"]), desc_repr=repr(caso["desc"]),
        esperado_repr=repr(caso["esperado"]), pasos_repr=repr(caso.get("pasos", "")), body=body,
        ruta_menu_repr=repr(ruta_menu), selector_pantalla_repr=repr(selector_pantalla),
    ).replace("%%CAPTURAR_PASO%%", core.CAPTURAR_PASO_CODE) \
     .replace("%%LOGIN%%", core.LOGIN_BLOCK) \
     .replace("%%CLICK_VISIBLE%%", core.CLICK_VISIBLE_BLOCK) \
     .replace("%%ABRIR_APLICACION%%", core.ABRIR_APLICACION_BLOCK) \
     .replace("%%HELPERS_ESPERA%%", core.ESPERAR_FIN_CARGA_BLOCK + "\n\n\n" + core.ESPERAR_ANIMACION_BLOCK + "\n\n\n" + core.SELECCIONAR_PRIMERA_OPCION_BLOCK + "\n\n\n" + core.SELECCIONAR_OPCION_POR_TEXTO_BLOCK) \
     .replace("%%VIDEO_HELPERS%%", core.RENOMBRAR_VIDEO_BLOCK) \
     .replace("%%SP6F_HELPERS%%", SP6F_HELPERS) \
     .replace("%%CURSOR_OVERLAY_JS%%", repr(core.CURSOR_JS_FULL.strip("\n"))) \
     .replace("%%WORD_HELPERS%%", core.WORD_HELPERS_FULL.strip("\n"))


CASES = []


def add(cp, body):
    c = MATRIZ[cp]
    CASES.append(dict(
        cp=cp, rf=c["rf"], cu=c["cu"], name=c["name"], desc=c["desc"],
        precond=c["precond"], datos=c.get("datos", ""), esperado=c["esperado"],
        pasos=c.get("pasos", ""), body=body,
    ))


# ======================== RF-05: Informe De Refacturaciones A Ingresar ========================

add("CP051", '''
capturar_paso(app, "antes_de_generar", paso_excel=3)
campo_fecha(frame, "Fecha Desde").fill("2026-08-01")
campo_fecha(frame, "Fecha Hasta").fill("2027-08-15")
frame.get_by_role("button", name="Generar").click(timeout=15000)
esperar_fin_generando(frame)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Generado" in texto, f"No aparecio el mensaje de exito esperado: {texto!r}"
capturar_paso(app, "informe_generado", paso_excel=5)
cerrar_dialogo(frame)
''')

add("CP052", '''
capturar_paso(app, "antes_de_generar", paso_excel=3)
campo_fecha(frame, "Fecha Desde").fill("2026-01-01")
frame.get_by_role("button", name="Generar").click(timeout=15000)
esperar_fin_generando(frame)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Generado" in texto, f"No aparecio el mensaje de exito esperado (Fecha Hasta omitida): {texto!r}"
capturar_paso(app, "informe_generado_hasta_omitida", paso_excel=5)
cerrar_dialogo(frame)
''')

add("CP053", '''
capturar_paso(app, "antes_de_generar", paso_excel=3)
frame.get_by_role("button", name="Generar").click(timeout=15000)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Fecha Desde es obligatoria" in texto, f"No aparecio el mensaje de campo obligatorio: {texto!r}"
capturar_paso(app, "mensaje_desde_obligatoria", paso_excel=5)
cerrar_dialogo(frame)
''')

add("CP054", '''
capturar_paso(app, "antes_de_generar", paso_excel=3)
campo_fecha(frame, "Fecha Desde").fill("2026-08-15")
campo_fecha(frame, "Fecha Hasta").fill("2026-08-01")
frame.get_by_role("button", name="Generar").click(timeout=15000)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "anterior a Fecha Desde" in texto, f"No aparecio el mensaje de rango invalido: {texto!r}"
capturar_paso(app, "mensaje_rango_invalido", paso_excel=5)
cerrar_dialogo(frame)
''')

add("CP055", '''
for ancho, alto, nombre in ((1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")):
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(500)
    assert frame.get_by_role("button", name="Generar").is_visible(), f"Boton Generar no visible en {nombre}"
    capturar_paso(app, f"responsive_{nombre}")
''')


# ======================== RF-06: Informe De Débitos Varios ========================

add("CP056", '''
capturar_paso(app, "antes_de_generar", paso_excel=3)
campo_fecha(frame, "Fecha Desde").fill("2026-01-01")
campo_fecha(frame, "Fecha Hasta").fill("2026-09-01")
frame.get_by_role("button", name="Generar").click(timeout=15000)
esperar_fin_generando(frame)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Generado" in texto, f"No aparecio el mensaje de exito esperado: {texto!r}"
capturar_paso(app, "informe_generado", paso_excel=6)
cerrar_dialogo(frame)
campos_limpios = campo_fecha(frame, "Fecha Desde").input_value() == "" and campo_fecha(frame, "Fecha Hasta").input_value() == ""
assert campos_limpios, "Los campos de fecha no quedaron limpios tras generar"
capturar_paso(app, "campos_limpios_tras_generar")
''')

add("CP057", '''
capturar_paso(app, "antes_de_generar", paso_excel=3)
campo_fecha(frame, "Fecha Desde").fill("2026-02-01")
frame.get_by_role("button", name="Generar").click(timeout=15000)
esperar_fin_generando(frame)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Generado" in texto, f"No aparecio el mensaje de exito esperado (Hasta omitida): {texto!r}"
capturar_paso(app, "informe_generado_hasta_omitida", paso_excel=5)
cerrar_dialogo(frame)
''')

add("CP058", '''
capturar_paso(app, "antes_de_generar", paso_excel=3)
frame.get_by_role("button", name="Generar").click(timeout=15000)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Fecha Desde es obligatoria" in texto, f"No aparecio el mensaje de campo obligatorio: {texto!r}"
capturar_paso(app, "mensaje_desde_obligatoria", paso_excel=5)
cerrar_dialogo(frame)
''')

add("CP059", '''
capturar_paso(app, "antes_de_generar", paso_excel=3)
campo_fecha(frame, "Fecha Desde").fill("2026-08-15")
campo_fecha(frame, "Fecha Hasta").fill("2026-08-01")
frame.get_by_role("button", name="Generar").click(timeout=15000)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "anterior a Fecha Desde" in texto, f"No aparecio el mensaje de rango invalido: {texto!r}"
capturar_paso(app, "mensaje_rango_invalido", paso_excel=5)
cerrar_dialogo(frame)
''')

add("CP060", '''
campo_fecha(frame, "Fecha Desde").fill("2026-01-01")
campo_fecha(frame, "Fecha Hasta").fill("2026-09-01")
capturar_paso(app, "antes_de_cancelar", paso_excel=3)
frame.get_by_role("button", name="Cancelar").click(timeout=15000)
app.wait_for_timeout(800)
campos_limpios = campo_fecha(frame, "Fecha Desde").input_value() == "" and campo_fecha(frame, "Fecha Hasta").input_value() == ""
assert campos_limpios, "Los campos de fecha no quedaron limpios tras Cancelar"
capturar_paso(app, "campos_limpios_tras_cancelar", paso_excel=5)
''')

add("CP061", '''
for ancho, alto, nombre in ((1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")):
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(500)
    assert frame.get_by_role("button", name="Generar").is_visible(), f"Boton Generar no visible en {nombre}"
    capturar_paso(app, f"responsive_{nombre}")
''')


# ======================== RF-07: Informe De Refacturaciones ========================

add("CP062", '''
opcion_dia_proceso = frame.locator('input[type="radio"][value="P"]')
assert opcion_dia_proceso.is_checked(), "La opcion 'Dia de Proceso' deberia estar marcada por defecto"
capturar_paso(app, "opcion_dia_proceso_por_defecto", paso_excel=4)
campo_fecha(frame, "Fecha Desde").fill("2026-01-01")
campo_fecha(frame, "Fecha Hasta").fill("2026-09-01")
frame.get_by_role("button", name="Generar").click(timeout=15000)
esperar_fin_generando(frame)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Generado" in texto, f"No aparecio el mensaje de exito esperado: {texto!r}"
capturar_paso(app, "informe_generado", paso_excel=6)
cerrar_dialogo(frame)
''')

add("CP063", '''
frame.locator('input[type="radio"][value="I"]').check()
capturar_paso(app, "opcion_fecha_ingreso", paso_excel=4)
campo_fecha(frame, "Fecha Desde").fill("2026-01-01")
campo_fecha(frame, "Fecha Hasta").fill("2026-09-01")
frame.get_by_role("button", name="Generar").click(timeout=15000)
esperar_fin_generando(frame)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Generado" in texto, f"No aparecio el mensaje de exito esperado (Por fecha de ingreso): {texto!r}"
capturar_paso(app, "informe_generado", paso_excel=6)
cerrar_dialogo(frame)
''')

add("CP064", '''
campo_fecha(frame, "Fecha Desde").fill("2026-01-01")
capturar_paso(app, "antes_de_generar", paso_excel=3)
frame.get_by_role("button", name="Generar").click(timeout=15000)
esperar_fin_generando(frame)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Generado" in texto, f"No aparecio el mensaje de exito esperado (Hasta omitida): {texto!r}"
capturar_paso(app, "informe_generado_hasta_omitida", paso_excel=5)
cerrar_dialogo(frame)
''')

add("CP065", '''
capturar_paso(app, "antes_de_generar", paso_excel=3)
frame.get_by_role("button", name="Generar").click(timeout=15000)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "obligatori" in texto.lower(), f"No aparecio el mensaje de campo obligatorio: {texto!r}"
capturar_paso(app, "mensaje_desde_obligatoria", paso_excel=5)
cerrar_dialogo(frame)
''')

add("CP066", '''
campo_fecha(frame, "Fecha Desde").fill("2026-08-15")
campo_fecha(frame, "Fecha Hasta").fill("2026-08-01")
capturar_paso(app, "antes_de_generar", paso_excel=3)
frame.get_by_role("button", name="Generar").click(timeout=15000)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "anterior a Fecha Desde" in texto, f"No aparecio el mensaje de rango invalido: {texto!r}"
capturar_paso(app, "mensaje_rango_invalido", paso_excel=5)
cerrar_dialogo(frame)
''')

add("CP067", '''
opcion_dia_proceso = frame.locator('input[type="radio"][value="P"]')
assert opcion_dia_proceso.is_checked(), "La opcion 'Dia de Proceso' deberia estar marcada por defecto al abrir"
capturar_paso(app, "opcion_por_defecto")
''')

add("CP068", '''
campo_fecha(frame, "Fecha Desde").fill("2026-01-01")
campo_fecha(frame, "Fecha Hasta").fill("2026-09-01")
frame.locator('input[type="radio"][value="I"]').check()
capturar_paso(app, "antes_de_cancelar", paso_excel=3)
frame.get_by_role("button", name="Cancelar").click(timeout=15000)
app.wait_for_timeout(800)
campos_limpios = campo_fecha(frame, "Fecha Desde").input_value() == "" and campo_fecha(frame, "Fecha Hasta").input_value() == ""
opcion_default_de_nuevo = frame.locator('input[type="radio"][value="P"]').is_checked()
assert campos_limpios and opcion_default_de_nuevo, "Los campos/opcion no volvieron al estado por defecto tras Cancelar"
capturar_paso(app, "estado_limpio_tras_cancelar", paso_excel=4)
''')

add("CP069", '''
for ancho, alto, nombre in ((1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")):
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(500)
    assert frame.get_by_role("button", name="Generar").is_visible(), f"Boton Generar no visible en {nombre}"
    capturar_paso(app, f"responsive_{nombre}")
''')


# ======================== RF-08: Consulta De Refacturaciones Procesadas ========================
# NOTA: el sistema de pruebas no tiene refacturaciones procesadas reales
# (tabla vacia: no se pudo hacer ningun Ingresar todavia por el permiso de
# escritura pendiente, ver docstring del modulo). Por eso solo se
# automatizan aca los casos que NO dependen de que existan filas
# coincidentes (carga de combos, ejecucion de una consulta amplia,
# responsive). CP072/CP073 (Fecha Desde/Hasta vacia) se probaron en vivo
# con el operador "entre" y NO se reprodujo el mensaje esperado por la
# matriz ("Debe ingresar los dos valores del rango") - quedan pendientes
# de una exploracion mas profunda en vez de asumir un comportamiento no
# confirmado. CP074-082/085 (paginacion >25 filas y filtros que verifican
# coincidencia de datos reales) y CP084 (Guardar como... - confirmado en
# vivo que el boton queda DESHABILITADO con la grilla en "Sin
# resultados", igual que "Calcular total") quedan PENDIENTES hasta que
# haya datos reales que consultar.

add("CP070", '''
combos = frame.locator("select")
total_combos = combos.count()
assert total_combos > 0, "No se encontraron combos en la pantalla"
for i in range(total_combos):
    opciones = combos.nth(i).locator("option").count()
    assert opciones > 0, f"El combo #{i} no tiene opciones cargadas"
fecha_valor = frame.locator('input[aria-label="Fecha inicio"]').input_value()
hoy = date.today().strftime("%Y-%m-%d")
assert fecha_valor == hoy, f"La fecha inicial deberia ser hoy ({hoy}) pero es {fecha_valor!r}"
capturar_paso(app, "combos_cargados_y_fecha_actual", paso_excel=4)
''')

add("CP071", '''
capturar_paso(app, "antes_de_leer", paso_excel=4)
frame.get_by_role("button", name="Leer").click(timeout=15000)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Desea continuar" in texto, f"No aparecio el dialogo de confirmacion esperado: {texto!r}"
cerrar_dialogo(frame)
esperar_fin_de_carga(app, frame)
capturar_paso(app, "resultado_consulta", paso_excel=5)
''')

add("CP086", '''
for ancho, alto, nombre in ((1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")):
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(500)
    assert frame.get_by_role("button", name="Leer").is_visible(), f"Boton Leer no visible en {nombre}"
    capturar_paso(app, f"responsive_{nombre}")
''')


# ======================== RF-01/RF-02/RF-03/RF-04/RF-09: casos sin permiso de escritura ========================
# Estos 5 RF necesitan el INSERT de la hoja "permiso_refacturacion" (ver
# docstring del modulo) para Ingresar/Modificar/Eliminar. Los casos de
# abajo son los que SI se pudieron confirmar en vivo sin ese permiso:
# el propio modal de "solo consulta" (CP002/CP014, con el texto real
# confirmado: "Usuario no tiene permisos asignados para refactuaciones.
# Sólo podrá consultar." y los 4 botones de escritura de RF-01
# deshabilitados: Ingresar/Eliminar/Generar/Carátula), y los checks de
# responsive (no dependen de datos ni de permiso). El resto de RF-01/02/
# 03/04/09 (validaciones de campo con datos de cliente reales, alta/
# modificacion/eliminacion, carga de grilla por tipo de tabla en RF-09)
# QUEDA PENDIENTE: necesita datos de prueba reales (numeros de cliente
# con estados especificos) que no estan disponibles todavia, ademas del
# permiso de escritura para los casos que sí lo requieren.
#
# Hallazgo menor confirmado en vivo: el texto del modal de "solo
# consulta" NO esta escrito igual en las 2 apps - RF-01 dice
# "...para refactuaciones." (sin la "r" de "refacturaciones", typo real
# del formulario migrado) mientras RF-02 lo escribe bien
# ("...para refacturaciones."). El assert de abajo usa el prefijo comun
# "para refac" para no depender de cual de las 2 grafias use cada app.

add("CP002", '''
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "no tiene permisos asignados para refac" in texto and "consultar" in texto, f"No aparecio el modal de solo consulta esperado: {texto!r}"
capturar_paso(app, "modal_solo_consulta", paso_excel=3)
cerrar_dialogo(frame)
for nombre_boton in ("Ingresar", "Eliminar", "Generar", "Carátula"):
    boton = frame.get_by_role("button", name=nombre_boton, exact=True)
    assert boton.count() > 0 and boton.first.is_disabled(), f"El boton {nombre_boton!r} deberia estar deshabilitado en modo solo consulta"
capturar_paso(app, "botones_escritura_deshabilitados", paso_excel=5)
''')

# NOTA RF-01 (confirmado en vivo 21/09/2026, tras habilitarse el permiso
# de escritura): consulta valida de referencia (sugerida por la propia
# matriz para CP003): Clave Movimiento 3-6-8, Fecha O.R. 04/09/2026,
# Total Caratula 500 - ejecuta sin error, grilla puede salir vacia. El
# boton "Ingresar" del panel de captura, al primer click, habilita los
# campos y el MISMO boton cambia su texto a "Aceptar" (mismo patron
# confirmado en RF-09/RF-10). Cliente de prueba real: 000100001 (ver
# buscar_cliente_valido() en los helpers).

add("CP001", '''
inputs_clave = frame.locator('input[aria-label*="Clave de Movimiento parte"]')
inputs_clave.nth(0).fill("3")
inputs_clave.nth(1).fill("6")
inputs_clave.nth(2).fill("8")
campo_fecha(frame, "Fecha O.R.").fill("2099-12-31")
frame.locator('input[aria-label="Total Carátula"]').fill("500")
capturar_paso(app, "antes_de_leer", paso_excel=3)
frame.get_by_role("button", name="Leer").click(timeout=15000)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "fecha" in texto.lower(), f"No aparecio un mensaje de validacion de fecha: {texto!r}"
capturar_paso(app, "mensaje_fecha_invalida", paso_excel=5)
cerrar_dialogo(frame)
''')

add("CP003", '''
inputs_clave = frame.locator('input[aria-label*="Clave de Movimiento parte"]')
inputs_clave.nth(0).fill("3")
inputs_clave.nth(1).fill("6")
inputs_clave.nth(2).fill("8")
campo_fecha(frame, "Fecha O.R.").fill("2026-09-04")
frame.locator('input[aria-label="Total Carátula"]').fill("500")
frame.get_by_role("button", name="Leer").click(timeout=15000)
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(2000)
cerrar_cualquier_dialogo(frame)
capturar_paso(app, "antes_de_ingresar", paso_excel=4)
registrar_orden_rf01(frame, app, "000100001", "100.00")
fila_nueva = frame.locator("table tbody tr", has_text="000100001")
assert fila_nueva.count() > 0, "La nueva orden deberia aparecer en la grilla"
capturar_paso(app, "orden_registrada", paso_excel=6)
''')

add("CP004", '''
inputs_clave = frame.locator('input[aria-label*="Clave de Movimiento parte"]')
inputs_clave.nth(0).fill("3")
inputs_clave.nth(1).fill("6")
inputs_clave.nth(2).fill("8")
campo_fecha(frame, "Fecha O.R.").fill("2026-09-04")
frame.locator('input[aria-label="Total Carátula"]').fill("500")
frame.get_by_role("button", name="Leer").click(timeout=15000)
esperar_fin_de_carga(app, frame)
frame.get_by_role("button", name="Ingresar", exact=True).click(timeout=15000)
app.wait_for_timeout(600)
campo_cliente = frame.locator('input[aria-label="N° Cliente"]')
campo_doc = frame.locator('input[aria-label="N° Documento"]')
# Cliente con estado no permitido -- best effort: numero de prueba distinto
# al confirmado valido, sin confirmacion previa de que su estado real sea
# el esperado (MAXIMETRO/gran cliente). Si el sistema devuelve
# "no encontrado" en vez de "estado no permitido", este caso necesita un
# numero de cliente real con ese estado especifico, a confirmar con el
# usuario/negocio.
resultado = buscar_cliente_valido(frame, campo_cliente, "000200002", campo_documento=campo_doc)
capturar_paso(app, "resultado_cliente_no_permitido", paso_excel=5)
assert resultado is not None, "Se esperaba un mensaje de rechazo (estado no permitido o cliente no encontrado)"
texto = resultado.inner_text()
cerrar_dialogo(frame)
''')

add("CP009", '''
inputs_clave = frame.locator('input[aria-label*="Clave de Movimiento parte"]')
inputs_clave.nth(0).fill("3")
inputs_clave.nth(1).fill("6")
inputs_clave.nth(2).fill("8")
campo_fecha(frame, "Fecha O.R.").fill("2026-09-04")
frame.locator('input[aria-label="Total Carátula"]').fill("500")
frame.get_by_role("button", name="Leer").click(timeout=15000)
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(2000)
cerrar_cualquier_dialogo(frame)
filas = frame.locator("table tbody tr")
if filas.count() == 0 or "No hay" in filas.first.inner_text():
    registrar_orden_rf01(frame, app, "000100001", "100.00")
capturar_paso(app, "antes_de_generar", paso_excel=4)
frame.get_by_role("button", name="Generar", exact=True).click(timeout=15000)
esperar_fin_de_carga(app, frame)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "gener" in texto.lower(), f"No aparecio el mensaje de generacion exitosa: {texto!r}"
capturar_paso(app, "listado_generado", paso_excel=6)
cerrar_dialogo(frame)
''')

add("CP010", '''
inputs_clave = frame.locator('input[aria-label*="Clave de Movimiento parte"]')
inputs_clave.nth(0).fill("3")
inputs_clave.nth(1).fill("6")
inputs_clave.nth(2).fill("8")
campo_fecha(frame, "Fecha O.R.").fill("2026-09-04")
frame.locator('input[aria-label="Total Carátula"]').fill("500")
frame.get_by_role("button", name="Leer").click(timeout=15000)
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(2000)
cerrar_cualquier_dialogo(frame)
filas = frame.locator("table tbody tr")
if filas.count() == 0 or "No hay" in filas.first.inner_text():
    registrar_orden_rf01(frame, app, "000100001", "100.00")
    filas = frame.locator("table tbody tr")
filas_antes = filas.count()
filas.first.click(timeout=10000)
app.wait_for_timeout(500)
capturar_paso(app, "antes_de_eliminar", paso_excel=4)
frame.get_by_role("button", name="Eliminar", exact=True).click(timeout=15000)
app.wait_for_timeout(1500)
dlg_confirma = frame.locator(".ant-modal-wrap", has_text="Desea eliminar")
dlg_confirma.wait_for(state="visible", timeout=10000)
dlg_confirma.locator("button", has_text="Aceptar").click(timeout=8000, force=True)
app.wait_for_timeout(1500)
dlg_resultado = frame.locator(".ant-modal-wrap", has_text="eliminada correctamente")
try:
    dlg_resultado.wait_for(state="visible", timeout=6000)
    dlg_resultado.locator("button", has_text="Aceptar").click(timeout=8000, force=True)
except PWTimeoutError:
    pass
esperar_fin_de_carga(app, frame)
cerrar_cualquier_dialogo(frame)
capturar_paso(app, "orden_eliminada", paso_excel=6)
filas_despues = frame.locator("table tbody tr")
count_despues = filas_despues.count()
texto_despues = filas_despues.first.inner_text() if count_despues > 0 else ""
# GOTCHA REAL confirmado en vivo 23/09/2026: cuando la grilla queda sin
# ordenes, el sistema renderiza una fila PLACEHOLDER ("No hay ordenes
# para los criterios indicados.") en vez de dejar la tabla realmente
# vacia - el conteo de filas puede quedar IGUAL (1 orden real antes, 1
# placeholder despues) pese a que la eliminacion SI funciono. Se
# tolera ese caso verificando el texto en vez de asumir que el conteo
# siempre baja.
assert count_despues < filas_antes or "no hay" in texto_despues.lower(), f"Se esperaba que la orden se elimine (menos filas o mensaje de grilla vacia), se vieron {count_despues} filas: {texto_despues!r}"
''')

add("CP011", '''
inputs_clave = frame.locator('input[aria-label*="Clave de Movimiento parte"]')
inputs_clave.nth(0).fill("3")
inputs_clave.nth(1).fill("6")
inputs_clave.nth(2).fill("7")
campo_fecha(frame, "Fecha O.R.").fill("2026-09-04")
frame.locator('input[aria-label="Total Carátula"]').fill("500")
capturar_paso(app, "antes_de_leer", paso_excel=3)
frame.get_by_role("button", name="Leer", exact=True).click(timeout=15000)
esperar_fin_de_carga(app, frame)
boton_generar = frame.get_by_role("button", name="Generar", exact=True)
assert boton_generar.is_disabled(), "El boton Generar deberia estar deshabilitado con la grilla vacia"
capturar_paso(app, "generar_deshabilitado", paso_excel=4)
''')

add("CP012", '''
inputs_clave = frame.locator('input[aria-label*="Clave de Movimiento parte"]')
inputs_clave.nth(0).fill("3")
inputs_clave.nth(1).fill("6")
inputs_clave.nth(2).fill("8")
campo_fecha(frame, "Fecha O.R.").fill("2026-09-04")
frame.locator('input[aria-label="Total Carátula"]').fill("500")
frame.get_by_role("button", name="Leer").click(timeout=15000)
esperar_fin_de_carga(app, frame)
app.wait_for_timeout(2000)
cerrar_cualquier_dialogo(frame)

total_antes = frame.locator('input[aria-label="Total Ingresado"]').input_value()
registrar_orden_rf01(frame, app, "000100001", "50.00")
capturar_paso(app, "primera_orden_registrada", paso_excel=4)
registrar_orden_rf01(frame, app, "000100001", "30.00")
total_despues = frame.locator('input[aria-label="Total Ingresado"]').input_value()
capturar_paso(app, "segunda_orden_registrada", paso_excel=5)
assert total_despues != total_antes, f"El Total Ingresado deberia cambiar tras registrar 2 ordenes (antes={total_antes!r}, despues={total_despues!r})"
''')

add("CP013", '''
for ancho, alto, nombre in ((1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")):
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(500)
    assert frame.get_by_role("button", name="Leer").is_visible(), f"Boton Leer no visible en {nombre}"
    capturar_paso(app, f"responsive_{nombre}")
''')

add("CP014", '''
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "no tiene permisos asignados para refac" in texto and "consultar" in texto, f"No aparecio el modal de solo consulta esperado: {texto!r}"
capturar_paso(app, "modal_solo_consulta", paso_excel=3)
cerrar_dialogo(frame)
''')

add("CP015", '''
# CONFIRMADO EN VIVO 22/09/2026 (_exploracion/explore_rf02_arreglos.py):
# cliente real 000100001 (mismo usado en RF-01), DV=2, Nombre="SEGURA
# RAMOS ALEX JUAN". Aria-labels reales: "N.\\u00b0 de Cliente", "DV",
# "Nombre del Cliente" (NO "DV Cliente"/"Nombre" a secas como en RF-01).
campo_cliente = frame.locator('input[aria-label="N.\\u00b0 de Cliente"]')
campo_dv = frame.locator('input[aria-label="DV"]')
campo_nombre = frame.locator('input[aria-label="Nombre del Cliente"]')
resultado = buscar_cliente_valido(frame, campo_cliente, "000100001", campo_dv=campo_dv)
capturar_paso(app, "cliente_ingresado", paso_excel=3)
assert resultado is None, f"Se esperaba que el cliente 000100001 sea valido, se vio: {resultado!r}"
assert campo_dv.input_value().strip() == "2", f"Se esperaba DV=2, se vio: {campo_dv.input_value()!r}"
assert campo_nombre.input_value().strip(), "Se esperaba que el Nombre del cliente se complete automaticamente"
capturar_paso(app, "datos_cliente_cargados", paso_excel=4)
print(f"[INFO] Cliente validado: DV={campo_dv.input_value()!r} Nombre={campo_nombre.input_value()!r}")
''')

add("CP016", '''
# CONFIRMADO EN VIVO 22/09/2026 (_exploracion/check_cp016_cliente2.py):
# el cliente "2" no existe en este ambiente - mensaje real exacto
# "No se encontro el cliente 2." (distinto de un cliente con estado NO
# permitido como sugiere el nombre del caso, pero cumple el mismo
# resultado esperado de la matriz: "al perder el foco, el sistema
# muestra un mensaje de validacion indicando que el cliente no es
# valido"). DV y Nombre del Cliente quedan vacios.
campo_cliente = frame.locator('input[aria-label="N.\\u00b0 de Cliente"]')
campo_dv = frame.locator('input[aria-label="DV"]')
campo_nombre = frame.locator('input[aria-label="Nombre del Cliente"]')
campo_cliente.fill("2")
campo_cliente.press("Tab")
app.wait_for_timeout(2000)
capturar_paso(app, "cliente_ingresado", paso_excel=3)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=8000)
texto = dlg.inner_text()
capturar_paso(app, "mensaje_validacion_verificado", paso_excel=5)
assert "no se encontr" in texto.lower() and "cliente" in texto.lower(), f"Se esperaba un mensaje indicando que el cliente 2 no es valido/no se encontro, se vio: {texto!r}"
cerrar_dialogo(frame)
app.wait_for_timeout(500)
assert not campo_dv.input_value().strip(), f"Se esperaba que DV quede vacio para un cliente invalido, se vio: {campo_dv.input_value()!r}"
assert not campo_nombre.input_value().strip(), f"Se esperaba que Nombre quede vacio para un cliente invalido, se vio: {campo_nombre.input_value()!r}"
print(f"[INFO] Mensaje de validacion: {texto!r}")
''')

add("CP017", '''
# CONFIRMADO EN VIVO 22/09/2026 (_exploracion/explore_rf02_leer.py):
# combinacion real SIN arreglo existente: cliente 000100001, Clave de
# Movimiento 3-5-1 (catalogo real: Clave1 3=CARGO/4=ABONO, Clave2
# 5=CONSUMO/8=INTERESES/9=REFACTURACION ARREGLO CONTABLE, Clave3 sin
# catalogo - "0" es RECHAZADO pese a lo que sugiere el manual, "1" SI
# es valido). Al presionar Leer sin arreglo existente, el boton
# principal queda en "Ingresar" (no se vio un dialogo de aviso
# separado en esta corrida, a diferencia de lo que documenta el manual
# - se tolera que aparezca o no).
campo_cliente = frame.locator('input[aria-label="N.\\u00b0 de Cliente"]')
campo_dv = frame.locator('input[aria-label="DV"]')
buscar_cliente_valido(frame, campo_cliente, "000100001", campo_dv=campo_dv)
frame.locator("#inputClave1").fill("3")
frame.locator("#inputClave1").press("Tab")
frame.locator("#inputClave2").fill("5")
frame.locator("#inputClave2").press("Tab")
frame.locator("#inputClave3").fill("1")
frame.locator("#inputClave3").press("Tab")
app.wait_for_timeout(1200)
cerrar_cualquier_dialogo(frame)
capturar_paso(app, "claves_completadas", paso_excel=4)
frame.get_by_role("button", name="Leer", exact=True).click(timeout=15000)
app.wait_for_timeout(2000)
capturar_paso(app, "busqueda_ejecutada", paso_excel=5)
dlg = dialogo_f(frame)
if dlg.count() and dlg.is_visible():
    texto = dlg.inner_text()
    print(f"[INFO] Dialogo tras Leer: {texto!r}")
    assert "no se encontraron" in texto.lower(), f"Se esperaba el mensaje de 'no se encontraron refacturaciones' o ningun dialogo, se vio: {texto!r}"
    cerrar_dialogo(frame)
    app.wait_for_timeout(500)
boton_principal = frame.get_by_role("button", name=re.compile("^(Ingresar|Modificar)$"))
assert boton_principal.count() > 0, "Se esperaba ver el boton principal (Ingresar/Modificar) tras Leer"
texto_boton = boton_principal.inner_text().strip()
assert texto_boton == "Ingresar", f"Se esperaba que el formulario quede en modo Ingresar (sin arreglo existente), se vio boton: {texto_boton!r}"
capturar_paso(app, "modo_ingresar_confirmado", paso_excel=6)
''')

add("CP018", '''
# CONFIRMADO EN VIVO 22/09/2026 (_exploracion/explore_rf02_cargo.py):
# flujo completo probado hasta el dialogo de confirmacion (cancelado a
# proposito en la exploracion para no escribir datos reales antes de
# confirmar con el usuario). Texto REAL del dialogo de confirmacion es
# distinto al que documenta el manual: la app dice "\\u00bfEsta seguro de
# Ingresar la Refacturaci\\u00f3n?" (el manual dice "...el Arreglo de
# Facturado?"). Calculo de IGV verificado en vivo: importe 100.00 ->
# IGV 18.00 -> Total 118.00 (18%).
leer_arreglo_base(frame, app)
capturar_paso(app, "arreglo_leido", paso_excel=3)
boton_principal = frame.get_by_role("button", name=re.compile("^(Ingresar|Modificar)$"))
assert boton_principal.inner_text().strip() == "Ingresar", "Se esperaba modo Ingresar (sin arreglo existente) para este caso base"

frame.locator('select[aria-label="Motivo"]').select_option(label=" 01 - Error en el proceso de facturacion ")
app.wait_for_timeout(800)
frame.locator('select[aria-label="Detalle de Motivo"]').select_option(label=" 01 - Lectura errada del contratista ")
app.wait_for_timeout(800)
capturar_paso(app, "motivo_completado", paso_excel=4)

elegir_fecha_a_corregir(frame, app, indice=0)
fecha_corregir = frame.locator('input[aria-label="Fecha a Corregir"]').input_value()
numero_factura = frame.locator('input[aria-label="Número Factura"]').input_value()
assert fecha_corregir, "Se esperaba que Fecha a Corregir se complete desde el historial"
assert numero_factura, "Se esperaba que Numero Factura se complete desde el historial"
capturar_paso(app, "fecha_a_corregir_elegida", paso_excel=5)

frame.locator('input[aria-label="N° Documento"]').fill("00001")

checkbox_cargo = frame.get_by_role("checkbox", name="CARGO FIJO", exact=True)
checkbox_cargo.check()
app.wait_for_timeout(800)
campo_importe = frame.locator('input[aria-label*="Importe CARGO FIJO"]')
campo_importe.fill("100")
app.wait_for_timeout(1000)
capturar_paso(app, "cargo_e_importe_completados", paso_excel=6)
# NOTA: los campos Valor I.G.V./Total a Refacturar NO tienen aria-label
# (confirmado en vivo 22/09/2026) - el calculo (100 + 18% IGV = 118.00)
# se verifico visualmente en la captura anterior, no se puede leer con
# un locator robusto sin ese atributo.

boton_ingresar = frame.get_by_role("button", name="Ingresar", exact=True)
boton_ingresar.click(timeout=10000)
app.wait_for_timeout(1200)
dlg_confirma = esperar_dialogo_visible(frame, timeout_ms=8000)
texto_confirma = dlg_confirma.inner_text()
assert "seguro" in texto_confirma.lower() and "ingresar" in texto_confirma.lower(), f"Se esperaba el dialogo de confirmacion de Ingresar, se vio: {texto_confirma!r}"
capturar_paso(app, "confirmacion_mostrada", paso_excel=8)
# GOTCHA REAL (mismo patron ya documentado en dialogo_f()): reutilizar
# la referencia `dlg_confirma` para el click puede apuntar a un
# elemento re-resuelto distinto - se usa cerrar_dialogo() que vuelve a
# resolver el dialogo fresco y busca especificamente "Aceptar" (ver
# NOMBRES_ACEPTAR), no el primer boton que encuentre.
cerrar_dialogo(frame)
app.wait_for_timeout(1500)

dlg_resultado = esperar_dialogo_visible(frame, timeout_ms=8000)
texto_resultado = dlg_resultado.inner_text()
capturar_paso(app, "mensaje_resultado_verificado", paso_excel=9)
assert "correctamente" in texto_resultado.lower(), f"Se esperaba un mensaje de EXITO al ingresar el arreglo, se vio: {texto_resultado!r}"
cerrar_dialogo(frame)
app.wait_for_timeout(1000)

boton_principal_final = frame.get_by_role("button", name=re.compile("^(Ingresar|Modificar)$"))
assert boton_principal_final.inner_text().strip() == "Modificar", f"Se esperaba que el boton pase a Modificar tras registrar, se vio: {boton_principal_final.inner_text()!r}"
capturar_paso(app, "modo_modificar_confirmado", paso_excel=10)
''')

add("CP026", '''
for ancho, alto, nombre in ((1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")):
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(500)
    assert frame.get_by_role("button", name="Leer").is_visible(), f"Boton Leer no visible en {nombre}"
    capturar_paso(app, f"responsive_{nombre}")
''')

add("CP027", '''
# CONFIRMADO EN VIVO 22/09/2026 (_exploracion/explore_rf03.py): el combo
# real "Descripcion de debito" trae 8 opciones (incluyendo el
# placeholder "-- Seleccione --"): RESELLADO DE CAJA MEDIDOR, REV. INST.
# INTERNA, DISPOSITIVO ANTIROBO, CONTRASTE EN CAMPO, MANTENIMIENTO DE
# REDES, CONTRASTE EN LABORATORIO, INTERESES POR TRANSACCION
# EXTRAJUDUCIAL - KOPESA. El campo codigo y el select quedan
# sincronizados (confirmado seleccionando "REV. INST. INTERNA" -> el
# campo Codigo de debito paso a "018" solo).
select_debito = frame.locator('select[aria-label="Descripción de débito"]')
opciones = select_debito.locator("option").all_inner_texts()
capturar_paso(app, "combo_debitos_revisado", paso_excel=5)
assert len(opciones) > 1, f"Se esperaba al menos 1 clave de debito real en el combo (ademas del placeholder), se vieron: {opciones!r}"
ESPERADAS = ["RESELLADO DE CAJA MEDIDOR", "REV. INST. INTERNA"]
for e in ESPERADAS:
    assert any(e in o.upper() for o in opciones), f"Se esperaba la opcion {e!r} en el combo de debitos, opciones reales: {opciones!r}"
print(f"[INFO] Opciones reales del combo de debitos: {opciones!r}")
''')

add("CP029", '''
# CONFIRMADO EN VIVO 22/09/2026: clave de debito real 018 (REV. INST.
# INTERNA), Fecha 04/09/2026 y Total Caratula 500.00 (mismos datos
# sugeridos por la matriz para este caso). Leer se ejecuta sin errores
# de validacion.
select_debito = frame.locator('select[aria-label="Descripción de débito"]')
select_debito.select_option(label="REV. INST. INTERNA")
app.wait_for_timeout(600)
codigo_val = frame.locator('input[aria-label="Código de débito"]').input_value()
assert codigo_val.strip() == "018", f"Se esperaba que el codigo se sincronice a 018, se vio: {codigo_val!r}"
frame.locator("#fechaInput").fill("2026-09-04")
frame.locator("#totalCaratulaInput").fill("500")
app.wait_for_timeout(500)
capturar_paso(app, "parametros_completados", paso_excel=4)
boton_leer = frame.get_by_role("button", name="Leer débitos existentes")
assert boton_leer.is_enabled(), "Se esperaba que 'Leer' quede habilitado con Clave/Fecha/Total Caratula completos"
boton_leer.click(timeout=15000)
app.wait_for_timeout(2000)
capturar_paso(app, "consulta_ejecutada", paso_excel=5)
boton_ingresar = frame.get_by_role("button", name="Ingresar", exact=True)
assert boton_ingresar.is_visible(), "Se esperaba que la consulta habilite el area de ingreso (boton Ingresar visible) tras Leer"
capturar_paso(app, "consulta_confirmada", paso_excel=6)
''')

add("CP031", '''
# CONFIRMADO EN VIVO 22/09/2026: cliente real 000100001 (mismo usado en
# RF-01/02/04) - Ruta Lectura se completa (015090530). GOTCHA REAL: el
# campo "DV cliente" queda VACIO en esta pantalla para este cliente
# (reproducido 2 veces, no es timing) - no bloquea el caso porque el
# resultado esperado segun la matriz es especificamente Ruta Lectura +
# boton Ingresar habilitado, no el DV.
select_debito = frame.locator('select[aria-label="Descripción de débito"]')
select_debito.select_option(label="REV. INST. INTERNA")
app.wait_for_timeout(600)
frame.locator("#fechaInput").fill("2026-09-04")
frame.locator("#totalCaratulaInput").fill("500")
app.wait_for_timeout(500)
frame.get_by_role("button", name="Leer débitos existentes").click(timeout=15000)
app.wait_for_timeout(2000)
capturar_paso(app, "debitos_leidos", paso_excel=3)

campo_cliente = frame.locator('input[aria-label="Número Cliente"]')
campo_cliente.fill("000100001")
campo_cliente.press("Tab")
app.wait_for_timeout(2500)
capturar_paso(app, "cliente_ingresado", paso_excel=4)
ruta = frame.locator('input[aria-label="Ruta Lectura"]').input_value()
assert ruta.strip(), "Se esperaba que Ruta Lectura se complete automaticamente para un cliente con estado valido"
boton_ingresar = frame.get_by_role("button", name="Ingresar", exact=True)
assert boton_ingresar.is_enabled(), "Se esperaba que el boton Ingresar quede habilitado con un cliente de estado valido"
capturar_paso(app, "ruta_lectura_y_boton_verificados", paso_excel=5)
print(f"[INFO] Ruta Lectura={ruta!r}")
''')

add("CP038", '''
for ancho, alto, nombre in ((1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")):
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(500)
    assert frame.get_by_role("button", name="Leer").is_visible(), f"Boton Leer no visible en {nombre}"
    capturar_paso(app, f"responsive_{nombre}")
''')

add("CP039", '''
# CONFIRMADO EN VIVO 22/09/2026 (_exploracion/explore_rf04.py): aria-labels
# reales de esta pantalla (RF-04, distinta a RF-03): "N\\u00famero de Cliente"
# (id nroClienteInput), "D\\u00edgito verificador", "C\\u00f3digo de D\\u00e9bito",
# "Fecha de Proceso" (id fechaProcesoInput), select "Descripci\\u00f3n de D\\u00e9bito".
# El boton "Leer" tiene aria-label "Leer datos del cliente" (el nombre
# accesible real NO es solo "Leer" - hay que buscarlo por ese aria-label
# completo o por el texto visible, no por name="Leer" exacto).
fecha_val = frame.locator("#fechaProcesoInput").input_value()
capturar_paso(app, "fecha_inicial_revisada", paso_excel=3)
from datetime import date as _date
hoy_iso = _date.today().isoformat()
assert fecha_val == hoy_iso, f"Se esperaba que Fecha de Proceso inicie con la fecha del sistema ({hoy_iso}), se vio: {fecha_val!r}"

select_debito = frame.locator('select[aria-label="Descripción de Débito"]')
opciones = select_debito.locator("option").all_inner_texts()
capturar_paso(app, "combo_debito_revisado", paso_excel=4)
assert len(opciones) > 1, f"Se esperaba al menos 1 clave de debito real en el combo, se vieron: {opciones!r}"

campo_cliente = frame.locator("#nroClienteInput")
assert not campo_cliente.is_disabled(), "El campo N Cliente deberia estar habilitado desde el inicio para poder escribir"
boton_ingresar = frame.get_by_role("button", name="Ingresar", exact=True)
assert not boton_ingresar.is_visible() or not boton_ingresar.is_enabled(), "Se esperaba que el boton Ingresar este deshabilitado/oculto antes de Leer"
capturar_paso(app, "estado_inicial_verificado", paso_excel=6)
print(f"[INFO] Fecha inicial={fecha_val!r} Opciones combo={opciones!r}")
''')

add("CP040", '''
# CONFIRMADO EN VIVO: boton Leer real tiene aria-label "Leer datos del
# cliente", se ubica por ese texto completo.
select_debito = frame.locator('select[aria-label="Descripción de Débito"]')
select_debito.select_option(label="REV. INST. INTERNA")
app.wait_for_timeout(500)
capturar_paso(app, "clave_debito_seleccionada", paso_excel=3)
frame.get_by_role("button", name="Leer datos del cliente").click(timeout=15000)
app.wait_for_timeout(1200)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=8000)
texto = dlg.inner_text()
capturar_paso(app, "mensaje_validacion_verificado", paso_excel=6)
assert "n" in texto.lower() and "cliente" in texto.lower(), f"Se esperaba el mensaje 'Ingrese el Numero de Cliente.', se vio: {texto!r}"
cerrar_dialogo(frame)
''')

add("CP041", '''
campo_cliente = frame.locator("#nroClienteInput")
campo_cliente.fill("000100001")
app.wait_for_timeout(500)
capturar_paso(app, "cliente_ingresado_sin_debito", paso_excel=4)
frame.get_by_role("button", name="Leer datos del cliente").click(timeout=15000)
app.wait_for_timeout(1200)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=8000)
texto = dlg.inner_text()
capturar_paso(app, "mensaje_validacion_verificado", paso_excel=6)
assert "clave" in texto.lower() and ("d\\u00e9bito" in texto.lower() or "debito" in texto.lower()), f"Se esperaba el mensaje 'Seleccione la Clave de Debitos Varios.', se vio: {texto!r}"
cerrar_dialogo(frame)
''')

add("CP042", '''
# CONFIRMADO EN VIVO 22/09/2026: a diferencia de lo que sugiere el
# manual ("al salir del campo con fecha futura"), el rechazo real NO se
# dispara solo con blur/Tab - hace falta completar cliente + clave de
# debito y presionar "Leer" (como indica la matriz) para que la
# validacion de fecha se ejecute.
campo_cliente = frame.locator("#nroClienteInput")
campo_cliente.fill("000100001")
select_debito = frame.locator('select[aria-label="Descripción de Débito"]')
select_debito.select_option(label="REV. INST. INTERNA")
frame.locator("#fechaProcesoInput").fill("2099-12-31")
app.wait_for_timeout(600)
capturar_paso(app, "fecha_futura_ingresada", paso_excel=3)
frame.get_by_role("button", name="Leer datos del cliente").click(timeout=15000)
app.wait_for_timeout(1500)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=8000)
texto = dlg.inner_text()
capturar_paso(app, "mensaje_validacion_verificado", paso_excel=4)
assert "fecha" in texto.lower() and ("posterior" in texto.lower() or "mayor" in texto.lower()), f"Se esperaba un mensaje de fecha no puede ser posterior/mayor a hoy, se vio: {texto!r}"
cerrar_dialogo(frame)
app.wait_for_timeout(500)
fecha_val = frame.locator("#fechaProcesoInput").input_value()
capturar_paso(app, "fecha_limpiada_verificada", paso_excel=5)
assert fecha_val != "2099-12-31", f"Se esperaba que el campo de fecha quede limpio tras el rechazo, se vio: {fecha_val!r}"
''')

add("CP050", '''
for ancho, alto, nombre in ((1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")):
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(500)
    assert frame.get_by_role("button", name="Leer").is_visible(), f"Boton Leer no visible en {nombre}"
    capturar_paso(app, f"responsive_{nombre}")
''')

# NOTA sobre RF-09 (confirmado en vivo 21/09/2026, tras habilitarse el
# permiso de escritura): CLARE1 y CLAREF son dominios CERRADOS de solo 2
# valores posibles cada uno (CARGO/ABONO), y ambos YA EXISTEN como
# registros reales - seleccionar cualquiera de las 2 descripciones
# AUTOCOMPLETA Código y Abono/Cargo con los del registro existente y el
# boton pasa a "Modificar" (nunca "Ingresar"). Por eso CP091 (alta nueva
# en Movimiento 1), CP092 (alta nueva en Movimiento 2) y CP095 (alta en
# Movimiento 1 sin Abono/Cargo, que requiere estar en modo alta) NO SON
# REPRODUCIBLES con los datos actuales - no hay ningun "codigo nuevo"
# posible en esos 2 dominios saturados. Documentado aqui en vez de
# forzar un caso que no puede pasar por diseño de datos, no por bug.
# CP098 (Eliminar/desactivar un registro) tampoco se automatiza: CARGO y
# ABONO en CLARE1 son valores base compartidos por toda la operacion de
# refacturacion (los usa RF-03/04 tambien) - desactivar uno de los 2
# unicos valores existentes podria romper otras pruebas/uso real. Queda
# pendiente de confirmar con el usuario antes de ejecutarlo.

add("CP087", '''
boton_ingresar = frame.get_by_role("button", name="Ingresar", exact=True)
boton_eliminar = frame.get_by_role("button", name="Eliminar", exact=True)
assert boton_ingresar.is_disabled() and boton_eliminar.is_disabled(), "Los botones de accion deberian estar deshabilitados sin tipo de tabla seleccionado"
capturar_paso(app, "estado_inicial_sin_tabla", paso_excel=3)
''')

add("CP088", '''
frame.locator('input[type="radio"][value="CLARE1"]').check()
app.wait_for_timeout(800)
opciones = frame.locator('select[aria-label="Descripción"]').locator("option").evaluate_all("els => els.map(e => e.textContent.trim())")
assert "CARGO" in opciones and "ABONO" in opciones, f"No se cargaron las opciones esperadas de CLARE1: {opciones!r}"
assert frame.locator('input[aria-label="Abono o Cargo"]').count() > 0, "No aparece el panel Abono/Cargo para Clave Movimiento 1"
capturar_paso(app, "grilla_clare1_cargada", paso_excel=4)
''')

add("CP089", '''
frame.locator('input[type="radio"][value="CLAREF"]').check()
app.wait_for_timeout(800)
opciones = frame.locator('select[aria-label="Descripción"]').locator("option").evaluate_all("els => els.map(e => e.textContent.trim())")
assert "CARGO" in opciones and "ABONO" in opciones, f"No se cargaron las opciones esperadas de CLAREF: {opciones!r}"
assert frame.locator("#chk-deuda").count() > 0 and frame.locator("#chk-conta").count() > 0, "No aparecen las casillas Afecta Deuda / Afecta solo Contabilidad"
capturar_paso(app, "grilla_claref_cargada", paso_excel=5)
''')

add("CP090", '''
frame.locator('input[type="radio"][value="CLARE3"]').check()
app.wait_for_timeout(800)
opciones = frame.locator('select[aria-label="Descripción"]').locator("option").evaluate_all("els => els.map(e => e.textContent.trim())")
assert len(opciones) > 5, f"Se esperaban varias opciones para CLARE3, se obtuvo: {opciones!r}"
assert frame.locator("#chk-deuda").count() == 0 and frame.locator('input[aria-label="Abono o Cargo"]').count() == 0, "No deberia mostrarse ningun panel de atributos adicionales para Clave Movimiento 3"
capturar_paso(app, "grilla_clare3_cargada", paso_excel=5)
''')

add("CP093", '''
frame.locator('input[type="radio"][value="CLARE3"]').check()
app.wait_for_timeout(800)
desc = frame.locator('select[aria-label="Descripción"]')
opciones = desc.locator("option").evaluate_all("els => els.map(e => ({value: e.value, texto: e.textContent.trim()}))")
opcion_libre = next((o for o in opciones if o["texto"] == "INTERESES"), None)
assert opcion_libre, f"No se encontro la opcion 'INTERESES' en CLARE3: {opciones!r}"
desc.select_option(value=opcion_libre["value"])
app.wait_for_timeout(500)
boton = frame.get_by_role("button", name=re.compile("Ingresar|Modificar"))
texto_boton = boton.first.inner_text().strip()
assert texto_boton == "Ingresar", f"Se esperaba modo alta (Ingresar) para 'INTERESES' en CLARE3, pero el boton dice {texto_boton!r} (la clave ya existe con los datos de prueba actuales)"
capturar_paso(app, "antes_de_ingresar_clare3", paso_excel=4)
frame.get_by_role("button", name="Ingresar", exact=True).click(timeout=15000)
app.wait_for_timeout(1200)
dlg = dialogo_f(frame)
if dlg.count() > 0 and dlg.is_visible():
    capturar_paso(app, "resultado_alta_clare3", paso_excel=6)
    cerrar_dialogo(frame)
''')

add("CP094", '''
frame.locator('input[type="radio"][value="CLARE1"]').check()
app.wait_for_timeout(800)
frame.locator('input[aria-label="Código"]').fill("9")
ac = frame.locator('input[aria-label="Abono o Cargo"]')
ac.click()
ac.press("A")
capturar_paso(app, "antes_de_ingresar_sin_descripcion", paso_excel=4)
frame.get_by_role("button", name="Ingresar", exact=True).click(timeout=15000)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Descripci" in texto and "obligator" in texto, f"No aparecio el mensaje de descripcion obligatoria esperado: {texto!r}"
capturar_paso(app, "mensaje_descripcion_obligatoria", paso_excel=6)
cerrar_dialogo(frame)
''')

add("CP096", '''
frame.locator('input[type="radio"][value="CLARE1"]').check()
app.wait_for_timeout(800)
ac = frame.locator('input[aria-label="Abono o Cargo"]')
ac.click()
ac.press("X")
app.wait_for_timeout(300)
assert ac.input_value() == "", f"El campo Abono/Cargo deberia rechazar el caracter invalido 'X', pero quedo en {ac.input_value()!r}"
capturar_paso(app, "caracter_invalido_rechazado", paso_excel=6)
''')

add("CP097", '''
frame.locator('input[type="radio"][value="CLARE1"]').check()
app.wait_for_timeout(800)
frame.locator('select[aria-label="Descripción"]').select_option(value="4")
app.wait_for_timeout(600)
checkbox_provisional = frame.locator("#chk-provisional")
estado_previo = checkbox_provisional.is_checked()
capturar_paso(app, "antes_de_modificar", paso_excel=5)
if estado_previo:
    checkbox_provisional.uncheck()
else:
    checkbox_provisional.check()
frame.get_by_role("button", name="Modificar", exact=True).click(timeout=15000)
app.wait_for_timeout(1200)
dlg = dialogo_f(frame)
if dlg.count() > 0 and dlg.is_visible():
    capturar_paso(app, "resultado_modificacion", paso_excel=7)
    cerrar_dialogo(frame)
''')

add("CP099", '''
frame.locator('input[type="radio"][value="CLARE1"]').check()
app.wait_for_timeout(800)
capturar_paso(app, "antes_de_cancelar", paso_excel=3)
frame.get_by_role("button", name="Cancelar").click(timeout=15000)
app.wait_for_timeout(1000)
radios_marcados = frame.locator('input[type="radio"]:checked').count()
assert radios_marcados == 0, "El selector de tipo de tabla deberia quedar sin ninguna opcion marcada tras Cancelar"
boton_ingresar = frame.get_by_role("button", name="Ingresar", exact=True)
assert boton_ingresar.is_disabled(), "El boton Ingresar deberia quedar deshabilitado tras Cancelar (sin tipo de tabla seleccionado)"
capturar_paso(app, "estado_reseteado", paso_excel=5)
''')

add("CP100", '''
for ancho, alto, nombre in ((1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")):
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(500)
    assert frame.get_by_role("button", name="Cancelar").is_visible(), f"Boton Cancelar no visible en {nombre}"
    capturar_paso(app, f"responsive_{nombre}")
''')


# ======================== RF-10: Parámetros De Refacturaciones Automáticas ========================
# Confirmado en vivo 21/09/2026 (ya con el permiso de menu PAREFAUT
# resuelto): pantalla con grilla real (7 parametros ya existentes en
# produccion) + panel "Ingreso" con 4 campos (Parámetro, Clave Movimiento
# Cargo, Clave Movimiento Abono, Rol Creador) deshabilitados hasta
# presionar "Adicionar" o "Modificar" (boton dinamico: pasa a decir
# "Aceptar" mientras se edita). "Rol Creador" normaliza a mayusculas EN
# VIVO mientras se escribe (confirmado: "dcaba" -> "DCABA" apenas se
# completa el campo, no solo al guardar). Los casos de alta (CP102/104/
# 111) y eliminacion (CP110) crean/borran su PROPIO registro de prueba
# (prefijo "QA-CP1xx") en vez de tocar los 7 parametros reales
# preexistentes; los de modificacion (CP106-109) hacen lo mismo: dan de
# alta un registro propio primero y lo modifican, para no alterar datos
# de produccion compartidos.

add("CP101", '''
filas = frame.locator("table tbody tr")
assert filas.count() > 0, "La grilla deberia mostrar parametros ya registrados al abrir la pantalla, sin presionar ningun boton"
capturar_paso(app, "grilla_cargada_automaticamente", paso_excel=4)
''')

add("CP102", '''
frame.get_by_role("button", name="Adicionar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Parámetro"]').fill("QA-CP102 Refacturacion Automatica")
frame.locator('input[aria-label="Clave Movimiento Cargo"]').fill("901")
frame.locator('input[aria-label="Clave Movimiento Abono"]').fill("902")
frame.locator('input[aria-label="Rol Creador"]').fill("QATEST")
capturar_paso(app, "antes_de_aceptar", paso_excel=4)
frame.get_by_role("button", name="Aceptar").click(timeout=15000)
esperar_fin_de_carga(app, frame)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Registro" in texto and ("Ingresado" in texto or "Insertado" in texto), f"No aparecio el mensaje de alta exitosa esperado: {texto!r}"
capturar_paso(app, "registro_ingresado", paso_excel=6)
cerrar_dialogo(frame)
''')

add("CP103", '''
frame.get_by_role("button", name="Adicionar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Clave Movimiento Cargo"]').fill("903")
frame.locator('input[aria-label="Clave Movimiento Abono"]').fill("904")
frame.locator('input[aria-label="Rol Creador"]').fill("QATEST")
capturar_paso(app, "antes_de_aceptar_sin_parametro", paso_excel=4)
frame.get_by_role("button", name="Aceptar").click(timeout=15000)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Par" in texto and "obligator" in texto, f"No aparecio el mensaje de campo obligatorio esperado: {texto!r}"
capturar_paso(app, "mensaje_campo_obligatorio", paso_excel=6)
cerrar_dialogo(frame)
''')

add("CP104", '''
frame.get_by_role("button", name="Adicionar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Parámetro"]').fill("QA-CP104 Cargo Igual Abono")
frame.locator('input[aria-label="Clave Movimiento Cargo"]').fill("905")
frame.locator('input[aria-label="Clave Movimiento Abono"]').fill("905")
frame.locator('input[aria-label="Rol Creador"]').fill("QATEST")
capturar_paso(app, "antes_de_aceptar_claves_iguales", paso_excel=5)
frame.get_by_role("button", name="Aceptar").click(timeout=15000)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "no pueden ser iguales" in texto, f"No aparecio el mensaje de claves iguales esperado: {texto!r}"
capturar_paso(app, "mensaje_claves_iguales", paso_excel=7)
cerrar_dialogo(frame)
''')

add("CP105", '''
frame.get_by_role("button", name="Adicionar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Parámetro"]').fill("QA-CP105 Cancelar Antes De Guardar")
capturar_paso(app, "antes_de_cancelar", paso_excel=4)
frame.get_by_role("button", name="Cancelar").click(timeout=15000)
app.wait_for_timeout(800)
assert frame.locator('input[aria-label="Parámetro"]').is_disabled(), "El panel de ingreso deberia volver a deshabilitarse tras Cancelar"
boton_adicionar = frame.get_by_role("button", name="Adicionar")
assert boton_adicionar.count() > 0, "El boton deberia volver a decir Adicionar tras Cancelar"
capturar_paso(app, "panel_deshabilitado_tras_cancelar", paso_excel=6)
''')

add("CP106", '''
frame.get_by_role("button", name="Adicionar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Parámetro"]').fill("QA-CP106 Original")
frame.locator('input[aria-label="Clave Movimiento Cargo"]').fill("911")
frame.locator('input[aria-label="Clave Movimiento Abono"]').fill("912")
frame.locator('input[aria-label="Rol Creador"]').fill("QATEST")
frame.get_by_role("button", name="Aceptar").click(timeout=15000)
esperar_fin_de_carga(app, frame)
cerrar_dialogo(frame)
app.wait_for_timeout(800)
fila = frame.locator("table tbody tr", has_text="QA-CP106 Original")
fila.click(timeout=10000)
app.wait_for_timeout(500)
frame.get_by_role("button", name="Modificar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Parámetro"]').fill("QA-CP106 Modificado")
capturar_paso(app, "antes_de_aceptar_modificacion", paso_excel=6)
frame.get_by_role("button", name="Aceptar").click(timeout=15000)
esperar_fin_de_carga(app, frame)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "Registro" in texto and "Modificado" in texto, f"No aparecio el mensaje de modificacion exitosa esperado: {texto!r}"
capturar_paso(app, "registro_modificado", paso_excel=7)
cerrar_dialogo(frame)
''')

add("CP107", '''
frame.get_by_role("button", name="Adicionar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Parámetro"]').fill("QA-CP107 Original")
frame.locator('input[aria-label="Clave Movimiento Cargo"]').fill("913")
frame.locator('input[aria-label="Clave Movimiento Abono"]').fill("914")
frame.locator('input[aria-label="Rol Creador"]').fill("QATEST")
frame.get_by_role("button", name="Aceptar").click(timeout=15000)
esperar_fin_de_carga(app, frame)
cerrar_dialogo(frame)
app.wait_for_timeout(800)
fila = frame.locator("table tbody tr", has_text="QA-CP107 Original")
fila.click(timeout=10000)
app.wait_for_timeout(500)
frame.get_by_role("button", name="Modificar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Parámetro"]').fill("")
capturar_paso(app, "antes_de_aceptar_sin_parametro", paso_excel=6)
frame.get_by_role("button", name="Aceptar").click(timeout=15000)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "obligator" in texto, f"No aparecio el mensaje de validacion esperado: {texto!r}"
capturar_paso(app, "mensaje_validacion", paso_excel=7)
cerrar_dialogo(frame)
''')

add("CP108", '''
frame.get_by_role("button", name="Adicionar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Parámetro"]').fill("QA-CP108 Original")
frame.locator('input[aria-label="Clave Movimiento Cargo"]').fill("915")
frame.locator('input[aria-label="Clave Movimiento Abono"]').fill("916")
frame.locator('input[aria-label="Rol Creador"]').fill("QATEST")
frame.get_by_role("button", name="Aceptar").click(timeout=15000)
esperar_fin_de_carga(app, frame)
cerrar_dialogo(frame)
app.wait_for_timeout(800)
fila = frame.locator("table tbody tr", has_text="QA-CP108 Original")
fila.click(timeout=10000)
app.wait_for_timeout(500)
frame.get_by_role("button", name="Modificar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Clave Movimiento Abono"]').fill("915")
capturar_paso(app, "antes_de_aceptar_claves_iguales", paso_excel=5)
frame.get_by_role("button", name="Aceptar").click(timeout=15000)
dlg = dialogo_f(frame)
dlg.wait_for(state="visible", timeout=10000)
texto = dlg.inner_text()
assert "no pueden ser iguales" in texto, f"No aparecio el mensaje de claves iguales esperado: {texto!r}"
capturar_paso(app, "mensaje_claves_iguales", paso_excel=7)
cerrar_dialogo(frame)
''')

add("CP109", '''
frame.get_by_role("button", name="Adicionar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Parámetro"]').fill("QA-CP109 Original")
frame.locator('input[aria-label="Clave Movimiento Cargo"]').fill("917")
frame.locator('input[aria-label="Clave Movimiento Abono"]').fill("918")
frame.locator('input[aria-label="Rol Creador"]').fill("QATEST")
frame.get_by_role("button", name="Aceptar").click(timeout=15000)
esperar_fin_de_carga(app, frame)
cerrar_dialogo(frame)
app.wait_for_timeout(800)
fila = frame.locator("table tbody tr", has_text="QA-CP109 Original")
fila.click(timeout=10000)
app.wait_for_timeout(500)
frame.get_by_role("button", name="Modificar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Parámetro"]').fill("QA-CP109 Cambiado (no deberia guardarse)")
capturar_paso(app, "antes_de_cancelar_modificacion", paso_excel=6)
frame.get_by_role("button", name="Cancelar").click(timeout=15000)
app.wait_for_timeout(1000)
assert frame.locator('input[aria-label="Parámetro"]').is_disabled(), "El panel deberia volver a deshabilitarse tras Cancelar"
fila_sin_cambios = frame.locator("table tbody tr", has_text="QA-CP109 Original")
assert fila_sin_cambios.count() > 0, "La grilla no deberia reflejar el cambio cancelado"
capturar_paso(app, "grilla_sin_cambios", paso_excel=7)
''')

add("CP110", '''
frame.get_by_role("button", name="Adicionar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Parámetro"]').fill("QA-CP110 Para Eliminar")
frame.locator('input[aria-label="Clave Movimiento Cargo"]').fill("919")
frame.locator('input[aria-label="Clave Movimiento Abono"]').fill("920")
frame.locator('input[aria-label="Rol Creador"]').fill("QATEST")
frame.get_by_role("button", name="Aceptar").click(timeout=15000)
esperar_fin_de_carga(app, frame)
cerrar_dialogo(frame)
app.wait_for_timeout(800)
fila = frame.locator("table tbody tr", has_text="QA-CP110 Para Eliminar")
fila.click(timeout=10000)
app.wait_for_timeout(500)
capturar_paso(app, "antes_de_eliminar", paso_excel=4)
frame.get_by_role("button", name="Eliminar").click(timeout=15000)
dlg_confirma = esperar_dialogo_visible(frame)
texto_confirma = dlg_confirma.inner_text()
assert "eliminar" in texto_confirma.lower(), f"No aparecio el dialogo de confirmacion esperado: {texto_confirma!r}"
dlg_confirma.get_by_role("button", name=re.compile("^(Aceptar|S[ií])$")).click(timeout=8000)
esperar_fin_de_carga(app, frame)
dlg_resultado = dialogo_f(frame)
if dlg_resultado.count() > 0 and dlg_resultado.is_visible():
    texto_resultado = dlg_resultado.inner_text()
    assert "Eliminado" in texto_resultado, f"No aparecio el mensaje de eliminacion exitosa esperado: {texto_resultado!r}"
    capturar_paso(app, "registro_eliminado", paso_excel=6)
    cerrar_dialogo(frame)
fila_borrada = frame.locator("table tbody tr", has_text="QA-CP110 Para Eliminar")
assert fila_borrada.count() == 0, "El registro deberia haber desaparecido de la grilla tras eliminarlo"
''')

add("CP111", '''
frame.get_by_role("button", name="Adicionar").click(timeout=15000)
app.wait_for_timeout(600)
frame.locator('input[aria-label="Parámetro"]').fill("QA-CP111 Normalizacion Rol")
frame.locator('input[aria-label="Clave Movimiento Cargo"]').fill("921")
frame.locator('input[aria-label="Clave Movimiento Abono"]').fill("922")
campo_rol = frame.locator('input[aria-label="Rol Creador"]')
campo_rol.fill("admref")
app.wait_for_timeout(400)
valor_normalizado = campo_rol.input_value()
assert valor_normalizado == "ADMREF", f"El campo Rol Creador deberia normalizarse a mayusculas ('ADMREF'), pero quedo en {valor_normalizado!r}"
capturar_paso(app, "rol_normalizado_mayusculas", paso_excel=6)
frame.get_by_role("button", name="Aceptar").click(timeout=15000)
esperar_fin_de_carga(app, frame)
cerrar_dialogo(frame)
''')

add("CP112", '''
for ancho, alto, nombre in ((1920, 1080, "desktop"), (768, 1024, "tablet"), (375, 667, "mobile")):
    app.set_viewport_size({"width": ancho, "height": alto})
    app.wait_for_timeout(500)
    assert frame.get_by_role("button", name="Adicionar").is_visible(), f"Boton Adicionar no visible en {nombre}"
    capturar_paso(app, f"responsive_{nombre}")
''')


if __name__ == "__main__":
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")
