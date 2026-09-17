"""
Modulo: Actualizacion De Tasas De Interes (Web LDS)
Componente Angular: app-tasas-interes-list
Ruta de menu confirmada en vivo: Interno > Actualización De Tasas De Interés

Ficha tecnica (confirmado en vivo, PR000325-SP3, 16/09/2026):
"Ultima Fecha Registrada" (texto rojo, no editable) + "Fecha de
Vigencia" (<input type=date>, campo de consulta) + 8 campos de tasa
(TAMN/TIPMN Simple y Compuesta, Promedio TAMN-TIPMN, Legal Simple,
Promedio Compuesta, Promedio Simple) + boton "Ingresar" FIJO (NO alterna
a "Modificar" como otros aplicativos de este proyecto) + boton dual
Cerrar/Cancelar.

BUG REAL / precision confirmada en vivo: leer una fecha EXACTA (=Ultima
Fecha Registrada) no muestra asterisco en ningun campo pero SI un aviso
amarillo "Esta fecha es historica. Los campos estan en modo consulta."
(los inputs no quedan realmente `disabled` a nivel HTML pese al aviso -
si un caso necesita verificar "modo consulta", chequear el aviso, no
`is_disabled()`). Leer una fecha SIN registro exacto (futura o sin
historial) marca los 8 campos con un "*" (leyenda "* Tasa proyectada de
fecha anterior") y el boton dual cambia a "Cancelar".

Tasa Promedio TAMN-TIPMN se recalcula solo AL SALIR de TAMN o TIPMN
(evento blur, no oninput) - confirmado en vivo la formula: (TAMN + TIPMN)
/ 2, redondeado a 3 decimales.

GOTCHA confirmado en vivo (CP050/CP052, 17/09/2026): a pesar de que esta
ficha tecnica YA documentaba el formulario real de 8 campos y el modo
consulta historico desde el 16/09/2026, los casos igual fallaron por
IGNORARLA - usaron `inputs.nth(1)/nth(3)/nth(4)` posicional (que con 8
campos en 2 columnas NO caen donde se asume) y `date.today() + N dias`
en vez de leer "Ultima Fecha Registrada" en vivo. Cualquier caso nuevo
sobre este modulo DEBE:
  1. Usar `campo_por_etiqueta(frame, "Tasa TAMN (Interés Simple)")` /
     "Tasa TIPMN (Interés Simple)" / "Tasa Promedio TAMN - TIPMN" (etc,
     etiqueta COMPLETA) en vez de indices posicionales.
  2. Leer "Ultima Fecha Registrada" con
     `frame.get_by_text(re.compile(r"\d{2}/\d{2}/\d{4}")).first.inner_text()`
     (es texto plano, no un input) y usar una fecha con margen POR
     DELANTE de esa (ej. +30 dias), nunca un offset fijo desde
     `date.today()` - el sistema ya tiene datos cargados bastante mas
     adelante que "hoy" (confirmado con valores en 2027-2028) y cualquier
     fecha anterior a "Ultima Fecha Registrada" cae en modo consulta
     (ver parrafo de arriba).

Este aplicativo no tuvo helpers propios mas alla de abrir_* - los casos
usan directamente los helpers GENERICOS del proyecto (escribir_campo,
confirmar_si_no) sobre los inputs/campo_por_etiqueta de la pantalla.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
"""


def abrir_actualizacion_tasas_interes(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Actualización De Tasas De Interés"], "app-tasas-interes-list", paso_excel=paso_excel)
