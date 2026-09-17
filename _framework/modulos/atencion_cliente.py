"""
Modulo: Atención al Cliente (Web LDS)
Proyecto donde se confirmo: PR000335-SP2 (Sprint 2 - Atencion al Cliente
/ Cortes Programados / Instalacion Programada por Norma / Listado de
Atenciones).

Cubre en realidad 4 RF relacionados bajo una misma ruta de menu y un
mismo par de popups (ver abrir_atencion_cliente/abrir_listado_atenciones
mas abajo):
  RF-01/02/03: pantalla de detalle/registro "Atenciones A Clientes"
    (busqueda de suministro/SST, Informacion de Contacto, Cortes
    Programados, Mediciones Programadas por Norma).
  RF-04: "Consulta De Atenciones Comerciales" (listado con acciones
    Agregar/Consultar/Modificar/Eliminar, MISMO componente Angular que
    PR000335 Sprint 1: app-listado-de-atenciones).

Ruta de menu real CONFIRMADA EN VIVO el 14/09/2026 (la del EF con
"Tecnico > Registro De Atencion" daba error de servidor .NET -
assembly incompleto - la ruta real es la vieja de Sprint 1, que ya
apunta a la pantalla nueva):
    Comercial > Atención Integral Al Cliente > Atenciones A Clientes >
    Consulta De Atenciones Comerciales
Ese ULTIMO click abre DOS popups casi simultaneos en el mismo contexto
(confirmado revisando context.pages()): uno titulado "Consulta De
Atenciones Comerciales" (el Listado, RF-04) y otro titulado "Atenciones
A Clientes" (el detalle, RF-01/02/03) - por eso la navegacion usa
_abrir_popup_por_titulo() (busqueda activa filtrando por titulo exacto)
en vez de page.expect_popup() a ciegas, que capturaba cualquiera de los
2 segun cual disparara primero.

--- RF-01/02/03: pantalla "Atenciones A Clientes" ---
Campos de Informacion del Contacto CONFIRMADOS EN VIVO (ids reales, ver
CAMPO_ID): Nombre=nombreA, Apellido Paterno=apellidoPaterno, Apellido
Materno=apellidoMaterno, Correo=correo, Numero de Documento=dni,
Referencia de Direccion=direcionA (sic, typo real de la app),
Referencia=referencia, Telefono Fijo=telefonoFijo, Movil=movil,
Suministro=txtNumeroCodigoSumSST (el MISMO campo que la busqueda
principal, no uno separado). Anotacion/Motivo NO confirmados en vivo.

Checkboxes "Sin X" CONFIRMADOS (ver CHECKBOX_ID) - ojo con la falta de
consistencia real de mayusculas/plural: SinNombre (S mayuscula),
sinApellido (SINGULAR pese a que el label dice "Sin Apellidos").

Boton de busqueda real: NO tiene texto "Buscar" (es
`button.matf-btn-buscar-tipo`), y para tipo SST (y probablemente SST CON
SUMINISTRO) ese boton ni deja hacer click - el flujo real confirmado es
presionar Enter en el campo tras llenarlo (funciona para TODOS los
tipos, ver buscar_por_codigo()). Combo "Tipo" = #tipo (SUMINISTRO/SST/
FNL/SST CON SUMINISTRO/SUMINISTRO NUEVO/SAS); combo "Origen" = #origenA,
DISTINTO de Tipo (B-FACEBOOK, C-CARTA, E-CORREO ELECTRONICO, F-FAX,
I-INTERNET, K-DENUNCIAS TK, L-LIBRO DE OBSERVACION, N-MEDICION NTCSE,
V-VENTANILLA...).

BUG REAL confirmado en vivo (codigo real 2074382): para tipo SST CON
SUMINISTRO, si el suministro tiene una o mas solicitudes SST asociadas,
Enter abre un dialogo INTERMEDIO "Seleccionar SST por suministro"
(grilla) que hay que resolver (elegir fila + Aceptar) antes de que el
resto de la pantalla se autocomplete - ver buscar_por_codigo(), ya lo
maneja como no-op si no aparece.

--- RF-02: Cortes Programados / RF-03: Mediciones Programadas por Norma ---
Ambos iconos (NO botones de texto) viven OCULTOS dentro de la seccion
"Inf. Tecnica" del sidebar izquierdo, que hay que expandir primero
(expandir_inf_tecnica). BUG REAL de timing: sin esperar a que la
busqueda del suministro termine de cargar antes de expandir, el icono
nunca se estabiliza como visible.
  - Cortes Programados: `<img title="Cortes Programados">`. Suministro
    1045027 = sin cortes (dialog con "No se encontraron cortes
    programados", sin tabla). Suministro 204850 = CON cortes (mismo
    dialog, seccion "Ultimas Interrupciones" con tabla real: Codigo |
    Fecha Inicio | Fecha Fin | Estado | fecha_ini_int). NO hay columna
    de "nivel de tension" ni "tipo" en esta grilla real.
  - Mediciones Programadas por Norma: el EF la llama "Instalaciones en
    Medidor x Control Calidad", pero el tooltip REAL es "Mediciones
    programadas por norma" (mayus. inconsistente en el propio HTML - el
    selector cubre ambas variantes). Abre un dialog con TRES grillas:
    "Precision de la Medida" (unica con datos reales en los 3
    suministros probados: 1045027, 870783, 1768544), "Calidad de
    Producto" (la que coincide con RF-03 pero salio VACIA en los 3
    suministros probados) y "Contraste de Medidor 227" (tambien vacia).
    Las grillas tardan unos segundos en cargar tras abrir el dialogo.

BUG REAL confirmado en vivo (grillas de estos 2 dialogos): una grilla
"vacia" NO tiene 0 filas - Angular deja UNA fila <tr> fantasma con TODAS
las celdas en blanco. Un chequeo de count()==0 no la detecta (falso OK)
- usar grilla_tiene_datos().

--- RF-04: Listado de Atenciones (popup "Consulta De Atenciones Comerciales") ---
El filtro "Fecha:" viene tildado por defecto con el rango de HOY
unicamente - "Buscar" sin tocar nada casi siempre da 0 resultados
reales. El formulario exige al menos un filtro y RECHAZA mas de 31 dias
de rango - usar 30 dias hacia atras desde hoy (el maximo permitido, trae
filas reales - confirmado 24 filas).

Boton "Agregar" es UNICO y GLOBAL (fuera de la tabla); Consultar/
Modificar/Eliminar son POR FILA (columna "Acciones" de cada registro) -
escoparlos a la fila seleccionada, no buscarlos en toda la pantalla.
Cada fila tiene TAMBIEN un boton "Modificar Contacto" cuyo nombre
accesible CONTIENE "Modificar" como substring - usar SIEMPRE
exact=True.

Agregar/Consultar/Modificar NO cambian de pestana dentro de la misma
app - abren un POPUP NUEVO independiente que navega DIRECTO a la URL de
la app (sin el wrapper #aplicacion que si tienen los popups abiertos
desde el menu) - el "frame" a usar ahi es la pagina misma (verificar con
`if pg.locator("#aplicacion").count(): ... else: frame = pg`).

DEFECTO REAL CONFIRMADO EN VIVO (no de la automatizacion): el backend
rechaza CUALQUIER guardado de "Modificar" con 400 Acceso Denegado
(POST .../api/registro-atencion/ModificarAtencionCliente) y el FRONTEND
NO MUESTRA NINGUN MENSAJE DE ERROR - el popup vuelve silenciosamente a
un formulario en blanco, sin avisar al usuario que el guardado fallo.
intentar_guardar_modificacion() devuelve True solo si aparece la
confirmacion real (nunca deberia dar True mientras este defecto real
siga sin corregir en la app).

--- Modal "Informacion de Contacto" ---
No existe un boton con texto "Informacion de Contacto" - el trigger real
es el LINK "Información adicional del contacto" (sin href, disparado por
Angular (click), por eso el ARIA implicito es "generic" y
get_by_role("link", ...) NO lo encuentra - usar get_by_text).

--- Datos especificos sin confirmar (pendiente si se retoma este modulo) ---
Varios casos originales necesitaban un suministro/atencion con datos MUY
especificos (sin cortes, con varios periodos, fuera del MAC, Alumbrado
Publico, etc.) no incluidos aca por ser demasiado puntuales del proyecto
que los uso. Varias reglas de negocio (RANGO_CORTE, nivel de tension,
dedup de incidencias) viven en tablas de Informix (matf_parametros,
sgi_programa), no verificables solo con UI.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  capturar_paso, _click_visible
"""
import re
import time
from datetime import date, timedelta
from playwright.sync_api import TimeoutError as PWTimeoutError

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
    "Suministro": "txtNumeroCodigoSumSST",
    # Sin confirmar en vivo (no aparecieron en la vista principal ya
    # buscada; podrian vivir en el modal "Anotaciones" u otro lado):
    "Anotacion": "txtAnot",
    "Motivo": "txtMotivo",
}

