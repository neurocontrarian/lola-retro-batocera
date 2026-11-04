#!/usr/bin/env python3
"""Build the Lola Retro shader sets for Batocera.

Reads mapping/systems.yml and third_party/lola-retro, writes dist/shaders/ (the folder to copy to
/userdata/shaders on Batocera) and dist/lola-retro-batocera-<version>.zip.

dist/shaders/
  lola-retro/                      Lola Retro's RetroArch presets, unchanged
  lola-retro-batocera/<chain>/<glass>/<name>.slangp
                                   small presets: #reference to Lola Retro's + the settings below
  configs/<set>/rendering-defaults.yml
                                   one Batocera shader set: which preset each system gets
"""
from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LOLA = ROOT / "third_party" / "lola-retro"
MAPPING = ROOT / "mapping" / "systems.yml"
DIST = ROOT / "dist"
VERSION = (ROOT / "VERSION").read_text().strip()

OURS = "lola-retro-batocera"

# Shader sets as Batocera's menu lists them: (set folder, Lola Retro chain, glass)
SETS = [
    ("lola-retro", "lite", "curved"),
    ("lola-retro-flat", "lite", "flat"),
    ("lola-retro-full", "full", "curved"),
    ("lola-retro-full-flat", "full", "flat"),
    ("lola-retro-superlite", "super-lite", "curved"),
    ("lola-retro-superlite-flat", "super-lite", "flat"),
]

# Settings over Lola Retro's presets, for every system (the defaults StrikeHD settled on):
COMMON_PARAMS = {
    "LR_MASK_PX": 1,      # mask on whole screen pixels: no moire below 4K (Lola Retro issue #11)
    "LR_SMOOTH": 1,       # each screen pixel shows the light averaged over its height: less moire
    "LR_DBLEND_AUTO": 1,  # RGB and S-Video presets blend 1-pixel dither as composite did
    "LR_DAMPER": 0,       # no Trinitron damper wires across the picture (issue #16)
}


def chain_dir(chain: str) -> Path:
    return LOLA if chain == "full" else LOLA / chain


def lola_preset(chain: str, glass: str, name: str) -> Path:
    """Lola Retro's preset for a system name or a device name."""
    for folder in (chain_dir(chain) / "systems" / glass, chain_dir(chain) / glass):
        path = folder / f"{name}.slangp"
        if path.exists():
            return path
    raise SystemExit(f"no Lola Retro preset '{name}' in {chain}/{glass}")


_PRAGMA = re.compile(r"^#pragma parameter (\w+)", re.M)
_INCLUDE = re.compile(r'^#include "([^"]+)"', re.M)


def declared_params(preset: Path) -> set[str]:
    """Every parameter the preset's passes declare (following #include)."""
    names: set[str] = set()
    seen: set[Path] = set()

    def scan(path: Path) -> None:
        path = path.resolve()
        if path in seen:
            return
        seen.add(path)
        text = path.read_text()
        names.update(_PRAGMA.findall(text))
        for inc in _INCLUDE.findall(text):
            scan(path.parent / inc)

    for line in preset.read_text().splitlines():
        m = re.match(r"^shader\d+\s*=\s*\"?([^\"]+?)\"?\s*$", line)
        if m:
            scan(preset.parent / m.group(1))
    return names


def fmt(v: float | int) -> str:
    return str(int(v)) if float(v).is_integer() else str(v)


def entry(value) -> dict:
    """Normalise one mapping value to {kind, name, as, params}."""
    if isinstance(value, dict):
        return {"kind": "lola", "name": value["lola"], "as": value.get("as", value["lola"]),
                "params": value.get("params", {})}
    if value is None or value == "none":
        return {"kind": "none"}
    if value.startswith("stock:"):
        return {"kind": "stock", "path": value[len("stock:"):]}
    return {"kind": "lola", "name": value, "as": value, "params": {}}


def build() -> None:
    mapping = yaml.safe_load(MAPPING.read_text())
    systems = {k: entry(v) for k, v in mapping["systems"].items()}
    default = entry(mapping["default"])

    out = DIST / "shaders"
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(LOLA, out / "lola-retro")

    wrappers: dict[tuple[str, str, str], str] = {}  # (chain, glass, as) -> path for rendering-defaults
    for chain, glass in sorted({(c, g) for _, c, g in SETS}):
        for e in [default, *systems.values()]:
            if e["kind"] != "lola":
                continue
            key = (chain, glass, e["as"])
            if key in wrappers:
                continue
            src = lola_preset(chain, glass, e["name"])
            known = declared_params(src)
            params = {**COMMON_PARAMS, **e["params"]}
            missing = sorted(set(e["params"]) - known)
            if missing:
                raise SystemExit(f"{src}: no parameter {missing}")
            dst = out / OURS / chain / glass / f"{e['as']}.slangp"
            dst.parent.mkdir(parents=True, exist_ok=True)
            ref = Path("..", "..", "..", src.relative_to(LOLA.parent)).as_posix()
            lines = [f'#reference "{ref}"',
                     f"# Lola Retro for Batocera {VERSION}: settings over the Lola Retro preset"]
            lines += [f"{k} = {fmt(v)}" for k, v in params.items() if k in known]
            dst.write_text("\n".join(lines) + "\n")
            wrappers[key] = f"{OURS}/{chain}/{glass}/{e['as']}"

    def shader_of(e: dict, chain: str, glass: str) -> str | None:
        if e["kind"] == "none":
            return None
        if e["kind"] == "stock":
            return e["path"]
        return wrappers[(chain, glass, e["as"])]

    for set_name, chain, glass in SETS:
        doc = {"default": {"shader": shader_of(default, chain, glass), "scanline": False}}
        for system, e in systems.items():
            doc[system] = {"shader": shader_of(e, chain, glass)}
        path = out / "configs" / set_name / "rendering-defaults.yml"
        path.parent.mkdir(parents=True, exist_ok=True)
        head = (f"## {set_name.upper()}: Lola Retro {chain}, {glass} glass "
                f"(Lola Retro for Batocera {VERSION})\n"
                "## Generated by tools/build.py from mapping/systems.yml. An empty shader means none.\n")
        path.write_text(head + yaml.safe_dump(doc, sort_keys=False, default_flow_style=False))

    zip_path = DIST / f"lola-retro-batocera-{VERSION}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob("*")):
            if f.is_file():
                z.write(f, Path("shaders") / f.relative_to(out))
        for extra in ("install.sh", "README.md"):
            z.write(ROOT / extra, extra)

    print(f"{len(SETS)} sets, {len(wrappers)} presets, {len(systems)} systems -> {zip_path.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(build())
