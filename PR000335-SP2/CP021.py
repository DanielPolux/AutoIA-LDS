"""
CP021 - Casilla Sin Apellidos inhabilita y limpia sus campos

RF: RF-01   CU: CU-01
Descripcion: El EF establece que la casilla 'Sin Apellidos' inhabilita y limpia los campos Apellido Paterno y Apellido Materno.
Precondicion: 1. Debe asignarse el rol funcional: MAC.CONSULTAS.
2. Debe estar disponible la aplicacion Atencion al Cliente.
Datos de prueba: Casilla 'Sin Apellidos' marcada, con Apellido Paterno y Apellido Materno previamente completados.
Resultado esperado: Al marcar la casilla, los campos Apellido Paterno y Apellido Materno quedan inhabilitados y con su contenido limpio.

Pasos a seguir (segun matriz de casos original):
1. Ingresar a la plataforma web LDS.
2. Buscar la aplicacion de Atencion al Cliente.
3. Ingresar a la aplicacion.
4. Completar Apellido Paterno y Apellido Materno en la seccion Informacion del Contacto.
5. Marcar la casilla 'Sin Apellidos'.
6. Verificar que los campos Apellido Paterno y Apellido Materno quedan inhabilitados y vacios.

*** SELECTORES SIN CONFIRMAR EN VIVO *** (ambiente caido al
13/09/2026, ver memoria pr000335-2-registro-atencion-error-servidor.md
y el docstring de generate_scripts.py) - revisar contra el HTML real
apenas el ambiente este arriba, siguiendo el Paso 2 del checklist.

Por defecto corre en segundo plano (headless). Para verlo trabajar:
    set PR000335-2_HEADLESS=0
    python CP021.py
"""
import os, random, re, shutil, struct, subprocess, time, zipfile
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape as _escape_xml
from playwright.sync_api import sync_playwright, expect, TimeoutError as PWTimeoutError

# Por defecto corre en segundo plano (headless), sin abrir ventana de
# Edge. Para verlo trabajar en pantalla (util para un tester que quiere
# mirar el caso paso a paso), fijar PR000335-2_HEADLESS=0 antes de correrlo.
HEADLESS = os.environ.get("PR000335-2_HEADLESS", "1") == "1"

# Con PR000335-2_VIDEO=1 se graba un video (.webm) de toda la ejecucion,
# ademas de las capturas por paso. Apagado por defecto (un video por caso
# pesa/tarda mas; para una corrida masiva mejor dejarlo apagado y prenderlo
# solo cuando haga falta revisar un caso en detalle).
GRABAR_VIDEO = os.environ.get("PR000335-2_VIDEO", "0") == "1"

# Con PR000335-2_WORD=0 se omite el Word de evidencia (por defecto SI se
# genera: cada CPxxx.py arma su propio .docx con sus capturas, sin
# depender de ningun otro archivo del proyecto -asi se puede copiar este
# archivo solo a otra maquina y sigue generando su evidencia completa-).
GRABAR_WORD = os.environ.get("PR000335-2_WORD", "1") == "1"

# Con PR000335-2_SLOWMO=<milisegundos> Playwright agrega esa pausa entre
# CADA accion (click, fill, etc.). Sirve sobre todo junto con
# PR000335-2_VIDEO=1: sin esto, un fill() llena el campo de golpe y en
# el video no alcanza a verse el cambio. 0 = sin pausa (default, no afecta
# la velocidad normal de la corrida).
try:
    SLOWMO = int(os.environ.get("PR000335-2_SLOWMO", "0"))
except ValueError:
    SLOWMO = 0

# Pausa (ms) que se agrega justo despues de dejar los datos listos en
# pantalla y ANTES del clic que dispara la accion (capturar_paso con una
# descripcion "antes_de_*", ej. "antes_de_buscar", "antes_de_aceptar"): sin
# esto, con fill() llenando los campos de golpe, el video pasa de campos
# vacios a clic casi en el mismo instante y no da tiempo a ver los datos ya
# cargados antes de que se dispare la busqueda/accion. Por defecto se activa
# solo si se esta grabando video (GRABAR_VIDEO); se puede ajustar o apagar
# a mano con PR000335-2_PAUSA_ANTES_CLIC=<ms> (0 = sin pausa).
try:
    PAUSA_ANTES_CLIC = int(os.environ.get("PR000335-2_PAUSA_ANTES_CLIC", "1200" if GRABAR_VIDEO else "0"))
except ValueError:
    PAUSA_ANTES_CLIC = 0


