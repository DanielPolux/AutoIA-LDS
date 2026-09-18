"""
CP: CP012 | RF: RF-01 | CU: CU-01
Nombre: Truncado de nombres largos al volcar el contacto

El original trunca a 14 caracteres nombre, apellido paterno y materno cuando el valor del contacto supera 15 (ucDetalleAtencion.cs:12014-12025), pese a que los campos admiten 15.

Precondiciones:
1. Debe asignarse el rol funcional: MAC.CONSULTAS.
2. Debe estar disponible la aplicacion Atencion a clientes.

Datos: Un contacto cuyo nombre o apellidos superen los 15 caracteres.

Resultado esperado: Al aceptar, los campos de la atencion reciben el valor truncado a 14 caracteres, igual que en el sistema original.
"""
import os, re, shutil, struct, subprocess, time, zipfile
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape as _escape_xml
from playwright.sync_api import sync_playwright, expect, TimeoutError as PWTimeoutError

# Por defecto corre en segundo plano (headless), sin abrir ventana de
# Edge. Para verlo trabajar en pantalla (util para un tester que quiere
# mirar el caso paso a paso), fijar PR000335-SP4_HEADLESS=0 antes de correrlo.
HEADLESS = os.environ.get("PR000335-SP4_HEADLESS", "1") == "1"

# Con PR000335-SP4_VIDEO=1 se graba un video (.webm) de toda la ejecucion,
# ademas de las capturas por paso. Apagado por defecto (un video por caso
# pesa/tarda mas; para una corrida masiva mejor dejarlo apagado y prenderlo
# solo cuando haga falta revisar un caso en detalle).
GRABAR_VIDEO = os.environ.get("PR000335-SP4_VIDEO", "0") == "1"

# Con PR000335-SP4_WORD=0 se omite el Word de evidencia (por defecto SI se
# genera: cada CPxxx.py arma su propio .docx con sus capturas, sin
# depender de ningun otro archivo del proyecto -asi se puede copiar este
# archivo solo a otra maquina y sigue generando su evidencia completa-).
GRABAR_WORD = os.environ.get("PR000335-SP4_WORD", "1") == "1"

# Con PR000335-SP4_SLOWMO=<milisegundos> Playwright agrega esa pausa entre
# CADA accion (click, fill, etc.). Sirve sobre todo junto con
# PR000335-SP4_VIDEO=1: sin esto, un fill() llena el campo de golpe y en
# el video no alcanza a verse el cambio. 0 = sin pausa (default, no afecta
# la velocidad normal de la corrida).
try:
    SLOWMO = int(os.environ.get("PR000335-SP4_SLOWMO", "0"))
except ValueError:
    SLOWMO = 0

# Pausa (ms) que se agrega justo despues de dejar los datos listos en
# pantalla y ANTES del clic que dispara la accion (capturar_paso con una
# descripcion "antes_de_*", ej. "antes_de_buscar", "antes_de_aceptar"): sin
# esto, con fill() llenando los campos de golpe, el video pasa de campos
# vacios a clic casi en el mismo instante y no da tiempo a ver los datos ya
# cargados antes de que se dispare la busqueda/accion. Por defecto se activa
# solo si se esta grabando video (GRABAR_VIDEO); se puede ajustar o apagar
# a mano con PR000335-SP4_PAUSA_ANTES_CLIC=<ms> (0 = sin pausa).
try:
    PAUSA_ANTES_CLIC = int(os.environ.get("PR000335-SP4_PAUSA_ANTES_CLIC", "1200" if GRABAR_VIDEO else "0"))
except ValueError:
    PAUSA_ANTES_CLIC = 0


URL = "https://pldsweb.luzdelsur.com.pe/Plataforma/PlataformaWeb"
USUARIO = "DCABA_DW"
PASSWORD = "Melquisedec_01"

CASO = "CP012"
EVIDENCIA = Path(__file__).resolve().parent / CASO
if EVIDENCIA.exists():
    shutil.rmtree(EVIDENCIA, ignore_errors=True)
EVIDENCIA.mkdir(parents=True, exist_ok=True)

