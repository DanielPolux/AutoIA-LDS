"""
CP044 - Eliminar tramo exitoso

RF: RF-06   CU: CU-28
Descripcion: Seleccionar un tramo, presionar "Eliminar" y verificar que desaparece de la grilla y su proyección se elimina.
Precondicion: Debe asignarse el rol funcional: LUZGENACT
Datos de prueba: El tramo a eliminar debe tener proyección calculada para varios días futuros (tramos1).
Resultado esperado: El sistema muestra "Registro será Eliminado." y el tramo desaparece de la grilla de vigencia actual. Además, no deben quedar filas de proyección futura del tramo eliminado en tramos1 (fechas posteriores a hoy).

Pasos a seguir (segun matriz de casos original):
1. Ingresar a la plataforma web LDS.
2. Buscar el módulo "Actualización de Precios".
3. Cargar un precio existente asociado a Tramos.
4. Hacer clic sobre un tramo de la grilla para seleccionarlo.
5. Presionar Eliminar y confirmar "¿Está seguro de eliminar el Tramo?"
6. Verificar la grilla de vigencia actual.
7. Revisar el insert en la tabla audit.
8. Si es posible verificar en BD, consultar tramos1 para ese código/sector/tramo con fecha futura y confirmar que no quedan registros.

Por defecto corre en segundo plano (headless). Para verlo trabajar:
    set PR000325-SP3_HEADLESS=0
    python CP044.py
"""
import os, random, re, shutil, struct, subprocess, time, zipfile
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape as _escape_xml
from playwright.sync_api import sync_playwright, expect, TimeoutError as PWTimeoutError

# Por defecto corre en segundo plano (headless), sin abrir ventana de
# Edge. Para verlo trabajar en pantalla (util para un tester que quiere
# mirar el caso paso a paso), fijar PR000325-SP3_HEADLESS=0 antes de correrlo.
HEADLESS = os.environ.get("PR000325-SP3_HEADLESS", "1") == "1"

# Con PR000325-SP3_VIDEO=1 se graba un video (.webm) de toda la ejecucion,
# ademas de las capturas por paso. Apagado por defecto (un video por caso
# pesa/tarda mas; para una corrida masiva mejor dejarlo apagado y prenderlo
# solo cuando haga falta revisar un caso en detalle).
GRABAR_VIDEO = os.environ.get("PR000325-SP3_VIDEO", "0") == "1"

# Con PR000325-SP3_WORD=0 se omite el Word de evidencia (por defecto SI se
# genera: cada CPxxx.py arma su propio .docx con sus capturas, sin
# depender de ningun otro archivo del proyecto -asi se puede copiar este
# archivo solo a otra maquina y sigue generando su evidencia completa-).
GRABAR_WORD = os.environ.get("PR000325-SP3_WORD", "1") == "1"

# Con PR000325-SP3_SLOWMO=<milisegundos> Playwright agrega esa pausa entre
# CADA accion (click, fill, etc.). Sirve sobre todo junto con
# PR000325-SP3_VIDEO=1: sin esto, un fill() llena el campo de golpe y en
# el video no alcanza a verse el cambio. 0 = sin pausa (default, no afecta
# la velocidad normal de la corrida).
try:
    SLOWMO = int(os.environ.get("PR000325-SP3_SLOWMO", "0"))
except ValueError:
    SLOWMO = 0

# Pausa (ms) que se agrega justo despues de dejar los datos listos en
# pantalla y ANTES del clic que dispara la accion (capturar_paso con una
# descripcion "antes_de_*", ej. "antes_de_buscar", "antes_de_aceptar"): sin
# esto, con fill() llenando los campos de golpe, el video pasa de campos
# vacios a clic casi en el mismo instante y no da tiempo a ver los datos ya
# cargados antes de que se dispare la busqueda/accion. Por defecto se activa
# solo si se esta grabando video (GRABAR_VIDEO); se puede ajustar o apagar
# a mano con PR000325-SP3_PAUSA_ANTES_CLIC=<ms> (0 = sin pausa).
try:
    PAUSA_ANTES_CLIC = int(os.environ.get("PR000325-SP3_PAUSA_ANTES_CLIC", "1200" if GRABAR_VIDEO else "0"))
except ValueError:
    PAUSA_ANTES_CLIC = 0


URL = "https://pldsweb.luzdelsur.com.pe/Plataforma/PlataformaWeb"
USUARIO = "DCABA_DW"
PASSWORD = "Melquisedec_01"

CASO = "CP044"
EVIDENCIA = Path(__file__).resolve().parent / CASO
if EVIDENCIA.exists():
    shutil.rmtree(EVIDENCIA, ignore_errors=True)
EVIDENCIA.mkdir(parents=True, exist_ok=True)

NOMBRE_CASO = 'Eliminar tramo exitoso'
RF_CASO = 'RF-06'
CU_CASO = 'CU-28'
DESCRIPCION_CASO = 'Seleccionar un tramo, presionar "Eliminar" y verificar que desaparece de la grilla y su proyección se elimina.'
RESULTADO_ESPERADO_CASO = 'El sistema muestra "Registro será Eliminado." y el tramo desaparece de la grilla de vigencia actual. Además, no deben quedar filas de proyección futura del tramo eliminado en tramos1 (fechas posteriores a hoy).'
PASOS_CASO = '1. Ingresar a la plataforma web LDS.\n2. Buscar el módulo "Actualización de Precios".\n3. Cargar un precio existente asociado a Tramos.\n4. Hacer clic sobre un tramo de la grilla para seleccionarlo.\n5. Presionar Eliminar y confirmar "¿Está seguro de eliminar el Tramo?"\n6. Verificar la grilla de vigencia actual.\n7. Revisar el insert en la tabla audit.\n8. Si es posible verificar en BD, consultar tramos1 para ese código/sector/tramo con fecha futura y confirmar que no quedan registros.'

PASO_CONTADOR = {"n": 0}
CAPTURAS_POR_PASO_EXCEL = {}  # numero de paso del Excel (int) -> [nombres de archivo .png]


def capturar_paso(objetivo, descripcion, paso_excel=None):
    """Guarda una captura de evidencia por CADA paso relevante del caso
    (no solo al final), numerada en orden dentro de la carpeta EVIDENCIA
    (una por CP). `objetivo` es la Page donde tomar la captura (page antes
    de abrir el popup, o app una vez abierto).

    `paso_excel` (opcional): numero del paso de la columna "Pasos a
    seguir" de la matriz Excel al que corresponde esta captura (ej. 3 si
    esta screenshot ilustra el paso "3. Ingresar codigo nuevo."). Si se
    pasa, generar_word_evidencia() (ver WORD_HELPERS_FULL) agrupa la
    imagen bajo el texto real de ESE paso en vez de una etiqueta tecnica
    derivada del nombre de archivo. Una captura puede repetir el mismo
    paso_excel que otra anterior (ej. 2 capturas para el mismo paso del
    Excel) - quedan ambas bajo el mismo encabezado, en orden.

    Si la descripcion empieza con "antes_de" (ej. "antes_de_buscar",
    "antes_de_aceptar", "antes_de_limpiar", "antes_de_cancelar") se agrega
    ademas PAUSA_ANTES_CLIC despues de la captura: son justo los pasos
    donde los datos ya quedaron cargados en pantalla y lo siguiente en el
    caso es un clic, asi que sin esta pausa el video pasa de "campos
    llenos" a "clic" casi en el mismo frame."""
    PASO_CONTADOR["n"] += 1
    nombre = f"{CASO}_{PASO_CONTADOR['n']:02d}_{descripcion}.png"
    objetivo.screenshot(path=str(EVIDENCIA / nombre), full_page=True)
    if paso_excel is not None:
        CAPTURAS_POR_PASO_EXCEL.setdefault(paso_excel, []).append(nombre)
    if PAUSA_ANTES_CLIC and descripcion.startswith("antes_de"):
        objetivo.wait_for_timeout(PAUSA_ANTES_CLIC)


def login(page, reintentos=2, paso_excel=None):
    # `paso_excel` (opcional): numero del paso de "Pasos a seguir" del Excel
    # al que corresponde el login (ej. 1, si el Excel dedica un paso propio
    # a "Ingresar a la plataforma"). Sin esto, la captura de login siempre
    # cae en la seccion generica "Otras capturas" del Word de evidencia en
    # vez de agruparse bajo el paso real (ver generar_word_evidencia()).
    #
    # Varios campos del formulario de login se completan via JS de forma
    # asincrona tras cargar la pagina, en momentos distintos (confirmado en
    # exploracion en vivo):
    #   - #servidorWCF / #servidor: vacios al cargar, se llenan ~0.3-1.5s despues.
    #   - #Dominios (combo oculto de Dominio): arranca con 0 <option> y
    #     recien se puebla un poco DESPUES de que #servidor ya tiene valor.
    # Si se envia el login en esa ventana (Playwright llena el formulario
    # mucho mas rapido que un humano tecleando), el POST sale con el
    # dominio vacio y el backend responde con mensajes inconsistentes:
    # "Invalid URI: The hostname could not be parsed.", "No existe
    # dominio.", "Ud. no tiene acceso a la empresa." Por eso a mano nunca
    # pasa (tarda de sobra) y en la automatizacion sale intermitente. Se
    # espera a que AMBAS cosas esten listas antes de tocar el formulario -
    # pero incluso asi, a veces igual falla el primer intento (confirmado
    # en vivo en PR000325 el 10/09/2026: fallo 1ra vez con "Ud. no tiene
    # acceso a la empresa", OK reintentando), por eso se reintenta el
    # formulario completo hasta `reintentos` veces antes de rendirse.
    for intento in range(reintentos):
        page.goto(URL)
        page.wait_for_function("document.querySelector('#servidor')?.value", timeout=15000)
        page.wait_for_function("document.querySelector('#Dominios')?.options?.length > 0", timeout=15000)
        page.get_by_role("textbox", name="Usuario").click()
        page.get_by_role("textbox", name="Usuario").fill(USUARIO)
        page.get_by_role("textbox", name="Usuario").press("Tab")
        page.get_by_role("textbox", name="Contraseña").fill(PASSWORD)
        page.wait_for_timeout(1000)  # confirmado en vivo el 11/09/2026: dar 1s antes de Ingresar reduce el login fallido intermitente
        page.get_by_role("button", name="Ingresar ").click()
        page.wait_for_load_state("networkidle")
        if "Login" not in page.url:
            capturar_paso(page, "login", paso_excel=paso_excel)
            return
        print(f"  (aviso) login fallo (intento {intento + 1}/{reintentos}), reintentando..." if intento < reintentos - 1 else "  (aviso) login fallo en todos los intentos")
    capturar_paso(page, "login_fallo")
    raise RuntimeError(f"No se pudo iniciar sesion tras {reintentos} intento(s) (ver captura *_login_fallo.png).")


def _click_visible(page, text):
    """Clickea el enlace <a> VISIBLE cuyo texto sea EXACTAMENTE `text` (el
    menu lateral renderiza el arbol completo oculto; hay que filtrar
    visibles).

    Usa match EXACTO (regex ancla ^...$, insensible a espacios alrededor),
    no substring: `filter(has_text=text)` con un string hace substring
    case-insensitive, y el menu real tiene decenas de items cuyo texto
    CONTIENE la etiqueta buscada como substring ademas del item exacto (ej.
    PR000325: "Facturacion" tambien aparece dentro de "Calendario
    Facturacion", "Gestion Facturacion", "Liquidacion De Promedios Fuera De
    Proceso De Facturacion", etc.). Con substring, _click_visible podia
    clickear cualquiera de esos otros items en vez del nodo de menu
    correcto.

    Ademas recorre los candidatos en orden INVERSO (del ultimo al primero):
    incluso con match exacto, una ruta con la misma etiqueta repetida en 2
    niveles anidados (ej. PR000325 RF-05: Comercial > Facturacion >
    Facturacion > Mantenedor De Contratistas) deja AMBOS "Facturacion"
    visibles a la vez tras expandir el nivel 1 (el ancestro no se oculta
    solo porque se revelo su hijo), y el ancestro aparece ANTES en el DOM
    que el descendiente recien revelado. Devolver el primer visible volvia
    a clickear el mismo ancestro (colapsando el menu) en vez de bajar de
    nivel -bug real, confirmado en vivo: la ruta RF-05 nunca llegaba a
    revelar 'Mantenedor De Contratistas'."""
    patron = re.compile(r"^\s*" + re.escape(text) + r"\s*$")
    candidatos = page.locator("a").filter(has_text=patron)
    for i in reversed(range(candidatos.count())):
        candidato = candidatos.nth(i)
        if candidato.is_visible():
            candidato.click()
            return
    raise RuntimeError(f"No se encontro un enlace de menu visible con texto exacto: {text!r}")



