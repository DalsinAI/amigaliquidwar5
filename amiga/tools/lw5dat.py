#!/usr/bin/env python3
"""Build Liquid War 5's data/liquidwar.dat without Allegro's dat tool.

Upstream builds the datafile with Allegro 4's `dat` and three helpers
(utils/liquidwarcol.c, liquidwarmap.c, liquidwartex.c), all linked with a
host Allegro. GFOS builds have no host Allegro, so this does the same steps
with the Python standard library and writes an Allegro 4 datafile that
gfopenallegro's load_datafile_object() reads:

  back.dat     the menu background (palette cut to colours 0-45) + palette
  font.dat     two colour fonts grabbed from grids, two cursors, palette, void
  map.dat      every map as liquidwarmap's run-length format ("RAW ")
  maptex.dat   each map's own texture, liquidwartex's 5-plane format
  texture.dat  the plain textures, same format
  sfx.dat, water.dat   WAV files as samples
  music.dat    MIDI files

Objects in each inner datafile are sorted by name, as `dat` keeps them
(src/disk.c reads them by position). The colour picks liquidwarcol makes at
random are made here with a fixed seed per file, so builds are repeatable.

  lw5dat.py DATA_DIR OUT_FILE [--pack]

Copyright (c) 2026 AmiCradle Team. GPL-2 or later, as Liquid War.
"""
import os
import random
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lw5img  # noqa: E402


def dat_id(s):
    return struct.unpack(">I", s.encode("ascii"))[0]


DAT_MAGIC = dat_id("ALL.")
F_NOPACK_MAGIC = 0x736C682E
F_PACK_MAGIC = 0x736C6821


def read_bytes(path, n=-1):
    with open(path, "rb") as f:
        return f.read(n)


def mw(v):
    return struct.pack(">H", v & 0xFFFF)


def ml(v):
    return struct.pack(">I", v & 0xFFFFFFFF)


class Obj:
    def __init__(self, name, type_, data):
        self.name, self.type, self.data = name, type_, data


def datafile_body(objs):
    """'ALL.', the count, then each object's NAME property and chunk."""
    out = [ml(DAT_MAGIC), ml(len(objs))]
    for o in sorted(objs, key=lambda o: o.name.upper()):
        name = o.name.encode("ascii")
        out += [ml(dat_id("prop")), ml(dat_id("NAME")), ml(len(name)), name]
        out += [ml(dat_id(o.type)), ml(len(o.data)), ml(len(o.data)), o.data]
    return b"".join(out)


def obj_name(filename):
    return re.sub(r"[^A-Za-z0-9]", "_", os.path.basename(filename)).upper()


# ---- objects -------------------------------------------------------------

def to6(c):
    return c >> 2


def bitmap_obj(im):
    return mw(8) + mw(im.w) + mw(im.h) + bytes(im.pixels)


def palette_obj(pal6):
    # 6-bit entries stored as 8-bit, as Allegro writes them
    return b"".join(bytes(((c << 2) | (c >> 4)) for c in rgb) for rgb in pal6)


def image_pal6(im):
    return [tuple(to6(c) for c in rgb) for rgb in im.palette]


