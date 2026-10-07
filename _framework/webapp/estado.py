"""
Lectura/escritura de `estado_actual.json` (uno por proyecto, dentro de
`C:\\AUTOMATIZACION_LDS\\PROYECTO\\estado_actual.json`) - el archivo que
el frontend consulta por polling (`GET /api/estado/<proyecto>`) mientras
`procesos.py` corre bootstrap/exploracion/pruebas en un hilo de fondo.

Escritura ATOMICA: se escribe a un archivo `.tmp` y se reemplaza con
`os.replace()` (atomico en NTFS dentro del mismo volumen), para que un
poll en medio de una escritura nunca lea un JSON a medio escribir.

Un solo hilo escribe el estado de un proyecto dado a la vez - eso lo
garantiza el registro de hilos activos en `procesos.py`, no hace falta
un lock adicional aca.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

MAX_LOG = 500

FASES_TERMINALES = {
    "bootstrap_error",
    "exploracion_manual_pendiente",
    "exploracion_terminada",
    "exploracion_error",
    "listo",
    "reporte_error",
}


def _archivo_estado(proyecto_dir: Path) -> Path:
    return proyecto_dir / "estado_actual.json"


def leer(proyecto_dir: Path) -> dict:
    archivo = _archivo_estado(proyecto_dir)
    if not archivo.exists():
        return {"fase": "sin_iniciar"}
    try:
        return json.loads(archivo.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # No debe pasar gracias a la escritura atomica, pero si pasa,
        # el polling no debe romperse - se reporta como desconocido.
        return {"fase": "desconocido", "mensaje": "No se pudo leer estado_actual.json"}


def _escribir(proyecto_dir: Path, datos: dict) -> None:
    proyecto_dir.mkdir(parents=True, exist_ok=True)
    archivo = _archivo_estado(proyecto_dir)
    tmp = archivo.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, archivo)


def actualizar(proyecto_dir: Path, **campos) -> dict:
    """Merge parcial sobre el estado existente - solo pisa las claves
    pasadas, preserva el resto (ej. el `log` acumulado)."""
    actual = leer(proyecto_dir)
    actual.update(campos)
    actual["actualizado"] = datetime.now().isoformat()
    _escribir(proyecto_dir, actual)
    return actual


def agregar_log(proyecto_dir: Path, linea: str) -> None:
    if not linea.strip():
        return
    actual = leer(proyecto_dir)
    log = actual.get("log", [])
    log.append(linea)
    actual["log"] = log[-MAX_LOG:]
    actual["actualizado"] = datetime.now().isoformat()
    _escribir(proyecto_dir, actual)


def es_fase_terminal(fase: str) -> bool:
    return fase in FASES_TERMINALES
