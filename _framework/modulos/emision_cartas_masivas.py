"""
Modulo: Emision de Cartas Masivas (Web LDS)
Componente Angular: app-cartas-masivas
Ruta de menu confirmada en vivo: Comercial > Emisión De Cartas Masivas
Sistema/frente de negocio: Retiro y Castigo de Clientes

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP1, 26/09/2026)
============================================================================

Pantalla ng-zorro/Ant Design. **Al abrir la pantalla aparece SIEMPRE un
dialogo inicial** ("Ventana de Validacion": "No existen datos
registrados con su rol", sobre el Responsable) que hay que cerrar antes
de tocar cualquier otro control - si no se cierra, los siguientes clicks
(ej. "Agregar") quedan bloqueados por el modal (invisible pero aun
presente en el DOM). Campo cliente: `input[placeholder="Ej. 1002345"]` +
boton "Agregar". Datos del responsable: nombre (`input[maxlength="23"]`),
anexo (`input[maxlength="6"][inputmode="numeric"]`), celular
(`input[placeholder="9XXXXXXXX"]`). Los checkboxes "Carta Art. 90"/
"Carta Art. 178" vienen MARCADOS por defecto.

**Campo Fecha defensivo**: SIEMPRE revierte a la fecha de hoy si se
intenta dejar vacio o escribir texto invalido - no es posible provocar
"Fecha no es valida." via UI real (la pantalla se defiende antes de
llegar a esa validacion).

**Gotcha mas sutil confirmado en este proyecto: el toast de exito se
autodesvanece EXTREMADAMENTE rapido.** El mensaje ("Impresion finalizada
con exito.") NO usa dialogo `.ant-modal` (a diferencia de otras
pantallas del mismo sistema) - es un toast que desaparece tan rapido que
ni siquiera una pausa fija de 2000ms alcanza a leerlo (la captura de
pantalla en el momento del fallo ya no mostraba nada, el formulario ya
se habia reseteado, dando la falsa impresion de que la operacion fallo
cuando en realidad si funciono). Resuelto con un SONDEO en bucle corto
(`esperar_mensaje_exito_impresion`, cada 150ms hasta 4s) en vez de
cualquier pausa fija. El dialogo de rechazo de esta misma pantalla
("Error de Servicio") SI usa `.ant-modal`, pero con boton "Cerrar" en
vez de "Aceptar" - `cerrar_dialogo_cartas_masivas()` acepta ambos
textos (ademas de "Si").

**"Sin medidor activo" no es facilmente reproducible con un cliente
real**: un cliente con direccion/distrito reales completos genera carta
real igual aunque el campo "medidor" venga vacio (no excluye per se). No
se encontro la condicion exacta que la matriz describe para ese
escenario - usar un numero de cliente INEXISTENTE junto a uno valido en
el mismo lote logra el mismo efecto practico ("dato incompleto que no
debe bloquear al resto del lote").
============================================================================
"""

import re
import time
from playwright.sync_api import TimeoutError as PWTimeoutError


def abrir_emision_cartas_masivas(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Emisión De Cartas Masivas"], "app-cartas-masivas", paso_excel=paso_excel)


def cerrar_dialogo_cartas_masivas(app, frame, timeout_ms=3000, timeout_aparicion_ms=1500):
    """Cierra cualquier dialogo visible (.ant-modal/nz-modal-container) -
    usa Aceptar, Cerrar o Si segun cual tenga (confirmado en vivo: esta
    pantalla usa "Cerrar" para su dialogo de error de servicio, distinto
    de "Aceptar" en otras pantallas del mismo sistema). Espera un poco a
    que aparezca antes de descartar que hay uno - confirmado en vivo: el
    dialogo inicial ("No existen datos registrados con su rol") puede
    tardar en renderizar, y un chequeo inmediato sin esperar lo pasaba
    por alto, dejando ese dialogo bloqueando el siguiente click (ej.
    "Agregar" nunca llegaba a agregar nada)."""
    dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(r".", re.S))
    try:
        dialogo.first.wait_for(state="visible", timeout=timeout_aparicion_ms)
    except PWTimeoutError:
        return None
    texto = dialogo.first.inner_text()
    try:
        dialogo.first.get_by_role("button", name=re.compile(r"^Aceptar$|^Cerrar$|^S[ií]$", re.I)).first.click(timeout=timeout_ms)
        app.wait_for_timeout(500)
    except PWTimeoutError:
        pass
    return texto


def agregar_cliente_carta(app, frame, numero):
    frame.locator('input[placeholder="Ej. 1002345"]').fill(numero)
    app.wait_for_timeout(400)
    frame.locator("button", has_text=re.compile(r"^\s*Agregar\s*$")).click()
    app.wait_for_timeout(1000)


def completar_responsable_carta(frame, nombre="PRUEBA AUTOMATIZADA", anexo="1234", celular="987654321"):
    frame.locator('input[maxlength="23"]').fill(nombre)
    frame.locator('input[maxlength="6"][inputmode="numeric"]').fill(anexo)
    frame.locator('input[placeholder="9XXXXXXXX"]').fill(celular)


def esperar_mensaje_exito_impresion(app, frame, timeout_ms=4000, intervalo_ms=150):
    """El mensaje de exito ("Impresion finalizada con exito.") NO usa
    dialogo .ant-modal - es un toast que se autodesvanece MUY rapido
    (confirmado en vivo: hasta 2000ms de espera fija ya lo perdia
    siempre, la captura de pantalla en el momento del fallo ya no
    mostraba nada). Sondea el texto del body cada `intervalo_ms` en vez
    de una espera fija, devolviendo apenas aparece la frase esperada (o
    el ultimo texto visto, si nunca aparecio, para poder diagnosticar)."""
    plazo = time.monotonic() + timeout_ms / 1000
    ultimo = ""
    while time.monotonic() < plazo:
        ultimo = frame.locator("body").inner_text()
        if "impresion finalizada" in ultimo.lower():
            return ultimo
        app.wait_for_timeout(intervalo_ms)
    return ultimo
