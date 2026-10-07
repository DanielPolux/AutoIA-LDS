"""
Modulo: Investigacion de Clientes (Web LDS)
Componente Angular: app-clientes-investigar
Ruta de menu confirmada en vivo: Comercial > Investigacion De Clientes
  (OJO: el EF/ET de origen la llama "Clientes a Investigar" - el nombre
  real del menu NO coincide, confirmado en vivo)
Sistema/frente de negocio: Retiro y Castigo de Clientes

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP1, 26/09/2026)
============================================================================

Pantalla ng-zorro/Ant Design. Selector de cartera (`.sel-cartera`, mismo
patron "buscar y elegir" que Asignacion de Clientes a Carteras) + boton
"Leer / Consultar" (texto exacto con espacios alrededor de la barra) ->
grilla de clientes de la cartera (`nz-table tbody tr`, filtrar la fila
fantasma `.ant-table-measure-now`). Cada fila tiene un checkbox para
marcar el cliente antes de pulsar "A Investigar" / "Normalizar".

**Gotcha real: los botones de accion quedan REALMENTE deshabilitados
(atributo `disabled`, no solo estilo) mientras no haya ninguna fila
marcada** - confirmado en vivo que esto NO es un bug de reactividad
(se probo explicitamente marcar y desmarcar, el boton se re-deshabilita
correctamente). Un caso que espera un mensaje de advertencia al pulsar
el boton "sin seleccion" nunca lo va a ver porque el click ni siquiera
llega a dispararse - verificar el atributo `disabled` en vez de intentar
el click y esperar un mensaje que no existe.
============================================================================
"""

import re


def abrir_investigacion_clientes(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Investigacion De Clientes"], "app-clientes-investigar", paso_excel=paso_excel)


def seleccionar_cartera_investigacion(app, frame, codigo):
    frame.locator(".sel-cartera").click(timeout=20000)
    app.wait_for_timeout(700)
    frame.locator(".sel-cartera input.ant-select-selection-search-input").fill(codigo)
    app.wait_for_timeout(1000)
    frame.locator("nz-option-item, .ant-select-item-option").filter(has_text=codigo).first.click()
    app.wait_for_timeout(1000)


def leer_clientes_investigacion(app, frame):
    frame.locator("button", has_text=re.compile(r"^\s*Leer\s*/\s*Consultar\s*$")).click()
    app.wait_for_timeout(1500)


def fila_cliente_investigacion(frame, numero):
    return frame.locator("nz-table tbody tr:not(.ant-table-measure-now)").filter(has_text=numero)


def marcar_cliente_investigacion(frame, numero):
    fila = fila_cliente_investigacion(frame, numero)
    fila.locator('input[type="checkbox"]').click()
