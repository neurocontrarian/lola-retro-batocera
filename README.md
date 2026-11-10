# Lola Retro for Batocera

The [Lola Retro](https://github.com/zoran123456/lola-retro) CRT shader (MIT) as **Batocera shader sets**:
once installed they show up in **Game settings → Shader set**, and every system gets the right TV or
monitor by itself (NES on a composite TV, Amiga on a 1084S, arcade on a 15 kHz monitor, DOS on a VGA
monitor, Game Boy on an LCD grid…).

## The sets

| Set (menu) | Lola Retro chain | Glass | For |
|---|---|---|---|
| `LOLA-RETRO` | lite | curved | **recommended**: the same picture as the full chain for a fraction of the GPU cost |
| `LOLA-RETRO-FLAT` | lite | flat | the same, flat glass |
| `LOLA-RETRO-FULL` | full | curved | high-end GPUs; adds what is around the tube, games take longer to start |
| `LOLA-RETRO-FULL-FLAT` | full | flat | the same |
| `LOLA-RETRO-SUPERLITE` | super lite | curved | modest GPUs |
| `LOLA-RETRO-SUPERLITE-FLAT` | super lite | flat | the same |

In these six sets every console gets the TV and cable most players had (NES, SNES, Mega Drive… on
composite; PS2 and GameCube on S-Video).

**The sets by device** put the same device in place of that TV for every console. Each console keeps its
own values (timing, encoder, TV standard). All of them use the lite chain and flat glass. Computers and arcade keep their
monitors (VGA, 1084S, X68000, 15 kHz arcade).

| Set (menu) | Device |
|---|---|
| `LOLA-RETRO-RF` | old TV on the antenna input: snow, ghosting, soft focus |
| `LOLA-RETRO-COMPOSITE` | living-room TV on the yellow RCA cable: colour bleed, dithering blends |
| `LOLA-RETRO-S-VIDEO` | Sony Trinitron on S-Video: sharper, cool white |
| `LOLA-RETRO-PERITEL` | living-room TV on SCART (Péritel) RGB: sharp, no signal artefacts |
| `LOLA-RETRO-PVM-RGB` | Sony PVM/BVM studio monitor on RGB: the sharpest, strong scanlines |
| `LOLA-RETRO-PERITEL-PLUS` | `PERITEL` with Dither blend auto 1 and Phosphor afterglow 0 (see below) |
| `LOLA-RETRO-PVM-RGB-PLUS` | `PVM-RGB` with the same two settings |
| `LOLA-RETRO-PVM-COMPOSITE` | Sony PVM-14L2 studio monitor on composite: clean but blended |
| `LOLA-RETRO-PROJECTOR` | three-tube arcade CRT projector: no mask, colour fringes, soft |
| `LOLA-RETRO-TV-SHOW` | the game as seen on a 90s TV programme (broadcast in PAL, received with an antenna) |

Measured with the same shader (StrikeHD project): RTX 3090 at 4K, lite = 4.5 ms per frame and ~60 W, the
full chain = 12.4 ms and ~310 W for no visible difference. Intel UHD 630 at 1080p: lite = 72 ms, too slow;
recent integrated GPUs (Intel Core Ultra, Radeon 780M) run the lite chain. Raspberry Pi 4 and ARM
handhelds: too slow even with super lite (measured by the author of Lola Retro, issue #13).

## Installation

On the Batocera machine, from the zip unzipped in an empty folder (files left from an older version
would be installed too):

```sh
sh install.sh              # install or update
sh install.sh --uninstall  # remove everything
```

Or by hand: copy the contents of the zip's `shaders/` folder to the network share `\\BATOCERA\share\shaders`
(that is `/userdata/shaders`). Nothing in the system is changed: Batocera reads user sets from
`/userdata/shaders/configs/`.

Then: **Menu → Game settings → Shader set → LOLA-RETRO** (for everything), or the same setting in a
system's advanced settings.

## What is installed

```
/userdata/shaders/
  lola-retro/                  Lola Retro's RetroArch presets, unchanged (also usable from RetroArch's menu)
  lola-retro-batocera/<set>/   small presets: #reference to Lola Retro's + the settings below
  configs/lola-retro*/rendering-defaults.yml   the sets: which preset for which system
```

The presets keep Lola Retro's settings. Only the two `-PLUS` sets add two (`params` of those sets in
`mapping/systems.yml`):

| Parameter | Value | Effect |
|---|---|---|
| Dither blend auto (`LR_DBLEND_AUTO`) | 1 | on RGB, 1-pixel dithering blends as it did on composite: Sonic's waterfall looks transparent instead of striped |
| Phosphor afterglow (`LR_PERSIST`) | 0 | no trail behind moving sprites (Lola Retro's default is 0.08) |

Dither blend auto works on console and Amiga timings only: arcade (Console timing 8) and computer
monitors keep Dither blend as it is set.

PlayStation: Console timing 4 and "Frames over 300 lines" 1, because the default cores send 1× frames.
At 2× internal resolution, set "Frames over 300 lines" back to 0 (Quick Menu → Shaders → Shader Parameters).

Every parameter can still be changed in game in RetroArch (Hotkey + B → Quick Menu → Shaders).

## What it covers, and what it doesn't

- **Every system run by a RetroArch core** (most of Batocera's retro systems). The system → preset
  mapping is in `mapping/systems.yml`, which lists every Batocera system.
- **Standalone emulators** (PCSX2, Dolphin, Mupen64Plus, DuckStation, PPSSPP, Cemu, standalone MAME…)
  don't use Batocera's shader sets: each has its own filters. Their systems are listed anyway: switch
  a system to its RetroArch core (the system's *Emulator* option, e.g. N64 → mupen64plus-next, PS2 →
  lrps2, GameCube → dolphin libretro) and it gets the right preset.
- **Arcade**: `arcade-15khz` sets Console timing 8 for every MAME and FBNeo game, so 24 and 31 kHz
  games in those cores are drawn on a 15 kHz tube too. One preset per system can't avoid that. Naomi and
  Atomiswave use `dos-pc` (31 kHz, 480 lines), the closest preset until Lola Retro has an arcade 31 kHz one.
- **LCD handhelds**: Batocera's own LCD grid (`handheld/lcd-grid-v2`), since they had no tube.
  **Vectrex, Virtual Boy, Game & Watch, DS, 3DS, PSP and HD systems**: no shader.

## Video driver

The presets exist in slang only: Batocera detects it and starts RetroArch on **glcore** (OpenGL 3.1+)
on NVIDIA, AMD and Intel, unless a driver is forced in the options. **Vulkan** (the *Graphics API*
option) works too and is recommended by Lola Retro. The old `gl` driver doesn't read slang: with it,
there is no shader (the YabaSanshiro, PPSSPP and Boom3 cores, which Batocera puts on `gl`).

NVIDIA on X11: if a fixed tearing band shows in full screen, it is Batocera's picom compositor
(issue batocera-linux/batocera.linux#17272), not the shader.

## Development

```sh
python3 tools/build.py   # dist/shaders/ and dist/lola-retro-batocera-<version>.zip
python3 tools/check.py   # checks every Batocera system is listed, resolves every system of every set as Batocera does, checks every file opened
```

- `third_party/lola-retro/`: Lola Retro's `shaders/lola-retro` at the commit in `UPSTREAM`.
  To update: copy that folder again from a recent clone, then build + check.
- `mapping/systems.yml`: the sets and the mapping; `mapping/batocera-systems.tsv`: Batocera's list of
  systems (es_systems.yml), to check none is missing.
- The Batocera code read for this project: `batocera_launch/config/config.py` (`render_config`, user
  sets in `/userdata/shaders/configs`), `batocera_launch_libretro/emulator.py` (`.slangp` or `.glslp`
  by driver, `_slang_only_shader` which forces glcore), ES `ApiSystem::getShaderList`.

## Licences

This project (tools, mapping, generated presets): MIT, © 2026 neurocontrarian (`LICENSE`).
Lola Retro: MIT, © 2026 Zoki (`third_party/lola-retro/LICENSE`, installed with the shaders).