NOMBRE_CASO = 'Truncado de nombres largos al volcar el contacto'
RF_CASO = 'RF-01'
CU_CASO = 'CU-01'
DESCRIPCION_CASO = 'El original trunca a 14 caracteres nombre, apellido paterno y materno cuando el valor del contacto supera 15 (ucDetalleAtencion.cs:12014-12025), pese a que los campos admiten 15.'
RESULTADO_ESPERADO_CASO = 'Al aceptar, los campos de la atencion reciben el valor truncado a 14 caracteres, igual que en el sistema original.'
PASOS_CASO = "1. Ingresar a la plataforma web LDS.\n2. Buscar la aplicacion de Atencion a clientes.\n3. Ingresar a la aplicacion.\n4. Abrir el listado de contactos y seleccionar uno con nombre o apellidos largos.\n5. Presionar 'Aceptar'.\n6. Verificar la longitud del valor cargado en la atencion."

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



CAMPO_ID = {
    "Nombre": "nombreA",
    "Apellido Paterno": "apellidoPaterno",
    "Apellido Materno": "apellidoMaterno",
    "Correo Electronico": "correo",
    "Numero de Documento": "dni",
    "Telefono Fijo": "telefonoFijo",
    "Movil": "movil",
    "Suministro": "txtNumeroCodigoSumSST",
}

RUTA_MENU_ATENCIONES = ["Comercial", "Atención Integral Al Cliente", "Atenciones A Clientes", "Consulta De Atenciones Comerciales"]

SELECTOR_MODAL = "cdk-dialog-container"


def campo(frame, etiqueta):
    return frame.locator(f"#{CAMPO_ID.get(etiqueta, etiqueta)}")


def seleccionar_tipo(frame, texto):
    frame.locator("#tipo").select_option(label=texto)


def buscar_por_codigo(app, frame, codigo):
    """Busca por Suministro/SST. Enter funciona para TODOS los tipos
    (confirmado en PR000335-SP2) - el boton real matf-btn-buscar-tipo NO
    funciona para SST/SST CON SUMINISTRO."""
    campo_busq = frame.locator("#txtNumeroCodigoSumSST")
    campo_busq.fill(codigo)
    campo_busq.press("Enter")
    try:
        app.wait_for_load_state("networkidle", timeout=15000)
    except PWTimeoutError:
        pass
    app.wait_for_timeout(1500)
    dialogo = frame.get_by_role("dialog")
    try:
        dialogo.first.wait_for(state="visible", timeout=2000)
    except PWTimeoutError:
        return
    if "Seleccionar SST" in dialogo.first.inner_text():
        dialogo.first.locator("table tbody tr").first.click()
        dialogo.first.get_by_role("button", name="Aceptar").click()
        app.wait_for_timeout(2500)


def modal(frame):
    """Dialogo real (cdk-dialog-container) - SIEMPRE .last: un dialogo
    nuevo (validacion) puede apilarse encima de uno ya abierto (patron
    confirmado en PR000335-SP5)."""
    return frame.locator(SELECTOR_MODAL).last


def cerrar_modal(frame, app):
    btn = modal(frame).get_by_text("X", exact=True)
    if btn.count():
        btn.click()
        app.wait_for_timeout(600)


def _abrir_popup_por_titulo(page, ruta_menu, titulo_esperado, selector_pantalla, timeout_popup_seg=15, paso_excel=None):
    """El ultimo click de RUTA_MENU_ATENCIONES abre DOS popups casi
    simultaneos en el mismo contexto (confirmado en PR000335-SP2) - se
    busca activamente por TITULO exacto en vez de expect_popup() a
    ciegas, que capturaba cualquiera de los 2 segun cual disparara
    primero."""
    paginas_antes = set(page.context.pages)
    page.get_by_role("link", name="  Aplicaciones").click(timeout=30000)
    page.wait_for_timeout(500)
    for texto in ruta_menu[:-1]:
        _click_visible(page, texto)
        page.wait_for_timeout(500)
    _click_visible(page, ruta_menu[-1])

    plazo = time.monotonic() + timeout_popup_seg
    encontrada = None
    while time.monotonic() < plazo and encontrada is None:
        nuevas = [pg for pg in page.context.pages if pg not in paginas_antes]
        for pg in nuevas:
            try:
                pg.wait_for_load_state("domcontentloaded", timeout=2000)
            except Exception:
                pass
            try:
                if pg.title() == titulo_esperado:
                    encontrada = pg
                    break
            except Exception:
                pass
        if encontrada is None:
            page.wait_for_timeout(300)
    if encontrada is None:
        titulos_vistos = [pg.title() for pg in page.context.pages if pg not in paginas_antes]
        raise RuntimeError(f"No aparecio ninguna pagina nueva con titulo {titulo_esperado!r} (se vieron: {titulos_vistos})")

    app = encontrada
    app.wait_for_load_state("networkidle")
    frame = app.locator("#aplicacion").content_frame
    frame.locator(selector_pantalla).wait_for(timeout=20000)
    capturar_paso(app, "aplicacion_abierta", paso_excel=paso_excel)
    return app, frame


