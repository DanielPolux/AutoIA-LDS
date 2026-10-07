"""
Modulo: Mantenimiento de Carteras (Web LDS)
Componente Angular: app-carteras
Ruta de menu confirmada en vivo: Comercial > Mantenimiento De Carteras
Sistema/frente de negocio: Retiro y Castigo de Clientes

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP1, 25/09/2026)
============================================================================

Pantalla ng-zorro/Ant Design: ABM de carteras (codigo "OT" + proveedor
asociado). Boton "Ingresar" abre el formulario (input `#cartera` para el
codigo, select `#proveedor` con opciones `nz-option-item`/
`.ant-select-item-option`). "Ingresar"/"Modificar"/"Anular" piden
confirmacion via `.ant-modal`/`nz-modal-container` ("¿Esta
seguro/sera ingresada/modificada?").

**Bug real de framework (ya generico a varias pantallas ant-design de
este proyecto): el toast de exito se autodesvanece rapido.** El mensaje
("Cartera creada/modificada/anulada exitosamente.") se AUTODESVANECE en
pocos segundos (a diferencia de "Traslado de Clientes", que usa un
popover `.conf-btn-ok` persistente) - leer `body.inner_text()` despues
de esperas largas (networkidle + pausas de sobra) lo pierde SIEMPRE,
dando un falso FALLO aunque la operacion SI funciono (confirmado
revisando la grilla: la cartera quedaba creada igual). Solucion:
`confirmar_y_leer_resultado_cartera()` lee el texto INMEDIATAMENTE
(~1s) tras cerrar el dialogo de confirmacion, antes de que el toast
tenga chance de desvanecerse. Si la operacion es rechazada en cambio,
aparece una SEGUNDA ventana ("Ventana de Validacion", con su propio
boton Aceptar) que NO se autodesvanece.

**La grilla NO se refresca sola** tras Ingresar/Modificar/Anular
(confirmado en vivo: sigue mostrando los mismos registros de antes) -
`recargar_carteras()` recarga el popup entero para forzar un fetch
nuevo. Tras llamarla, hay que volver a obtener `frame` con
`app.locator("#aplicacion").content_frame`.

**Grilla sin buscador (59+ paginas reales) y con orden ASCII, no
numerico**: la grilla "Carteras registradas" ordena por string ASCII
(confirmado en vivo: "01.03" < "04.06" < "1 PRUE" < "10.12" < "12") y no
tiene campo de busqueda/filtro. `generar_codigo_ot()` genera un codigo
con prefijo "00" a proposito para que caiga siempre en la pagina 1 tras
recargar. Aun asi, si se acumulan suficientes carteras de prueba con el
mismo patron en la misma sesion, un codigo "00xxxx" puede dejar de
aparecer en la pagina 1 - usar SIEMPRE `buscar_fila_en_paginas_carteras()`
(pagina hasta encontrar) en vez de asumir pagina 1, incluso para
registros "recien creados".

Requiere del framework compartido (web_lds_core.py, ya inyectado en la
plantilla de cada proyecto via los bloques NAV / HELPERS_ESPERA):
`abrir_aplicacion`. Y del bloque de helpers genericos del proyecto:
`boton_por_texto(frame, texto)` (buscar un `<button>` por texto exacto).
============================================================================
"""

import re
import time
from playwright.sync_api import TimeoutError as PWTimeoutError


