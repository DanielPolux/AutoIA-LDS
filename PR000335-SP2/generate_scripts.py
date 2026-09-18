"""
generate_scripts.py (PR000335-2 - Atencion al Cliente / Cortes Programados /
Instalacion Programada por Norma / Listado de Atenciones, Sprint 2)

Fuente de verdad: genera los 98 CPxxx.py (CP001..CP098) a partir de
matriz_casos.json + el framework compartido _framework/web_lds_core.py.

*** ESTADO: PARCIALMENTE CONFIRMADO EN VIVO el 13/09/2026 (ver abajo). ***
Escrito primero 100% a partir de Documentos/EF_texto.txt y ET_texto.txt
mientras la ruta de menu de Sprint 2 (Tecnico > ... > "Registro De
Atencion"/"Listado Atenciones") daba un error de servidor .NET
(assembly LuzDelSur.Tecnico.CalAteCom.MATF.Atencion.Entity incompleto -
ver memoria "pr000335-2-registro-atencion-error-servidor.md"). El MISMO
DIA se encontro que la ruta ORIGINAL de PR000335 Sprint 1 SIGUE
funcionando y de hecho ya apunta a la pantalla NUEVA de este sprint:

    Aplicaciones > Comercial > Atencion Integral Al Cliente >
    Atenciones A Clientes > Consulta De Atenciones Comerciales

(el primer intento de probar esta ruta fallo por un bug propio: uso
matching por substring en vez de exacto - `_click_visible` real usa
regex ancla exacta - y una `t` de acento mal codificada; con el
mecanismo real SI carga, ver _exploracion/validar_atenciones_a_clientes.py
y dump_atencion_cliente_real.py). Esta pantalla es RF-01 "Atencion al
Cliente" real y funcional: se confirmaron en vivo casi todos los ids de
campo (ver CAMPO_ID abajo, calcan el EF), el boton de busqueda real
(`button.matf-btn-buscar-tipo`, NO un boton con texto "Buscar"), los
checkboxes reales (`SinNombre`, `sinApellido` -singular-, `sinTelefono`,
`sinCorreo`, `sinDocumento`), el combo "Tipo" (`#tipo`) y el combo
"Origen" (`#origenA`, DISTINTO de "Tipo" - contiene B-FACEBOOK,
C-CARTA, ..., K-DENUNCIAS TK, ... - asi que CP017/018 usan `#origenA`,
no `#tipo`), y el disparador real de "Cortes Programados": un
`<img title="Cortes Programados">` oculto hasta expandir la seccion
"Inf. Tecnica" del sidebar, que al hacer click abre un dialog real
(`role=dialog`, componente `<app-alert>`) - confirmado con el mensaje
EXACTO "No se encontraron cortes programados" (CP046) usando el
suministro 1045027. La "Instalaciones en Medidor x Control Calidad"
del EF tiene un tooltip real DISTINTO: "Mediciones programadas por
norma" (`<img title="Mediciones programadas por norma">`, minusc./mayus.
inconsistente en el propio HTML) - el comportamiento de ESE icono
todavia no se hizo click en vivo, sigue marcado SIN CONFIRMAR.

Las rutas de RF-04 (Listado de Atenciones con acciones Agregar/
Consultar/Modificar/Eliminar) NO se pudieron re-verificar todavia bajo
esta ruta corregida - `abrir_listado_atenciones` sigue apuntando a la
ruta de Tecnico que dio error de assembly; falta confirmar si esa
funcionalidad vive DENTRO de esta misma pantalla (ej. como listado
previo) o en otro lugar. Revisar esto sigue siendo el proximo paso.

Convenciones que SIGUEN sin confirmar en vivo (todo lo que no se lista
arriba): el modal "Informacion de Contacto", los botones Aceptar/
Cancelar del registro de llamada, la grilla Pedidos, y toda la logica
de RF-04. Se mantienen con locators semanticos (get_by_label/get_by_role/
get_by_text) con el texto EXACTO del EF como mejor apuesta disponible.
  - Varias reglas del ET (RANGO_CORTE, nivel de tension B/M, dedup de
    incidencias, tipo de incidencia) viven en tablas de Informix
    (matf_parametros, sgi_programa) y German no son verificables solo con
    UI/Playwright - esos casos (CP059-062) dejan un `print("[AVISO] ...")`
    documentando que hace falta una consulta a base de datos aparte.
  - Varios casos (CP046, CP050, CP054, CP057, CP058, CP061, CP063, CP069,
    CP070, CP075, CP095, etc.) necesitan un suministro/atencion con datos
    MUY especificos (sin cortes, con varios periodos, fuera del MAC,
    Alumbrado Publico, etc.) que no se pueden inventar sin explorar en
    vivo - quedan con un codigo de ejemplo + comentario "TODO SIN
    CONFIRMAR" pidiendo el dato real, siguiendo el mismo patron con el que
    se resolvieron los casos de datos especificos de PR000325 (CP059/CP060
    de ese proyecto, ver rf06-copiar-asignaciones.md).
  - CP097 necesita un SEGUNDO usuario con perfil distinto al de
    DCABA_DW - no definido todavia, el caso deja evidencia de un solo
    perfil y avisa que falta el segundo.

Antes de dar estos 98 casos por definitivos: seguir el Paso 2 de
NUEVO_PROYECTO_CHECKLIST.md (exploracion en vivo) apenas LDS levante el
ambiente, y revisar caso por caso contra el HTML real - iterando igual
que se hizo con PR000325 (58/62 con datos reales confirmados via
correcciones sucesivas).
"""
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT_DIR.parent.parent.parent / "AUTOMATIZACION_LDS" / "_framework"))
import web_lds_core as core  # noqa: E402

PROYECTO = "PR000335-2"  # debe coincidir con el nombre de esta carpeta
MATRIZ = json.loads((OUT_DIR / "matriz_casos.json").read_text(encoding="utf-8"))

ENV_TOGGLES = core.ENV_TOGGLES_CODE.replace("__PROYECTO__", PROYECTO)

# ===========================================================================
# Helpers propios de PR000335-2 (no genericos del portal -> no van en
# _framework). NINGUNO confirmado en vivo (ver docstring del modulo).
# ===========================================================================
PR000335_2_HELPERS = '''
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
    frame.get_by_text(re.compile("Informaci(o|\\u00f3)n adicional del contacto", re.IGNORECASE)).click()
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
PASSWORD = "Melquisedec_01"  # mismo usuario/clave que PR000325 - confirmado en vivo el 14/09/2026: es el usuario del propio tester, unico necesario para este proyecto (reemplaza a JOBLIT_DW por indicacion explicita)

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

# --- Navegacion: RF-01/02/03 CONFIRMADA en vivo el 13/09/2026 (ruta Y
#     selector_pantalla, ver dump_atencion_cliente_real.py). RF-04 sigue
#     apuntando a la ruta vieja de Tecnico que dio error de assembly -
#     pendiente de re-verificar si esa funcionalidad vive DENTRO de esta
#     misma pantalla (ver docstring del modulo). ---
RUTA_MENU_ATENCIONES = ["Comercial", "Atenci\\u00f3n Integral Al Cliente", "Atenciones A Clientes", "Consulta De Atenciones Comerciales"]


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
            # BUG REAL confirmado en vivo (CP087, 13/09/2026): la consola de
            # Windows usa cp1252 por default, y el mensaje de una excepcion
            # real a veces trae un caracter fuera de ese charset (ej. un
            # glifo de icono capturado sin querer por un locator de texto
            # generico) - un print() directo TAPABA el error real con un
            # UnicodeEncodeError nuevo. Se sanea antes de imprimir.
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
                    # BUG REAL confirmado en vivo (CP042, 13/09/2026): Windows a
                    # veces todavia tiene el .webm abierto en este punto (mismo
                    # motivo por el que _renombrar_video ya reintenta) - sin este
                    # try/except, la excepcion se disparaba DENTRO del finally y
                    # TAPABA el resultado real del caso (uno que habia terminado
                    # OK quedaba marcado FALLO solo por esto). Se deja el video
                    # con su nombre original en vez de perder el resultado real.
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
        f'*** SELECTORES SIN CONFIRMAR EN VIVO *** (ambiente caido al\n'
        f'13/09/2026, ver memoria pr000335-2-registro-atencion-error-servidor.md\n'
        f'y el docstring de generate_scripts.py) - revisar contra el HTML real\n'
        f'apenas el ambiente este arriba, siguiendo el Paso 2 del checklist.\n\n'
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
     .replace("%%HELPERS_PROPIOS%%", PR000335_2_HELPERS.strip("\n"))


CASES = []


def add(cp, abrir_fn, body):
    m = MATRIZ[cp]
    CASES.append(dict(
        cp=cp, rf=m["rf"], cu=m["cu"], name=m["name"], desc=m["desc"],
        precond=m["precond"], datos=m["datos"], esperado=m["esperado"],
        pasos=m["pasos"], abrir_fn=abrir_fn, body=body,
    ))


# ===========================================================================
# RF-01 - Atencion al Cliente (CP001-CP042, CP076-CP088, CP096-CP098)
# App: "Registro De Atencion". NADA confirmado en vivo (ver docstring).
# ===========================================================================

# --- CP001-CP006: secciones visibles segun "Tipo" ---
# Titulos CONFIRMADOS EN VIVO el 13/09/2026 (dump_atencion_real.html +
# dump_con_busqueda.html, todos con class="barraTitulo"): DIFIEREN del
# texto literal del EF en 2 de los 4 - "Información de la Atención"
# (SIN "Telefónica") e "Información de Cliente" (SIN el "l" de "del").
# "Información del Contacto" y "Registro de Pedidos" SI calcan el EF.
# "Información de SST" sigue sin confirmar (no se probo tipo SST en vivo).
TODAS_LAS_SECCIONES = [
    "Información de la Atención",
    "Información del Contacto",
    "Información de Cliente",
    "Información de SST",
    "Registro de Pedidos",
]

SECCIONES_POR_TIPO = {
    "SUMINISTRO": ["Información de la Atención", "Información del Contacto", "Información de Cliente", "Registro de Pedidos"],
    "SUMINISTRO NUEVO": ["Información de la Atención", "Información del Contacto", "Información de Cliente", "Registro de Pedidos"],
    "FNL": ["Información de la Atención", "Información del Contacto", "Registro de Pedidos"],
    "SAS": ["Información de la Atención", "Información del Contacto", "Registro de Pedidos"],
    "SST": ["Información de la Atención", "Información del Contacto", "Información de SST", "Registro de Pedidos"],
    "SST CON SUMINISTRO": ["Información de la Atención", "Información del Contacto", "Información de SST", "Registro de Pedidos"],
}


def _cuerpo_secciones(tipo):
    esperadas = SECCIONES_POR_TIPO[tipo]
    no_esperadas = [s for s in TODAS_LAS_SECCIONES if s not in esperadas]
    asserts_si = "\n".join(f'assert {s!r} in secciones, "Falta la seccion {s}"' for s in esperadas)
    asserts_no = "\n".join(f'assert {s!r} not in secciones, "No deberia aparecer la seccion {s}"' for s in no_esperadas)
    return f'''
