"""
Modulo: Seguimiento De Clientes Mt (Web LDS)
Proyecto donde se confirmo: PR000335-SP5 (pausado 15/09/2026, primera
tanda de casos - RF-01 de ese sprint).
Componente Angular: app-seguimiento-de-clientes-mt
Ruta de menu confirmada en vivo: Comercial > Atención Integral Al
Cliente > Seguimiento De Clientes Mt (item HOJA directo, un solo popup
por click - a diferencia de PR000335-SP2, no hace falta abrir
"Atenciones A Clientes" primero ni el _abrir_popup_por_titulo custom;
alcanza el abrir_aplicacion() generico del framework).

Ficha tecnica (confirmado en vivo, 15/09/2026):
Filtros con ids reales (ver SC_ID): Area, SST, Expediente, Asignado,
Tipo Fecha, Desde, Hasta. Boton "Buscar [F6]" real: class=matf-btn-buscar
(sin id propio).

Defaults confirmados: Desde = hoy menos 1 mes, Hasta = hoy. Tipo Fecha
llega preseleccionado en "Fecha Creacion" (value=1); las 3 opciones
reales del combo son "Fecha Creacion", "Fecha Asignacion", "Fecha Sig.
Seguimiento".

**PENDIENTE / dato con el que seguir:** con Area="Fonoluz" (unica opcion
disponible para el usuario DCABA_DW) y el rango de fecha por defecto, la
busqueda dio "Registros: 0" en la exploracion en vivo - no se confirmo
todavia un filtro (otra Area, otro rango) que traiga resultados reales.
Cualquier caso que necesite verificar el CONTENIDO de una fila (no solo
que la busqueda responda) esta bloqueado hasta encontrar ese dato.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
"""


def abrir_seguimiento_clientes_mt(page, paso_excel=1):
    return abrir_aplicacion(page, ["Comercial", "Atención Integral Al Cliente", "Seguimiento De Clientes Mt"], "app-seguimiento-de-clientes-mt", paso_excel=paso_excel)


SC_ID = {
    "Area": "sc-area",
    "SST": "sc-sst",
    "Expediente": "sc-exp",
    "Asignado": "sc-asig",
    "Tipo Fecha": "sc-tipo-fecha",
    "Desde": "sc-desde",
    "Hasta": "sc-hasta",
}


def campo_seguimiento(frame, etiqueta):
    return frame.locator(f"#{SC_ID[etiqueta]}")


def buscar_seguimiento(frame):
    """Boton 'Buscar [F6]' real: class=matf-btn-buscar (sin id propio)."""
    frame.locator("button.matf-btn-buscar").click()