URL = "https://pldsweb.luzdelsur.com.pe/Plataforma/PlataformaWeb"
USUARIO = "DCABA_DW"
PASSWORD = "Melquisedec_01"  # mismo usuario/clave que PR000325 - confirmado en vivo el 14/09/2026: es el usuario del propio tester, unico necesario para este proyecto (reemplaza a JOBLIT_DW por indicacion explicita)

CASO = "CP021"
EVIDENCIA = Path(__file__).resolve().parent / CASO
if EVIDENCIA.exists():
    shutil.rmtree(EVIDENCIA, ignore_errors=True)
EVIDENCIA.mkdir(parents=True, exist_ok=True)

NOMBRE_CASO = 'Casilla Sin Apellidos inhabilita y limpia sus campos'
RF_CASO = 'RF-01'
CU_CASO = 'CU-01'
DESCRIPCION_CASO = "El EF establece que la casilla 'Sin Apellidos' inhabilita y limpia los campos Apellido Paterno y Apellido Materno."
RESULTADO_ESPERADO_CASO = 'Al marcar la casilla, los campos Apellido Paterno y Apellido Materno quedan inhabilitados y con su contenido limpio.'
PASOS_CASO = "1. Ingresar a la plataforma web LDS.\n2. Buscar la aplicacion de Atencion al Cliente.\n3. Ingresar a la aplicacion.\n4. Completar Apellido Paterno y Apellido Materno en la seccion Informacion del Contacto.\n5. Marcar la casilla 'Sin Apellidos'.\n6. Verificar que los campos Apellido Paterno y Apellido Materno quedan inhabilitados y vacios."

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
            video1.unlink(missing_ok=True)
            video2.unlink(missing_ok=True)
            return True
        print(f"  (aviso) no se pudieron unir los videos (ffmpeg devolvio {resultado.returncode}); quedan separados.")
        return False
    except Exception as e:
        print(f"  (aviso) no se pudieron unir los videos: {e}; quedan separados.")
        return False
    finally:
        lista.unlink(missing_ok=True)


# --- Informacion del Contacto: ids CONFIRMADOS EN VIVO el 13/09/2026
#     (dump_atencion_cliente_real.py) - calcan el EF casi al 100%. ---
CAMPO_ID = {
    "Nombre": "nombreA",
    "Apellido Paterno": "apellidoPaterno",
    "Apellido Materno": "apellidoMaterno",
    "Correo Electronico": "correo",
    "Numero de Documento": "dni",
    "Referencia de la Direccion de Atencion": "direcionA",
    "Referencia": "referencia",
    "Telefono Fijo": "telefonoFijo",
    "Movil": "movil",
    "Suministro": "txtNumeroCodigoSumSST",  # confirmado en vivo: es el MISMO campo "Suministro / SST", no uno separado
    # Sin confirmar en vivo (no aparecieron en la vista principal ya
    # buscada; podrian vivir en el modal "Anotaciones" u otro lado):
    "Anotacion": "txtAnot",
    "Motivo": "txtMotivo",
}

# Checkboxes "Sin X": ids CONFIRMADOS EN VIVO - notar la falta de
# consistencia real de mayusculas/plural (SinNombre con S mayuscula,
# sinApellido en SINGULAR pese a que el EF y el propio label dicen
# "Sin Apellidos").
CHECKBOX_ID = {
    "Sin Nombre": "SinNombre",
    "Sin Apellidos": "sinApellido",
    "Sin Telefono": "sinTelefono",
    "Sin Correo": "sinCorreo",
    "Sin Documento": "sinDocumento",
}


def campo(frame, etiqueta):
    """Ubica un campo por su id real (ver CAMPO_ID). CONFIRMADO EN VIVO
    el 13/09/2026 para los campos de Informacion del Contacto + el campo
    Suministro/SST; el resto (Anotacion/Motivo) sigue sin confirmar."""
    id_campo = CAMPO_ID.get(etiqueta, etiqueta)
    return frame.locator(f"#{id_campo}")


def secciones_visibles(frame):
    """Titulos de seccion (encabezados) actualmente visibles. CONFIRMADO
    EN VIVO el 13/09/2026: cada seccion real usa `class="barraTitulo"`
    (ej. `<div class="barraTitulo">&nbsp;Información de la Atención</div>`,
    con &nbsp; y espacios variables alrededor - por eso se usa
    " ".join(t.split()) para normalizar antes de comparar). Se excluye el
    titulo del panel exterior "Nuevas Atenciones" (no es una de las
    secciones que declara el EF)."""
    titulos = []
    for h in frame.locator(".barraTitulo").all():
        if h.is_visible():
            t = " ".join(h.inner_text().split())
            if t and t != "Nuevas Atenciones":
                titulos.append(t)
    return titulos


