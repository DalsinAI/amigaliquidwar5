/* Liquid War 5 for GFOS: data/liquidwar.dat as built by amiga/tools/lw5dat.py,
 * read back through gfopenallegro's own datafile code (host build, fake
 * acgame.library), the way src/disk.c reads it on GFOS.
 *   test_datafile DAT MAPS TEXTURES MAPTEX
 * Copyright (c) 2026 AmiCradle Team. GPL-2 or later, as Liquid War. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <allegro.h>

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #c); } } while (0)

static int count(DATAFILE *d)
{
    int n = 0;
    while (d[n].type != DAT_END) n++;
    return n;
}

static DATAFILE *inner(const char *dat, const char *name, int *n)
{
    DATAFILE *df = load_datafile_object(dat, name);
    CHECK(df != NULL);
    if (!df) { *n = 0; return NULL; }
    CHECK(df->type == DAT_FILE);
    *n = count((DATAFILE *)df->dat);
    return df;
}

int main(int argc, char **argv)
{
    const char *dat;
    int maps, textures, maptex, n, i;
    DATAFILE *df, *d;

    if (argc < 5) return 2;
    dat = argv[1];
    maps = atoi(argv[2]); textures = atoi(argv[3]); maptex = atoi(argv[4]);
    CHECK(allegro_init() == 0);

    /* back_dat: df[0] the 640x480 picture, df[1] its palette (disk.c) */
    df = inner(dat, "back_dat", &n);
    if (df) {
        d = (DATAFILE *)df->dat;
        CHECK(n == 2);
        CHECK(d[0].type == DAT_BITMAP && d[1].type == DAT_PALETTE);
        CHECK(((BITMAP *)d[0].dat)->w == 640 && ((BITMAP *)d[0].dat)->h == 480);
        for (i = 0; i < 640 * 480; i++)
            if (((BITMAP *)d[0].dat)->line[i / 640][i % 640] >= 46) break;
        CHECK(i == 640 * 480);              /* liquidwarcol -s 0 46 */
        unload_datafile_object(df);
    }
    /* font_dat: two fonts, two cursors, the palette, the empty cursor */
    df = inner(dat, "font_dat", &n);
    if (df) {
        d = (DATAFILE *)df->dat;
        CHECK(n == 6);
        CHECK(d[0].type == DAT_FONT && d[1].type == DAT_FONT);
        CHECK(d[2].type == DAT_BITMAP && d[3].type == DAT_BITMAP && d[5].type == DAT_BITMAP);
        CHECK(d[4].type == DAT_PALETTE);
        CHECK(text_height((FONT *)d[0].dat) > 0);
        CHECK(text_height((FONT *)d[1].dat) > text_height((FONT *)d[0].dat));
        CHECK(text_length((FONT *)d[0].dat, "Liquid War") > 0);
        CHECK(((BITMAP *)d[2].dat)->w == 20 && ((BITMAP *)d[3].dat)->w == 40);
        unload_datafile_object(df);
    }
    /* map_dat: liquidwarmap's header, then RLE runs that cover w*h */
    df = inner(dat, "map_dat", &n);
    if (df) {
        d = (DATAFILE *)df->dat;
        CHECK(n == maps);
        for (i = 0; i < n; i++) {
            const unsigned char *p = (const unsigned char *)d[i].dat;
            long size = p[0] | p[1] << 8 | p[2] << 16 | (long)p[3] << 24, cover = 0, k;
            int w = p[4] | p[5] << 8, h = p[6] | p[7] << 8;
            CHECK(d[i].size == 8 + 16 + 32 + size);
            for (k = 0; k < size - 1; k++) {
                signed char r = (signed char)p[56 + k];
                cover += r < 0 ? -r : r;
            }
            CHECK(p[56 + size - 1] == 0);
            CHECK(cover == (long)w * h);
        }
        unload_datafile_object(df);
    }
    /* texture_dat and maptex_dat: header, 32 colours, 5 planes */
    {
        const char *names[2] = { "texture_dat", "maptex_dat" };
        int want[2], t;
        want[0] = textures; want[1] = maptex;
        for (t = 0; t < 2; t++) {
            df = inner(dat, names[t], &n);
            if (!df) continue;
            d = (DATAFILE *)df->dat;
            CHECK(n == want[t]);
            for (i = 0; i < n; i++) {
                const unsigned char *p = (const unsigned char *)d[i].dat;
                int w = p[0] | p[1] << 8, h = p[2] | p[3] << 8, c;
                CHECK(d[i].size == 4 + 16 + 32 * 3 + ((w * h + 7) / 8) * 5);
                for (c = 0; c < 32 * 3; c++) CHECK(p[20 + c] < 64);
            }
            unload_datafile_object(df);
        }
    }
    df = inner(dat, "sfx_dat", &n);
    if (df) { CHECK(n == 6); CHECK(((DATAFILE *)df->dat)[0].type == DAT_SAMPLE); unload_datafile_object(df); }
    df = inner(dat, "water_dat", &n);
    if (df) {
        d = (DATAFILE *)df->dat;
        CHECK(n == 16);
        for (i = 0; i < n; i++) CHECK(d[i].type == DAT_SAMPLE && ((SAMPLE *)d[i].dat)->len > 0);
        unload_datafile_object(df);
    }
    df = inner(dat, "music_dat", &n);
    if (df) {
        d = (DATAFILE *)df->dat;
        CHECK(n == 7);
        for (i = 0; i < n; i++) CHECK(d[i].type == DAT_MIDI && ((MIDI *)d[i].dat)->track[0].len > 0);
        unload_datafile_object(df);
    }
    printf("%s: %d checks, %d failed\n", dat, checks, fails);
    return fails ? 1 : 0;
}
