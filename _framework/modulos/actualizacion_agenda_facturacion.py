"""
Modulo: Actualizacion De Agenda De Facturacion (Web LDS)
Componente Angular: app-agenda-principal
Ruta de menu confirmada en vivo: Interno > Actualización De Agenda De Facturación
Manual de usuario real disponible (si el proyecto lo tiene en
Documentos/): manual_usuario_agenda_facturacion.pdf - documenta mensajes
exactos, reglas de calculo de vencimientos y las 3 sub-pantallas.

Ficha tecnica (confirmado en vivo, PR000325-SP3, 16/09/2026):
Pantalla "Calendario de Facturacion" con 3 secciones:
  - "Proceso": Fecha de Proceso + Leer/Cancelar.
  - "Agenda": grilla con fila de filtro/alta EN LA CABECERA (Sector +
    Fecha Lectura/Emision/Reparto/Corte Boleta/Corte Terr., 7 inputs
    type=date en total contando Fecha de Proceso) + botones
    Ingresar/Eliminar/Vencimientos.../Feriados....
  - "Vencimientos": grilla de vencimientos del sector seleccionado + un
    8vo input type=date (indice 6) + boton Modifica Fecha.
TODOS los botones salvo Leer quedan deshabilitados en la carga inicial.

Catalogo real de Tipos de Vencimiento confirmado en vivo: codigo 1
"REGULADOS" (15 dias, Dias Habiles=N/corridos, el UNICO modificable
desde esta pantalla principal) y codigo 2 "LIBRES" (20 dias, Dias
Habiles=S/habiles, "Clientes Libres" - bloqueado para modificar desde
aqui, da "No puede modificar Fecha de Clientes Libres. Debe de hacerlo
del modulo de Grandes Clientes.").

BUG / regla de negocio real confirmada en vivo: Fecha Corte Boleta y
Fecha Corte Terr. son UNICAS EN TODO EL SISTEMA (no por sector) -
reutilizar una fecha de corte ya usada por CUALQUIER sector en cualquier
corrida anterior da "La Fecha Corte Boleta: [fecha] ingresada esta
asignada al sector [X]. Ingrese otra fecha." (o el generico "No se pudo
registrar la agenda." si la colision es contra la fecha que la MISMA
sucesion de intentos acaba de consumir). crear_agenda_prueba() sortea la
Fecha de Proceso al azar en una ventana de ~4 anios en el futuro en cada
llamada para evitar esto, y reintenta con otra fecha si el sistema
reporta colision/feriado.

Restriccion de sectores maximetro: Fecha Corte Boleta/Terr. no puede
caer en lunes ni viernes para esos sectores - por eso los helpers de
este modulo generan fechas de corte en martes/miercoles/jueves siempre
(seguro para cualquier sector, no solo maximetro).

Aviso/bloqueo al modificar un vencimiento en sabado/domingo/feriado
(confirmado en vivo, los 3 casos):
  - Sabado: aviso "Fecha de Vencimiento es Sabado." (informativo) -
    Modifica Fecha SI actualiza (con el confirm normal Si/No).
  - Domingo: aviso "Fecha de Vencimiento es Domingo." - Modifica Fecha
    BLOQUEA con "Dia feriado o Domingo, ingrese otra fecha." (sin
    dialogo de confirmacion).
  - Feriado: sin aviso previo en la grilla, pero Modifica Fecha BLOQUEA
    con el mismo mensaje que domingo.

PENDIENTE / no reproducible en este ambiente (16/09/2026):
  - "Modificar vencimiento bloqueado por corte programado" y "Bloqueo
    por corte programado - eliminar" requieren una fila de Agenda cuyo
    sector YA este "en proceso de facturacion" (corte programado
    vigente) - ese estado lo pone un proceso batch real del sistema, no
    se puede generar via UI. Se escaneo en vivo un rango de ~52 fechas
    reales sin encontrar ningun sector en ese estado.

Sub-pantalla "Actualizacion de Tipos de Vencimientos" (boton
Vencimientos..., confirmado en vivo): Cantidad de Vencimientos (solo
lectura) + fila de edicion (Codigo maxlength=5, Descripcion maxlength=30,
Cant. Dias type=number min=1, Dias Habiles maxlength=1 "S/N") + grilla +
boton dual Ingresar/Modificar + Cancelar. Al hacer click en una fila
existente, el campo Codigo queda "readonly" (NO "disabled" - verificar
ambos atributos si un caso necesita confirmar "solo lectura"). Mensaje
de exito: "Registro Actualizado."

Sub-pantalla "Ingreso Dias Feriados" (boton Feriados..., confirmado en
vivo): campo Ano (input, valores validos 2000-2099, valida con "Ingrese
un ano valido (2000-2099).") + campo Fecha (type=date) + lista + botones
Leer/Ingresar/Eliminar/Descargar PDF/Cancelar-Cerrar. Mensajes: "Registro
Ingresado." / "Registro Eliminado." Al abrir, consulta el ano en curso
automaticamente. TODOS los anios validos (2000-2099) traen un calendario
civil/religioso PRE-POBLADO automaticamente (10-11 feriados fijos,
probado en los extremos 2000/2099 y en 2087) - nunca hay grilla
realmente vacia sin intervenir.

CONFIRMADO EN VIVO (CP089, 17/09/2026) - "Descargar PDF con grilla
vacia debe bloquear" SI es reproducible, con estos 3 hallazgos clave:
  1. La lista de fechas es un `<ul>/<li>` (con estado transitorio de
     opacidad reducida + spinner de puntos mientras carga), NO una
     `<table>` - matchear por texto con patron de fecha
     (`re.compile(r"\d{2}/\d{2}/\d{4}")` via `modal.get_by_text(...)`),
     nunca `table tbody tr` (da 0 siempre, sin importar cuanto se
     espere).
  2. Los feriados FIJOS precargados SI se pueden eliminar uno por uno
     (NO estan protegidos) - mismo dialogo de confirmacion "¿Esta
     seguro de eliminar el Feriado?" que un feriado agregado a mano.
     Vaciando un anio de prueba DEDICADO por completo (ver
     `_exploracion/diag_cp089_eliminar_feriados.py` de PR000325-SP3
     como referencia del patron de eliminacion en loop) se llega a la
     grilla vacia real que pide el caso.
  3. El modal de esta sub-pantalla tambien sufre el apilamiento
     documentado abajo (2 `nz-modal-container` superpuestos al abrir) -
     usar SIEMPRE `.last` sobre SELECTOR_DIALOGO para ubicarlo, nunca
     `.first` (con `.first` la grilla se lee siempre vacia/vieja, sin
     importar el polling).
  Mensaje real de bloqueo con la grilla vacia: "Debe existir datos en
  la grilla para que puedan ser Impresos." (sin iniciar ninguna
  descarga). El anio de prueba usado queda vacio de forma PERMANENTE
  (no hay forma de "recargar" el calendario fijo desde la UI) - si se
  reutiliza el mismo anio dedicado en corridas futuras, el caso es
  idempotente (ya lo encuentra vacio, no necesita eliminar nada de
  nuevo).

BUG REAL confirmado en vivo (timing, presente en TODOS los flujos de
confirmar/resultado de este modulo): el spinner de carga puede limpiarse
ANTES de que el dialogo de resultado ("Agenda registrada exitosamente.",
etc.) termine de renderizarse - un chequeo inmediato tras el spinner a
veces llega demasiado pronto. Hace falta polling (varios segundos) antes
de decidir que no hubo ningun dialogo de resultado - ver el polling
dentro de crear_agenda_prueba() como referencia del patron. Relacionado:
justo despues de confirmar, el dialogo de "Confirmacion" (Si/No) puede
seguir un instante en el DOM (animacion de cierre) al mismo tiempo que
ya aparece el dialogo de resultado - usar SIEMPRE ".last" (el mas
nuevo) sobre SELECTOR_DIALOGO en vez de ".first" para ubicar el dialogo
de resultado real.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
Y helpers/constante GENERICOS del proyecto (no especificos de este
modulo, ver NUEVO_PROYECTO_CHECKLIST.md Seccion 0c): SELECTOR_DIALOGO.
"""
import random
import re
from datetime import date, timedelta
from playwright.sync_api import TimeoutError as PWTimeoutError