def seleccionar_tipo(frame, texto):
    """Selecciona 'texto' en el combo 'Tipo' (id CONFIRMADO EN VIVO:
    #tipo, opciones reales SUMINISTRO/SST/FNL/SST CON SUMINISTRO/
    SUMINISTRO NUEVO/SAS)."""
    frame.locator("#tipo").select_option(label=texto)


def seleccionar_origen(frame, texto):
    """Selecciona 'texto' en el combo 'Origen' (id CONFIRMADO EN VIVO:
    #origenA - OJO, es un campo DISTINTO de 'Tipo': sus opciones reales
    son B-FACEBOOK, C-CARTA, E-CORREO ELECTRONICO, F-FAX, I-INTERNET,
    K-DENUNCIAS TK, L-LIBRO DE OBSERVACION, N-MEDICION NTCSE, V-VENTANILLA
    (lista puede seguir, no se vieron todas). El 'tipo origen' que
    menciona el EF para CP017/018 -'K - DENUNCIAS TK'- es ESTE campo, no
    'Tipo'."""
    frame.locator("#origenA").select_option(label=texto)


def suministro(frame):
    """Campo 'Suministro / SST'. CONFIRMADO EN VIVO: id=txtNumeroCodigoSumSST,
    es el MISMO campo que usa la busqueda (buscar_por_codigo) - no hay dos
    campos separados como se asumio originalmente."""
    return frame.locator("#txtNumeroCodigoSumSST")


def buscar_por_codigo(app, frame, codigo):
    """CONFIRMADO EN VIVO el 14/09/2026: el boton 'matf-btn-buscar-tipo'
    funciona para tipo SUMINISTRO/SUMINISTRO NUEVO, pero para SST (y
    probablemente SST CON SUMINISTRO, que ademas ni deja hacer click en
    el boton - timeout confirmado) el dato real que usa el tester es
    presionar Enter en el campo tras llenarlo. Enter funciona para todos
    los tipos probados, asi que se usa siempre en vez de depender del
    boton (mas simple y mas robusto)."""
    campo = frame.locator("#txtNumeroCodigoSumSST")
    campo.fill(codigo)
    campo.press("Enter")
    # BUG REAL confirmado en vivo (RF-02/CP043, 15/09/2026): fill()
    # sin esperar a que la busqueda termine de cargar dejaba el resto
    # de la pantalla (Inf. Tecnica, iconos de Cortes/Mediciones) sin
    # datos reales asociados - los iconos nunca se volvian visibles
    # aunque el codigo estuviera escrito en el campo. Se espera la
    # carga real antes de seguir.
    try:
        app.wait_for_load_state("networkidle", timeout=15000)
    except PWTimeoutError:
        pass
    app.wait_for_timeout(1500)
    # BUG REAL / paso adicional confirmado en vivo (CP013, 14/09/2026,
    # codigo 2074382): para tipo SST CON SUMINISTRO, si el suministro
    # tiene una o mas solicitudes SST asociadas, Enter abre un dialogo
    # INTERMEDIO "Seleccionar SST por suministro" (grilla de
    # solicitudes) - hay que elegir una fila y confirmar con Aceptar
    # antes de que el resto de la pantalla (#cliente, etc.) se
    # autocomplete. Para los demas tipos (y para un codigo sin
    # solicitud asociada) este dialogo no aparece, asi que el chequeo
    # es un no-op inofensivo el resto de las veces.
    dialogo = frame.get_by_role("dialog")
    try:
        dialogo.first.wait_for(state="visible", timeout=2000)
    except PWTimeoutError:
        return
    if "Seleccionar SST" in dialogo.first.inner_text():
        dialogo.first.locator("table tbody tr").first.click()
        dialogo.first.get_by_role("button", name="Aceptar").click()
        # Tras confirmar, la pantalla sigue cargando la Info. de SST un
        # momento mas (spinner propio, no atado a la red de forma que
        # "networkidle" lo detecte) - confirmado en vivo que la captura
        # "antes_de_verificar_autocompletado" salia con el spinner
        # todavia girando. Se espera de mas por las dudas.
        app.wait_for_timeout(2500)


def marcar_checkbox(frame, etiqueta):
    """CONFIRMADO EN VIVO: usa el id real (ver CHECKBOX_ID), no
    get_by_label (no se confirmo que estos checkboxes tengan un <label
    for=...> real asociado)."""
    id_checkbox = CHECKBOX_ID.get(etiqueta, etiqueta)
    frame.locator(f"#{id_checkbox}").check()


