"""
Modulo: Listados de Ingresos de CNR por Deuda de Servicios (Web LDS)
Componente Angular: app-listado-facilidades-no-deuda
Ruta de menu confirmada en vivo: Comercial > Listados De Ingresos De Cnr
  Por Deuda De Servicios
Sistema/frente de negocio: Convenios de Pago

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP1, 26/09/2026)
============================================================================

Pantalla IDENTICA en estructura a "Listados de Facilidad de Pago por
Deuda de Energia" (mismo sistema "Convenios de Pago"): radio Vigentes /
Cancelados y Revocados, campo Fecha, boton "Generar" -> descarga XLSX
directa, banner inline "No existen registros para el requerimiento."
Mismo patron defensivo de Fecha (blanco o futura -> usa la fecha de hoy
al pulsar Generar).

**Falso "defecto real de infraestructura" - LECCION IMPORTANTE**: en la
sesion de automatizacion de PR000349-SP1, esta app fallo con un error
CORS real en consola (endpoint interno `LanzarAplicativoDebug`, el
iframe `#aplicacion` nunca se creaba) 2 veces seguidas y se documento
como "defecto real de infraestructura, no transitorio", bloqueando 6
casos de prueba. Horas despues, en una sesion nueva, la MISMA app abrio
perfecto 3/3 veces sin ningun error. Era una falla TRANSITORIA del
backend (sobrecarga puntual), no un defecto reproducible. **No concluir
"defecto real" a partir de 2 fallos seguidos en la misma sesion corta -
reintentar en una sesion separada por horas antes de reportarlo como
defecto permanente.**

**Datos de prueba (tabla `fac_cli`)**: sin una facilidad real para el
cliente consultado, "Generar" siempre da "No existen registros para el
requerimiento." Igual que con `conve` (ver
`listado_facilidades_deuda_energia.py`), verificar el esquema REAL de
`fac_cli` (`SELECT * FROM fac_cli WHERE 1=0`) antes de correr cualquier
INSERT "ya validado en Desarrollo" - el esquema real del ambiente puede
haber cambiado.
============================================================================
"""

import re


def abrir_listado_ingresos_cnr_deuda_servicios(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Listados De Ingresos De Cnr Por Deuda De Servicios"], "app-listado-facilidades-no-deuda", paso_excel=paso_excel)


def generar_informe_cnr(app, frame):
    frame.locator("button", has_text=re.compile(r"^\s*Generar\s*$")).click()
    app.wait_for_timeout(1500)
