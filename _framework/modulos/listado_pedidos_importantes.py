"""
Modulo: Listado Pedidos Importantes (Web LDS)
Proyecto donde se confirmo: PR000335-SP5 (RF-03 de ese sprint, CU-01/02/03).
Componente Angular: app-listado-pedidos-importantes
Ruta de menu confirmada en vivo: Comercial > Atención Integral Al
Cliente > Listado Pedidos Importantes (item hoja directo, un solo
popup).

Ficha tecnica (confirmado en vivo, 17/09/2026):
Filtros con ids reales: Codigo Llamada (#pi-codigo-llamada, texto),
Caso Critico (#pi-caso, select: NINGUNO/ACCIDENTE/INCENDIO/FUGA DE GAS/
AMENAZA), Estado (#pi-estado, select: REGISTRADO/ATENDIDO, default
REGISTRADO), Fecha Llamada / modo de rango (#pi-rango, select:
NINGUNO/DESDE/ENTRE/HASTA/IGUAL, default DESDE), Clasificacion Pedido
(#pi-clasif), Tipo Pedido (#pi-tipo), Sub Tipo Pedido (#pi-subtipo),
Desde (#pi-desde, date), Hasta (#pi-hasta, date - solo visible en modo
ENTRE), Filtro Personalizado (#pi-filtro-pers, checkbox). Boton "Buscar
[F6]" real: get_by_role(name=re.compile(r"^Buscar")) (el nombre
accesible incluye el sufijo "[F6]", no usar exact=True con "Buscar" a
secas).

Default de fecha CONFIRMADO: modo DESDE, fecha inicial = hoy menos 7
dias (a diferencia de Seguimiento De Clientes Mt, que es hoy menos 1
mes).

Codigo Llamada: exige guion (formato NNNNN-NN o similar) - un valor sin
guion (ej. "12345") muestra el mensaje INLINE (texto rojo bajo el
campo, NO un modal) "El Codigo Llamada no es válido" y la busqueda NO
se ejecuta (el contador/grilla quedan igual que antes). El campo
tambien filtra caracteres al tipear: digitos y guion se aceptan,
letras arbitrarias se rechazan (el prefijo especifico de 3 letras de
"llamadas finalizadas" que la matriz menciona no se identifico en vivo).

Filtro Personalizado: al marcar, deshabilita los 3 combos
Clasificacion/Tipo/Subtipo (los 3, a diferencia de Resumen De Pedidos
que solo bloquea 2) y aparece un boton "..." que abre el modal
"Listado de Tipo de Llamadas" (checkboxes por Clasificacion, con "+"
para expandir Tipo/Subtipo de cada una) + Aceptar/Cancelar.

Exportar: SI ofrece un modal de opciones ("Exportar a Excel" - radio/
checkbox "Exportar pagina actual" / "Exportar todas las paginas" +
Cancelar/Aceptar) - hay que elegir una opcion ANTES de Aceptar, o el
modal se cierra sin iniciar ninguna descarga. Con la grilla vacia,
Exportar muestra DE INMEDIATO (sin pasar por el modal de opciones) el
aviso "No puede continuar... No hay registros para dicha operación."

Seleccion de fila: la grilla NO tiene checkbox de seleccion propio (los
2 checkboxes visibles por fila, en las columnas Importante/Riesgo Vida,
son DATOS de solo lectura, no seleccion) - se selecciona con CLICK
directo en la fila (queda con class="selected"). Sin seleccion,
"Dar por Atendido"/"Historial"-like acciones muestran "Por favor
seleccione un pedido".

Dar por Atendido: con 1 fila seleccionada, muestra un dialogo de
confirmacion "¿Desea dar por atendido el pedido con código de llamada
<codigo>?" (Cancelar/Aceptar).

DEFECTO REAL CONFIRMADO EN VIVO el 17/09/2026 (ver
PR000335-SP5/_exploracion/recheck_cp061_red.py, NO es un bug de la
automatizacion): al Aceptar la confirmacion de "Dar por Atendido", el
backend responde 400 en POST .../DarPorAtendido con el mensaje generico
"Acceso denegado. StatusCode: BadRequest...", y el dialogo de
"resultado" en pantalla dice explicitamente "No se pudo dar por
atendido el pedido con código de llamada <codigo>" - el pedido NO
cambia de estado (sigue REGISTRADO). MISMO PATRON ya confirmado en
RF-02 de este sprint (Asignacion RHD, ver asignacion_usuarios_rhd.py) y
en PR000335-SP2 (ModificarAtencionCliente) - 3ra vez que aparece este
"Acceso denegado" en distintas pantallas/endpoints del modulo MAC,
fuerte indicio de que es un problema de PERMISOS de la cuenta de
pruebas (DCABA_DW) para acciones de escritura, no defectos aislados por
pantalla.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
Y helpers/constante GENERICOS del proyecto (no especificos de este
modulo): SELECTOR_MODAL_PI (cdk-dialog-container, .mdl-confirmar,
nz-modal-container - mismo gotcha de dialogos apilados que otros
modulos de este framework, usar SIEMPRE .last).
"""
import re


def abrir_listado_pedidos_importantes(page, paso_excel=1):
    return abrir_aplicacion(page, ["Comercial", "Atención Integral Al Cliente", "Listado Pedidos Importantes"], "app-listado-pedidos-importantes", paso_excel=paso_excel)


PI_ID = {
    "Codigo Llamada": "pi-codigo-llamada",
    "Caso Critico": "pi-caso",
    "Estado": "pi-estado",
    "Rango Fecha": "pi-rango",
    "Clasificacion": "pi-clasif",
    "Tipo": "pi-tipo",
    "Subtipo": "pi-subtipo",
    "Desde": "pi-desde",
    "Hasta": "pi-hasta",
    "Filtro Personalizado": "pi-filtro-pers",
}

SELECTOR_MODAL_PI = "cdk-dialog-container, .mdl-confirmar, nz-modal-container"


def campo_pedido(frame, etiqueta):
    return frame.locator(f"#{PI_ID[etiqueta]}")


def buscar_pedidos(frame):
    frame.get_by_role("button", name=re.compile(r"^Buscar")).click()


def total_pedidos(frame):
    return frame.get_by_text(re.compile(r"Total registros:\s*\{\d+\}")).first


def modal_pi(frame):
    return frame.locator(SELECTOR_MODAL_PI).last


def cerrar_modal_pi(frame, app):
    modal = modal_pi(frame)
    if not modal.count():
        return False
    for nombre in ("X", "Aceptar", "Cerrar", "Cancelar"):
        boton = modal.get_by_role("button", name=nombre, exact=True)
        if boton.count():
            boton.first.click()
            app.wait_for_timeout(800)
            return True
    return False


def seleccionar_fila_pedido(frame, indice=0):
    frame.locator("table tbody tr").nth(indice).click()
