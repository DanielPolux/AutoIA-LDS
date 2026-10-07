"""
Modulo: Consulta de Movimientos de Saldos (Web LDS)
Componente Angular: app-consulta-movimientos
Ruta de menu confirmada en vivo: Comercial > Consulta De Movimientos De Saldos
Sistema/frente de negocio: Cuadratura de Saldos (distinto de "Retiro y
  Castigo de Clientes")

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP1, 26/09/2026)
============================================================================

Pantalla ng-zorro/Ant Design, pero con grillas HTML planas (`<table
class="g">`, NO `nz-table`) - sin el problema de fila fantasma de otras
pantallas del proyecto. Filtros: Fecha Inicio/Fin
(`input[placeholder="Seleccionar fecha"]`), Tipo de Movimiento, Estado
(radios, ej. `label[nzvalue="R"]` = Retirado), checkboxes "Agrupar por
Sucursal/Sector/Zona". Boton "Consultar" -> "Resumen de Movimientos"
(con boton "Copiar" propio) y, al seleccionar una fila del resumen,
"Detalle" (grilla propia, tambien con boton "Copiar").

**Gotcha real, distinto de otras pantallas del proyecto: el panel
ENTERO de filtros queda DESHABILITADO tras cada "Consultar"** (no solo
el campo tocado) hasta pulsar "Limpiar" - hay que limpiar entre
consultas sucesivas dentro del mismo caso, a diferencia de "Anulacion de
Facturas" donde solo el campo cliente se bloqueaba.

**Los botones "Copiar" (Resumen y Detalle) copian al portapapeles un TSV
con headers** - confirmado leyendo `navigator.clipboard.readText()`
tras conceder permisos al contexto
(`context.grant_permissions(["clipboard-read", "clipboard-write"])`).

**La pantalla es mas permisiva que lo que describe la matriz/EF en
varios escenarios de fecha vacia**: dejar Desde o Hasta vacio NO
bloquea la consulta (corre igual, "Sin registros" si no hay datos, sin
ningun mensaje de validacion) - confirmar SIEMPRE en vivo antes de
asumir que un mensaje "Debe ingresar fecha de..." es alcanzable. El
rango invertido (Hasta anterior a Desde) SI se valida, con el mensaje
exacto: "Fecha de inicio no debe ser mayor a fecha de término."

**Datos de prueba (tabla `cuadra_saldo`)**: la grilla de Resumen queda
vacia para cualquier rango de fechas si no hay filas reales en
`cuadra_saldo` para la empresa/periodo consultado - un INSERT minimo
(sucursal/sector/zona fijos, un tipo de movimiento, fecha_movimiento =
hoy) es suficiente para que aparezca de inmediato.
============================================================================
"""

import re
from playwright.sync_api import TimeoutError as PWTimeoutError


def abrir_consulta_movimientos_saldos(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Consulta De Movimientos De Saldos"], "app-consulta-movimientos", paso_excel=paso_excel)


def llenar_fecha_movimientos(app, frame, indice, valor):
    campo = frame.locator('input[placeholder="Seleccionar fecha"]').nth(indice)
    campo.click()
    app.wait_for_timeout(300)
    campo.fill(valor)
    frame.locator("body").press("Enter")
    app.wait_for_timeout(300)
    frame.locator("body").press("Escape")
    app.wait_for_timeout(300)


def limpiar_filtros_movimientos(frame):
    frame.locator("button", has_text=re.compile(r"^\s*Limpiar\s*$")).click()


def consultar_movimientos(app, frame):
    frame.locator("button", has_text=re.compile(r"^\s*Consultar\s*$")).click()
    app.wait_for_timeout(1500)


def cerrar_dialogo_movimientos(app, frame, timeout_ms=3000):
    dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(r".", re.S))
    if dialogo.count() == 0 or not dialogo.first.is_visible():
        return None
    texto = dialogo.first.inner_text()
    try:
        dialogo.first.get_by_role("button", name=re.compile(r"^Aceptar$|^Cerrar$", re.I)).first.click(timeout=timeout_ms)
        app.wait_for_timeout(500)
    except PWTimeoutError:
        pass
    return texto
