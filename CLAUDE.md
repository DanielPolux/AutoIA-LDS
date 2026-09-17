# Proyecto: Automatización de Pruebas - Web LDS (Luz del Sur)

## Contexto
Este proyecto genera pruebas automatizadas (Playwright + Python) a partir de pruebas
que hasta ahora se ejecutaban manualmente en Web LDS, dentro de una máquina virtual
accedida por Citrix Workspace. La fuente de verdad de qué probar es un Excel con la
matriz de pruebas manuales ya ejecutadas (llevarlo a esta misma carpeta).

## Entorno (según "MANUAL DE INSTALACION Y CONFIGURACION PARA PRUEBAS DE CALIDAD USANDO IA.docx")
- VS Code
- Python 3.13 + entorno virtual (.venv)
- Extensiones VS Code: Python, Python Debugger, Playwright Test for VSCode
  (+ opencode, o Claude Code según qué conectividad de red tenga esta VM)
- Node.js (necesario si se usa opencode)
- Modelo de IA de opencode corre en servidor interno 10.105.5.63:11434 (solo accesible
  dentro de esta red). Si se usa Claude Code en su lugar, se necesita salida a internet
  hacia Anthropic (api.anthropic.com / claude.ai) — verificar con
  `Test-NetConnection api.anthropic.com -Port 443` antes de decidir.

## Arquitectura real (validada en PR000335, 123/123 casos corridos)

El plan original de abajo ("Estructura de carpeta objetivo" con Page
Object Model clásico `pages/`+`test/`) **no es el que terminó usándose**.
El patrón real, probado con una corrida completa de 123 casos contra
producción, es **un archivo por caso, 100% autónomo**, sin capa de Page
Object separada. Motivo: cada `CPxxx.py` se puede copiar solo (sin el
resto del proyecto) a otra máquina/VM Citrix y sigue generando su
evidencia completa — prioridad más importante que la separación clásica
de capas para este contexto (transferencia de archivos hacia la VM
incierta, ver historial de "pendientes" abajo).

```
C:\Proyectos\PlataformaWeb\
  .venv\
  requirements.txt
  automation\
    PR0000NN\                  <- una carpeta por proyecto/matriz Excel
      generate_scripts.py      <- FUENTE DE VERDAD: genera los CPxxx.py
      matriz_casos.json        <- matriz Excel extraida a JSON
      run_all.py                <- orquesta la corrida de todos los CP + reporte
      CPxxx.py                  <- un archivo por caso, generado, 100% autonomo
      CPxxx\                    <- evidencia de ESE caso (capturas, video, .docx)
      reportes\                 <- CSV consolidado + logs por caso

C:\AUTOMATIZACION_LDS\
  _framework\                  <- COMPARTIDO por todos los proyectos (ver abajo)
```

Cada `CPxxx.py` generado: hace login, navega, ejecuta el caso, captura
evidencia paso a paso, arma su propio Word de evidencia y (opcional)
graba video — todo sin importar nada más del proyecto ni de este
framework en tiempo de ejecución.

### Framework compartido entre proyectos

`C:\AUTOMATIZACION_LDS\_framework\` tiene todo lo que es **igual para
cualquier proyecto de Web LDS** (login del portal, navegación por menús,
cursor visual + pausas para que el video se entienda, Word de evidencia,
extractor de Excel, orquestador `run_all.py`), extraído y validado desde
PR000335. Para automatizar un proyecto nuevo, **seguir
`_framework\NUEVO_PROYECTO_CHECKLIST.md`** en vez de arrancar de cero —
ahí está el paso a paso y qué SÍ hay que rehacer por proyecto (selectores
propios de cada app, cuerpo de cada caso).

## Pendiente / a confirmar (histórico — algunos ya resueltos en PR000335)
- ~~URL exacta de Web LDS a probar~~ → resuelta: `https://pldsweb.luzdelsur.com.pe/Plataforma/PlataformaWeb`.
- Qué casos de la matriz Excel se automatizan primero (prioridad) — se define por proyecto.
- ~~Si la VM usará opencode (modelo local) o Claude Code (requiere internet)~~ → esta sesión corre con Claude Code y acceso directo al filesystem de `C:\Proyectos\PlataformaWeb`, sin necesidad de transferencia manual vía Citrix.
- Método de transferencia de archivos hacia la VM vía Citrix — en la práctica no hizo falta para PR000335 (acceso directo al filesystem); revisar si aplica igual en otras VMs/sesiones.
