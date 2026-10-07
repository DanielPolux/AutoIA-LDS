"""
web_lds_core.py - Framework compartido para generar automatizaciones
Playwright (Python) de proyectos "Web LDS" (Luz del Sur), a partir de una
matriz de casos de prueba en Excel. Nace de PR000335 (123 casos,
"Consulta De Atenciones Comerciales") como primer proyecto; todo lo que
esta aca es PORTAL-GENERICO (funciona igual sin importar que aplicacion
del portal se este probando).

---------------------------------------------------------------------
COMO SE USA (import en tiempo de GENERACION, no en tiempo de ejecucion)
---------------------------------------------------------------------
Cada proyecto nuevo (PR0000NN) tiene su propio generate_scripts.py, igual
que PR000335. Ese generate_scripts.py es el unico que importa de aca:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_framework"))
    import web_lds_core as core

Y usa los bloques de aca como STRINGS DE CODIGO FUENTE que se insertan tal
cual en cada CPxxx.py generado (via .replace(), igual que ya hace PR000335
con WORD_HELPERS_CODE) -NUNCA se importa web_lds_core en tiempo de
ejecucion desde un CPxxx.py-. Esto es clave: cada CPxxx.py generado sigue
siendo 100% autonomo (se puede copiar solo a otra maquina con Python +
Playwright y corre igual, sin este framework ni ningun otro archivo del
proyecto), que es el requisito original de PR000335 (ver README_PR000335.md).

Ver NUEVO_PROYECTO_CHECKLIST.md (en esta misma carpeta) para el ejemplo
completo de como un generate_scripts.py nuevo arma su HEADER_TEMPLATE
reusando cada bloque de aca.

---------------------------------------------------------------------
QUE HAY ACA (todo extraido y validado en PR000335, corrida real de 123
casos, 09/09/2026)
---------------------------------------------------------------------
- ENV_TOGGLES_CODE          Interruptores por variable de entorno
                            (HEADLESS/VIDEO/WORD/SLOWMO/PAUSA_ANTES_CLIC).
                            Contiene el placeholder de texto __PROYECTO__
                            (reemplazar con .replace(), NO con .format(),
                            antes de insertarlo) que se usa como prefijo
                            de cada variable de entorno, ej. "PR000456_VIDEO".
- CAPTURAR_PASO_CODE        PASO_CONTADOR + capturar_paso(): captura de
                            evidencia numerada + pausa automatica antes de
                            clics (requiere CASO/EVIDENCIA/PAUSA_ANTES_CLIC
                            ya definidos, que son de tu proyecto).
- LOGIN_BLOCK               login(page): formulario de login del portal
                            Web LDS, IDENTICO para cualquier proyecto
                            (mismas carreras async #servidor/#Dominios que
                            costo descubrir en PR000335 - ver comentarios
                            dentro del bloque). Requiere URL/USUARIO/
                            PASSWORD/capturar_paso ya definidos.
- CLICK_VISIBLE_BLOCK       _click_visible(page, texto): clickea el <a>
                            visible que contenga el texto (el menu lateral
                            renderiza el arbol completo oculto).
- ABRIR_APLICACION_BLOCK    abrir_aplicacion(page, ruta_menu,
                            selector_pantalla): generalizacion de
                            abrir_consulta_atenciones() de PR000335 -mismo
                            mecanismo de navegacion (menu > ... > popup >
                            iframe #aplicacion) para cualquier app del
                            portal, parametrizado por la ruta de menus y
                            el selector de la pantalla final. Requiere
                            _click_visible/capturar_paso ya definidos.
- SELECCIONAR_PRIMERA_OPCION_BLOCK
                            seleccionar_primera_opcion(select_locator):
                            elige la primera opcion real (no el
                            placeholder "-- Seleccione --") de un <select>
                            Angular que carga sus opciones de forma
                            asincrona.
- ESPERAR_FIN_CARGA_BLOCK   esperar_fin_de_carga(app, pantalla): espera a
                            que un boton deje de decir "Cargando..." y no
                            quede red pendiente antes de capturar (convencion
                            de UI del portal; si tu app usa otro texto de
                            boton, ajustar el nombre adentro).
- ESPERAR_ANIMACION_BLOCK   esperar_animacion_estable(locator): espera a
                            que un elemento (tipicamente un modal/dialog)
                            deje de moverse/cambiar de tamano por su
                            animacion CSS de entrada, antes de capturar.
- RENOMBRAR_VIDEO_BLOCK     _renombrar_video/_localizar_ffmpeg/_unir_videos:
                            renombra los .webm que graba Playwright al
                            nombre final del caso y los une en uno solo
                            con ffmpeg si hay uno "completo" disponible
                            (con demuxer concat) en el sistema.
- CURSOR_JS_FULL            JS que dibuja un cursor rojo (sigue mousemove
                            real) + "ripple" en cada clic, inyectado con
                            context.add_init_script(...) SOLO si se graba
                            video: Playwright no graba el cursor real del
                            SO (el video es un screencast del DOM via
                            CDP), asi que sin esto no se ve donde se mueve
                            ni hace clic el mouse en el .webm. Insertar con
                            repr(CURSOR_JS_FULL.strip(chr(10))) (ver
                            NUEVO_PROYECTO_CHECKLIST.md) para que quede
                            como un string Python valido sin pelear con
                            escapes de llaves del JS.
- WORD_HELPERS_FULL         Arma el .docx de evidencia (portada + "Pasos a
                            seguir" + una imagen por captura + "Resultado
                            esperado" al final) a mano con zipfile de la
                            libreria estandar -sin depender de
                            python-docx/lxml ni de ningun otro archivo del
                            proyecto-. 100% generico: no conoce nada de la
                            app bajo prueba, solo lee los .png de EVIDENCIA.
                            Pensado para lectura FUNCIONAL (no tecnica):
                            requiere que tu CPxxx.py defina PASOS_CASO
                            (el texto de "Pasos a seguir" tal cual viene de
                            la matriz Excel), ademas de los ya conocidos
                            NOMBRE_CASO/RF_CASO/CU_CASO/DESCRIPCION_CASO/
                            RESULTADO_ESPERADO_CASO.

QUE NO ESTA ACA (varia por proyecto, hay que escribirlo a mano/explorando
en vivo la app real, ver NUEVO_PROYECTO_CHECKLIST.md):
- El cuerpo de cada caso de prueba (logica de negocio, asserts).
- Los selectores de la pantalla especifica (ids, roles, textos de botones).
- La ruta de menus y el selector de pantalla que se le pasan a
  abrir_aplicacion() (SI son especificos de cada app).
- URL/USUARIO/PASSWORD (mismo portal, pero cada proyecto puede correr con
  un usuario de prueba distinto).
"""


# ===========================================================================
# ENV_TOGGLES_CODE
# ===========================================================================
ENV_TOGGLES_CODE = '# Por defecto corre en segundo plano (headless), sin abrir ventana de\n# Edge. Para verlo trabajar en pantalla (util para un tester que quiere\n# mirar el caso paso a paso), fijar __PROYECTO___HEADLESS=0 antes de correrlo.\nHEADLESS = os.environ.get("__PROYECTO___HEADLESS", "1") == "1"\n\n# Con __PROYECTO___VIDEO=1 se graba un video (.webm) de toda la ejecucion,\n# ademas de las capturas por paso. Apagado por defecto (un video por caso\n# pesa/tarda mas; para una corrida masiva mejor dejarlo apagado y prenderlo\n# solo cuando haga falta revisar un caso en detalle).\nGRABAR_VIDEO = os.environ.get("__PROYECTO___VIDEO", "0") == "1"\n\n# Con __PROYECTO___WORD=0 se omite el Word de evidencia (por defecto SI se\n# genera: cada CPxxx.py arma su propio .docx con sus capturas, sin\n# depender de ningun otro archivo del proyecto -asi se puede copiar este\n# archivo solo a otra maquina y sigue generando su evidencia completa-).\nGRABAR_WORD = os.environ.get("__PROYECTO___WORD", "1") == "1"\n\n# Con __PROYECTO___SLOWMO=<milisegundos> Playwright agrega esa pausa entre\n# CADA accion (click, fill, etc.). Sirve sobre todo junto con\n# __PROYECTO___VIDEO=1: sin esto, un fill() llena el campo de golpe y en\n# el video no alcanza a verse el cambio. 0 = sin pausa (default, no afecta\n# la velocidad normal de la corrida).\ntry:\n    SLOWMO = int(os.environ.get("__PROYECTO___SLOWMO", "0"))\nexcept ValueError:\n    SLOWMO = 0\n\n# Pausa (ms) que se agrega justo despues de dejar los datos listos en\n# pantalla y ANTES del clic que dispara la accion (capturar_paso con una\n# descripcion "antes_de_*", ej. "antes_de_buscar", "antes_de_aceptar"): sin\n# esto, con fill() llenando los campos de golpe, el video pasa de campos\n# vacios a clic casi en el mismo instante y no da tiempo a ver los datos ya\n# cargados antes de que se dispare la busqueda/accion. Por defecto se activa\n# solo si se esta grabando video (GRABAR_VIDEO); se puede ajustar o apagar\n# a mano con __PROYECTO___PAUSA_ANTES_CLIC=<ms> (0 = sin pausa).\ntry:\n    PAUSA_ANTES_CLIC = int(os.environ.get("__PROYECTO___PAUSA_ANTES_CLIC", "1200" if GRABAR_VIDEO else "0"))\nexcept ValueError:\n    PAUSA_ANTES_CLIC = 0\n'