def abrir_actualizacion_agenda_facturacion(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Actualización De Agenda De Facturación"], "app-agenda-principal", paso_excel=paso_excel)


def _fecha_habil_segura(base, offset):
    """Fecha a partir de base+offset dias que cae en martes, miercoles o
    jueves - evita lunes/viernes (restriccion de sectores maximetro en
    Fecha Corte Boleta/Terr.) y fin de semana."""
    d = base + timedelta(days=offset)
    while d.weekday() not in (1, 2, 3):
        d += timedelta(days=1)
    return d


def leer_agenda(app, frame, fecha_proceso_iso):
    """Ejecuta Leer para una Fecha de Proceso dada.

    CONFIRMADO EN VIVO el 17/09/2026: a veces aparece un dialogo (aviso u
    otro) justo cuando "Leer" pasa de deshabilitado a habilitado, y tapa
    el click con un "intercepts pointer events" del overlay
    (nz-modal-container) aunque el boton ya sea clickeable - un chequeo
    unico ANTES de intentar el click no alcanza porque el dialogo puede
    aparecer DESPUES de ese chequeo. Se reintenta en loop: si el click
    falla por timeout, se cierra cualquier dialogo visible y se
    reintenta, en vez de asumir que un solo intento/cierre alcanza.
    """
    frame.locator("input[type=date]").first.fill(fecha_proceso_iso)
    app.wait_for_timeout(300)
    boton_leer = frame.get_by_role("button", name="Leer", exact=True)
    for _intento in range(15):
        dialogo_previo = frame.locator(SELECTOR_DIALOGO)
        if dialogo_previo.count() and dialogo_previo.last.is_visible():
            boton_cierre = dialogo_previo.last.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar|No)$"))
            if boton_cierre.count():
                boton_cierre.first.click()
                app.wait_for_timeout(500)
                continue
        try:
            boton_leer.click(timeout=3000)
            break
        except PWTimeoutError:
            app.wait_for_timeout(500)
    else:
        boton_leer.click()
    esperar_fin_de_carga(app, frame)
    try:
        frame.locator(".ant-spin-blur").first.wait_for(state="hidden", timeout=8000)
    except PWTimeoutError:
        pass
    app.wait_for_timeout(800)


