#!/usr/bin/env python3
"""Check dist/shaders the way Batocera reads it.

For every shader set and every Batocera system, resolves the shader as batocera-launch does
(config/config.py render_config + config/defaults.py load_defaults, then
batocera_launch_libretro/emulator.py: <shader>.slangp on glcore/vulkan, .glslp on gl, looked up in
/userdata/shaders then /usr/share/batocera/shaders), and checks every file RetroArch will open.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
USER = ROOT / "dist" / "shaders"           # stands for /userdata/shaders
STOCK_OK = {"handheld/lcd-grid-v2"}         # in Batocera's /usr/share/batocera/shaders (slang and glsl)
errors: list[str] = []


def load_defaults(system: str, d: dict) -> dict:
    """batocera_launch/config/defaults.py load_defaults (no -arch file here)."""
    config = dict(d.get("default", {}))
    config.update(d.get(system, {}))
    return config


def check_preset(path: Path, seen: set[Path]) -> None:
    """A .slangp: #reference chain, then every pass and its #includes."""
    if path in seen:
        return
    seen.add(path)
    if not path.is_file():
        errors.append(f"missing {path.relative_to(ROOT)}")
        return
    text = path.read_text()
    for ref in re.findall(r'^#reference "([^"]+)"', text, re.M):
        check_preset((path.parent / ref).resolve(), seen)
    for src in re.findall(r'^shader\d+\s*=\s*"?([^"\n]+?)"?\s*$', text, re.M):
        check_slang((path.parent / src).resolve(), seen)


def check_slang(path: Path, seen: set[Path]) -> None:
    if path in seen:
        return
    seen.add(path)
    if not path.is_file():
        errors.append(f"missing {path}")
        return
    for inc in re.findall(r'^#include "([^"]+)"', path.read_text(), re.M):
        check_slang((path.parent / inc).resolve(), seen)


def main() -> int:
    systems = [l.split("\t")[0] for l in (ROOT / "mapping" / "batocera-systems.tsv").read_text().splitlines()
               if l and not l.startswith("#")]
    mapping = yaml.safe_load((ROOT / "mapping" / "systems.yml").read_text())["systems"]
    unmapped = [s for s in systems if s not in mapping]
    if unmapped:
        errors.append(f"systems on the default entry: {' '.join(unmapped)}")

    sets = sorted(p.parent for p in (USER / "configs").glob("*/rendering-defaults.yml"))
    seen: set[Path] = set()
    counts = {}
    for set_dir in sets:
        yml = yaml.load((set_dir / "rendering-defaults.yml").read_text(), Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
        n = {"lola": 0, "stock": 0, "none": 0}
        for system in systems + ["some-new-system"]:
            shader = load_defaults(system, yml).get("shader")
            if shader is None:
                n["none"] += 1
                continue
            slang, glsl = USER / f"{shader}.slangp", USER / f"{shader}.glslp"
            if slang.exists():
                n["lola"] += 1
                if glsl.exists():
                    errors.append(f"{glsl}: a .glslp would make Batocera pick the gl driver on Intel")
                check_preset(slang.resolve(), seen)
            elif shader in STOCK_OK:
                n["stock"] += 1
            else:
                errors.append(f"{set_dir.name}/{system}: {shader} not found")
        counts[set_dir.name] = n

    for name, n in counts.items():
        print(f"{name:28} Lola {n['lola']:3}  stock LCD {n['stock']:2}  none {n['none']:2}")
    print(f"{len(seen)} files RetroArch opens, all present" if not errors else "")
    for e in errors:
        print("ERROR", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
