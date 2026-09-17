"""
Modulo: Mantenedor De Contratistas (Web LDS)
Familia ADMTARIF, proyecto viejo PR000325 Sprint 2
(C:\\Proyectos\\PlataformaWeb\\automation\\PR000325\\).
Ruta de menu: Comercial > Facturación > Facturación > Mantenedor De Contratistas
(distinta de las otras 5 apps de esta familia, que viven bajo "Interno").
Selector de pantalla: text=Mantenedor de Contratistas

**Confianza: BAJA - revisar antes de usar.** Los `name` de campos NO se
confirmaron en vivo: el menu "Comercial > Facturación > Facturación" fue
inestable durante la exploracion y no se pudo extraer el HTML real. Los
selectores via campo_por_etiqueta() se basaron en una captura de
pantalla (RF05_contratistas.png en el proyecto viejo), no en el HTML
real. Antes de reusar este modulo en un proyecto nuevo, repetir la
exploracion en vivo de esta pantalla puntual.

Mismo patron de dialogos que el resto de la familia ADMTARIF - ver ficha
tecnica completa en actualizacion_claves_tarifas.py.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
Y los 4 helpers GENERICOS de este proyecto viejo: campo_por_etiqueta,
dialogo_visible, confirmar, boton_grabar.
"""


def abrir_mantenedor_contratistas(page, paso_excel=1):
    return abrir_aplicacion(page, ["Comercial", "Facturación", "Facturación", "Mantenedor De Contratistas"], "text=Mantenedor de Contratistas", paso_excel=paso_excel)