CHECKBOX_ID = {
    "Sin Nombre": "SinNombre",
    "Sin Apellidos": "sinApellido",
    "Sin Telefono": "sinTelefono",
    "Sin Correo": "sinCorreo",
    "Sin Documento": "sinDocumento",
}

RUTA_MENU_ATENCIONES = ["Comercial", "Atención Integral Al Cliente", "Atenciones A Clientes", "Consulta De Atenciones Comerciales"]


def campo(frame, etiqueta):
    """Ubica un campo por su id real (ver CAMPO_ID)."""
    id_campo = CAMPO_ID.get(etiqueta, etiqueta)
    return frame.locator(f"#{id_campo}")


def secciones_visibles(frame):
    """Titulos de seccion (encabezados) actualmente visibles - cada
    seccion real usa class="barraTitulo" (con &nbsp;/espacios variables
    alrededor, normalizar con " ".join(t.split()) antes de comparar). Se
    excluye el titulo del panel exterior "Nuevas Atenciones"."""
    titulos = []
    for h in frame.locator(".barraTitulo").all():
        if h.is_visible():
            t = " ".join(h.inner_text().split())
            if t and t != "Nuevas Atenciones":
                titulos.append(t)
    return titulos


def seleccionar_tipo(frame, texto):
    frame.locator("#tipo").select_option(label=texto)