def abrir_aplicacion(page, ruta_menu, selector_pantalla, timeout_menu=30000, timeout_pantalla=20000, paso_excel=None):
    """Navega Aplicaciones > ruta_menu[0] > ruta_menu[1] > ... (clic final
    que abre el POPUP de la aplicacion), y espera a que selector_pantalla
    (el componente Angular raiz de la pantalla, ej. "app-listado-de-x")
    este listo dentro del iframe #aplicacion del popup.

    Generalizacion de abrir_consulta_atenciones() (PR000335): la mecanica
    de navegacion -menu lateral con arbol oculto, popup con iframe
    #aplicacion- es la MISMA para cualquier aplicacion del portal Web LDS;
    lo unico que cambia por proyecto es la ruta de menus a clickear y el
    selector de la pantalla final. Ejemplo de uso (equivalente a PR000335):
        app, frame = abrir_aplicacion(
            page,
            ["Comercial", "Atencion Integral Al Cliente", "Consulta De Atenciones Comerciales"],
            "app-listado-de-atenciones",
        )
    Requiere _click_visible() y capturar_paso() ya definidos en el archivo.

    `paso_excel` (opcional): numero del paso de "Pasos a seguir" del Excel
    al que corresponde abrir la app (comun: el mismo paso 1 que cubre
    "entrar a la plataforma" + "entrar a la aplicacion" juntos, cuando el
    Excel no los separa). Sin esto, la captura "aplicacion_abierta" siempre
    cae en la seccion generica "Otras capturas" del Word de evidencia en
    vez de agruparse bajo el paso real - confirmado en vivo en PR000325
    (59 de 62 casos con esta seccion vacia de contenido util)."""
    page.get_by_role("link", name="  Aplicaciones").click(timeout=timeout_menu)
    page.wait_for_timeout(500)
    for texto in ruta_menu[:-1]:
        _click_visible(page, texto)
        page.wait_for_timeout(500)
    with page.expect_popup() as popup_info:
        _click_visible(page, ruta_menu[-1])
    app = popup_info.value
    app.wait_for_load_state("networkidle")
    frame = app.locator("#aplicacion").content_frame
    frame.locator(selector_pantalla).wait_for(timeout=timeout_pantalla)
    capturar_paso(app, "aplicacion_abierta", paso_excel=paso_excel)
    return app, frame


def esperar_fin_de_carga(app, pantalla, timeout_ms=45000):
    """Espera a que termine de cargar una busqueda/accion antes de seguir
    (y sobre todo, antes de tomar la captura de evidencia): el boton deja
    de decir 'Cargando...' y no queda actividad de red pendiente. Sin esto,
    la captura final a veces salia a medio cargar (spinner + boton
    'Cargando...' todavia visibles), como se detecto en la evidencia real
    de CP002."""
    try:
        pantalla.get_by_role("button", name="Cargando...").wait_for(state="hidden", timeout=timeout_ms)
    except PWTimeoutError:
        pass
    try:
        app.wait_for_load_state("networkidle", timeout=10000)
    except PWTimeoutError:
        pass
    app.wait_for_timeout(500)



def esperar_animacion_estable(locator, timeout_ms=3000, intervalo_seg=0.15):
    """Espera a que un elemento deje de moverse/cambiar de tamaño (fin de
    una transicion/animacion CSS de entrada, ej. un modal apareciendo con
    fade+slide) comparando su bounding box en dos instantes seguidos.
    Sin esto, una captura tomada apenas el elemento se vuelve "visible"
    puede salir a medio animar (confirmado con evidencia real: el dialogo
    de Restriccion de Busqueda de CP001 salio descuadrado/fantasma)."""
    plazo = time.monotonic() + timeout_ms / 1000
    anterior = None
    estable = 0
    while time.monotonic() < plazo:
        try:
            actual = locator.bounding_box()
        except Exception:
            actual = None
        if actual is not None and actual == anterior:
            estable += 1
            if estable >= 2:
                return
        else:
            estable = 0
        anterior = actual
        locator.page.wait_for_timeout(int(intervalo_seg * 1000))



def seleccionar_primera_opcion(select_locator, timeout_ms=8000):
    """Selecciona la primera opcion real (distinta del placeholder
    '-- Seleccione --') de un <select>. Los combos del modal Filtro Avanzado
    cargan sus opciones de forma asincrona luego de abrirse (confirmado en
    exploracion en vivo: hasta ~3s), por lo que se espera activamente hasta
    timeout_ms antes de rendirse. Devuelve True si pudo seleccionar."""
    plazo = time.monotonic() + timeout_ms / 1000
    while True:
        valores = [v for v in select_locator.locator("option").evaluate_all("els => els.map(e => e.value)") if v]
        if valores:
            select_locator.select_option(value=valores[0])
            return True
        if time.monotonic() >= plazo:
            break
        select_locator.page.wait_for_timeout(300)
    print("  (aviso) el combo no tiene opciones cargadas; se omite la seleccion.")
    return False



def seleccionar_opcion_por_texto(select_locator, patron, timeout_ms=8000):
    """Selecciona la opcion de un <select> cuyo texto visible matchee
    `patron` (un re.Pattern, ej. re.compile("Simple", re.I)).

    OJO: select_option(label=patron) de Playwright NO acepta un re.Pattern
    -su parametro `label` solo admite str o lista de str-; pasarle un
    Pattern directamente compila pero falla recien en tiempo de ejecucion
    con `TypeError: 're.Pattern' object is not iterable` (confirmado en
    vivo: PR000325 CP022/CP023/CP024/CP031/CP032). Por eso se leen las
    opciones del DOM y se matchea el texto a mano antes de seleccionar por
    `value`. Los combos pueden cargar sus opciones de forma asincrona, por
    lo que se espera activamente hasta timeout_ms antes de rendirse."""
    plazo = time.monotonic() + timeout_ms / 1000
    while True:
        opciones = select_locator.locator("option").evaluate_all("els => els.map(e => ({value: e.value, texto: e.textContent}))")
        for o in opciones:
            if patron.search(o["texto"] or ""):
                select_locator.select_option(value=o["value"])
                return True
        if time.monotonic() >= plazo:
            break
        select_locator.page.wait_for_timeout(300)
    raise RuntimeError(f"No se encontro una opcion que matchee {patron.pattern!r} en el combo.")


def _renombrar_video(video, destino, intentos=8, espera_seg=0.5):
    """Mueve/renombra el .webm que graba Playwright (nombre hash) al nombre
    final del caso, y devuelve la ruta que quedo REALMENTE valida (destino
    si se pudo renombrar, o el nombre-hash original si no se pudo) -nunca
    None si el video existe- para que el caller pueda seguir usando ese
    video (union con ffmpeg o guardado directo) aunque el renombre fallara.

    En Windows el proceso de ffmpeg a veces suelta el archivo un instante
    despues de que .path() ya lo devuelve, asi que se reintenta un par de
    veces antes de avisar que no se pudo. BUG REAL confirmado en vivo
    (PR000325, CP001, 10/09/2026): cuando los 8 intentos (4s) no alcanzan
    -maquina bajo carga tras correr varios casos seguidos-, el codigo
    anterior devolvia None y el caller SOLO revisaba si el archivo con el
    nombre BONITO (destino) existia; como nunca se creo, el video de ESE
    lado (portal o app) se descartaba en silencio -el caso seguia dando
    [OK] pero el .webm final quedaba INCOMPLETO (solo la mitad de la
    grabacion), sin ningun aviso salvo un print facil de pasar por alto
    entre 62 casos. Ahora el caller usa la ruta que se devuelve aca
    (renombrada o no) para la union/guardado, asi el video sigue completo
    aunque el renombre en si haya fallado."""
    origen = Path(video.path())
    for intento in range(intentos):
        try:
            origen.replace(destino)
            return destino
        except (PermissionError, OSError):
            if intento == intentos - 1:
                print(f"  (aviso) no se pudo renombrar el video {origen.name} -> {destino.name} (se sigue usando con su nombre original para la union/guardado).")
                return origen
            time.sleep(espera_seg)


def _localizar_ffmpeg():
    """Ubica un ffmpeg CON SOPORTE PARA 'concat' (el demuxer que hace
    falta para unir portal+aplicacion en un solo .webm). Primero un
    ffmpeg "completo" instalado en el sistema (PATH); si no hay, prueba el
    ffmpeg minimo que Playwright ya descarga para grabar (`playwright
    install ffmpeg`) -pero ese build viene compilado con
    --disable-everything y solo habilita a mano image2pipe/matroska/webm,
    NUNCA concat (confirmado en vivo corriendo `ffmpeg -demuxers` sobre el
    binario real: no aparece en absoluto)-. Devuelve None si NINGUNO
    soporta concat, para que el caller se ahorre el intento (que si se
    hace igual, ffmpeg no falla con un error prolijo: crashea con un
    codigo de salida basura tipo 2880417800, dificil de diagnosticar en
    medio de una corrida de 60+ casos)."""
    def soporta_concat(ruta):
        try:
            r = subprocess.run([str(ruta), "-hide_banner", "-demuxers"], capture_output=True, text=True, timeout=10)
            return "concat" in r.stdout
        except Exception:
            return False

    de_sistema = shutil.which("ffmpeg")
    if de_sistema and soporta_concat(de_sistema):
        return Path(de_sistema)
    # Ffmpeg portable dedicado, instalado a mano en la raiz AUTOMATIZACION_LDS
    # (2 niveles arriba de cada CPxxx.py: AUTOMATIZACION_LDS\\PRxxxxxx\\CPxxx.py)
    # - con soporte concat completo, a diferencia del build minimo que trae
    # Playwright.
    raiz_automatizacion = Path(__file__).resolve().parent.parent
    for candidato_portable in (raiz_automatizacion / "ffmpeg" / "ffmpeg.exe", raiz_automatizacion / "ffmpeg" / "bin" / "ffmpeg.exe"):
        if candidato_portable.is_file() and soporta_concat(candidato_portable):
            return candidato_portable
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright"
    if base.is_dir():
        candidatos = sorted(base.glob("ffmpeg-*/ffmpeg-win64.exe"), reverse=True)
        if candidatos and soporta_concat(candidatos[0]):
            return candidatos[0]
    return None