def desmarcar_checkbox(frame, etiqueta):
    id_checkbox = CHECKBOX_ID.get(etiqueta, etiqueta)
    frame.locator(f"#{id_checkbox}").uncheck()


def completar_informacion_contacto_minima(frame):
    """Completa el minimo de Informacion del Contacto para habilitar la
    grilla Pedidos, segun el EF (seccion obligatoria para habilitar
    edicion). SIN CONFIRMAR EN VIVO cuales campos son el minimo real -
    se completan todos los conocidos por las dudas."""
    campo(frame, "Nombre").fill("CONTACTO PRUEBA")
    campo(frame, "Apellido Paterno").fill("PRUEBA")
    campo(frame, "Apellido Materno").fill("PRUEBA")
    campo(frame, "Telefono Fijo").fill("1234567")


def completar_pedido_minimo(frame):
    """Completa el minimo de un registro en la grilla Pedidos (se asume
    que es la ULTIMA tabla de la pantalla). SIN CONFIRMAR EN VIVO."""
    grilla_pedidos = frame.get_by_role("table").last
    fila = grilla_pedidos.locator("tbody tr").first
    select_tipo_pedido = fila.locator("select").first
    if select_tipo_pedido.count():
        seleccionar_primera_opcion(select_tipo_pedido)


# --- RF-02: Cortes Programados ---
def expandir_inf_tecnica(frame):
    """CONFIRMADO EN VIVO el 13/09/2026: los iconos de Cortes Programados
    y Mediciones Programadas por Norma existen en el DOM pero quedan
    OCULTOS hasta expandir la seccion 'Inf. Tecnica' del sidebar
    izquierdo (no son botones de texto sueltos como se asumio original-
    mente). Hay que llamar esto antes de abrir_cortes_programados() o
    abrir_mediciones_programadas()."""
    frame.get_by_text("Inf. Técnica", exact=False).first.click()


def abrir_cortes_programados(app, frame):
    """CONFIRMADO EN VIVO: no es un <button> con texto "Cortes
    Programados" sino un <img title="Cortes Programados"> (icono
    Icon/bateria.png) dentro de la seccion 'Inf. Tecnica', oculto hasta
    expandirla (se expande sola aqui, con chequeo de visibilidad primero
    para no volver a colapsarla si otro caso ya la dejo abierta). Con el
    suministro 1045027 (sin cortes) abre un dialog real con el mensaje
    EXACTO "No se encontraron cortes programados" (confirma CP046
    literal); con el suministro 204850 (CON cortes, dato real
    confirmado en vivo el 15/09/2026) abre el MISMO dialog pero con una
    grilla real bajo el titulo "Ultimas Interrupciones" (ver
    modal_cortes). BUG REAL confirmado en vivo (15/09/2026): sin
    esperar a que la busqueda del suministro termine de cargar antes de
    expandir 'Inf. Tecnica', el icono nunca se estabiliza como visible
    y el click original quedaba reintentando hasta timeout (visto en
    CP043/046/051/095) - se agrega una espera corta tras expandir."""
    icono = frame.locator('img[title="Cortes Programados"]')
    if not icono.is_visible():
        expandir_inf_tecnica(frame)
        app.wait_for_timeout(1000)
    icono.click()


def modal_cortes(frame):
    """CONFIRMADO EN VIVO el 15/09/2026 con el suministro 204850: el
    dialogo real es un <cdk-dialog-container role="dialog">, titulo
    "Cortes Programados". Cuando NO hay cortes muestra un <app-alert>
    (texto "No se encontraron cortes programados", boton Aceptar, SIN
    tabla). Cuando SI hay cortes muestra una seccion "Ultimas
    Interrupciones" con una tabla real, columnas: Codigo | Fecha Inicio
    | Fecha Fin | Estado | fecha_ini_int (ej. fila real: SP 1901290540
    | 29/05/2026 16:00:00 | 29/05/2026 17:00:00 | APROBADO |
    29/05/2026 16:00:00). NO hay columna de "nivel de tension" ni de
    "tipo" (programado/incidencia) visible en esta grilla - CP060/061/
    062 (que asumen esas columnas) no se pueden verificar tal como
    estan escritos, ver AVISO en cada uno."""
    return frame.get_by_role("dialog")