# ===========================================================================
# CAPTURAR_PASO_CODE
# ===========================================================================
CAPTURAR_PASO_CODE = 'PASO_CONTADOR = {"n": 0}\nCAPTURAS_POR_PASO_EXCEL = {}  # numero de paso del Excel (int) -> [nombres de archivo .png]\nULTIMA_CAPTURA = {"nombre": None}  # nombre del ultimo .png tomado (ver generar_word_evidencia)\n\n\ndef capturar_paso(objetivo, descripcion, paso_excel=None):\n    """Guarda una captura de evidencia por CADA paso relevante del caso\n    (no solo al final), numerada en orden dentro de la carpeta EVIDENCIA\n    (una por CP). `objetivo` es la Page donde tomar la captura (page antes\n    de abrir el popup, o app una vez abierto).\n\n    `paso_excel` (opcional): numero del paso de la columna "Pasos a\n    seguir" de la matriz Excel al que corresponde esta captura (ej. 3 si\n    esta screenshot ilustra el paso "3. Ingresar codigo nuevo."). Si se\n    pasa, generar_word_evidencia() (ver WORD_HELPERS_FULL) agrupa la\n    imagen bajo el texto real de ESE paso en vez de una etiqueta tecnica\n    derivada del nombre de archivo. Una captura puede repetir el mismo\n    paso_excel que otra anterior (ej. 2 capturas para el mismo paso del\n    Excel) - quedan ambas bajo el mismo encabezado, en orden.\n\n    Si la descripcion empieza con "antes_de" (ej. "antes_de_buscar",\n    "antes_de_aceptar", "antes_de_limpiar", "antes_de_cancelar") se agrega\n    ademas PAUSA_ANTES_CLIC despues de la captura: son justo los pasos\n    donde los datos ya quedaron cargados en pantalla y lo siguiente en el\n    caso es un clic, asi que sin esta pausa el video pasa de "campos\n    llenos" a "clic" casi en el mismo frame."""\n    PASO_CONTADOR["n"] += 1\n    nombre = f"{CASO}_{PASO_CONTADOR[\'n\']:02d}_{descripcion}.png"\n    objetivo.screenshot(path=str(EVIDENCIA / nombre), full_page=True)\n    ULTIMA_CAPTURA["nombre"] = nombre\n    if paso_excel is not None:\n        CAPTURAS_POR_PASO_EXCEL.setdefault(paso_excel, []).append(nombre)\n    if PAUSA_ANTES_CLIC and descripcion.startswith("antes_de"):\n        objetivo.wait_for_timeout(PAUSA_ANTES_CLIC)\n'


# ===========================================================================
# LOGIN_BLOCK (portal Web LDS - identico para todos los proyectos)
# ===========================================================================
LOGIN_BLOCK = 'def login(page, reintentos=2, paso_excel=None):\n    # `paso_excel` (opcional): numero del paso de "Pasos a seguir" del Excel\n    # al que corresponde el login (ej. 1, si el Excel dedica un paso propio\n    # a "Ingresar a la plataforma"). Sin esto, la captura de login siempre\n    # cae en la seccion generica "Otras capturas" del Word de evidencia en\n    # vez de agruparse bajo el paso real (ver generar_word_evidencia()).\n    #\n    # Varios campos del formulario de login se completan via JS de forma\n    # asincrona tras cargar la pagina, en momentos distintos (confirmado en\n    # exploracion en vivo):\n    #   - #servidorWCF / #servidor: vacios al cargar, se llenan ~0.3-1.5s despues.\n    #   - #Dominios (combo oculto de Dominio): arranca con 0 <option> y\n    #     recien se puebla un poco DESPUES de que #servidor ya tiene valor.\n    # Si se envia el login en esa ventana (Playwright llena el formulario\n    # mucho mas rapido que un humano tecleando), el POST sale con el\n    # dominio vacio y el backend responde con mensajes inconsistentes:\n    # "Invalid URI: The hostname could not be parsed.", "No existe\n    # dominio.", "Ud. no tiene acceso a la empresa." Por eso a mano nunca\n    # pasa (tarda de sobra) y en la automatizacion sale intermitente. Se\n    # espera a que AMBAS cosas esten listas antes de tocar el formulario -\n    # pero incluso asi, a veces igual falla el primer intento (confirmado\n    # en vivo en PR000325 el 10/09/2026: fallo 1ra vez con "Ud. no tiene\n    # acceso a la empresa", OK reintentando), por eso se reintenta el\n    # formulario completo hasta `reintentos` veces antes de rendirse.\n    for intento in range(reintentos):\n        page.goto(URL)\n        page.wait_for_function("document.querySelector(\'#servidor\')?.value", timeout=15000)\n        page.wait_for_function("document.querySelector(\'#Dominios\')?.options?.length > 0", timeout=15000)\n        page.get_by_role("textbox", name="Usuario").click()\n        page.get_by_role("textbox", name="Usuario").fill(USUARIO)\n        page.get_by_role("textbox", name="Usuario").press("Tab")\n        page.get_by_role("textbox", name="Contraseña").fill(PASSWORD)\n        page.wait_for_timeout(1000)  # confirmado en vivo el 11/09/2026: dar 1s antes de Ingresar reduce el login fallido intermitente\n        page.get_by_role("button", name="Ingresar ").click()\n        page.wait_for_load_state("networkidle")\n        if "Login" not in page.url:\n            capturar_paso(page, "login", paso_excel=paso_excel)\n            return\n        print(f"  (aviso) login fallo (intento {intento + 1}/{reintentos}), reintentando..." if intento < reintentos - 1 else "  (aviso) login fallo en todos los intentos")\n    capturar_paso(page, "login_fallo")\n    raise RuntimeError(f"No se pudo iniciar sesion tras {reintentos} intento(s) (ver captura *_login_fallo.png).")\n'


# ===========================================================================
# CLICK_VISIBLE_BLOCK y ABRIR_APLICACION_BLOCK (navegacion del portal)
# ===========================================================================
CLICK_VISIBLE_BLOCK = 'def _click_visible(page, text):\n    """Clickea el enlace <a> VISIBLE cuyo texto sea EXACTAMENTE `text` (el\n    menu lateral renderiza el arbol completo oculto; hay que filtrar\n    visibles).\n\n    Usa match EXACTO (regex ancla ^...$, insensible a espacios alrededor),\n    no substring: `filter(has_text=text)` con un string hace substring\n    case-insensitive, y el menu real tiene decenas de items cuyo texto\n    CONTIENE la etiqueta buscada como substring ademas del item exacto (ej.\n    PR000325: "Facturacion" tambien aparece dentro de "Calendario\n    Facturacion", "Gestion Facturacion", "Liquidacion De Promedios Fuera De\n    Proceso De Facturacion", etc.). Con substring, _click_visible podia\n    clickear cualquiera de esos otros items en vez del nodo de menu\n    correcto.\n\n    Ademas recorre los candidatos en orden INVERSO (del ultimo al primero):\n    incluso con match exacto, una ruta con la misma etiqueta repetida en 2\n    niveles anidados (ej. PR000325 RF-05: Comercial > Facturacion >\n    Facturacion > Mantenedor De Contratistas) deja AMBOS "Facturacion"\n    visibles a la vez tras expandir el nivel 1 (el ancestro no se oculta\n    solo porque se revelo su hijo), y el ancestro aparece ANTES en el DOM\n    que el descendiente recien revelado. Devolver el primer visible volvia\n    a clickear el mismo ancestro (colapsando el menu) en vez de bajar de\n    nivel -bug real, confirmado en vivo: la ruta RF-05 nunca llegaba a\n    revelar \'Mantenedor De Contratistas\'."""\n    patron = re.compile(r"^\\s*" + re.escape(text) + r"\\s*$")\n    candidatos = page.locator("a").filter(has_text=patron)\n    for i in reversed(range(candidatos.count())):\n        candidato = candidatos.nth(i)\n        if candidato.is_visible():\n            candidato.click()\n            return\n    raise RuntimeError(f"No se encontro un enlace de menu visible con texto exacto: {text!r}")\n'

