#!/bin/sh
# Lola Retro for Batocera: install or remove the shader sets in /userdata/shaders.
# Run on the Batocera machine, from the unzipped folder (not from /userdata itself):
#   sh install.sh             install (or update)
#   sh install.sh --uninstall remove
set -e
DEST=/userdata/shaders
HERE=$(cd "$(dirname "$0")" && pwd)
PKG="$HERE/shaders"

[ -d "$PKG/lola-retro" ] || { echo "shaders/ not found next to install.sh"; exit 1; }
if [ "$(cd "$PKG" && pwd -P)" = "$(cd "$DEST" 2>/dev/null && pwd -P)" ]; then
    echo "Unzip the archive in its own folder (for example /userdata/lola-tmp), not in /userdata."
    exit 1
fi

# Only this package's folders and sets: other sets in configs/ are left alone.
remove() {
    rm -rf "$DEST/lola-retro" "$DEST/lola-retro-batocera"
    for set in "$PKG"/configs/*/; do
        rm -rf "$DEST/configs/$(basename "$set")"
    done
}

if [ "$1" = "--uninstall" ]; then
    remove
    echo "Lola Retro removed. If a system still uses it, pick another SHADER SET in the menu."
    exit 0
fi

remove
mkdir -p "$DEST/configs"
cp -r "$PKG/lola-retro" "$PKG/lola-retro-batocera" "$DEST/"
cp -r "$PKG"/configs/* "$DEST/configs/"
echo "Installed in $DEST:"
for set in "$PKG"/configs/*/; do echo "  $(basename "$set")"; done
echo "Choose one in Main menu > Game settings > Shader set (global, or per system)."