def seleccionar_origen(frame, texto):
    frame.locator("#origenA").select_option(label=texto)


def suministro(frame):
    return frame.locator("#txtNumeroCodigoSumSST")


def buscar_por_codigo(app, frame, codigo):
    """Busca por Suministro/SST. Enter funciona para TODOS los tipos
    probados (a diferencia del boton real matf-btn-buscar-tipo, que no
    funciona para SST/SST CON SUMINISTRO) - se usa siempre en vez de
    depender del boton."""
    campo_busq = frame.locator("#txtNumeroCodigoSumSST")
    campo_busq.fill(codigo)
    campo_busq.press("Enter")
    try:
        app.wait_for_load_state("networkidle", timeout=15000)
    except PWTimeoutError:
        pass
    app.wait_for_timeout(1500)
    # Para tipo SST CON SUMINISTRO con una o mas solicitudes SST
    # asociadas, Enter abre un dialogo INTERMEDIO "Seleccionar SST por
    # suministro" (grilla) - hay que elegir una fila y confirmar con
    # Aceptar antes de que el resto de la pantalla se autocomplete. Para
    # los demas casos este bloque es un no-op inofensivo.
    dialogo = frame.get_by_role("dialog")
    try:
        dialogo.first.wait_for(state="visible", timeout=2000)
    except PWTimeoutError:
        return
    if "Seleccionar SST" in dialogo.first.inner_text():
        dialogo.first.locator("table tbody tr").first.click()
        dialogo.first.get_by_role("button", name="Aceptar").click()
        app.wait_for_timeout(2500)


def marcar_checkbox(frame, etiqueta):
    id_checkbox = CHECKBOX_ID.get(etiqueta, etiqueta)
    frame.locator(f"#{id_checkbox}").check()


def desmarcar_checkbox(frame, etiqueta):
    id_checkbox = CHECKBOX_ID.get(etiqueta, etiqueta)
    frame.locator(f"#{id_checkbox}").uncheck()


def completar_informacion_contacto_minima(frame):
    """Completa el minimo de Informacion del Contacto para habilitar la
    grilla Pedidos. SIN CONFIRMAR EN VIVO cuales campos son el minimo
    real - se completan todos los conocidos por las dudas."""
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
    """Los iconos de Cortes Programados y Mediciones Programadas por
    Norma quedan OCULTOS hasta expandir la seccion 'Inf. Tecnica' del
    sidebar izquierdo - llamar esto antes de abrir_cortes_programados()
    o abrir_mediciones_programadas()."""
    frame.get_by_text("Inf. Técnica", exact=False).first.click()


