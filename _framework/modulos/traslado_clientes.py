"""
Modulo: Traslado de Clientes (Web LDS)
Componente Angular: app-traslado-clientes
Ruta de menu confirmada en vivo: Comercial > Traslado De Clientes
Sistema/frente de negocio: Retiro y Castigo de Clientes

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual. Un generate_scripts.py de proyecto
importa lo que necesite de aca y le agrega solo los cuerpos de caso (los
CPxxx puntuales de SU matriz), sin tener que re-descubrir nada de lo que
ya esta documentado aca.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP1, 25/09/2026)
============================================================================

Pantalla ng-zorro/Ant Design. Flujo: elegir Tipo de Traslado (radio
"RACE" = Retirado a Cobranza Externa, default; o "CEAR" = Cobranza
Externa a Retirado), opcionalmente marcar "Forzar Retiro de Carteras"
(solo tiene efecto real al trasladar de Cobranza Externa a Retirado),
agregar uno o mas clientes al lote (input "N° Cliente" + boton
"Agregar"), y pulsar "Trasladar".

"Trasladar" abre un dialogo de confirmacion ("¿Esta seguro...?",
.ant-modal/nz-modal-container) - DISTINTO del popover de resultado que
aparece despues (`button.conf-btn-ok`). El resultado exitoso muestra el
mensaje "se procesaron todos los clientes" (comparar en minusculas). El
popover de resultado puede aparecer 1 vez (exito) o 2 veces superpuestas
(fallo: toast "Operacion Exitosa" + "Ventana de Validacion" con el
detalle) - un click generico sobre "Aceptar" puede colgar por
strict-mode/interceptacion de puntero entre ambos; cerrar en bucle el
primero visible hasta que no quede ninguno (ver
cerrar_dialogos_resultado_traslado()).

**Gotcha real (nz-table, ant-design)**: la grilla de clientes del lote
siempre trae una fila oculta extra "ant-table-measure-now" (uso interno
de layout, nz-table-measure-row) que un `nz-table tbody tr` sin filtrar
cuenta de mas - confirmado en vivo (un caso esperaba 3 filas y veia 4).
Excluirla siempre (ver filas_clientes_traslado()).

**Datos de prueba**: no hay forma de saber el estado de un cliente sin
consultarlo - la propia UI expone su validacion (`ValidarCliente`,
llamada por el frontend en CADA "Agregar") con el estado real de
cualquier numero de cliente. Reusar `app.request` (mismas cookies de
sesion que el browser) para escanear varios numeros de cliente conocidos
y encontrar uno en el estado que se necesite (estadoCliente: "2" =
Retirado, "0" = Activo/no elegible) es mucho mas rapido y confiable que
buscar en la BD Informix real. Metodo: interceptar la request real que
dispara la UI al hacer click en "Agregar" (`app.on("request", ...)`,
filtrar por "ValidarCliente"), guardar URL/headers/post_data, y
reproducirla con `app.request.post(...)` sustituyendo el numero de
cliente en el post_data via regex.

**Cuidado con "quemar" clientes de prueba**: cada traslado exitoso es
una escritura REAL en el ambiente de Pruebas - un cliente usado una vez
para "Retirado -> Cobranza Externa" deja de calificar para ese mismo
escenario en una corrida futura (queda en estado "pendiente de
validacion" o similar). Si un caso que antes daba OK empieza a fallar
sin haber cambiado el script, sospechar PRIMERO que el numero de cliente
hardcodeado ya fue consumido, antes de asumir un bug nuevo - resolver
buscando un cliente fresco con el mismo metodo de arriba.
============================================================================
"""

import re
from playwright.sync_api import TimeoutError as PWTimeoutError


def abrir_traslado_clientes(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Traslado De Clientes"], "app-traslado-clientes", paso_excel=paso_excel)


def seleccionar_tipo_traslado(frame, valor):
    """valor: "RACE" (Retirado a Cobranza Externa, default) o "CEAR" (Cobranza Externa a Retirado)."""
    frame.locator(f'label[nzvalue="{valor}"]').click()


def marcar_forzar_retiro_carteras(frame):
    frame.get_by_text("Forzar Retiro de Carteras", exact=True).click()


def agregar_cliente_traslado(app, frame, numero):
    campo = frame.locator('input[placeholder="N° Cliente"]')
    boton_agregar = frame.locator("button", has_text=re.compile(r"^\s*Agregar\s*$"))
    campo.fill(numero)
    app.wait_for_timeout(500)
    boton_agregar.click()
    app.wait_for_timeout(800)


def trasladar_y_confirmar(app, frame):
    """Pulsa Trasladar y acepta el dialogo de confirmacion (¿Esta seguro...?,
    clase .ant-modal/nz-modal-container) - DISTINTO del popover de resultado
    (.conf-btn-ok) que aparece despues, ver cerrar_dialogos_resultado_traslado()."""
    boton_trasladar = frame.locator("button", has_text=re.compile(r"^\s*Trasladar\s*$"))
    boton_trasladar.click()
    app.wait_for_timeout(1500)
    dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(r".", re.S))
    dialogo.first.wait_for(state="visible", timeout=8000)
    dialogo.first.get_by_role("button", name=re.compile(r"^Aceptar$", re.I)).first.click()
    app.wait_for_timeout(2500)
    try:
        app.wait_for_load_state("networkidle", timeout=10000)
    except PWTimeoutError:
        pass
    app.wait_for_timeout(1000)


def leer_mensaje_resultado_traslado(frame):
    return frame.locator("body").inner_text()


def filas_clientes_traslado(frame):
    """nz-table (ant-design) siempre trae una fila oculta extra
    'ant-table-measure-now' (uso interno de layout, ver
    nz-table-measure-row en el HTML del componente) que un
    `nz-table tbody tr` sin filtrar cuenta de mas - confirmado en vivo el
    25/09/2026 (un caso esperaba 3 filas y veia 4; otro esperaba 1 y veia 2).
    Excluirla siempre al contar filas reales de esta grilla."""
    return frame.locator("nz-table tbody tr:not(.ant-table-measure-now)")


def cerrar_dialogos_resultado_traslado(app, frame, intentos=4):
    """El popover de resultado (.conf-btn-ok) puede aparecer 1 vez (exito) o
    2 veces superpuestas (fallo: toast "Operacion Exitosa" + "Ventana de
    Validacion" con el detalle) - confirmado en vivo que un click(name=...)
    generico sobre "Aceptar" cuelga por strict-mode/intercepcion de puntero
    entre ambos; cerrar en bucle el primero visible hasta que no quede ninguno."""
    for _ in range(intentos):
        boton = frame.locator("button.conf-btn-ok")
        if boton.count() == 0:
            break
        try:
            boton.first.click(timeout=2000)
            app.wait_for_timeout(400)
        except Exception:
            break