ABRIR_APLICACION_BLOCK = 'def abrir_aplicacion(page, ruta_menu, selector_pantalla, timeout_menu=30000, timeout_pantalla=20000, paso_excel=None):\n    """Navega Aplicaciones > ruta_menu[0] > ruta_menu[1] > ... (clic final\n    que abre el POPUP de la aplicacion), y espera a que selector_pantalla\n    (el componente Angular raiz de la pantalla, ej. "app-listado-de-x")\n    este listo dentro del iframe #aplicacion del popup.\n\n    Generalizacion de abrir_consulta_atenciones() (PR000335): la mecanica\n    de navegacion -menu lateral con arbol oculto, popup con iframe\n    #aplicacion- es la MISMA para cualquier aplicacion del portal Web LDS;\n    lo unico que cambia por proyecto es la ruta de menus a clickear y el\n    selector de la pantalla final. Ejemplo de uso (equivalente a PR000335):\n        app, frame = abrir_aplicacion(\n            page,\n            ["Comercial", "Atencion Integral Al Cliente", "Consulta De Atenciones Comerciales"],\n            "app-listado-de-atenciones",\n        )\n    Requiere _click_visible() y capturar_paso() ya definidos en el archivo.\n\n    `paso_excel` (opcional): numero del paso de "Pasos a seguir" del Excel\n    al que corresponde abrir la app (comun: el mismo paso 1 que cubre\n    "entrar a la plataforma" + "entrar a la aplicacion" juntos, cuando el\n    Excel no los separa). Sin esto, la captura "aplicacion_abierta" siempre\n    cae en la seccion generica "Otras capturas" del Word de evidencia en\n    vez de agruparse bajo el paso real - confirmado en vivo en PR000325\n    (59 de 62 casos con esta seccion vacia de contenido util)."""\n    page.get_by_role("link", name="  Aplicaciones").click(timeout=timeout_menu)\n    page.wait_for_timeout(500)\n    for texto in ruta_menu[:-1]:\n        _click_visible(page, texto)\n        page.wait_for_timeout(500)\n    with page.expect_popup() as popup_info:\n        _click_visible(page, ruta_menu[-1])\n    app = popup_info.value\n    app.wait_for_load_state("networkidle")\n    frame = app.locator("#aplicacion").content_frame\n    frame.locator(selector_pantalla).wait_for(timeout=timeout_pantalla)\n    capturar_paso(app, "aplicacion_abierta", paso_excel=paso_excel)\n    return app, frame\n'


# ===========================================================================
# Helpers de espera
# ===========================================================================
SELECCIONAR_PRIMERA_OPCION_BLOCK = 'def seleccionar_primera_opcion(select_locator, timeout_ms=8000):\n    """Selecciona la primera opcion real (distinta del placeholder\n    \'-- Seleccione --\') de un <select>. Los combos del modal Filtro Avanzado\n    cargan sus opciones de forma asincrona luego de abrirse (confirmado en\n    exploracion en vivo: hasta ~3s), por lo que se espera activamente hasta\n    timeout_ms antes de rendirse. Devuelve True si pudo seleccionar."""\n    plazo = time.monotonic() + timeout_ms / 1000\n    while True:\n        valores = [v for v in select_locator.locator("option").evaluate_all("els => els.map(e => e.value)") if v]\n        if valores:\n            select_locator.select_option(value=valores[0])\n            return True\n        if time.monotonic() >= plazo:\n            break\n        select_locator.page.wait_for_timeout(300)\n    print("  (aviso) el combo no tiene opciones cargadas; se omite la seleccion.")\n    return False\n'

SELECCIONAR_OPCION_POR_TEXTO_BLOCK = 'def seleccionar_opcion_por_texto(select_locator, patron, timeout_ms=8000):\n    """Selecciona la opcion de un <select> cuyo texto visible matchee\n    `patron` (un re.Pattern, ej. re.compile("Simple", re.I)).\n\n    OJO: select_option(label=patron) de Playwright NO acepta un re.Pattern\n    -su parametro `label` solo admite str o lista de str-; pasarle un\n    Pattern directamente compila pero falla recien en tiempo de ejecucion\n    con `TypeError: \'re.Pattern\' object is not iterable` (confirmado en\n    vivo: PR000325 CP022/CP023/CP024/CP031/CP032). Por eso se leen las\n    opciones del DOM y se matchea el texto a mano antes de seleccionar por\n    `value`. Los combos pueden cargar sus opciones de forma asincrona, por\n    lo que se espera activamente hasta timeout_ms antes de rendirse."""\n    plazo = time.monotonic() + timeout_ms / 1000\n    while True:\n        opciones = select_locator.locator("option").evaluate_all("els => els.map(e => ({value: e.value, texto: e.textContent}))")\n        for o in opciones:\n            if patron.search(o["texto"] or ""):\n                select_locator.select_option(value=o["value"])\n                return True\n        if time.monotonic() >= plazo:\n            break\n        select_locator.page.wait_for_timeout(300)\n    raise RuntimeError(f"No se encontro una opcion que matchee {patron.pattern!r} en el combo.")\n'

ESPERAR_FIN_CARGA_BLOCK = 'def esperar_fin_de_carga(app, pantalla, timeout_ms=45000):\n    """Espera a que termine de cargar una busqueda/accion antes de seguir\n    (y sobre todo, antes de tomar la captura de evidencia): el boton deja\n    de decir \'Cargando...\' y no queda actividad de red pendiente. Sin esto,\n    la captura final a veces salia a medio cargar (spinner + boton\n    \'Cargando...\' todavia visibles), como se detecto en la evidencia real\n    de CP002."""\n    try:\n        pantalla.get_by_role("button", name="Cargando...").wait_for(state="hidden", timeout=timeout_ms)\n    except PWTimeoutError:\n        pass\n    try:\n        app.wait_for_load_state("networkidle", timeout=10000)\n    except PWTimeoutError:\n        pass\n    app.wait_for_timeout(500)\n'

ESPERAR_ANIMACION_BLOCK = 'def esperar_animacion_estable(locator, timeout_ms=3000, intervalo_seg=0.15):\n    """Espera a que un elemento deje de moverse/cambiar de tamaño (fin de\n    una transicion/animacion CSS de entrada, ej. un modal apareciendo con\n    fade+slide) comparando su bounding box en dos instantes seguidos.\n    Sin esto, una captura tomada apenas el elemento se vuelve "visible"\n    puede salir a medio animar (confirmado con evidencia real: el dialogo\n    de Restriccion de Busqueda de CP001 salio descuadrado/fantasma)."""\n    plazo = time.monotonic() + timeout_ms / 1000\n    anterior = None\n    estable = 0\n    while time.monotonic() < plazo:\n        try:\n            actual = locator.bounding_box()\n        except Exception:\n            actual = None\n        if actual is not None and actual == anterior:\n            estable += 1\n            if estable >= 2:\n                return\n        else:\n            estable = 0\n        anterior = actual\n        locator.page.wait_for_timeout(int(intervalo_seg * 1000))\n'