seleccionar_tipo(frame, {tipo!r})
capturar_paso(app, "tipo_seleccionado", paso_excel=4)
secciones = secciones_visibles(frame)
capturar_paso(app, "secciones_visibles", paso_excel=5)
print("Secciones visibles:", secciones)
{asserts_si}
{asserts_no}
'''


for _cp, _tipo in [("CP001", "SUMINISTRO"), ("CP002", "SUMINISTRO NUEVO"), ("CP003", "FNL"),
                    ("CP004", "SAS"), ("CP005", "SST"), ("CP006", "SST CON SUMINISTRO")]:
    add(_cp, "abrir_atencion_cliente", _cuerpo_secciones(_tipo))


# --- CP007-CP016: busqueda de informacion del cliente por tipo ---
# Codigos y campo a verificar CONFIRMADOS EN VIVO el 14/09/2026 - el
# campo depende del tipo: SUMINISTRO/SUMINISTRO NUEVO autocompletan
# "Informacion de Cliente" (#nombreC); SST/SST CON SUMINISTRO NO tienen
# esa seccion - autocompletan "Informacion de SST" en su lugar (#cliente).
CODIGO_VALIDO_POR_TIPO = {
    "SUMINISTRO": "1045027",
    "SUMINISTRO NUEVO": "1045027",  # mismo codigo, confirmado en vivo que tambien autocompleta con este tipo
    "SST": "990001",  # confirmado en vivo el 14/09/2026 con el usuario (se busca con Enter, no con el boton)
    "SST CON SUMINISTRO": "2074382",  # CONFIRMADO EN VIVO el 14/09/2026: suministro real con 1 solicitud SST asociada (Nro Solicitud 3295197, cliente "URETA DE GAMERO BILMA ROSALIND") - dispara el dialogo "Seleccionar SST por suministro" (ver buscar_por_codigo). El codigo 990001 (reutilizado de SST) y el 3295197 (que en realidad es un Nro de Solicitud, no de suministro) NO sirven para este tipo.
}
CAMPO_VALIDACION_POR_TIPO = {
    "SUMINISTRO": "#nombreC",
    "SUMINISTRO NUEVO": "#nombreC",
    "SST": "#cliente",
    "SST CON SUMINISTRO": "#cliente",
}
CODIGO_INVALIDO = "0000000000"


def _cuerpo_busqueda_valida(tipo, codigo):
    campo_verificar = CAMPO_VALIDACION_POR_TIPO[tipo]
    return f'''
seleccionar_tipo(frame, {tipo!r})
capturar_paso(app, "tipo_seleccionado", paso_excel=4)
buscar_por_codigo(app, frame, {codigo!r})
esperar_fin_de_carga(app, frame)
capturar_paso(app, "antes_de_verificar_autocompletado", paso_excel=6)
assert (frame.locator({campo_verificar!r}).input_value() or "").strip(), "Se esperaba que la informacion se autocompletara tras la busqueda (campo {campo_verificar})"
capturar_paso(app, "informacion_autocompletada", paso_excel=7)
'''


def _cuerpo_busqueda_invalida(tipo, codigo):
    campo_verificar = CAMPO_VALIDACION_POR_TIPO[tipo]
    return f'''
seleccionar_tipo(frame, {tipo!r})
capturar_paso(app, "tipo_seleccionado", paso_excel=4)
buscar_por_codigo(app, frame, {codigo!r})
# CONFIRMADO EN VIVO el 14/09/2026: un codigo invalido NO deja un spinner
# colgado - muestra un dialogo real, pero el TEXTO varia por tipo: para
# SUMINISTRO es "El Cliente no se encuentra registrado actualmente."; para
# SST es "El numero de SST ingresado no es valido." (distinto titulo
# tambien: "Error" vs "Atencion"); para SST CON SUMINISTRO (confirmado
# en vivo con los codigos 0000000000 y 3295197) es "El numero de
# suministro ingresado no tiene una solicitud asociada." - se acepta
# cualquiera de los 3 patrones conocidos.
dialogo = frame.get_by_role("dialog")
expect(dialogo).to_be_visible(timeout=8000)
texto_dialogo = dialogo.inner_text()
assert "no se encuentra" in texto_dialogo.lower() or "no es v\\u00e1lido" in texto_dialogo.lower() or "no valido" in texto_dialogo.lower() or "no tiene" in texto_dialogo.lower(), f"Se esperaba un mensaje de codigo/cliente invalido, se vio: {{texto_dialogo!r}}"
capturar_paso(app, "mensaje_error_verificado", paso_excel=6)
dialogo.get_by_role("button", name="Aceptar").click()
expect(dialogo).to_be_hidden(timeout=5000)
assert (frame.locator({campo_verificar!r}).input_value() or "").strip() == "", "No se esperaba que la informacion se completara con un codigo invalido (campo {campo_verificar})"
capturar_paso(app, "flujo_no_continua", paso_excel=7)
'''


def _cuerpo_busqueda_no_aplica(tipo):
    return f'''
seleccionar_tipo(frame, {tipo!r})
capturar_paso(app, "tipo_seleccionado", paso_excel=4)
# SIN CONFIRMAR EN VIVO: se verifica que no se ofrezca la accion de
# busqueda (boton "Buscar") para este tipo.
boton_buscar = frame.get_by_role("button", name="Buscar")
assert boton_buscar.count() == 0 or not boton_buscar.first.is_visible(), "No se esperaba poder buscar informacion del cliente para el tipo {tipo}"
capturar_paso(app, "busqueda_no_disponible", paso_excel=5)
'''


for _cp, _tipo in [("CP007", "SUMINISTRO"), ("CP009", "SUMINISTRO NUEVO"), ("CP011", "SST"), ("CP013", "SST CON SUMINISTRO")]:
    add(_cp, "abrir_atencion_cliente", _cuerpo_busqueda_valida(_tipo, CODIGO_VALIDO_POR_TIPO[_tipo]))

for _cp, _tipo in [("CP008", "SUMINISTRO"), ("CP010", "SUMINISTRO NUEVO"), ("CP012", "SST"), ("CP014", "SST CON SUMINISTRO")]:
    add(_cp, "abrir_atencion_cliente", _cuerpo_busqueda_invalida(_tipo, CODIGO_INVALIDO))

for _cp, _tipo in [("CP015", "FNL"), ("CP016", "SAS")]:
    add(_cp, "abrir_atencion_cliente", _cuerpo_busqueda_no_aplica(_tipo))


# --- CP017-CP018: campo Solicitud TK segun "Origen" (CONFIRMADO EN VIVO
# que "tipo origen" del EF = combo #origenA, DISTINTO de "Tipo" - ver
# seleccionar_origen()) ---
add("CP017", "abrir_atencion_cliente", '''
seleccionar_origen(frame, "K - DENUNCIAS TK")
capturar_paso(app, "origen_seleccionado", paso_excel=4)
campo_tk = frame.get_by_label("Solicitud TK")
expect(campo_tk).to_be_visible(timeout=8000)
assert campo_tk.is_enabled(), "Solicitud TK deberia estar habilitado con Origen K - DENUNCIAS TK"
capturar_paso(app, "solicitud_tk_visible", paso_excel=5)
''')

add("CP018", "abrir_atencion_cliente", '''
seleccionar_origen(frame, "V - VENTANILLA")  # valor real distinto de K - DENUNCIAS TK, confirmado en vivo como opcion visible del combo #origenA
capturar_paso(app, "origen_seleccionado", paso_excel=4)
campo_tk = frame.get_by_label("Solicitud TK")
assert campo_tk.count() == 0 or not campo_tk.first.is_visible(), "Solicitud TK no deberia mostrarse con un Origen distinto de K - DENUNCIAS TK"
capturar_paso(app, "solicitud_tk_oculto", paso_excel=5)
''')


# --- CP019-CP027: checkboxes "Sin X" inhabilitan y limpian ---
CHECKBOX_INHABILITA_CASOS = [
    ("CP019", "Sin Nombre", ["Nombre"]),
    ("CP021", "Sin Apellidos", ["Apellido Paterno", "Apellido Materno"]),
    ("CP023", "Sin Telefono", ["Telefono Fijo", "Movil"]),
    ("CP025", "Sin Correo", ["Correo Electronico"]),
]


def _cuerpo_checkbox_inhabilita(etiqueta_check, campos):
    llenados = "\n".join(f'campo(frame, {c!r}).fill("PRUEBA")' for c in campos)
    verif = "\n".join(
        f'assert not campo(frame, {c!r}).is_enabled(), "{c} deberia quedar inhabilitado tras marcar {etiqueta_check}"\n'
        f'assert (campo(frame, {c!r}).input_value() or "") == "", "{c} deberia quedar vacio tras marcar {etiqueta_check}"'
        for c in campos
    )
    return f'''
{llenados}
capturar_paso(app, "campos_completados", paso_excel=4)
marcar_checkbox(frame, {etiqueta_check!r})
capturar_paso(app, "checkbox_marcada", paso_excel=5)
{verif}
capturar_paso(app, "campos_inhabilitados_y_vacios", paso_excel=6)
'''


for _cp, _etq, _campos in CHECKBOX_INHABILITA_CASOS:
    add(_cp, "abrir_atencion_cliente", _cuerpo_checkbox_inhabilita(_etq, _campos))


add("CP027", "abrir_atencion_cliente", '''
frame.locator("#tipoDocumento").select_option(index=1)
campo(frame, "Numero de Documento").fill("12345678")
capturar_paso(app, "documento_completado", paso_excel=4)
marcar_checkbox(frame, "Sin Documento")
capturar_paso(app, "sin_documento_marcada", paso_excel=5)
tipo_doc_texto = frame.locator("#tipoDocumento").locator("option:checked").inner_text()
assert "NINGUNO" in tipo_doc_texto.upper(), "Tipo Documento deberia quedar en NINGUNO"
assert (campo(frame, "Numero de Documento").input_value() or "") == "", "Numero de Documento deberia quedar vacio"
capturar_paso(app, "tipo_documento_ninguno", paso_excel=6)
''')


# --- CP020, CP022, CP024, CP026: checkboxes "Sin X" rehabilitan al desmarcar ---
CHECKBOX_REHABILITA_CASOS = [
    ("CP020", "Sin Nombre", ["Nombre"]),
    ("CP022", "Sin Apellidos", ["Apellido Paterno", "Apellido Materno"]),
    ("CP024", "Sin Telefono", ["Telefono Fijo", "Movil"]),
    ("CP026", "Sin Correo", ["Correo Electronico"]),
]


def _cuerpo_checkbox_rehabilita(etiqueta_check, campos):
    verif = "\n".join(f'assert campo(frame, {c!r}).is_enabled(), "{c} deberia quedar habilitado tras desmarcar {etiqueta_check}"' for c in campos)
    return f'''
