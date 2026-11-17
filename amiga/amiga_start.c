/* Liquid War 5 for GFOS: start-up bits.
 * Copyright (c) 2026 AmiCradle Team. GPL-2 or later, as Liquid War. */
#include <sys/stat.h>

unsigned long __stack = 512 * 1024;
static const char amiga_ver[] __attribute__((used)) =
  "$VER: LiquidWar 5.6.7 (16.11.2026)";

static void __attribute__((constructor)) amiga_user_dir (void)
{
  mkdir ("PROGDIR:User", 0755);
}