def _unir_videos(video1, video2, destino, timeout_seg=60):
    """Concatena 2 .webm (portal + aplicacion) en un solo archivo con
    ffmpeg (stream copy, sin recodificar: ambos ya comparten resolucion y
    codec porque los graba el mismo record_video_size). Si no encuentra un
    ffmpeg con soporte 'concat' o falla la union, no toca los archivos
    originales y devuelve False para que el caller los deje como 2 videos
    separados (ver _localizar_ffmpeg: en una maquina sin ffmpeg completo
    en el PATH, esto es la norma, no un error - instalar un ffmpeg
    "completo" y agregarlo al PATH si se quiere un solo .webm por caso)."""
    ffmpeg = _localizar_ffmpeg()
    if not ffmpeg:
        print("  (aviso) no hay un ffmpeg con soporte 'concat' disponible (el de Playwright no lo trae); quedan los 2 videos separados. Instalar ffmpeg completo y agregarlo al PATH para unirlos en uno solo.")
        return False
    lista = destino.parent / f"{destino.stem}_lista.txt"
    lista.write_text(f"file '{video1.name}'\nfile '{video2.name}'\n", encoding="utf-8")
    try:
        resultado = subprocess.run(
            [str(ffmpeg), "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(destino)],
            cwd=str(destino.parent),
            capture_output=True,
            text=True,
            timeout=timeout_seg,
        )
        if resultado.returncode == 0 and destino.exists():
            # La union en si ya funciono (destino existe y esta completo) -
            # la limpieza de los originales es best-effort: si Windows
            # todavia tiene el archivo bloqueado un instante despues de
            # browser.close(), NO se debe reportar la union como fallida
            # (bug real confirmado en vivo 17/09/2026: un WinError 32 aca
            # tapaba un merge exitoso con el aviso "no se pudieron unir").
            for video_origen in (video1, video2):
                for intento_borrado in range(4):
                    try:
                        video_origen.unlink(missing_ok=True)
                        break
                    except (PermissionError, OSError) as e:
                        if intento_borrado == 3:
                            print(f"  (aviso) la union de videos funciono, pero no se pudo borrar {video_origen.name}: {e}")
                        else:
                            time.sleep(0.5)
            return True
        print(f"  (aviso) no se pudieron unir los videos (ffmpeg devolvio {resultado.returncode}); quedan separados.")
        return False
    except Exception as e:
        print(f"  (aviso) no se pudieron unir los videos: {e}; quedan separados.")
        return False
    finally:
        lista.unlink(missing_ok=True)


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
    return scope.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\s*$"))


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

#
# Modulo: Mantenedor De Tablas Del Sistema Comercial (Web LDS)
# Componente Angular: app-mantenedor-tablas-list
# Ruta de menu confirmada en vivo: Interno > Mantenedor De Tablas Del Sistema Comercial
#
# Ficha tecnica (confirmado en vivo, PR000325-SP3, 15/09/2026):
# Estructura de 2 niveles:
#   - Nivel 1: catalogo de "tablas" (ej. ACRECO/ACRERE/ACTECO/AGRUPA/
#     ALMMED/AMBUSO/BANCOS/BCOCTA/CALCUO... - datos reales ya cargados de
#     entrada, sin necesidad de buscar). Grilla `table.g tbody tr`.
#   - Nivel 2: codigos DENTRO de una tabla de Nivel 1 (ej. dentro de
#     ACRECO: 10=CORTE FUSIBLE 0000, 20=CORTE CABLE, 26=CORTE ENCINTADO).
#     Se entra con DOBLE CLICK sobre la fila de Nivel 1 (NO con
#     seleccionar + Leer, que solo repite la busqueda de Nivel 1) - ver
#     entrar_nivel2(). El boton "Volver >>" regresa a Nivel 1.
#
# BUG REAL / carrera confirmada en vivo (CP005, 15/09/2026): Angular
# selecciona la PRIMERA fila de Nivel 2 de forma ASINCRONA poco despues de
# entrar - si se empieza a escribir en el campo Codigo demasiado rapido,
# esa seleccion tardia SOBRESCRIBE lo ya tecleado (quedaba con el codigo
# de la fila 1, ej. "10", en vez del valor nuevo). entrar_nivel2() ya
# espera un margen fijo extra para que esa seleccion inicial termine antes
# de que el caso siga.
#
# TOPE de 30 filas confirmado en vivo (CP005/CP008, 17/09/2026): la grilla
# de Nivel 2 solo trae los primeros 30 codigos de esa tabla (ordenados
# ascendente: numeros primero, despues letras) - NO es paginacion ni
# virtualizacion (forzar scroll no trae mas filas, el conteo real en el
# DOM se queda en 30). Un codigo de prueba con prefijo "Y"/"Z" ordena al
# FINAL y, apenas la tabla acumula basura de corridas previas (nunca se
# borra - "Eliminar" es baja LOGICA, marca "*" pero la fila sigue
# ocupando un lugar), el codigo recien creado queda FUERA de esas 30 filas
# - no aparece ni con scroll, aunque el insert en si haya funcionado
# (dialogo de exito real). Si tu caso necesita interactuar con la fila
# recien creada (click, Eliminar, etc.) y no solo verificar el mensaje de
# exito, usa un prefijo que ordene TEMPRANO (ej. "A" + digitos, que cae
# antes que los codigos reales de 2 letras tipo "AO") para que se mantenga
# siempre dentro de esas 30 filas.
#
# Requiere del framework compartido (web_lds_core.py, ya inyectado en la
# plantilla de cada proyecto via los bloques NAV / HELPERS_ESPERA):
#   abrir_aplicacion, capturar_paso
# Y helpers GENERICOS del proyecto (no especificos de este modulo, ver
# NUEVO_PROYECTO_CHECKLIST.md Seccion 0c): escribir_campo, confirmar_si_no,
# SELECTOR_DIALOGO.
#


def abrir_mantenedor_tablas(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Mantenedor De Tablas Del Sistema Comercial"], "app-mantenedor-tablas-list", paso_excel=paso_excel)


def entrar_nivel2(app, frame, fila_index=0):
    """Entra al Nivel 2 (codigos dentro de una tabla) con DOBLE CLICK
    sobre la fila de Nivel 1 elegida (fila_index, 0 = primera)."""
    frame.locator("table.g tbody tr").nth(fila_index).dblclick()
    app.wait_for_timeout(1500)


#
# Modulo: Relacion Sucursal - Sector - Zona (Web LDS)
# Componente Angular: app-susec-zona-list
# Ruta de menu confirmada en vivo: Interno > Relación Sucursal - Sector - Zona
#
# Ficha tecnica (confirmado en vivo, PR000325-SP3, 16/09/2026):
# Pantalla de Filtros (Sucursal, <select>) + Rango (Sector Inicio/Fin, Zona
# Inicio/Fin, TODOS <select>, no inputs libres) + grilla con columnas
# SECTOR/ZONA/BENEFICIARIO FISE. Boton unico "Ingresar"/"Modificar" segun
# si hay fila seleccionada (igual que Sprint 2, ver boton_grabar() en los
# helpers genericos) - a diferencia de RF-01 donde son 2 botones separados.
# Dialogo de confirmacion usa botones "Si"/"No" (no "Aceptar"/"Cancelar"
# como RF-01) - ver confirmar_si_no() en los helpers genericos.
#
# Ninguna sucursal del ambiente de pruebas tenia rangos precargados al
# momento de explorar - todos los casos crean su propio dato descartable
# con crear_rango_prueba() en vez de asumir datos reales existentes.
#
# BUG/regla de negocio real confirmada en vivo (16/09/2026): la combinacion
# Sector/Zona debe ser UNICA A NIVEL GLOBAL (entre TODAS las sucursales, no
# solo dentro de la seleccionada) - crear un rango con una combinacion ya
# usada por OTRA sucursal responde "La combinacion Sector X / Zona Y ya
# esta asignada a otra sucursal." Hay bastante dato real precargado (varias
# combinaciones bajas, Sector 01-03, ya estaban ocupadas durante la
# exploracion) - se sortea con random.choice/randint sobre TODO el rango
# disponible (no un contador secuencial ni time.time() de baja entropia).
#
# "Leer" puede quedar deshabilitado de forma persistente si, tras
# seleccionar una NUEVA sucursal, se intenta un segundo "Leer" filtrado
# (Sector/Zona) inmediatamente despues del primero (blanco) - patron NO
# resuelto del todo; el workaround confirmado es hacer UN solo "Leer" en
# blanco por cambio de sucursal y buscar la fila deseada del lado cliente
# en la grilla completa (ver buscar_fila_rango/esperar_fila_rango) en vez
# de un segundo Leer filtrado.
#
# CASO CP015 (Replicacion a sucursal "0000") - hallazgo confirmado en vivo
# el 16/09/2026: la replicacion de un rango Sector/Zona hacia la sucursal
# especial "0000" (Sin Sucursal) SI ocurre (reproducido a mano por el
# usuario, con video propio), pero la automatizacion NO logro verla en 2
# corridas automatizadas seguidas releyendo "0000" inmediatamente despues
# de crear el rango (ni siquiera con una espera deliberada de 100s antes de
# releer). Hipotesis: delay/proceso batch corto entre la creacion y la
# replicacion visible en 0000, mas rapido para una sesion manual (mas
# lenta en general) que para la automatizacion. Si un caso depende de ver
# un rango replicado en 0000, considerar esta limitacion de timing conocida
# antes de marcarlo como fallo real de la app.
#
# Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
#   abrir_aplicacion, esperar_fin_de_carga, capturar_paso
# Y helpers GENERICOS del proyecto (no especificos de este modulo, ver
# NUEVO_PROYECTO_CHECKLIST.md Seccion 0c): boton_grabar, confirmar_si_no,
# SELECTOR_DIALOGO.
#


def abrir_relacion_sucursal_sector_zona(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Relación Sucursal - Sector - Zona"], "app-susec-zona-list", paso_excel=paso_excel)


def elegir_sector_zona_libre(app, frame, intentos=15):
    """Generador: en cada iteracion selecciona un Sector/Zona al azar
    (sobre TODO el rango de opciones disponibles) y hace yield
    (sector, zona) para que el llamador intente crear el rango - ver
    crear_rango_prueba()."""
    selects = frame.locator("select")
    sector_ini, sector_fin, zona_ini, zona_fin = selects.nth(1), selects.nth(2), selects.nth(3), selects.nth(4)
    sectores_validos = sector_ini.locator("option").evaluate_all("els => els.map(e => e.value).filter(v => v)")
    for _intento in range(intentos):
        sector = random.choice(sectores_validos)
        zona = str(random.randint(1, 999)).zfill(3)
        sector_ini.select_option(value=sector)
        sector_fin.select_option(value=sector)
        zona_ini.select_option(value=zona)
        zona_fin.select_option(value=zona)
        app.wait_for_timeout(300)
        yield sector, zona


def crear_rango_prueba(app, frame, fise=False, intentos=15):
    """Crea un rango Sector/Zona descartable para pruebas, reintentando
    con otra combinacion si la elegida ya esta asignada a otra sucursal
    (ver elegir_sector_zona_libre)."""
    checkbox = frame.locator("input[type=checkbox]").first
    if fise:
        checkbox.check()
    else:
        checkbox.uncheck()
    ultimo_texto = ""
    for sector, zona in elegir_sector_zona_libre(app, frame, intentos=intentos):
        boton_grabar(frame).click()
        ultimo_texto = confirmar_si_no(frame)
        print(f"[DEBUG] intento Sector={sector} Zona={zona} -> {ultimo_texto.strip()[:120]!r}")
        if "asignada a otra sucursal" not in ultimo_texto.lower():
            return sector, zona, ultimo_texto
    raise AssertionError(f"No se pudo crear un rango de prueba tras {intentos} intentos - ultimo mensaje: {ultimo_texto!r}")


def buscar_fila_rango(frame, sector, zona):
    """Busca la fila de la grilla que corresponde a un Sector/Zona dados
    - la grilla muestra los codigos SIN ceros a la izquierda (ej.
    '01'->'1', '001'->'1'), a diferencia del select que usa el codigo con
    padding, por lo que no alcanza un substring match directo."""
    filas = frame.locator("table.g tbody tr")
    for i in range(filas.count()):
        fila = filas.nth(i)
        celdas = fila.locator("td").all_inner_texts()
        if len(celdas) >= 2 and celdas[0].strip() == str(int(sector)) and celdas[1].strip() == str(int(zona)):
            return fila
    return None


def esperar_fila_rango(app, frame, sector, zona, aparece=True, intentos=24, espera_ms=500):
    """Tras confirmar una accion la grilla queda unos instantes en
    estado transitorio antes de reflejar el cambio - se hace polling
    explicito en vez de asumir que ya esta actualizada tras el primer
    chequeo."""
    fila = None
    for _ in range(intentos):
        fila = buscar_fila_rango(frame, sector, zona)
        if (fila is not None) == aparece:
            return fila
        app.wait_for_timeout(espera_ms)
    return fila


#
# Modulo: Actualizacion De Agenda De Pagos (Web LDS)
# Componente Angular: app-agenda-pagos-list
# Ruta de menu confirmada en vivo: Interno > Actualización De Agenda De Pagos
#
# Ficha tecnica (confirmado en vivo, PR000325-SP3, 16/09/2026):
# Pantalla MUY simple - 2 radios FIJOS "Cia. Electrica"/"Otras
# Instituciones" (NO hay una lista/select de "otras instituciones", son
# solo estas 2 opciones fijas, pese a lo que sugiere el nombre) + 1 campo
# "Numero de Dias" (input de texto sin id/name - usar campo_por_etiqueta o
# directo como primer input[type=text]).
#
# Boton unico Ingresar/Modificar (boton_grabar, helper generico) que
# cambia de texto segun si el campo TIENE VALOR, NO segun si el registro
# "existe" en BD - un registro con Numero de Dias vacio se trata como
# "Ingresar" aunque conceptualmente la institucion siempre existe.
#
# Dialogo Si/No igual que RF-02 ("¿Esta seguro de la actualizacion a
# realizar?") seguido de un dialogo de resultado con Aceptar ("Registro
# Actualizado."/"Registro Ingresado.") - mismo confirmar_si_no() generico,
# pero aca ese 2do dialogo puede tardar MAS de 3s en aparecer (usar el
# timeout_siguientes mas generoso de confirmar_si_no, no el default corto).
#
# Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
#   abrir_aplicacion, esperar_fin_de_carga, capturar_paso
# Y helpers GENERICOS del proyecto (no especificos de este modulo, ver
# NUEVO_PROYECTO_CHECKLIST.md Seccion 0c): boton_grabar, confirmar_si_no,
# campo_por_etiqueta, SELECTOR_DIALOGO.
#


def abrir_actualizacion_agenda_pagos(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Actualización De Agenda De Pagos"], "app-agenda-pagos-list", paso_excel=paso_excel)


def esperar_valor_campo(app, campo, valor_esperado=None, intentos=20, espera_ms=500):
    """Tras "Leer" la grilla/campo queda unos instantes en un estado
    transitorio (spinner sin boton "Cargando..." detectable, mismo
    patron de RF-01/RF-02) antes de reflejar el valor real - se hace
    polling explicito sobre el VALOR del campo en vez de leerlo una sola
    vez. Si `valor_esperado` es None, espera a que el campo tenga
    CUALQUIER contenido (no vacio)."""
    valor = campo.input_value().strip()
    for _ in range(intentos):
        if (valor_esperado is not None and valor == valor_esperado) or (valor_esperado is None and valor):
            break
        app.wait_for_timeout(espera_ms)
        valor = campo.input_value().strip()
    return valor


#
# Modulo: Actualizacion De Documentos (Web LDS)
# Componente Angular: app-documentos-list
# Ruta de menu confirmada en vivo: Interno > Actualización De Documentos
#
# Ficha tecnica (confirmado en vivo, PR000325-SP3, 16/09/2026):
# Pantalla "Tipo de Documento": campo Tipo (input maxlength=1, UNA letra) +
# un combo con todos los tipos existentes (SOLO visible cuando Tipo esta
# vacio o tiene una letra YA existente - se reemplaza por un input de
# Descripcion editable de maxlength=30 cuando la letra es NUEVA) +
# checkbox "Ind. Actualiza". Boton unico Ingresar/Modificar (boton_grabar,
# helper generico).
#
# En el ambiente de pruebas ya habia 10 tipos reales cargados
# (A,B,C,E,F,O,P,R,X,Z - Z es "PRUEBA", posible dato de prueba dejado de
# otra sesion). Como Tipo es UNA SOLA LETRA (sin margen para sufijos unicos
# tipo time.time()), los casos que crean datos usan letras_tipo_libres()
# para elegir una letra REALMENTE libre y la ELIMINAN al final
# (eliminar_tipo), para no agotar el pool limitado de 26 letras entre
# corridas repetidas.
#
# BUG REAL confirmado en vivo (16/09/2026): el campo Tipo queda
# DESHABILITADO despues de cualquier Leer exitoso (no solo despues de
# guardar) - si se necesita volver a escribir en el (ej. releer otro tipo,
# o limpiar uno recien creado), hay que pasar por "Cancelar" primero. Tanto
# crear_tipo_prueba() como eliminar_tipo() ya hacen este chequeo antes de
# escribir.
#
# Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
#   abrir_aplicacion, esperar_fin_de_carga, capturar_paso
# Y helpers GENERICOS del proyecto (no especificos de este modulo, ver
# NUEVO_PROYECTO_CHECKLIST.md Seccion 0c): escribir_campo, confirmar_si_no,
# SELECTOR_DIALOGO.
#


def abrir_actualizacion_documentos(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Actualización De Documentos"], "app-documentos-list", paso_excel=paso_excel)


def campo_tipo_documento(frame):
    return frame.locator("input").first


def letras_tipo_libres(frame):
    """El campo "Tipo" es una unica letra (maxlength=1, sin margen para
    sufijos tipo time.time()) - enumera las letras YA USADAS desde el
    combo (solo visible con el campo Tipo vacio, en la pantalla inicial)
    para elegir una libre y no chocar con tipos reales ni agotar el pool
    de 26 letras posibles entre corridas repetidas."""
    select = frame.locator("select").first
    usadas = set(v for v in select.locator("option").evaluate_all("els => els.map(e => e.value)") if v)
    return [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in usadas]


def crear_tipo_prueba(app, frame, letra, descripcion, actualiza=False):
    """Crea un tipo de documento descartable. Se espera llamar con la
    pantalla en su estado inicial (Tipo vacio), pero por las dudas
    tambien pasa por "Cancelar" si el campo Tipo ya esta deshabilitado
    (ver eliminar_tipo)."""
    campo_tipo = campo_tipo_documento(frame)
    if campo_tipo.is_disabled():
        frame.get_by_role("button", name="Cancelar", exact=True).click()
        app.wait_for_timeout(500)
    campo_tipo.click()
    campo_tipo.press_sequentially(letra, delay=50)
    frame.get_by_role("button", name="Leer", exact=True).click()
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(1200)
    campo_desc = frame.locator("input").nth(1)
    escribir_campo(campo_desc, descripcion)
    if actualiza:
        frame.locator("input[type=checkbox]").first.check()
    boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\s*$"))
    boton.click()
    texto = confirmar_si_no(frame)
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(1200)
    return texto


def eliminar_tipo(app, frame, letra):
    """Elimina (desactiva) un tipo de documento por su letra - usado
    para limpiar los tipos descartables creados por las pruebas y no
    agotar el pool limitado de letras libres."""
    campo_tipo = campo_tipo_documento(frame)
    if campo_tipo.is_disabled():
        frame.get_by_role("button", name="Cancelar", exact=True).click()
        app.wait_for_timeout(500)
    campo_tipo.click()
    campo_tipo.press("Control+A")
    campo_tipo.press("Delete")
    campo_tipo.press_sequentially(letra, delay=50)
    frame.get_by_role("button", name="Leer", exact=True).click()
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(1200)
    frame.get_by_role("button", name="Eliminar", exact=True).click()
    texto = confirmar_si_no(frame)
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(1200)
    return texto


#
# Modulo: Actualizacion De Conceptos (Web LDS)
# Componente Angular: app-conceptos-list
# Ruta de menu confirmada en vivo: Interno > Actualización De Conceptos
#
# Ficha tecnica (confirmado en vivo, PR000325-SP3, 16/09/2026):
# Pantalla "Concepto" (codigo, 3 caracteres) + "Configuracion Contable"
# (Documento: select; Cuenta Contable: input poblado via modal "Busqueda
# Cuenta Contable" abierto con el boton "..."; Movimiento: input de 1
# caracter restringido a I/E EN TIEMPO REAL - cualquier otro caracter
# tipeado se descarta y el campo queda vacio). Boton unico
# Ingresar/Modificar (boton_grabar, helper generico).
#
# BUG REAL / orden real distinto al que sugiere la matriz de pasos: para
# un codigo NUEVO, "Leer" exige que Descripcion ya tenga contenido (si
# esta vacia responde "Ingrese descripcion." y NO cambia a modo Insertar)
# - a diferencia del orden "Leer primero, completar despues" que sugiere
# la matriz, se llena Descripcion ANTES de presionar Leer (ver
# crear_concepto_prueba()).
#
# Modal de cuenta contable: "Buscar" (con filtros CUENTA/DESCRIPCION
# opcionales, vacios trae hasta 100 resultados) + doble-click en una fila
# selecciona y CIERRA el modal solo, sin boton "Seleccionar" adicional.
#
# Codigos de prueba de 3 letras al azar (26^3 combinaciones, margen de
# sobra - a diferencia de RF-04, no hace falta reutilizar/limpiar el pool).
#
# RAIZ REAL del bug mas dificil de este modulo (releer_concepto,
# confirmada en vivo via captura de pantalla Y volcado del DOM en el
# momento exacto del fallo): para un CODIGO YA EXISTENTE, escribirlo en el
# campo y tabular dispara una autolectura on-blur ASINCRONICA contra el
# backend que puede tardar MUCHO (confirmado, en un dia con el backend
# lento, mas de 24s). Mientras tanto Documento/Cuenta Contable quedan
# vacios y "Leer"/"Modificar" siguen sin habilitarse. Cuando por fin
# resuelve, dejar "Leer" deshabilitado es el estado de EXITO (no un bug):
# forzar un click ahi agota el timeout porque el boton nunca se
# re-habilita esperando otra cosa. Por eso releer_concepto() favorece
# esperar con PACIENCIA (decenas de segundos, polling) por encima de
# reintentar el tipeo o recargar la pagina - ambos "arreglos" mas
# agresivos se probaron en vivo y resultaron CONTRAPRODUCENTES (rompieron
# un caso que antes pasaba, CP033) - NUNCA usar app.reload() aca.
#
# Otros gotchas confirmados en vivo:
#   - Tras una accion anterior (Eliminar/desactivar) puede quedar un
#     overlay de carga (`.ant-spin-blur`) bloqueando clicks por mas
#     tiempo del que esperar_fin_de_carga() + el margen fijo cubren.
#   - El campo Descripcion tiene un autocomplete que a veces queda
#     abierto/colgado en el DOM despues de escribir e intercepta el
#     siguiente click sobre Concepto - se cierra con Escape por las dudas
#     antes de cualquier interaccion.
#   - El campo Concepto puede volverse "readonly disabled" tanto ANTES de
#     empezar (lectura anterior en modo solo-lectura) como EN MEDIO de un
#     reintento (el form se resetea tras Eliminar/desactivar con un
#     render en DOS FASES: primero luce habilitado/en blanco un instante,
#     y un ciclo de Angular despues lo vuelve a bloquear).
#   - Un solo chequeo de boton_leer.is_enabled()==True no alcanza: puede
#     estar habilitado en un instante y ya deshabilitado de nuevo
#     milisegundos despues (debounce de 3 lecturas seguidas antes de
#     confiar en que es un codigo nuevo/inexistente).
#
# Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
#   abrir_aplicacion, esperar_fin_de_carga, capturar_paso
# Y helpers GENERICOS del proyecto (no especificos de este modulo, ver
# NUEVO_PROYECTO_CHECKLIST.md Seccion 0c): escribir_campo, confirmar_si_no,
# SELECTOR_DIALOGO.
#


def abrir_actualizacion_conceptos(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Actualización De Conceptos"], "app-conceptos-list", paso_excel=paso_excel)


def campo_concepto_codigo(frame):
    return frame.locator("input").first


def releer_concepto(app, frame, codigo):
    """Vuelve a poner la pantalla en un codigo de Concepto conocido
    (pasando por "Cancelar" primero si el campo esta deshabilitado por
    una lectura anterior). Ver la ficha tecnica del modulo para el
    detalle completo de la carrera de autolectura on-blur que motiva el
    polling paciente de esta funcion - NUNCA reemplazarlo por
    app.reload(), confirmado en vivo que rompe casos que antes pasaban."""
    app.keyboard.press("Escape")
    app.wait_for_timeout(300)
    campo = campo_concepto_codigo(frame)
    boton_leer = frame.get_by_role("button", name="Leer", exact=True)
    campo_cuenta = frame.locator("input").nth(2)

    def _ya_cargado_solo():
        # Senal de que la autolectura on-blur YA cargo el registro sola
        # (Leer debe quedar SIN clickear en ese caso), basada en DATOS
        # (que Cuenta Contable ya tenga valor, o el label "Registro
        # Desactivado" este visible) en vez del estado
        # habilitado/deshabilitado de un boton, que puede ir desfasado
        # respecto al DOM real.
        try:
            if campo_cuenta.input_value(timeout=500).strip():
                return True
        except PWTimeoutError:
            pass
        etiqueta_desactivado = frame.get_by_text(re.compile(r"registro desactivado", re.IGNORECASE))
        return bool(etiqueta_desactivado.count() and etiqueta_desactivado.first.is_visible())

    def _desbloquear_si_hace_falta():
        # El campo Concepto puede volverse "readonly disabled" tanto
        # ANTES de empezar como EN MEDIO de un reintento (render en dos
        # fases tras Eliminar/desactivar) - se llama antes de CADA
        # intento de click, no solo una vez al principio.
        if not campo.is_disabled():
            return
        for _intento_cancelar in range(4):
            try:
                frame.locator(".ant-spin-blur").first.wait_for(state="hidden", timeout=5000)
            except PWTimeoutError:
                pass
            frame.get_by_role("button", name="Cancelar", exact=True).click()
            for _espera in range(10):
                app.wait_for_timeout(300)
                if not campo.is_disabled():
                    break
            if not campo.is_disabled():
                break

    # Si el campo YA esta bloqueado mostrando exactamente el codigo
    # buscado (puede pasar justo tras crear/desactivar), no hay nada que
    # tipear - ya estamos en el estado correcto.
    try:
        valor_inicial = campo.input_value(timeout=500).strip().upper()
    except PWTimeoutError:
        valor_inicial = ""
    if campo.is_disabled() and valor_inicial == codigo.strip().upper():
        return frame

    ya_cargado = False
    for _intento in range(3):
        _desbloquear_si_hace_falta()
        campo = campo_concepto_codigo(frame)
        if campo.is_disabled():
            # Sigue bloqueado pese al desbloqueo - no forzar el click
            # (agotaria 30s de timeout), esperar un poco mas y reintentar
            # en la siguiente vuelta del for.
            app.wait_for_timeout(800)
            continue
        campo.click()
        campo.press("Control+A")
        campo.press("Delete")
        campo.press_sequentially(codigo, delay=50)
        campo.press("Tab")
        app.keyboard.press("Escape")
        # Polling PACIENTE (ver ficha tecnica: la autolectura on-blur
        # puede tardar bastante mas de lo que parece razonable) antes de
        # asumir que el Tab no disparo nada y recien ahi reintentar el
        # tipeo completo.
        resuelto = False
        for _poll in range(75):
            app.wait_for_timeout(400)
            if _ya_cargado_solo():
                ya_cargado = True
                resuelto = True
                break
            if boton_leer.is_enabled():
                # Un solo chequeo de is_enabled()==True no alcanza - se
                # exige que se vea habilitado 3 veces seguidas (~900ms)
                # antes de confiar en que de verdad es un codigo
                # nuevo/inexistente (ver ficha tecnica del modulo).
                _estable = True
                for _ in range(3):
                    app.wait_for_timeout(300)
                    if not boton_leer.is_enabled():
                        _estable = False
                        break
                if _estable:
                    resuelto = True
                    break
        if resuelto:
            break
    if not ya_cargado:
        try:
            frame.locator(".ant-spin-blur").first.wait_for(state="hidden", timeout=8000)
        except PWTimeoutError:
            pass
        if boton_leer.is_enabled():
            boton_leer.click()
            esperar_fin_de_carga(app, frame)
            app.wait_for_timeout(800)
    return frame


def crear_concepto_prueba(app, frame, codigo, descripcion, movimiento="I"):
    """Crea un concepto contable descartable de punta a punta
    (codigo+descripcion+documento+cuenta contable via el modal de
    busqueda+movimiento) y confirma."""
    campo = campo_concepto_codigo(frame)
    campo.click()
    campo.press_sequentially(codigo, delay=50)
    campo.press("Tab")
    app.wait_for_timeout(500)
    campo_desc = frame.locator("input").nth(1)
    escribir_campo(campo_desc, descripcion)
    app.keyboard.press("Escape")
    app.wait_for_timeout(300)
    frame.get_by_role("button", name="Leer", exact=True).click()
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(800)
    boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\s*$"))
    assert boton.inner_text().strip() == "Ingresar", f"Se esperaba modo Insertar para el codigo nuevo {codigo!r}, se vio el boton: {boton.inner_text()!r}"
    select_doc = frame.locator("select").first
    valores_doc = [v for v in select_doc.locator("option").evaluate_all("els => els.map(e => e.value)") if v]
    assert valores_doc, "Se esperaba al menos un tipo de documento disponible para elegir"
    select_doc.select_option(value=random.choice(valores_doc))
    app.wait_for_timeout(300)
    campo_mov = frame.locator("input").nth(3)
    campo_mov.click()
    campo_mov.press_sequentially(movimiento, delay=50)
    app.wait_for_timeout(300)
    frame.get_by_role("button", name="...", exact=True).click()
    app.wait_for_timeout(1000)
    frame.get_by_role("button", name="Buscar", exact=True).click()
    app.wait_for_timeout(1500)
    frame.locator("table tbody tr").first.dblclick()
    app.wait_for_timeout(800)
    boton.click()
    texto = confirmar_si_no(frame)
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(1200)
    return texto


def desactivar_concepto(app, frame, codigo):
    """Re-lee un concepto por codigo y lo desactiva (Eliminar). Devuelve
    (frame, texto) - frame puede ser un objeto NUEVO si releer_concepto()
    tuvo que pasar por un desbloqueo intermedio (ver su docstring) -
    siempre usar el frame devuelto de aca en adelante, no el original."""
    frame = releer_concepto(app, frame, codigo)
    frame.get_by_role("button", name="Eliminar", exact=True).click()
    texto = confirmar_si_no(frame)
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(1200)
    return frame, texto


#
# Modulo: Actualizacion De Precios (Web LDS)
# Componente Angular: app-precios-list
# Ruta de menu confirmada en vivo: Interno > Actualizacion De Precios
#
# Este archivo es el INSUMO reutilizable para generar casos de prueba de
# este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
# depende de ningun proyecto puntual (no importa nada de un
# matriz_casos.json ni de un generate_scripts.py de proyecto). Un
# generate_scripts.py de proyecto importa lo que necesite de aca y le
# agrega solo los cuerpos de caso (los CPxxx puntuales de SU matriz), sin
# tener que re-descubrir nada de lo que ya esta documentado aca.
#
# ============================================================================
# FICHA TECNICA (confirmado en vivo, PR000325-SP3, 16/09/2026)
# ============================================================================
#
# Pantalla principal (3 cards apiladas + barra de acciones fija):
#   - Identificacion del Precio: Codigo de Precio (select, ~1157 opciones,
#     NO correlativo con el texto visible - buscar por indice via
#     indice_opcion_precio(), nunca hardcodear un indice fijo) + Fecha de
#     Vigencia (<input type=date>) + Sector Tipico (select, valores "1"-"4"
#     confirmados).
#   - Modo: radios Normal / Por Tramos - se BLOQUEAN (quedan solo lectura)
#     apenas se lee un precio EXISTENTE; solo son editables para un precio
#     NUEVO (boton dinamico en "Ingresar").
#   - Valores: Valor Actual (Neto) SIEMPRE readonly, Valor Nuevo (Neto) y
#     Porc. Reajuste editables segun modo/estado.
#   - Barra de acciones: Leer (siempre habilitado) | Ingresar/Modificar
#     (boton dinamico, habilitado solo despues de Leer) | Tramos (solo
#     visible/util en modo Por Tramos) | Cancelar (siempre habilitado,
#     limpia el formulario completo).
#
# Precio "023 - ALUMBRADO PUBLICO (TRAMOS)" es el UNICO confirmado en modo
# Por Tramos entre los primeros 605 codigos explorados (de 1157 totales) -
# usarlo como referencia conocida para cualquier caso que necesite un
# precio en ese modo; buscarlo por texto ("ALUMBRADO PUBLICO") con
# indice_opcion_precio(), nunca por indice fijo (el catalogo real podria
# reordenarse).
#
# Mensajes exactos del sistema (ver manual_usuario_actualizacion_precios.pdf
# si el proyecto lo tiene en Documentos/ - trae la lista completa de
# validaciones por campo):
#   - "Ingrese Codigo Precio Valido."  (codigo no reconocido)
#   - "Ingrese fecha." / "Ingrese sector tipico."
#   - "¡Debe ingresar o Valor o Porcentaje!"
#   - "No debe reajustar sobre valor actual cero." (solo Porc.Reajuste sin
#     Valor Actual registrado)
#   - "¿Esta seguro de ingresar el precio?" / "...de modificar el precio?"
#     (confirm Si/No)
#   - "Registro Actualizado." (resultado exitoso, alta y modificacion)
#
# Ventana de Tramos ("Actualizacion de Precios por Tramo"): se abre SOLA al
# elegir Por Tramos en modo Ingresar, o al Leer un precio que ya es Por
# Tramos. Card "Tramos" (vigencia actual, editable) + card "Valores
# Utilizados al DD/MM/AAAA" (vigencia anterior, solo lectura, boton
# Pegar copia sus rangos Inferior/Superior a la fila de edicion).
#   - Los tramos se guardan de forma INDIVIDUAL e INMEDIATA en BD al
#     presionar Ingresar/Modificar dentro de esta ventana - no hay un
#     confirm global al cerrar.
#   - Numeracion estrictamente consecutiva (1, 2, 3...) y SIN huecos ni
#     superposicion: el Tramo Inferior de un tramo nuevo debe ser EXACTAMENTE
#     igual al Tramo Superior del ultimo tramo ya cargado.
#   - Solo se puede modificar el Valor de un tramo existente, nunca sus
#     rangos (Inferior/Superior quedan grises/deshabilitados al
#     seleccionar una fila existente).
#   - Mensajes: "Registro actualizado." (alta/modificacion de UN tramo),
#     "Registro sera Eliminado." (eliminar), "Numero de Tramo debe ser
#     consecutivo", "Tramo Inferior debe ser igual al ultimo tramo
#     superior", "Debe ingresar Tramos." (al intentar Ingresar en la
#     pantalla principal sin haber cargado ningun tramo).
#   - Cierre con boton dual Cancelar/Cerrar: "Cancelar" (hay datos en la
#     fila de edicion, solo la limpia) vs "Cerrar" (fila vacia - cierra
#     directo si no hubo cambios en la sesion, o pide confirmar "Se
#     guardaron los cambios, ¿Continuar?" si sí hubo).
#
# BUGS REALES / gotchas confirmados en vivo (no asumir que ya no aplican
# sin volver a probar si la app cambio):
#   - Si se usa "Pegar", hay que escribir el Nro. de Tramo ANTES de
#     presionar Pegar - al reves (escribir el numero DESPUES), los valores
#     recien pegados de Inferior/Superior se resetean a vacio. Ver
#     crear_tramo() abajo, parametro usar_pegar.
#   - "Pegar" siempre trae los rangos de la VIGENCIA ANTERIOR, sin importar
#     si la vigencia ACTUAL que se esta armando ya tiene tramos cargados -
#     solo es correcto usarlo para el PRIMER tramo de una vigencia vacia;
#     si ya hay tramos hoy, hay que encadenar a mano con el Superior de la
#     ultima fila actual en vez de Pegar.
#   - La grilla de vigencia actual, cuando esta vacia, muestra una fila
#     PLACEHOLDER de un solo <td> ("Sin tramos registrados para esta
#     vigencia.") que TAMBIEN cuenta como <tr> en tbody - un
#     filas.count() > 0 ingenuo la confunde con un tramo real y rompe
#     cualquier lectura de columna (ej. .nth(2) sobre esa fila cuelga 30s
#     esperando una celda que no existe). Ver el chequeo hay_tramos_reales
#     en crear_tramo().
#   - El campo Valor del modal de Tramos, al modificar un tramo EXISTENTE
#     (no uno recien creado), puede mostrar un valor "mezclado" entre el
#     valor viejo y el nuevo (ej. escribir 4444.44 sobre un tramo que tenia
#     3333.33 dejo "3,333.33444444" en la grilla) PESE a hacer Control+A +
#     Delete antes de escribir - reproducido tambien a mano por el usuario
#     SIN el bug (quedo limpio), asi que es sospecha de bug de
#     AUTOMATIZACION (limpieza de campo insuficiente en ese input puntual),
#     no un defecto real de la app. Investigar mas si vuelve a aparecer.
#   - Notificacion automatica al equipo GTE (email, SistemaGrupo=GTE,
#     ItemGrupo=CAMBTAR, CorreoRemitente=ActualizacionPrecios@luzdelsur.com.pe)
#     y el insert en la bitacora de auditoria (tabla audit) NO son
#     verificables solo por UI - documentar como [AVISO], no como fallo.
#
# Requiere del framework compartido (web_lds_core.py, ya inyectado en la
# plantilla de cada proyecto via los bloques NAV / HELPERS_ESPERA):
#   abrir_aplicacion, esperar_fin_de_carga, capturar_paso
# Y la constante SELECTOR_DIALOGO (".mdl-confirmar, nz-modal-container,
# .ant-modal-wrap") ya presente en generate_scripts.py de cada proyecto -
# candidata a subir tambien a web_lds_core.py, es igual de generica.
# ============================================================================
#


def abrir_actualizacion_precios(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Actualización De Precios"], "app-precios-list", paso_excel=paso_excel)


def indice_opcion_precio(frame, texto_buscar):
    """Busca el indice de una opcion del combo Codigo de Precio por texto
    (mas robusto que hardcodear un indice fijo - el select tiene ~1157
    opciones y podria reordenarse si cambia el catalogo real)."""
    select_precio = frame.locator("select").first
    nombres = select_precio.locator("option").all_inner_texts()
    for i, nombre in enumerate(nombres):
        if texto_buscar.upper() in nombre.upper():
            return i
    return None


def leer_precio(app, frame, precio_index, fecha_iso, sector_value):
    """Selecciona un Codigo de Precio (por INDICE de opcion), Fecha de
    Vigencia (YYYY-MM-DD) y Sector Tipico, y presiona Leer."""
    select_precio = frame.locator("select").first
    select_precio.select_option(index=precio_index)
    app.wait_for_timeout(300)
    frame.locator("input[type=date]").fill(fecha_iso)
    app.wait_for_timeout(200)
    frame.locator("select").nth(1).select_option(value=sector_value)
    app.wait_for_timeout(200)
    frame.get_by_role("button", name="Leer", exact=True).click()
    esperar_fin_de_carga(app, frame)
    try:
        frame.locator(".ant-spin-blur").first.wait_for(state="hidden", timeout=8000)
    except PWTimeoutError:
        pass
    app.wait_for_timeout(500)


def confirmar_en_modal_abierto(app, frame, aceptar=True, max_dialogos=4, timeout=8000):
    """Variante de confirmar_si_no() para usar DENTRO de un modal ya
    abierto (ej. la ventana de Tramos). El modal de Tramos TAMBIEN
    matchea SELECTOR_DIALOGO (es un nz-modal-container mas), asi que
    ".first"/".last" sobre ese selector devuelven el modal CONTENEDOR en
    vez del dialogo de confirmacion/resultado apilado encima - se espera
    a que haya un 2do elemento (indice 1) antes de tratar cualquiera de
    ellos como el dialogo a cerrar."""
    texto_final = ""
    for i in range(max_dialogos):
        todos = frame.locator(SELECTOR_DIALOGO)
        try:
            todos.nth(1).wait_for(state="visible", timeout=timeout)
        except PWTimeoutError:
            break
        dialogo = todos.last
        texto_final = dialogo.inner_text()
        boton_si_no = dialogo.get_by_role("button", name=re.compile(r"^S.$" if aceptar else r"^No$"))
        boton_cancelar = dialogo.get_by_role("button", name="Cancelar")
        boton_aceptar = dialogo.get_by_role("button", name="Aceptar")
        es_confirmacion = boton_cancelar.count() > 0 and boton_aceptar.count() > 0
        if boton_si_no.count():
            boton_si_no.click()
        elif es_confirmacion:
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
        app.wait_for_timeout(400)
    return texto_final


def siguiente_nro_tramo(frame):
    """Lee la grilla de vigencia ACTUAL (dentro del modal de Tramos ya
    abierto) y devuelve el proximo Nro. de Tramo consecutivo (ultima fila
    + 1, o 1 si esta vacia)."""
    modal = frame.locator(SELECTOR_DIALOGO).first
    filas = modal.locator("table").first.locator("tbody tr")
    if filas.count() == 0:
        return 1
    primera_celda = filas.last.locator("td").first.inner_text().strip()
    if not primera_celda or not primera_celda.isdigit():
        return 1
    return int(primera_celda) + 1


def crear_tramo(app, frame, nro_tramo, valor, usar_pegar=True):
    """Dentro del modal de Tramos YA ABIERTO, crea un tramo. Ver los
    gotchas de "Pegar" y de la fila placeholder en la ficha tecnica de
    arriba."""
    modal = frame.locator(SELECTOR_DIALOGO).first
    inputs_modal = modal.locator("input")
    campo_nro, campo_inferior, campo_superior, campo_valor = inputs_modal.nth(2), inputs_modal.nth(3), inputs_modal.nth(4), inputs_modal.nth(5)
    campo_nro.click()
    campo_nro.press_sequentially(str(nro_tramo), delay=50)
    app.wait_for_timeout(300)
    filas_actuales = modal.locator("table").first.locator("tbody tr")
    hay_tramos_reales = filas_actuales.count() > 0 and "sin tramos" not in filas_actuales.first.inner_text().lower()
    if usar_pegar and hay_tramos_reales:
        ultimo_superior = filas_actuales.last.locator("td").nth(2).inner_text().replace(",", "").strip()
        campo_inferior.click()
        campo_inferior.press_sequentially(ultimo_superior, delay=50)
        campo_superior.click()
        campo_superior.press_sequentially(str(int(float(ultimo_superior)) + 1000000), delay=50)
        app.wait_for_timeout(300)
    elif usar_pegar:
        fila_anterior = modal.locator("table").nth(1).locator("tbody tr").first
        if fila_anterior.count():
            fila_anterior.click()
            app.wait_for_timeout(300)
        modal.get_by_role("button", name="Pegar", exact=True).click()
        app.wait_for_timeout(500)
    campo_valor.click()
    campo_valor.press_sequentially(str(valor), delay=50)
    app.wait_for_timeout(300)
    modal.get_by_role("button", name="Ingresar", exact=True).click()
    texto = confirmar_en_modal_abierto(app, frame)
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(800)
    return texto


#
# Modulo: Actualizacion De Tasas De Interes (Web LDS)
# Componente Angular: app-tasas-interes-list
# Ruta de menu confirmada en vivo: Interno > Actualización De Tasas De Interés
#
# Ficha tecnica (confirmado en vivo, PR000325-SP3, 16/09/2026):
# "Ultima Fecha Registrada" (texto rojo, no editable) + "Fecha de
# Vigencia" (<input type=date>, campo de consulta) + 8 campos de tasa
# (TAMN/TIPMN Simple y Compuesta, Promedio TAMN-TIPMN, Legal Simple,
# Promedio Compuesta, Promedio Simple) + boton "Ingresar" FIJO (NO alterna
# a "Modificar" como otros aplicativos de este proyecto) + boton dual
# Cerrar/Cancelar.
#
# BUG REAL / precision confirmada en vivo: leer una fecha EXACTA (=Ultima
# Fecha Registrada) no muestra asterisco en ningun campo pero SI un aviso
# amarillo "Esta fecha es historica. Los campos estan en modo consulta."
# (los inputs no quedan realmente `disabled` a nivel HTML pese al aviso -
# si un caso necesita verificar "modo consulta", chequear el aviso, no
# `is_disabled()`). Leer una fecha SIN registro exacto (futura o sin
# historial) marca los 8 campos con un "*" (leyenda "* Tasa proyectada de
# fecha anterior") y el boton dual cambia a "Cancelar".
#
# Tasa Promedio TAMN-TIPMN se recalcula solo AL SALIR de TAMN o TIPMN
# (evento blur, no oninput) - confirmado en vivo la formula: (TAMN + TIPMN)
# / 2, redondeado a 3 decimales.
#
# GOTCHA confirmado en vivo (CP050/CP052, 17/09/2026): a pesar de que esta
# ficha tecnica YA documentaba el formulario real de 8 campos y el modo
# consulta historico desde el 16/09/2026, los casos igual fallaron por
# IGNORARLA - usaron `inputs.nth(1)/nth(3)/nth(4)` posicional (que con 8
# campos en 2 columnas NO caen donde se asume) y `date.today() + N dias`
# en vez de leer "Ultima Fecha Registrada" en vivo. Cualquier caso nuevo
# sobre este modulo DEBE:
#   1. Usar `campo_por_etiqueta(frame, "Tasa TAMN (Interés Simple)")` /
#      "Tasa TIPMN (Interés Simple)" / "Tasa Promedio TAMN - TIPMN" (etc,
#      etiqueta COMPLETA) en vez de indices posicionales.
#   2. Leer "Ultima Fecha Registrada" con
#      `frame.get_by_text(re.compile(r"\d{2}/\d{2}/\d{4}")).first.inner_text()`
#      (es texto plano, no un input) y usar una fecha con margen POR
#      DELANTE de esa (ej. +30 dias), nunca un offset fijo desde
#      `date.today()` - el sistema ya tiene datos cargados bastante mas
#      adelante que "hoy" (confirmado con valores en 2027-2028) y cualquier
#      fecha anterior a "Ultima Fecha Registrada" cae en modo consulta
#      (ver parrafo de arriba).
#
# Este aplicativo no tuvo helpers propios mas alla de abrir_* - los casos
# usan directamente los helpers GENERICOS del proyecto (escribir_campo,
# confirmar_si_no) sobre los inputs/campo_por_etiqueta de la pantalla.
#
# Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
#   abrir_aplicacion, esperar_fin_de_carga, capturar_paso
#


def abrir_actualizacion_tasas_interes(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Actualización De Tasas De Interés"], "app-tasas-interes-list", paso_excel=paso_excel)


#
# Modulo: Actualizacion De Agenda De Facturacion (Web LDS)
# Componente Angular: app-agenda-principal
# Ruta de menu confirmada en vivo: Interno > Actualización De Agenda De Facturación
# Manual de usuario real disponible (si el proyecto lo tiene en
# Documentos/): manual_usuario_agenda_facturacion.pdf - documenta mensajes
# exactos, reglas de calculo de vencimientos y las 3 sub-pantallas.
#
# Ficha tecnica (confirmado en vivo, PR000325-SP3, 16/09/2026):
# Pantalla "Calendario de Facturacion" con 3 secciones:
#   - "Proceso": Fecha de Proceso + Leer/Cancelar.
#   - "Agenda": grilla con fila de filtro/alta EN LA CABECERA (Sector +
#     Fecha Lectura/Emision/Reparto/Corte Boleta/Corte Terr., 7 inputs
#     type=date en total contando Fecha de Proceso) + botones
#     Ingresar/Eliminar/Vencimientos.../Feriados....
#   - "Vencimientos": grilla de vencimientos del sector seleccionado + un
#     8vo input type=date (indice 6) + boton Modifica Fecha.
# TODOS los botones salvo Leer quedan deshabilitados en la carga inicial.
#
# Catalogo real de Tipos de Vencimiento confirmado en vivo: codigo 1
# "REGULADOS" (15 dias, Dias Habiles=N/corridos, el UNICO modificable
# desde esta pantalla principal) y codigo 2 "LIBRES" (20 dias, Dias
# Habiles=S/habiles, "Clientes Libres" - bloqueado para modificar desde
# aqui, da "No puede modificar Fecha de Clientes Libres. Debe de hacerlo
# del modulo de Grandes Clientes.").
#
# BUG / regla de negocio real confirmada en vivo: Fecha Corte Boleta y
# Fecha Corte Terr. son UNICAS EN TODO EL SISTEMA (no por sector) -
# reutilizar una fecha de corte ya usada por CUALQUIER sector en cualquier
# corrida anterior da "La Fecha Corte Boleta: [fecha] ingresada esta
# asignada al sector [X]. Ingrese otra fecha." (o el generico "No se pudo
# registrar la agenda." si la colision es contra la fecha que la MISMA
# sucesion de intentos acaba de consumir). crear_agenda_prueba() sortea la
# Fecha de Proceso al azar en una ventana de ~4 anios en el futuro en cada
# llamada para evitar esto, y reintenta con otra fecha si el sistema
# reporta colision/feriado.
#
# Restriccion de sectores maximetro: Fecha Corte Boleta/Terr. no puede
# caer en lunes ni viernes para esos sectores - por eso los helpers de
# este modulo generan fechas de corte en martes/miercoles/jueves siempre
# (seguro para cualquier sector, no solo maximetro).
#
# Aviso/bloqueo al modificar un vencimiento en sabado/domingo/feriado
# (confirmado en vivo, los 3 casos):
#   - Sabado: aviso "Fecha de Vencimiento es Sabado." (informativo) -
#     Modifica Fecha SI actualiza (con el confirm normal Si/No).
#   - Domingo: aviso "Fecha de Vencimiento es Domingo." - Modifica Fecha
#     BLOQUEA con "Dia feriado o Domingo, ingrese otra fecha." (sin
#     dialogo de confirmacion).
#   - Feriado: sin aviso previo en la grilla, pero Modifica Fecha BLOQUEA
#     con el mismo mensaje que domingo.
#
# PENDIENTE / no reproducible en este ambiente (16/09/2026):
#   - "Modificar vencimiento bloqueado por corte programado" y "Bloqueo
#     por corte programado - eliminar" requieren una fila de Agenda cuyo
#     sector YA este "en proceso de facturacion" (corte programado
#     vigente) - ese estado lo pone un proceso batch real del sistema, no
#     se puede generar via UI. Se escaneo en vivo un rango de ~52 fechas
#     reales sin encontrar ningun sector en ese estado.
#
# Sub-pantalla "Actualizacion de Tipos de Vencimientos" (boton
# Vencimientos..., confirmado en vivo): Cantidad de Vencimientos (solo
# lectura) + fila de edicion (Codigo maxlength=5, Descripcion maxlength=30,
# Cant. Dias type=number min=1, Dias Habiles maxlength=1 "S/N") + grilla +
# boton dual Ingresar/Modificar + Cancelar. Al hacer click en una fila
# existente, el campo Codigo queda "readonly" (NO "disabled" - verificar
# ambos atributos si un caso necesita confirmar "solo lectura"). Mensaje
# de exito: "Registro Actualizado."
#
# Sub-pantalla "Ingreso Dias Feriados" (boton Feriados..., confirmado en
# vivo): campo Ano (input, valores validos 2000-2099, valida con "Ingrese
# un ano valido (2000-2099).") + campo Fecha (type=date) + lista + botones
# Leer/Ingresar/Eliminar/Descargar PDF/Cancelar-Cerrar. Mensajes: "Registro
# Ingresado." / "Registro Eliminado." Al abrir, consulta el ano en curso
# automaticamente. TODOS los anios validos (2000-2099) traen un calendario
# civil/religioso PRE-POBLADO automaticamente (10-11 feriados fijos,
# probado en los extremos 2000/2099 y en 2087) - nunca hay grilla
# realmente vacia sin intervenir.
#
# CONFIRMADO EN VIVO (CP089, 17/09/2026) - "Descargar PDF con grilla
# vacia debe bloquear" SI es reproducible, con estos 3 hallazgos clave:
#   1. La lista de fechas es un `<ul>/<li>` (con estado transitorio de
#      opacidad reducida + spinner de puntos mientras carga), NO una
#      `<table>` - matchear por texto con patron de fecha
#      (`re.compile(r"\d{2}/\d{2}/\d{4}")` via `modal.get_by_text(...)`),
#      nunca `table tbody tr` (da 0 siempre, sin importar cuanto se
#      espere).
#   2. Los feriados FIJOS precargados SI se pueden eliminar uno por uno
#      (NO estan protegidos) - mismo dialogo de confirmacion "¿Esta
#      seguro de eliminar el Feriado?" que un feriado agregado a mano.
#      Vaciando un anio de prueba DEDICADO por completo (ver
#      `_exploracion/diag_cp089_eliminar_feriados.py` de PR000325-SP3
#      como referencia del patron de eliminacion en loop) se llega a la
#      grilla vacia real que pide el caso.
#   3. El modal de esta sub-pantalla tambien sufre el apilamiento
#      documentado abajo (2 `nz-modal-container` superpuestos al abrir) -
#      usar SIEMPRE `.last` sobre SELECTOR_DIALOGO para ubicarlo, nunca
#      `.first` (con `.first` la grilla se lee siempre vacia/vieja, sin
#      importar el polling).
#   Mensaje real de bloqueo con la grilla vacia: "Debe existir datos en
#   la grilla para que puedan ser Impresos." (sin iniciar ninguna
#   descarga). El anio de prueba usado queda vacio de forma PERMANENTE
#   (no hay forma de "recargar" el calendario fijo desde la UI) - si se
#   reutiliza el mismo anio dedicado en corridas futuras, el caso es
#   idempotente (ya lo encuentra vacio, no necesita eliminar nada de
#   nuevo).
#
# BUG REAL confirmado en vivo (timing, presente en TODOS los flujos de
# confirmar/resultado de este modulo): el spinner de carga puede limpiarse
# ANTES de que el dialogo de resultado ("Agenda registrada exitosamente.",
# etc.) termine de renderizarse - un chequeo inmediato tras el spinner a
# veces llega demasiado pronto. Hace falta polling (varios segundos) antes
# de decidir que no hubo ningun dialogo de resultado - ver el polling
# dentro de crear_agenda_prueba() como referencia del patron. Relacionado:
# justo despues de confirmar, el dialogo de "Confirmacion" (Si/No) puede
# seguir un instante en el DOM (animacion de cierre) al mismo tiempo que
# ya aparece el dialogo de resultado - usar SIEMPRE ".last" (el mas
# nuevo) sobre SELECTOR_DIALOGO en vez de ".first" para ubicar el dialogo
# de resultado real.
#
# Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
#   abrir_aplicacion, esperar_fin_de_carga, capturar_paso
# Y helpers/constante GENERICOS del proyecto (no especificos de este
# modulo, ver NUEVO_PROYECTO_CHECKLIST.md Seccion 0c): SELECTOR_DIALOGO.
#


def abrir_actualizacion_agenda_facturacion(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Actualización De Agenda De Facturación"], "app-agenda-principal", paso_excel=paso_excel)


def _fecha_habil_segura(base, offset):
    """Fecha a partir de base+offset dias que cae en martes, miercoles o
    jueves - evita lunes/viernes (restriccion de sectores maximetro en
    Fecha Corte Boleta/Terr.) y fin de semana."""
    d = base + timedelta(days=offset)
    while d.weekday() not in (1, 2, 3):
        d += timedelta(days=1)
    return d


def leer_agenda(app, frame, fecha_proceso_iso):
    """Ejecuta Leer para una Fecha de Proceso dada.

    CONFIRMADO EN VIVO el 17/09/2026: a veces aparece un dialogo (aviso u
    otro) justo cuando "Leer" pasa de deshabilitado a habilitado, y tapa
    el click con un "intercepts pointer events" del overlay
    (nz-modal-container) aunque el boton ya sea clickeable - un chequeo
    unico ANTES de intentar el click no alcanza porque el dialogo puede
    aparecer DESPUES de ese chequeo. Se reintenta en loop: si el click
    falla por timeout, se cierra cualquier dialogo visible y se
    reintenta, en vez de asumir que un solo intento/cierre alcanza.
    """
    frame.locator("input[type=date]").first.fill(fecha_proceso_iso)
    app.wait_for_timeout(300)
    boton_leer = frame.get_by_role("button", name="Leer", exact=True)
    for _intento in range(15):
        dialogo_previo = frame.locator(SELECTOR_DIALOGO)
        if dialogo_previo.count() and dialogo_previo.last.is_visible():
            boton_cierre = dialogo_previo.last.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar|No)$"))
            if boton_cierre.count():
                boton_cierre.first.click()
                app.wait_for_timeout(500)
                continue
        try:
            boton_leer.click(timeout=3000)
            break
        except PWTimeoutError:
            app.wait_for_timeout(500)
    else:
        boton_leer.click()
    esperar_fin_de_carga(app, frame)
    try:
        frame.locator(".ant-spin-blur").first.wait_for(state="hidden", timeout=8000)
    except PWTimeoutError:
        pass
    app.wait_for_timeout(800)


def crear_agenda_prueba(app, frame, sector_valor=None, dias_semana_emision=(1, 2, 3), offset_corte=25):
    """Crea un registro de agenda de facturacion descartable de punta a
    punta (Fecha de Proceso elegida al azar lejos en el futuro + Sector +
    5 fechas validas + Ingresar + confirmar) y devuelve (fecha_proceso,
    sector_valor, corte_boleta, corte_terr) - las 4 fechas/valor quedan
    disponibles para los pasos siguientes del caso (releer, modificar,
    eliminar, etc).

    dias_semana_emision (0=lunes..6=domingo) controla que dia de la
    semana cae la Fecha Emision/Proceso - por defecto martes/miercoles/
    jueves (seguro para cualquier sector), pero algunos casos necesitan
    forzar VIERNES especificamente (para verificar que un vencimiento de
    dias corridos puede caer en sabado sin corregirse - ver ficha
    tecnica del modulo)."""
    for _intento in range(5):
        fecha_proceso = date(2027, 1, 1) + timedelta(days=random.randint(0, 1400))
        while fecha_proceso.weekday() not in dias_semana_emision:
            fecha_proceso += timedelta(days=1)
        fp_iso = fecha_proceso.isoformat()
        corte_boleta = _fecha_habil_segura(fecha_proceso, offset_corte + _intento * 7)
        corte_terr = _fecha_habil_segura(corte_boleta, 3)

        leer_agenda(app, frame, fp_iso)

        select_sector = frame.locator("select").first
        opciones = [v for v in select_sector.locator("option").evaluate_all("els => els.map(e => e.value)") if v]
        valor_sector = sector_valor or opciones[0]
        select_sector.select_option(value=valor_sector)
        app.wait_for_timeout(300)

        inputs_fecha = frame.locator("input[type=date]")
        inputs_fecha.nth(1).fill(fp_iso)
        app.wait_for_timeout(150)
        inputs_fecha.nth(2).fill(fp_iso)
        app.wait_for_timeout(150)
        inputs_fecha.nth(3).fill(fp_iso)
        app.wait_for_timeout(150)
        inputs_fecha.nth(4).fill(corte_boleta.isoformat())
        app.wait_for_timeout(150)
        inputs_fecha.nth(5).fill(corte_terr.isoformat())
        app.wait_for_timeout(300)

        frame.get_by_role("button", name="Ingresar", exact=True).click()
        app.wait_for_timeout(800)
        dialogo = frame.locator(SELECTOR_DIALOGO)
        if not (dialogo.count() and dialogo.last.is_visible()):
            continue
        texto = dialogo.last.inner_text()
        if "modificar" not in texto.lower():
            # Coleccion/feriado/otro rechazo: cerrar el aviso y reintentar
            # con una fecha nueva en la proxima vuelta. Se usa ".last" y
            # se reintenta el click de cierre (mismo riesgo de dialogo
            # apilado que en el resultado final) para no dejar un modal
            # fantasma bloqueando el "Leer" del proximo intento.
            boton_cerrar = dialogo.last.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$"))
            if boton_cerrar.count():
                for _cierre in range(5):
                    boton_cerrar.first.click()
                    app.wait_for_timeout(400)
                    dialogo_actual = frame.locator(SELECTOR_DIALOGO)
                    if not (dialogo_actual.count() and dialogo_actual.last.is_visible()):
                        break
            continue
        boton_si = dialogo.last.get_by_role("button", name=re.compile(r"^S.?$"))
        boton_si.first.click()
        esperar_fin_de_carga(app, frame)
        for _i in range(30):
            app.wait_for_timeout(400)
            if not frame.locator(".ant-spin-blur").count():
                break
        # El spinner puede limpiarse ANTES de que el dialogo de resultado
        # ("Agenda registrada exitosamente.") termine de renderizarse -
        # se hace polling hasta 6s esperando a que el dialogo de
        # resultado aparezca antes de decidir que no hubo ninguno.
        dialogo_resultado = None
        for _i in range(15):
            app.wait_for_timeout(400)
            resultado = frame.locator(SELECTOR_DIALOGO)
            if resultado.count() and resultado.last.is_visible():
                dialogo_resultado = resultado.last
                break
        if dialogo_resultado is not None:
            # El dialogo de "Confirmacion" (Si/No) puede seguir un
            # instante en el DOM (animacion de cierre) al mismo tiempo
            # que ya aparece el dialogo de resultado - con dos matches
            # de SELECTOR_DIALOGO al mismo tiempo, ".first" a veces
            # resuelve al dialogo VIEJO. Se usa ".last" (el mas nuevo).
            texto_resultado = dialogo_resultado.inner_text()
            boton_cerrar2 = dialogo_resultado.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$"))
            if boton_cerrar2.count():
                for _cierre in range(5):
                    boton_cerrar2.first.click()
                    app.wait_for_timeout(400)
                    resultado_actual = frame.locator(SELECTOR_DIALOGO)
                    if not (resultado_actual.count() and resultado_actual.last.is_visible()):
                        break
            if "exitosamente" in texto_resultado.lower():
                return fecha_proceso, valor_sector, corte_boleta, corte_terr
    raise AssertionError("No se pudo crear una agenda de prueba tras varios intentos (colisiones de fecha de corte)")


abrir_rf01 = abrir_mantenedor_tablas
abrir_rf02 = abrir_relacion_sucursal_sector_zona
abrir_rf03 = abrir_actualizacion_agenda_pagos
abrir_rf04 = abrir_actualizacion_documentos
abrir_rf05 = abrir_actualizacion_conceptos
abrir_rf06 = abrir_actualizacion_precios
abrir_rf07 = abrir_actualizacion_tasas_interes
abrir_rf10 = abrir_actualizacion_agenda_facturacion

_EMU_POR_PULGADA = 914400
_ANCHO_MAX_PULGADAS = 6.3


def _tamano_png(ruta):
    """Lee ancho/alto (px) del header IHDR de un PNG, sin depender de Pillow."""
    with open(ruta, "rb") as f:
        data = f.read(33)
    ancho, alto = struct.unpack(">II", data[16:24])
    return ancho, alto


def _calcular_extent_emu(ancho_px, alto_px, dpi=96):
    ancho_in = ancho_px / dpi
    alto_in = alto_px / dpi
    if ancho_in > _ANCHO_MAX_PULGADAS:
        factor = _ANCHO_MAX_PULGADAS / ancho_in
        ancho_in *= factor
        alto_in *= factor
    return int(ancho_in * _EMU_POR_PULGADA), int(alto_in * _EMU_POR_PULGADA)


def _etiqueta_paso_png(ruta_png):
    """'CP002_03_antes_de_buscar.png' -> 'Paso 3: antes de buscar'."""
    base = ruta_png.stem
    resto = base[len(CASO) + 1:] if base.startswith(CASO + "_") else base
    m = re.match(r"^(\d{2})_(.+)$", resto)
    if m:
        numero, desc = m.groups()
        return f"Paso {int(numero)}: {desc.replace('_', ' ')}"
    if resto == "error":
        return "Captura de error"
    return resto.replace("_", " ")


_DOCX_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Default Extension="png" ContentType="image/png"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    "</Types>"
)

_DOCX_RELS_RAIZ = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    "</Relationships>"
)

_DOCX_NS = (
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
)


def _docx_parrafo(texto, estilo=None):
    pPr = f'<w:pPr><w:pStyle w:val="{estilo}"/></w:pPr>' if estilo else ""
    return f'<w:p>{pPr}<w:r><w:t xml:space="preserve">{_escape_xml(texto)}</w:t></w:r></w:p>'


def _docx_parrafo_imagen(indice, rid, nombre_media, cx, cy):
    return (
        "<w:p><w:r><w:drawing>"
        f'<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{indice}" name="{_escape_xml(nombre_media)}"/>'
        "<a:graphic><a:graphicData uri=\"http://schemas.openxmlformats.org/drawingml/2006/picture\">"
        "<pic:pic>"
        f'<pic:nvPicPr><pic:cNvPr id="{indice}" name="{_escape_xml(nombre_media)}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        "</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>"
    )


def _parsear_pasos_excel(texto_pasos):
    """"1. Ingresar codigo nuevo.\n2. Presionar Leer." -> {1: "1. Ingresar
    codigo nuevo.", 2: "2. Presionar Leer."} - conserva la linea completa
    (con el numero) como texto del encabezado, solo la indexa por numero."""
    pasos = {}
    for linea in texto_pasos.splitlines():
        linea = linea.strip()
        m = re.match(r"^(\d+)\.\s*.+$", linea)
        if m:
            pasos[int(m.group(1))] = linea
    return pasos


def generar_word_evidencia():
    """Arma CASO_evidencia.docx con todas las capturas .png que ya existen
    en EVIDENCIA. No depende de python-docx/lxml (arma el .docx a mano con
    zipfile, libreria estandar) ni de ningun otro archivo del proyecto.
    Pensado para revision FUNCIONAL (no tecnica): cada captura se agrupa
    bajo el texto REAL del paso de la matriz Excel al que corresponde
    (via CAPTURAS_POR_PASO_EXCEL, poblado por capturar_paso(...,
    paso_excel=N) - ver CAPTURAR_PASO_CODE), en vez de listar el texto de
    "Pasos a seguir" aparte y las capturas con una etiqueta tecnica
    derivada del nombre de archivo. Las capturas sin paso_excel asignado
    (o si el caso no uso ese parametro en absoluto) quedan en una seccion
    "Otras capturas" al final, con su etiqueta tecnica de siempre como
    respaldo. "Resultado esperado" cierra el documento."""
    pngs = sorted(EVIDENCIA.glob("*.png"))
    if not pngs:
        return
    rels = []
    medias = []
    cuerpo = [_docx_parrafo(f"{CASO} - {NOMBRE_CASO}", "Title")]
    cuerpo.append(_docx_parrafo(f"RF: {RF_CASO}  |  CU: {CU_CASO}"))
    cuerpo.append(_docx_parrafo(f"Descripcion: {DESCRIPCION_CASO}"))

    contador_imagen = [0]

    def agregar_imagen(ruta_png):
        contador_imagen[0] += 1
        i = contador_imagen[0]
        ancho_px, alto_px = _tamano_png(ruta_png)
        cx, cy = _calcular_extent_emu(ancho_px, alto_px)
        rid = f"rId{i + 1}"
        nombre_media = f"image{i}.png"
        rels.append(
            f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{nombre_media}"/>'
        )
        medias.append((f"word/media/{nombre_media}", ruta_png))
        cuerpo.append(_docx_parrafo_imagen(i, rid, nombre_media, cx, cy))

    pngs_por_nombre = {p.name: p for p in pngs}
    usados = set()

    if CAPTURAS_POR_PASO_EXCEL:
        textos_paso = _parsear_pasos_excel(PASOS_CASO)
        for numero in sorted(CAPTURAS_POR_PASO_EXCEL):
            cuerpo.append(_docx_parrafo(textos_paso.get(numero, f"Paso {numero}"), "Heading2"))
            for nombre_archivo in CAPTURAS_POR_PASO_EXCEL[numero]:
                ruta_png = pngs_por_nombre.get(nombre_archivo)
                if ruta_png is not None:
                    agregar_imagen(ruta_png)
                    usados.add(nombre_archivo)

    pngs_restantes = [p for p in pngs if p.name not in usados and not p.name.endswith("_error.png")]
    if pngs_restantes:
        if usados:
            cuerpo.append(_docx_parrafo("Otras capturas:", "Heading2"))
        for ruta_png in pngs_restantes:
            cuerpo.append(_docx_parrafo(_etiqueta_paso_png(ruta_png), "Heading2"))
            agregar_imagen(ruta_png)

    cuerpo.append(_docx_parrafo("Resultado esperado:", "Heading2"))
    cuerpo.append(_docx_parrafo(RESULTADO_ESPERADO_CASO))

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:document {_DOCX_NS}><w:body>"
        + "".join(cuerpo)
        + '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>'
        "</w:body></w:document>"
    )
    document_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(rels)
        + "</Relationships>"
    )

    destino = EVIDENCIA / f"{CASO}_evidencia.docx"
    try:
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", _DOCX_CONTENT_TYPES)
            z.writestr("_rels/.rels", _DOCX_RELS_RAIZ)
            z.writestr("word/document.xml", document_xml)
            z.writestr("word/_rels/document.xml.rels", document_rels)
            for nombre_interno, ruta_png in medias:
                z.write(ruta_png, nombre_interno)
        print(f"  Word de evidencia: {destino.name} ({len(pngs)} captura(s))")
    except Exception as e:
        print(f"  (aviso) no se pudo generar el Word de evidencia: {e}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=HEADLESS, slow_mo=SLOWMO)
        opciones_contexto = {"viewport": {"width": 1600, "height": 900}}
        if GRABAR_VIDEO:
            opciones_contexto["record_video_dir"] = str(EVIDENCIA)
            opciones_contexto["record_video_size"] = {"width": 1600, "height": 900}
        context = browser.new_context(**opciones_contexto)
        if GRABAR_VIDEO:
            context.add_init_script('(() => {\n  if (window.__pwCursorInjected) return;\n  window.__pwCursorInjected = true;\n\n  const ES_TOP = window.top === window.self;\n\n  function estilizarBase(el, tam) {\n    el.style.position = \'fixed\';\n    el.style.width = tam + \'px\';\n    el.style.height = tam + \'px\';\n    el.style.borderRadius = \'50%\';\n    el.style.pointerEvents = \'none\';\n    el.style.zIndex = \'2147483647\';\n    el.style.transform = \'translate(-50%,-50%)\';\n  }\n\n  if (ES_TOP) {\n    // Documento de nivel superior (page o popup "app"): dibuja el cursor\n    // real. Recibe coordenadas propias (mousemove/mousedown locales) Y\n    // las reenviadas por iframes hijos via postMessage.\n    let cursorEl = null;\n    function asegurarCursor() {\n      if (!document.documentElement) return null;\n      if (!cursorEl) {\n        cursorEl = document.createElement(\'div\');\n        cursorEl.id = \'__pw_cursor\';\n        estilizarBase(cursorEl, 46);\n        cursorEl.style.background = \'rgba(255,0,0,.45)\';\n        cursorEl.style.border = \'5px solid rgba(220,0,0,.95)\';\n        cursorEl.style.boxShadow = \'0 0 14px 4px rgba(255,0,0,.65)\';\n        cursorEl.style.opacity = \'0\';\n        cursorEl.style.transition = \'left .35s ease, top .35s ease, opacity .2s ease\';\n        document.documentElement.appendChild(cursorEl);\n      }\n      return cursorEl;\n    }\n    function moverCursor(x, y) {\n      const el = asegurarCursor();\n      if (!el) return;\n      el.style.left = x + \'px\';\n      el.style.top = y + \'px\';\n      el.style.opacity = \'1\';\n    }\n    function ripple(x, y) {\n      if (!document.documentElement) return;\n      const r = document.createElement(\'div\');\n      estilizarBase(r, 24);\n      r.style.background = \'rgba(255,0,0,.6)\';\n      r.style.left = x + \'px\';\n      r.style.top = y + \'px\';\n      document.documentElement.appendChild(r);\n      const inicio = performance.now();\n      const duracionMs = 1400;\n      function paso(ahora) {\n        const t = Math.min(1, (ahora - inicio) / duracionMs);\n        const tam = 24 + t * (120 - 24);\n        r.style.width = tam + \'px\';\n        r.style.height = tam + \'px\';\n        r.style.opacity = String(0.95 * (1 - t));\n        if (t < 1) requestAnimationFrame(paso);\n        else r.remove();\n      }\n      requestAnimationFrame(paso);\n    }\n\n    document.addEventListener(\'mousemove\', (e) => moverCursor(e.clientX, e.clientY), true);\n    document.addEventListener(\'mousedown\', (e) => ripple(e.clientX, e.clientY), true);\n\n    window.addEventListener(\'message\', (ev) => {\n      const datos = ev.data;\n      if (!datos || datos.__pwCursor !== true) return;\n      let iframeOrigen = null;\n      for (const f of document.querySelectorAll(\'iframe\')) {\n        if (f.contentWindow === ev.source) { iframeOrigen = f; break; }\n      }\n      if (!iframeOrigen) return;\n      const rect = iframeOrigen.getBoundingClientRect();\n      const x = rect.left + datos.x;\n      const y = rect.top + datos.y;\n      if (datos.tipo === \'move\') moverCursor(x, y);\n      else if (datos.tipo === \'click\') ripple(x, y);\n    });\n  } else {\n    // Dentro de un iframe: position:fixed ahi queda acotado al viewport\n    // DEL IFRAME (no de la ventana completa), y ademas el grabador de\n    // video de Playwright no compone bien un overlay asi cuando el\n    // iframe es de otro origen (confirmado en vivo el 10/09/2026 con\n    // PR000325: el cursor SI se veia en captura de pantalla normal pero\n    // NUNCA en el video). Se reenvian las coordenadas al documento de\n    // nivel superior, que es quien realmente dibuja el cursor.\n    document.addEventListener(\'mousemove\', (e) => {\n      window.top.postMessage({ __pwCursor: true, tipo: \'move\', x: e.clientX, y: e.clientY }, \'*\');\n    }, true);\n    document.addEventListener(\'mousedown\', (e) => {\n      window.top.postMessage({ __pwCursor: true, tipo: \'click\', x: e.clientX, y: e.clientY }, \'*\');\n    }, true);\n  }\n})();')
        page = context.new_page()
        app = None
        _CASO_OK = False
        try:
            login(page, paso_excel=1)
            app, frame = abrir_rf06(page)

            indice_tramos = indice_opcion_precio(frame, "ALUMBRADO PUBLICO")
            assert indice_tramos is not None, "No se encontro en el combo un precio en modo Por Tramos conocido (\'ALUMBRADO PUBLICO\') para esta verificacion"
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
            assert "eliminad" in texto_resultado.lower(), f"Se esperaba \'Registro sera Eliminado.\', se vio: {texto_resultado!r}"
            fila_tras_eliminar = modal.locator("table").first.locator("tbody tr").filter(has_text=re.compile(r"2,?222\.22"))
            for _intento in range(16):
                if fila_tras_eliminar.count() == 0:
                    break
                app.wait_for_timeout(500)
            capturar_paso(app, "estado_tras_eliminar", paso_excel=7)
            assert fila_tras_eliminar.count() == 0, "Se esperaba que el tramo eliminado ya no apareciera en la grilla de vigencia actual"
            print("[AVISO] No se pudo verificar en BD que no queden filas de proyeccion futura del tramo eliminado en tramos1 - requiere acceso a BD, fuera del alcance de una verificacion solo-UI.")

            capturar_paso(app, "estado_final_del_caso", paso_excel=max(_parsear_pasos_excel(PASOS_CASO), default=None))
            _CASO_OK = True

        except (PWTimeoutError, AssertionError) as e:
            print(f"[FALLO] {CASO} FALLO: {str(e).encode('ascii', 'replace').decode('ascii')}")
            (app if app else page).screenshot(path=str(EVIDENCIA / f"{CASO}_error.png"), full_page=True)
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
                ruta_portal = _renombrar_video(video_portal, EVIDENCIA / f"{CASO}-1.webm") if video_portal is not None else None
                ruta_app = _renombrar_video(video_app, EVIDENCIA / f"{CASO}-2.webm") if video_app is not None else None
                if ruta_portal and ruta_app:
                    _unir_videos(ruta_portal, ruta_app, EVIDENCIA / f"{CASO}_video.webm")
                elif ruta_portal:
                    try:
                        ruta_portal.replace(EVIDENCIA / f"{CASO}_video.webm")
                    except (PermissionError, OSError) as e:
                        print(f"  (aviso) no se pudo renombrar el video final: {e}")
                elif ruta_app:
                    try:
                        ruta_app.replace(EVIDENCIA / f"{CASO}_video.webm")
                    except (PermissionError, OSError) as e:
                        print(f"  (aviso) no se pudo renombrar el video final: {e}")
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

    print(f"[OK] {CASO}: {NOMBRE_CASO}")


if __name__ == "__main__":
    main()