def grab_font(im):
    """Glyph boxes in a grid of the colour at (0,0), read left to right and
    top to bottom from ' ' on, as Allegro's font grabber does."""
    w, h, px = im.w, im.h, im.pixels
    d = px[0]

    def p(x, y):
        return px[y * w + x] if 0 <= x < w and 0 <= y < h else d

    glyphs = []
    x = y = 0
    while y < h:
        if p(x, y) == d and p(x + 1, y) == d and p(x, y + 1) == d and p(x + 1, y + 1) != d:
            gw = 0
            while p(x + 1 + gw, y + 1) != d:
                gw += 1
            gh = 0
            while p(x + 1, y + 1 + gh) != d:
                gh += 1
            rows = bytes(px[(y + 1 + j) * w + x + 1 + i] for j in range(gh) for i in range(gw))
            glyphs.append((gw, gh, rows))
            x += gw + 1
        else:
            x += 1
        if x >= w:
            x = 0
            y += 1
    if not glyphs:
        raise ValueError("no glyphs in font bitmap")
    mono = all(c in (0, 255) for _, _, r in glyphs for c in r)
    out = [mw(0), mw(1), bytes([1 if mono else 8]), ml(32), ml(32 + len(glyphs) - 1)]
    for gw, gh, rows in glyphs:
        out += [mw(gw), mw(gh)]
        if mono:
            for j in range(gh):
                line = bytearray((gw + 7) // 8)
                for i in range(gw):
                    if rows[j * gw + i]:
                        line[i >> 3] |= 0x80 >> (i & 7)
                out.append(bytes(line))
        else:
            out.append(rows)
    return b"".join(out), len(glyphs)


def sample_obj(path):
    data = read_bytes(path)
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("%s: not a WAV" % path)
    pos, fmt = 12, None
    while pos + 8 <= len(data):
        cid, clen = data[pos:pos + 4], struct.unpack_from("<I", data, pos + 4)[0]
        body = data[pos + 8:pos + 8 + clen]
        if cid == b"fmt ":
            fmt = struct.unpack_from("<HHIIHH", body, 0)
        elif cid == b"data" and fmt:
            tag, ch, freq, _br, _ba, bits = fmt
            if tag != 1 or bits not in (8, 16) or ch not in (1, 2):
                raise ValueError("%s: PCM 8/16-bit only" % path)
            frames = len(body) // ((bits // 8) * ch)
            if bits == 8:
                pcm = body[:frames * ch]
            else:
                n = frames * ch
                vals = struct.unpack_from("<%dh" % n, body, 0)
                pcm = struct.pack("<%dH" % n, *[(v + 0x8000) & 0xFFFF for v in vals])
            return mw(-bits if ch == 2 else bits) + mw(freq) + ml(frames) + pcm
        pos += 8 + clen + (clen & 1)
    raise ValueError("%s: no PCM data" % path)


def midi_obj(path):
    data = read_bytes(path)
    if data[:4] != b"MThd":
        raise ValueError("%s: not MIDI" % path)
    hlen = struct.unpack_from(">I", data, 4)[0]
    _fmt, ntr, div = struct.unpack_from(">HHH", data, 8)
    pos, tracks = 8 + hlen, []
    while pos + 8 <= len(data) and len(tracks) < ntr:
        cid, clen = data[pos:pos + 4], struct.unpack_from(">I", data, pos + 4)[0]
        if cid == b"MTrk":
            tracks.append(data[pos + 8:pos + 8 + clen])
        pos += 8 + clen
    out = [mw(div)]
    for i in range(32):
        t = tracks[i] if i < len(tracks) else b""
        out += [ml(len(t)), t]
    return b"".join(out)


# ---- liquidwarcol, liquidwarmap, liquidwartex ------------------------------

def pixel_colours6(im):
    """Each pixel's 6-bit colour (a truecolor image is cut to 6 bits, as
    Allegro does when it loads one into 8-bit colour)."""
    if im.rgb is not None:
        return [tuple(to6(c) for c in rgb) for rgb in im.rgb]
    pal = image_pal6(im)
    return [pal[i] for i in im.pixels]


def bestfit(pal, first, n, rgb):
    best, bi = None, first
    for i in range(first, first + n):
        r, g, b = pal[i]
        dd = 30 * (r - rgb[0]) ** 2 + 59 * (g - rgb[1]) ** 2 + 11 * (b - rgb[2]) ** 2
        if best is None or dd < best:
            best, bi = dd, i
            if dd == 0:
                break
    return bi


def liquidwarcol(im, first, count, seed):
    """utils/liquidwarcol.c: keep `count` colours sampled from the picture
    at colours first.. first+count-1; 0..first-1 black, the rest white."""
    cols = pixel_colours6(im)
    distinct = []
    seen = set()
    for c in cols:
        if c not in seen:
            seen.add(c)
            distinct.append(c)
            if len(distinct) >= count:
                break
    n = len(distinct)
    rnd = random.Random(seed)
    pal = [cols[rnd.randrange(len(cols))]] * 256
    have = set([pal[0]])
    i, retries = 1, 0
    while i < n:
        c = cols[rnd.randrange(len(cols))]
        if c not in have or retries > 1000:
            pal[first + i] = c
            have.add(c)
            i += 1
            retries = 0
        else:
            retries += 1
    pal = list(pal)
    for k in range(first):
        pal[k] = (0, 0, 0)
    for k in range(first + n, 256):
        pal[k] = (63, 63, 63)
    cache = {}
    out = bytearray(len(cols))
    for k, c in enumerate(cols):
        idx = cache.get(c)
        if idx is None:
            idx = cache[c] = bestfit(pal, first, n, c)
        out[k] = idx
    return lw5img.Image(im.w, im.h, bytes(out), [tuple(c << 2 for c in p) for p in pal]), pal


def name_field(s, size):
    b = s.encode("latin-1")[:size]
    return b + bytes(size - len(b))


def liquidwarmap(path):
    """utils/liquidwarmap.c: dark pixels (6r+3g+b <= 315 in 6-bit colour) are
    wall; runs of wall (+n) and of floor (-n), n <= 127, then 0."""
    im = lw5img.read_image(path)
    cols = pixel_colours6(im)
    dark = bytes(1 if 6 * r + 3 * g + b <= 315 else 0 for r, g, b in cols)
    buf = bytearray()
    pos, wh = 0, len(dark)
    while pos < wh:
        wall = dark[pos]
        n = 0
        while pos < wh and dark[pos] == wall and n < 127:
            n += 1
            pos += 1
        buf.append(n if wall else (256 - n) & 0xFF)
    buf.append(0)
    base = os.path.basename(path)
    system = base.split(".")[0]
    txt = os.path.join(os.path.dirname(path), system + ".txt")
    if os.path.exists(txt):
        readable = read_bytes(txt, 32).decode("latin-1")
        readable = readable.split("\n")[0].split("\r")[0]
    else:
        readable = system
    head = struct.pack("<IHH", len(buf), im.w, im.h)
    return system, head + name_field(system, 16) + name_field(readable, 32) + bytes(buf)


def liquidwartex(path, seed, first=32, count=32):
    """liquidwarcol -s 32 32 then utils/liquidwartex.c: the 32 colours, then
    the picture as 5 bit planes, 8 pixels to a group of 5 bytes."""
    im, pal = liquidwarcol(lw5img.read_image(path), first, count, seed)
    system = os.path.basename(path).split(".")[0]
    out = bytearray(struct.pack("<HH", im.w, im.h) + name_field(system, 16))
    for i in range(count):
        out += bytes(pal[first + i])
    octet = [0] * 5
    pos8 = 0
    last = im.w * im.h - 1
    for k, v in enumerate(im.pixels):
        c = v - first
        bit = 1 << pos8
        for p in range(5):
            if c & (1 << p):
                octet[p] |= bit
        if pos8 == 7 or k == last:
            out += bytes(octet)
            octet = [0] * 5
            pos8 = 0
        else:
            pos8 += 1
    return system, bytes(out)


# ---- the makefile lists ---------------------------------------------------

def make_list(makefile, var):
    text = read_bytes(makefile).decode("latin-1").replace("\\\n", " ")
    m = re.search(r"^%s\s*=(.*)$" % var, text, re.M)
    if not m:
        raise ValueError("%s: no %s" % (makefile, var))
    return m.group(1).split()


def seed_of(name):
    return sum(ord(c) * (i + 1) for i, c in enumerate(name))


def build(data_dir):
    j = lambda *p: os.path.join(data_dir, *p)  # noqa: E731
    files = []

    # back: lw5back.pcx, colours cut to 0..45 (liquidwarcol -s 0 46)
    im, pal = liquidwarcol(lw5img.read_image(j("back", "lw5back.pcx")), 0, 46, seed_of("lw5back"))
    files.append(Obj("BACK_DAT", "FILE", datafile_body([
        Obj("LW5BACK_CONVERTED_PCX", "BMP ", bitmap_obj(im)),
        Obj("PALETTE_PCX", "PAL ", palette_obj(pal)),
    ])))

    f = j("font")
    small = lw5img.read_image(os.path.join(f, "degrad10.pcx"))
    objs = [
        Obj("DEGRAD10_PCX", "FONT", grab_font(small)[0]),
        Obj("DEGRAD20_PCX", "FONT", grab_font(lw5img.read_image(os.path.join(f, "degrad20.pcx")))[0]),
        Obj("MOUSE20_PCX", "BMP ", bitmap_obj(lw5img.read_image(os.path.join(f, "mouse20.pcx")))),
        Obj("MOUSE40_PCX", "BMP ", bitmap_obj(lw5img.read_image(os.path.join(f, "mouse40.pcx")))),
        Obj("PALETTE_PCX", "PAL ", palette_obj(image_pal6(small))),
        Obj("VOID1_PCX", "BMP ", bitmap_obj(lw5img.read_image(os.path.join(f, "void1.pcx")))),
    ]
    files.append(Obj("FONT_DAT", "FILE", datafile_body(objs)))

    objs = []
    for n in make_list(j("map", "Makefile.in"), "MAP_NAMES"):
        src = j("map", n + ".pcx")
        if not os.path.exists(src):
            src = j("map", n + ".bmp")
        _s, data = liquidwarmap(src)
        objs.append(Obj(obj_name(n + ".map"), "RAW ", data))
    files.append(Obj("MAP_DAT", "FILE", datafile_body(objs)))

    objs = []
    mk = j("maptex", "Makefile.in")
    for n in make_list(mk, "TEXTURES_BMP"):
        objs.append(Obj(obj_name(n + ".tex"), "DATA", liquidwartex(j("maptex", n + ".orig.bmp"), seed_of(n))[1]))
    for n in make_list(mk, "TEXTURES_PCX"):
        objs.append(Obj(obj_name(n + ".tex"), "DATA", liquidwartex(j("maptex", n + ".orig.pcx"), seed_of(n))[1]))
    files.append(Obj("MAPTEX_DAT", "FILE", datafile_body(objs)))

    objs = []
    for n in make_list(j("texture", "Makefile.in"), "TEXTURES"):
        objs.append(Obj(obj_name(n + ".tex"), "DATA", liquidwartex(j("texture", n + ".gimp.pcx"), seed_of(n))[1]))
    files.append(Obj("TEXTURE_DAT", "FILE", datafile_body(objs)))

    for d, var in (("sfx", "WAVS"), ("water", "WAVS")):
        objs = [Obj(obj_name(w), "SAMP", sample_obj(j(d, w))) for w in make_list(j(d, "Makefile.in"), var)]
        files.append(Obj(d.upper() + "_DAT", "FILE", datafile_body(objs)))

    objs = [Obj(obj_name(m), "MIDI", midi_obj(j("music", m))) for m in make_list(j("music", "Makefile.in"), "MIDI")]
    files.append(Obj("MUSIC_DAT", "FILE", datafile_body(objs)))

    return datafile_body(files)


def lzss_pack(data):
    """Allegro 4's LZSS (4096-byte ring starting at 4078 filled with 0,
    matches 3..18, flag bit 1 = literal, LSB first)."""
    N, F, TH = 4096, 18, 2
    out = bytearray()
    ring = bytearray(N)
    r = N - F
    heads = {}
    i, n = 0, len(data)
    # positions in `data` for each 3-byte key; the ring holds the last N-F bytes
    while i < n:
        flags_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= n:
                break
            best_len, best_pos = 0, 0
            if i + 2 < n:
                key = data[i:i + 3]
                cands = heads.get(key)
                if cands:
                    for p in reversed(cands[-16:]):
                        if i - p > N - F:
                            break
                        L = 3
                        lim = min(F, n - i)
                        while L < lim and data[p + L] == data[i + L]:
                            L += 1
                        if L > best_len:
                            best_len, best_pos = L, p
                            if L == lim:
                                break
            if best_len > TH:
                rp = (r + (best_pos - i)) % N
                out.append(rp & 0xFF)
                out.append(((rp >> 4) & 0xF0) | (best_len - TH - 1))
                step = best_len
            else:
                flags |= 1 << bit
                out.append(data[i])
                step = 1
            for k in range(step):
                if i + 2 < n:
                    heads.setdefault(data[i:i + 3], []).append(i)
                ring[r] = data[i]
                r = (r + 1) % N
                i += 1
        out[flags_pos] = flags
    return bytes(out)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    body = build(argv[1])
    with open(argv[2], "wb") as f:
        if "--pack" in argv[3:]:
            f.write(ml(F_PACK_MAGIC) + lzss_pack(body))
        else:
            f.write(ml(F_NOPACK_MAGIC) + body)
    print("%s: %d bytes" % (argv[2], os.path.getsize(argv[2])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