marcar_checkbox(frame, {etiqueta_check!r})
capturar_paso(app, "checkbox_marcada", paso_excel=4)
desmarcar_checkbox(frame, {etiqueta_check!r})
capturar_paso(app, "checkbox_desmarcada", paso_excel=5)
{verif}
capturar_paso(app, "campos_rehabilitados", paso_excel=6)
'''


for _cp, _etq, _campos in CHECKBOX_REHABILITA_CASOS:
    add(_cp, "abrir_atencion_cliente", _cuerpo_checkbox_rehabilita(_etq, _campos))


# --- CP028-CP030: validacion de formato del correo ---
add("CP028", "abrir_atencion_cliente", '''
campo(frame, "Correo Electronico").fill("correo_invalido@")
capturar_paso(app, "correo_invalido_ingresado", paso_excel=4)
mensaje_formato = frame.get_by_text(re.compile("formato", re.IGNORECASE))
expect(mensaje_formato.first).to_be_visible(timeout=5000)
capturar_paso(app, "mensaje_formato_visible", paso_excel=5)
marcar_checkbox(frame, "Sin Correo")
capturar_paso(app, "sin_correo_marcada", paso_excel=6)
assert mensaje_formato.count() == 0 or not mensaje_formato.first.is_visible(), "El mensaje de formato invalido deberia desaparecer al marcar Sin Correo"
capturar_paso(app, "mensaje_formato_desaparecido", paso_excel=7)
''')

add("CP029", "abrir_atencion_cliente", '''
campo(frame, "Correo Electronico").fill("prueba@")
capturar_paso(app, "correo_parcial_invalido", paso_excel=4)
mensaje_formato = frame.get_by_text(re.compile("formato", re.IGNORECASE))
expect(mensaje_formato.first).to_be_visible(timeout=5000)
capturar_paso(app, "mensaje_formato_en_tiempo_real", paso_excel=5)
''')

add("CP030", "abrir_atencion_cliente", '''
campo(frame, "Correo Electronico").fill("prueba@luzdelsur.com.pe")
capturar_paso(app, "correo_valido_ingresado", paso_excel=4)
mensaje_formato = frame.get_by_text(re.compile("formato", re.IGNORECASE))
assert mensaje_formato.count() == 0 or not mensaje_formato.first.is_visible(), "No deberia mostrarse mensaje de formato invalido con un correo valido"
capturar_paso(app, "sin_mensaje_de_error", paso_excel=5)
''')


# --- CP031-CP033: modal "Informacion de Contacto" ---
# (helper abrir_modal_informacion_contacto ahora vive en PR000335_2_HELPERS
# -mas abajo en este archivo- para que quede DENTRO de cada CPxxx.py
# generado; un def suelto aca en generate_scripts.py solo existe en
# tiempo de generacion, nunca en el archivo final - BUG REAL propio,
# confirmado en vivo el 13/09/2026 con CP031: NameError en runtime.)

add("CP031", "abrir_atencion_cliente", '''
abrir_modal_informacion_contacto(frame)
capturar_paso(app, "modal_abierto", paso_excel=4)
modal = frame.get_by_role("dialog")
modal.get_by_label("Nombre").fill("CONTACTO PRUEBA")
capturar_paso(app, "datos_modal_ingresados", paso_excel=5)
modal.get_by_role("button", name="Aceptar").click()
capturar_paso(app, "modal_aceptado", paso_excel=6)
assert campo(frame, "Nombre").input_value() == "CONTACTO PRUEBA", "El valor ingresado en el modal deberia reflejarse en Informacion del Contacto"
capturar_paso(app, "datos_reflejados", paso_excel=7)
''')

add("CP032", "abrir_atencion_cliente", '''
valor_previo = campo(frame, "Nombre").input_value()
abrir_modal_informacion_contacto(frame)
capturar_paso(app, "modal_abierto", paso_excel=4)
modal = frame.get_by_role("dialog")
modal.get_by_label("Nombre").fill("CAMBIO QUE NO DEBE APLICARSE")
capturar_paso(app, "datos_modal_modificados", paso_excel=5)
modal.get_by_role("button", name="Cancelar").click()
capturar_paso(app, "modal_cancelado", paso_excel=6)
assert campo(frame, "Nombre").input_value() == valor_previo, "Cancelar el modal no deberia aplicar cambios a la vista principal"
capturar_paso(app, "valores_previos_conservados", paso_excel=7)
''')

add("CP033", "abrir_atencion_cliente", '''
valor_previo = campo(frame, "Nombre").input_value()
abrir_modal_informacion_contacto(frame)
capturar_paso(app, "modal_abierto", paso_excel=4)
modal = frame.get_by_role("dialog")
modal.get_by_label("Nombre").fill("CAMBIO SIN CONFIRMAR")
capturar_paso(app, "modal_modificado_sin_confirmar", paso_excel=5)
assert campo(frame, "Nombre").input_value() == valor_previo, "Mientras el modal esta abierto sin confirmar, la vista principal no deberia reflejar el cambio"
capturar_paso(app, "vista_principal_sin_cambios", paso_excel=6)
''')


# --- CP034-CP036: grilla Pedidos bloqueada/habilitada segun Informacion del Contacto ---
add("CP034", "abrir_atencion_cliente", '''
# Informacion del Contacto se deja SIN completar (formulario recien abierto).
grilla_pedidos = frame.get_by_role("table").last  # SIN CONFIRMAR: asume que la grilla Pedidos es la ultima tabla de la pantalla
fila = grilla_pedidos.locator("tbody tr").first
capturar_paso(app, "antes_de_intentar_editar", paso_excel=5)
celda = fila.locator("td").first
try:
    celda.click()
    editable = celda.locator("input, select").count() > 0 and celda.locator("input, select").first.is_enabled()
except Exception:
    editable = False
assert not editable, "La grilla Pedidos no deberia admitir edicion sin Informacion del Contacto completa"
capturar_paso(app, "edicion_no_habilitada", paso_excel=6)
''')

add("CP035", "abrir_atencion_cliente", '''
grilla_pedidos = frame.get_by_role("table").last
fila = grilla_pedidos.locator("tbody tr").first
lista = fila.locator("select").first
casilla = fila.locator("input[type=checkbox]").first
capturar_paso(app, "antes_de_intentar_modificar", paso_excel=5)
lista_bloqueada = (not lista.is_enabled()) if lista.count() else True
casilla_bloqueada = (not casilla.is_enabled()) if casilla.count() else True
assert lista_bloqueada, "La lista desplegable de Pedidos no deberia admitir cambios sin Informacion del Contacto"
assert casilla_bloqueada, "La casilla de Pedidos no deberia admitir cambios sin Informacion del Contacto"
capturar_paso(app, "listas_y_casillas_bloqueadas", paso_excel=6)
''')

add("CP036", "abrir_atencion_cliente", '''
completar_informacion_contacto_minima(frame)
capturar_paso(app, "informacion_contacto_completada", paso_excel=4)
grilla_pedidos = frame.get_by_role("table").last
fila = grilla_pedidos.locator("tbody tr").first
lista = fila.locator("select").first
assert lista.count() == 0 or lista.is_enabled(), "La grilla Pedidos deberia admitir edicion tras completar Informacion del Contacto"
capturar_paso(app, "grilla_pedidos_habilitada", paso_excel=5)
''')


# --- CP037-CP039: registro de la llamada ---
add("CP037", "abrir_atencion_cliente", '''
completar_informacion_contacto_minima(frame)
capturar_paso(app, "informacion_contacto_completada", paso_excel=4)
completar_pedido_minimo(frame)
capturar_paso(app, "pedido_registrado", paso_excel=5)
frame.get_by_role("button", name="Aceptar").click()
capturar_paso(app, "antes_de_verificar_registro", paso_excel=6)
confirmacion = frame.get_by_text(re.compile("registr", re.IGNORECASE))
expect(confirmacion.first).to_be_visible(timeout=8000)
capturar_paso(app, "atencion_registrada", paso_excel=7)
''')

add("CP038", "abrir_atencion_cliente", '''
completar_informacion_contacto_minima(frame)
capturar_paso(app, "informacion_contacto_completada", paso_excel=4)
completar_pedido_minimo(frame)
capturar_paso(app, "pedido_registrado", paso_excel=5)
# Se abandona la vista SIN presionar Aceptar. SIN CONFIRMAR EN VIVO: falta
# el paso de reabrir el Listado de Atenciones para comprobar que no quedo
# ningun registro nuevo (cruza con RF-04) - pendiente de definir una vez
# el ambiente este arriba.
capturar_paso(app, "vista_abandonada_sin_aceptar", paso_excel=6)
''')

add("CP039", "abrir_atencion_cliente", '''
capturar_paso(app, "antes_de_revisar_botones", paso_excel=4)
todos_los_botones = [b.inner_text().strip() for b in frame.locator("button").all() if b.is_visible()]
capturar_paso(app, "botones_revisados", paso_excel=5)
assert "Aceptar" in todos_los_botones, "Se esperaba el boton Aceptar"
assert "Cancelar" in todos_los_botones, "Se esperaba el boton Cancelar"
otros_esperables = {"Ingresar", "Modificar", "Eliminar", "Buscar", "Consultar", "Agregar"}
extras = [b for b in todos_los_botones if b not in ("Aceptar", "Cancelar") and b in otros_esperables]
assert not extras, f"No deberian ofrecerse otros botones de la version de escritorio en el registro de la llamada: {extras}"
''')


# --- CP040-CP042: cancelar atencion (CU-02) ---
add("CP040", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "1045027")
capturar_paso(app, "atencion_en_curso", paso_excel=4)
frame.get_by_role("button", name="Cancelar").click()
capturar_paso(app, "antes_de_confirmar_cancelacion", paso_excel=5)
dialogo = frame.get_by_role("dialog")
texto_dialogo = dialogo.inner_text()
assert "no se ha grabado" in texto_dialogo.lower(), "Se esperaba la advertencia de datos no grabados"
assert "esta seguro" in texto_dialogo.lower() and "cancelar" in texto_dialogo.lower(), "Se esperaba la pregunta de confirmacion de cancelar la atencion"
capturar_paso(app, "texto_advertencia_verificado", paso_excel=6)
dialogo.get_by_role("button", name=re.compile("^S(i|\\u00ed)$")).click()
capturar_paso(app, "cancelacion_confirmada", paso_excel=7)
assert (campo(frame, "Nombre").input_value() or "") == "", "La pantalla deberia quedar lista para una nueva atencion (Nombre vacio)"
capturar_paso(app, "pantalla_lista_para_nueva_atencion", paso_excel=8)
''')