# ===========================================================================
# Video: renombrar/unir .webm
# ===========================================================================
RENOMBRAR_VIDEO_BLOCK = 'def _renombrar_video(video, destino, intentos=8, espera_seg=0.5):\n    """Mueve/renombra el .webm que graba Playwright (nombre hash) al nombre\n    final del caso, y devuelve la ruta que quedo REALMENTE valida (destino\n    si se pudo renombrar, o el nombre-hash original si no se pudo) -nunca\n    None si el video existe- para que el caller pueda seguir usando ese\n    video (union con ffmpeg o guardado directo) aunque el renombre fallara.\n\n    En Windows el proceso de ffmpeg a veces suelta el archivo un instante\n    despues de que .path() ya lo devuelve, asi que se reintenta un par de\n    veces antes de avisar que no se pudo. BUG REAL confirmado en vivo\n    (PR000325, CP001, 10/09/2026): cuando los 8 intentos (4s) no alcanzan\n    -maquina bajo carga tras correr varios casos seguidos-, el codigo\n    anterior devolvia None y el caller SOLO revisaba si el archivo con el\n    nombre BONITO (destino) existia; como nunca se creo, el video de ESE\n    lado (portal o app) se descartaba en silencio -el caso seguia dando\n    [OK] pero el .webm final quedaba INCOMPLETO (solo la mitad de la\n    grabacion), sin ningun aviso salvo un print facil de pasar por alto\n    entre 62 casos. Ahora el caller usa la ruta que se devuelve aca\n    (renombrada o no) para la union/guardado, asi el video sigue completo\n    aunque el renombre en si haya fallado."""\n    origen = Path(video.path())\n    for intento in range(intentos):\n        try:\n            origen.replace(destino)\n            return destino\n        except (PermissionError, OSError):\n            if intento == intentos - 1:\n                print(f"  (aviso) no se pudo renombrar el video {origen.name} -> {destino.name} (se sigue usando con su nombre original para la union/guardado).")\n                return origen\n            time.sleep(espera_seg)\n\n\ndef _localizar_ffmpeg():\n    """Ubica un ffmpeg CON SOPORTE PARA \'concat\' (el demuxer que hace\n    falta para unir portal+aplicacion en un solo .webm). Primero un\n    ffmpeg "completo" instalado en el sistema (PATH); si no hay, prueba el\n    ffmpeg minimo que Playwright ya descarga para grabar (`playwright\n    install ffmpeg`) -pero ese build viene compilado con\n    --disable-everything y solo habilita a mano image2pipe/matroska/webm,\n    NUNCA concat (confirmado en vivo corriendo `ffmpeg -demuxers` sobre el\n    binario real: no aparece en absoluto)-. Devuelve None si NINGUNO\n    soporta concat, para que el caller se ahorre el intento (que si se\n    hace igual, ffmpeg no falla con un error prolijo: crashea con un\n    codigo de salida basura tipo 2880417800, dificil de diagnosticar en\n    medio de una corrida de 60+ casos)."""\n    def soporta_concat(ruta):\n        try:\n            r = subprocess.run([str(ruta), "-hide_banner", "-demuxers"], capture_output=True, text=True, timeout=10)\n            return "concat" in r.stdout\n        except Exception:\n            return False\n\n    de_sistema = shutil.which("ffmpeg")\n    if de_sistema and soporta_concat(de_sistema):\n        return Path(de_sistema)\n    # Ffmpeg portable dedicado, instalado a mano en la raiz AUTOMATIZACION_LDS\n    # (2 niveles arriba de cada CPxxx.py: AUTOMATIZACION_LDS\\\\PRxxxxxx\\\\CPxxx.py)\n    # - con soporte concat completo, a diferencia del build minimo que trae\n    # Playwright.\n    raiz_automatizacion = Path(__file__).resolve().parent.parent\n    for candidato_portable in (raiz_automatizacion / "ffmpeg" / "ffmpeg.exe", raiz_automatizacion / "ffmpeg" / "bin" / "ffmpeg.exe"):\n        if candidato_portable.is_file() and soporta_concat(candidato_portable):\n            return candidato_portable\n    base = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright"\n    if base.is_dir():\n        candidatos = sorted(base.glob("ffmpeg-*/ffmpeg-win64.exe"), reverse=True)\n        if candidatos and soporta_concat(candidatos[0]):\n            return candidatos[0]\n    return None\n\n\ndef _unir_videos(destino, *videos, timeout_seg=60):\n    """Concatena N .webm (portal + aplicacion + cualquier pagina extra\n    que Playwright haya grabado, ej. una pestana efimera abierta\n    durante una descarga) en un solo archivo con ffmpeg (stream copy,\n    sin recodificar: todos comparten resolucion/codec porque los graba\n    el mismo record_video_size). Si no encuentra un ffmpeg con soporte\n    \'concat\' o falla la union, no toca los archivos originales y\n    devuelve False para que el caller los deje como videos separados\n    (ver _localizar_ffmpeg: en una maquina sin ffmpeg completo en el\n    PATH, esto es la norma, no un error - instalar un ffmpeg "completo"\n    y agregarlo al PATH si se quiere un solo .webm por caso).\n\n    BUG REAL confirmado en vivo 22/09/2026 (PR000335-SP5, casos con\n    descarga real via expect_download): Chromium a veces abre una\n    pagina efimera adicional para servir la descarga, que Playwright\n    graba igual (record_video_dir aplica a TODO el contexto) pero\n    nunca queda referenciada por ninguna variable page/app del caller -\n    por eso la firma acepta *videos en vez de exactamente 2, para que\n    el caller pueda barrer y sumar cualquier page@*.webm huerfano que\n    haya quedado en la carpeta de evidencia antes de llamar a esta\n    funcion."""\n    videos = [v for v in videos if v is not None]\n    if len(videos) < 2:\n        return False\n    ffmpeg = _localizar_ffmpeg()\n    if not ffmpeg:\n        print("  (aviso) no hay un ffmpeg con soporte \'concat\' disponible (el de Playwright no lo trae); quedan los videos separados. Instalar ffmpeg completo y agregarlo al PATH para unirlos en uno solo.")\n        return False\n    lista = destino.parent / f"{destino.stem}_lista.txt"\n    lista.write_text("".join(f"file \'{v.name}\'\\n" for v in videos), encoding="utf-8")\n    try:\n        resultado = subprocess.run(\n            [str(ffmpeg), "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(destino)],\n            cwd=str(destino.parent),\n            capture_output=True,\n            text=True,\n            timeout=timeout_seg,\n        )\n        if resultado.returncode == 0 and destino.exists():\n            # La union en si ya funciono (destino existe y esta completo) -\n            # la limpieza de los originales es best-effort: si Windows\n            # todavia tiene el archivo bloqueado un instante despues de\n            # browser.close(), NO se debe reportar la union como fallida\n            # (bug real confirmado en vivo 17/09/2026: un WinError 32 aca\n            # tapaba un merge exitoso con el aviso "no se pudieron unir").\n            for video_origen in videos:\n                for intento_borrado in range(14):\n                    try:\n                        video_origen.unlink(missing_ok=True)\n                        break\n                    except (PermissionError, OSError) as e:\n                        if intento_borrado == 13:\n                            print(f"  (aviso) la union de videos funciono, pero no se pudo borrar {video_origen.name}: {e}")\n                        else:\n                            time.sleep(0.5)\n            return True\n        print(f"  (aviso) no se pudieron unir los videos (ffmpeg devolvio {resultado.returncode}); quedan separados.")\n        return False\n    except Exception as e:\n        print(f"  (aviso) no se pudieron unir los videos: {e}; quedan separados.")\n        return False\n    finally:\n        lista.unlink(missing_ok=True)\n'


# ===========================================================================
# Cursor visual para el video (JS)
# ===========================================================================
CURSOR_JS_FULL = '(() => {\n  if (window.__pwCursorInjected) return;\n  window.__pwCursorInjected = true;\n\n  const ES_TOP = window.top === window.self;\n\n  function estilizarBase(el, tam) {\n    el.style.position = \'fixed\';\n    el.style.width = tam + \'px\';\n    el.style.height = tam + \'px\';\n    el.style.borderRadius = \'50%\';\n    el.style.pointerEvents = \'none\';\n    el.style.zIndex = \'2147483647\';\n    el.style.transform = \'translate(-50%,-50%)\';\n  }\n\n  if (ES_TOP) {\n    // Documento de nivel superior (page o popup "app"): dibuja el cursor\n    // real. Recibe coordenadas propias (mousemove/mousedown locales) Y\n    // las reenviadas por iframes hijos via postMessage.\n    let cursorEl = null;\n    function asegurarCursor() {\n      if (!document.documentElement) return null;\n      if (!cursorEl) {\n        cursorEl = document.createElement(\'div\');\n        cursorEl.id = \'__pw_cursor\';\n        estilizarBase(cursorEl, 46);\n        cursorEl.style.background = \'rgba(255,0,0,.45)\';\n        cursorEl.style.border = \'5px solid rgba(220,0,0,.95)\';\n        cursorEl.style.boxShadow = \'0 0 14px 4px rgba(255,0,0,.65)\';\n        cursorEl.style.opacity = \'0\';\n        cursorEl.style.transition = \'left .35s ease, top .35s ease, opacity .2s ease\';\n        document.documentElement.appendChild(cursorEl);\n      }\n      return cursorEl;\n    }\n    function moverCursor(x, y) {\n      const el = asegurarCursor();\n      if (!el) return;\n      el.style.left = x + \'px\';\n      el.style.top = y + \'px\';\n      el.style.opacity = \'1\';\n    }\n    function ripple(x, y) {\n      if (!document.documentElement) return;\n      const r = document.createElement(\'div\');\n      estilizarBase(r, 24);\n      r.style.background = \'rgba(255,0,0,.6)\';\n      r.style.left = x + \'px\';\n      r.style.top = y + \'px\';\n      document.documentElement.appendChild(r);\n      const inicio = performance.now();\n      const duracionMs = 1400;\n      function paso(ahora) {\n        const t = Math.min(1, (ahora - inicio) / duracionMs);\n        const tam = 24 + t * (120 - 24);\n        r.style.width = tam + \'px\';\n        r.style.height = tam + \'px\';\n        r.style.opacity = String(0.95 * (1 - t));\n        if (t < 1) requestAnimationFrame(paso);\n        else r.remove();\n      }\n      requestAnimationFrame(paso);\n    }\n\n    document.addEventListener(\'mousemove\', (e) => moverCursor(e.clientX, e.clientY), true);\n    document.addEventListener(\'mousedown\', (e) => ripple(e.clientX, e.clientY), true);\n\n    window.addEventListener(\'message\', (ev) => {\n      const datos = ev.data;\n      if (!datos || datos.__pwCursor !== true) return;\n      let iframeOrigen = null;\n      for (const f of document.querySelectorAll(\'iframe\')) {\n        if (f.contentWindow === ev.source) { iframeOrigen = f; break; }\n      }\n      if (!iframeOrigen) return;\n      const rect = iframeOrigen.getBoundingClientRect();\n      const x = rect.left + datos.x;\n      const y = rect.top + datos.y;\n      if (datos.tipo === \'move\') moverCursor(x, y);\n      else if (datos.tipo === \'click\') ripple(x, y);\n    });\n  } else {\n    // Dentro de un iframe: position:fixed ahi queda acotado al viewport\n    // DEL IFRAME (no de la ventana completa), y ademas el grabador de\n    // video de Playwright no compone bien un overlay asi cuando el\n    // iframe es de otro origen (confirmado en vivo el 10/09/2026 con\n    // PR000325: el cursor SI se veia en captura de pantalla normal pero\n    // NUNCA en el video). Se reenvian las coordenadas al documento de\n    // nivel superior, que es quien realmente dibuja el cursor.\n    document.addEventListener(\'mousemove\', (e) => {\n      window.top.postMessage({ __pwCursor: true, tipo: \'move\', x: e.clientX, y: e.clientY }, \'*\');\n    }, true);\n    document.addEventListener(\'mousedown\', (e) => {\n      window.top.postMessage({ __pwCursor: true, tipo: \'click\', x: e.clientX, y: e.clientY }, \'*\');\n    }, true);\n  }\n})();\n'