# --- RF-03: Instalacion Programada por Norma ---
def abrir_mediciones_programadas(app, frame):
    """OJO: el EF llama a este boton "Instalaciones en Medidor x Control
    Calidad", pero el tooltip REAL confirmado en vivo es "Mediciones
    programadas por norma" (<img title="Mediciones programadas por norma">
    o "...por Norma", el propio HTML tiene la mayuscula inconsistente
    entre 2 apariciones) - tambien dentro de 'Inf. Tecnica' ya expandida.
    Alias abrir_instalaciones se deja por compatibilidad con los cuerpos
    de caso ya generados. CONFIRMADO EN VIVO el 15/09/2026: al hacer
    click abre un <cdk-dialog-container role="dialog"> (NO una pestana
    como se asumia) con TRES grillas separadas - la que corresponde a
    RF-03/EF es "Mediciones programadas por Calidad de Producto
    (Control Tecnico)" (columnas: Periodo | Suministro | Nombre |
    Estado | Det.No Medicion | Resultado | Fecha Instal. Prog | Fecha
    Retiro. Prog | Fecha Instal. Real | Fecha Retiro Real) - ver
    modal_instalaciones. Mismo BUG REAL de timing que
    abrir_cortes_programados: se espera tras expandir."""
    icono = frame.locator('img[title="Mediciones programadas por norma"], img[title="Mediciones programadas por Norma"]').first
    if not icono.is_visible():
        expandir_inf_tecnica(frame)
        app.wait_for_timeout(1000)
    icono.click()


abrir_instalaciones = abrir_mediciones_programadas


def modal_instalaciones(frame):
    """BUG REAL confirmado en vivo el 15/09/2026: NO es una pestana
    (role=tab) - abrir_instalaciones() abre un <cdk-dialog-container
    role="dialog"> real (titulo "Mediciones programadas por norma") con
    TRES grillas separadas (ver abrir_mediciones_programadas):
    "Precision de la Medida" (contraste de medidor - la unica con datos
    reales en los 3 suministros probados: 1045027, 870783, 1768544),
    "Calidad de Producto" (la que coincide textualmente con CP055/057/
    058/063 - Periodo/Estado/etc - pero salio VACIA en los 3 casos
    probados) y "Contraste de Medidor 227" (tambien vacia). OJO: las
    grillas tardan unos segundos en cargar tras abrir el dialogo -
    confirmado en vivo que leerlas antes de tiempo las hace parecer
    vacias cuando en realidad seguian con "Cargando..."."""
    return frame.get_by_role("dialog")


def grilla_instalaciones(dialogo, indice=1):
    """Ubica una de las 3 tablas reales dentro del dialogo de
    abrir_instalaciones (ver modal_instalaciones). indice=0 Precision
    de la Medida, indice=1 (default) Calidad de Producto - la que
    coincide con el EF/RF-03 -, indice=2 Contraste de Medidor 227."""
    return dialogo.get_by_role("table").nth(indice)


def grilla_tiene_datos(grilla):
    """BUG REAL confirmado en vivo (CP056/058, 15/09/2026): una grilla
    "vacia" en este dialogo NO tiene 0 filas - Angular deja UNA fila
    <tr> fantasma con TODAS las celdas en blanco (confirmado con
    captura: encabezados visibles, ninguna fila con dato real). Un
    chequeo de count()==0 no la detecta y deja pasar casos como si
    hubiera datos reales (falso OK). Se considera "sin datos" tambien
    cuando la unica fila esta vacia."""
    filas = grilla.locator("tbody tr")
    if filas.count() == 0:
        return False
    return bool(filas.first.inner_text().strip())


# --- RF-04: Listado de Atenciones (grilla + Agregar/Consultar/Modificar/Eliminar) ---
def ejecutar_busqueda_listado(pantalla):
    """Ejecuta una busqueda que devuelva atenciones reales. BUG REAL
    confirmado en vivo (CP066, 14/09/2026): el filtro 'Fecha:' viene
    tildado por defecto con el rango de HOY unicamente (#fFechaDesde/
    #fFechaHasta, ambos <input type="date">) - 'Buscar' sin tocar nada
    mas casi siempre da 0 resultados reales (la grilla muestra una fila
    placeholder "No hay datos para mostrar"). El formulario exige al
    menos un filtro y RECHAZA mas de 31 dias de rango (dialogo
    "Restriccion de Busqueda" / "Restriccion..." si se destilda Fecha
    sin poner otro filtro) - se usan 30 dias hacia atras desde hoy, el
    maximo permitido, que trae filas reales (confirmado: 24 filas)."""
    hoy = date.today()
    desde = hoy - timedelta(days=29)
    pantalla.locator("#fFechaDesde").fill(desde.isoformat())
    pantalla.locator("#fFechaHasta").fill(hoy.isoformat())
    pantalla.get_by_role("button", name="Buscar").click()
    # La busqueda de 30 dias tarda mas que la de "hoy" (el propio aviso
    # de la pantalla lo advierte) - el boton cambia su texto a
    # "Cargando..." mientras tanto, esperar a que vuelva a "Buscar".
    pantalla.get_by_role("button", name="Buscar").wait_for(state="visible", timeout=20000)


