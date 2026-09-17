"""
Modulo: Actualizacion De Agenda De Pagos (Web LDS)
Componente Angular: app-agenda-pagos-list
Ruta de menu confirmada en vivo: Interno > Actualización De Agenda De Pagos

Ficha tecnica (confirmado en vivo, PR000325-SP3, 16/09/2026):
Pantalla MUY simple - 2 radios FIJOS "Cia. Electrica"/"Otras
Instituciones" (NO hay una lista/select de "otras instituciones", son
solo estas 2 opciones fijas, pese a lo que sugiere el nombre) + 1 campo
"Numero de Dias" (input de texto sin id/name - usar campo_por_etiqueta o
directo como primer input[type=text]).

Boton unico Ingresar/Modificar (boton_grabar, helper generico) que
cambia de texto segun si el campo TIENE VALOR, NO segun si el registro
"existe" en BD - un registro con Numero de Dias vacio se trata como
"Ingresar" aunque conceptualmente la institucion siempre existe.

Dialogo Si/No igual que RF-02 ("¿Esta seguro de la actualizacion a
realizar?") seguido de un dialogo de resultado con Aceptar ("Registro
Actualizado."/"Registro Ingresado.") - mismo confirmar_si_no() generico,
pero aca ese 2do dialogo puede tardar MAS de 3s en aparecer (usar el
timeout_siguientes mas generoso de confirmar_si_no, no el default corto).

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
Y helpers GENERICOS del proyecto (no especificos de este modulo, ver
NUEVO_PROYECTO_CHECKLIST.md Seccion 0c): boton_grabar, confirmar_si_no,
campo_por_etiqueta, SELECTOR_DIALOGO.
"""


def abrir_actualizacion_agenda_pagos(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Actualización De Agenda De Pagos"], "app-agenda-pagos-list", paso_excel=paso_excel)


def esperar_valor_campo(app, campo, valor_esperado=None, intentos=20, espera_ms=500):
    """Tras "Leer" la grilla/campo queda unos instantes en un estado
    transitorio (spinner sin boton "Cargando..." detectable, mismo
    patron de RF-01/RF-02) antes de reflejar el valor real - se hace
    polling explicito sobre el VALOR del campo en vez de leerlo una sola
    vez. Si `valor_esperado` es None, espera a que el campo tenga
    CUALQUIER contenido (no vacio)."""
    valor = campo.input_value().strip()
    for _ in range(intentos):
        if (valor_esperado is not None and valor == valor_esperado) or (valor_esperado is None and valor):
            break
        app.wait_for_timeout(espera_ms)
        valor = campo.input_value().strip()
    return valor
