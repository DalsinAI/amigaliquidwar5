/* Liquid War 5 for GFOS: see a4compat.h.
 * Copyright (c) 2026 AmiCradle Team. GPL-2 or later, as Liquid War. */
#include "a4compat.h"

#ifndef A4_HAS_DRAW_SCROLLABLE_FRAME
/* Allegro's internal list box frame (src/alleg2.c draws its own list and
 * text boxes with it): the frame, and when the list is longer than the
 * box, a scroll bar on the right with a checked thumb. */
void
_draw_scrollable_frame (DIALOG *d, int listsize, int offset, int height,
                        int fg_color, int bg)
{
  BITMAP *b = gui_get_screen ();
  int x2 = d->x + d->w - 1, y2 = d->y + d->h - 1;
  int edge = (d->flags & D_GOTFOCUS) ? fg_color : bg;

  rect (b, d->x, d->y, x2, y2, fg_color);
  if (listsize <= height)
    {
      rect (b, d->x + 1, d->y + 1, x2 - 1, y2 - 1, edge);
      return;
    }
  vline (b, x2 - 12, d->y + 1, y2 - 1, fg_color);
  rect (b, d->x + 1, d->y + 1, x2 - 13, y2 - 1, edge);
  rect (b, x2 - 11, d->y + 1, x2 - 1, y2 - 1, edge);
  {
    int xx = x2 - 10, yy = d->y + 2, bottom = y2 - 2;
    int thumb = ((d->h - 5) * height + listsize / 2) / listsize;
    int len, x, y;

    if (offset > 0)
      {
        len = ((d->h - 5) * offset + listsize / 2) / listsize;
        rectfill (b, xx, yy, xx + 8, yy + len, bg);
        yy += len;
      }
    len = (yy + thumb < bottom) ? thumb : bottom - yy;
    for (y = yy; y <= yy + len; y++)
      for (x = xx; x <= xx + 8; x++)
        putpixel (b, x, y, ((x + y) & 1) ? bg : fg_color);
    if (yy + len + 1 <= bottom)
      rectfill (b, xx, yy + len + 1, xx + 8, bottom, bg);
  }
}
#endif
