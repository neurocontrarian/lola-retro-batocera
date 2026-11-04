#!/bin/sh
# Lola Retro for Batocera: install or remove the shader sets in /userdata/shaders.
# Run on the Batocera machine, from the folder this script is in:
#   sh install.sh             install (or update)
#   sh install.sh --uninstall remove
set -e
DEST=/userdata/shaders
HERE=$(cd "$(dirname "$0")" && pwd)

remove() {
    rm -rf "$DEST/lola-retro" "$DEST/lola-retro-batocera"
    for d in "$DEST"/configs/lola-retro*; do
        [ -d "$d" ] && rm -rf "$d"
    done
    return 0
}

if [ "$1" = "--uninstall" ]; then
    remove
    echo "Lola Retro removed. If a system still uses it, pick another SHADER SET in the menu."
    exit 0
fi

[ -d "$HERE/shaders/lola-retro" ] || { echo "shaders/ not found next to install.sh"; exit 1; }
remove
mkdir -p "$DEST/configs"
cp -r "$HERE/shaders/lola-retro" "$HERE/shaders/lola-retro-batocera" "$DEST/"
cp -r "$HERE"/shaders/configs/lola-retro* "$DEST/configs/"
echo "Installed in $DEST:"
ls -d "$DEST"/configs/lola-retro* | sed 's|.*/|  |'
echo "Choose one in Main menu > Game settings > Shader set (global, or per system)."
