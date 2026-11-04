#!/usr/bin/env python3
"""Check dist/shaders the way Batocera reads it.

For every shader set and every Batocera system, resolves the shader as batocera-launch does
(config/config.py render_config + config/defaults.py load_defaults, then
batocera_launch_libretro/emulator.py: <shader>.slangp on glcore/vulkan, .glslp on gl, looked up in
/userdata/shaders then /usr/share/batocera/shaders), and checks every file RetroArch will open.
"""
from __future__ import annotations

import sys

import yaml

from presets import MAPPING, ROOT, STOCK_SHADERS, SYSTEMS_TSV, USER_SHADERS, files_opened


def main() -> int:
    errors: list[str] = []
    systems = [l.split("\t")[0] for l in SYSTEMS_TSV.read_text().splitlines() if l and not l.startswith("#")]
    mapping = yaml.safe_load(MAPPING.read_text())
    mapped = set(mapping["systems"])
    if unmapped := [s for s in systems if s not in mapped]:
        errors.append(f"systems on the default entry: {' '.join(unmapped)}")
    if unknown := sorted(mapped - set(systems) - set(mapping["old_names"])):
        errors.append(f"mapping names Batocera doesn't have: {' '.join(unknown)}")

    opened: set = set()
    for yml in sorted(USER_SHADERS.glob("configs/*/rendering-defaults.yml")):
        doc = yaml.safe_load(yml.read_text())
        n = {"lola": 0, "stock": 0, "none": 0}
        # load_defaults: the system's entry merged over `default`
        for system in ["default"] + systems:
            shader = {**doc["default"], **(doc.get(system) or {})}.get("shader")
            if shader is None:
                n["none"] += 1
            elif (slang := USER_SHADERS / f"{shader}.slangp").exists():
                n["lola"] += 1
                if slang.with_suffix(".glslp").exists():
                    errors.append(f"{shader}.glslp would make Batocera pick the gl driver on Intel")
                opened.update(files_opened(slang))
            elif shader in STOCK_SHADERS:
                n["stock"] += 1
            else:
                errors.append(f"{yml.parent.name}/{system}: {shader} not found")
        print(f"{yml.parent.name:28} Lola {n['lola']:3}  stock {n['stock']:2}  none {n['none']:2}  (default included)")

    errors += [f"missing {p.relative_to(ROOT) if p.is_relative_to(ROOT) else p}"
               for p in sorted(opened) if not p.is_file()]
    print(f"{len(opened)} files RetroArch opens" + ("" if errors else ", all present"))
    for e in errors:
        print("ERROR", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
