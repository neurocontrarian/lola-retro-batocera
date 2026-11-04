# Lola Retro pour Batocera

Le shader CRT [Lola Retro](https://github.com/zoran123456/lola-retro) (MIT) sous forme de **shader sets
Batocera** : après installation, ils apparaissent dans le menu **Réglages des jeux → Shader set**, et chaque
système reçoit automatiquement le bon téléviseur ou moniteur (NES sur TV composite, Amiga sur 1084S, arcade
sur moniteur 15 kHz, DOS sur moniteur VGA, Game Boy sur grille LCD…).

## Les six sets

| Set (menu) | Chaîne Lola Retro | Écran | Pour qui |
|---|---|---|---|
| `LOLA-RETRO` | lite | bombé | **recommandé** : même image que la chaîne complète pour une fraction du coût GPU |
| `LOLA-RETRO-FLAT` | lite | plat | idem, écran plat |
| `LOLA-RETRO-FULL` | complète | bombé | GPU haut de gamme ; ajoute le tour du tube, démarrage des jeux plus long |
| `LOLA-RETRO-FULL-FLAT` | complète | plat | idem |
| `LOLA-RETRO-SUPERLITE` | super lite | bombé | GPU modestes |
| `LOLA-RETRO-SUPERLITE-FLAT` | super lite | plat | idem |

Repères mesurés (projet StrikeHD, même shader) : RTX 3090 en 4K, lite = 4,5 ms par image et ~60 W, la
chaîne complète = 12,4 ms et ~310 W pour aucune différence visible. Intel UHD 630 en 1080p : lite = 72 ms,
trop lent ; les iGPU récents (Intel Core Ultra, Radeon 780M) tiennent la lite. Raspberry Pi 4 et consoles
portables ARM : trop lents même en super lite (mesuré par l'auteur de Lola Retro, issue #13).

## Installation

Sur la machine Batocera, depuis le dossier décompressé du zip :

```sh
sh install.sh              # installe ou met à jour
sh install.sh --uninstall  # retire tout
```

Ou à la main : copier le contenu du dossier `shaders/` du zip dans le partage réseau `\\BATOCERA\share\shaders`
(c'est `/userdata/shaders`). Rien n'est modifié dans le système : Batocera lit les sets utilisateur dans
`/userdata/shaders/configs/`.

Puis : **Menu → Réglages des jeux → Shader set → LOLA-RETRO** (pour tout), ou le même réglage dans les
options avancées d'un système.

## Ce qui est installé

```
/userdata/shaders/
  lola-retro/                  presets RetroArch de Lola Retro, intacts (aussi utilisables depuis le menu RetroArch)
  lola-retro-batocera/         petits presets : #reference vers ceux de Lola Retro + les réglages ci-dessous
  configs/lola-retro*/rendering-defaults.yml   les six sets : quel preset pour quel système
```

Réglages ajoutés par-dessus les presets d'origine (ceux retenus pour StrikeHD, section `params` de `mapping/systems.yml`) :

| Paramètre | Valeur | Effet |
|---|---|---|
| Mask on screen pixels (`LR_MASK_PX`) | 1 | masque aligné sur les pixels de l'écran : pas de moiré sous la 4K |
| Scanline smoothing (`LR_SMOOTH`) | 1 | moins de moiré sur les lignes |
| Dither blend auto (`LR_DBLEND_AUTO`) | 1 | en RGB et S-Video, le tramage d'un pixel se fond comme en composite (eaux, ombres) |
| Damper wires (`LR_DAMPER`) | 0 | pas de fils de Trinitron en travers de l'image |

PlayStation : timing console 4 et « Frames over 300 lines » 1, car les cœurs par défaut envoient l'image 1×.
En résolution interne 2×, remettre « Frames over 300 lines » à 0 (Menu rapide → Shaders → Paramètres).

Tous les paramètres restent réglables en jeu dans RetroArch (Hotkey + B → Menu rapide → Shaders).

## Ce que ça couvre, et ce que ça ne couvre pas

- **Tous les systèmes lancés par un cœur RetroArch** (la grande majorité des systèmes rétro de Batocera).
  La correspondance système → preset est dans `mapping/systems.yml` (tous les systèmes de Batocera y sont listés).
- **Les émulateurs autonomes** (PCSX2, Dolphin, Mupen64Plus, DuckStation, PPSSPP, Cemu, MAME autonome…)
  n'utilisent pas les shader sets de Batocera : chacun a ses propres filtres. Les systèmes concernés sont
  quand même listés : en passant un système sur son cœur RetroArch (option *Émulateur* du système, par ex.
  N64 → mupen64plus-next, PS2 → lrps2, GameCube → dolphin libretro), il reçoit le bon preset.
- **Portables à écran LCD** : la grille LCD d'origine de Batocera (`handheld/lcd-grid-v2`), puisqu'elles
  n'avaient pas de tube. **Vectrex, Virtual Boy, Game & Watch, DS, 3DS, PSP et systèmes HD** : pas de shader.

## Pilote vidéo

Les presets n'existent qu'en slang : Batocera le détecte et lance RetroArch en **glcore** (OpenGL 3.1+)
sur NVIDIA, AMD et Intel, sauf si un pilote est forcé dans les options. En **Vulkan** (option *Pilote
graphique*), ça marche aussi. Le vieux pilote `gl` ne lit pas le slang : avec lui, pas de shader (cas des
cœurs YabaSanshiro, PPSSPP et Boom3, que Batocera met sur `gl`).

NVIDIA sous X11 : si une bande de déchirement fixe apparaît en plein écran, c'est le compositeur picom de
Batocera (issue batocera-linux/batocera.linux#17272), pas le shader.

## Développement

```sh
python3 tools/build.py   # dist/shaders/ et dist/lola-retro-batocera-<version>.zip
python3 tools/check.py   # vérifie que chaque système de Batocera est listé, résout chaque système de chaque set comme Batocera, vérifie chaque fichier ouvert
```

- `third_party/lola-retro/` : `shaders/lola-retro` de Lola Retro au commit indiqué dans `UPSTREAM`.
  Mise à jour : recopier ce dossier depuis un clone récent, puis build + check.
- `mapping/systems.yml` : la correspondance ; `mapping/batocera-systems.tsv` : la liste des systèmes de
  Batocera (es_systems.yml) pour vérifier qu'aucun n'est oublié.
- Le code de Batocera relu pour ce projet : `batocera_launch/config/config.py` (`render_config`, sets
  utilisateur dans `/userdata/shaders/configs`), `batocera_launch_libretro/emulator.py` (`.slangp` ou
  `.glslp` selon le pilote, `_slang_only_shader` qui force glcore), ES `ApiSystem::getShaderList`.

## Licences

Lola Retro : MIT, © 2026 Zoki (`third_party/lola-retro/LICENSE`, installé avec les shaders).
