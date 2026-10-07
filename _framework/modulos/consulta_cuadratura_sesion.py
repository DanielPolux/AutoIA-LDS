"""
Modulo: Consulta de Cuadratura de Sesion (Web LDS)
Ruta de menu confirmada en vivo: Comercial > Consulta De Cuadratura De Sesion
Sistema/frente de negocio: Recaudacion (recauda/pagoscent/cuadrasesion)

Este archivo es el INSUMO reutilizable para generar casos de prueba de
este modulo en CUALQUIER proyecto/sprint que vuelva a tocarlo - no
depende de ningun proyecto puntual.

============================================================================
FICHA TECNICA (confirmado en vivo, PR000349-SP2, 28/09/2026)
============================================================================

**Requiere el rol funcional ANDESE - no visible en el menu para la cuenta
SCASTI_DW.** Se explorto y valido con DCABA_DW/Melquisedec_01.

A diferencia de RF-07/RF-09 (ng-zorro/Ant Design), esta pantalla es HTML
plano: `<select id="fld-oficina">` (con `(Todos)` + oficinas reales) y su
combo sincronizado `#fld-nombre-oficina`; `#fld-cajero` y `#fld-sesion` son
inputs de TEXTO con un `<datalist>` asociado (`lst-cajeros`/`lst-sesiones`,
NO son `<select>` reales, son "combo editable": aceptan cualquier valor
tecleado aunque no figure en las sugerencias); `#fld-operador` es un
`<select>` con `=`, `<=`, `>=`, `entre`; `#fld-fecha-inicio` es un
`<input type="date">` NATIVO (a diferencia del `nz-date-picker` de
RF-07/RF-09 - ver mas abajo, esto es justamente lo que lo salva del
defecto de esas 2 pantallas); al elegir operador "entre" aparece un
segundo campo `#fld-fecha-fin` (tambien `<input type="date">` nativo).
Checkbox `#fld-ampliar-campos` (deshabilitado hasta un Leer exitoso).
Botones Limpiar / "Guardar como..." / Leer (que pasa a decir "Siguiente"
tras el primer clic, para paginacion de a 50 - RN-10).

**Cascada Oficina -> Cajero (RN-06): el datalist de Cajero se VACIA (no
se llena) al elegir una Oficina especifica** - confirmado en vivo: con
"(Todos)" trae ~200 codigos de cajero; al elegir Oficina "0010" el
datalist queda vacio, porque la cascada esta acotada tambien al RANGO DE
FECHA vigente (que por defecto es "hoy" - normalmente sin sesiones para
ese dia). Esto es una cascada real funcionando, NO un bug: para probar el
flujo completo con datos reales, es mas simple TECLEAR el codigo de
cajero conocido directamente en el input (es un combo editable, RN-08)
en vez de depender del datalist.

**Cajero/Oficina reales confirmados con datos historicos**: Oficina
"0010" (Chacarilla) + Cajero "1324" + operador "<=" + fecha inicial
"01/01/2026" trae 50 filas reales (sesiones 0002-0004, fecha real de
sesion 9/6/2005 - los datos de prueba en Pruebas son historicos, no del
dia de hoy).

**GOTCHA CRITICO DE TIMING - MUY IMPORTANTE, distinto de "freeze"
real: el clic en "Leer" (o en "Guardar como...") dispara una consulta
que puede tardar HASTA ~60 SEGUNDOS en responder** (mucho mas lento que
cualquier otra pantalla de este proyecto, incluida RF-07 con sus 10-15s).
Mientras esa consulta esta en curso, CUALQUIER operacion de Playwright
que necesite evaluar JS dentro del frame (`is_enabled()`, `input_value()`,
`inner_text()`, incluso un `click()` nuevo) se queda esperando hasta SU
PROPIO timeout (tipicamente 30s) antes de fallar o de finalmente
responder - dando la falsa impresion de que la pantalla esta "congelada"
igual que el defecto real de RF-07/RF-09. La diferencia clave, confirmada
en vivo: aca NO es un defecto, es una consulta lenta que SI termina bien
sola (sin excepcion JS, sin error de consola) - basta con esperar con un
`app.wait_for_timeout(...)` (que no toca el frame, por lo que no se
bloquea) el tiempo suficiente ANTES de intentar leer el frame. Usar
SIEMPRE `leer_cuadratura_sesion()` (espera ciega de bloque, no un sondeo
que toque el frame a cada rato - un sondeo corto Y FRECUENTE es
CONTRAPRODUCENTE aca, porque cada intento de tocar el frame durante la
consulta puede el mismo tardar hasta 30s en resolver).

**Mensajes reales confirmados** (via modal "Ventana de Validación",
icono "i", boton "Aceptar" - RN-07):
- "Debe ingresar los dos valores del rango." (operador "entre" con solo 1 fecha)
- "Fecha inicial debe ser menor o igual que fecha final." (fecha inicial > fecha final)

**Confirmacion real confirmada** (modal "Confirmación", icono "?",
botones "Cancelar"/"Aceptar" - RN-09, al presionar Leer con Oficina,
Cajero y Sesion los 3 vacios):
"No ha seleccionado ningún filtro, se mostrarán todos los pagos entre
las fechas seleccionadas. ¿Desea continuar?"

**Ampliar Campos (RN-12) confirmado**: la casilla queda deshabilitada
hasta un Leer exitoso; al marcarla, la grilla pasa de 11 a 39 columnas
(detalle monetario extendido).

**"Guardar como..." (RN-14/15/16) confirmado**: es una descarga real de
archivo de texto (Playwright: evento `download`, NO un dialogo nativo de
guardado ni un `page.on("dialog")`), nombre
`CuadraturaSesion_<timestamp>.txt`. Vuelve a ejecutar la consulta
COMPLETA (mismo gotcha de ~60s) antes de generar el archivo. El archivo
exportado trae una fila de encabezado con 39 columnas pero cada fila de
datos real solo trae ~20 valores (columnas de mas en el encabezado que
datos reales) - comportamiento heredado documentado en el EF (RN-16), NO
un bug de esta automatizacion.

**Por que esta pantalla SI se pudo probar con fecha valida y RF-07/RF-09
NO**: la fecha aca es un `<input type="date">` NATIVO del navegador; el
defecto real de freeze de RF-07/RF-09 esta acotado al componente
`nz-date-picker` (ng-zorro) - confirmado por contraste directo, no por
suposicion.
============================================================================
"""

