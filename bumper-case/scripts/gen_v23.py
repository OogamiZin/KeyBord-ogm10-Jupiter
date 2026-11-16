# ogm10-Jupiter side guard v23 = v22 + more PCB/bottom-plate wedges
#  front: 7 short wedges (2.6mm under the PCB) in the gaps between the Choc sockets / diodes
#  rear : the 62..129.5 run is one continuous wedge
import sys, json
import numpy as np, trimesh
import gen_guard as G, gen_half2 as H, gen_v22 as P

W = P.W
FRONT_SHORT = [(22.8, 25.6), (46.6, 50.4), (65.7, 67.8), (89.5, 93.0), (141.9, 145.4), (165.7, 167.8), (194.3, 198.1)]
SHORT_DEPTH = 2.6
W.REAR_WEDGES = [(48.3, 51.0), (62.0, 129.5), (132.8, 136.6), (162.7, 167.8), (181.7, 186.9), (200.8, 212.4)]

_front_v22 = W.front_guard
def front_guard():
    m = _front_v22()
    for a, b in FRONT_SHORT:
        m = m + W.wedge_xz(W.bx(a), W.bx(b), H.Y_F_IN - 0.3, G.Y_FRONT + SHORT_DEPTH, inner_at_y0=False)
    return m
W.front_guard = front_guard

if __name__ == '__main__':
    print(json.dumps(P.export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
