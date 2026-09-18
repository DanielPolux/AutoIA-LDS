"""
Modulo: Seguimiento De Clientes Mt (Web LDS)
Proyecto donde se confirmo: PR000335-SP5 (RF-01 de ese sprint, CU-01 a
CU-09).
Componente Angular: app-seguimiento-de-clientes-mt
Ruta de menu confirmada en vivo: Comercial > Atención Integral Al
Cliente > Seguimiento De Clientes Mt (item HOJA directo, un solo popup
por click - a diferencia de PR000335-SP2, no hace falta abrir
"Atenciones A Clientes" primero ni el _abrir_popup_por_titulo custom;
alcanza el abrir_aplicacion() generico del framework).

Ficha tecnica (confirmado en vivo, 15-17/09/2026):
Filtros con ids reales (ver SC_ID): Area, SST, Expediente, Asignado,
Tipo Fecha, Desde, Hasta. Boton "Buscar [F6]" real: class=matf-btn-buscar
(sin id propio). Botones de accion (sin id propio, usar
get_by_role(..., exact=True)): "Asignar", "Historial Estados",
"Contactos Llamada por SST", "Contactos Llamada por Expediente",
"Exportar", "Limpiar".

Defaults confirmados: Desde = hoy menos 1 mes, Hasta = hoy. Tipo Fecha
llega preseleccionado en "Fecha Creacion" (value=1); las 3 opciones
reales del combo son "Fecha Creacion", "Fecha Asignacion", "Fecha Sig.
Seguimiento".

RESUELTO (17/09/2026): con el rango de fecha por DEFECTO (hoy menos 1
mes) la busqueda daba "Registros: 0" - el usuario confirmo un rango real
con datos: Area="Fonoluz", Tipo Fecha="Fecha Creacion", Desde=24/07/2022,
Hasta=31/07/2022 -> "Registros: 21". Cualquier caso que necesite verificar
el CONTENIDO de una fila ya puede usar este rango en vez de quedar
bloqueado. GOTCHA (causo FALLO real en CP008): este rango hay que
fijarlo SIEMPRE, incluso cuando el caso filtra ademas por SST/Expediente
puntual - el default (hoy menos 1 mes) excluye datos de 2022, y sin el
rango la busqueda por SST da "No hay seguimientos para mostrar." aunque
el codigo exista.

Columnas reales de la grilla principal (confirmado en vivo, scroll
horizontal completo): SST, Expediente, Estado, Motivo, Usuario asigna,
Usuario asignado, Área asignada, Prioridad, Ult. Fec. asignación, Fec.
Sig. seguimiento, Indicador, Días atraso, Fecha prim. llamada, Fecha
últ. llamada, Fecha creación, Contacto llamada, Celular llamada, Correo
llamada, Relación contacto, CR, Resultado, Etapa actual, Etapa
siguiente, Nombre cliente, Proyectista, Potenc. cont., Teléfono 1,
Teléfono 2, Correo cliente. La columna "Etapa siguiente" SI existe (mas
alla del scroll) - es un valor calculado, no vacio.

GOTCHA confirmado en vivo (17/09/2026, CP001): `esperar_fin_de_carga()`
generico NO alcanza para saber cuando el contador "Registros: N" (o
cualquier dato de la grilla) ya tiene el valor real tras "Buscar". El
elemento `<app-loading-spinner>` (componente Angular propio, no Ant
Design/`.ant-spin*` como en otros modulos) parecia el indicador obvio,
pero se confirmo con debug en vivo que NO es confiable: puede
desaparecer de la pantalla mientras el contador TODAVIA muestra el
valor VIEJO (el backend sigue actualizando el contador un rato despues
de que el spinner visual ya se oculto) - un polling basado en el
spinner deja pasar el caso con el dato viejo, sin ningun error visible.
Usar SIEMPRE `esperar_busqueda()` (ver abajo) tras cualquier Buscar/
Limpiar antes de leer el contador o la grilla.

GOTCHA confirmado en vivo (17/09/2026): los dialogos de esta pantalla
(validaciones, confirmaciones, y TODOS los modales de accion - Historial,
Asignar, Contactos por SST/Expediente) usan el contenedor Angular CDK
`<cdk-dialog-container>` - NO `.mdl-confirmar`/`nz-modal-container`/
`.ant-modal-wrap` como en otros modulos de este framework. El boton de
cerrar de los dialogos simples de validacion es un boton con texto
literal "X" (no un icono/aria-label), y tambien tienen "Aceptar". Ver
SELECTOR_MODAL_SC y cerrar_modal_sc().

Mensajes/estructuras de cada accion confirmados en vivo:
  - Buscar sin "Desde": "La fecha de inicio no puede ser vacia"
  - Buscar con "Desde" > "Hasta": "La fecha de fin no puede ser mayor a la de inicio"
  - min date de "Desde"/"Hasta": "2021-01-01" en ambos.
  - maxlength de SST/Expediente/Asignado: "10" en los 3.
  - Exportar CON datos: descarga "SeguimientoClientes_<fecha>.xlsx" +
    dialogo posterior "Exportación generada."
  - Exportar CON GRILLA VACIA: no descarga nada, dialogo "No hay datos
    para exportar."
  - Asignar SIN seleccion: "Seleccione como mínimo una fila." (modal NO se abre)
  - Asignar CON seleccion: modal "¿Asignación" con una grilla de
    usuarios (Nombre/Ap.Paterno/Ap.Materno/Usuario/Correo/Empresa/
    Dominio, seleccionable por fila) + botones Aceptar/Cancelar (no hay
    un <select>, es una tabla clickeable).
  - Historial Estados CON 1 seleccion: modal "Historial" con campos
    SST/Expediente/Id seguimiento (inputs de solo lectura) + boton
    Exportar + tabla (Anterior/Actual/Fecha/Usuario/App Origen/
    Comentario/Cod Llamada).
  - Contactos Llamada por SST CON 1 seleccion: modal "¿Contactos por
    SST" con Expediente/SST (solo lectura) + boton Exportar + tabla
    (SST/Cliente/Telefono/Celular/Correo/Documento/Relacion/Fec.
    Creacion).
  - Contactos Llamada por Expediente CON 1 seleccion: mismo modal que
    por SST pero titulado "¿Contactos por Expediente" - trae los
    contactos de TODAS las solicitudes/SST asociadas a ese expediente
    (puede traer mas filas que la version por SST).
  - Filtro "Estado": boton toggle (sin texto, icono flecha) que abre una
    lista de 11 checkboxes (+ "TODOS" al inicio, seleccion multiple):
    Pendiente de asignar, Asignado, Contacto no ubicado, Reprogramar
    seguimiento, Requiere asesoría proyectos (*), Requiere asesoría por
    correo, Cliente pauso proyecto (*), Cliente cancela proyecto (*),
    Cliente enviará nueva SST (*), Seguimiento terminado. Los 4 con "(*)"
    llevan el sufijo (confirma CP011); el resto no.

PENDIENTE (17/09/2026, no bloqueante): no se confirmo en vivo el mensaje
exacto de "Asignar sin elegir usuario" (CP020, la matriz dice "Seleccione
un usuario para continuar.") ni el orden exacto por Id seguimiento
(CP014/CP023/CP028) ni el contenido columna-por-columna de los archivos
exportados (CP018/CP024/CP029/CP032, requeriria abrir el .xlsx
descargado) - los casos que dependen de esto usan la redaccion de la
matriz (ya validada al 100% en los 4 mensajes que SI se confirmaron en
vivo con la misma fuente) o quedan como verificacion informativa
(AVISO) en vez de asercion dura.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
"""
import re