import re
import time
from playwright.sync_api import TimeoutError as PWTimeoutError


def abrir_consulta_cuadratura_sesion(page, paso_excel=None):
    return abrir_aplicacion(page, ["Comercial", "Consulta De Cuadratura De Sesion"], "app-cuadratura-sesion", paso_excel=paso_excel)


def leer_cuadratura_sesion(app, frame, timeout_ms=90000, espera_bloque_ms=60000):
    """Pulsa Leer y espera el resultado. Las validaciones (RN-07) y la
    confirmacion (RN-09) son de cliente y aparecen de inmediato: se
    detectan leyendo el texto del body justo despues del clic. Si NO
    aparecio ningun modal, es una consulta real (lenta, ver ficha
    tecnica) - se espera en UN SOLO bloque `espera_bloque_ms` SIN tocar
    el frame (un sondeo corto y frecuente es contraproducente aca: cada
    intento de leer el frame mientras la consulta esta en curso puede el
    mismo tardar hasta 30s). Devuelve el texto del modal si aparecio, o
    None si la busqueda real termino (con o sin resultados)."""
    boton_leer = frame.get_by_role("button", name=re.compile(r"^\s*(Leer|Siguiente)\s*$"))
    boton_leer.click()
    app.wait_for_timeout(1200)
    texto = frame.locator("body").inner_text()
    if "Ventana de Validaci" in texto or "Confirmaci" in texto:
        return texto
    app.wait_for_timeout(espera_bloque_ms)
    plazo = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < plazo:
        try:
            texto = frame.locator("body").inner_text(timeout=15000)
            return texto if ("Ventana de Validaci" in texto or "Confirmaci" in texto) else None
        except PWTimeoutError:
            app.wait_for_timeout(10000)
    raise PWTimeoutError(f"leer_cuadratura_sesion: no termino en {timeout_ms + espera_bloque_ms}ms")


def cerrar_modal_cuadratura(frame, boton="Aceptar"):
    frame.get_by_role("button", name=re.compile(rf"^\s*{boton}\s*$")).click()


def filas_cuadratura_sesion(frame):
    return frame.locator("table.grid tbody tr")
