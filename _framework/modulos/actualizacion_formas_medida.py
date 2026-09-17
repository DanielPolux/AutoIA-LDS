"""
Modulo: Actualizacion De Formas De Medida (Web LDS)
Familia ADMTARIF, proyecto viejo PR000325 Sprint 2
(C:\\Proyectos\\PlataformaWeb\\automation\\PR000325\\).
Ruta de menu: Interno > Actualización De Formas De Medida
Selector de pantalla confirmado en vivo: text=Actualización de Formas de Medida
(sin componente Angular con selector propio identificado - se referencia
por texto visible).

**Confianza: MEDIA.** El patron de navegacion/selectores generico de la
familia ADMTARIF SI esta confirmado en vivo (ver
actualizacion_claves_tarifas.py), pero los cuerpos de caso puntuales de
este RF se generaron por patron a partir de la Especificacion Funcional
y NO se ejecutaron en vivo caso por caso - revisar/confirmar antes de
dar por definitivos, sobre todo la clave de demanda/fase real que usan
los casos de Leer (se referencia una combinacion existente conocida del
ambiente, confirmar que sigue vigente).

Mismo patron de UI/dialogos que el resto de la familia ADMTARIF - ver
ficha tecnica completa en actualizacion_claves_tarifas.py.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
Y los 4 helpers GENERICOS de este proyecto viejo: campo_por_etiqueta,
dialogo_visible, confirmar, boton_grabar.
"""


def abrir_actualizacion_formas_medida(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Actualización De Formas De Medida"], "text=Actualización de Formas de Medida", paso_excel=paso_excel)
