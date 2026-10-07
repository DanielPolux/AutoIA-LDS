"""
Modulo: Asignacion de Clientes a Carteras (Web LDS)
Componente Angular: app-asignacion-carteras
Ruta de menu confirmada en vivo: Comercial > Asignacion De Clientes A Carteras
Sistema/frente de negocio: Retiro y Castigo de Clientes

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP1, 26/09/2026)
============================================================================

Pantalla ng-zorro/Ant Design. Selector de cartera tipo "buscar y elegir"
(`.cartera-select`, click para abrir, input de busqueda interno
`.ant-select-selection-search-input`, opciones `nz-option-item`/
`.ant-select-item-option`). Panel(es) con grillas identificadas por su
titulo visible (`.grid-panel` filtrado por texto).

**Gotcha real, distinto de Mantenimiento de Carteras/Traslado de
Clientes: "Asignar" NO muestra dialogo de confirmacion**, procesa
DIRECTO al click - confirmado en vivo (varios casos fallaron la 1ra vez
esperando un dialogo que nunca llega). No se confirmo si "Quitar" si lo
muestra - por eso `confirmar_dialogo_asignacion()` es TOLERANTE (si
aparece un dialogo lo cierra, si no aparece nada en unos segundos sigue
sin fallar), en vez de asumir que siempre hay uno.

**Ojo con el efecto colateral real**: si un caso choca esperando un
dialogo que nunca llega, el CLICK que disparo la accion YA SE EJECUTO -
el backend puede haber procesado el cambio de verdad aunque el script
termine en FALLO. Confirmado en vivo: un cliente quedo asignado de
verdad a una cartera en una corrida marcada como FALLO por este motivo,
dejando ese dato de prueba "quemado" (ya no elegible) para el siguiente
intento - si un caso vuelve a fallar tras corregir el timeout, sospechar
primero que el dato de prueba ya fue consumido por el intento anterior
antes de asumir un bug nuevo.

**La grilla NO se refresca sola** tras Agregar/Asignar/Quitar - hay que
RE-SELECCIONAR la cartera (dispara un nuevo fetch) para ver el estado
real, no confiar en lo que se ve inmediatamente despues de la accion.

**PENDIENTE-DUDA sin resolver** (anotado por si se repite en otro
modulo): una cartera con un cliente asociado confirmado desde el
mensaje de rechazo de "Traslado de Clientes" aparecio VACIA ("No hay
clientes asociados") al seleccionarla desde esta pantalla. Hipotesis sin
confirmar: los 2 endpoints (ValidarCliente/Trasladar de Traslado de
Clientes vs listar-clientes-asociados de esta pantalla) podrian leer de
tablas o vistas distintas, o aplicar un filtro adicional que el otro no
aplica. **Cuando dos pantallas parecen relacionadas por el mismo dato de
negocio (ej. "que cliente esta en que cartera"), preferir SIEMPRE la
pantalla que hace la consulta DIRECTAMENTE afectada como fuente de
verdad, no un mensaje/tabla cruzado de otra pantalla, por mas
relacionado que parezca.**
============================================================================
"""

import re
from playwright.sync_api import TimeoutError as PWTimeoutError


def abrir_asignacion_clientes_carteras(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Asignacion De Clientes A Carteras"], "app-asignacion-carteras", paso_excel=paso_excel)


def seleccionar_cartera_asignacion(app, frame, codigo):
    frame.locator(".cartera-select").click(timeout=20000)
    app.wait_for_timeout(700)
    frame.locator(".cartera-select input.ant-select-selection-search-input").fill(codigo)
    app.wait_for_timeout(1000)
    frame.locator("nz-option-item, .ant-select-item-option").filter(has_text=codigo).first.click()
    app.wait_for_timeout(2000)


def agregar_cliente_asignacion(frame, numero):
    frame.locator('input[placeholder="Máx. 7 dígitos"]').fill(numero)


def filas_panel_asignacion(frame, titulo_panel):
    panel = frame.locator(".grid-panel").filter(has_text=titulo_panel)
    return panel.locator("tbody tr:not(.ant-table-measure-now)")


def confirmar_dialogo_asignacion(app, frame, timeout_ms=4000):
    """Cierra el dialogo de confirmacion si aparece (mismo patron
    .ant-modal/nz-modal-container que otras pantallas del mismo sistema)
    - TOLERANTE a que no aparezca ninguno. Confirmado en vivo: a
    diferencia de otras pantallas, "Asignar" en esta NO muestra dialogo
    de confirmacion, procesa directo al click. No se confirmo aun si
    "Quitar" si lo muestra - por eso esta version no asume ninguno de los
    2 casos, simplemente sigue si no aparece nada."""
    dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(r".", re.S))
    try:
        dialogo.first.wait_for(state="visible", timeout=timeout_ms)
    except PWTimeoutError:
        return False
    dialogo.first.get_by_role("button", name=re.compile(r"^Aceptar$|^S[ií]$", re.I)).first.click()
    app.wait_for_timeout(1500)
    return True
