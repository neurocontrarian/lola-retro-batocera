#!/usr/bin/env python3
"""Build the Lola Retro shader sets for Batocera.

Reads mapping/systems.yml and third_party/lola-retro, writes dist/shaders/ (the folder to copy to
/userdata/shaders on Batocera) and dist/lola-retro-batocera-<version>.zip.

dist/shaders/
  lola-retro/                      Lola Retro's RetroArch presets, unchanged
  lola-retro-batocera/<set>/<name>.slangp
                                   small presets: #reference to Lola Retro's + the mapping's params
  configs/<set>/rendering-defaults.yml
                                   one Batocera shader set: which preset each system gets
"""
from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path

import yaml

from presets import DIST, LOLA, MAPPING, ROOT, STOCK_SHADERS, USER_SHADERS, declared_params, preset_values

VERSION = (ROOT / "VERSION").read_text().strip()
OURS = "lola-retro-batocera"

def lola_preset(chain: str, glass: str, name: str) -> Path:
    """Lola Retro's preset for a system name or a device name."""
    base = LOLA if chain == "full" else LOLA / chain
    for folder in (base / "systems" / glass, base / glass):
        path = folder / f"{name}.slangp"
        if path.exists():
            return path
    raise SystemExit(f"no Lola Retro preset '{name}' in {chain}/{glass}")


def fmt(v: float | int) -> str:
    return str(int(v)) if float(v).is_integer() else str(v)


def entry(value) -> dict:
    """One mapping value as {kind, name, as, params}."""
    if isinstance(value, dict):
        return {"kind": "lola", "name": value["lola"], "as": value.get("as", value["lola"]),
                "params": value.get("params", {})}
    if value is None or value == "none":
        return {"kind": "none"}
    if value.startswith("stock:"):
        path = value[len("stock:"):]
        if path not in STOCK_SHADERS:
            raise SystemExit(f"{path}: not in presets.STOCK_SHADERS (Batocera's own shaders)")
        return {"kind": "stock", "path": path}
    return {"kind": "lola", "name": value, "as": value, "params": {}}


def shader_of(e: dict, set_name: str, names: dict[str, str]) -> str | None:
    """The value for rendering-defaults.yml (a path under /userdata/shaders or Batocera's own)."""
    if e["kind"] == "none":
        return None
    if e["kind"] == "stock":
        return e["path"]
    return f"{OURS}/{set_name}/{names[e['as']]}"


def build() -> None:
    mapping = yaml.safe_load(MAPPING.read_text())
    common = mapping["params"]
    default = entry(mapping["default"])
    tvs, console_params = mapping["tvs"], mapping["console_params"]
    systems = {k: entry(v) for k, v in mapping["systems"].items()}

    variants: dict[str, tuple] = {}  # wrapper name -> (preset, params): one name, one meaning
    for e in [default, *systems.values()]:
        if e["kind"] == "lola":
            key = (e["name"], sorted(e["params"].items()))
            if variants.setdefault(e["as"], key) != key:
                raise SystemExit(f"'{e['as']}' is used for two different presets or params")

    declared: set[str] = set()
    shutil.rmtree(DIST, ignore_errors=True)
    shutil.copytree(LOLA, USER_SHADERS / "lola-retro")

    for set_name, s in mapping["sets"].items():
        chain, glass = s["chain"], s["glass"]
        none = set(s.get("none", []))
        preset_params = s.get("preset_params", {})
        if bad := sorted(none - set(systems)):
            raise SystemExit(f"{set_name}: 'none' lists systems the mapping doesn't have: {bad}")
        if bad := sorted(set(preset_params) - {lola for lola, _ in variants.values()}):
            raise SystemExit(f"{set_name}: preset_params for presets no system uses: {bad}")
        in_set = {k: {"kind": "none"} if k in none else e for k, e in systems.items()}
        used = {e["as"] for e in [default, *in_set.values()] if e["kind"] == "lola"}

        tv = s.get("tv")
        if tv:
            if lola_preset(chain, glass, tv).parent.parent.name == "systems":
                raise SystemExit(f"{set_name}: tv '{tv}' is a system preset, not a device")
            for lola, base in tvs.items():
                if lola_preset(chain, glass, base).parent.parent.name == "systems":
                    raise SystemExit(f"tvs: '{base}' is a system preset, not a device")
                lola_preset(chain, glass, lola)

        names: dict[str, str] = {}   # wrapper name in the mapping -> file name in this set
        written: dict[Path, str] = {}
        for name in sorted(used):
            lola, own_params = variants[name]
            src = lola_preset(chain, glass, lola)
            console, extra, file_name = {}, {}, name
            if tv and lola in tvs:   # the set's TV, with the console's own values
                base = preset_values(lola_preset(chain, glass, tvs[lola]))
                console = {k: v for k, v in preset_values(src).items()
                           if k in console_params and v != base.get(k)}
                extra = s.get("tv_params", {})
                src = lola_preset(chain, glass, tv)
                if lola == tvs[lola] and name == lola:   # a bare TV: name the file after the new one
                    file_name = tv
            known = declared_params(src)
            declared |= known
            ours = {**console, **s.get("params", {}), **extra, **dict(own_params), **preset_params.get(lola, {})}
            if missing := sorted(set(ours) - known):
                raise SystemExit(f"{src}: no parameter {missing}")
            names[name] = file_name
            dst = USER_SHADERS / OURS / set_name / f"{names[name]}.slangp"
            dst.parent.mkdir(parents=True, exist_ok=True)
            ref = os.path.relpath(USER_SHADERS / "lola-retro" / src.relative_to(LOLA), dst.parent)
            lines = [f'#reference "{Path(ref).as_posix()}"',
                     f"# Lola Retro for Batocera {VERSION}: settings over the Lola Retro preset"]
            lines += [f"{k} = {fmt(v)}" for k, v in {**common, **ours}.items() if k in known]
            text = "\n".join(lines) + "\n"
            if written.setdefault(dst, text) != text:
                raise SystemExit(f"{dst}: two presets would share this file")
            dst.write_text(text)

        doc = {"default": {"shader": shader_of(default, set_name, names), "scanline": False}}
        doc.update({system: {"shader": shader_of(e, set_name, names)} for system, e in in_set.items()})
        path = USER_SHADERS / "configs" / set_name / "rendering-defaults.yml"
        path.parent.mkdir(parents=True)
        head = (f"## {set_name.upper()}: Lola Retro {chain}, {glass} glass "
                f"(Lola Retro for Batocera {VERSION})\n"
                "## Generated by tools/build.py from mapping/systems.yml. `shader: null` means none.\n")
        path.write_text(head + yaml.safe_dump(doc, sort_keys=False, default_flow_style=False))

    if unused := sorted(set(common) - declared):
        raise SystemExit(f"mapping params declared by no Lola Retro preset: {unused}")

    zip_path = DIST / f"lola-retro-batocera-{VERSION}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(USER_SHADERS.rglob("*")):
            if f.is_file():
                z.write(f, Path("shaders") / f.relative_to(USER_SHADERS))
        for extra in ("install.sh", "README.md"):
            z.write(ROOT / extra, extra)

    print(f"{len(mapping['sets'])} sets, {len(variants)} presets, {len(systems)} systems -> {zip_path.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
