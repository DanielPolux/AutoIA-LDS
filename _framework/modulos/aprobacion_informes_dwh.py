"""
Modulo: Aprobacion de Informes DWH (Web LDS)
Componente Angular: app-aprobacion-informes
Ruta de menu confirmada en vivo: Comercial > Aprobación De Informes Dwh
  (OJO: se confirmaron 2 entradas de menu DUPLICADAS con el mismo texto
  exacto "Aprobación De Informes Dwh" bajo Comercial - ambas abren esta
  misma pantalla igual de bien, no es un bug de seleccion de menu)
Sistema/frente de negocio: Aprobacion de Informes del Datawarehouse

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP1, 26/09/2026)
============================================================================

Pantalla Angular simple (sin ng-zorro): select Informe (4 opciones fijas:
Informe de Ventas / Liquidacion de IGV / Morosidad Semanal / Recaudacion
Semanal) + badge "Periodicidad: Mensual" (no editable) + select Mes /
input Año + boton "Leer" -> grilla de aprobaciones (`table.g`, confirmada
ordenada por fecha descendente con datos historicos reales) + botones
"Aprobar"/"Revocar".

**Gotcha real: select Mes e input Año quedan DESHABILITADOS hasta pulsar
"Leer"**, incluso DESPUES de elegir un Informe (confirmado en vivo: la
clase `ng-dirty` del select Informe muestra que Angular SI registro el
cambio, pero Mes/Año no se habilitan hasta la respuesta de "Leer").

"Aprobar" y "Revocar" (con fila seleccionada) piden confirmacion via
`.ant-modal` ("¿Desea aprobar el informe?" / "¿Desea eliminar la
aprobación del informe?"). **"Revocar" SIN fila seleccionada muestra un
dialogo DISTINTO** ("Ventana de Validación" con icono "i", texto EXACTO
"Debe seleccionar el informe.", boton "Aceptar") - no es un `.ant-modal`
de confirmacion, es un modal de validacion/aviso; el boton en si NO esta
deshabilitado (a diferencia del patron de "Investigacion de Clientes"),
valida recien al click.

**Falso "defecto real de infraestructura" - misma leccion que
`listado_ingresos_cnr_deuda_servicios.py`**: esta app fallo con el mismo
error CORS 2 veces seguidas en la sesion original (incluso habiendo
funcionado bien ANTES en la misma sesion) y se documento como defecto
permanente, bloqueando 6 casos. Horas despues abrio perfecto 3/3 veces.
Era transitorio. No concluir "defecto real" de 2 fallos seguidos en poco
tiempo.

**Buena practica de aislamiento al escribir casos de escritura**: usar
un informe poco tocado (ej. "Liquidacion de IGV", con historial real
2000-2014) y un periodo lejano a cualquier dato historico (ej. un mes/
año futuro sin uso) para Aprobar/Revocar de prueba, revocando la propia
aprobacion de prueba al final del caso para dejar el ambiente igual a
como estaba.
============================================================================
"""

import re
from playwright.sync_api import TimeoutError as PWTimeoutError


def abrir_aprobacion_informes_dwh(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Aprobación De Informes Dwh"], "app-aprobacion-informes", paso_excel=paso_excel)


def leer_aprobaciones(app, frame):
    frame.get_by_role("button", name=re.compile("Leer")).click()
    app.wait_for_timeout(1200)


def confirmar_dialogo_aprobacion(app, frame, timeout_ms=4000):
    dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(r".", re.S))
    try:
        dialogo.first.wait_for(state="visible", timeout=timeout_ms)
    except PWTimeoutError:
        return None
    texto = dialogo.first.inner_text()
    dialogo.first.get_by_role("button", name=re.compile(r"S[ií]|Aceptar|Confirmar", re.I)).first.click()
    app.wait_for_timeout(1200)
    return texto