def seleccionar_primera_fila(pantalla):
    """Selecciona la primera fila de la grilla de resultados. SIN
    CONFIRMAR EN VIVO - Sprint 1 (PR000335) solo automatizo busqueda/
    filtro de esta pantalla, nunca seleccion de fila ni las acciones
    Agregar/Consultar/Modificar/Eliminar (son nuevas de este sprint)."""
    fila = pantalla.locator("table tbody tr").first
    fila.click()
    return fila


def accion_listado(pantalla, nombre):
    """Botones de accion: Agregar/Consultar/Modificar/Eliminar. BUG
    REAL confirmado en vivo (CP066, 14/09/2026): 'Agregar' es un boton
    UNICO y GLOBAL (arriba de la grilla, fuera de la tabla), pero
    Consultar/Modificar/Eliminar son POR FILA (uno en la columna
    'Acciones' de CADA registro) - buscarlos en 'pantalla' entera con
    datos reales (mas de una fila) da "strict mode violation" al
    matchear las N filas a la vez. Se escopean a la PRIMERA fila (la
    que deja seleccionada seleccionar_primera_fila) para esos 3 casos.
    BUG REAL adicional confirmado en vivo (CP067/069/070/090/093,
    14/09/2026): cada fila tiene TAMBIEN un boton "Modificar Contacto"
    (otra accion, no la de este caso) cuyo nombre accesible CONTIENE
    "Modificar" como substring - name= sin exact=True matcheaba los 2 y
    tiraba "strict mode violation". Se usa exact=True."""
    if nombre == "Agregar":
        return pantalla.get_by_role("button", name=nombre, exact=True)
    return pantalla.locator("table tbody tr").first.get_by_role("button", name=nombre, exact=True)


def intentar_abrir_detalle_desde_listado(app, pantalla, nombre_boton, timeout_ms=6000):
    """CORREGIDO tras corrida real (14/09/2026): Agregar/Consultar/
    Modificar NO cambian de "pestana" dentro de la misma app (no existe
    tal pestana) - abren un POPUP NUEVO independiente (confirmado
    revisando context.pages(): 'Agregar' sobre la fila 1553339-080 abrio
    una ventana titulada 'Atencion a Clientes' con URL
    .../atencion-atenciones?codigo=1553339-080&tipo=1&opcion=agregar,
    con los datos de esa fila ya autocompletados). Devuelve (detalle,
    frame_detalle) si se abrio un popup nuevo dentro de timeout_ms, o
    (None, None) si no se abrio ninguno (util para los casos que esperan
    que la accion NO proceda)."""
    paginas_antes = set(app.context.pages)
    accion_listado(pantalla, nombre_boton).click()
    plazo = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < plazo:
        nuevas = [pg for pg in app.context.pages if pg not in paginas_antes]
        if nuevas:
            detalle = nuevas[0]
            detalle.wait_for_load_state("networkidle")
            # OJO: a diferencia de los popups abiertos desde el MENU (que
            # SI pasan por el wrapper Principal/NuevaPestana + iframe
            # #aplicacion), este popup lo abre el boton Agregar/Consultar/
            # Modificar DESDE ADENTRO del Listado - confirmado en vivo que
            # navega DIRECTO a la URL de tk0s-web (sin wrapper ni iframe),
            # asi que el "frame" a usar es la pagina misma.
            frame_detalle = detalle
            if detalle.locator("#aplicacion").count():
                frame_detalle = detalle.locator("#aplicacion").content_frame
            return detalle, frame_detalle
        app.wait_for_timeout(200)
    return None, None


def intentar_guardar_modificacion(detalle, frame_detalle):
    """Cambia el campo 'Nombre' (id CONFIRMADO, ver CAMPO_ID) y hace
    clic en Aceptar dentro de la pantalla de Modificar. DEFECTO REAL
    CONFIRMADO EN VIVO (CP066/067, 14/09/2026, ver
    _exploracion/network_log_cp066.txt): el backend rechaza CUALQUIER
    guardado de Modificar con 400 Acceso Denegado
    (POST .../api/registro-atencion/ModificarAtencionCliente) y el
    FRONTEND NO MUESTRA NINGUN MENSAJE DE ERROR - el popup vuelve
    silenciosamente a un formulario en blanco con el panel superior en
    estado "Nuevas Atenciones" (confirmado con capturas, ver
    _exploracion/cp093_02_despues_aceptar.png), sin avisar al usuario
    que el guardado fallo. Devuelve True solo si aparece la
    confirmacion real de guardado (nunca deberia dar False mientras
    este defecto siga sin corregir)."""
    frame_detalle.locator("#nombreA").fill("MODIFICACION DE PRUEBA")
    frame_detalle.get_by_role("button", name="Aceptar").click()
    detalle.wait_for_timeout(3000)
    confirmacion = frame_detalle.get_by_text(re.compile("actualiz|guard", re.IGNORECASE))
    return confirmacion.count() > 0 and confirmacion.first.is_visible()


