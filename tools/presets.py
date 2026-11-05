"""Paths and RetroArch preset parsing shared by build.py and check.py."""
from __future__ import annotations

import functools
import re
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOLA = ROOT / "third_party" / "lola-retro"
MAPPING = ROOT / "mapping" / "systems.yml"
SYSTEMS_TSV = ROOT / "mapping" / "batocera-systems.tsv"
DIST = ROOT / "dist"
USER_SHADERS = DIST / "shaders"           # stands for /userdata/shaders

# Batocera's own shaders the mapping may use (in /usr/share/batocera/shaders, slang and glsl)
STOCK_SHADERS = {"handheld/lcd-grid-v2"}

_REFERENCE = re.compile(r'^#reference "([^"]+)"', re.M)
_PASS = re.compile(r'^shader\d+\s*=\s*"?([^"\n]+?)"?\s*$', re.M)
_INCLUDE = re.compile(r'^#include "([^"]+)"', re.M)
_PRAGMA = re.compile(r"^#pragma parameter (\w+)", re.M)
_VALUE = re.compile(r'^(LR_\w+)\s*=\s*"?([-\d.]+)"?\s*$', re.M)


@functools.cache
def _links(path: Path) -> tuple[Path, ...]:
    """The files one preset or shader file opens directly ([] if it is missing)."""
    if not path.is_file():
        return ()
    text = path.read_text()
    found = _REFERENCE.findall(text) + _PASS.findall(text) + _INCLUDE.findall(text)
    return tuple((path.parent / f).resolve() for f in found)


def files_opened(preset: Path) -> list[Path]:
    """Every file RetroArch opens for a preset: #reference chain, passes, #includes."""
    seen: dict[Path, None] = {}
    todo = [preset.resolve()]
    while todo:
        path = todo.pop()
        if path not in seen:
            seen[path] = None
            todo.extend(_links(path))
    return list(seen)


@functools.cache
def _pragmas(path: Path) -> frozenset[str]:
    if path.suffix not in (".slang", ".inc"):
        return frozenset()
    if not path.is_file():
        raise SystemExit(f"missing {path}")
    return frozenset(_PRAGMA.findall(path.read_text()))


def declared_params(preset: Path) -> set[str]:
    """Every parameter the preset's passes declare."""
    return set().union(*(_pragmas(p) for p in files_opened(preset)))


@functools.cache
def preset_values(preset: Path) -> types.MappingProxyType:
    """The LR_ values one preset file sets itself (not those of the presets it references)."""
    return types.MappingProxyType({k: float(v) for k, v in _VALUE.findall(preset.read_text())})
