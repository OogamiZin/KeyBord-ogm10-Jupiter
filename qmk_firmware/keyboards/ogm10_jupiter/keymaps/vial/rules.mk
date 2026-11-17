VIA_ENABLE = yes
VIAL_ENABLE = yes
ENCODER_MAP_ENABLE = yes
LTO_ENABLE = yes


# Override dynamic_keymap_reset
LDFLAGS += -Wl,-wrap=dynamic_keymap_reset
# Override dynamic_keymap_macro_reset（マクロの初期設定を書き込む）
LDFLAGS += -Wl,-wrap=dynamic_keymap_macro_reset

# Host OS detection (Mac -> layer 3, others -> layer 0)
OS_DETECTION_ENABLE = yes

# Dynamic Macro (Ctrl+Shift+@位置+M/L/P で REC1/PLY1/RSTP)
DYNAMIC_MACRO_ENABLE = yes
