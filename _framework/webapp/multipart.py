"""
Parser manual de multipart/form-data (RFC 7578), SOLO libreria estandar.

Por que existe: `cgi.FieldStorage` (la forma clasica de parsear esto en
Python) fue removido en Python 3.13 (PEP 594) - confirmado en el venv de
este proyecto (`C:\\Proyectos\\PlataformaWeb\\.venv`, Python 3.13.13). No
hay ningun framework web instalado (ver README.md de este webapp) y
instalar paquetes nuevos por pip es poco confiable en esta VM, asi que
este parser evita cualquier dependencia externa.

Uso:
    campos = parsear(cuerpo_bytes, content_type_header)
    # campos["proyecto"][0].texto()      -> valor de un campo de texto simple
    # campos["excel"][0].nombre_archivo  -> "MCP-....xlsx"
    # campos["excel"][0].datos           -> bytes crudos del archivo

Ejemplo minimo verificado a mano (ver bloque `if __name__ == "__main__"`
al final: arma un body con boundary conocido y confirma que separa bien
un campo de texto y un archivo).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Parte:
    nombre: str
    nombre_archivo: str | None
    content_type: str | None
    datos: bytes

    def texto(self, encoding: str = "utf-8") -> str:
        return self.datos.decode(encoding, errors="replace")


class MultipartError(ValueError):
    pass


_RE_BOUNDARY = re.compile(r'boundary="?([^";]+)"?', re.IGNORECASE)
_RE_DISPOSICION = re.compile(
    r'Content-Disposition:\s*form-data;\s*(.*)', re.IGNORECASE
)
_RE_PARAM = re.compile(r'(\w+)="((?:[^"\\]|\\.)*)"')
_RE_CONTENT_TYPE = re.compile(r'Content-Type:\s*([^\r\n]+)', re.IGNORECASE)


def extraer_boundary(content_type_header: str) -> bytes:
    if not content_type_header or "multipart/form-data" not in content_type_header.lower():
        raise MultipartError(f"Content-Type no es multipart/form-data: {content_type_header!r}")
    m = _RE_BOUNDARY.search(content_type_header)
    if not m:
        raise MultipartError(f"No se encontro boundary en Content-Type: {content_type_header!r}")
    return m.group(1).encode("ascii")


def _parsear_headers_parte(bloque_headers: bytes) -> tuple[str, str | None, str | None]:
    texto = bloque_headers.decode("utf-8", errors="replace")
    m_disp = _RE_DISPOSICION.search(texto)
    if not m_disp:
        raise MultipartError(f"Parte sin Content-Disposition: form-data valido: {texto!r}")
    params = dict(_RE_PARAM.findall(m_disp.group(1)))
    nombre = params.get("name")
    if nombre is None:
        raise MultipartError(f"Parte sin 'name' en Content-Disposition: {texto!r}")
    nombre_archivo = params.get("filename")
    m_ct = _RE_CONTENT_TYPE.search(texto)
    content_type = m_ct.group(1).strip() if m_ct else None
    return nombre, nombre_archivo, content_type


def parsear(cuerpo: bytes, content_type_header: str) -> dict[str, list[Parte]]:
    boundary = extraer_boundary(content_type_header)
    delimitador = b"--" + boundary
    # Cada parte queda entre delimitadores; el ultimo delimitador termina
    # en "--" (delimitador de cierre) en vez de "\r\n".
    trozos = cuerpo.split(delimitador)
    resultado: dict[str, list[Parte]] = {}
    for trozo in trozos:
        if not trozo or trozo in (b"--", b"--\r\n") or trozo.strip() == b"":
            continue
        # cada trozo arranca con \r\n tras el boundary y termina con \r\n
        # antes del siguiente boundary (o "--" si es el cierre final).
        cuerpo_trozo = trozo[2:] if trozo.startswith(b"\r\n") else trozo
        if cuerpo_trozo.endswith(b"--\r\n") or cuerpo_trozo.endswith(b"--"):
            continue  # delimitador de cierre sin datos utiles
        cuerpo_trozo = cuerpo_trozo[:-2] if cuerpo_trozo.endswith(b"\r\n") else cuerpo_trozo

        separador = b"\r\n\r\n"
        idx = cuerpo_trozo.find(separador)
        if idx == -1:
            continue  # trozo malformado, se ignora en vez de tumbar todo el parseo
        bloque_headers = cuerpo_trozo[:idx]
        datos = cuerpo_trozo[idx + len(separador):]

        try:
            nombre, nombre_archivo, content_type = _parsear_headers_parte(bloque_headers)
        except MultipartError:
            continue

        parte = Parte(nombre=nombre, nombre_archivo=nombre_archivo, content_type=content_type, datos=datos)
        resultado.setdefault(nombre, []).append(parte)

    return resultado


if __name__ == "__main__":
    # Verificacion manual minima (no hay pytest en el venv): arma un body
    # con boundary conocido, con un campo de texto y un archivo chico, y
    # confirma que el parseo separa bien ambos.
    boundary = "----WebKitFormBoundaryTEST123"
    cuerpo = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="proyecto"\r\n\r\n'
        f"PR999999\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="excel"; filename="matriz.xlsx"\r\n'
        f"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n"
    ).encode("utf-8") + b"BYTES-FALSOS-DE-XLSX" + f"\r\n--{boundary}--\r\n".encode("utf-8")

    campos = parsear(cuerpo, f"multipart/form-data; boundary={boundary}")
    assert campos["proyecto"][0].texto() == "PR999999", campos["proyecto"][0].texto()
    assert campos["excel"][0].nombre_archivo == "matriz.xlsx", campos["excel"][0].nombre_archivo
    assert campos["excel"][0].datos == b"BYTES-FALSOS-DE-XLSX", campos["excel"][0].datos
    assert campos["excel"][0].content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    print("OK: multipart.py parsea campo de texto + archivo correctamente.")
