/* Liquid War 5 for GFOS: see a4compat.h.
 * Copyright (c) 2026 AmiCradle Team. GPL-2 or later, as Liquid War. */
#include "a4compat.h"
#ifndef A4_HAS_SYSTEM_DRIVERS
static LW_AMIGA_DRIVER t = { 0, "ACGame timer", "ACGame timer", "ACGame timer" };
static LW_AMIGA_DRIVER k = { 0, "ACGame keyboard", "ACGame keyboard", "ACGame keyboard" };
static LW_AMIGA_DRIVER m = { 0, "ACGame mouse", "ACGame mouse", "ACGame mouse" };
static LW_AMIGA_DRIVER j = { 0, "ACGame joystick", "ACGame joystick", "ACGame joystick" };
LW_AMIGA_DRIVER *lw_amiga_timer_driver = &t, *lw_amiga_keyboard_driver = &k,
  *lw_amiga_mouse_driver = &m, *lw_amiga_joystick_driver = &j;
const char lw_amiga_allegro_id[] = "Allegro 4 (gfopenallegro) on acgame.library";
#endif
