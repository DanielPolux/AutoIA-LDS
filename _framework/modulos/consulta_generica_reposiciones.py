"""
Modulo: Consulta Generica de Solicitudes de Reposicion (Web LDS)
Componente Angular: app-consulta-generica-reposiciones
Ruta de menu confirmada en vivo: Comercial > Consulta Generica De Solicitudes De Reposicion
Sistema/frente de negocio: Reposiciones (recauda/CONSUREP)

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP2, 28/09/2026)
============================================================================

Pantalla ng-zorro/Ant Design. Filtros: N.° de Cliente (`#fldCliente`),
Sector (`#fldSector`), Sucursal Cliente (`nz-select#fldSucursal`), N.°
Solicitud (`#fldSolicitud`), Estado Solicitud (`nz-select#fldEstado`),
tipo de filtro de fecha OBLIGATORIO (`nz-select#fldTipoFecha`: "=",
"Entre") + Fecha Inicial (`#fldFechaIni`, con calendario `nz-date-picker`
asociado) / Fecha Final (solo visible con "Entre"). Botones Leer /
Limpiar / "a Excel" (deshabilitado hasta tener resultado).

**Mensajes reales confirmados** (via "Ventana de Validacion" modal,
`.ant-modal`/`nz-modal-container`, icono "i", boton "Aceptar"):
- "Debe Seleccionar Filtro de Fechas" (RN-07, ningun tipo de fecha elegido)
- "Fecha Inválida" (RN-06, fecha con valor calendario inexistente)
- "Debe Seleccionar Rango Inferior de Fecha" (RN-08, tipo elegido sin fecha inicial)

**DEFECTO REAL CRITICO, confirmado en 2 PANTALLAS DISTINTAS del mismo
proyecto (ver tambien `consulta_cortes_pendientes.py`): ingresar una
fecha calendario VALIDA en cualquier campo de fecha de este tipo
(`nz-date-picker` + input asociado) congela la pantalla por completo.**
Reproducido aca con `press_sequentially` normal Y con delay de 300ms por
caracter (descarta que sea un artefacto de automatizacion "demasiado
rapida" - el freeze ocurre incluso escribiendo lento, a mitad de la
cadena de caracteres). Sintoma identico al de RF-07: cualquier operacion
posterior sobre el popup (`screenshot()`, etc.) cuelga 30s+ sin
excepcion de JS, sin error de consola, sin dialogo nativo. Una fecha
INVALIDA o el campo vacio NO producen el freeze (validan rapido). Dado
que se reproduce IGUAL en 2 aplicativos Angular distintos (con
estructura de date-picker ligeramente distinta en el HTML), es probable
que sea un defecto compartido de una libreria/version de componente
comun a varias pantallas de este sprint - **cualquier caso que necesite
ingresar una fecha calendario real y valida en un filtro de este tipo
queda bloqueado hasta que se resuelva en el ambiente.**
============================================================================
"""

import re
import time
from playwright.sync_api import TimeoutError as PWTimeoutError


def abrir_consulta_generica_reposiciones(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Consulta Generica De Solicitudes De Reposicion"], "app-consulta-generica-reposiciones", paso_excel=paso_excel)


def elegir_select_reposiciones(app, frame, select_id, texto_opcion=None):
    """Si texto_opcion es None, elige la primera opcion real disponible
    (util para 'tipo de fecha' cuando cualquier valor sirve, ej. '=')."""
    frame.locator(f"#{select_id}").click()
    app.wait_for_timeout(500)
    opciones = frame.locator(".ant-select-item-option")
    if texto_opcion is None:
        opciones.first.click()
    else:
        opciones.filter(has_text=texto_opcion).first.click()
    app.wait_for_timeout(400)


def cerrar_ventana_validacion_reposiciones(app, frame, timeout_ms=4000):
    dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(r".", re.S))
    try:
        dialogo.first.wait_for(state="visible", timeout=timeout_ms)
    except PWTimeoutError:
        return None
    texto = dialogo.first.inner_text()
    dialogo.first.get_by_role("button", name=re.compile("Aceptar", re.I)).first.click()
    app.wait_for_timeout(500)
    return texto


def leer_reposiciones(app, frame):
    frame.get_by_role("button", name=re.compile("Leer")).click()
    app.wait_for_timeout(1200)
