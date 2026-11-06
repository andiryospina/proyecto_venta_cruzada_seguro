"""Leer los informes del repositorio y partir su markdown en secciones, sin depender de Streamlit.

La app (`app/streamlit_app.py`) solo dibuja; aquí vive la lógica que se puede probar. Principio VII: la app no escribe
cifras ni avisos a mano, los **extrae** de los archivos de `reports/` y `models/`. Si un archivo falta, las funciones de
lectura devuelven `None` y la app muestra un aviso en vez de fallar.
"""
import json
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
PENDING_TITLE = re.compile(r"^(P\d+)\s*·\s*(.*)$")


@dataclass(frozen=True)
class Section:
    """Una sección de un informe: título sin `#`, nivel del encabezado (1 a 6) y cuerpo en markdown."""
    title: str
    level: int
    body: str


@dataclass(frozen=True)
class Pending:
    """Un pendiente de dato externo (`### Pnn · ...`) de `reports/decisiones_del_grupo.md`."""
    code: str
    title: str
    body: str
    closed: bool


def read_text(path: Path) -> str | None:
    """Texto UTF-8 del archivo, o `None` si no existe o no se puede leer."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def read_json(path: Path) -> dict | None:
    """Contenido de un JSON, o `None` si falta o no es un JSON válido."""
    text = read_text(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def read_csv(path: Path) -> pd.DataFrame | None:
    """Tabla de un CSV, o `None` si falta o está vacío o dañado."""
    try:
        return pd.read_csv(path)
    except (OSError, ValueError, UnicodeDecodeError):
        return None


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """Encabezados `(índice de línea, nivel, título)`, sin contar los `#` dentro de bloques de código."""
    found, in_code = [], False
    for index, line in enumerate(lines):
        if FENCE.match(line):
            in_code = not in_code
            continue
        match = None if in_code else HEADING.match(line)
        if match:
            found.append((index, len(match.group(1)), match.group(2)))
    return found


def _section_at(lines: list[str], headings: list[tuple[int, int, str]], position: int) -> Section:
    """Sección del encabezado `position`: llega hasta el siguiente encabezado del mismo nivel o menor."""
    start, level, title = headings[position]
    end = len(lines)
    for next_start, next_level, _ in headings[position + 1:]:
        if next_level <= level:
            end = next_start
            break
    return Section(title=title, level=level, body="\n".join(lines[start + 1:end]).strip("\n"))


def split_sections(markdown: str | None, level: int) -> list[Section]:
    """Todas las secciones cuyo encabezado es exactamente del nivel dado (las subsecciones quedan dentro del cuerpo)."""
    if not markdown:
        return []
    lines = markdown.splitlines()
    headings = _headings(lines)
    return [_section_at(lines, headings, i) for i, (_, lvl, _) in enumerate(headings) if lvl == level]


def find_section(markdown: str | None, prefix: str, levels: tuple[int, ...] = (2, 3, 4)) -> Section | None:
    """Primera sección cuyo título empieza por `prefix` (sin distinguir mayúsculas), o `None` si no existe."""
    if not markdown:
        return None
    lines = markdown.splitlines()
    headings = _headings(lines)
    wanted = prefix.casefold()
    for i, (_, level, title) in enumerate(headings):
        if level in levels and title.replace("*", "").strip().casefold().startswith(wanted):
            return _section_at(lines, headings, i)
    return None


def strip_title(markdown: str | None) -> str:
    """Quita el título `# ...` del inicio (la pestaña de la app pone el suyo)."""
    if not markdown:
        return ""
    lines = markdown.splitlines()
    first = next((i for i, line in enumerate(lines) if line.strip()), None)
    if first is None or not re.match(r"^#\s+\S", lines[first]):
        return markdown
    return "\n".join(lines[first + 1:]).lstrip("\n")


def pick_bullets(markdown: str | None, starts: list[str]) -> list[str]:
    """Viñetas (`- ...`, con sus líneas de continuación) cuyo texto empieza por alguno de `starts`, ignorando las negritas."""
    if not markdown:
        return []
    bullets, current = [], None
    for line in markdown.splitlines():
        if line.startswith("- "):
            current = [line]
            bullets.append(current)
        elif current is not None and line.startswith((" ", "\t")) and line.strip():
            current.append(line)
        else:
            current = None
    picked = []
    for bullet in bullets:
        plain = bullet[0][2:].replace("*", "").strip()
        if any(plain.startswith(start) for start in starts):
            picked.append("\n".join(bullet))
    return picked


def list_pending(markdown: str | None) -> tuple[str, list[Pending]]:
    """Introducción y pendientes de la sección `B.` de `decisiones_del_grupo.md` (`("", [])` si no existe)."""
    section = find_section(markdown, "B.", levels=(2,))
    if section is None:
        return "", []
    intro_lines = []
    for line in section.body.splitlines():
        if line.startswith("### "):
            break
        intro_lines.append(line)
    items = []
    for sub in split_sections(section.body, 3):
        match = PENDING_TITLE.match(sub.title.replace("*", ""))
        if match:
            items.append(Pending(code=match.group(1), title=sub.title, body=sub.body, closed="CERRADO" in sub.title.upper()))
    return "\n".join(intro_lines).strip(), items
