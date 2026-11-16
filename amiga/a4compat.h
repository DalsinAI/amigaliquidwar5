/* Liquid War 5 for GFOS: Allegro 4 names gfopenallegro e74af28 does not
 * have yet. Each one is guarded, so this file goes away untouched once
 * gfopenallegro carries them (asked for on 16 Nov 2026).
 * Copyright (c) 2026 AmiCradle Team. GPL-2 or later, as Liquid War. */
#ifndef LW_AMIGA_A4COMPAT_H
#define LW_AMIGA_A4COMPAT_H
#include <allegro.h>

#ifndef KB_NORMAL
#define KB_NORMAL 1
#define KB_EXTENDED 2
#endif
#ifndef ASSERT
#define ASSERT(x) ((void) 0)
#endif
#ifndef COLORCONV_REDUCE_TO_256
#define COLORCONV_REDUCE_TO_256 0
#endif
#ifndef A4_HAS_SYSTEM_DRIVERS
typedef struct LW_AMIGA_DRIVER { int id; const char *name; const char *desc;
  const char *ascii_name; } LW_AMIGA_DRIVER;
extern LW_AMIGA_DRIVER *lw_amiga_timer_driver, *lw_amiga_keyboard_driver,
  *lw_amiga_mouse_driver, *lw_amiga_joystick_driver;
extern const char lw_amiga_allegro_id[];
#define timer_driver lw_amiga_timer_driver
#define keyboard_driver lw_amiga_keyboard_driver
#define mouse_driver lw_amiga_mouse_driver
#define joystick_driver lw_amiga_joystick_driver
#define allegro_id lw_amiga_allegro_id
#endif
#endif