def abrir_seguimiento_mt(page, paso_excel=1):
    return abrir_aplicacion(page, ["Comercial", "Atención Integral Al Cliente", "Seguimiento De Clientes Mt"], "app-seguimiento-de-clientes-mt", paso_excel=paso_excel)


SC_ID = {
    "Area": "sc-area",
    "SST": "sc-sst",
    "Expediente": "sc-exp",
    "Asignado": "sc-asig",
    "Tipo Fecha": "sc-tipo-fecha",
    "Desde": "sc-desde",
    "Hasta": "sc-hasta",
}


def campo_seguimiento(frame, etiqueta):
    return frame.locator(f"#{SC_ID[etiqueta]}")


def buscar_seguimiento(frame):
    """Boton 'Buscar [F6]' real: class=matf-btn-buscar (sin id propio)."""
    frame.locator("button.matf-btn-buscar").click()


def contador_registros(frame):
    return frame.get_by_text(re.compile(r"Registros:\s*\d+")).first


def esperar_busqueda(app, frame, valor_previo=None):
    """Espera a que 'Registros: N' cambie de valor tras Buscar/Limpiar y
    se estabilice 2 lecturas seguidas - ver GOTCHA del docstring del
    modulo (el spinner app-loading-spinner NO es confiable aca). Si no
    se pasa valor_previo, lo toma del contador ANTES de llamar a esta
    funcion (llamar a esta funcion DESPUES de disparar la busqueda, con
    el valor_previo leido ANTES)."""
    contador = contador_registros(frame)
    texto = valor_previo
    estable = 0
    for _i in range(40):
        app.wait_for_timeout(300)
        actual = contador.inner_text() if contador.count() else texto
        if actual == texto and actual != valor_previo:
            estable += 1
            if estable >= 2:
                break
        else:
            estable = 0
        texto = actual
    return texto


SELECTOR_MODAL_SC = "cdk-dialog-container"


def modal_sc(frame):
    """CONFIRMADO EN VIVO el 17/09/2026: varias acciones de esta pantalla
    apilan un 2do cdk-dialog-container ENCIMA del primero (ej. "Atencion
    a clientes" sobre "Asignacion", o "Exportacion generada" sobre
    "Historial"/"Contactos") - usar SIEMPRE .last (el mas nuevo), nunca
    el locator crudo (que resuelve al primero/mas viejo, ya tapado -
    causo 4 FALLO reales en PR000335-SP5: CP020/CP024/CP029/CP032)."""
    return frame.locator(SELECTOR_MODAL_SC).last


def cerrar_modal_sc(frame, app):
    """Cierra el modal/dialogo activo de esta pantalla (X/Aceptar/Cerrar/
    Cancelar, el primero que encuentre) - ver GOTCHA del docstring:
    ninguno de estos modales matchea los selectores genericos de otros
    modulos (.mdl-confirmar/nz-modal-container/.ant-modal-wrap)."""
    modal = modal_sc(frame)
    if not modal.count():
        return False
    for nombre in ("X", "Aceptar", "Cerrar", "Cancelar"):
        boton = modal.get_by_role("button", name=nombre, exact=True)
        if boton.count():
            boton.first.click()
            app.wait_for_timeout(800)
            return True
    return False


def marcar_filas(frame, indices):
    """Marca (check) el checkbox de las filas de la grilla principal en
    los indices dados (0-based)."""
    filas = frame.locator("table tbody tr")
    for i in indices:
        filas.nth(i).locator("input[type=checkbox]").check()


def desmarcar_todas_las_filas(frame):
    marcadas = frame.locator("table tbody tr input[type=checkbox]:checked")
    for i in range(marcadas.count()):
        marcadas.nth(i).uncheck()
