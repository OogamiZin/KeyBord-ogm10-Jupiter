# ogm10-Jupiter side guard v27 = v26 + rear guard keys that fill the bottom-plate USB notches
#  each USB notch (13 x 9.5 mm, no plate) gets two raised keys from the rear guard's under-lip, one at each side of the
#  USB-C receptacle body: they sit against the notch side walls (0.1mm) and lock the guard in X/Y.
import sys, json
import gen_guard as G, gen_half2 as H, gen_v26 as Z
from pcb_bottom_obstacles import PLATE_NOTCH_X

W = Z.W
NOTCH_DEPTH = 9.5           # bottom-plate USB notch depth from the rear edge
KEY_CLR_WALL = 0.10         # to the notch side wall / inner end
USB_BODY_HALF = 4.47        # USB-C receptacle shell half width (dips below the plate top, Z>=1.34)
KEY_CLR_USB = 0.40
KEY_TOP = G.PLATE_T - 0.1   # 1.5: stays under the plate top / receptacle body

_rear_v23 = W.rear_guard
def rear_guard():
    m = _rear_v23()
    y0, y1 = G.Y_REAR - NOTCH_DEPTH + KEY_CLR_WALL, G.Y_REAR - 0.05
    for a, b in PLATE_NOTCH_X:
        xa, xb = W.bx(a), W.bx(b); xc = (xa + xb) / 2
        for k0, k1 in ((xa + KEY_CLR_WALL, xc - USB_BODY_HALF - KEY_CLR_USB), (xc + USB_BODY_HALF + KEY_CLR_USB, xb - KEY_CLR_WALL)):
            m = m + G.box(k0, y0, H.USB_Z0 - 0.05, k1, y1, KEY_TOP)
    return m
W.rear_guard = rear_guard

if __name__ == '__main__':
    print(json.dumps(Z.Q.P.export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
