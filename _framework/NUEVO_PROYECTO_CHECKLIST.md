# Checklist para automatizar un proyecto nuevo de Web LDS

Receta para replicar lo que se hizo en **PR000335** (123 casos, "Consulta
De Atenciones Comerciales") en cualquier proyecto nuevo del portal Web
LDS. Úsala como prompt/guía al arrancar — no hace falta reinventar nada
de lo que ya se resolvió ahí.

Antes de empezar, lee `web_lds_core.py` (mismo directorio): tiene todo lo
portal-genérico ya armado y probado (login, navegación, cursor de video,
Word de evidencia, etc.). Este checklist es solo el "pegamento" que falta
por proyecto.

> **Nota de versión:** desde el 11/09/2026 la estructura recomendada para
> proyectos **nuevos** es la de una sola carpeta raíz (ver Sección 0).
> `PR000335` y `PR000325` se armaron con la estructura anterior (documentos
> en `C:\AUTOMATIZACION_LDS\PR0000NN\` y scripts en
> `C:\Proyectos\PlataformaWeb\automation\PR0000NN\`, repartidos en 2
> raíces) y **no se migraron** — siguen ahí, funcionando igual. Úsalos como
> referencia de código, pero para un proyecto nuevo seguí esta versión.

## 0. Estructura de carpetas (una sola raíz)

Todo un proyecto — documentos que entregan, scripts, evidencia generada y
reportes — vive **dentro de una sola carpeta**, junto al framework
compartido. Ventaja práctica: VS Code / Claude Code solo necesitan permiso
de acceso a **una** carpeta raíz (`C:\AUTOMATIZACION_LDS\`) para todo el
flujo, en vez de tener que autorizar 2 árboles de carpetas distintos.

```
C:\AUTOMATIZACION_LDS\                    <- LA carpeta raiz (unica)
  _framework\                             <- compartido, NO tocar por proyecto
    modulos\                              <- ficha tecnica + helpers por aplicativo (ver Seccion 0c)
      actualizacion_precios.py
    web_lds_core.py
    extraer_matriz.py
    extraer_docx.py
    nuevo_proyecto.py                     <- bootstrap en un solo comando (ver 0b)
    run_all.py                            <- plantilla, se copia tal cual
    generar_reporte_excel.py              <- reporte consolidado OK/NO OK/Fallido (ver Seccion 6)
    sesion_manual_con_red.py              <- reproducir defectos reales con logging de red (ver Seccion 3)
    NUEVO_PROYECTO_CHECKLIST.md           <- este archivo
    MANUAL_NUEVO_PROYECTO.docx            <- version Word de este checklist

  PR0000NN\                               <- TODO este proyecto, en un solo lugar
    documentos\                           <- lo que entrega el cliente/negocio
      MCP-PR0000NN-....xlsx               <- matriz de casos (SIEMPRE llega esta)
      EF-PR0000NN-....docx                <- Especificacion Funcional (a veces)
      ET-PR0000NN-....docx                <- Diseno Tecnico (a veces)
      EF_texto.txt, EF_media\             <- generados al extraer el EF
      ET_texto.txt, ET_media\             <- generados al extraer el ET, si hay
    _exploracion\                         <- capturas/scripts descartables del paso 2
    matriz_casos.json                     <- salida de extraer_matriz.py
    generate_scripts.py                   <- TU fuente de verdad (nueva, usa el framework)
    run_all.py                            <- copia textual de _framework\run_all.py
    CPxxx.py                              <- generados, uno por caso
    CPxxx\                                <- evidencia de cada caso (se crea sola)
    reportes\                             <- CSV + logs (se crea sola al correr run_all.py)
```

**Importante:** el nombre de la carpeta del proyecto (`PR0000NN`) es el
prefijo que usan las variables de entorno (`PR0000NN_VIDEO`, etc.) y lo
que `run_all.py` autodetecta solo — no hace falta escribirlo a mano en
ningún lado nuevo.

## 0b. Un solo comando para arrancar (bootstrap)

En vez de crear carpetas y correr `extraer_matriz.py`/`extraer_docx.py` a
mano uno por uno, `nuevo_proyecto.py` hace todo el trabajo mecánico de una
sola vez:

```
.venv\Scripts\python.exe C:\AUTOMATIZACION_LDS\_framework\nuevo_proyecto.py PR0000NN ^
    --excel "C:\ruta\donde\te\lo\dejaron\MCP-PR0000NN-....xlsx" ^
    --ef "C:\ruta\EF-PR0000NN-....docx" ^
    --et "C:\ruta\ET-PR0000NN-....docx"
```

(`--ef`/`--et` son opcionales — omitirlos si no te los dieron.)

Esto, en un solo comando:

1. Crea `C:\AUTOMATIZACION_LDS\PR0000NN\` y `PR0000NN\documentos\`.
2. Copia el Excel (y EF/ET si se pasaron) a `documentos\`.
3. Corre `extraer_matriz.py` -> `PR0000NN\matriz_casos.json`.
4. Corre `extraer_docx.py` sobre EF/ET si se pasaron -> `documentos\EF_texto.txt`
   + `EF_media\` (ídem ET).
5. Deja un `generate_scripts.py` **esqueleto** (a completar a mano — ver
   Paso 3, el cuerpo de cada caso no es automatizable) y copia
   `run_all.py` tal cual.

Lo que **no** hace (adrede, no es automatizable): la exploración en vivo
(Paso 2) ni escribir el cuerpo real de cada caso (Paso 3). Al terminar,
imprime esos próximos pasos manuales en pantalla.

Si preferís hacerlo a mano paso a paso (o `nuevo_proyecto.py` no cubre tu
caso), los Pasos 1 y 1b de abajo son exactamente lo que hace por dentro.

## 0c. Módulos por aplicativo (reutilizables entre proyectos)

**Convención agregada 16/09/2026, validada con un piloto real (RF-06
"Actualización De Precios" de PR000325-SP3, 10 casos, corridos contra la
app real).** Cuando un aplicativo de Web LDS (una pantalla/componente
Angular puntual — "Actualización de Precios", "Consulta a Clientes",
etc.) es candidato a volver a tocarse en un sprint/proyecto futuro
(la mayoría lo son — son pantallas del mismo portal, no algo de un solo
uso), su ficha técnica + helpers **no van inline en el
`generate_scripts.py` del proyecto**: van en un archivo propio dentro de
`_framework\modulos\`, con el nombre del aplicativo:

```
_framework\
  modulos\
    actualizacion_precios.py      <- ejemplo real, ya armado (PR000325-SP3, RF-06)
    consulta_clientes.py          <- ejemplo, cuando llegue un proyecto que lo toque
```

**Qué va en un archivo de módulo** (ver `actualizacion_precios.py` como
referencia real):
1. **Docstring del módulo** = la ficha técnica: componente Angular, ruta
   de menú, estructura real de la pantalla, mensajes exactos del
   sistema, y sobre todo los **bugs/gotchas confirmados en vivo** (para
   que la próxima vez que se toque este aplicativo no haga falta
   re-descubrirlos).
2. **Funciones helper** específicas de ese aplicativo (ej.
   `leer_precio`, `crear_tramo`) — sin nada del proyecto puntual que las
   usó primero (nada de `matriz_casos.json`, nada de números de CP).

**Qué NO va ahí:** los cuerpos de caso (`add("CPxxx", ...)`) — esos son
siempre del proyecto/matriz puntual, quedan en el `generate_scripts.py`
de cada `PR0000NN`.

**Cómo lo usa el `generate_scripts.py` de un proyecto:** importa el
módulo de verdad (no copia/pega texto a mano) y usa `inspect.getsource()`
para volcar su código como texto en cada `CPxxx.py` generado — así el
`CPxxx.py` final sigue siendo 100% autónomo (sin dependencia de
`_framework` en tiempo de EJECUCIÓN, misma prioridad que ya aplica a
`web_lds_core.py`), pero la fuente de la lógica del módulo vive en un
solo lugar:

```python
import sys
sys.path.insert(0, str(FRAMEWORK_DIR / "modulos"))
import actualizacion_precios as modulo_rf06

HELPERS_RF06 = fuente_modulo(modulo_rf06)   # ver la función fuente_modulo()
                                             # del piloto en _sandbox_modulos/
                                             # RF06_piloto/generate_scripts.py
                                             # como referencia para escribirla
```

**Gotcha real confirmado en vivo al armar el piloto:** la ficha técnica
del módulo NO puede mencionar literalmente la sintaxis `%%NOMBRE%%` de
los placeholders de la plantilla (ej. escribir "esto viene de
`%%HELPERS_ESPERA%%`" como texto explicativo) — el `.replace()` que
inyecta esos bloques en el `CPxxx.py` final no distingue el placeholder
real de una mención accidental en un comentario, y reemplaza AMBOS,
corrompiendo el archivo generado (síntoma: `SyntaxError` en un lugar que
no tiene nada que ver con tu caso). Si necesitás referirte a esos
nombres en la documentación de un módulo, escribilos sin los `%%` (ej.
"los bloques NAV / HELPERS_ESPERA de la plantilla").

**Cuándo NO crear un módulo separado:** si una pantalla es genuinamente
de un solo uso (poco probable en Web LDS, pero puede pasar), no hace
falta el archivo aparte — dejá los helpers inline en el
`generate_scripts.py` del proyecto como se hacía antes. La convención es
"por defecto sí, salvo que se sepa que no se va a reusar", no al revés.

**Helpers genuinamente genéricos** (usados por CASI cualquier
aplicativo, no específicos de uno — `escribir_campo`,
`confirmar_si_no`, `SELECTOR_DIALOGO`, `dialogo_visible`, `confirmar`,
`boton_grabar`, `campo_por_etiqueta`) siguen sin un hogar definitivo:
hoy se repiten inline en cada `generate_scripts.py` (copiados del
proyecto anterior). Son candidatos a subir a `web_lds_core.py` en una
siguiente iteración de esta convención, pero **eso queda pendiente** —
por ahora seguí copiándolos inline como siempre.

## 1. Extraer la matriz de casos (Excel -> JSON) — manual, si no usaste 0b

```
.venv\Scripts\python.exe -m pip install openpyxl   # solo si no esta instalado
.venv\Scripts\python.exe C:\AUTOMATIZACION_LDS\_framework\extraer_matriz.py ^
    "C:\AUTOMATIZACION_LDS\PR0000NN\documentos\MCP-PR0000NN-....xlsx" ^
    C:\AUTOMATIZACION_LDS\PR0000NN\matriz_casos.json
```

Revisar la salida: si faltan columnas obligatorias (`cp`, `pasos`) el
script avisa con los encabezados que sí encontró — ajustar el diccionario
`COLUMNAS` de `extraer_matriz.py` (en el framework, beneficia a todos los
proyectos futuros) si el Excel usa nombres de columna distintos a los de
PR000335.

Con `matriz_casos.json` ya tienes `rf/cu/name/desc/precond/datos/esperado/pasos`
por caso — no hace falta re-tipear estos campos a mano al llamar `add(...)`
en `generate_scripts.py` (ver paso 3).

## 1b. Extraer EF/ET (Word) a texto + imágenes — manual, si no usaste 0b

Cuando el proyecto viene con Especificación Funcional (EF) y/o Diseño
Técnico (ET) en `.docx` (no siempre — a veces solo dan Excel + EF),
conviene extraerlos a texto plano + imágenes sueltas para poder leerlos
como contexto sin abrir el binario:

```
.venv\Scripts\python.exe C:\AUTOMATIZACION_LDS\_framework\extraer_docx.py ^
    "C:\AUTOMATIZACION_LDS\PR0000NN\documentos\EF-PR0000NN-....docx"
.venv\Scripts\python.exe C:\AUTOMATIZACION_LDS\_framework\extraer_docx.py ^
    "C:\AUTOMATIZACION_LDS\PR0000NN\documentos\ET-PR0000NN-....docx"
```

Genera `EF_texto.txt`/`EF_media\` y `ET_texto.txt`/`ET_media\` junto a
cada `.docx` (prefijo autodetectado del nombre del archivo; usar
`--prefijo` si hace falta forzarlo).

**Ojo con confiar en el EF/ET a ciegas**: en PR000335 la ruta de menús y
varios selectores reales terminaron siendo distintos de lo que mostraba
el EF (ver "Navegación real (confirmada, no es la del EF/mockup)" en
`README_PR000335.md`), y un par de campos del diccionario de datos del EF
no tenían un selector 1:1 en la UI real (se mapearon a mano, dejando el
mapeo comentado en el código). Úsalos para entender intención de negocio
y nombres de campo, pero el paso 2 (exploración en vivo) sigue siendo
obligatorio para confirmar selectores/rutas reales — más aún si **no** te
dieron ET (solo Excel + EF), porque ahí no hay ninguna referencia técnica
de respaldo.

## 2. Exploración en vivo de la aplicación real

**No te saltes este paso ni lo automatices a ciegas.** Cada aplicación del
portal tiene su propio árbol de menú y sus propios selectores; hay que
verlos corriendo de verdad (headed) al menos una vez:

1. Login manual/headed en la app real, anotar la ruta exacta de menús
   (`Aplicaciones > ... > ... > Nombre De Tu App`) — es lo que le vas a
   pasar a `abrir_aplicacion(page, ruta_menu, selector_pantalla)`.
2. Identificar el **componente Angular raíz** de la pantalla (ej.
   `app-listado-de-atenciones` en PR000335) — ábrelo con DevTools o
   `page.content()` tras entrar.
3. Identificar selectores reales de cada campo/botón relevante (ids,
   roles, textos exactos de botones) para los casos que vas a automatizar.
4. Guardar capturas de esta exploración en `PR0000NN\_exploracion\` — sirve
   de referencia si algo cambia después.

Usa un script descartable tipo `_exploracion/explore_app.py` (Playwright
headed, capturas en cada paso) para esto — no hace falta que sea elegante,
es exploración de un uso.

## 3. Escribir `generate_scripts.py` usando el framework

Si usaste el bootstrap (0b), ya tenés un esqueleto en
`PR0000NN\generate_scripts.py` — complétalo. Si no, este es el mínimo (ver
PR000335 completo como referencia de un caso real con 123 casos y varios
patrones repetidos vía funciones helper):

```python
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).parent
sys.path.insert(0, str(OUT_DIR.parent / "_framework"))
import web_lds_core as core

PROYECTO = "PR0000NN"  # <-- debe coincidir con el nombre de esta carpeta
MATRIZ = json.loads((OUT_DIR / "matriz_casos.json").read_text(encoding="utf-8"))

ENV_TOGGLES = core.ENV_TOGGLES_CODE.replace("__PROYECTO__", PROYECTO)

HEADER_TEMPLATE = '''"""
{docstring_con_ficha_del_caso}
"""
import os, re, shutil, struct, subprocess, time, zipfile
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape as _escape_xml
from playwright.sync_api import sync_playwright, expect, TimeoutError as PWTimeoutError

''' + ENV_TOGGLES + '''

URL = "https://.../Plataforma/PlataformaWeb"     # <-- tuyo
USUARIO = "..."                                    # <-- tuyo
PASSWORD = "..."                                    # <-- tuyo

CASO = "{cp}"
EVIDENCIA = Path(__file__).resolve().parent / CASO
if EVIDENCIA.exists():
    shutil.rmtree(EVIDENCIA, ignore_errors=True)
EVIDENCIA.mkdir(parents=True, exist_ok=True)

NOMBRE_CASO = {name_repr}
RF_CASO = {rf_repr}
CU_CASO = {cu_repr}
DESCRIPCION_CASO = {desc_repr}
RESULTADO_ESPERADO_CASO = {esperado_repr}
PASOS_CASO = {pasos_repr}  # texto de "Pasos a seguir" tal cual viene del Excel (columna I) - lo usa WORD_HELPERS_FULL

%%CAPTURAR_PASO%%

%%LOGIN%%

%%NAV%%

%%HELPERS_ESPERA%%

%%VIDEO_HELPERS%%

# --- Aca van TUS funciones especificas de esta app (selectores propios) ---
def abrir_tu_app(page):
    return core... # llama a abrir_aplicacion(page, ["Menu1", "Menu2", "Tu App"], "app-tu-pantalla")

%%WORD_HELPERS%%


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=HEADLESS, slow_mo=SLOWMO)
        opciones_contexto = {{"viewport": {{"width": 1600, "height": 900}}}}
        if GRABAR_VIDEO:
            opciones_contexto["record_video_dir"] = str(EVIDENCIA)
            opciones_contexto["record_video_size"] = {{"width": 1600, "height": 900}}
        context = browser.new_context(**opciones_contexto)
        if GRABAR_VIDEO:
            context.add_init_script(%%CURSOR_OVERLAY_JS%%)
        page = context.new_page()
        app = None
        _CASO_OK = False
        try:
            login(page)
            app, frame = abrir_tu_app(page)
            pantalla = frame.locator("app-tu-pantalla")

{body}

            # Captura final generica antes de terminar el caso (confirmado
            # util en vivo el 12/09/2026, PR000325): etiquetada con el
            # ULTIMO paso real de PASOS_CASO (no sin paso_excel) para que
            # no genere una seccion "Otras capturas" vacia de contenido.
            capturar_paso(app, "estado_final_del_caso", paso_excel=max(_parsear_pasos_excel(PASOS_CASO), default=None))
            _CASO_OK = True

        except (PWTimeoutError, AssertionError) as e:
            print(f"[FALLO] {{CASO}} FALLO: {{e}}")
            (app if app else page).screenshot(path=str(EVIDENCIA / f"{{CASO}}_error.png"), full_page=True)
            raise
        finally:
            if GRABAR_VIDEO:
                (app if app else page).wait_for_timeout(3000)  # 3s extra del ultimo estado antes de cerrar
            video_portal = page.video
            video_app = app.video if app else None
            browser.close()
            # Video/Word solo tienen valor para casos que terminan OK
            # (patron _CASO_OK, estandar desde PR000325-SP3, 17/09/2026):
            # un caso NO OK ya deja su _error.png + su entrada en el .log
            # de run_all.py para seguimiento, asi que no vale la pena
            # gastar tiempo/espacio armando video/Word de un flujo que no
            # llego a completarse - se descartan los .webm crudos.
            if _CASO_OK:
                # _renombrar_video devuelve la ruta que quedo REALMENTE
                # valida (renombrada, o el nombre-hash original si el
                # renombre fallo) - NUNCA asumir que existe con el nombre
                # bonito nada mas, o se pierde ese video en silencio (bug
                # real, ver Seccion "Errores reales" mas abajo).
                ruta_portal = _renombrar_video(video_portal, EVIDENCIA / f"{{CASO}}-1.webm") if video_portal is not None else None
                ruta_app = _renombrar_video(video_app, EVIDENCIA / f"{{CASO}}-2.webm") if video_app is not None else None
                if ruta_portal and ruta_app:
                    _unir_videos(ruta_portal, ruta_app, EVIDENCIA / f"{{CASO}}_video.webm")
                elif ruta_portal:
                    ruta_portal.replace(EVIDENCIA / f"{{CASO}}_video.webm")
                elif ruta_app:
                    ruta_app.replace(EVIDENCIA / f"{{CASO}}_video.webm")
                if GRABAR_WORD:
                    generar_word_evidencia()
            else:
                for video_obj in (video_portal, video_app):
                    if video_obj is None:
                        continue
                    for _intento_descarte in range(4):
                        try:
                            Path(video_obj.path()).unlink(missing_ok=True)
                            break
                        except (PermissionError, OSError):
                            time.sleep(0.5)


if __name__ == "__main__":
    main()
'''


def render(caso: dict) -> str:
    body = ...  # indentar caso["body"], igual que PR000335
    return HEADER_TEMPLATE.format(
        cp=caso["cp"], name_repr=repr(caso["name"]), rf_repr=repr(caso["rf"]),
        cu_repr=repr(caso["cu"]), desc_repr=repr(caso["desc"]),
        esperado_repr=repr(caso["esperado"]), body=body,
    ).replace("%%CAPTURAR_PASO%%", core.CAPTURAR_PASO_CODE) \
     .replace("%%LOGIN%%", core.LOGIN_BLOCK) \
     .replace("%%NAV%%", core.CLICK_VISIBLE_BLOCK + "\n\n\n" + core.ABRIR_APLICACION_BLOCK) \
     .replace("%%HELPERS_ESPERA%%", core.ESPERAR_FIN_CARGA_BLOCK + "\n\n\n" + core.ESPERAR_ANIMACION_BLOCK + "\n\n\n" + core.SELECCIONAR_PRIMERA_OPCION_BLOCK + "\n\n\n" + core.SELECCIONAR_OPCION_POR_TEXTO_BLOCK) \
     .replace("%%VIDEO_HELPERS%%", core.RENOMBRAR_VIDEO_BLOCK) \
     .replace("%%CURSOR_OVERLAY_JS%%", repr(core.CURSOR_JS_FULL.strip("\n"))) \
     .replace("%%WORD_HELPERS%%", core.WORD_HELPERS_FULL.strip("\n"))


CASES = []

def add(cp, rf, cu, name, desc, precond, datos, esperado, body):
    CASES.append(dict(cp=cp, rf=rf, cu=cu, name=name, desc=desc, precond=precond, datos=datos, esperado=esperado, body=body))

# --- Casos, uno por cada fila de MATRIZ, con el body Playwright real ---
# add("CP001", MATRIZ["CP001"]["rf"], ..., body='''
#     pantalla.locator("#miCampo").fill("valor")
#     pantalla.get_by_role("button", name="Buscar").click()
#     ...
# ''')

if __name__ == "__main__":
    for c in CASES:
        (OUT_DIR / f"{c['cp']}.py").write_text(render(c), encoding="utf-8")
    print(f"Generados {len(CASES)} scripts en {OUT_DIR}")
```

El `body` de cada caso (los `assert`/clics reales) **no es automatizable
a ciegas**: hay que escribirlo mirando el caso de la matriz + la
exploración en vivo del paso 2. Sí puedes reconocer patrones repetidos
(como `RESTRICCION_ESPERADA`/`SIN_RESTRICCION`/`cu07_maxlength` en
PR000335) y armarlos como funciones helper propias del proyecto para no
repetir código entre casos parecidos.

**Gotcha confirmado en vivo (PR000325): usa siempre `exact=True`.**
`get_by_label(texto)` y `get_by_role(rol, name=texto)` de Playwright hacen
match por **substring**, case-insensitive, por defecto — igual que
`has_text` (ver el bug de `_click_visible` en el changelog de
`web_lds_core.py`). Si la pantalla real tiene labels parecidos entre sí
(ej. "Activa" / "Reactiva" / "Activa H.P."), `get_by_label("Activa")` sin
más falla con `strict mode violation: resolved to 3 elements`. No asumas
que un texto es único solo porque lo parece en la matriz Excel o el EF:
usa `get_by_label(texto, exact=True)` / `get_by_role(rol, name=texto,
exact=True)` en cualquier selector nuevo que escribas.

**Si tu app muestra un segundo diálogo con el resultado real** (ej. "Ingresar"
abre un "¿Está seguro?" y, al aceptar, un SEGUNDO diálogo con "Registro
Insertado"), dale un timeout generoso a la espera de ese segundo diálogo
(6-8s, no 3s) — confirmado en vivo que con timeouts cortos el segundo
diálogo puede tardar más de lo esperado bajo carga, y el caso queda con la
captura del diálogo de confirmación en vez del resultado real, sin ningún
error visible (ver `confirmar()` de PR000325 como referencia).

**Si tu app tiene un campo "código único" con `maxlength` chico, un
generador simple basado en `time.time()` se satura rápido en un ambiente
de pruebas compartido — issue abierto, no resuelto al 11/09/2026.**
Confirmado en vivo en PR000325 (RF-01, campo `codigo` con `maxlength=4` →
solo 9000 valores posibles): tras un día de corridas repetidas, el
espacio quedó tan ocupado que 40 códigos al azar seguidos (CP001 + CP003,
20 cada uno) ya existían todos, y subir a 50 intentos con muestreo amplio
(`random.randint`) sigue sin ser 100% confiable — además, tantos
reintentos seguidos contra un ambiente que ya responde lento puede dejar
el formulario a mitad de una petición anterior y el siguiente clic en
"Leer" falla por timeout (el botón queda deshabilitado). No hay forma de
listar los códigos ya usados desde esta pantalla (el botón "Leer" exige
un código puntual, no lista todo). Si tu proyecto tiene un campo así:
detectá la colisión en el momento correcto del flujo (no inmediatamente
tras el primer "Leer" — confirmado que el estado del botón
Ingresar/Modificar recién es confiable DESPUÉS de completar el resto del
formulario), esperá a que el botón de acción esté HABILITADO antes de
cada reintento (no solo que la carga haya terminado), y aceptá que puede
hacer falta limpiar datos de prueba viejos en la base si el campo es
chico y el ambiente se usa mucho.

**Pasále `paso_excel` a `login()`/`abrir_aplicacion()` o esas 2 capturas
quedan en "Otras capturas".** `capturar_paso()` agrupa las imágenes del
Word de evidencia por el número de paso del Excel (`paso_excel=N`); sin
ese número, la imagen cae en un bloque genérico "Otras capturas" al final,
sin el texto real del paso. `login()` y `abrir_aplicacion()` (del
framework) no lo pasan por defecto — confirmado en vivo que **59 de los 62
casos de PR000325** tenían esa sección vacía de contenido útil porque su
Excel dedica un único Paso 1 a "entrar a la plataforma + abrir la
aplicación" y ninguna de las 2 capturas llevaba ese número. Antes de dar
por buena la agrupación del Word, revisá la convención de numeración de
`PASOS_CASO` de tu propio Excel (no asumas que es uniforme entre todos los
casos — PR000325 tuvo 1 caso, de 62, con una numeración distinta al
resto) y pasá `login(page, paso_excel=N)` / `abrir_aplicacion(..., paso_excel=N)`
(o agregá el parámetro a tus wrappers `abrir_tu_app()`) según corresponda.

**Pausa de 2s antes Y 2s después de cada acción relevante del cuerpo del
caso (click, select_option, fill, check) — pedido en vivo el
12/09/2026, confirmado en PR000325 CP009.** No es lo mismo que
`PAUSA_ANTES_CLIC` (que solo se dispara con capturas `"antes_de_*"` y
solo del lado ANTES): esta es una convención más simple y pareja para
que el video de evidencia se pueda revisar con detalle paso a paso.
Patrón:
```python
app.wait_for_timeout(2000)
frame.locator('select[name="algo"]').select_option(value="X")
app.wait_for_timeout(2000)
capturar_paso(app, "algo_seleccionado", paso_excel=N)
```
No hace falta en TODAS las líneas (ej. no antes de `esperar_fin_de_carga`,
que ya espera lo suyo) — sí antes/después de cada interacción real con la
UI (click, select, fill, check) que el video deba mostrar con claridad.

**Captura final antes de terminar el caso, adjunta al Word — ya viene
en el `HEADER_TEMPLATE` de este checklist y de `generate_scripts.py`
(agregado 12/09/2026), no hace falta escribirla a mano en cada cuerpo de
caso.** Justo después del cuerpo de cada caso (antes del `except`) se
agrega automáticamente `capturar_paso(app, "estado_final_del_caso",
paso_excel=max(_parsear_pasos_excel(PASOS_CASO), default=None))` -
etiquetada con el ÚLTIMO paso real del Excel (no sin `paso_excel`, que
generaba una sección "Otras capturas" con una sola imagen suelta - visto
en vivo en PR000325 CP015 y corregido).

**Para regenerar un solo `CPxxx.py` sin pisar los demás** (útil cuando
corregís el cuerpo de un caso puntual en `generate_scripts.py` y no
querés correr el generador completo, que reescribe los 62): copiá
`_regenerar_uno.py` (ya vive en `_framework/_regenerar_uno.py`, referencia
también en `automation/PR000325/_regenerar_uno.py`) a la carpeta del
proyecto y corré `python _regenerar_uno.py CPxxx`.

**Las descargas de archivo (Excel, PDF, etc.) que dispara un botón DENTRO
DE UN POPUP se capturan con `app.expect_download()`, NO
`page.expect_download()`.** Confirmado en vivo el 12/09/2026 (PR000325
CP055, "Exportar a Excel"): `page` es la pestaña/ventana que abrió el
popup, pero el botón vive dentro del popup (`app`) - el evento de
descarga se dispara ahí. Con `page.expect_download()` el timeout salta
SIEMPRE (15-30s), sin importar si hay datos para exportar o no - error
fácil de confundir con "no hay nada que exportar". Patrón correcto:
```python
with app.expect_download(timeout=15000) as descarga_info:
    frame.get_by_role("button", name="a Excel").click()
descarga = descarga_info.value
descarga.save_as(str(EVIDENCIA / f"{CASO}_exportado.xlsx"))
```

**Algunas apps abren su popup con un tamaño de ventana FIJO más chico que
el resto** (confirmado en vivo: RF-06 de PR000325 abre a 1280x720 en vez
del 1600x900 habitual), lo que puede tapar botones de acción sin scroll
horizontal disponible - un tester a mano puede quedarse sin ver "Leer" u
otro botón por más que haga zoom o baje. Si vas a explorar una app así en
vivo (headed) y algo no se ve, probá `app.set_viewport_size({"width":
1366, "height": 768})` (u otro tamaño) apenas conseguís la referencia al
popup, antes de interactuar.

**El mismo selector genérico de diálogo (`.mdl-confirmar`) puede
matchear MÁS DE UNO a la vez si tu acción abre un modal ENCIMA de otro
modal que sigue abierto de fondo** (confirmado en vivo: RF-06, el modal
"Copia de libros" es `.mdl-confirmar` Y el mensaje de validación que
aparece al aceptar TAMBIÉN lo es) - `dialogo_visible()`/`confirmar()`
genéricos fallan con `strict mode violation: resolved to 2 elements`. Si
tu caso abre un modal propio (no genérico) y después dispara una
validación/confirmación encima, tomá el diálogo real así en vez de los
helpers genéricos:
```python
dialogo_validacion = frame.locator(".mdl-confirmar").filter(has_not_text="texto del modal de fondo")
dialogo_validacion.wait_for(state="visible", timeout=8000)
texto_dialogo = dialogo_validacion.inner_text()
...
dialogo_validacion.get_by_role("button", name="Aceptar").click()
```

**Verificá altas/bajas/cambios por el MENSAJE de confirmación real, no
contando filas de una grilla antes/después.** Confirmado en vivo dos
veces (PR000325 CP028 y CP038, "Eliminar"): grillas grandes (1700+ filas)
o con varias filas visualmente idénticas en las columnas mostradas hacen
que `cantidad_antes == cantidad_despues` de falsos negativos aunque el
borrado SÍ haya funcionado (mensaje real: "Se eliminó el registro
correctamente"). Guardá y verificá el texto de `confirmar(...)` en vez de
comparar conteos:
```python
texto_confirmacion = confirmar(frame, aceptar=True)
assert "elimin" in texto_confirmacion.lower() and "correctamente" in texto_confirmacion.lower()
```

**Los combos "existente vs. nuevo" con heurísticas tipo "última opción"
o "índice N" se rompen apenas el ambiente de datos cambia** - confirmado
en vivo repetidas veces en PR000325 (RF-02 y RF-03: "última opción de
demanda+fase" o "primera tarifa de la lista" resultaron estar YA
OCUPADAS, o dispararon una regla de negocio cruzada no relacionada con lo
que el caso quería probar - ej. una caja "Polimérica" solo válida para
ciertas tarifas). Preferí SIEMPRE un valor concreto confirmado en vivo
(a mano o con un chequeo puntual aislado) por sobre una heurística
posicional, y dejá comentado en el caso CÓMO se confirmó ese valor y
cuándo, para que quien lo retome sepa si conviene volver a confirmarlo.

**Las grillas de reasignación DENTRO de un modal (ej. "a qué contratista
nuevo mapear cada uno viejo") pueden tardar en recalcularse después de
cambiar un campo relacionado (ej. el mes/año destino) - completar el
mapeo demasiado rápido deja timing de carrera.** Confirmado en vivo
(PR000325 CP059/CP060): con 500ms de espera tras cambiar destino, el
mapeo se aplicaba sobre una versión vieja de la grilla y el sistema
rechazaba con "Debe asignar todos los contratistas" pese a que la
captura de pantalla mostraba todo completo; con 2000ms alcanzó. Si un
campo dispara el recálculo de OTRA sección del formulario, dale al menos
1.5-2s antes de tocar esa sección.

**Un `<select>` puede restringir sus valores válidos por una regla de
negocio no evidente en el DOM** (ej. "año destino" solo acepta el año
actual en adelante, no años pasados) - confirmado en vivo (PR000325
CP060): `select_option(value="2023")` colgó 30s con "did not find some
options" en vez de fallar rápido, porque la opción simplemente no existe
en ESE combo puntual (aunque exista un combo hermano - "año origen" - que
sí la acepta). Si un `select_option()` cuelga sin motivo aparente,
sospechá primero que el valor no es una opción válida ahí antes de
asumir que es el bug genérico de "Leer nunca habilita".

**Gotchas confirmados en vivo (PR000335-2, 123→98 casos entre Sprint 1 y
Sprint 2 de "Atención al Cliente"):**

**Un campo de búsqueda "lleno" no es lo mismo que "buscado" -
`fill()` solo no dispara nada.** Confirmado en vivo repetidas veces: un
cuerpo de caso que hace `campo.fill(codigo)` y sigue de largo (sin
`.press("Enter")` ni click en el botón de buscar real) deja el dato
escrito pero la app nunca ejecuta la búsqueda - todo lo que dependía de
esos datos (iconos que se habilitan, secciones que se completan) queda
huérfano, y el síntoma en el log es engañoso ("elemento no visible,
reintentando" hasta timeout), no un error claro de "no se buscó nada".
Si tu app tiene un campo así, envolvelo en una función tipo
`buscar_por_codigo(app, frame, codigo)` que haga fill + submit real +
**espere la carga** (`app.wait_for_load_state("networkidle", timeout=...)`
+ un `wait_for_timeout` corto de margen) antes de devolver el control,
y usala SIEMPRE en vez de `campo.fill()` suelto en el cuerpo de los casos.

**Los íconos/botones que quedan ocultos hasta expandir una sección del
sidebar necesitan una espera corta DESPUÉS de expandir, no solo un
chequeo de visibilidad inmediato.** Angular tarda un instante en
re-renderizar tras el click de expandir; comprobar `is_visible()` en el
mismo tick casi siempre da `False` aunque la sección ya se esté
expandiendo, y el siguiente `.click()` puede quedar reintentando 30s
sin nunca estabilizarse. Patrón: `expandir_seccion(frame); app.wait_for_timeout(1000)`
antes de tocar lo que estaba escondido ahí.

**Una grilla "vacía" en un modal/dialog puede seguir teniendo 1 fila
en el DOM (`tbody tr` cuenta 1), solo que con todas las celdas en
blanco.** Un chequeo `filas.count() == 0` no detecta esta fila
fantasma y deja pasar el caso como si hubiera datos reales (falso OK).
Comprobá también el texto: `filas.count() == 0 or not filas.first.inner_text().strip()`.
Relacionado: estas grillas pueden tardar varios segundos en cargar
DESPUÉS de que el modal ya se ve "abierto" - leer su contenido
demasiado rápido las muestra en estado "Cargando..." (visualmente
distinto de "vacía de verdad", confirmá con una captura antes de
concluir que no hay datos).

**Los botones de acción POR FILA de una grilla (ej. Consultar/
Modificar/Eliminar en un listado) hay que escoparlos a la fila
seleccionada, no buscarlos en toda la pantalla.** Con una grilla vacía
o de 1 sola fila de prueba esto no se nota (nunca falla), pero apenas
la grilla trae datos reales (docenas de filas, cada una con sus propios
botones) `pantalla.get_by_role("button", name="Consultar")` sin más
revienta con `strict mode violation: resolved to N elements`. Guardá
la fila que seleccionaste y buscá el botón DENTRO de ella. Sumale
`exact=True` si además hay botones "hermanos" con nombres que se
solapan como substring (ej. "Modificar" vs. "Modificar Contacto" en la
misma fila).

**Un popup abierto por un botón DENTRO de una grilla/listado (no desde
el menú de Aplicaciones) puede no tener el wrapper `#aplicacion` que sí
tienen los que abre el menú.** Confirmado en vivo: `Agregar`/
`Consultar`/`Modificar` sobre una fila abren una ventana nueva que
navega DIRECTO a la URL de la app, sin el iframe `#aplicacion` de por
medio - así que el "frame" a usar ahí es la página misma, no
`pagina.locator("#aplicacion").content_frame`. Verificá con
`if pg.locator("#aplicacion").count(): frame = pg.locator("#aplicacion").content_frame else: frame = pg` en vez de asumir un solo patrón para todos los popups del proyecto.

**Las pantallas de búsqueda/listado pueden exigir como mínimo un
filtro para buscar, Y tener un filtro de fecha tildado por defecto con
el rango de HOY (que casi siempre da 0 resultados reales).** Si tu app
tiene un listado con filtros, no asumas que "Buscar" sin tocar nada
trae datos - confirmá en vivo cuál es el rango/filtro mínimo real que
trae resultados (a veces el propio formulario avisa el mínimo con un
mensaje tipo "Debe utilizar como mínimo uno de los filtros..." si lo
destildás sin poner otro) y ajustá el filtro de fecha a un rango amplio
(ej. últimos 30 días) en vez de confiar en el default.

**Metodología para distinguir "la automatización está mal" de "la app
tiene un defecto real": una sesión headed con logging de red en vivo,
manejada a mano por el usuario del proyecto.** Cuando un caso falla de
forma rara (ej. un guardado que no muestra ningún error pero tampoco
guarda), no sirve solo mirar el DOM - hace falta ver qué respondió el
backend. Copiá `_framework/sesion_manual_con_red.py` a
`PR0000NN/_exploracion/`, ajustá URL/usuario/clave, corré el script (deja
un Edge headed abierto ~20 min) y pedile al usuario del proyecto que
reproduzca el flujo a mano mientras el script escucha TODAS las
respuestas HTTP (de la pestaña principal y de cualquier popup nuevo) y
vuelca a un `.txt` con flush inmediato cada una con status >= 400 -
podés leer ese archivo sin esperar a que la sesión termine. Una vez
confirmado así (no solo "el assert de Playwright falló"), marcá el caso
en `casos_fallidos_confirmados.json` (ver Sección 6) en vez de dejarlo
como un FALLO más indistinguible del resto.

**No hay que asumir que un modal/dialog contiene UNA sola grilla - puede
tener varias secciones con título propio, cada una con su propia
`<table>`, y solo una corresponde al caso que estás automatizando.**
Confirmado en vivo (PR000335-2, ícono "Mediciones programadas por
norma"): un solo dialog traía 3 grillas distintas (Precisión de la
Medida, Calidad de Producto, Contraste de Medidor 227), cada una de una
funcionalidad distinta que solo comparte el mismo botón disparador.
`dialogo.get_by_role("table")` sin más devuelve las 3 mezcladas -
identificá la tabla correcta por su título/sección (ej.
`dialogo.get_by_role("table").nth(indice)`, documentando en un
comentario CUÁL índice es cuál y cómo se confirmó) antes de leer
columnas/filas.

**Gotchas confirmados en vivo (PR000325-SP3, 17/09/2026):**

**Corrida automática por defecto: video/Word solo en casos OK, sin
preguntar, `--slowmo 2000`.** Desde este proyecto, correr los CP de un
proyecto (nuevo o existente) es el default: `run_all.py --video` (el
`--slowmo` ya viene en 2000ms). No hace falta preguntarle al usuario por
los flags salvo la PRIMERA corrida completa de cada proyecto nuevo — de
ahí en más, correr directo. El propio `HEADER_TEMPLATE` (bandera
`_CASO_OK`, ver el `main()` de arriba) decide solo si vale la pena armar
video/Word: un caso NO OK ya deja su `_error.png` + su entrada en
`reportes\logs\CPxxx.log`, no necesita más.

**`import CPxxx as mod` para reusar sus funciones en un script de
diagnóstico borra la evidencia YA VALIDADA de ese CP.** Cada `CPxxx.py`
generado limpia su propia carpeta de evidencia (`shutil.rmtree`) apenas
se lo importa — no solo al correrlo como script (`EVIDENCIA.exists():
shutil.rmtree(...)` corre a nivel de módulo, antes de `if __name__ ==
"__main__"`). Si necesitás reusar sus helpers (`abrir_tu_app`,
`entrar_nivel2`, etc.) para investigar algo en vivo, o le copiás solo las
funciones puntuales a tu script de diagnóstico en vez de importar el
módulo completo, o volvés a correr ese CP con `--video` al terminar para
regenerar su evidencia. Pasó dos veces en PR000325-SP3 (CP005 y CP087
perdieron su video/Word por esto).

**Un ffmpeg "completo" (con soporte `concat`) es necesario para que el
video de portal+app quede en UN solo `.webm`** — el que trae Playwright
(`ms-playwright\ffmpeg-*\ffmpeg-win64.exe`) NUNCA lo tiene (viene
compilado con `--disable-everything`), así que sin esto cada caso deja 2
videos separados. Se instaló un build portable en
`C:\AUTOMATIZACION_LDS\ffmpeg\ffmpeg.exe` y `_localizar_ffmpeg()` (en
`web_lds_core.py`) ya lo busca ahí antes de caer al de Playwright — no
hace falta nada más por proyecto, es 2 niveles arriba de cualquier
`CPxxx.py` (`AUTOMATIZACION_LDS\PRxxxxxx\CPxxx.py`).

## 4. Copiar `run_all.py` tal cual

```
copy C:\AUTOMATIZACION_LDS\_framework\run_all.py C:\AUTOMATIZACION_LDS\PR0000NN\run_all.py
```

No requiere edición — autodetecta el prefijo por el nombre de carpeta. (Si
usaste el bootstrap del Paso 0b, esto ya está hecho.)

## 5. Generar, compilar, smoke test

```
.venv\Scripts\python.exe C:\AUTOMATIZACION_LDS\PR0000NN\generate_scripts.py

.venv\Scripts\python.exe -c "import py_compile, glob; [py_compile.compile(f, doraise=True) for f in glob.glob(r'C:\AUTOMATIZACION_LDS\PR0000NN\CP*.py')]; print('OK')"

.venv\Scripts\python.exe C:\AUTOMATIZACION_LDS\PR0000NN\run_all.py --solo CP001,CP002 --video
```

Antes de correr los 100+ casos completos, confirma que 2-3 casos
representativos (uno de cada patrón: búsqueda simple, un caso con modal,
uno con validación de campo) pasan y que el video/evidencia se ve bien.

## 6. Corrida completa

```
.venv\Scripts\python.exe C:\AUTOMATIZACION_LDS\PR0000NN\run_all.py --video --slowmo 700
```

Ajustar `--slowmo`/`--workers`/`--timeout` según el tamaño de la matriz y
cuánto tiempo hay disponible (ver notas de tiempos reales en
`README_PR000335.md` como referencia: ~45-115s por caso con video+slowmo).

Al terminar, revisar `reportes\reporte_<fecha>.csv` (columna `Resultado`:
OK/FALLO/TIMEOUT/ERROR) y `reportes\logs\CPxxx.log` para el detalle de
cualquier caso que no haya dado OK. **Metodología recomendada** (confirmada
en 2 proyectos): en una corrida masiva de 60-120+ casos seguidos, una
buena parte de los FALLO/TIMEOUT suele ser sobrecarga transitoria del
propio servidor de LDS — relanzar SOLO los que fallaron (`--solo
CPxxx,CPyyy`) para separar timeouts transitorios de bugs reales antes de
reportar resultados como definitivos.

**Reporte Excel consolidado (opcional, pedido en vivo el 12/09/2026):**
copiá `_framework\generar_reporte_excel.py` (genérico, no hace falta
editarlo) a la carpeta del proyecto y corré
```
.venv\Scripts\python.exe C:\AUTOMATIZACION_LDS\PR0000NN\generar_reporte_excel.py
```
Lee `matriz_casos.json` + TODOS los `reportes\reporte_*.csv` existentes
(se queda con el resultado más nuevo de cada CP, así una corrida parcial
después de la completa pisa el estado viejo de esos CP puntuales) y arma
un `.xlsx` con una hoja "Resumen" (por RF) y una hoja "Detalle por caso"
(con colores). No ejecuta ningún caso — solo lee lo que ya corrió.

**3 estados en vez de 2 (agregado PR000335-2, 15/09/2026):** un caso que
no dio OK puede ser un bug de automatización todavía sin confirmar, o un
defecto real de la app ya verificado en vivo — son cosas muy distintas
para el negocio. Si creás (a mano) un `casos_fallidos_confirmados.json`
junto a `generate_scripts.py` con el formato
`{"CPxxx": {"motivo": "...", "fecha_verificacion": "YYYY-MM-DD",
"evidencia": "ruta o descripción"}, ...}` — solo para los casos que
confirmaste en vivo que son defectos reales (ver el patrón de
`sesion_manual_con_red.py` en la nota anterior) —, el reporte separa
"NO OK" (amarillo, sin confirmar) de "Fallido" (rojo, defecto real,
con el motivo en su propia columna en "Detalle por caso"). Sin ese
archivo el reporte sigue funcionando igual que antes, todo cae en
"NO OK".

## 7. Si mejoras algo genérico en el camino

Si encuentras una mejora que no es específica de esta app (ej. el cursor
del video, un bug en `esperar_fin_de_carga`, una columna nueva en el
Excel), **edítala en `_framework\web_lds_core.py` / `extraer_matriz.py` /
`run_all.py` / `generar_reporte_excel.py`**, no solo en tu copia local —
así el próximo proyecto la hereda gratis.

**Cada vez que corrijas algo así, actualizá los 3 lugares:**

1. El código en `_framework\` (fuente de verdad).
2. La sección "Changelog" al final de `web_lds_core.py` (qué proyecto lo
   originó, por qué, y si algún proyecto anterior necesita regenerar sus
   `CPxxx.py` por esto).
3. **Este checklist** y `MANUAL_NUEVO_PROYECTO.docx` (sección "Errores
   reales ya resueltos") — si la lección es del tipo "acordate de usar
   `exact=True`" o similar, que no vive en el código sino en cómo se
   escribe `generate_scripts.py`, el único lugar donde queda registrada es
   acá. (Para regenerar el `.docx` después de editar este `.md`, ver
   `build_manual.py` en el mismo directorio.)

Proyectos ya generados con una versión anterior del framework **no se
actualizan solos** (cada `CPxxx.py` es autónomo, sin import al
framework): si la mejora vale la pena propagarla a un proyecto viejo, hay
que volver a correr su `generate_scripts.py` después de que ese proyecto
también actualice sus imports del framework.
