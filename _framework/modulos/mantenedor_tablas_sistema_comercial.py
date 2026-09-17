"""
Modulo: Mantenedor De Tablas Del Sistema Comercial (Web LDS)
Componente Angular: app-mantenedor-tablas-list
Ruta de menu confirmada en vivo: Interno > Mantenedor De Tablas Del Sistema Comercial

Ficha tecnica (confirmado en vivo, PR000325-SP3, 15/09/2026):
Estructura de 2 niveles:
  - Nivel 1: catalogo de "tablas" (ej. ACRECO/ACRERE/ACTECO/AGRUPA/
    ALMMED/AMBUSO/BANCOS/BCOCTA/CALCUO... - datos reales ya cargados de
    entrada, sin necesidad de buscar). Grilla `table.g tbody tr`.
  - Nivel 2: codigos DENTRO de una tabla de Nivel 1 (ej. dentro de
    ACRECO: 10=CORTE FUSIBLE 0000, 20=CORTE CABLE, 26=CORTE ENCINTADO).
    Se entra con DOBLE CLICK sobre la fila de Nivel 1 (NO con
    seleccionar + Leer, que solo repite la busqueda de Nivel 1) - ver
    entrar_nivel2(). El boton "Volver >>" regresa a Nivel 1.

BUG REAL / carrera confirmada en vivo (CP005, 15/09/2026): Angular
selecciona la PRIMERA fila de Nivel 2 de forma ASINCRONA poco despues de
entrar - si se empieza a escribir en el campo Codigo demasiado rapido,
esa seleccion tardia SOBRESCRIBE lo ya tecleado (quedaba con el codigo
de la fila 1, ej. "10", en vez del valor nuevo). entrar_nivel2() ya
espera un margen fijo extra para que esa seleccion inicial termine antes
de que el caso siga.

TOPE de 30 filas confirmado en vivo (CP005/CP008, 17/09/2026): la grilla
de Nivel 2 solo trae los primeros 30 codigos de esa tabla (ordenados
ascendente: numeros primero, despues letras) - NO es paginacion ni
virtualizacion (forzar scroll no trae mas filas, el conteo real en el
DOM se queda en 30). Un codigo de prueba con prefijo "Y"/"Z" ordena al
FINAL y, apenas la tabla acumula basura de corridas previas (nunca se
borra - "Eliminar" es baja LOGICA, marca "*" pero la fila sigue
ocupando un lugar), el codigo recien creado queda FUERA de esas 30 filas
- no aparece ni con scroll, aunque el insert en si haya funcionado
(dialogo de exito real). Si tu caso necesita interactuar con la fila
recien creada (click, Eliminar, etc.) y no solo verificar el mensaje de
exito, usa un prefijo que ordene TEMPRANO (ej. "A" + digitos, que cae
antes que los codigos reales de 2 letras tipo "AO") para que se mantenga
siempre dentro de esas 30 filas.

Requiere del framework compartido (web_lds_core.py, ya inyectado en la
plantilla de cada proyecto via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, capturar_paso
Y helpers GENERICOS del proyecto (no especificos de este modulo, ver
NUEVO_PROYECTO_CHECKLIST.md Seccion 0c): escribir_campo, confirmar_si_no,
SELECTOR_DIALOGO.
"""


def abrir_mantenedor_tablas(page, paso_excel=1):
    return abrir_aplicacion(page, ["Interno", "Mantenedor De Tablas Del Sistema Comercial"], "app-mantenedor-tablas-list", paso_excel=paso_excel)


def entrar_nivel2(app, frame, fila_index=0):
    """Entra al Nivel 2 (codigos dentro de una tabla) con DOBLE CLICK
    sobre la fila de Nivel 1 elegida (fila_index, 0 = primera)."""
    frame.locator("table.g tbody tr").nth(fila_index).dblclick()
    app.wait_for_timeout(1500)