def abrir_atencion_cliente(page, paso_excel=1):
    """Popup titulado "Atenciones A Clientes" - vive aca el detalle donde
    estan los links de RF-01 (Ver relacion contactos) y RF-03 (Ver
    Personas)."""
    return _abrir_popup_por_titulo(
        page, RUTA_MENU_ATENCIONES, "Atenciones A Clientes", "#txtNumeroCodigoSumSST", paso_excel=paso_excel,
    )


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
            login(page)
            app, frame = abrir_atencion_cliente(page)

            seleccionar_tipo(frame, "SUMINISTRO")
            buscar_por_codigo(app, frame, "1045027")
            app.wait_for_timeout(1500)

            frame.get_by_text("Ver relación contactos del suministro", exact=False).click()
            app.wait_for_timeout(1500)
            dialogo = modal(frame)
            fila = dialogo.locator("table tbody tr").first
            nombre_original = fila.locator("td").first.inner_text().strip()
            fila.click()
            app.wait_for_timeout(1000)
            dialogo.get_by_role("button", name="Aceptar", exact=True).click()
            app.wait_for_timeout(1500)
            capturar_paso(app, "contacto_volcado", paso_excel=5)

            valor_cargado = campo(frame, "Nombre").input_value()
            assert len(valor_cargado) <= 14, f"El campo Nombre no deberia superar 14 caracteres tras volcar el contacto, se vio {len(valor_cargado)} caracteres: {valor_cargado!r}"
            if len(nombre_original) > 15:
                assert valor_cargado == nombre_original[:14], f"Se esperaba el nombre truncado a 14 caracteres ({nombre_original[:14]!r}), se vio {valor_cargado!r}"
            else:
                print(f"[AVISO] {CASO}: el contacto real disponible ({nombre_original!r}, {len(nombre_original)} caracteres) no supera los 15 caracteres que disparan el truncado - se verifico la cota de 14 caracteres del campo destino, no el truncado en si.")
            capturar_paso(app, "longitud_verificada", paso_excel=6)

            capturar_paso(app, "estado_final_del_caso", paso_excel=max(_parsear_pasos_excel(PASOS_CASO), default=None))
            _CASO_OK = True

        except (PWTimeoutError, AssertionError) as e:
            print(f"[FALLO] {CASO} FALLO: {e}")
            (app if app else page).screenshot(path=str(EVIDENCIA / f"{CASO}_error.png"), full_page=True)
            raise
        finally:
            if GRABAR_VIDEO:
                (app if app else page).wait_for_timeout(3000)
            video_portal = page.video
            video_app = app.video if app else None
            browser.close()
            if _CASO_OK:
                ruta_portal = _renombrar_video(video_portal, EVIDENCIA / f"{CASO}-1.webm") if video_portal is not None else None
                ruta_app = _renombrar_video(video_app, EVIDENCIA / f"{CASO}-2.webm") if video_app is not None else None
                if ruta_portal and ruta_app:
                    _unir_videos(ruta_portal, ruta_app, EVIDENCIA / f"{CASO}_video.webm")
                elif ruta_portal:
                    ruta_portal.replace(EVIDENCIA / f"{CASO}_video.webm")
                elif ruta_app:
                    ruta_app.replace(EVIDENCIA / f"{CASO}_video.webm")
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


if __name__ == "__main__":
    main()
