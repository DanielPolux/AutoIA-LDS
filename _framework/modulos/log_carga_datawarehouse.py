"""
Modulo: Log de Carga de Datawarehouse (Web LDS)
Componente Angular: app-log-carga
Ruta de menu confirmada en vivo: Comercial > Log De Carga De Datawarehouse
Sistema/frente de negocio: Aprobacion de Informes del Datawarehouse

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP1, 26/09/2026)
============================================================================

Pantalla Angular simple: 2 `<select>` (Proceso - 12 opciones fijas +
"(Todos)", Etapa - se recalcula segun el Proceso), 2 `<input type=date>`
NATIVOS del navegador (Desde/Hasta) + boton "Buscar" -> grilla "LOG DE
CARGA" (`table.g`); al hacer click en una fila carga la grilla "ETAPAS
DEL PROCESO" (2do `table.g`).

**Campo Fecha defensivo, variante NATIVA**: el `<input type=date>`
propio del navegador RECHAZA cualquier texto no valido tecleado (queda
vacio, sin dialogo ni mensaje) - la busqueda corre igual con el campo
vacio, sin bloquear la pantalla. "Fecha inicial no válida."/"Fecha
final no válida." de la matriz/EF no son alcanzables via UI real por
este motivo (mismo patron defensivo de campo Fecha ya visto en otras
pantallas del proyecto, pero aca resuelto a nivel de navegador en vez de
por logica Angular).

**Datos de prueba (tablas `etl_log_carga_cli` / `etl_log_etapa_cli`)**:
confirmado en vivo que la tabla de logs puede estar COMPLETAMENTE VACIA
en un ambiente de Pruebas (probados los 12 procesos con un rango de 11
años, la API `ConsultarLogCarga` siempre devolvio `[]`) - en ese caso,
todo caso que dependa de que EXISTA al menos un registro (consultar,
filtrar, ver orden, ver detalle de etapas) queda bloqueado hasta que se
inserte data real. Un registro insertado en `etl_log_carga_cli` SIN
ninguna fila correspondiente en `etl_log_etapa_cli` sirve para probar el
escenario "registro sin detalle de etapas" (la grilla de etapas debe
quedar vacia al seleccionarlo).
============================================================================
"""

import re


def abrir_log_carga_datawarehouse(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Log De Carga De Datawarehouse"], "app-log-carga", paso_excel=paso_excel)


def buscar_log_carga(app, frame):
    frame.get_by_role("button", name=re.compile("Buscar")).click()
    app.wait_for_timeout(1200)
