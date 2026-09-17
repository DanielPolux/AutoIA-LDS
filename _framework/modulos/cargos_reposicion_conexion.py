"""
Modulo: Cargos De Reposición De Conexión (Web LDS)
Familia ADMTARIF, proyecto viejo PR000325 Sprint 2
(C:\\Proyectos\\PlataformaWeb\\automation\\PR000325\\).
Ruta de menu: Interno > Cargos De Reposición De Conexión
Selector de pantalla confirmado en vivo: text=Cargos de Reposición de Conexión

**Confianza: MEDIA-BAJA.** Los selectores del LISTADO estan confirmados
en vivo, pero los botones Aceptar/Cancelar del FORMULARIO DE DETALLE (al
Agregar/Modificar un precio) estan tomados solo de la Especificacion
Funcional, NO confirmados en vivo (la exploracion en vivo solo mostro
Agregar/Modificar/Eliminar a nivel de grilla, nunca se abrio el detalle)
- revisar antes de dar por definitivos los casos que dependen de ese
formulario de detalle.

Mismo patron de UI/dialogos que el resto de la familia ADMTARIF - ver
ficha tecnica completa en actualizacion_claves_tarifas.py.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
Y los 4 helpers GENERICOS de este proyecto viejo: campo_por_etiqueta,
dialogo_visible, confirmar, boton_grabar.
"""


def abrir_cargos_reposicion_conexion(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Cargos De Reposición De Conexión"], "text=Cargos de Reposición de Conexión", paso_excel=paso_excel)
