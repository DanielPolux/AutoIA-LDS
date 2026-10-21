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

**Datos de prueba (tablas `etl_log_carga_cli` / `etl_log_etapa_cli` /
`etl_log_carga_sif`)**: el hallazgo de "tabla completamente VACIA" de
IT1/IT2 (26/09 y 16/10/2026) fue DESCARTADO en IT3 (21/10/2026) -
confirmado con captura de red real que el servicio SI devuelve datos
(176 registros historicos reales 2026 + los sembrados por la matriz).
La causa real de "siempre devuelve []" en IT1/IT2 era otra, ver abajo.

**Buscar con TODOS los filtros vacios (Proceso=Todos, Etapa=Todos,
fechas vacias) NO FUNCIONA via UI real - y no es un simple "no-op"**:
confirmado en vivo dos veces de forma independiente (21/10/2026): la
sonda automatizada mostro 0 llamadas de red al backend (el boton
Buscar no dispara ConsultarLogCarga en absoluto con todo vacio), y el
usuario, probandolo a mano en el navegador real, confirmo que la
pantalla se queda colgada ("esperando") y al rato termina mostrando una
**Ventana de Error por timeout/espera** - mas grave que un simple no-op
silencioso. **Cualquier caso futuro que la matriz describa como
"sin filtros"/"fechas vacias" debe adaptarse a un Proceso especifico +
rango de fechas acotado** (igual resultado esperado - integra ambas
fuentes, cli y sif, en una sola lista - sin pasar por este camino roto).
No perder tiempo reintentando la busqueda literal sin filtros.
============================================================================
"""

import re


def abrir_log_carga_datawarehouse(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Log De Carga De Datawarehouse"], "app-log-carga", paso_excel=paso_excel)


def buscar_log_carga(app, frame):
    frame.get_by_role("button", name=re.compile("Buscar")).click()
    app.wait_for_timeout(1200)