def abrir_cortes_programados(app, frame):
    """No es un <button> sino un <img title="Cortes Programados"> dentro
    de 'Inf. Tecnica', oculto hasta expandirla (se expande sola aqui, con
    chequeo de visibilidad primero para no volver a colapsarla)."""
    icono = frame.locator('img[title="Cortes Programados"]')
    if not icono.is_visible():
        expandir_inf_tecnica(frame)
        app.wait_for_timeout(1000)
    icono.click()


def modal_cortes(frame):
    """Dialogo real: <cdk-dialog-container role="dialog">, titulo
    "Cortes Programados"."""
    return frame.get_by_role("dialog")


# --- RF-03: Instalacion Programada por Norma ---
def abrir_mediciones_programadas(app, frame):
    """El EF llama a este boton "Instalaciones en Medidor x Control
    Calidad", pero el tooltip REAL es "Mediciones programadas por
    norma" - tambien dentro de 'Inf. Tecnica' ya expandida. Abre un
    <cdk-dialog-container role="dialog"> (NO una pestana) con TRES
    grillas separadas - ver modal_instalaciones/grilla_instalaciones."""
    icono = frame.locator('img[title="Mediciones programadas por norma"], img[title="Mediciones programadas por Norma"]').first
    if not icono.is_visible():
        expandir_inf_tecnica(frame)
        app.wait_for_timeout(1000)
    icono.click()


abrir_instalaciones = abrir_mediciones_programadas


def modal_instalaciones(frame):
    """Dialogo real con TRES grillas: "Precision de la Medida" (indice
    0, unica con datos reales en los suministros probados), "Calidad de
    Producto" (indice 1, la que coincide con RF-03) y "Contraste de
    Medidor 227" (indice 2). Las grillas tardan unos segundos en cargar
    tras abrir el dialogo - leerlas antes de tiempo las hace parecer
    vacias cuando en realidad seguian con "Cargando..."."""
    return frame.get_by_role("dialog")


def grilla_instalaciones(dialogo, indice=1):
    return dialogo.get_by_role("table").nth(indice)


def grilla_tiene_datos(grilla):
    """Una grilla "vacia" en este dialogo NO tiene 0 filas - Angular deja
    UNA fila <tr> fantasma con TODAS las celdas en blanco. Un chequeo de
    count()==0 no la detecta (falso OK) - se considera "sin datos"
    tambien cuando la unica fila esta vacia."""
    filas = grilla.locator("tbody tr")
    if filas.count() == 0:
        return False
    return bool(filas.first.inner_text().strip())


# --- RF-04: Listado de Atenciones (grilla + Agregar/Consultar/Modificar/Eliminar) ---
def ejecutar_busqueda_listado(pantalla):
    """Ejecuta una busqueda que devuelva atenciones reales. El filtro
    'Fecha:' (#fFechaDesde/#fFechaHasta) viene tildado por defecto con
    el rango de HOY unicamente - se usan 30 dias hacia atras (el maximo
    permitido, RECHAZA mas de 31 dias con "Restriccion de Busqueda")."""
    hoy = date.today()
    desde = hoy - timedelta(days=29)
    pantalla.locator("#fFechaDesde").fill(desde.isoformat())
    pantalla.locator("#fFechaHasta").fill(hoy.isoformat())
    pantalla.get_by_role("button", name="Buscar").click()
    pantalla.get_by_role("button", name="Buscar").wait_for(state="visible", timeout=20000)


def seleccionar_primera_fila(pantalla):
    fila = pantalla.locator("table tbody tr").first
    fila.click()
    return fila


def accion_listado(pantalla, nombre):
    """Botones de accion: Agregar/Consultar/Modificar/Eliminar. "Agregar"
    es UNICO y GLOBAL (arriba de la grilla); Consultar/Modificar/
    Eliminar son POR FILA - se escopean a la PRIMERA fila (la que deja
    seleccionada seleccionar_primera_fila). exact=True obligatorio:
    cada fila tiene TAMBIEN un boton "Modificar Contacto" cuyo nombre
    CONTIENE "Modificar" como substring."""
    if nombre == "Agregar":
        return pantalla.get_by_role("button", name=nombre, exact=True)
    return pantalla.locator("table tbody tr").first.get_by_role("button", name=nombre, exact=True)


