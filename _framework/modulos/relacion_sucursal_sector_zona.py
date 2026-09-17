"""
Modulo: Relacion Sucursal - Sector - Zona (Web LDS)
Componente Angular: app-susec-zona-list
Ruta de menu confirmada en vivo: Interno > Relación Sucursal - Sector - Zona

Ficha tecnica (confirmado en vivo, PR000325-SP3, 16/09/2026):
Pantalla de Filtros (Sucursal, <select>) + Rango (Sector Inicio/Fin, Zona
Inicio/Fin, TODOS <select>, no inputs libres) + grilla con columnas
SECTOR/ZONA/BENEFICIARIO FISE. Boton unico "Ingresar"/"Modificar" segun
si hay fila seleccionada (igual que Sprint 2, ver boton_grabar() en los
helpers genericos) - a diferencia de RF-01 donde son 2 botones separados.
Dialogo de confirmacion usa botones "Si"/"No" (no "Aceptar"/"Cancelar"
como RF-01) - ver confirmar_si_no() en los helpers genericos.

Ninguna sucursal del ambiente de pruebas tenia rangos precargados al
momento de explorar - todos los casos crean su propio dato descartable
con crear_rango_prueba() en vez de asumir datos reales existentes.

BUG/regla de negocio real confirmada en vivo (16/09/2026): la combinacion
Sector/Zona debe ser UNICA A NIVEL GLOBAL (entre TODAS las sucursales, no
solo dentro de la seleccionada) - crear un rango con una combinacion ya
usada por OTRA sucursal responde "La combinacion Sector X / Zona Y ya
esta asignada a otra sucursal." Hay bastante dato real precargado (varias
combinaciones bajas, Sector 01-03, ya estaban ocupadas durante la
exploracion) - se sortea con random.choice/randint sobre TODO el rango
disponible (no un contador secuencial ni time.time() de baja entropia).

"Leer" puede quedar deshabilitado de forma persistente si, tras
seleccionar una NUEVA sucursal, se intenta un segundo "Leer" filtrado
(Sector/Zona) inmediatamente despues del primero (blanco) - patron NO
resuelto del todo; el workaround confirmado es hacer UN solo "Leer" en
blanco por cambio de sucursal y buscar la fila deseada del lado cliente
en la grilla completa (ver buscar_fila_rango/esperar_fila_rango) en vez
de un segundo Leer filtrado.

CASO CP015 (Replicacion a sucursal "0000") - hallazgo confirmado en vivo
el 16/09/2026: la replicacion de un rango Sector/Zona hacia la sucursal
especial "0000" (Sin Sucursal) SI ocurre (reproducido a mano por el
usuario, con video propio), pero la automatizacion NO logro verla en 2
corridas automatizadas seguidas releyendo "0000" inmediatamente despues
de crear el rango (ni siquiera con una espera deliberada de 100s antes de
releer). Hipotesis: delay/proceso batch corto entre la creacion y la
replicacion visible en 0000, mas rapido para una sesion manual (mas
lenta en general) que para la automatizacion. Si un caso depende de ver
un rango replicado en 0000, considerar esta limitacion de timing conocida
antes de marcarlo como fallo real de la app.

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
Y helpers GENERICOS del proyecto (no especificos de este modulo, ver
NUEVO_PROYECTO_CHECKLIST.md Seccion 0c): boton_grabar, confirmar_si_no,
SELECTOR_DIALOGO.
"""
import random


def abrir_relacion_sucursal_sector_zona(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Relación Sucursal - Sector - Zona"], "app-susec-zona-list", paso_excel=paso_excel)


def elegir_sector_zona_libre(app, frame, intentos=15):
    """Generador: en cada iteracion selecciona un Sector/Zona al azar
    (sobre TODO el rango de opciones disponibles) y hace yield
    (sector, zona) para que el llamador intente crear el rango - ver
    crear_rango_prueba()."""
    selects = frame.locator("select")
    sector_ini, sector_fin, zona_ini, zona_fin = selects.nth(1), selects.nth(2), selects.nth(3), selects.nth(4)
    sectores_validos = sector_ini.locator("option").evaluate_all("els => els.map(e => e.value).filter(v => v)")
    for _intento in range(intentos):
        sector = random.choice(sectores_validos)
        zona = str(random.randint(1, 999)).zfill(3)
        sector_ini.select_option(value=sector)
        sector_fin.select_option(value=sector)
        zona_ini.select_option(value=zona)
        zona_fin.select_option(value=zona)
        app.wait_for_timeout(300)
        yield sector, zona


def crear_rango_prueba(app, frame, fise=False, intentos=15):
    """Crea un rango Sector/Zona descartable para pruebas, reintentando
    con otra combinacion si la elegida ya esta asignada a otra sucursal
    (ver elegir_sector_zona_libre)."""
    checkbox = frame.locator("input[type=checkbox]").first
    if fise:
        checkbox.check()
    else:
        checkbox.uncheck()
    ultimo_texto = ""
    for sector, zona in elegir_sector_zona_libre(app, frame, intentos=intentos):
        boton_grabar(frame).click()
        ultimo_texto = confirmar_si_no(frame)
        print(f"[DEBUG] intento Sector={sector} Zona={zona} -> {ultimo_texto.strip()[:120]!r}")
        if "asignada a otra sucursal" not in ultimo_texto.lower():
            return sector, zona, ultimo_texto
    raise AssertionError(f"No se pudo crear un rango de prueba tras {intentos} intentos - ultimo mensaje: {ultimo_texto!r}")


def buscar_fila_rango(frame, sector, zona):
    """Busca la fila de la grilla que corresponde a un Sector/Zona dados
    - la grilla muestra los codigos SIN ceros a la izquierda (ej.
    '01'->'1', '001'->'1'), a diferencia del select que usa el codigo con
    padding, por lo que no alcanza un substring match directo."""
    filas = frame.locator("table.g tbody tr")
    for i in range(filas.count()):
        fila = filas.nth(i)
        celdas = fila.locator("td").all_inner_texts()
        if len(celdas) >= 2 and celdas[0].strip() == str(int(sector)) and celdas[1].strip() == str(int(zona)):
            return fila
    return None


def esperar_fila_rango(app, frame, sector, zona, aparece=True, intentos=24, espera_ms=500):
    """Tras confirmar una accion la grilla queda unos instantes en
    estado transitorio antes de reflejar el cambio - se hace polling
    explicito en vez de asumir que ya esta actualizada tras el primer
    chequeo."""
    fila = None
    for _ in range(intentos):
        fila = buscar_fila_rango(frame, sector, zona)
        if (fila is not None) == aparece:
            return fila
        app.wait_for_timeout(espera_ms)
    return fila