def crear_agenda_prueba(app, frame, sector_valor=None, dias_semana_emision=(1, 2, 3), offset_corte=25):
    """Crea un registro de agenda de facturacion descartable de punta a
    punta (Fecha de Proceso elegida al azar lejos en el futuro + Sector +
    5 fechas validas + Ingresar + confirmar) y devuelve (fecha_proceso,
    sector_valor, corte_boleta, corte_terr) - las 4 fechas/valor quedan
    disponibles para los pasos siguientes del caso (releer, modificar,
    eliminar, etc).

    dias_semana_emision (0=lunes..6=domingo) controla que dia de la
    semana cae la Fecha Emision/Proceso - por defecto martes/miercoles/
    jueves (seguro para cualquier sector), pero algunos casos necesitan
    forzar VIERNES especificamente (para verificar que un vencimiento de
    dias corridos puede caer en sabado sin corregirse - ver ficha
    tecnica del modulo)."""
    for _intento in range(5):
        fecha_proceso = date(2027, 1, 1) + timedelta(days=random.randint(0, 1400))
        while fecha_proceso.weekday() not in dias_semana_emision:
            fecha_proceso += timedelta(days=1)
        fp_iso = fecha_proceso.isoformat()
        corte_boleta = _fecha_habil_segura(fecha_proceso, offset_corte + _intento * 7)
        corte_terr = _fecha_habil_segura(corte_boleta, 3)

        leer_agenda(app, frame, fp_iso)

        select_sector = frame.locator("select").first
        opciones = [v for v in select_sector.locator("option").evaluate_all("els => els.map(e => e.value)") if v]
        valor_sector = sector_valor or opciones[0]
        select_sector.select_option(value=valor_sector)
        app.wait_for_timeout(300)

        inputs_fecha = frame.locator("input[type=date]")
        inputs_fecha.nth(1).fill(fp_iso)
        app.wait_for_timeout(150)
        inputs_fecha.nth(2).fill(fp_iso)
        app.wait_for_timeout(150)
        inputs_fecha.nth(3).fill(fp_iso)
        app.wait_for_timeout(150)
        inputs_fecha.nth(4).fill(corte_boleta.isoformat())
        app.wait_for_timeout(150)
        inputs_fecha.nth(5).fill(corte_terr.isoformat())
        app.wait_for_timeout(300)

        frame.get_by_role("button", name="Ingresar", exact=True).click()
        app.wait_for_timeout(800)
        dialogo = frame.locator(SELECTOR_DIALOGO)
        if not (dialogo.count() and dialogo.last.is_visible()):
            continue
        texto = dialogo.last.inner_text()
        if "modificar" not in texto.lower():
            # Coleccion/feriado/otro rechazo: cerrar el aviso y reintentar
            # con una fecha nueva en la proxima vuelta. Se usa ".last" y
            # se reintenta el click de cierre (mismo riesgo de dialogo
            # apilado que en el resultado final) para no dejar un modal
            # fantasma bloqueando el "Leer" del proximo intento.
            boton_cerrar = dialogo.last.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$"))
            if boton_cerrar.count():
                for _cierre in range(5):
                    boton_cerrar.first.click()
                    app.wait_for_timeout(400)
                    dialogo_actual = frame.locator(SELECTOR_DIALOGO)
                    if not (dialogo_actual.count() and dialogo_actual.last.is_visible()):
                        break
            continue
        boton_si = dialogo.last.get_by_role("button", name=re.compile(r"^S.?$"))
        boton_si.first.click()
        esperar_fin_de_carga(app, frame)
        for _i in range(30):
            app.wait_for_timeout(400)
            if not frame.locator(".ant-spin-blur").count():
                break
        # El spinner puede limpiarse ANTES de que el dialogo de resultado
        # ("Agenda registrada exitosamente.") termine de renderizarse -
        # se hace polling hasta 6s esperando a que el dialogo de
        # resultado aparezca antes de decidir que no hubo ninguno.
        dialogo_resultado = None
        for _i in range(15):
            app.wait_for_timeout(400)
            resultado = frame.locator(SELECTOR_DIALOGO)
            if resultado.count() and resultado.last.is_visible():
                dialogo_resultado = resultado.last
                break
        if dialogo_resultado is not None:
            # El dialogo de "Confirmacion" (Si/No) puede seguir un
            # instante en el DOM (animacion de cierre) al mismo tiempo
            # que ya aparece el dialogo de resultado - con dos matches
            # de SELECTOR_DIALOGO al mismo tiempo, ".first" a veces
            # resuelve al dialogo VIEJO. Se usa ".last" (el mas nuevo).
            texto_resultado = dialogo_resultado.inner_text()
            boton_cerrar2 = dialogo_resultado.get_by_role("button", name=re.compile(r"^(Aceptar|Cerrar)$"))
            if boton_cerrar2.count():
                for _cierre in range(5):
                    boton_cerrar2.first.click()
                    app.wait_for_timeout(400)
                    resultado_actual = frame.locator(SELECTOR_DIALOGO)
                    if not (resultado_actual.count() and resultado_actual.last.is_visible()):
                        break
            if "exitosamente" in texto_resultado.lower():
                return fecha_proceso, valor_sector, corte_boleta, corte_terr
    raise AssertionError("No se pudo crear una agenda de prueba tras varios intentos (colisiones de fecha de corte)")
