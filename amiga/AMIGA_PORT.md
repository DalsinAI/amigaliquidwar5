# Liquid War 5 for GFOS

Liquid War 5.6.7 by Christian Mauduit (GPL-2 or later), built for
AmigaOS 3.2 / GFOS on a 68040, 68060 or 68080. No FPU is needed.

Each player steers a cursor, and their army of liquid flows towards it
along the shortest path through the maze. Where two armies touch, the
stronger side eats the other. Up to 6 teams can play, against each other
or against the computer, on more than 150 maps.

## What is in the drawer

- `LiquidWar`: the game.
- `data/liquidwar.dat`: the maps, textures, fonts, sounds and music.
- `custom/map`, `custom/texture`, `custom/music`: extra maps, textures and
  music. The game picks up any BMP or PCX map you add to `custom/map`.
- `Libs/allegro4.library` and `Libs/acgame.library`: Allegro 4 for GFOS
  (gfopenallegro) on ACGame. The game opens them from its own `Libs/`.
- `User/`: your settings (`liquidwar.cfg`), made the first time you play.
  Updates and `GFOpenUpTool REMOVE` leave it alone.

## Playing

The default keys are those of the original game, and you can change them
in the Controls menu. The mouse and joysticks can steer cursors too.

## How the port is made

- The code is upstream's, built as its UNIX port with 68040 soft float
  against gfopenallegro's Allegro 4 (`amiga/Makefile.amigaos`).
- Upstream builds `liquidwar.dat` with Allegro's `dat` tool and three
  helper programs. GFOS builds have no host Allegro, so
  `amiga/tools/lw5dat.py` does the same steps and writes an Allegro 4
  datafile, LZSS packed. The colours that upstream's `liquidwarcol` picks
  at random are picked here with a fixed seed, so every build is the same.
- The network game uses bsdsocket.library (Roadshow), so it needs a TCP/IP
  stack running. Local games do not.
- Sound and music are silent for now: gfopenallegro plays samples once
  ACGame has audio, and MIDI is not played yet.

Designed, tested and delivered by The AmiCradle Team.
