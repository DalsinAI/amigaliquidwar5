"""Host unit tests of amiga/tools/lw5dat.py (python3 -m unittest).
Copyright (c) 2026 AmiCradle Team. GPL-2 or later, as Liquid War."""
import os
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "amiga", "tools"))
import lw5dat  # noqa: E402
import lw5img  # noqa: E402


def lzss_unpack(data):
    N, F, TH = 4096, 18, 2
    ring = bytearray(N)
    r, out, i, flags = N - F, bytearray(), 0, 0
    while i < len(data):
        flags >>= 1
        if not flags & 256:
            if i >= len(data):
                break
            flags = data[i] | 0xFF00
            i += 1
        if flags & 1:
            if i >= len(data):
                break
            c = data[i]; i += 1
            out.append(c); ring[r] = c; r = (r + 1) & (N - 1)
        else:
            if i + 1 >= len(data):
                break
            a, b = data[i], data[i + 1]; i += 2
            a |= (b & 0xF0) << 4
            for k in range((b & 0x0F) + TH + 1):
                c = ring[(a + k) & (N - 1)]
                out.append(c); ring[r] = c; r = (r + 1) & (N - 1)
    return bytes(out)


def _w(path, data):
    with open(path, "wb") as f:
        f.write(data)


def pcx8(w, h, pixels, pal):
    head = bytearray(128)
    struct.pack_into("<BBBBHHHH", head, 0, 10, 5, 0, 8, 0, 0, w - 1, h - 1)
    head[65] = 1
    struct.pack_into("<H", head, 66, w)
    return bytes(head) + bytes(pixels) + b"\x0c" + b"".join(bytes(c) for c in pal)


class Lw5DatTest(unittest.TestCase):
    def test_lzss_round_trip(self):
        for data in (b"", b"a", b"abcabcabcabc" * 50, os.urandom(3000),
                     bytes(range(256)) * 40 + b"x" * 5000):
            self.assertEqual(lzss_unpack(lw5dat.lzss_pack(data)), data)

    def test_map_runs(self):
        # 3x2: dark, dark, light / light, light, dark
        pal = [(0, 0, 0)] * 256
        pal[1] = (255, 255, 255)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "tiny.pcx")
            _w(p, pcx8(3, 2, [0, 0, 1, 1, 1, 0], pal))
            _w(os.path.join(d, "tiny.txt"), b"Tiny map\nmore")
            name, data = lw5dat.liquidwarmap(p)
        self.assertEqual(name, "tiny")
        size, w, h = struct.unpack_from("<IHH", data, 0)
        self.assertEqual((w, h), (3, 2))
        self.assertEqual(data[8:12], b"tiny")
        self.assertEqual(data[24:32], b"Tiny map")
        runs = [b - 256 if b > 127 else b for b in data[56:56 + size]]
        self.assertEqual(runs, [2, -3, 1, 0])

    def test_texture_planes(self):
        pal = [(i * 4, i * 4, i * 4) for i in range(64)] + [(0, 0, 0)] * 192
        pix = [i % 3 for i in range(10)]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.gimp.pcx")
            _w(p, pcx8(10, 1, pix, pal))
            name, data = lw5dat.liquidwartex(p, 1)
        self.assertEqual(name, "t")
        self.assertEqual(struct.unpack_from("<HH", data, 0), (10, 1))
        self.assertEqual(len(data), 4 + 16 + 96 + 2 * 5)
        cols = [tuple(data[20 + i * 3:23 + i * 3]) for i in range(3)]
        self.assertEqual(sorted(cols), [(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        # decode the planes back and check pixels keep their colours
        planes = data[116:]
        got = []
        for k in range(10):
            g, b = divmod(k, 8)
            c = sum(((planes[g * 5 + p] >> b) & 1) << p for p in range(5))
            got.append(cols[c][0])
        self.assertEqual(got, pix)

    def test_font_grid(self):
        # two glyphs 2x1 and 1x1 in a grid of colour 255
        w, h = 6, 3
        g = [255] * (w * h)
        g[1 * w + 1] = 3; g[1 * w + 2] = 0; g[1 * w + 4] = 5
        im = lw5img.Image(w, h, bytes(g), [(0, 0, 0)] * 256)
        data, n = lw5dat.grab_font(im)
        self.assertEqual(n, 2)
        self.assertEqual(struct.unpack_from(">HHB", data, 0), (0, 1, 8))
        self.assertEqual(struct.unpack_from(">II", data, 5), (32, 33))
        self.assertEqual(data[13:19], struct.pack(">HH", 2, 1) + bytes([3, 0]))
        self.assertEqual(data[19:24], struct.pack(">HH", 1, 1) + bytes([5]))

    def test_datafile_sorted_and_named(self):
        body = lw5dat.datafile_body([lw5dat.Obj("ZED", "DATA", b"z"), lw5dat.Obj("ABC", "DATA", b"ab")])
        self.assertEqual(body[:8], b"ALL." + struct.pack(">I", 2))
        self.assertEqual(body[8:23], b"propNAME" + struct.pack(">I", 3) + b"ABC")
        self.assertEqual(body[23:27], b"DATA")
        self.assertEqual(struct.unpack_from(">II", body, 27), (2, 2))
        self.assertEqual(body[35:37], b"ab")


if __name__ == "__main__":
    unittest.main()
