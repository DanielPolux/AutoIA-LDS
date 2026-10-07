"""
Modulo: Listados de Facilidad de Pago por Deuda de Energia (Web LDS)
Componente Angular: app-listado-convenios-deuda
Ruta de menu confirmada en vivo: Comercial > Listados De Facilidades De
  Pago Por Deuda De Energía
Sistema/frente de negocio: Convenios de Pago

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP1, 26/09/2026)
============================================================================

Pantalla simple: radio Vigentes ("V") / Cancelados y Revocados ("CT"),
campo Fecha (`input[placeholder="Seleccionar fecha"]`), boton "Generar"
-> descarga directa de un informe XLSX (sin grilla intermedia en
pantalla). El mensaje "No existen registros para el requerimiento."
aparece como banner INLINE (no dialogo `.ant-modal`) - se lee de
`body.inner_text()` directo. El mensaje de exito real es "Listado
generado."

**Campo Fecha defensivo** (mismo patron que otras pantallas del
proyecto): fecha en blanco O fecha futura ambas terminan usando la fecha
de hoy al pulsar "Generar" - no es posible provocar un mensaje de
rechazo de fecha invalida via UI real.

**Datos de prueba (tabla `conve`)**: sin un convenio real para el
cliente consultado, "Generar" siempre da "No existen registros para el
requerimiento." - necesita un INSERT en `conve` con `estado` = 'V'
(Vigentes) o 'C' (Cancelados/Revocados). **Verificar el esquema REAL de
la tabla antes de insertar** (`SELECT * FROM conve WHERE 1=0`): un
INSERT "ya validado en Desarrollo" puede referirse a un esquema
DISTINTO al del ambiente actual - confirmado en vivo que las columnas
`tasa_fija`/`id_tasa_convenio` ya no existen en esta version de la
tabla, y que las fechas deben construirse con `MDY(mes, dia, anio)` en
vez de string literal (`'01/01/2026'` fallo con "String to date
conversion error" por el `DBDATE` de la sesion Informix). El
`fecha_termino` de un convenio Cancelado debe coincidir EXACTAMENTE con
la fecha de corte que se ingrese en pantalla para que aparezca en la
consulta.

**Confirmado un caso puntual sin explicar del todo**: un convenio
Vigente insertado sin error a veces NO aparece en "Vigentes" pese a que
un convenio Cancelado (mismo cliente, mismo tipo de INSERT) SI aparecio
de inmediato - hipotesis sin confirmar: falta la columna real
`ind_caduca` (ausente del INSERT de referencia) o `saldo_origen`/
`deuda_convenida` en 0 no califican como "vigente" para la regla de
negocio real. Investigar esto primero si se retoma el escenario
"Vigentes" de este modulo.
============================================================================
"""

import re


def abrir_listado_facilidades_deuda_energia(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Listados De Facilidades De Pago Por Deuda De Energía"], "app-listado-convenios-deuda", paso_excel=paso_excel)


def generar_informe_facilidades(app, frame):
    frame.locator("button", has_text=re.compile(r"^\s*Generar\s*$")).click()
    app.wait_for_timeout(1500)