add("CP041", "abrir_atencion_cliente", '''
campo(frame, "Nombre").fill("CONTACTO A DESCARTAR")
capturar_paso(app, "datos_capturados", paso_excel=4)
frame.get_by_role("button", name="Cancelar").click()
dialogo = frame.get_by_role("dialog")
dialogo.get_by_role("button", name=re.compile("^S(i|\\u00ed)$")).click()
capturar_paso(app, "cancelado", paso_excel=5)
assert (campo(frame, "Nombre").input_value() or "") == "", "La interfaz deberia quedar limpia tras cancelar"
capturar_paso(app, "interfaz_limpia", paso_excel=6)
''')

add("CP042", "abrir_listado_atenciones", '''
# NOTA: el precond de este caso en la matriz dice "aplicacion Atencion al
# Cliente", pero la accion que registra usuario/fecha (Eliminar) vive en
# el Listado de Atenciones (RF-04), no en el detalle de RF-01 - el boton
# Cancelar del detalle solo descarta el formulario (ver EF 12.1.8 y CP042
# en el propio texto de la matriz). Se usa abrir_listado_atenciones.
pantalla = frame.locator("app-listado-de-atenciones")
seleccionar_primera_fila(pantalla)
capturar_paso(app, "atencion_seleccionada", paso_excel=4)
accion_listado(pantalla, "Eliminar").click()
capturar_paso(app, "antes_de_confirmar_eliminar", paso_excel=5)
dialogo = frame.get_by_role("dialog")
dialogo.get_by_role("button", name=re.compile("^S(i|\\u00ed)$")).click()
capturar_paso(app, "atencion_eliminada", paso_excel=6)
# SIN CONFIRMAR EN VIVO: falta ubicar donde se expone el usuario/fecha de
# eliminacion (columna oculta, tooltip, detalle) - a determinar una vez
# el ambiente este arriba.
capturar_paso(app, "verificar_usuario_y_fecha_eliminacion", paso_excel=7)
''')


# --- CP076-CP086: maxlength de campos ---
CAMPOS_MAXLENGTH = [
    ("CP076", "Nombre", 15),
    ("CP077", "Apellido Paterno", 15),
    ("CP078", "Apellido Materno", 15),
    ("CP079", "Correo Electronico", 70),
    ("CP080", "Numero de Documento", 11),
    ("CP081", "Referencia de la Direccion de Atencion", 250),
    ("CP082", "Referencia", 250),
    ("CP083", "Telefono Fijo", 7),
    ("CP084", "Movil", 9),
    ("CP085", "Anotacion", 200),
    ("CP086", "Motivo", 100),
]


# CONFIRMADO EN VIVO el 13/09/2026 (corrida real de CP002-CP098):
# - "Referencia de la Direccion de Atencion" (direcionA) es READONLY por
#   defecto en esta pantalla (se autocompleta al buscar un suministro,
#   ver CP001-CP016) - el fill() directo del EF nunca aplica aca. Puede
#   que el EF describa un estado/tipo distinto (ej. sin suministro
#   asociado) donde si sea editable - sin confirmar todavia.
# - "Anotacion" (txtAnot) y "Motivo" (txtMotivo) NO aparecen en el DOM de
#   la pantalla principal en absoluto (0 matches en dump_con_busqueda.html)
#   - probablemente viven dentro de un modal/fila de detalle de un
#     pedido ya agregado a "Registro de Pedidos", no confirmado todavia.
_CAMPOS_MAXLENGTH_PROBLEMATICOS = {
    "Referencia de la Direccion de Atencion": "CONFIRMADO EN VIVO: este campo es READONLY en esta pantalla (se autocompleta al buscar un suministro) - no se puede probar el maxlength con un fill() directo aqui.",
    "Anotacion": "El campo Anotacion (id txtAnot) no aparece en el DOM de la pantalla principal - probablemente vive en el detalle de un pedido ya agregado, sin confirmar todavia.",
    "Motivo": "El campo Motivo (id txtMotivo) no aparece en el DOM de la pantalla principal - probablemente vive en el detalle de un pedido ya agregado, sin confirmar todavia.",
}


def _cuerpo_maxlength(etiqueta, longitud):
    aviso = _CAMPOS_MAXLENGTH_PROBLEMATICOS.get(etiqueta)
    if aviso:
        return f'''
print("[AVISO] {aviso}")
capturar_paso(app, "campo_no_disponible_para_esta_prueba", paso_excel=5)
'''
    return f'''
valor_excedido = "9" * {longitud + 5}
c = campo(frame, {etiqueta!r})
c.fill(valor_excedido)
capturar_paso(app, "valor_excedido_ingresado", paso_excel=5)
valor_final = c.input_value() or ""
capturar_paso(app, "longitud_verificada", paso_excel=6)
assert len(valor_final) <= {longitud}, "El campo {etiqueta} deberia truncar en {longitud} caracteres, quedo con " + str(len(valor_final))
'''


for _cp, _etq, _len in CAMPOS_MAXLENGTH:
    add(_cp, "abrir_atencion_cliente", _cuerpo_maxlength(_etq, _len))


# --- CP087-CP088: longitud de documento segun tipo ---
add("CP087", "abrir_atencion_cliente", '''
# BUG REAL confirmado en vivo (CP087, 14/09/2026): el locator original
# buscaba el DIGITO de la longitud exigida (ej. "8") como texto, pero el
# mensaje real del sistema escribe el numero en letras ("El numero de
# DNI no puede tener menos de ocho digitos.") - ese regex de digito solo
# matcheaba opciones OCULTAS de un combo de motivos que por coincidencia
# arrancan con "8 - ...", nunca el mensaje real (confirmado con
# investigar_cp087_longitud_doc.py: 24 matches, ninguno visible, en
# ambos estados). Se usa en cambio el contenedor real del campo
# (.matf-contacto-doc, confirmado en vivo) + su .text-danger: el
# parrafo de error se agrega/quita del DOM con *ngIf (no solo se oculta
# con CSS), asi que count()==0 ya alcanza para confirmar que desaparecio.
CASOS_DOC = [("DNI", 8), ("RUC", 11), ("CARNET EXTRANJERIA", 9)]
contenedor_doc = frame.locator("#dni").locator("xpath=ancestor::*[contains(@class,'matf-contacto-doc')][1]")
mensaje_error = contenedor_doc.locator(".text-danger")
for tipo_doc, longitud in CASOS_DOC:
    frame.locator("#tipoDocumento").select_option(label=tipo_doc)
    campo_doc = campo(frame, "Numero de Documento")
    campo_doc.fill("1" * (longitud - 1))
    campo_doc.press("Tab")
    capturar_paso(app, f"doc_corto_{tipo_doc.replace(' ', '_')}", paso_excel=4)
    expect(mensaje_error.first).to_be_visible(timeout=5000)
    campo_doc.fill("1" * longitud)
    campo_doc.press("Tab")
    capturar_paso(app, f"doc_correcto_{tipo_doc.replace(' ', '_')}", paso_excel=6)
    assert mensaje_error.count() == 0, f"El error de longitud deberia desaparecer con {longitud} digitos para {tipo_doc}"
''')

add("CP088", "abrir_atencion_cliente", '''
CASOS_DOC = [("DNI", 8), ("RUC", 11), ("CARNET EXTRANJERIA", 9)]
mensajes = {}
for tipo_doc, longitud in CASOS_DOC:
    frame.locator("#tipoDocumento").select_option(label=tipo_doc)
    campo_doc = campo(frame, "Numero de Documento")
    campo_doc.fill("1" * (longitud - 1))
    campo_doc.press("Tab")
    mensajes[(tipo_doc, "defecto")] = frame.get_by_text(re.compile(tipo_doc, re.IGNORECASE)).first.inner_text()
    capturar_paso(app, f"mensaje_defecto_{tipo_doc.replace(' ', '_')}", paso_excel=4)
    campo_doc.fill("1" * (longitud + 1))
    campo_doc.press("Tab")
    mensajes[(tipo_doc, "exceso")] = frame.get_by_text(re.compile(tipo_doc, re.IGNORECASE)).first.inner_text()
    capturar_paso(app, f"mensaje_exceso_{tipo_doc.replace(' ', '_')}", paso_excel=6)
for (tipo_doc, sentido), texto in mensajes.items():
    assert tipo_doc.split()[0].lower() in texto.lower(), f"El mensaje deberia nombrar el tipo de documento {tipo_doc!r}: {texto!r}"
print("Mensajes recolectados:", mensajes)
''')


# --- CP096-CP098: reglas del ET (CargarDatosIniciales) ---
add("CP096", "abrir_atencion_cliente", '''
capturar_paso(app, "vista_abierta", paso_excel=4)
opciones_medio_recepcion = frame.get_by_label(re.compile("Medio de Recepci(o|\\u00f3)n", re.IGNORECASE)).locator("option").all_inner_texts()
capturar_paso(app, "opciones_medio_recepcion", paso_excel=5)
assert not any("11" in o for o in opciones_medio_recepcion), "El medio de recepcion con ID 11 no deberia ofrecerse fuera de WebApp"
print("[AVISO] Este caso asume que la sesion actual NO es WebApp; confirmar en vivo el contexto real desde el que corre DCABA_DW.")
''')

add("CP097", "abrir_atencion_cliente", '''
accesos_usuario = [b.inner_text().strip() for b in frame.locator("button").all() if b.is_visible()]
capturar_paso(app, "accesos_usuario_actual", paso_excel=5)
print("Accesos visibles para DCABA_DW:", accesos_usuario)
print("[AVISO] CP097 requiere un SEGUNDO usuario con perfil distinto para comparar accesos - no definido todavia, queda pendiente de acordar con el usuario del proyecto.")
''')

add("CP098", "abrir_atencion_cliente", '''
capturar_paso(app, "vista_recien_abierta", paso_excel=4)
# CONFIRMADO EN VIVO el 13/09/2026: "Relación" (id=relacion) y "Distrito"
# (id=distritoB) SI son combos reales de esta pantalla y llegan poblados.
# "Tipo Identificación", "Casos Críticos" y "Tipos de Pedido" no se
# lograron ubicar via get_by_label (0 opciones = get_by_label no
# encontro nada, no que el combo este vacio) - probablemente no tienen
# <label> asociado o su etiqueta real es otra; quedan como aviso en vez
# de una falla ciega.
for id_combo, nombre in [("relacion", "Relación"), ("distritoB", "Distrito")]:
    opciones = frame.locator(f"#{id_combo}").locator("option").count()
    capturar_paso(app, f"combo_{id_combo}", paso_excel=5)
    assert opciones > 1, f"El combo {nombre!r} deberia llegar poblado por CargarDatosIniciales (tiene {opciones} opciones)"
print("[AVISO] 'Tipo Identificación', 'Casos Críticos' y 'Tipos de Pedido' no se pudieron ubicar con certeza en esta corrida - revisar sus ids reales en vivo.")
''')