# ===========================================================================
# Word de evidencia (.docx armado a mano con zipfile)
# ===========================================================================
WORD_HELPERS_FULL = '_EMU_POR_PULGADA = 914400\n_ANCHO_MAX_PULGADAS = 6.3\n\n\ndef _tamano_png(ruta):\n    """Lee ancho/alto (px) del header IHDR de un PNG, sin depender de Pillow."""\n    with open(ruta, "rb") as f:\n        data = f.read(33)\n    ancho, alto = struct.unpack(">II", data[16:24])\n    return ancho, alto\n\n\ndef _calcular_extent_emu(ancho_px, alto_px, dpi=96):\n    ancho_in = ancho_px / dpi\n    alto_in = alto_px / dpi\n    if ancho_in > _ANCHO_MAX_PULGADAS:\n        factor = _ANCHO_MAX_PULGADAS / ancho_in\n        ancho_in *= factor\n        alto_in *= factor\n    return int(ancho_in * _EMU_POR_PULGADA), int(alto_in * _EMU_POR_PULGADA)\n\n\ndef _etiqueta_paso_png(ruta_png):\n    """\'CP002_03_antes_de_buscar.png\' -> \'Paso 3: antes de buscar\'."""\n    base = ruta_png.stem\n    resto = base[len(CASO) + 1:] if base.startswith(CASO + "_") else base\n    m = re.match(r"^(\\d{2})_(.+)$", resto)\n    if m:\n        numero, desc = m.groups()\n        return f"Paso {int(numero)}: {desc.replace(\'_\', \' \')}"\n    if resto == "error":\n        return "Captura de error"\n    return resto.replace("_", " ")\n\n\n_DOCX_CONTENT_TYPES = (\n    \'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\'\n    \'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\'\n    \'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\'\n    \'<Default Extension="xml" ContentType="application/xml"/>\'\n    \'<Default Extension="png" ContentType="image/png"/>\'\n    \'<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\'\n    "</Types>"\n)\n\n_DOCX_RELS_RAIZ = (\n    \'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\'\n    \'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\'\n    \'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>\'\n    "</Relationships>"\n)\n\n_DOCX_NS = (\n    \'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" \'\n    \'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" \'\n    \'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" \'\n    \'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" \'\n    \'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"\'\n)\n\n\ndef _docx_parrafo(texto, estilo=None):\n    pPr = f\'<w:pPr><w:pStyle w:val="{estilo}"/></w:pPr>\' if estilo else ""\n    return f\'<w:p>{pPr}<w:r><w:t xml:space="preserve">{_escape_xml(texto)}</w:t></w:r></w:p>\'\n\n\ndef _docx_parrafo_imagen(indice, rid, nombre_media, cx, cy):\n    return (\n        "<w:p><w:r><w:drawing>"\n        f\'<wp:inline distT="0" distB="0" distL="0" distR="0">\'\n        f\'<wp:extent cx="{cx}" cy="{cy}"/>\'\n        \'<wp:effectExtent l="0" t="0" r="0" b="0"/>\'\n        f\'<wp:docPr id="{indice}" name="{_escape_xml(nombre_media)}"/>\'\n        "<a:graphic><a:graphicData uri=\\"http://schemas.openxmlformats.org/drawingml/2006/picture\\">"\n        "<pic:pic>"\n        f\'<pic:nvPicPr><pic:cNvPr id="{indice}" name="{_escape_xml(nombre_media)}"/><pic:cNvPicPr/></pic:nvPicPr>\'\n        f\'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>\'\n        f\'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>\'\n        \'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>\'\n        "</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>"\n    )\n\n\ndef _parsear_pasos_excel(texto_pasos):\n    """"1. Ingresar codigo nuevo.\\n2. Presionar Leer." -> {1: "1. Ingresar\n    codigo nuevo.", 2: "2. Presionar Leer."} - conserva la linea completa\n    (con el numero) como texto del encabezado, solo la indexa por numero."""\n    pasos = {}\n    for linea in texto_pasos.splitlines():\n        linea = linea.strip()\n        m = re.match(r"^(\\d+)\\.\\s*.+$", linea)\n        if m:\n            pasos[int(m.group(1))] = linea\n    return pasos\n\n\ndef generar_word_evidencia():\n    """Arma CASO_evidencia.docx con todas las capturas .png que ya existen\n    en EVIDENCIA. No depende de python-docx/lxml (arma el .docx a mano con\n    zipfile, libreria estandar) ni de ningun otro archivo del proyecto.\n    Pensado para revision FUNCIONAL (no tecnica): cada captura se agrupa\n    bajo el texto REAL del paso de la matriz Excel al que corresponde\n    (via CAPTURAS_POR_PASO_EXCEL, poblado por capturar_paso(...,\n    paso_excel=N) - ver CAPTURAR_PASO_CODE), en vez de listar el texto de\n    "Pasos a seguir" aparte y las capturas con una etiqueta tecnica\n    derivada del nombre de archivo. La ULTIMA captura tomada en el caso (ULTIMA_CAPTURA, actualizada por\n    capturar_paso() en cada llamada) se excluye SIEMPRE de su grupo por\n    paso numerico y se coloca junto a "Resultado esperado" al final del\n    documento, para que quien revisa el Word vea de forma inequivoca la\n    imagen que valida el resultado esperado. Las capturas sin\n    paso_excel asignado (no deberian existir si cada capturar_paso()\n    del caso pasa ese parametro) se incluyen igual, con su etiqueta\n    tecnica de siempre, sin agruparlas bajo un encabezado generico."""\n    pngs = sorted(EVIDENCIA.glob("*.png"))\n    if not pngs:\n        return\n    rels = []\n    medias = []\n    cuerpo = [_docx_parrafo(f"{CASO} - {NOMBRE_CASO}", "Title")]\n    cuerpo.append(_docx_parrafo(f"RF: {RF_CASO}  |  CU: {CU_CASO}"))\n    cuerpo.append(_docx_parrafo(f"Descripcion: {DESCRIPCION_CASO}"))\n\n    contador_imagen = [0]\n\n    def agregar_imagen(ruta_png):\n        contador_imagen[0] += 1\n        i = contador_imagen[0]\n        ancho_px, alto_px = _tamano_png(ruta_png)\n        cx, cy = _calcular_extent_emu(ancho_px, alto_px)\n        rid = f"rId{i + 1}"\n        nombre_media = f"image{i}.png"\n        rels.append(\n            f\'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{nombre_media}"/>\'\n        )\n        medias.append((f"word/media/{nombre_media}", ruta_png))\n        cuerpo.append(_docx_parrafo_imagen(i, rid, nombre_media, cx, cy))\n\n    pngs_por_nombre = {p.name: p for p in pngs}\n    usados = set()\n    nombre_ultima = ULTIMA_CAPTURA.get("nombre")\n\n    if CAPTURAS_POR_PASO_EXCEL:\n        textos_paso = _parsear_pasos_excel(PASOS_CASO)\n        for numero in sorted(CAPTURAS_POR_PASO_EXCEL):\n            nombres_paso = [n for n in CAPTURAS_POR_PASO_EXCEL[numero] if n != nombre_ultima]\n            if not nombres_paso:\n                continue\n            cuerpo.append(_docx_parrafo(textos_paso.get(numero, f"Paso {numero}"), "Heading2"))\n            for nombre_archivo in nombres_paso:\n                ruta_png = pngs_por_nombre.get(nombre_archivo)\n                if ruta_png is not None:\n                    agregar_imagen(ruta_png)\n                    usados.add(nombre_archivo)\n\n    pngs_restantes = [p for p in pngs if p.name not in usados and p.name != nombre_ultima and not p.name.endswith("_error.png")]\n    for ruta_png in pngs_restantes:\n        cuerpo.append(_docx_parrafo(_etiqueta_paso_png(ruta_png), "Heading2"))\n        agregar_imagen(ruta_png)\n        usados.add(ruta_png.name)\n\n    cuerpo.append(_docx_parrafo("Resultado esperado:", "Heading2"))\n    if nombre_ultima:\n        ruta_ultima = pngs_por_nombre.get(nombre_ultima)\n        if ruta_ultima is not None:\n            agregar_imagen(ruta_ultima)\n    cuerpo.append(_docx_parrafo(RESULTADO_ESPERADO_CASO))\n\n    document_xml = (\n        \'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\'\n        f"<w:document {_DOCX_NS}><w:body>"\n        + "".join(cuerpo)\n        + \'<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>\'\n        \'<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>\'\n        "</w:body></w:document>"\n    )\n    document_rels = (\n        \'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\'\n        \'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\'\n        + "".join(rels)\n        + "</Relationships>"\n    )\n\n    destino = EVIDENCIA / f"{CASO}_evidencia.docx"\n    try:\n        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:\n            z.writestr("[Content_Types].xml", _DOCX_CONTENT_TYPES)\n            z.writestr("_rels/.rels", _DOCX_RELS_RAIZ)\n            z.writestr("word/document.xml", document_xml)\n            z.writestr("word/_rels/document.xml.rels", document_rels)\n            for nombre_interno, ruta_png in medias:\n                z.write(ruta_png, nombre_interno)\n        print(f"  Word de evidencia: {destino.name} ({len(pngs)} captura(s))")\n    except Exception as e:\n        print(f"  (aviso) no se pudo generar el Word de evidencia: {e}")\n'


