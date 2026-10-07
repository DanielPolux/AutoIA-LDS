"""
Modulo: Mantenimiento de Informes DWH (Web LDS)
Componente Angular: app-mantenimiento-informes
Ruta de menu confirmada en vivo: Comercial > Mantenimiento De Informes Dwh
Sistema/frente de negocio: Aprobacion de Informes del Datawarehouse

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP1, 26/09/2026)
============================================================================

Pantalla Angular simple (sin ng-zorro): 2 `<select>` (Informe,
Agrupacion - el 2do se RECALCULA segun el 1ro, ej. "Morosidad Semanal"
no tiene NINGUNA agrupacion configurada) + boton "Leer" -> grilla de
grupos (`table.g`). Seleccionar una fila carga "DETALLE DEL GRUPO" en
solo-lectura; "Nuevo"/"Modificar" habilitan los campos (Descripcion,
Tipo radio Blanco/Elemento/Formula/Texto, Formato, Valor1/2, Texto1/2).

"Guardar" y "Eliminar" SIEMPRE piden confirmacion via `.ant-modal`
("¿Desea guardar los cambios realizados?" / "¿Desea eliminar el
grupo?"). El boton "Leer" exige AMBOS combos (Informe Y Agrupacion)
elegidos - queda deshabilitado si falta cualquiera de los dos.

"Ordenar" cambia la grilla a modo reordenamiento (columna "#"
recalculada 1..N secuencial, botones Inicio/Subir/Bajar/Fin) y el boton
de guardar pasa a decir "Guardar Orden" - el nuevo orden persiste al
volver a consultar.

**Crear un grupo (tipo Blanco) recibe el siguiente numero de orden
disponible** (confirmado en vivo: grupo creado quedo con el numero
inmediatamente posterior al maximo existente). **Crear un grupo tipo
Elemento** habilita mover elementos entre "No seleccionados"/
"Seleccionados" (tabla dual con botones Agregar/Quitar/Agregar todos/
Quitar todos) - el elemento movido queda asignado tras Guardar.
**Eliminar** deja el grupo fuera de toda consulta posterior (baja
logica, no vuelve a aparecer al re-Leer).

**Buena practica al escribir casos**: usar un informe poco tocado (ej.
"Liquidacion de IGV") en vez del mas usado en produccion ("Informe de
Ventas") para las pruebas de escritura, y ELIMINAR cualquier grupo de
prueba creado al final de cada caso (verificado con un Leer posterior
mostrando la grilla de vuelta a su tamaño original).
============================================================================
"""

import re
from playwright.sync_api import TimeoutError as PWTimeoutError


def abrir_mantenimiento_informes_dwh(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Mantenimiento De Informes Dwh"], "app-mantenimiento-informes", paso_excel=paso_excel)


def confirmar_dialogo_mantenimiento_informes(app, frame, timeout_ms=4000):
    dialogo = frame.locator(".ant-modal, nz-modal-container").filter(has_text=re.compile(r".", re.S))
    try:
        dialogo.first.wait_for(state="visible", timeout=timeout_ms)
    except PWTimeoutError:
        return None
    texto = dialogo.first.inner_text()
    dialogo.first.get_by_role("button", name=re.compile(r"S[ií]|Aceptar|Confirmar", re.I)).first.click()
    app.wait_for_timeout(1200)
    return texto


def leer_grupos_informe(app, frame, informe_val, agrupacion_val):
    selects = frame.locator("select")
    selects.nth(0).select_option(informe_val)
    app.wait_for_timeout(400)
    selects.nth(1).select_option(agrupacion_val)
    app.wait_for_timeout(400)
    frame.get_by_role("button", name=re.compile("Leer")).click()
    app.wait_for_timeout(1200)


def fila_grupo_informe(frame, texto):
    return frame.locator("table.g").first.locator("tbody tr", has_text=texto)