# --- Navegacion real a "Consulta De Atenciones Comerciales": CONFIRMADO
# EN VIVO el 14/09/2026 que el ultimo click de esa ruta de menu abre DOS
# popups casi simultaneos en el MISMO contexto (revisando page.context.pages):
#   - uno titulado "Consulta De Atenciones Comerciales" -> el Listado real
#     (RF-04, componente app-listado-de-atenciones, mismo de PR000335
#     Sprint 1)
#   - otro titulado "Atenciones A Clientes" -> la pantalla de detalle/
#     registro (RF-01/02/03, la que ya se vino usando)
# page.expect_popup() capturaba a ciegas cualquiera de los dos segun cual
# disparara el evento primero - por eso TODAS las corridas anteriores de
# RF-04 (abrir_listado_atenciones apuntando a otra ruta rota) fallaban, y
# por que a veces se penso que el ambiente estaba mas roto de lo que
# realmente esta. Se reemplaza por busqueda activa en context.pages()
# filtrando por titulo exacto.
def _abrir_popup_por_titulo(page, ruta_menu, titulo_esperado, selector_pantalla, timeout_menu=30000, timeout_pantalla=20000, paso_excel=None, timeout_popup_seg=15):
    paginas_antes = set(page.context.pages)
    page.get_by_role("link", name="  Aplicaciones").click(timeout=timeout_menu)
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
    frame.locator(selector_pantalla).wait_for(timeout=timeout_pantalla)
    capturar_paso(app, "aplicacion_abierta", paso_excel=paso_excel)
    return app, frame


# --- CP031-CP033: modal "Informacion de Contacto" ---
# CORREGIDO tras corrida real (13/09/2026): no existe un boton con texto
# "Informacion de Contacto" (timeout confirmado) - el trigger real segun
# la pantalla es el LINK "Información adicional del contacto" (visible en
# la seccion Informacion del Contacto, ver captura 09/12 de _exploracion).
# Sigue sin confirmarse que ESE link abra el mismo modal que describe el
# EF con los mismos campos - es la mejor apuesta disponible.
def abrir_modal_informacion_contacto(frame):
    """CORREGIDO tras corrida real (13/09/2026): get_by_role("link", ...)
    tambien dio timeout - probablemente el <a> real no tiene href (dispara
    la accion via (click) de Angular), asi que el ARIA implicito NO es
    "link" sino "generic" y get_by_role nunca lo encuentra. Se cambia a
    get_by_text, que no depende del role."""
    frame.get_by_text(re.compile("Informaci(o|\u00f3)n adicional del contacto", re.IGNORECASE)).click()

# --- Navegacion: RF-01/02/03 CONFIRMADA en vivo el 13/09/2026 (ruta Y
#     selector_pantalla, ver dump_atencion_cliente_real.py). RF-04 sigue
#     apuntando a la ruta vieja de Tecnico que dio error de assembly -
#     pendiente de re-verificar si esa funcionalidad vive DENTRO de esta
#     misma pantalla (ver docstring del modulo). ---
RUTA_MENU_ATENCIONES = ["Comercial", "Atenci\u00f3n Integral Al Cliente", "Atenciones A Clientes", "Consulta De Atenciones Comerciales"]


def abrir_atencion_cliente(page, paso_excel=1):
    """RF-01, RF-02, RF-03: pantalla de detalle/registro real (popup
    titulado "Atenciones A Clientes" - CONFIRMADO EN VIVO el 14/09/2026
    que ese click de menu abre 2 popups a la vez, ver
    _abrir_popup_por_titulo). selector_pantalla = "#txtNumeroCodigoSumSST"
    (el campo Suministro/SST, CONFIRMADO presente al cargar)."""
    return _abrir_popup_por_titulo(
        page, RUTA_MENU_ATENCIONES, "Atenciones A Clientes", "#txtNumeroCodigoSumSST", paso_excel=paso_excel,
    )


