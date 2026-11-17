VIA_ENABLE = yes
VIAL_ENABLE = yes
ENCODER_MAP_ENABLE = yes
LTO_ENABLE = yes


# Override dynamic_keymap_reset
LDFLAGS += -Wl,-wrap=dynamic_keymap_reset

# Host OS detection (Mac -> layer 3, others -> layer 0)
OS_DETECTION_ENABLE = yes

# Dynamic Macro (Ctrl+Shift+@位置+M/L/P で REC1/PLY1/RSTP)
DYNAMIC_MACRO_ENABLE = yes
