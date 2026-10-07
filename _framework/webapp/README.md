# Webapp de Automatización LDS

Página web local para envolver el flujo de automatización de pruebas de
Web LDS: subir los 3 documentos de un proyecto (matriz Excel + EF/ET en
Word), disparar el bootstrap y la exploración/generación de casos, y
ejecutar las pruebas filtradas por RF con reporte consolidado en la
misma página.

## Cómo arrancar

Sin dependencias que instalar (backend 100% librería estándar de
Python — ver "Por qué stdlib" abajo):

```
.venv\Scripts\python.exe _framework\webapp\server.py
```

Por defecto escucha en `http://127.0.0.1:8765` (solo local, no se
expone a la red). Cambiar el puerto con la variable de entorno
`WEBAPP_PORT` si hace falta.

Abrir esa URL en el navegador y usar las 3 pestañas: **Nuevo
proyecto** (subir documentos), **Ejecutar pruebas** (elegir RF) y
**Reporte** (ver el resultado consolidado).

## Por qué stdlib (sin Flask/FastAPI)

El venv de este proyecto (`C:\Proyectos\PlataformaWeb\.venv`) no tiene
ningún framework web instalado, y en esta VM instalar paquetes Python
nuevos con pip no es confiable (las descargas de `.whl` se cortan). El
backend (`server.py`) usa `http.server.ThreadingHTTPServer` y el
frontend (`static/`) es JS vanilla sin build step — cero dependencias
nuevas que instalar. Es el mismo criterio que ya sigue
`extraer_docx.py` en `_framework\`, que evita `python-docx` a
propósito por la misma razón.

## Sobre la exploración/generación con IA (`claude -p`)

Si el CLI `claude` (Claude Code) está instalado en esta máquina
(`shutil.which("claude")`), el botón "Analizar" también dispara la
exploración/generación de `generate_scripts.py` en modo headless, con
el prompt armado por `claude_prompt.py` (incluye la política de
autonomía acotada: nunca frena el batch completo por un solo caso, ver
docstring de ese archivo).

Si el CLI **no** está instalado, la página sigue funcionando igual: el
bootstrap corre normal, y en vez de disparar la IA sola, muestra el
mismo prompt con un botón "Copiar" para pegarlo a mano en una sesión
interactiva de Claude Code — el punto de entrada manual (como se venía
haciendo hasta ahora) sigue siendo válido en todo momento, no es un
callejón sin salida.

**No verificado en esta VM todavía** (el CLI no estaba instalado al
escribir esto): los nombres exactos de los flags de `claude -p`
(`--output-format stream-json`, `--dangerously-skip-permissions`, etc.)
y el schema real de las líneas de `stream-json`. El parseo en
`procesos.py` está escrito para degradar con gracia (una línea que no
es JSON válido no tumba el hilo) — la fuente de verdad real del
progreso es contar `CPxxx.py` en el disco, no el parseo del stream.

## Archivos

- `server.py` — rutas HTTP (`GET /api/proyectos`, `/api/estado/<p>`,
  `/api/rf/<p>`, `/api/reporte/<p>`; `POST /api/proyectos/analizar`,
  `/api/ejecutar/<p>`).
- `procesos.py` — orquesta los subprocesos (`nuevo_proyecto.py`,
  `claude -p`, `run_all.py`, `generar_reporte_excel.py`) en hilos de
  fondo, uno por proyecto.
- `estado.py` — lee/escribe `PROYECTO\estado_actual.json` de forma
  atómica (el polling del frontend consulta esto).
- `claude_prompt.py` — arma el prompt de exploración/generación.
- `multipart.py` — parser manual de `multipart/form-data` (necesario
  porque `cgi.FieldStorage` fue removido en Python 3.13).
- `static/` — frontend (HTML/CSS/JS vanilla, sin build step).
- `_uploads/` — staging temporal de archivos subidos (no se versiona,
  ver `.gitignore`).

## Notas

- Cada proyecto solo puede tener un proceso de fondo a la vez
  (bootstrap/exploración O ejecución de pruebas) — un segundo intento
  mientras el primero sigue corriendo responde `409`.
- `run_all.py`/`generar_reporte_excel.py` se re-copian desde
  `_framework\` a la carpeta del proyecto antes de cada corrida (son
  "copia textual" por convención, ver `NUEVO_PROYECTO_CHECKLIST.md`
  Sección 7) — así un proyecto viejo hereda el flag `--rf` sin tener
  que tocarlo a mano.