def abrir_mantenimiento_carteras(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Mantenimiento De Carteras"], "app-carteras", paso_excel=paso_excel)


def generar_codigo_ot():
    """Genera un codigo de Orden de Trabajo de 6 caracteres, unico por
    timestamp. Prefijo "00" a proposito: la grilla "Carteras registradas"
    ordena por string ASCII y NO tiene campo de busqueda/filtro (59+
    paginas reales) - "00xxxx" siempre cae en la pagina 1 tras recargar,
    evitando tener que paginar para encontrar una cartera recien creada."""
    return f"00{int(time.time()) % 10000:04d}"


def click_ingresar_cartera(frame):
    boton_por_texto(frame, "Ingresar").click()


def completar_ot_proveedor(app, frame, ot, indice_proveedor=0):
    frame.locator("#cartera").fill(ot)
    app.wait_for_timeout(400)
    frame.locator("#proveedor").click()
    app.wait_for_timeout(800)
    opciones = frame.locator("nz-option-item, .ant-select-item-option")
    opciones.nth(indice_proveedor).click()
    app.wait_for_timeout(400)


def confirmar_y_leer_resultado_cartera(app, frame):
    """Cierra el dialogo de confirmacion ("Esta seguro/sera ingresada/
    modificada?", clase .ant-modal/nz-modal-container) y devuelve el
    resultado real.

    BUG REAL confirmado en vivo: el toast de exito ("Cartera creada/
    modificada/anulada exitosamente.") se AUTODESVANECE en pocos
    segundos (a diferencia de Traslado de Clientes, que usa un popover
    .conf-btn-ok persistente) - leer `body.inner_text()` despues de
    esperas largas (networkidle + pausas de sobra) lo pierde siempre,
    dando un falso FALLO aunque la operacion SI funciono (confirmado
    revisando la grilla: la cartera quedaba creada igual). Por eso esta
    funcion lee el texto INMEDIATAMENTE (espera corta, ~1s) tras cerrar
    el dialogo de confirmacion, antes de que el toast tenga chance de
    desvanecerse.

    Si en cambio la operacion es rechazada, aparece una SEGUNDA ventana
    ("Ventana de Validacion", con su propio boton Aceptar) que NO se
    autodesvanece - si se detecta, se cierra y se devuelve SU texto en su
    lugar (mas especifico que el mensaje generico de exito)."""
    dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(r".", re.S))
    dialogo.first.wait_for(state="visible", timeout=8000)
    dialogo.first.get_by_role("button", name=re.compile(r"^Aceptar$|^S[ií]$", re.I)).first.click()
    app.wait_for_timeout(1000)
    mensaje = frame.locator("body").inner_text()

    segunda = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(r".", re.S))
    if segunda.count() > 0 and segunda.first.is_visible():
        mensaje = segunda.first.inner_text()
        segunda.first.get_by_role("button", name=re.compile(r"^Aceptar$", re.I)).first.click()
        app.wait_for_timeout(500)

    try:
        app.wait_for_load_state("networkidle", timeout=8000)
    except PWTimeoutError:
        pass
    return mensaje


def leer_mensaje_resultado_cartera(frame):
    return frame.locator("body").inner_text()


def recargar_carteras(app):
    """La grilla NO se refresca sola tras Ingresar/Modificar/Anular
    (confirmado en vivo: sigue mostrando los mismos registros de antes) -
    recargar el popup entero fuerza un CargarDatos nuevo. Tras llamar a
    esto, hay que volver a obtener `frame` con
    app.locator("#aplicacion").content_frame."""
    app.reload()
    app.wait_for_load_state("networkidle", timeout=20000)
    app.wait_for_timeout(2000)


def buscar_fila_en_paginas_carteras(app, frame, codigo, max_paginas=65):
    """Esta grilla no tiene buscador/filtro (59+ paginas reales) - recorre
    paginas con "Pagina siguiente" hasta encontrar `codigo` o llegar al
    final. Devuelve el locator de la fila (ya en la pagina donde esta
    visible) o None si no se encontro."""
    boton_siguiente = frame.locator("li.ant-pagination-next button")
    for _ in range(max_paginas):
        fila = frame.locator("nz-table tbody tr:not(.ant-table-measure-now)").filter(has_text=codigo)
        if fila.count() > 0:
            return fila.first
        if boton_siguiente.get_attribute("disabled") is not None:
            return None
        boton_siguiente.click()
        app.wait_for_timeout(600)
    return None
