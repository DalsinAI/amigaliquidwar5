#!/bin/sh
# Liquid War 5 for GFOS, host tests: the data tool's unit tests, then
# data/liquidwar.dat (plain and LZSS packed) read back by gfopenallegro.
#   tests/amiga/test_host.sh A4_DIR     (gfopenallegro/allegro4)
# Copyright (c) 2026 AmiCradle Team. GPL-2 or later, as Liquid War.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
A4=${1:?gfopenallegro/allegro4 directory}
T=${TMPDIR:-/tmp}/lw5-host-$$
mkdir -p "$T"
trap 'rm -rf "$T"' EXIT HUP INT TERM
python3 -m unittest discover -s "$ROOT/tests/amiga" -p 'test_lw5dat.py'
CC=${HOSTCC:-cc}
"$CC" -std=c99 -D_DEFAULT_SOURCE -w -O1 -I"$A4/include" -I"$A4/src" -I"$A4/tests" \
  "$A4"/src/a4_bitmap.c "$A4"/src/a4_blit.c "$A4"/src/a4_palette.c "$A4"/src/a4_fixed.c \
  "$A4"/src/a4_gfx.c "$A4"/src/a4_input.c "$A4"/src/a4_timer.c "$A4"/src/a4_file.c \
  "$A4"/src/a4_datafile.c "$A4"/src/a4_font.c "$A4"/src/a4_image.c "$A4"/src/a4_sound.c \
  "$A4"/src/a4_system.c "$A4"/src/a4_public.c "$A4"/src/a4_gui.c "$A4"/src/a4_os_host.c \
  "$A4"/tests/fake_acgame.c "$ROOT/tests/amiga/test_datafile.c" -o "$T/test_datafile"
MAPS=$(python3 -c "import sys; sys.path.insert(0,'$ROOT/amiga/tools'); import lw5dat; print(len(lw5dat.make_list('$ROOT/data/map/Makefile.in','MAP_NAMES')))")
TEX=$(python3 -c "import sys; sys.path.insert(0,'$ROOT/amiga/tools'); import lw5dat; print(len(lw5dat.make_list('$ROOT/data/texture/Makefile.in','TEXTURES')))")
MTX=$(python3 -c "import sys; sys.path.insert(0,'$ROOT/amiga/tools'); import lw5dat; m='$ROOT/data/maptex/Makefile.in'; print(len(lw5dat.make_list(m,'TEXTURES_BMP'))+len(lw5dat.make_list(m,'TEXTURES_PCX')))")
python3 "$ROOT/amiga/tools/lw5dat.py" "$ROOT/data" "$T/plain.dat"
"$T/test_datafile" "$T/plain.dat" "$MAPS" "$TEX" "$MTX"
python3 "$ROOT/amiga/tools/lw5dat.py" "$ROOT/data" "$T/packed.dat" --pack
"$T/test_datafile" "$T/packed.dat" "$MAPS" "$TEX" "$MTX"
echo "host tests: PASS"