def intentar_abrir_detalle_desde_listado(app, pantalla, nombre_boton, timeout_ms=6000):
    """Agregar/Consultar/Modificar abren un POPUP NUEVO independiente
    (no una pestana dentro de la misma app) que navega DIRECTO a la URL
    de la app, SIN el wrapper #aplicacion que si tienen los popups
    abiertos desde el menu. Devuelve (detalle, frame_detalle) si se
    abrio un popup nuevo dentro de timeout_ms, o (None, None) si no."""
    paginas_antes = set(app.context.pages)
    accion_listado(pantalla, nombre_boton).click()
    plazo = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < plazo:
        nuevas = [pg for pg in app.context.pages if pg not in paginas_antes]
        if nuevas:
            detalle = nuevas[0]
            detalle.wait_for_load_state("networkidle")
            frame_detalle = detalle
            if detalle.locator("#aplicacion").count():
                frame_detalle = detalle.locator("#aplicacion").content_frame
            return detalle, frame_detalle
        app.wait_for_timeout(200)
    return None, None


def intentar_guardar_modificacion(detalle, frame_detalle):
    """Cambia el campo 'Nombre' y hace clic en Aceptar dentro de la
    pantalla de Modificar. DEFECTO REAL CONFIRMADO (no de la
    automatizacion): el backend rechaza CUALQUIER guardado de Modificar
    con 400 Acceso Denegado y el frontend NO MUESTRA NINGUN error - el
    popup vuelve silenciosamente a un formulario en blanco. Devuelve
    True solo si aparece la confirmacion real de guardado (nunca
    deberia dar True mientras este defecto siga sin corregir)."""
    frame_detalle.locator("#nombreA").fill("MODIFICACION DE PRUEBA")
    frame_detalle.get_by_role("button", name="Aceptar").click()
    detalle.wait_for_timeout(3000)
    confirmacion = frame_detalle.get_by_text(re.compile("actualiz|guard", re.IGNORECASE))
    return confirmacion.count() > 0 and confirmacion.first.is_visible()


def _abrir_popup_por_titulo(page, ruta_menu, titulo_esperado, selector_pantalla, timeout_menu=30000, timeout_pantalla=20000, paso_excel=None, timeout_popup_seg=15):
    """El ultimo click de RUTA_MENU_ATENCIONES abre DOS popups casi
    simultaneos en el mismo contexto - se busca activamente por TITULO
    exacto en vez de usar page.expect_popup() a ciegas (que capturaba
    cualquiera de los 2 segun cual disparara primero)."""
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


def abrir_atencion_cliente(page, paso_excel=1):
    """RF-01, RF-02, RF-03: pantalla de detalle/registro real (popup
    titulado "Atenciones A Clientes"). selector_pantalla =
    "#txtNumeroCodigoSumSST" (el campo Suministro/SST, confirmado
    presente al cargar)."""
    return _abrir_popup_por_titulo(
        page, RUTA_MENU_ATENCIONES, "Atenciones A Clientes", "#txtNumeroCodigoSumSST", paso_excel=paso_excel,
    )


def abrir_listado_atenciones(page, paso_excel=1):
    """RF-04: 'Listado de Atenciones' real - vive en el SEGUNDO popup
    (titulado "Consulta De Atenciones Comerciales") que abre la MISMA
    ruta de menu de abrir_atencion_cliente. Selector de pantalla:
    app-listado-de-atenciones (el MISMO componente Angular de PR000335
    Sprint 1 - ver el modulo `consulta_atenciones_comerciales.py` si
    existe, es la misma pantalla)."""
    return _abrir_popup_por_titulo(
        page, RUTA_MENU_ATENCIONES, "Consulta De Atenciones Comerciales", "app-listado-de-atenciones", paso_excel=paso_excel,
    )


def abrir_modal_informacion_contacto(frame):
    """No existe un boton con texto "Informacion de Contacto" - el
    trigger real es el LINK "Información adicional del contacto" (sin
    href, disparado por Angular (click), asi que el ARIA implicito NO es
    "link" sino "generic" - se usa get_by_text en vez de get_by_role."""
    frame.get_by_text(re.compile("Informaci(o|ó)n adicional del contacto", re.IGNORECASE)).click()
