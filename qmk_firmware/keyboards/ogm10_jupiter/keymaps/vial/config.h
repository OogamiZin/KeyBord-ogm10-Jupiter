// Copyright 2026 OogamiZin
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#define VIAL_KEYBOARD_UID {0x36, 0xC9, 0x6B, 0xC8, 0xD0, 0xDA, 0xF4, 0x86}

// Unlock combo: hold Q and P together (physical positions [0,1] and [0,10])
#define VIAL_UNLOCK_COMBO_ROWS { 0, 0 }
#define VIAL_UNLOCK_COMBO_COLS { 1, 10 }

// W25Q128JVSIQ (16MB)
#define PICO_FLASH_SIZE_BYTES (16 * 1024 * 1024)
// Dynamic Macro のバッファサイズ（初期値 128 の10倍）
// マクロ1・2で共有。キーを押す・離すでそれぞれ1件消費する
#define DYNAMIC_MACRO_SIZE 1280

// スリープ復帰時に通信を再開するまでの待ち時間(ms)（macOS での復帰後の無反応対策）
#define USB_SUSPEND_WAKEUP_DELAY 200

#define VIAL_TAP_DANCE_ENTRIES 8
#define VIAL_COMBO_ENTRIES 8
#define VIAL_KEY_OVERRIDE_ENTRIES 4