def abrir_listado_atenciones(page, paso_excel=1):
    """RF-04: 'Listado de Atenciones' real - CONFIRMADO EN VIVO el
    14/09/2026 con el usuario DCABA_DW: vive en el SEGUNDO popup (titulado
    "Consulta De Atenciones Comerciales") que abre la MISMA ruta de menu
    de abrir_atencion_cliente - no es una app aparte ni requiere la ruta
    de Tecnico (que seguia rota por el error de assembly, pero resulto
    ser la pista equivocada). Selector de pantalla: app-listado-de-atenciones
    (el MISMO componente Angular de PR000335 Sprint 1)."""
    return _abrir_popup_por_titulo(
        page, RUTA_MENU_ATENCIONES, "Consulta De Atenciones Comerciales", "app-listado-de-atenciones", paso_excel=paso_excel,
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
        try:
            login(page, paso_excel=1)
            app, frame = abrir_atencion_cliente(page)

            campo(frame, 'Apellido Paterno').fill("PRUEBA")
            campo(frame, 'Apellido Materno').fill("PRUEBA")
            capturar_paso(app, "campos_completados", paso_excel=4)
            marcar_checkbox(frame, 'Sin Apellidos')
            capturar_paso(app, "checkbox_marcada", paso_excel=5)
            assert not campo(frame, 'Apellido Paterno').is_enabled(), "Apellido Paterno deberia quedar inhabilitado tras marcar Sin Apellidos"
            assert (campo(frame, 'Apellido Paterno').input_value() or "") == "", "Apellido Paterno deberia quedar vacio tras marcar Sin Apellidos"
            assert not campo(frame, 'Apellido Materno').is_enabled(), "Apellido Materno deberia quedar inhabilitado tras marcar Sin Apellidos"
            assert (campo(frame, 'Apellido Materno').input_value() or "") == "", "Apellido Materno deberia quedar vacio tras marcar Sin Apellidos"
            capturar_paso(app, "campos_inhabilitados_y_vacios", paso_excel=6)

            capturar_paso(app, "estado_final_del_caso", paso_excel=max(_parsear_pasos_excel(PASOS_CASO), default=None))

        except (PWTimeoutError, AssertionError) as e:
            # BUG REAL confirmado en vivo (CP087, 13/09/2026): la consola de
            # Windows usa cp1252 por default, y el mensaje de una excepcion
            # real a veces trae un caracter fuera de ese charset (ej. un
            # glifo de icono capturado sin querer por un locator de texto
            # generico) - un print() directo TAPABA el error real con un
            # UnicodeEncodeError nuevo. Se sanea antes de imprimir.
            print(f"[FALLO] {CASO} FALLO: {str(e).encode('ascii', 'replace').decode('ascii')}")
            (app if app else page).screenshot(path=str(EVIDENCIA / f"{CASO}_error.png"), full_page=True)
            raise
        finally:
            if GRABAR_VIDEO:
                (app if app else page).wait_for_timeout(3000)
            video_portal = page.video
            video_app = app.video if app else None
            browser.close()
            ruta_portal = _renombrar_video(video_portal, EVIDENCIA / f"{CASO}-1.webm") if video_portal is not None else None
            ruta_app = _renombrar_video(video_app, EVIDENCIA / f"{CASO}-2.webm") if video_app is not None else None
            if ruta_portal and ruta_app:
                _unir_videos(ruta_portal, ruta_app, EVIDENCIA / f"{CASO}_video.webm")
            elif ruta_portal:
                try:
                    ruta_portal.replace(EVIDENCIA / f"{CASO}_video.webm")
                except (PermissionError, OSError) as e:
                    # BUG REAL confirmado en vivo (CP042, 13/09/2026): Windows a
                    # veces todavia tiene el .webm abierto en este punto (mismo
                    # motivo por el que _renombrar_video ya reintenta) - sin este
                    # try/except, la excepcion se disparaba DENTRO del finally y
                    # TAPABA el resultado real del caso (uno que habia terminado
                    # OK quedaba marcado FALLO solo por esto). Se deja el video
                    # con su nombre original en vez de perder el resultado real.
                    print(f"  (aviso) no se pudo renombrar el video final: {e}")
            elif ruta_app:
                try:
                    ruta_app.replace(EVIDENCIA / f"{CASO}_video.webm")
                except (PermissionError, OSError) as e:
                    print(f"  (aviso) no se pudo renombrar el video final: {e}")
            if GRABAR_WORD:
                generar_word_evidencia()

    print(f"[OK] {CASO}: {NOMBRE_CASO}")


if __name__ == "__main__":
    main()
