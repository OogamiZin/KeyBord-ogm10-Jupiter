// Copyright 2026 OogamiZin
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#define VIAL_KEYBOARD_UID {0x36, 0xC9, 0x6B, 0xC8, 0xD0, 0xDA, 0xF4, 0x86}

// Unlock combo: hold both encoder push switches
#define VIAL_UNLOCK_COMBO_ROWS { 0, 0 }
#define VIAL_UNLOCK_COMBO_COLS { 0, 11 }

// W25Q128JVSIQ (16MB)
#define PICO_FLASH_SIZE_BYTES (16 * 1024 * 1024)

#define VIAL_TAP_DANCE_ENTRIES 4
#define VIAL_COMBO_ENTRIES 4
#define VIAL_KEY_OVERRIDE_ENTRIES 4