# ===========================================================================
# RF-02 - Cortes Programados (CP043-CP050, CP059-CP062)
# App: "Registro De Atencion" (modal). NADA confirmado en vivo.
# ===========================================================================
add("CP043", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "204850")  # CONFIRMADO EN VIVO el 15/09/2026: suministro real CON corte programado (dato provisto por el usuario del proyecto)
capturar_paso(app, "suministro_ingresado", paso_excel=5)
abrir_cortes_programados(app, frame)
capturar_paso(app, "antes_de_verificar_modal", paso_excel=6)
modal = modal_cortes(frame)
expect(modal).to_be_visible(timeout=8000)
assert modal.locator("table").count() > 0, "Se esperaba una grilla de cortes dentro del modal"
capturar_paso(app, "grilla_cortes_visible", paso_excel=7)
''')

add("CP044", "abrir_atencion_cliente", '''
expandir_inf_tecnica(frame)  # el icono queda oculto hasta expandir esta seccion (confirmado en vivo)
icono_cortes = frame.locator('img[title="Cortes Programados"]')
# CORREGIDO tras corrida real (14/09/2026): dos causas combinadas.
# 1) #tipo arranca ya en "SUMINISTRO" por defecto - volver a
#    "seleccionarlo" con select_option no dispara (change) de Angular si
#    el valor no cambia realmente, y el icono queda con el estado viejo.
#    Se fuerza un cambio real antes de arrancar el recorrido.
# 2) seleccionar_tipo() no espera nada tras el select_option - Angular
#    tarda un instante en re-renderizar el icono segun el tipo, asi que
#    hace falta una espera corta despues de CADA cambio antes de leer
#    is_visible() (confirmado en vivo: con esta espera, SUMINISTRO SI
#    aparece visible como corresponde).
seleccionar_tipo(frame, "SST")
app.wait_for_timeout(500)
TIPOS = ["SUMINISTRO", "SUMINISTRO NUEVO", "FNL", "SAS", "SST", "SST CON SUMINISTRO"]
OCULTO_EN = {"SST", "SST CON SUMINISTRO"}
for tipo in TIPOS:
    seleccionar_tipo(frame, tipo)
    app.wait_for_timeout(500)
    visible = icono_cortes.count() > 0 and icono_cortes.first.is_visible()
    capturar_paso(app, f"icono_cortes_{tipo.replace(' ', '_')}", paso_excel=4)
    if tipo in OCULTO_EN:
        assert not visible, f"El icono de Cortes Programados no deberia ofrecerse con tipo {tipo}"
    else:
        assert visible, f"El icono de Cortes Programados deberia ofrecerse con tipo {tipo}"
capturar_paso(app, "recorrido_de_tipos_completo", paso_excel=5)
# CORREGIDO tras corrida real: con tipo FNL el campo Suministro/SST NO
# EXISTE en el DOM (confirmado: count()==0 - FNL nunca tiene busqueda de
# suministro, ver CP015). Al accionar el icono sin poder cargar un
# suministro, la app muestra el MISMO mensaje "Por favor ingrese un
# numero de Suministro" que CP045 - NO es un "silencio total" como se
# penso originalmente, pero el resultado practico es el mismo: nunca
# llega a abrir la grilla real de cortes.
seleccionar_tipo(frame, "SST")  # forzar cambio real antes de ir a FNL
app.wait_for_timeout(500)
seleccionar_tipo(frame, "FNL")
app.wait_for_timeout(500)
icono_cortes.click()
capturar_paso(app, "boton_accionado_con_tipo_distinto", paso_excel=6)
modal = frame.get_by_role("dialog")
expect(modal).to_be_visible(timeout=8000)
assert modal.locator("table").count() == 0, "No deberia abrirse la grilla real de cortes con un tipo distinto de SUMINISTRO"
capturar_paso(app, "sin_grilla_de_cortes", paso_excel=7)
modal.get_by_role("button", name="Aceptar").click()
''')

add("CP045", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
capturar_paso(app, "suministro_vacio", paso_excel=5)
abrir_cortes_programados(app, frame)
capturar_paso(app, "antes_de_verificar_mensaje", paso_excel=6)
mensaje = frame.get_by_text("Por favor ingrese un n\\u00famero de Suministro")
expect(mensaje).to_be_visible(timeout=8000)
capturar_paso(app, "mensaje_verificado", paso_excel=7)
''')

add("CP046", "abrir_atencion_cliente", '''
# CONFIRMADO EN VIVO el 13/09/2026: el suministro 1045027 no tiene cortes
# asociados y dispara exactamente este flujo (mensaje literal verificado).
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "1045027")
capturar_paso(app, "suministro_sin_cortes", paso_excel=5)
abrir_cortes_programados(app, frame)
capturar_paso(app, "antes_de_verificar_mensaje", paso_excel=6)
modal = frame.get_by_role("dialog")
mensaje = frame.get_by_text("No se encontraron cortes programados")
expect(mensaje).to_be_visible(timeout=8000)
assert not modal.count() or not modal.first.locator("table").count(), "No deberia abrirse el modal con grilla cuando no hay cortes"
capturar_paso(app, "mensaje_sin_registros", paso_excel=7)
''')

add("CP047", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "204850")  # CONFIRMADO EN VIVO el 15/09/2026: suministro real CON corte programado
abrir_cortes_programados(app, frame)
modal = modal_cortes(frame)
expect(modal).to_be_visible(timeout=8000)
capturar_paso(app, "modal_cortes_abierto", paso_excel=4)
assert modal.locator("table").count() > 0, "Este suministro no tiene grilla de cortes que probar - reemplazar por uno con cortes reales"
celda = modal.locator("table tbody tr").first.locator("td").first
try:
    celda.dblclick()
    editable = celda.locator("input, select").count() > 0
except Exception:
    editable = False
assert not editable, "La grilla de cortes programados deberia ser de solo lectura"
capturar_paso(app, "grilla_no_editable", paso_excel=5)
''')

add("CP048", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "204850")  # CONFIRMADO EN VIVO el 15/09/2026: suministro real CON corte programado
abrir_cortes_programados(app, frame)
modal = modal_cortes(frame)
expect(modal).to_be_visible(timeout=8000)
capturar_paso(app, "modal_cortes_abierto", paso_excel=4)
assert modal.locator("table").count() > 0, "Este suministro no tiene grilla de cortes que probar - reemplazar por uno con cortes reales"
celdas_fecha = modal.locator("table tbody tr td").filter(has_text=re.compile(r"\\d{2}/\\d{2}/\\d{4}")).all_inner_texts()
fechas_ordenables = []
for texto in celdas_fecha:
    m = re.search(r"(\\d{2})/(\\d{2})/(\\d{4})", texto)
    if m:
        dd, mm, yyyy = m.groups()
        fechas_ordenables.append((yyyy, mm, dd))
capturar_paso(app, "fechas_extraidas", paso_excel=5)
assert fechas_ordenables == sorted(fechas_ordenables, reverse=True), "Los cortes deberian ordenarse por fecha de inicio descendente"
if len(set(fechas_ordenables)) < 2:
    print("[AVISO] El suministro 204850 solo tiene 1 corte (una sola fecha) - el orden descendente entre VARIOS cortes de distinta fecha sigue sin ejercitarse de verdad. Pedir un suministro con multiples cortes para una verificacion completa.")
''')

add("CP049", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "204850")  # CONFIRMADO EN VIVO el 15/09/2026: suministro real CON corte programado
abrir_cortes_programados(app, frame)
modal = modal_cortes(frame)
expect(modal).to_be_visible(timeout=8000)
capturar_paso(app, "modal_cortes_abierto", paso_excel=4)
assert modal.locator("table").count() > 0, "Este suministro no tiene grilla de cortes que probar - reemplazar por uno con cortes reales"
texto_fecha = modal.locator("table tbody tr td").filter(has_text=re.compile(r"\\d{2}/\\d{2}/\\d{4}")).first.inner_text()
assert re.search(r"\\d{2}/\\d{2}/\\d{4} \\d{2}:\\d{2}:\\d{2}", texto_fecha), f"Formato de fecha inesperado: {texto_fecha!r}"
capturar_paso(app, "formato_de_fecha_verificado", paso_excel=5)
''')

add("CP050", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "204850")  # CONFIRMADO EN VIVO el 15/09/2026: suministro real CON corte programado (Estado real observado: APROBADO)
abrir_cortes_programados(app, frame)
modal = modal_cortes(frame)
expect(modal).to_be_visible(timeout=8000)
capturar_paso(app, "modal_cortes_abierto", paso_excel=4)
# La columna real es "Estado" (confirmado en vivo, valores vistos:
# APROBADO) - se revisa esa columna puntual en vez de buscar el texto
# "Activo/Inactivo/Anulado" en cualquier celda (ese texto no aparecio
# en la grilla real).
idx_estado = [h.strip() for h in modal.locator("table th").all_inner_texts()].index("Estado")
estados = [f.locator("td").nth(idx_estado).inner_text().strip() for f in modal.locator("table tbody tr").all()]
capturar_paso(app, "estados_revisados", paso_excel=5)
assert all(e.upper() not in ("INACTIVO", "ANULADO", "RECHAZADO", "CANCELADO") for e in estados), f"Solo deberian listarse cortes activos, se vio: {estados}"
if len(set(estados)) < 2:
    print(f"[AVISO] Solo se observo el estado {estados!r} en los datos disponibles (204850) - no se pudo confirmar en vivo que un corte Inactivo/Anulado/Rechazado realmente se EXCLUYA de la grilla (haria falta un suministro con cortes en varios estados para probarlo de verdad).")
''')

add("CP059", "abrir_atencion_cliente", '''
# NOTA: RANGO_CORTE vive en matf_parametros (Informix), fuera del alcance
# de lo que Playwright puede leer via UI - se documenta el comportamiento
# esperado pero la verificacion del limite exacto requiere consultar la
# base de datos aparte.
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "204850")  # CONFIRMADO EN VIVO el 15/09/2026: suministro real CON corte programado
abrir_cortes_programados(app, frame)
modal = modal_cortes(frame)
expect(modal).to_be_visible(timeout=8000)
capturar_paso(app, "modal_cortes_abierto", paso_excel=5)
print("[AVISO] CP059 requiere confirmar el valor de RANGO_CORTE en matf_parametros para validar el limite exacto - no automatizable solo con UI.")
''')