# ===========================================================================
# Changelog (agregar una linea aca cada vez que se mejora algo generico de
# este framework, para que quede rastro de que proyecto lo origino y por
# que -asi el proximo proyecto sabe si conviene regenerar sus CPxxx.py-)
# ===========================================================================
# 2026-09-09  PR000335  Version inicial: extraido de generate_scripts.py
#                        tras la corrida real de los 123 casos (110 OK,
#                        13 FALLO por bugs/datos de la app, no del
#                        framework). Incluye cursor visual + pausa antes
#                        de clic para que el video se entienda, agregados
#                        ese mismo dia a pedido del usuario.
# 2026-09-10  PR000325  Bug real en WORD_HELPERS_FULL: el valor traia un
#                        envoltorio "WORD_HELPERS_CODE = '''...'''" de mas
#                        (quedo asi al extraerlo de PR000335, nunca se
#                        habia probado de punta a punta). Al insertarse en
#                        un CPxxx.py generado, eso solo creaba una VARIABLE
#                        DE TEXTO con el codigo adentro -generar_word_evidencia()
#                        nunca quedaba definida como funcion real-, y
#                        cualquier CP fallaba con
#                        "NameError: name 'generar_word_evidencia' is not
#                        defined" al llegar al finally. Corregido: ahora
#                        WORD_HELPERS_FULL es directamente el codigo fuente
#                        (mismo criterio que el resto de los bloques de
#                        este archivo). Si algun proyecto anterior a esta
#                        fecha genero sus CPxxx.py con este framework,
#                        regenerarlos.
# 2026-09-10  PR000325  login() ahora reintenta hasta 2 veces el formulario
#                        completo. Confirmado en vivo (smoke test de
#                        PR000325, 3 casos): incluso esperando a que
#                        #servidor/#Dominios esten listos, el login puede
#                        fallar igual en el primer intento ("Ud. no tiene
#                        acceso a la empresa" con un usuario que SI tiene
#                        acceso) - mismo sintoma que documento PR000335,
#                        pero ahi nunca se automatizo el reintento. Firma
#                        de login() cambio de login(page) a
#                        login(page, reintentos=2) - compatible hacia atras
#                        (reintentos tiene default). Si un login fallo
#                        anterior a esta fecha necesitaba investigarse a
#                        mano, ya no hace falta: se reintenta solo.
# 2026-09-10  PR000325  3 bugs mas del mismo origen que el de
#                        WORD_HELPERS_FULL (doble-escape heredado de
#                        cuando estos bloques vivian anidados dentro de un
#                        wrapper de string que ya no existe):
#                        1) CLICK_VISIBLE_BLOCK: el RuntimeError de
#                           _click_visible() imprimia literal "{text!r}"
#                           en vez del texto real buscado.
#                        2) RENOMBRAR_VIDEO_BLOCK: el aviso de "no se pudo
#                           renombrar el video" tambien imprimia los
#                           placeholders literales sin interpolar.
#                        3) RENOMBRAR_VIDEO_BLOCK: _unir_videos() escribia
#                           el archivo de lista para ffmpeg con "\\n"
#                           (backslash+n literal) en vez de un salto de
#                           linea real, dejando las 2 lineas "file '...'"
#                           pegadas en una sola -> el demuxer concat de
#                           ffmpeg SIEMPRE fallaba al unir portal+app en
#                           un solo video, silenciosamente (quedaba el
#                           aviso "no se pudieron unir, quedan separados"
#                           como si fuera simplemente que no habia un
#                           ffmpeg completo instalado, cuando en realidad
#                           el archivo de lista que se le pasaba estaba
#                           mal armado). Los 3 corregidos, verificados
#                           contra el CP001.py real de PR000335 (fuente de
#                           verdad, nunca tuvo este bug porque no paso por
#                           esta capa de extraccion). Regenerar CPxxx.py
#                           de cualquier proyecto anterior a esta fecha
#                           que le interese la union real de videos.
# 2026-09-10  PR000325  Word de evidencia: se agrega el texto de "Pasos a
#                        seguir" de la matriz Excel (constante nueva
#                        PASOS_CASO, que cada CPxxx.py debe definir) justo
#                        despues de la Descripcion, y "Resultado esperado"
#                        se mueve al final del documento (cierre), en vez
#                        de ir los dos arriba de las capturas. Pensado
#                        para que el Word se lea en clave funcional/de
#                        negocio, no tecnica.
# 2026-09-10  PR000325  Cursor rojo del video: mas grande (26px -> 46px de
#                        diametro, borde 3px -> 5px) y el ripple de clic
#                        mas grande y duradero (70px/0.9s -> 120px/1.4s),
#                        para que se siga bien en el video incluso con
#                        SLOWMO alto. Transicion de movimiento .25s -> .35s.
# 2026-09-10  PR000325  BUG GRAVE en CURSOR_JS_FULL, mismo origen que el de
#                        WORD_HELPERS_FULL (envoltorio "VAR = r'''...'''"
#                        de mas) pero con impacto peor: ese texto se pasa
#                        tal cual a context.add_init_script(), que lo
#                        inyecta como JAVASCRIPT en el navegador - y
#                        "CURSOR_OVERLAY_JS = r'''...'''" no es JS valido
#                        (es sintaxis Python), asi que tiraba SyntaxError
#                        silencioso en cada pagina/iframe y el cursor rojo
#                        NUNCA se dibujo en NINGUN video generado con este
#                        framework hasta ahora. Se detecto recien al
#                        extraer frames con ffmpeg del video real de
#                        PR000325 y ver que el cursor no aparecia en
#                        ninguno (ni en el login, ni dentro del iframe de
#                        la app) pese a que las acciones (fill/click) si
#                        se ejecutaban bien. Corregido igual que
#                        WORD_HELPERS_FULL: CURSOR_JS_FULL ahora es
#                        directamente el JS (el IIFE), sin el envoltorio.
#                        Cualquier proyecto anterior a esta fecha que haya
#                        grabado video con este framework tiene videos SIN
#                        cursor visible - regenerar sus CPxxx.py.
# 2026-09-10  PR000325  Con el bug de arriba ya corregido, el cursor
#                        seguia sin verse DENTRO del iframe #aplicacion
#                        (que es justamente donde vive toda la pantalla
#                        de cada app). Causa: position:fixed dentro de un
#                        iframe queda acotado al VIEWPORT DEL IFRAME, no
#                        al de la ventana/popup completo, y ademas el
#                        video de Playwright no compone bien ese overlay
#                        cuando el iframe es de otro origen (el portal es
#                        pldsweb.luzdelsur.com.pe, la app real corre en
#                        tk0s-web.luzdelsur.com.pe - confirmado con
#                        getComputedStyle: el cursor SI existia con la
#                        posicion/opacity correctos dentro del iframe,
#                        pero nunca aparecia compuesto en el .webm).
#                        CURSOR_JS_FULL se reescribio: si el script corre
#                        en un documento de nivel superior (page o el
#                        popup "app"), dibuja el cursor el mismo, IGUAL
#                        que antes; si corre DENTRO de un iframe, en vez
#                        de dibujar nada ahi, reenvia las coordenadas del
#                        mouse (mousemove/mousedown) a window.top via
#                        postMessage, y window.top las traduce sumando el
#                        offset real del iframe (getBoundingClientRect())
#                        antes de mover SU PROPIO cursor. Tambien se dejo
#                        de depender de un <style>/@keyframes para el
#                        ripple (ahora se anima a mano con
#                        requestAnimationFrame) - no hacia falta para el
#                        bug pero es mas robusto ante paginas con CSP
#                        estricta de style-src. Verificado con
#                        page.screenshot() + extraccion de frames del
#                        .webm real: el cursor aparece en la posicion
#                        correcta sobre el campo clickeado dentro del
#                        iframe.
# 2026-09-10  PR000325  BUG REAL en CLICK_VISIBLE_BLOCK: filtraba enlaces
#                        de menu con page.locator("a").filter(has_text=texto)
#                        pasando un STRING - eso hace match por SUBSTRING,
#                        case-insensitive, no exacto. El menu lateral del
#                        portal renderiza TODO el arbol oculto de una vez, y
#                        con decenas de items reales, el texto buscado (ej.
#                        "Facturacion") aparecia como substring de varios
#                        otros ("Calendario Facturacion", "Gestion
#                        Facturacion", etc.) ademas del item exacto - el
#                        click podia terminar en cualquiera de esos. Ademas,
#                        cuando una ruta de menu repite la MISMA etiqueta en
#                        2 niveles anidados (confirmado en vivo, RF-05 de
#                        PR000325: Comercial > Facturacion > Facturacion >
#                        Mantenedor De Contratistas), el nivel 1 seguia
#                        visible tras expandirse, y devolver el primer
#                        visible volvia a clickear el ancestro (colapsando
#                        el menu) en vez de bajar de nivel - la ruta nunca
#                        llegaba al destino final. Corregido: (1) match
#                        EXACTO con regex ancla ^...$ en vez de substring, y
#                        (2) recorrer los candidatos visibles en orden
#                        INVERSO (el descendiente recien revelado por una
#                        etiqueta repetida queda despues del ancestro en el
#                        DOM). Verificado en vivo: los 10 casos de RF-05 que
#                        fallaban por esto (CP040-CP049) pasaron a OK tras
#                        el fix. Cualquier proyecto anterior a esta fecha
#                        que navegue rutas de menu con etiquetas repetidas o
#                        parecidas entre si deberia regenerar sus CPxxx.py.
# 2026-09-10  PR000325  Se agrega SELECCIONAR_OPCION_POR_TEXTO_BLOCK: Playwright
#                        select_option(label=...) SOLO acepta un str o una
#                        lista de str, NUNCA un re.Pattern - pasarle uno
#                        compila sin error pero falla en tiempo de ejecucion
#                        con "TypeError: 're.Pattern' object is not
#                        iterable" (confirmado en vivo: PR000325 CP022,
#                        CP023, CP024, CP031, CP032, los 5 usaban
#                        select_option(label=re.compile(...))). El nuevo
#                        helper seleccionar_opcion_por_texto(select_locator,
#                        patron) lee las opciones del DOM y matchea el texto
#                        a mano antes de seleccionar por value, con la misma
#                        espera activa que seleccionar_primera_opcion() para
#                        combos que cargan sus opciones de forma asincrona.
#                        Cablear en %%HELPERS_ESPERA%% junto a los otros dos
#                        helpers de espera al escribir un generate_scripts.py
#                        nuevo (ver NUEVO_PROYECTO_CHECKLIST.md).
# 2026-09-11  PR000325  LECCION (no un helper nuevo, es un gotcha de uso):
#                        get_by_label()/get_by_role(..., name=...) de
#                        Playwright tambien hacen match por SUBSTRING
#                        case-insensitive por defecto, igual que has_text.
#                        Confirmado en vivo: frame.get_by_label("Activa")
#                        fallaba con "strict mode violation: resolved to 3
#                        elements" porque el formulario real tenia 3 radios
#                        con label "Activa", "Reactiva" y "Activa H.P." (los
#                        3 contienen "Activa" como substring). Regla a
#                        seguir en TODO generate_scripts.py nuevo: si un
#                        texto de label/role puede ser substring de otro
#                        label real de la misma pantalla (nombres cortos,
#                        variantes con sufijo/prefijo), usar SIEMPRE
#                        get_by_label(texto, exact=True) / get_by_role(rol,
#                        name=texto, exact=True) - no asumir que el texto es
#                        unico solo porque lo parece en la matriz Excel o el
#                        EF. No se creo un helper para esto en el framework
#                        porque exact=True ya es la solucion nativa de
#                        Playwright; el punto es acordarse de usarlo.
# 2026-09-11  PR000325  BUG REAL en RENOMBRAR_VIDEO_BLOCK: _renombrar_video()
#                        devolvia None si los 8 reintentos (4s) no alcanzaban
#                        para renombrar el .webm (Windows a veces tarda en
#                        soltar el archivo tras browser.close()); el caller
#                        (en generate_scripts.py de cada proyecto) solo
#                        revisaba si el archivo con el NOMBRE BONITO existia,
#                        asi que ese video (portal o app) se descartaba EN
#                        SILENCIO - el .webm final quedaba con solo la mitad
#                        de la grabacion y el caso igual daba [OK] (confirmado
#                        en vivo: PR000325 CP001, corrida completa). Corregido:
#                        ahora devuelve la ruta que quedo REALMENTE valida
#                        (renombrada, o el nombre-hash original si el
#                        renombre fallo) - el caller debe usar esa ruta en
#                        vez de asumir el nombre bonito. Proyectos anteriores
#                        a esta fecha deben actualizar tambien su
#                        generate_scripts.py (bloque finally de main(), ver
#                        NUEVO_PROYECTO_CHECKLIST.md Paso 3) para usar el
#                        valor de retorno, no solo regenerar CPxxx.py.
#                        Ademas, _localizar_ffmpeg() ahora verifica que el
#                        ffmpeg encontrado soporte el demuxer 'concat' antes
#                        de intentarlo (el ffmpeg minimo que trae Playwright
#                        NO lo soporta - confirmado corriendo `ffmpeg
#                        -demuxers` sobre el binario real -, y sin esta
#                        deteccion la union crasheaba con un codigo de salida
#                        basura tipo 2880417800 en vez de un aviso claro).
# 2026-09-11  PR000325  LOGIN_BLOCK y ABRIR_APLICACION_BLOCK ahora aceptan un
#                        parametro opcional `paso_excel` (default None, sin
#                        cambio de comportamiento) que se pasa a
#                        capturar_paso(). Motivo: sin esto, las capturas de
#                        login y "aplicacion_abierta" SIEMPRE caian en la
#                        seccion generica "Otras capturas" del Word de
#                        evidencia en vez de agruparse bajo el paso real del
#                        Excel - confirmado en vivo en PR000325: 59 de 62
#                        casos tenian esa seccion vacia de contenido util
#                        porque su Excel dedica un unico Paso 1 a "entrar a
#                        la plataforma + abrir la app" y las 2 capturas
#                        quedaban sin ese numero. Cada proyecto debe revisar
#                        su propia convencion de numeracion de pasos (no es
#                        necesariamente uniforme - PR000325 tiene 1 caso,
#                        CP001, con una numeracion distinta al resto) y
#                        pasar `paso_excel=N` al llamar login()/
#                        abrir_aplicacion() (o a los wrappers abrir_rfXX())
#                        segun corresponda.
# 2026-09-15  PR000335-2  Cierre de Sprint 2 (98 casos, 80% OK en la
#                        corrida final) - 3 aportes genericos al pasar a
#                        otro proyecto:
#                        1) generar_reporte_excel.py ahora soporta un
#                           3er estado "NO OK" vs "Fallido" (antes todo lo
#                           que no era OK caia en un unico "Fallido"). Si
#                           existe casos_fallidos_confirmados.json junto al
#                           script (formato documentado en su propio
#                           docstring), los CP listados ahi se muestran
#                           como "Fallido" (defecto real confirmado EN VIVO,
#                           listo para Desarrollo) y el resto de los que no
#                           dieron OK caen en "NO OK" (sin confirmar
#                           todavia - puede ser bug de automatizacion).
#                           Retrocompatible: sin ese archivo, comportamiento
#                           equivalente al de antes (todo "NO OK").
#                        2) Nuevo sesion_manual_con_red.py: template
#                           reutilizable para reproducir defectos reales a
#                           mano (headed, con el usuario del proyecto
#                           manejando el navegador) mientras el script
#                           registra en vivo (con flush) toda respuesta
#                           HTTP >= 400 de la pestana principal Y de
#                           cualquier popup nuevo. Nacio porque un caso de
#                           PR000335-2 (guardar en "Modificar") fallaba en
#                           silencio sin ningun error visible en el DOM -
#                           sin ver la red no habia forma de saber si era
#                           bug de automatizacion o la app rechazando el
#                           guardado (era esto ultimo: 400 Acceso Denegado).
#                        3) Varios gotchas nuevos en NUEVO_PROYECTO_CHECKLIST.md
#                           Seccion 3 (buscar con Enter y esperar la carga
#                           en vez de solo fill(), esperar tras expandir
#                           secciones colapsables antes de chequear
#                           visibilidad, filas "fantasma" vacias en grillas
#                           que rompen un chequeo ingenuo de count()==0,
#                           escopear botones de accion POR FILA a la fila
#                           seleccionada en vez de a toda la pantalla,
#                           popups internos sin el wrapper #aplicacion,
#                           filtros de fecha por defecto que devuelven 0
#                           resultados, y dialogos con varias grillas bajo
#                           un mismo trigger). Sin cambios de codigo en
#                           web_lds_core.py esta vez - son patrones de como
#                           ESCRIBIR generate_scripts.py, no del framework
#                           en si.
# 2026-09-17  PR000325-SP3  3 aportes genericos tras cerrar 76/78 OK:
#                        1) _localizar_ffmpeg() ahora tambien busca un
#                           ffmpeg portable dedicado en
#                           AUTOMATIZACION_LDS\ffmpeg\ffmpeg.exe (o
#                           \ffmpeg\bin\ffmpeg.exe), 2 niveles arriba de
#                           cualquier CPxxx.py, ANTES de caer al build
#                           minimo que trae Playwright (que nunca soporta
#                           el demuxer 'concat', confirmado corriendo
#                           `ffmpeg -demuxers` sobre ese binario - por eso
#                           hasta ahora TODO proyecto sin un ffmpeg
#                           "completo" en el PATH del sistema terminaba
#                           con 2 .webm separados por caso en vez de uno
#                           solo). Se instalo ese build portable
#                           (ffmpeg-release-essentials de gyan.dev) en la
#                           raiz AUTOMATIZACION_LDS - no hace falta nada
#                           mas por proyecto.
#                        2) Bug real en _unir_videos(): cuando la union
#                           SI funcionaba pero Windows todavia tenia el
#                           .webm original bloqueado un instante despues
#                           de browser.close(), el WinError 32 del
#                           unlink() posterior se reportaba como si la
#                           UNION hubiera fallado ("no se pudieron unir
#                           los videos") - engañoso, el .webm final ya
#                           estaba completo y correcto. Se separo la
#                           limpieza de los originales (best-effort, con
#                           4 reintentos de 0.5s) del resultado real de
#                           la union.
#                        3) Nuevo patron _CASO_OK en el main() de cada
#                           CPxxx.py (ver NUEVO_PROYECTO_CHECKLIST.md
#                           Seccion 3): video/Word solo se arman si el
#                           caso termino OK - un caso NO OK ya deja su
#                           _error.png + su entrada en
#                           reportes\logs\CPxxx.log para seguimiento, asi
#                           que no vale la pena gastar tiempo/espacio en
#                           video/Word de un flujo que no llego a
#                           completarse. Vive en el HEADER_TEMPLATE de
#                           generate_scripts.py de cada proyecto (no en
#                           este archivo), pero se anota aca porque es la
#                           decision que motivo los 2 fixes de arriba.
#                           run_all.py subio su default de --slowmo de 0
#                           a 2000ms de paso, para que el video se vea
#                           bien sin correr de golpe sin tener que
#                           pedirlo cada vez.
# 2026-09-22  PR000335-SP5  Bug real en _unir_videos(): casos que disparan
#                        una descarga real (app.expect_download(), ej.
#                        boton "Exportar") a veces dejan una pestana
#                        efimera adicional que Chromium abre para servir
#                        el archivo - Playwright la graba igual
#                        (record_video_dir aplica a TODO el contexto) pero
#                        esa pagina nunca queda referenciada por `page` ni
#                        `app`, asi que su video quedaba huerfano en la
#                        carpeta de evidencia (page@<hash>.webm suelto,
#                        nunca renombrado ni unido) pese a que el caso
#                        daba [OK]. Confirmado en vivo en 4 casos de golpe
#                        (CP015/CP016/CP074/CP075) - cualquier caso con
#                        descarga real tiene este gotcha, no es puntual de
#                        un caso. _unir_videos(video1, video2, destino)
#                        cambio de firma a _unir_videos(destino, *videos) -
#                        el caller ahora barre EVIDENCIA/page@*.webm antes
#                        de llamarla y suma cualquier huerfano a la lista,
#                        asi terminan TODOS en el mismo .webm final sin
#                        importar cuantas paginas abrio el caso. El caller
#                        (finally: de cada CPxxx.py) vive en el
#                        HEADER_TEMPLATE de generate_scripts.py de cada
#                        proyecto, no en este archivo - hay que actualizar
#                        esa parte tambien en cada proyecto que ya tenga
#                        sus CPxxx.py generados antes de esta fecha.
# 2026-10-06  PR000349-SP4  Dos fixes reales encontrados corrigiendo CP012
#                        a pedido del usuario (Word con captura de login
#                        huerfana al final + 2 videos en vez de 1):
#                        (1) RENOMBRAR_VIDEO_BLOCK/_unir_videos: el loop de
#                        borrado del .webm original tras la union solo
#                        reintentaba 4 veces (~2s) - en esta VM (antivirus
#                        corporativo Trend Micro Apex One escaneando el
#                        .webm recien creado) eso no alcanza y el archivo
#                        queda bloqueado bastante mas tiempo (confirmado
#                        en vivo: file lock liberado solo, varios minutos
#                        despues). Subido a 14 intentos (~7s) - mitiga la
#                        mayoria de los casos sin frenar corridas grandes,
#                        pero NO elimina el problema de raiz (requiere que
#                        IT excluya la carpeta del proyecto en la consola
#                        de Apex One - el usuario no puede hacerlo solo,
#                        a diferencia de Windows Defender). Ver gotcha #10
#                        en feedback_gotchas_playwright_web_lds (memoria).
#                        (2) HEADER_TEMPLATE de cada proyecto (no vive en
#                        este archivo, hay que corregirlo por proyecto):
#                        `login(page)` se llamaba SIN paso_excel, asi que
#                        esa captura nunca se agrupaba bajo el paso real y
#                        terminaba en la seccion de "pngs_restantes" con
#                        etiqueta tecnica derivada del nombre de archivo
#                        ("Paso 1: login"), renderizada DESPUES de los
#                        pasos numerados por paso_excel (confirmado:
#                        aparecia despues de "Paso 2" en el Word, pese a
#                        ser logicamente el primer paso). Fix: llamar
#                        `login(page, paso_excel=1)` (mismo paso que
#                        `abrir_rfXX(page, paso_excel=1)`). Ademas,
#                        `rutas_videos.extend(sorted(EVIDENCIA.glob(
#                        "page@*.webm")))` sumaba de nuevo el MISMO
#                        archivo que `_renombrar_video` ya habia devuelto
#                        como fallback (cuando el rename fallaba), asi que
#                        el video del portal quedaba DUPLICADO en la lista
#                        de union - fix: filtrar el glob con `if p not in
#                        rutas_videos`. Ambos fixes aplicados en
#                        PR000349-SP4/generate_scripts.py; PENDIENTE
#                        propagar a los demas proyectos de esta sesion
#                        (PR000325-SP7, PR000326-SP2, etc.) y al
#                        HEADER_TEMPLATE de ejemplo en
#                        NUEVO_PROYECTO_CHECKLIST.md.
