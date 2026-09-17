"""
Modulo: Actualizacion De Documentos (Web LDS)
Componente Angular: app-documentos-list
Ruta de menu confirmada en vivo: Interno > Actualización De Documentos

Ficha tecnica (confirmado en vivo, PR000325-SP3, 16/09/2026):
Pantalla "Tipo de Documento": campo Tipo (input maxlength=1, UNA letra) +
un combo con todos los tipos existentes (SOLO visible cuando Tipo esta
vacio o tiene una letra YA existente - se reemplaza por un input de
Descripcion editable de maxlength=30 cuando la letra es NUEVA) +
checkbox "Ind. Actualiza". Boton unico Ingresar/Modificar (boton_grabar,
helper generico).

En el ambiente de pruebas ya habia 10 tipos reales cargados
(A,B,C,E,F,O,P,R,X,Z - Z es "PRUEBA", posible dato de prueba dejado de
otra sesion). Como Tipo es UNA SOLA LETRA (sin margen para sufijos unicos
tipo time.time()), los casos que crean datos usan letras_tipo_libres()
para elegir una letra REALMENTE libre y la ELIMINAN al final
(eliminar_tipo), para no agotar el pool limitado de 26 letras entre
corridas repetidas.

BUG REAL confirmado en vivo (16/09/2026): el campo Tipo queda
DESHABILITADO despues de cualquier Leer exitoso (no solo despues de
guardar) - si se necesita volver a escribir en el (ej. releer otro tipo,
o limpiar uno recien creado), hay que pasar por "Cancelar" primero. Tanto
crear_tipo_prueba() como eliminar_tipo() ya hacen este chequeo antes de
escribir.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
Y helpers GENERICOS del proyecto (no especificos de este modulo, ver
NUEVO_PROYECTO_CHECKLIST.md Seccion 0c): escribir_campo, confirmar_si_no,
SELECTOR_DIALOGO.
"""
import re


def abrir_actualizacion_documentos(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Actualización De Documentos"], "app-documentos-list", paso_excel=paso_excel)


def campo_tipo_documento(frame):
    return frame.locator("input").first


def letras_tipo_libres(frame):
    """El campo "Tipo" es una unica letra (maxlength=1, sin margen para
    sufijos tipo time.time()) - enumera las letras YA USADAS desde el
    combo (solo visible con el campo Tipo vacio, en la pantalla inicial)
    para elegir una libre y no chocar con tipos reales ni agotar el pool
    de 26 letras posibles entre corridas repetidas."""
    select = frame.locator("select").first
    usadas = set(v for v in select.locator("option").evaluate_all("els => els.map(e => e.value)") if v)
    return [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in usadas]


def crear_tipo_prueba(app, frame, letra, descripcion, actualiza=False):
    """Crea un tipo de documento descartable. Se espera llamar con la
    pantalla en su estado inicial (Tipo vacio), pero por las dudas
    tambien pasa por "Cancelar" si el campo Tipo ya esta deshabilitado
    (ver eliminar_tipo)."""
    campo_tipo = campo_tipo_documento(frame)
    if campo_tipo.is_disabled():
        frame.get_by_role("button", name="Cancelar", exact=True).click()
        app.wait_for_timeout(500)
    campo_tipo.click()
    campo_tipo.press_sequentially(letra, delay=50)
    frame.get_by_role("button", name="Leer", exact=True).click()
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(1200)
    campo_desc = frame.locator("input").nth(1)
    escribir_campo(campo_desc, descripcion)
    if actualiza:
        frame.locator("input[type=checkbox]").first.check()
    boton = frame.get_by_role("button", name=re.compile(r"^(Ingresar|Modificar)\s*$"))
    boton.click()
    texto = confirmar_si_no(frame)
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(1200)
    return texto


def eliminar_tipo(app, frame, letra):
    """Elimina (desactiva) un tipo de documento por su letra - usado
    para limpiar los tipos descartables creados por las pruebas y no
    agotar el pool limitado de letras libres."""
    campo_tipo = campo_tipo_documento(frame)
    if campo_tipo.is_disabled():
        frame.get_by_role("button", name="Cancelar", exact=True).click()
        app.wait_for_timeout(500)
    campo_tipo.click()
    campo_tipo.press("Control+A")
    campo_tipo.press("Delete")
    campo_tipo.press_sequentially(letra, delay=50)
    frame.get_by_role("button", name="Leer", exact=True).click()
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(1200)
    frame.get_by_role("button", name="Eliminar", exact=True).click()
    texto = confirmar_si_no(frame)
    esperar_fin_de_carga(app, frame)
    app.wait_for_timeout(1200)
    return texto