add("CP060", "abrir_atencion_cliente", '''
# BUG REAL / limite confirmado en vivo el 15/09/2026 (suministro 204850,
# con corte real): la grilla "Ultimas Interrupciones" NO tiene ninguna
# columna de "nivel de tension" (columnas reales: Codigo | Fecha Inicio
# | Fecha Fin | Estado | fecha_ini_int, ver modal_cortes) - si el
# filtro B/M existe, es 100% server-side y no hay nada que verificar
# via UI/Playwright para este caso tal como esta descrito.
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "204850")
abrir_cortes_programados(app, frame)
modal = modal_cortes(frame)
expect(modal).to_be_visible(timeout=8000)
capturar_paso(app, "modal_cortes_abierto", paso_excel=5)
print("[AVISO] La grilla real de Cortes Programados no tiene columna de nivel de tension (ver docstring de modal_cortes) - este caso no es verificable via UI tal como esta descrito, requiere confirmar con Desarrollo/BD si el filtro B/M se aplica server-side.")
''')

add("CP061", "abrir_atencion_cliente", '''
# BUG REAL / limite confirmado en vivo el 15/09/2026 (suministro 204850,
# con corte real): la grilla no distingue visualmente "programado" de
# "incidencia" (no hay columna de origen) - no se puede verificar
# dedup entre ambas fuentes solo con lo que se ve en pantalla.
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "204850")
abrir_cortes_programados(app, frame)
modal = modal_cortes(frame)
expect(modal).to_be_visible(timeout=8000)
capturar_paso(app, "modal_cortes_abierto", paso_excel=5)
filas = modal.locator("table tbody tr").all_inner_texts()
capturar_paso(app, "filas_revisadas", paso_excel=6)
assert len(filas) == len(set(filas)), "No deberia haber filas duplicadas entre cortes programados e incidencias"
print("[AVISO] La grilla real no tiene columna de origen (programado vs. incidencia) - esta verificacion solo detecta filas IDENTICAS duplicadas, no dedup real entre las 2 fuentes de datos (sgi_pro_clientes/sgi_inc_clientes).")
''')

add("CP062", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "204850")  # CONFIRMADO EN VIVO el 15/09/2026: suministro real CON corte programado
abrir_cortes_programados(app, frame)
modal = modal_cortes(frame)
expect(modal).to_be_visible(timeout=8000)
capturar_paso(app, "modal_cortes_abierto", paso_excel=5)
capturar_paso(app, "tipos_revisados", paso_excel=6)
print("[AVISO] CP062 distingue cortes programados vs. incidencia por una columna de origen que no existe en la grilla real (ver docstring de modal_cortes) - no verificable via UI tal como esta descrito.")
''')


# ===========================================================================
# RF-03 - Instalacion Programada por Norma (CP051-CP058, CP063, CP094-CP095)
# App: "Registro De Atencion" (pestana). NADA confirmado en vivo.
# ===========================================================================
add("CP051", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "1768544")  # CONFIRMADO EN VIVO el 15/09/2026: suministro real con mediciones (dato provisto por el usuario)
capturar_paso(app, "suministro_ingresado", paso_excel=5)
abrir_instalaciones(app, frame)
capturar_paso(app, "antes_de_verificar_dialogo", paso_excel=6)
dialogo = modal_instalaciones(frame)
expect(dialogo).to_be_visible(timeout=8000)
# Las 3 grillas del dialogo tardan unos segundos en cargar (confirmado
# en vivo: leerlas de inmediato las mostraba en "Cargando...").
app.wait_for_timeout(4000)
assert dialogo.get_by_role("table").count() > 0, "Se esperaba al menos una grilla de instalaciones/mediciones dentro del dialogo"
capturar_paso(app, "dialogo_instalaciones_visible", paso_excel=7)
''')

add("CP052", "abrir_atencion_cliente", '''
expandir_inf_tecnica(frame)  # el icono queda oculto hasta expandir esta seccion (confirmado en vivo)
icono_medicion = frame.locator('img[title="Mediciones programadas por norma"], img[title="Mediciones programadas por Norma"]').first
TIPOS = ["SUMINISTRO", "SUMINISTRO NUEVO", "FNL", "SAS", "SST", "SST CON SUMINISTRO"]
VISIBLE_EN = {"SUMINISTRO", "SUMINISTRO NUEVO"}
for tipo in TIPOS:
    seleccionar_tipo(frame, tipo)
    visible = icono_medicion.count() > 0 and icono_medicion.is_visible()
    capturar_paso(app, f"icono_instalaciones_{tipo.replace(' ', '_')}", paso_excel=4)
    if tipo in VISIBLE_EN:
        assert visible, f"El icono de Instalaciones deberia ofrecerse con tipo {tipo}"
    else:
        assert not visible, f"El icono de Instalaciones no deberia ofrecerse con tipo {tipo}"
capturar_paso(app, "recorrido_de_tipos_completo", paso_excel=5)
seleccionar_tipo(frame, "SUMINISTRO NUEVO")
if suministro(frame).count():
    suministro(frame).fill("1045027")
icono_medicion.click()
capturar_paso(app, "boton_accionado_con_suministro_nuevo", paso_excel=6)
pestana = modal_instalaciones(frame)
assert pestana.count() == 0 or not pestana.first.is_visible(), "No deberia abrirse la pestana de instalaciones con tipo SUMINISTRO NUEVO"
capturar_paso(app, "sin_pestana_ni_mensaje", paso_excel=7)
''')

add("CP053", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
capturar_paso(app, "suministro_vacio", paso_excel=5)
abrir_instalaciones(app, frame)
capturar_paso(app, "antes_de_verificar_mensaje", paso_excel=6)
mensaje = frame.get_by_text(re.compile("ingrese.*[Ss]uministro"))
expect(mensaje.first).to_be_visible(timeout=8000)
capturar_paso(app, "mensaje_verificado", paso_excel=7)
''')

add("CP054", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "1431348")  # CONFIRMADO EN VIVO el 15/09/2026: suministro real SIN mediciones asociadas (dato provisto por el usuario) - "9999999" NO servia, es un codigo invalido (dispara "Cliente no encontrado" antes de llegar a Instalaciones)
capturar_paso(app, "suministro_sin_instalaciones", paso_excel=6)
abrir_instalaciones(app, frame)
capturar_paso(app, "antes_de_verificar_mensaje", paso_excel=7)
mensaje = frame.get_by_text(re.compile("no se encontraron", re.IGNORECASE))
expect(mensaje.first).to_be_visible(timeout=8000)
capturar_paso(app, "mensaje_sin_registros", paso_excel=8)
''')

add("CP055", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "1768544")  # CONFIRMADO EN VIVO el 15/09/2026: suministro real con mediciones (dato provisto por el usuario)
abrir_instalaciones(app, frame)
dialogo = modal_instalaciones(frame)
expect(dialogo).to_be_visible(timeout=8000)
app.wait_for_timeout(4000)  # las 3 grillas tardan en cargar (confirmado en vivo)
capturar_paso(app, "dialogo_instalaciones_abierto", paso_excel=4)
grilla = grilla_instalaciones(dialogo)  # "Calidad de Producto", la que coincide con el EF
encabezados = [h.strip() for h in grilla.locator("th").all_inner_texts()]
capturar_paso(app, "columnas_revisadas", paso_excel=5)
# COLUMNAS REALES CONFIRMADAS EN VIVO el 15/09/2026 (dialogo "Mediciones
# programadas por norma", grilla "Calidad de Producto"):
COLUMNAS_ESPERADAS = ["Periodo", "Suministro", "Estado", "Resultado"]
for col in COLUMNAS_ESPERADAS:
    assert any(col.lower() in h.lower() for h in encabezados), f"Se esperaba una columna relacionada a {col!r}, encabezados reales: {encabezados}"
''')

add("CP056", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "1768544")  # CONFIRMADO EN VIVO el 15/09/2026: suministro real con mediciones
abrir_instalaciones(app, frame)
dialogo = modal_instalaciones(frame)
expect(dialogo).to_be_visible(timeout=8000)
app.wait_for_timeout(4000)
capturar_paso(app, "dialogo_instalaciones_abierto", paso_excel=4)
grilla = grilla_instalaciones(dialogo)
if not grilla_tiene_datos(grilla):
    print("[AVISO] La grilla 'Calidad de Producto' esta vacia para el suministro 1768544 (fila fantasma sin datos, ver grilla_tiene_datos) - hace falta uno con datos reales en ESA grilla puntual para probar la edicion/alta/baja sobre una fila real.")
    assert False, "Pendiente de un suministro con filas reales en la grilla Calidad de Producto para verificar solo-lectura"
celda = grilla.locator("tbody tr").first.locator("td").first
try:
    celda.dblclick()
    editable = celda.locator("input, select").count() > 0
except Exception:
    editable = False
assert not editable, "La grilla de instalaciones deberia ser de solo lectura"
assert dialogo.get_by_role("button", name=re.compile("Agregar|Nuevo", re.IGNORECASE)).count() == 0, "No deberia ofrecerse un boton para agregar registros"
assert dialogo.get_by_role("button", name=re.compile("Eliminar", re.IGNORECASE)).count() == 0, "No deberia ofrecerse un boton para eliminar registros"
capturar_paso(app, "sin_edicion_ni_alta_ni_baja", paso_excel=8)
''')

add("CP057", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "1768544")  # TODO SIN CONFIRMAR: suministro con instalaciones de VARIOS periodos - 1768544 solo tiene datos en la grilla "Precision de la Medida", no en "Calidad de Producto"
abrir_instalaciones(app, frame)
dialogo = modal_instalaciones(frame)
expect(dialogo).to_be_visible(timeout=8000)
app.wait_for_timeout(4000)
capturar_paso(app, "dialogo_instalaciones_abierto", paso_excel=4)
grilla = grilla_instalaciones(dialogo)
periodos_texto = grilla.locator("tbody tr td").filter(has_text=re.compile(r"\\d{4}-?\\d{2}|\\d{2}/\\d{4}")).all_inner_texts()
capturar_paso(app, "periodos_revisados", paso_excel=5)
if not periodos_texto:
    print("[AVISO] La grilla 'Calidad de Producto' no tiene filas con periodo para el suministro 1768544 - hace falta uno con VARIOS periodos reales para verificar el orden descendente.")
    assert False, "Pendiente de un suministro con varios periodos reales en la grilla Calidad de Producto"
assert periodos_texto == sorted(periodos_texto, reverse=True), "Los periodos deberian listarse en orden descendente"
''')

add("CP058", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "1768544")  # TODO SIN CONFIRMAR: suministro con puntos de medicion en distintos estados - 1768544 no tiene filas en "Calidad de Producto"
abrir_instalaciones(app, frame)
dialogo = modal_instalaciones(frame)
expect(dialogo).to_be_visible(timeout=8000)
app.wait_for_timeout(4000)
capturar_paso(app, "dialogo_instalaciones_abierto", paso_excel=4)
grilla = grilla_instalaciones(dialogo)
if not grilla_tiene_datos(grilla):
    print("[AVISO] La grilla 'Calidad de Producto' esta vacia para el suministro 1768544 (fila fantasma sin datos, ver grilla_tiene_datos) - hace falta uno con puntos en distintos estados (Activo/Inactivo) para verificar el filtro.")
    assert False, "Pendiente de un suministro con puntos de medicion en distintos estados en la grilla Calidad de Producto"
estados = grilla.locator("tbody tr td").filter(has_text=re.compile("Activo|Inactivo", re.IGNORECASE)).all_inner_texts()
capturar_paso(app, "estados_revisados", paso_excel=5)
assert all("inactivo" not in e.lower() for e in estados), "Solo deberian listarse puntos de medicion activos"
''')

