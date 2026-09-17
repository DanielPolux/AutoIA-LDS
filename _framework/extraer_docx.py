"""
extraer_docx.py - Convierte un Word (.docx) de un proyecto Web LDS -
tipicamente la Especificacion Funcional (EF) o el Diseno Tecnico (ET) que
entrega el equipo funcional junto al Excel de la matriz de casos- a texto
plano + imagenes sueltas, para poder leerlo como contexto (Claude Code,
notas, etc.) sin abrir el binario .docx.

Nace del mismo patron ya usado a mano en PR000335 (EF_texto.txt +
EF_media/imageN.png, ET_texto.txt + ET_media/imageN.png): se formaliza
aca como script reusable, igual que extraer_matriz.py formaliza la
extraccion del Excel.

No depende de python-docx/lxml (esos paquetes no siempre estan
disponibles en la VM, ver README_PR000335.md): usa solo zipfile +
xml.etree de la libreria estandar. Un .docx es un ZIP con
word/document.xml (el texto, en WordprocessingML) y word/media/*.png|jpg
(las imagenes ya numeradas por Word en el orden en que se insertaron).

Uso:
    .venv\\Scripts\\python.exe extraer_docx.py "C:\\AUTOMATIZACION_LDS\\PR0000NN\\EF-PR0000NN-SP1.docx"
    .venv\\Scripts\\python.exe extraer_docx.py "...\\ET-PR0000NN-SP1.docx" --prefijo ET
    .venv\\Scripts\\python.exe extraer_docx.py "...\\Cualquiera.docx" --prefijo EF --salida "C:\\AUTOMATIZACION_LDS\\PR0000NN"

Genera, junto al .docx (o en --salida si se indica):
    <prefijo>_texto.txt   <- un parrafo o fila de tabla por linea, en el
                             orden real del documento (paragrafos de texto
                             normal, encabezados y celdas de tabla; celdas
                             de una misma fila separadas por " | ").
    <prefijo>_media/      <- copia de cada imagen embebida (word/media/*),
                             con el mismo nombre que ya trae Word
                             (image1.png, image2.png, ...) - no hace falta
                             renumerarlas.

El <prefijo> (EF/ET/lo que sea) se autodetecta del nombre del archivo
(la parte antes del primer "-", ej. "EF-PR000335-SP1 (1).docx" -> "EF")
si no se pasa --prefijo explicito.
"""
import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def _detectar_prefijo(ruta_docx: Path) -> str:
    """"EF-PR000335-SP1 (1).docx" -> "EF"; "EF_SP2_PR000325.docx" -> "EF"
    (cada proyecto/sprint parece nombrar sus entregables con un separador
    distinto -guion o guion bajo-, confirmado con PR000335 y PR000325).
    Toma las letras iniciales del nombre, cortando en el primer "-", "_"
    o digito que aparezca. Si no hay nada reconocible, usa el nombre de
    archivo completo (sin extension) tal cual."""
    nombre = ruta_docx.stem
    m = re.match(r"^([A-Za-zÀ-ÿ]+)", nombre)
    return m.group(1).strip() if m else nombre


def _texto_parrafo(p) -> str:
    """Concatena todos los <w:t> de un <w:p>, con un tab por cada <w:tab/>
    (Word usa <w:tab/> para las tabulaciones, no el caracter \\t suelto)."""
    partes = []
    for nodo in p.iter():
        tag = nodo.tag.rsplit("}", 1)[-1]
        if tag == "t":
            partes.append(nodo.text or "")
        elif tag == "tab":
            partes.append("\t")
    return "".join(partes)


def extraer_texto(document_xml: bytes) -> str:
    """Recorre el <w:body> en orden y arma una linea por parrafo normal y
    una linea por fila de tabla (celdas separadas por " | "), igual que
    se leeria el documento de arriba a abajo. No baja a headers/footers
    (word/header*.xml, word/footer*.xml): esos casi nunca traen contenido
    relevante para un EF/ET (numeracion de pagina, logo, etc.)."""
    raiz = ET.fromstring(document_xml)
    body = raiz.find("w:body", _NS)
    if body is None:
        raise SystemExit("El .docx no tiene <w:body> (documento invalido o corrupto).")

    lineas = []
    for elemento in body:
        tag = elemento.tag.rsplit("}", 1)[-1]
        if tag == "p":
            lineas.append(_texto_parrafo(elemento))
        elif tag == "tbl":
            for fila in elemento.findall("w:tr", _NS):
                celdas = []
                for celda in fila.findall("w:tc", _NS):
                    texto_celda = " ".join(
                        _texto_parrafo(p) for p in celda.findall(".//w:p", _NS)
                    ).strip()
                    celdas.append(texto_celda)
                lineas.append(" | ".join(celdas))
    return "\n".join(lineas)


def extraer_media(zip_docx: zipfile.ZipFile, carpeta_media: Path) -> int:
    """Copia cada word/media/* (imagenes embebidas) a carpeta_media/,
    conservando el nombre que ya les puso Word (image1.png, image2.png,
    ...). Devuelve cuantas se copiaron."""
    nombres = [n for n in zip_docx.namelist() if n.startswith("word/media/")]
    if not nombres:
        return 0
    carpeta_media.mkdir(parents=True, exist_ok=True)
    for nombre in nombres:
        destino = carpeta_media / Path(nombre).name
        with zip_docx.open(nombre) as origen, open(destino, "wb") as f:
            shutil.copyfileobj(origen, f)
    return len(nombres)


def extraer(ruta_docx: Path, carpeta_salida: Path, prefijo: str) -> tuple[Path, int]:
    with zipfile.ZipFile(ruta_docx) as z:
        try:
            document_xml = z.read("word/document.xml")
        except KeyError:
            raise SystemExit(
                f"'{ruta_docx}' no parece un .docx valido (no tiene word/document.xml)."
            )
        texto = extraer_texto(document_xml)
        carpeta_salida.mkdir(parents=True, exist_ok=True)
        ruta_texto = carpeta_salida / f"{prefijo}_texto.txt"
        ruta_texto.write_text(texto, encoding="utf-8")
        n_imagenes = extraer_media(z, carpeta_salida / f"{prefijo}_media")
    return ruta_texto, n_imagenes


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("docx", help="Ruta al .docx a extraer (EF, ET, o cualquier otro Word del proyecto)")
    p.add_argument(
        "--prefijo",
        default=None,
        help='Prefijo de salida ("EF", "ET", ...). Por defecto se autodetecta del nombre del archivo (parte antes del primer "-").',
    )
    p.add_argument(
        "--salida",
        default=None,
        help="Carpeta donde escribir <prefijo>_texto.txt y <prefijo>_media\\ (por defecto: la misma carpeta del .docx)",
    )
    args = p.parse_args()

    ruta_docx = Path(args.docx)
    if not ruta_docx.is_file():
        raise SystemExit(f"No existe el archivo: {ruta_docx}")

    prefijo = args.prefijo or _detectar_prefijo(ruta_docx)
    carpeta_salida = Path(args.salida) if args.salida else ruta_docx.parent

    ruta_texto, n_imagenes = extraer(ruta_docx, carpeta_salida, prefijo)
    print(f"Texto -> {ruta_texto}")
    print(f"Imagenes -> {carpeta_salida / (prefijo + '_media')} ({n_imagenes} archivo(s))" if n_imagenes else "Imagenes -> (el documento no trae ninguna embebida)")


if __name__ == "__main__":
    sys.exit(main())
