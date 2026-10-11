#!/usr/bin/env bash
# Build the constrained SeedSigner firmware in Keith's ESP-IDF image.
#
#   firmware/build.sh [BOARD]        -> firmware/build/<BOARD>/
#
# Stock MicroPython (the pinned checkout inside seedsigner-micropython-builder,
# left unpatched) + this repo's out-of-tree board + crypto-only user modules.
# The workspace is mounted at the same absolute path inside the container, so
# every path below means the same thing on both sides.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(cd "$HERE/../.." && pwd)"
BUILDER="$WORKSPACE/seedsigner-micropython-builder"
MP="$BUILDER/deps/micropython/upstream"
BOARD="${1:-SEEDSIGNER_S3_DEVKIT}"
OUT="$HERE/build/$BOARD"
IMAGE="${IMAGE:-ghcr.io/kdmukai-bot/seedsigner-micropython-builder-base:idf-v5.5.5}"

# ESP-IDF's component manager rewrites MicroPython's tracked
# ports/esp32/lockfiles/dependencies.lock.esp32s3 on every build (Keith's image
# ships IDF 5.5.5; MicroPython 1.27's lockfile was recorded against an earlier
# 5.5). That dirties the shared checkout, and seedsigner-micropython-builder
# refuses to build on a dirty MicroPython tree. Put it back on the way out, the
# same restore-on-exit pattern Keith's own scripts use.
# ponytail: firmware built here reports "v1.27.0-dirty" for the same reason. A
# MicroPython checkout of our own, with our own lockfile, fixes both properly.
trap 'git -C "$MP" checkout -- ports/esp32/lockfiles/ 2>/dev/null || true' EXIT

mkdir -p "$OUT" "$HOME/.cache"
docker run --rm \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp/home \
    --tmpfs "/tmp/home:uid=$(id -u),gid=$(id -g)" \
    -v "$HOME/.cache:/tmp/home/.cache" \
    -v "$WORKSPACE:$WORKSPACE" \
    -w "$MP" \
    "$IMAGE" bash -lc "
        set -e
        export IDF_PATH=/opt/toolchains/esp-idf
        source \$IDF_PATH/export.sh >/dev/null
        make -C mpy-cross USER_C_MODULES= -j\$(nproc)
        cd ports/esp32
        idf.py -B '$OUT' \
            -D MICROPY_BOARD='$BOARD' \
            -D MICROPY_BOARD_DIR='$HERE/boards/$BOARD' \
            -D USER_C_MODULES='$HERE/crypto.cmake' \
            -D MICROPY_FROZEN_MANIFEST='$HERE/manifest.py' \
            -D EXTRA_COMPONENT_DIRS='$BUILDER/deps/esp-secp256k1;$BUILDER/deps/esp-hashlib-ext' \
            build
    "

echo "built: $OUT"
ls -la "$OUT"/micropython.bin "$OUT"/flash_args