add("CP063", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "1768544")  # TODO SIN CONFIRMAR: suministro con un punto "No se pudo efectuar medicion" - 1768544 no tiene filas en "Calidad de Producto"
abrir_instalaciones(app, frame)
dialogo = modal_instalaciones(frame)
expect(dialogo).to_be_visible(timeout=8000)
app.wait_for_timeout(4000)
capturar_paso(app, "dialogo_instalaciones_abierto", paso_excel=4)
grilla = grilla_instalaciones(dialogo)
if not grilla_tiene_datos(grilla):
    print("[AVISO] La grilla 'Calidad de Producto' esta vacia para el suministro 1768544 (fila fantasma sin datos, ver grilla_tiene_datos) - hace falta uno con un punto 'No se pudo efectuar medicion' real para verificar la leyenda.")
    assert False, "Pendiente de un suministro con una medicion no efectuada en la grilla Calidad de Producto"
fila_no_medicion = dialogo.get_by_text("No se pudo efectuar medicion", exact=False)
expect(fila_no_medicion.first).to_be_visible(timeout=8000)
capturar_paso(app, "leyenda_no_medicion_verificada", paso_excel=5)
''')

add("CP094", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
capturar_paso(app, "suministro_vacio", paso_excel=5)
abrir_instalaciones(app, frame)
capturar_paso(app, "antes_de_verificar_mensaje", paso_excel=6)
mensaje = frame.get_by_text("Por favor ingrese un n\\u00famero de Suministro")
expect(mensaje).to_be_visible(timeout=8000)
capturar_paso(app, "mensaje_exacto_verificado", paso_excel=7)
''')

add("CP095", "abrir_atencion_cliente", '''
seleccionar_tipo(frame, "SUMINISTRO")
buscar_por_codigo(app, frame, "1431348")  # CONFIRMADO EN VIVO el 15/09/2026: suministro real SIN mediciones asociadas (dato provisto por el usuario) - "9999999" NO servia, es un codigo invalido
capturar_paso(app, "suministro_sin_mediciones", paso_excel=6)
abrir_instalaciones(app, frame)
capturar_paso(app, "antes_de_verificar_mensaje", paso_excel=7)
mensaje = frame.get_by_text("No se encontraron mediciones")
expect(mensaje).to_be_visible(timeout=8000)
capturar_paso(app, "mensaje_exacto_verificado", paso_excel=8)
''')


# ===========================================================================
# RF-04 - Listado de Atenciones (CP064-CP075, CP089-CP093)
# CONFIRMADO EN VIVO el 14/09/2026 con el usuario DCABA_DW: vive en el
# MISMO click de menu que abre "Atencion al Cliente" (RF-01/02/03) - ese
# click abre DOS popups a la vez, uno es este Listado (titulo "Consulta
# De Atenciones Comerciales", componente app-listado-de-atenciones, el
# mismo de PR000335 Sprint 1) y el otro es la pantalla de detalle (ver
# abrir_listado_atenciones/abrir_atencion_cliente). Busqueda/filtro ya
# confirmados en Sprint 1; seleccion de fila y Agregar/Consultar/
# Modificar CONFIRMADOS en vivo (abren un POPUP NUEVO con los datos de la
# fila, ver intentar_abrir_detalle_desde_listado) - Eliminar y las reglas
# de negocio especificas (modulo ajeno al MAC, Alumbrado Publico, permiso
# Eliminar Atencion) siguen sin confirmar.
# ===========================================================================
add("CP064", "abrir_listado_atenciones", '''
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
capturar_paso(app, "busqueda_ejecutada", paso_excel=4)
seleccionar_primera_fila(pantalla)
capturar_paso(app, "atencion_seleccionada", paso_excel=5)
capturar_paso(app, "antes_de_presionar_agregar", paso_excel=6)
detalle, frame_detalle = intentar_abrir_detalle_desde_listado(app, pantalla, "Agregar")
assert detalle is not None, "Se esperaba que Agregar abriera la pantalla de detalle con los datos de la atencion seleccionada"
capturar_paso(detalle, "detalle_abierto_desde_agregar", paso_excel=7)
''')

add("CP065", "abrir_listado_atenciones", '''
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
capturar_paso(app, "busqueda_ejecutada_sin_seleccion", paso_excel=4)
capturar_paso(app, "antes_de_presionar_agregar", paso_excel=5)
detalle, frame_detalle = intentar_abrir_detalle_desde_listado(app, pantalla, "Agregar")
assert detalle is None, "No deberia abrirse ninguna pantalla de detalle sin una atencion seleccionada"
mensaje = frame.get_by_role("dialog")
assert not (mensaje.count() and mensaje.first.is_visible()), "No deberia mostrarse ningun mensaje al presionar Agregar sin seleccion"
capturar_paso(app, "silencio_verificado", paso_excel=6)
''')

add("CP066", "abrir_listado_atenciones", '''
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
capturar_paso(app, "busqueda_ejecutada", paso_excel=4)
seleccionar_primera_fila(pantalla)
capturar_paso(app, "atencion_seleccionada", paso_excel=5)
capturar_paso(app, "antes_de_presionar_consultar", paso_excel=6)
detalle, frame_detalle = intentar_abrir_detalle_desde_listado(app, pantalla, "Consultar")
assert detalle is not None, "Se esperaba que Consultar abriera el detalle en modo solo lectura"
capturar_paso(detalle, "detalle_solo_lectura_abierto", paso_excel=7)
''')

add("CP067", "abrir_listado_atenciones", '''
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
capturar_paso(app, "busqueda_ejecutada", paso_excel=4)
seleccionar_primera_fila(pantalla)
capturar_paso(app, "atencion_seleccionada", paso_excel=5)
capturar_paso(app, "antes_de_presionar_modificar", paso_excel=6)
detalle, frame_detalle = intentar_abrir_detalle_desde_listado(app, pantalla, "Modificar")
assert detalle is not None, "Se esperaba que Modificar abriera el detalle en modo edicion"
capturar_paso(detalle, "detalle_en_edicion_abierto", paso_excel=7)
guardado = intentar_guardar_modificacion(detalle, frame_detalle)
capturar_paso(detalle, "despues_de_intentar_guardar", paso_excel=8)
assert guardado, "DEFECTO REAL CONFIRMADO EN VIVO el 14/09/2026: el backend rechaza el guardado de Modificar (400 Acceso Denegado, POST ModificarAtencionCliente) y el frontend no muestra ningun mensaje de error - el formulario queda en blanco silenciosamente. Rechazado para correccion por Desarrollo (ver _exploracion/network_log_cp066.txt)."
''')

add("CP068", "abrir_listado_atenciones", '''
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
seleccionar_primera_fila(pantalla)
detalle, frame_detalle = intentar_abrir_detalle_desde_listado(app, pantalla, "Consultar")
assert detalle is not None, "Se esperaba que Consultar abriera el detalle"
capturar_paso(detalle, "detalle_consultado", paso_excel=5)
campos = frame_detalle.locator("input, select, textarea").all()
no_editables = [c for c in campos if not c.is_editable()]
capturar_paso(detalle, "campos_revisados", paso_excel=6)
assert len(no_editables) == len(campos), f"DEFECTO REAL CONFIRMADO EN VIVO el 14/09/2026: se esperaba que TODOS los campos fueran solo lectura en modo Consultar, {len(campos) - len(no_editables)} admiten edicion. Si se edita alguno de estos campos, el intento de guardado silencioso resultante choca con el mismo defecto de Modificar (ver CP067/090/093, network_log_cp066.txt). Rechazado para correccion por Desarrollo."
''')

add("CP069", "abrir_listado_atenciones", '''
# TODO SIN CONFIRMAR: elegir especificamente una atencion registrada
# fuera del MAC. Ademas: DEFECTO REAL confirmado en vivo el 14/09/2026
# (ver intentar_guardar_modificacion) hace que el backend rechace
# CUALQUIER guardado de Modificar sin distinguir el motivo - no se
# puede aislar la regla de negocio especifica de este caso (bloqueo
# por modulo ajeno al MAC) de ese defecto general hasta que se
# corrija. Se deja documentado como AVISO y el caso igual se marca
# FALLO por el defecto real (mismo criterio que CP067/090/093).
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
capturar_paso(app, "busqueda_ejecutada", paso_excel=4)
seleccionar_primera_fila(pantalla)
capturar_paso(app, "atencion_ajena_al_mac_seleccionada", paso_excel=5)
detalle, frame_detalle = intentar_abrir_detalle_desde_listado(app, pantalla, "Modificar")
assert detalle is not None, "Se esperaba poder abrir el detalle de Modificar para intentar guardar y verificar el bloqueo"
capturar_paso(detalle, "detalle_abierto", paso_excel=6)
guardado = intentar_guardar_modificacion(detalle, frame_detalle)
capturar_paso(detalle, "despues_de_intentar_guardar", paso_excel=7)
print("[AVISO] No se pudo aislar la regla de negocio especifica ('modulo ajeno al MAC' deberia bloquear el guardado) del DEFECTO REAL confirmado en vivo el 14/09/2026: el backend rechaza CUALQUIER guardado de Modificar (400 Acceso Denegado) sin distinguir el motivo. Reevaluar este caso puntual una vez Desarrollo corrija ese defecto general.")
assert guardado, "DEFECTO REAL CONFIRMADO EN VIVO el 14/09/2026: el backend rechaza el guardado de Modificar (400 Acceso Denegado, POST ModificarAtencionCliente) sin mostrar ningun mensaje de error. Rechazado para correccion por Desarrollo (ver _exploracion/network_log_cp066.txt)."
''')

