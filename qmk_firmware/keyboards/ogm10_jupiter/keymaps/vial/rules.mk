VIA_ENABLE = yes
VIAL_ENABLE = yes
ENCODER_MAP_ENABLE = yes
LTO_ENABLE = yes


# Override dynamic_keymap_reset
LDFLAGS += -Wl,-wrap=dynamic_keymap_reset