"""
Modulo: Actualizacion De Claves De Tarifas (Web LDS)
Familia ADMTARIF (migracion VB3 -> Angular/.NET Core), proyecto viejo
PR000325 Sprint 2 (C:\\Proyectos\\PlataformaWeb\\automation\\PR000325\\).
Ruta de menu + selector de pantalla confirmados en vivo el 10/09/2026.

**Confianza: ALTA para este RF puntual.** Es el UNICO de los 6
aplicativos ADMTARIF con el flujo completo de alta+confirmacion+
persistencia validado en vivo de punta a punta (CP001, con codigo real
creado en Pruebas: "99"/"PRUEBA EXPLORACION CLAUDE"). Los demas RF de
esta familia (ver los otros modulos `*_tarifas.py`,
`actualizacion_formas_medida.py`, `cargos_reposicion_conexion.py`,
`mantenedor_presupuesto_ventas.py`, `mantenedor_contratistas.py`,
`asignacion_libros_contratistas.py`) siguen el MISMO patron de
navegacion/selectores pero NO tienen su flujo de alta confirmado en
vivo caso por caso - revisar la nota de confianza de cada uno.

Patron de UI comun a las 6 apps (confirmado en vivo, RF-01): sin
atributo "name" en la mayoria de campos (usar campo_por_etiqueta(),
fallback via <span class="fl">etiqueta</span> + <div class="val">
hermano) + checkboxes/radios en <label> real + boton unico
Ingresar/Modificar que cambia de texto segun si la clave ya existe
(ver boton_grabar()) + dialogo .mdl-confirmar (mismo componente para
validaciones de un solo boton Aceptar y confirmaciones
Cancelar+Aceptar) que puede mostrar un SEGUNDO dialogo apilado con el
resultado real ("Registro Actualizado.", "Registro Insertado.") -
confirmado en vivo que ese segundo dialogo puede tardar bastante mas de
lo esperado bajo carga (usar un timeout generoso, 7s+, no 3s).

Codigos de prueba: el campo "codigo" de estas apps parece aceptar solo
digitos (confirmado: "ZT99" se guardo como "99"). Como cada corrida de
un caso de alta deja un registro nuevo en Pruebas (a diferencia de otros
proyectos de solo lectura), generar un sufijo derivado de time.time() (u
otro valor variable) en cada caso que crea informacion nueva, para no
chocar entre corridas repetidas.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
Y los 4 helpers GENERICOS de este proyecto viejo (ligeramente distintos
de los helpers genericos de PR000325-SP3 - usan solo ".mdl-confirmar",
no la union con nz-modal-container/.ant-modal-wrap): campo_por_etiqueta,
dialogo_visible, confirmar, boton_grabar.
"""


def abrir_actualizacion_claves_tarifas(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Actualización De Claves De Tarifas"], "app-clave-tarifa-list", paso_excel=paso_excel)
