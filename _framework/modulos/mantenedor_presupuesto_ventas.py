"""
Modulo: Mantenedor De Presupuesto De Ventas (Web LDS)
Familia ADMTARIF, proyecto viejo PR000325 Sprint 2
(C:\\Proyectos\\PlataformaWeb\\automation\\PR000325\\).
Ruta de menu: Interno > Mantenedor De Presupuesto De Ventas
Componente Angular: app-presupuesto-ventas-list

**Confianza: MEDIA-ALTA.** Confirmado en vivo: navegacion, campos
`formAnioMes`/`formTarifa` (SI tienen atributo name, a diferencia del
resto de la familia), resto de campos via campo_por_etiqueta(), botones
Ingresar/Modificar/Eliminar. **Ojo:** en la exploracion en vivo NO se vio
un boton "Cancelar" visible en ningun estado del formulario - CP039
ASUME que existe en algun estado no explorado; confirmar antes de dar
por definitivo ese caso puntual.

Mismo patron de dialogos que el resto de la familia ADMTARIF - ver ficha
tecnica completa en actualizacion_claves_tarifas.py.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
Y los 4 helpers GENERICOS de este proyecto viejo: campo_por_etiqueta,
dialogo_visible, confirmar, boton_grabar.
"""


def abrir_mantenedor_presupuesto_ventas(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Mantenedor De Presupuesto De Ventas"], "app-presupuesto-ventas-list", paso_excel=paso_excel)
