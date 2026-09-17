"""
Modulo: Asignación De Libros A Contratistas (Web LDS)
Familia ADMTARIF, proyecto viejo PR000325 Sprint 2
(C:\\Proyectos\\PlataformaWeb\\automation\\PR000325\\).
Ruta de menu: Interno > Asignación De Libros A Contratistas
Componente Angular: app-asignacion-libro-list

**Confianza: MEDIA.** Navegacion + campos del formulario principal
confirmados en vivo (incluye `select[name="sector"]` y
`select[name="tipo"]`, que SI tienen atributo name). El modal "Copiar
Asignaciones" (usado por varios casos de este RF) NO se abrio en vivo -
sus selectores se tomaron solo de la Especificacion Funcional, marcados
ahi como "mejor esfuerzo" - confirmar en vivo antes de dar por
definitivos los casos que dependen de ese modal.

Mismo patron de dialogos que el resto de la familia ADMTARIF - ver ficha
tecnica completa en actualizacion_claves_tarifas.py.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
Y los 4 helpers GENERICOS de este proyecto viejo: campo_por_etiqueta,
dialogo_visible, confirmar, boton_grabar.
"""


def abrir_asignacion_libros_contratistas(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Asignación De Libros A Contratistas"], "app-asignacion-libro-list", paso_excel=paso_excel)
