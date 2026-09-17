"""
Modulo: Actualizacion De Conceptos (Web LDS)
Componente Angular: app-conceptos-list
Ruta de menu confirmada en vivo: Interno > Actualización De Conceptos

Ficha tecnica (confirmado en vivo, PR000325-SP3, 16/09/2026):
Pantalla "Concepto" (codigo, 3 caracteres) + "Configuracion Contable"
(Documento: select; Cuenta Contable: input poblado via modal "Busqueda
Cuenta Contable" abierto con el boton "..."; Movimiento: input de 1
caracter restringido a I/E EN TIEMPO REAL - cualquier otro caracter
tipeado se descarta y el campo queda vacio). Boton unico
Ingresar/Modificar (boton_grabar, helper generico).

BUG REAL / orden real distinto al que sugiere la matriz de pasos: para
un codigo NUEVO, "Leer" exige que Descripcion ya tenga contenido (si
esta vacia responde "Ingrese descripcion." y NO cambia a modo Insertar)
- a diferencia del orden "Leer primero, completar despues" que sugiere
la matriz, se llena Descripcion ANTES de presionar Leer (ver
crear_concepto_prueba()).

Modal de cuenta contable: "Buscar" (con filtros CUENTA/DESCRIPCION
opcionales, vacios trae hasta 100 resultados) + doble-click en una fila
selecciona y CIERRA el modal solo, sin boton "Seleccionar" adicional.

Codigos de prueba de 3 letras al azar (26^3 combinaciones, margen de
sobra - a diferencia de RF-04, no hace falta reutilizar/limpiar el pool).

RAIZ REAL del bug mas dificil de este modulo (releer_concepto,
confirmada en vivo via captura de pantalla Y volcado del DOM en el
momento exacto del fallo): para un CODIGO YA EXISTENTE, escribirlo en el
campo y tabular dispara una autolectura on-blur ASINCRONICA contra el
backend que puede tardar MUCHO (confirmado, en un dia con el backend
lento, mas de 24s). Mientras tanto Documento/Cuenta Contable quedan
vacios y "Leer"/"Modificar" siguen sin habilitarse. Cuando por fin
resuelve, dejar "Leer" deshabilitado es el estado de EXITO (no un bug):
forzar un click ahi agota el timeout porque el boton nunca se
re-habilita esperando otra cosa. Por eso releer_concepto() favorece
esperar con PACIENCIA (decenas de segundos, polling) por encima de
reintentar el tipeo o recargar la pagina - ambos "arreglos" mas
agresivos se probaron en vivo y resultaron CONTRAPRODUCENTES (rompieron
un caso que antes pasaba, CP033) - NUNCA usar app.reload() aca.

Otros gotchas confirmados en vivo:
  - Tras una accion anterior (Eliminar/desactivar) puede quedar un
    overlay de carga (`.ant-spin-blur`) bloqueando clicks por mas
    tiempo del que esperar_fin_de_carga() + el margen fijo cubren.
  - El campo Descripcion tiene un autocomplete que a veces queda
    abierto/colgado en el DOM despues de escribir e intercepta el
    siguiente click sobre Concepto - se cierra con Escape por las dudas
    antes de cualquier interaccion.
  - El campo Concepto puede volverse "readonly disabled" tanto ANTES de
    empezar (lectura anterior en modo solo-lectura) como EN MEDIO de un
    reintento (el form se resetea tras Eliminar/desactivar con un
    render en DOS FASES: primero luce habilitado/en blanco un instante,
    y un ciclo de Angular despues lo vuelve a bloquear).
  - Un solo chequeo de boton_leer.is_enabled()==True no alcanza: puede
    estar habilitado en un instante y ya deshabilitado de nuevo
    milisegundos despues (debounce de 3 lecturas seguidas antes de
    confiar en que es un codigo nuevo/inexistente).

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
Y helpers GENERICOS del proyecto (no especificos de este modulo, ver
NUEVO_PROYECTO_CHECKLIST.md Seccion 0c): escribir_campo, confirmar_si_no,
SELECTOR_DIALOGO.
"""
import random
import re
from playwright.sync_api import TimeoutError as PWTimeoutError


