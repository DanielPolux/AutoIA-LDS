"""
Modulo: Actualizacion De Precios (Web LDS)
Componente Angular: app-precios-list
Ruta de menu confirmada en vivo: Interno > Actualizacion De Precios

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual (no importa nada de un
matriz_casos.json ni de un generate_scripts.py de proyecto). Un
generate_scripts.py de proyecto importa lo que necesite de aca y le
agrega solo los cuerpos de caso (los CPxxx puntuales de SU matriz), sin
tener que re-descubrir nada de lo que ya esta documentado aca.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000325-SP3, 16/09/2026)
============================================================================

Pantalla principal (3 cards apiladas + barra de acciones fija):
  - Identificacion del Precio: Codigo de Precio (select, ~1157 opciones,
    NO correlativo con el texto visible - buscar por indice via
    indice_opcion_precio(), nunca hardcodear un indice fijo) + Fecha de
    Vigencia (<input type=date>) + Sector Tipico (select, valores "1"-"4"
    confirmados).
  - Modo: radios Normal / Por Tramos - se BLOQUEAN (quedan solo lectura)
    apenas se lee un precio EXISTENTE; solo son editables para un precio
    NUEVO (boton dinamico en "Ingresar").
  - Valores: Valor Actual (Neto) SIEMPRE readonly, Valor Nuevo (Neto) y
    Porc. Reajuste editables segun modo/estado.
  - Barra de acciones: Leer (siempre habilitado) | Ingresar/Modificar
    (boton dinamico, habilitado solo despues de Leer) | Tramos (solo
    visible/util en modo Por Tramos) | Cancelar (siempre habilitado,
    limpia el formulario completo).

Precio "023 - ALUMBRADO PUBLICO (TRAMOS)" es el UNICO confirmado en modo
Por Tramos entre los primeros 605 codigos explorados (de 1157 totales) -
usarlo como referencia conocida para cualquier caso que necesite un
precio en ese modo; buscarlo por texto ("ALUMBRADO PUBLICO") con
indice_opcion_precio(), nunca por indice fijo (el catalogo real podria
reordenarse).

Mensajes exactos del sistema (ver manual_usuario_actualizacion_precios.pdf
si el proyecto lo tiene en Documentos/ - trae la lista completa de
validaciones por campo):
  - "Ingrese Codigo Precio Valido."  (codigo no reconocido)
  - "Ingrese fecha." / "Ingrese sector tipico."
  - "¡Debe ingresar o Valor o Porcentaje!"
  - "No debe reajustar sobre valor actual cero." (solo Porc.Reajuste sin
    Valor Actual registrado)
  - "¿Esta seguro de ingresar el precio?" / "...de modificar el precio?"
    (confirm Si/No)
  - "Registro Actualizado." (resultado exitoso, alta y modificacion)

Ventana de Tramos ("Actualizacion de Precios por Tramo"): se abre SOLA al
elegir Por Tramos en modo Ingresar, o al Leer un precio que ya es Por
Tramos. Card "Tramos" (vigencia actual, editable) + card "Valores
Utilizados al DD/MM/AAAA" (vigencia anterior, solo lectura, boton
Pegar copia sus rangos Inferior/Superior a la fila de edicion).
  - Los tramos se guardan de forma INDIVIDUAL e INMEDIATA en BD al
    presionar Ingresar/Modificar dentro de esta ventana - no hay un
    confirm global al cerrar.
  - Numeracion estrictamente consecutiva (1, 2, 3...) y SIN huecos ni
    superposicion: el Tramo Inferior de un tramo nuevo debe ser EXACTAMENTE
    igual al Tramo Superior del ultimo tramo ya cargado.
  - Solo se puede modificar el Valor de un tramo existente, nunca sus
    rangos (Inferior/Superior quedan grises/deshabilitados al
    seleccionar una fila existente).
  - Mensajes: "Registro actualizado." (alta/modificacion de UN tramo),
    "Registro sera Eliminado." (eliminar), "Numero de Tramo debe ser
    consecutivo", "Tramo Inferior debe ser igual al ultimo tramo
    superior", "Debe ingresar Tramos." (al intentar Ingresar en la
    pantalla principal sin haber cargado ningun tramo).
  - Cierre con boton dual Cancelar/Cerrar: "Cancelar" (hay datos en la
    fila de edicion, solo la limpia) vs "Cerrar" (fila vacia - cierra
    directo si no hubo cambios en la sesion, o pide confirmar "Se
    guardaron los cambios, ¿Continuar?" si sí hubo).

BUGS REALES / gotchas confirmados en vivo (no asumir que ya no aplican
sin volver a probar si la app cambio):
  - Si se usa "Pegar", hay que escribir el Nro. de Tramo ANTES de
    presionar Pegar - al reves (escribir el numero DESPUES), los valores
    recien pegados de Inferior/Superior se resetean a vacio. Ver
    crear_tramo() abajo, parametro usar_pegar.
  - "Pegar" siempre trae los rangos de la VIGENCIA ANTERIOR, sin importar
    si la vigencia ACTUAL que se esta armando ya tiene tramos cargados -
    solo es correcto usarlo para el PRIMER tramo de una vigencia vacia;
    si ya hay tramos hoy, hay que encadenar a mano con el Superior de la
    ultima fila actual en vez de Pegar.
  - La grilla de vigencia actual, cuando esta vacia, muestra una fila
    PLACEHOLDER de un solo <td> ("Sin tramos registrados para esta
    vigencia.") que TAMBIEN cuenta como <tr> en tbody - un
    filas.count() > 0 ingenuo la confunde con un tramo real y rompe
    cualquier lectura de columna (ej. .nth(2) sobre esa fila cuelga 30s
    esperando una celda que no existe). Ver el chequeo hay_tramos_reales
    en crear_tramo().
  - El campo Valor del modal de Tramos, al modificar un tramo EXISTENTE
    (no uno recien creado), puede mostrar un valor "mezclado" entre el
    valor viejo y el nuevo (ej. escribir 4444.44 sobre un tramo que tenia
    3333.33 dejo "3,333.33444444" en la grilla) PESE a hacer Control+A +
    Delete antes de escribir - reproducido tambien a mano por el usuario
    SIN el bug (quedo limpio), asi que es sospecha de bug de
    AUTOMATIZACION (limpieza de campo insuficiente en ese input puntual),
    no un defecto real de la app. Investigar mas si vuelve a aparecer.
  - Notificacion automatica al equipo GTE (email, SistemaGrupo=GTE,
    ItemGrupo=CAMBTAR, CorreoRemitente=ActualizacionPrecios@luzdelsur.com.pe)
    y el insert en la bitacora de auditoria (tabla audit) NO son
    verificables solo por UI - documentar como [AVISO], no como fallo.

Requiere del framework compartido (web_lds_core.py, ya inyectado en la
plantilla de cada proyecto via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
Y la constante SELECTOR_DIALOGO (".mdl-confirmar, nz-modal-container,
.ant-modal-wrap") ya presente en generate_scripts.py de cada proyecto -
candidata a subir tambien a web_lds_core.py, es igual de generica.
============================================================================
"""

import re
from playwright.sync_api import TimeoutError as PWTimeoutError


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
