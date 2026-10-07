"""
Modulo: Anulacion de Facturas (Web LDS)
Componente Angular: app-anulamiento-factura
Ruta de menu confirmada en vivo: Comercial > Anulacion De Facturas
  (OJO: el EF/ET de origen la llama "Anulamiento de Facturas" - el
  nombre real del menu NO coincide, confirmado en vivo)
Sistema/frente de negocio: Retiro y Castigo de Clientes

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP1, 26/09/2026)
============================================================================

Pantalla ng-zorro/Ant Design. Input de cliente (primer `<input>` de la
pantalla) + boton "Leer" -> carga facturas anulables, refacturaciones y
totales del cliente. Mensaje de rechazo confirmado EXACTO para cliente
en estado invalido: "Cliente no está retirado o en cobranza externa."

**Dependencia fuerte de datos reales de facturacion**: a diferencia de
la mayoria de pantallas de este sistema, esta SI depende de datos de
facturacion reales que no se pueden fabricar via UI (transiciones de
estado de cliente no alcanzan para generar facturas anulables). Si el
ambiente de Pruebas no tiene ningun cliente con facturas anulables
reales, los casos de anulacion/reversion/calculo de IGV/exclusion de
consumos quedan bloqueados por falta de dato, no por un bug de
automatizacion - confirmar esto probando varios numeros de cliente
reales antes de asumir un problema de script.
============================================================================
"""

import re
from playwright.sync_api import TimeoutError as PWTimeoutError


def abrir_anulacion_facturas(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Anulacion De Facturas"], "app-anulamiento-factura", paso_excel=paso_excel)


def consultar_cliente_facturas(app, frame, numero):
    frame.locator("input").first.fill(numero)
    app.wait_for_timeout(300)
    frame.locator("button", has_text=re.compile(r"^\s*Leer\s*$")).click()
    app.wait_for_timeout(1500)


def cerrar_dialogo_anulacion_facturas(app, frame, timeout_ms=3000):
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
