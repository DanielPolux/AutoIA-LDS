"""
Modulo: Asignación De Usuarios (RHD) (Web LDS)
Proyecto donde se confirmo: PR000335-SP5 (pausado 15/09/2026 - el
usuario encontro varios defectos reales seguidos y decidio pausar este
proyecto para revisar otro, ver RF-02 de ese sprint).
Componente Angular: app-asignacion-rhd-page
Ruta de menu confirmada en vivo: Comercial > Atención Integral Al
Cliente > Asignación De Usuarios (item hoja directo, un solo popup).

Ficha tecnica (confirmado en vivo, 15/09/2026):
Sin filtro (Clase/Nivel Tension vacios) + Buscar trae "Total registros:
{0}" (no habia usuarios RHD registrados en la exploracion en vivo).

Modal "Agregar Registro"/"Modificar Registro"/"Eliminar Registro"
(componente app-modal-opciones-rhd, MISMO modal para las 3 acciones,
titulo cambia segun el boton que lo abrio - ver abrir_modal_rhd):
campos Clase (#rhd-modal-clase, select), Nivel Tension
(#rhd-modal-tension, select), Rol Usuario (#rhd-modal-usuario,
maxlength=20) + checkbox Asignar Responsable (#rhd-modal-responsable).

DEFECTO REAL CONFIRMADO EN VIVO el 15/09/2026 (ver
_exploracion/explore_rhd_red.py del proyecto donde se encontro, NO es un
bug de la automatizacion): al completar el modal "Agregar Registro"
(Clase="F1 - Por interrupción de servicio", Nivel Tension="BT", Rol
Usuario="DCABA_DW") y presionar Aceptar, el backend responde 400 con el
mensaje generico "Acceso denegado. StatusCode: BadRequest..." - MISMO
PATRON que el defecto de PR000335-SP2 (ModificarAtencionCliente, ver
modulo atencion_cliente.py): un POST de escritura rechazado, el
FRONTEND NO MUESTRA NINGUN ERROR, el modal se queda exactamente igual
sin ningun indicio visible de que fallo. Endpoint real: POST
.../api/asignacion-rhd/agregar-usuario-rhd.

Es esperable que Modificar/Eliminar compartan el mismo bloqueo (mismo
patron de backend), pero esto NO fue confirmado en vivo todavia -
confirmar antes de asumirlo a ciegas si se retoma este modulo, puede
haber matices por operacion.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
"""


def abrir_asignacion_usuarios_rhd(page, paso_excel=1):
    return abrir_aplicacion(page, ["Comercial", "Atención Integral Al Cliente", "Asignación De Usuarios"], "app-asignacion-rhd-page", paso_excel=paso_excel)


def abrir_modal_rhd(frame, nombre_boton):
    """Agregar/Modificar/Eliminar abren el MISMO tipo de modal
    (app-modal-opciones-rhd), titulo "Agregar Registro"/"Modificar
    Registro"/"Eliminar Registro" segun el boton."""
    frame.get_by_role("button", name=nombre_boton, exact=True).click()
    dialogo = frame.get_by_role("dialog")
    dialogo.wait_for(state="visible", timeout=8000)
    return dialogo


def completar_modal_rhd(dialogo, clase=None, tension=None, usuario=None, responsable=None):
    if clase is not None:
        dialogo.locator("#rhd-modal-clase").select_option(label=clase)
    if tension is not None:
        dialogo.locator("#rhd-modal-tension").select_option(label=tension)
    if usuario is not None:
        dialogo.locator("#rhd-modal-usuario").fill(usuario)
    if responsable is not None:
        checkbox = dialogo.locator("#rhd-modal-responsable")
        if responsable:
            checkbox.check()
        else:
            checkbox.uncheck()