add("CP070", "abrir_listado_atenciones", '''
# TODO SIN CONFIRMAR: elegir especificamente una atencion con Tipo
# Pedido Alumbrado Publico. Mismo DEFECTO REAL que CP069 (ver ahi):
# no se puede aislar la regla de negocio especifica del bloqueo
# general de guardado hasta que Desarrollo lo corrija.
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
capturar_paso(app, "busqueda_ejecutada", paso_excel=4)
seleccionar_primera_fila(pantalla)
capturar_paso(app, "atencion_alumbrado_publico_seleccionada", paso_excel=5)
detalle, frame_detalle = intentar_abrir_detalle_desde_listado(app, pantalla, "Modificar")
assert detalle is not None, "Se esperaba poder abrir el detalle de Modificar para intentar guardar y verificar el bloqueo"
capturar_paso(detalle, "detalle_abierto", paso_excel=6)
guardado = intentar_guardar_modificacion(detalle, frame_detalle)
capturar_paso(detalle, "despues_de_intentar_guardar", paso_excel=7)
print("[AVISO] No se pudo aislar la regla de negocio especifica ('Tipo Pedido Alumbrado Publico' deberia bloquear el guardado) del DEFECTO REAL confirmado en vivo el 14/09/2026: el backend rechaza CUALQUIER guardado de Modificar (400 Acceso Denegado) sin distinguir el motivo. Reevaluar este caso puntual una vez Desarrollo corrija ese defecto general.")
assert guardado, "DEFECTO REAL CONFIRMADO EN VIVO el 14/09/2026: el backend rechaza el guardado de Modificar (400 Acceso Denegado, POST ModificarAtencionCliente) sin mostrar ningun mensaje de error. Rechazado para correccion por Desarrollo (ver _exploracion/network_log_cp066.txt)."
''')

add("CP071", "abrir_listado_atenciones", '''
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
seleccionar_primera_fila(pantalla)
capturar_paso(app, "atencion_seleccionada", paso_excel=4)
paginas_antes = len(app.context.pages)
accion_listado(pantalla, "Eliminar").click()
capturar_paso(app, "antes_de_confirmar", paso_excel=5)
dialogo = frame.get_by_role("dialog")
expect(dialogo).to_be_visible(timeout=8000)
dialogo.get_by_role("button", name=re.compile("^S(i|\\u00ed)$")).click()
capturar_paso(app, "eliminacion_confirmada", paso_excel=6)
assert len(app.context.pages) == paginas_antes, "Eliminar no deberia abrir ninguna pantalla nueva"
capturar_paso(app, "vista_sin_cambios", paso_excel=7)
''')

add("CP072", "abrir_listado_atenciones", '''
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
seleccionar_primera_fila(pantalla)
texto_fila_previa = pantalla.locator("table tbody tr").first.inner_text()
capturar_paso(app, "atencion_seleccionada", paso_excel=4)
accion_listado(pantalla, "Eliminar").click()
capturar_paso(app, "antes_de_rechazar", paso_excel=5)
dialogo = frame.get_by_role("dialog")
expect(dialogo).to_be_visible(timeout=8000)
dialogo.get_by_role("button", name=re.compile("^No$")).click()
capturar_paso(app, "eliminacion_rechazada", paso_excel=6)
texto_fila_actual = pantalla.locator("table tbody tr").first.inner_text()
assert texto_fila_actual == texto_fila_previa, "La atencion deberia seguir en el listado sin cambios tras rechazar la confirmacion"
capturar_paso(app, "atencion_sigue_en_el_listado", paso_excel=7)
''')

add("CP073", "abrir_listado_atenciones", '''
# TODO SIN CONFIRMAR: requiere un usuario SIN el permiso "Eliminar
# Atencion" - se usa DCABA_DW como placeholder, reemplazar por un
# usuario de prueba sin ese permiso una vez definido.
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
seleccionar_primera_fila(pantalla)
capturar_paso(app, "atencion_seleccionada", paso_excel=5)
boton_eliminar = accion_listado(pantalla, "Eliminar")
disponible = boton_eliminar.count() > 0 and boton_eliminar.first.is_enabled()
capturar_paso(app, "boton_eliminar_revisado", paso_excel=6)
assert not disponible, "El boton Eliminar no deberia estar disponible sin el permiso Eliminar Atencion"
''')

add("CP074", "abrir_listado_atenciones", '''
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
seleccionar_primera_fila(pantalla)
codigo_eliminado = pantalla.locator("table tbody tr").first.locator("td").first.inner_text()
capturar_paso(app, "atencion_seleccionada", paso_excel=5)
accion_listado(pantalla, "Eliminar").click()
dialogo = frame.get_by_role("dialog")
dialogo.get_by_role("button", name=re.compile("^S(i|\\u00ed)$")).click()
capturar_paso(app, "atencion_eliminada", paso_excel=6)
filas_restantes = pantalla.locator("table tbody tr").all_inner_texts()
assert not any(codigo_eliminado in f for f in filas_restantes), "La atencion eliminada no deberia seguir en el listado"
capturar_paso(app, "ya_no_aparece_en_listado", paso_excel=7)
print("[AVISO] Verificar que el registro se conserva marcado como eliminado en base requiere acceso a BD, fuera del alcance de este script UI.")
''')

add("CP075", "abrir_listado_atenciones", '''
# TODO SIN CONFIRMAR: elegir especificamente una atencion CON pedidos y
# elementos asociados.
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
seleccionar_primera_fila(pantalla)
capturar_paso(app, "atencion_con_pedidos_seleccionada", paso_excel=5)
accion_listado(pantalla, "Eliminar").click()
dialogo = frame.get_by_role("dialog")
dialogo.get_by_role("button", name=re.compile("^S(i|\\u00ed)$")).click()
capturar_paso(app, "atencion_eliminada", paso_excel=6)
print("[AVISO] Verificar que pedidos/elementos asociados quedaron eliminados requiere acceso a BD o volver a Consultar la atencion - ambos fuera de lo confirmable con el ambiente caido.")
''')

add("CP089", "abrir_listado_atenciones", '''
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
# TODO SIN CONFIRMAR: el EF solo documenta "debe seleccionarse una
# atencion" como validacion de Agregar (igual que CP065) - no se
# identifico una regla adicional distinta en EF/ET para este caso.
seleccionar_primera_fila(pantalla)
capturar_paso(app, "atencion_seleccionada", paso_excel=5)
detalle, frame_detalle = intentar_abrir_detalle_desde_listado(app, pantalla, "Agregar")
assert detalle is None, "No deberia permitirse agregar cuando no se cumplen las validaciones"
capturar_paso(app, "agregar_no_procede", paso_excel=7)
''')

add("CP090", "abrir_listado_atenciones", '''
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
seleccionar_primera_fila(pantalla)
capturar_paso(app, "atencion_seleccionada", paso_excel=5)
detalle, frame_detalle = intentar_abrir_detalle_desde_listado(app, pantalla, "Modificar")
assert detalle is not None, "Se esperaba poder abrir el detalle de Modificar"
frame_detalle.get_by_role("button", name="Aceptar").click()
capturar_paso(detalle, "antes_de_verificar_rechazo", paso_excel=6)
mensaje = frame_detalle.get_by_role("dialog")
# DEFECTO REAL CONFIRMADO EN VIVO el 14/09/2026 (ver
# intentar_guardar_modificacion): al guardar en Modificar el backend
# responde 400 Acceso Denegado y el FRONTEND NO MUESTRA NINGUN
# mensaje/dialogo - por eso este assert (pensado para el mensaje de
# VALIDACION esperado) tambien falla, pero por el defecto general, no
# por ausencia de validacion de datos especificamente.
assert mensaje.count() > 0 and mensaje.first.is_visible(), "DEFECTO REAL CONFIRMADO EN VIVO el 14/09/2026: no aparece ningun mensaje (ni de validacion ni de error) al guardar - el backend rechaza el guardado (400 Acceso Denegado) en silencio. Rechazado para correccion por Desarrollo (ver _exploracion/network_log_cp066.txt)."
capturar_paso(app, "cambios_no_guardados", paso_excel=7)
''')

add("CP091", "abrir_listado_atenciones", '''
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
seleccionar_primera_fila(pantalla)
capturar_paso(app, "atencion_seleccionada", paso_excel=5)
accion_listado(pantalla, "Eliminar").click()
capturar_paso(app, "antes_de_verificar_rechazo", paso_excel=6)
dialogo = frame.get_by_role("dialog")
if dialogo.count() and dialogo.first.is_visible():
    dialogo.get_by_role("button", name=re.compile("^S(i|\\u00ed)$")).click()
capturar_paso(app, "verificar_eliminacion_no_procede", paso_excel=7)
print("[AVISO] CP091 necesita un caso concreto de 'atencion que no cumple las validaciones de eliminar' - no identificado explicitamente en el EF/ET mas alla de lo ya cubierto por CP073 (permiso).")
''')

add("CP092", "abrir_listado_atenciones", '''
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
seleccionar_primera_fila(pantalla)
detalle, frame_detalle = intentar_abrir_detalle_desde_listado(app, pantalla, "Agregar")
assert detalle is not None, "Se esperaba que Agregar abriera la pantalla de detalle"
capturar_paso(detalle, "pantalla_atencion_abierta", paso_excel=5)
completar_informacion_contacto_minima(frame_detalle)
completar_pedido_minimo(frame_detalle)
capturar_paso(detalle, "informacion_completada", paso_excel=6)
frame_detalle.get_by_role("button", name="Aceptar").click()
capturar_paso(detalle, "antes_de_verificar_registro", paso_excel=7)
confirmacion = frame_detalle.get_by_text(re.compile("registr", re.IGNORECASE))
expect(confirmacion.first).to_be_visible(timeout=8000)
capturar_paso(detalle, "atencion_registrada", paso_excel=8)
''')

add("CP093", "abrir_listado_atenciones", '''
# BUG REAL confirmado en vivo (14/09/2026): el id "txtAnot" para
# "Anotacion" (CAMPO_ID) nunca se confirmo en la vista principal -
# timeout esperandolo. Se usa el campo "Nombre" (#nombreA, CONFIRMADO)
# via intentar_guardar_modificacion en su lugar para llegar al mismo
# punto real de la prueba: intentar guardar un cambio en Modificar.
pantalla = frame.locator("app-listado-de-atenciones")
ejecutar_busqueda_listado(pantalla)
seleccionar_primera_fila(pantalla)
detalle, frame_detalle = intentar_abrir_detalle_desde_listado(app, pantalla, "Modificar")
assert detalle is not None, "Se esperaba que Modificar abriera la pantalla de detalle"
capturar_paso(detalle, "pantalla_atencion_abierta", paso_excel=5)
guardado = intentar_guardar_modificacion(detalle, frame_detalle)
capturar_paso(detalle, "despues_de_intentar_guardar", paso_excel=7)
assert guardado, "DEFECTO REAL CONFIRMADO EN VIVO el 14/09/2026: el backend rechaza el guardado de Modificar (400 Acceso Denegado, POST ModificarAtencionCliente) y el frontend no muestra ningun mensaje de error - el formulario queda en blanco silenciosamente. Rechazado para correccion por Desarrollo (ver _exploracion/network_log_cp066.txt)."
capturar_paso(detalle, "cambios_guardados", paso_excel=8)
''')


if __name__ == "__main__":
    if len(CASES) != len(MATRIZ):
        faltantes = sorted(set(MATRIZ) - {c["cp"] for c in CASES}, key=lambda k: int(''.join(ch for ch in k if ch.isdigit()) or 0))
        raise SystemExit(f"Faltan {len(faltantes)} casos por definir en CASES: {faltantes}")
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")