def abrir_actualizacion_conceptos(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Actualización De Conceptos"], "app-conceptos-list", paso_excel=paso_excel)


def campo_concepto_codigo(frame):
    return frame.locator("input").first


def releer_concepto(app, frame, codigo):
    """Vuelve a poner la pantalla en un codigo de Concepto conocido
    (pasando por "Cancelar" primero si el campo esta deshabilitado por
    una lectura anterior). Ver la ficha tecnica del modulo para el
    detalle completo de la carrera de autolectura on-blur que motiva el
    polling paciente de esta funcion - NUNCA reemplazarlo por
    app.reload(), confirmado en vivo que rompe casos que antes pasaban."""
    app.keyboard.press("Escape")
    app.wait_for_timeout(300)
    campo = campo_concepto_codigo(frame)
    boton_leer = frame.get_by_role("button", name="Leer", exact=True)
    campo_cuenta = frame.locator("input").nth(2)

    def _ya_cargado_solo():
        # Senal de que la autolectura on-blur YA cargo el registro sola
        # (Leer debe quedar SIN clickear en ese caso), basada en DATOS
        # (que Cuenta Contable ya tenga valor, o el label "Registro
        # Desactivado" este visible) en vez del estado
        # habilitado/deshabilitado de un boton, que puede ir desfasado
        # respecto al DOM real.
        try:
            if campo_cuenta.input_value(timeout=500).strip():
                return True
        except PWTimeoutError:
            pass
        etiqueta_desactivado = frame.get_by_text(re.compile(r"registro desactivado", re.IGNORECASE))
        return bool(etiqueta_desactivado.count() and etiqueta_desactivado.first.is_visible())

    def _desbloquear_si_hace_falta():
        # El campo Concepto puede volverse "readonly disabled" tanto
        # ANTES de empezar como EN MEDIO de un reintento (render en dos
        # fases tras Eliminar/desactivar) - se llama antes de CADA
        # intento de click, no solo una vez al principio.
        if not campo.is_disabled():
            return
        for _intento_cancelar in range(4):
            try:
                frame.locator(".ant-spin-blur").first.wait_for(state="hidden", timeout=5000)
            except PWTimeoutError:
                pass
            frame.get_by_role("button", name="Cancelar", exact=True).click()
            for _espera in range(10):
                app.wait_for_timeout(300)
                if not campo.is_disabled():
                    break
            if not campo.is_disabled():
                break

    # Si el campo YA esta bloqueado mostrando exactamente el codigo
    # buscado (puede pasar justo tras crear/desactivar), no hay nada que
    # tipear - ya estamos en el estado correcto.
    try:
        valor_inicial = campo.input_value(timeout=500).strip().upper()
    except PWTimeoutError:
        valor_inicial = ""
    if campo.is_disabled() and valor_inicial == codigo.strip().upper():
        return frame

    ya_cargado = False
    for _intento in range(3):
        _desbloquear_si_hace_falta()
        campo = campo_concepto_codigo(frame)
        if campo.is_disabled():
            # Sigue bloqueado pese al desbloqueo - no forzar el click
            # (agotaria 30s de timeout), esperar un poco mas y reintentar
            # en la siguiente vuelta del for.
            app.wait_for_timeout(800)
            continue
        campo.click()
        campo.press("Control+A")
        campo.press("Delete")
        campo.press_sequentially(codigo, delay=50)
        campo.press("Tab")
        app.keyboard.press("Escape")
        # Polling PACIENTE (ver ficha tecnica: la autolectura on-blur
        # puede tardar bastante mas de lo que parece razonable) antes de
        # asumir que el Tab no disparo nada y recien ahi reintentar el
        # tipeo completo.
        resuelto = False
        for _poll in range(75):
            app.wait_for_timeout(400)
            if _ya_cargado_solo():
                ya_cargado = True
                resuelto = True
                break
            if boton_leer.is_enabled():
                # Un solo chequeo de is_enabled()==True no alcanza - se
                # exige que se vea habilitado 3 veces seguidas (~900ms)
                # antes de confiar en que de verdad es un codigo
                # nuevo/inexistente (ver ficha tecnica del modulo).
                _estable = True
                for _ in range(3):
                    app.wait_for_timeout(300)
                    if not boton_leer.is_enabled():
                        _estable = False
                        break
                if _estable:
                    resuelto = True
                    break
        if resuelto:
            break
    if not ya_cargado:
        try:
            frame.locator(".ant-spin-blur").first.wait_for(state="hidden", timeout=8000)
        except PWTimeoutError:
            pass
        if boton_leer.is_enabled():
            boton_leer.click()
            esperar_fin_de_carga(app, frame)
            app.wait_for_timeout(800)
    return frame


def crear_concepto_prueba(app, frame, codigo, descripcion, movimiento="I"):
    """Crea un concepto contable descartable de punta a punta
    (codigo+descripcion+documento+cuenta contable via el modal de
    busqueda+movimiento) y confirma."""
    campo = campo_concepto_codigo(frame)
    campo.click()
    campo.press_sequentially(codigo, delay=50)
    campo.press("Tab")
    app.wait_for_timeout(500)
    campo_desc = frame.locator("input").nth(1)
    escribir_campo(campo_desc, descripcion)
    app.keyboard.press("Escape")
    app.wait_for_timeout(300)
    frame.get_by_role("button", name="Leer", exact=True).click()
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(800)
    boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\s*$"))
    assert boton.inner_text().strip() == "Ingresar", f"Se esperaba modo Insertar para el codigo nuevo {codigo!r}, se vio el boton: {boton.inner_text()!r}"
    select_doc = frame.locator("select").first
    valores_doc = [v for v in select_doc.locator("option").evaluate_all("els => els.map(e => e.value)") if v]
    assert valores_doc, "Se esperaba al menos un tipo de documento disponible para elegir"
    select_doc.select_option(value=random.choice(valores_doc))
    app.wait_for_timeout(300)
    campo_mov = frame.locator("input").nth(3)
    campo_mov.click()
    campo_mov.press_sequentially(movimiento, delay=50)
    app.wait_for_timeout(300)
    frame.get_by_role("button", name="...", exact=True).click()
    app.wait_for_timeout(1000)
    frame.get_by_role("button", name="Buscar", exact=True).click()
    app.wait_for_timeout(1500)
    frame.locator("table tbody tr").first.dblclick()
    app.wait_for_timeout(800)
    boton.click()
    texto = confirmar_si_no(frame)
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(1200)
    return texto


def desactivar_concepto(app, frame, codigo):
    """Re-lee un concepto por codigo y lo desactiva (Eliminar). Devuelve
    (frame, texto) - frame puede ser un objeto NUEVO si releer_concepto()
    tuvo que pasar por un desbloqueo intermedio (ver su docstring) -
    siempre usar el frame devuelto de aca en adelante, no el original."""
    frame = releer_concepto(app, frame, codigo)
    frame.get_by_role("button", name="Eliminar", exact=True).click()
    texto = confirmar_si_no(frame)
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(1200)
    return frame, texto
