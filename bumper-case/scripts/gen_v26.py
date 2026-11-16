# ogm10-Jupiter side guard v26 = v25 feet + front guard:
#  * PCB lip (1mm under the PCB front edge) made full height down to the bottom plate (Z 1.62..4.55), except the middle notch (U3/R15)
#  * short wedges (2.6mm deep) also under the shallow half of the Choc sockets (socket modelled as its two body halves,
#    not as one bounding box): shallow half x = c-9.6..c-2.5 reaches y = c+6.5, deep half x = c-2.5..c+4.6 reaches y = c+8.2
import sys, json
import shapely.geometry as sg
import gen_guard as G, gen_half2 as H, gen_v25 as P25, gen_v12 as V12

Q = P25            # gen_v25 = gen_v24 module copy (front_guard patched with the v23 short wedges)
W = Q.W
FRONT_SHORT = [(22.7, 25.6), (32.9, 38.5), (46.5, 57.5), (65.5, 67.8), (75.1, 81.3), (89.3, 105.1), (127.6, 133.7),
               (141.7, 157.5), (165.5, 167.8), (175.1, 186.1), (194.1, 205.2), (220.6, 224.2)]
SHORT_DEPTH = 2.6
LIP_IN = 1.0

def build_front():
    m = V12.front_guard()
    for a, b in W.FRONT_WEDGES:                                     # v16 deep wedges (5.5mm)
        m = m + W.wedge_xz(W.bx(a), W.bx(b), H.Y_F_IN - 0.3, G.Y_FRONT + W.DEPTH, inner_at_y0=False)
    for a, b in FRONT_SHORT:                                        # short wedges (2.6mm)
        m = m + W.wedge_xz(W.bx(a), W.bx(b), H.Y_F_IN - 0.3, G.Y_FRONT + SHORT_DEPTH, inner_at_y0=False)
    lip = H.prism_yz(H.front_pcb_lip().union(sg.box(H.Y_F_IN - 0.3, W.WZ[0], G.Y_FRONT + LIP_IN, H.PCB_LIP[1])), V12.X0, V12.X1)
    lip = lip - G.box(V12.NOTCH[0], -5, -5, V12.NOTCH[1], 20, 20)
    return m + lip
W.front_guard = build_front

if __name__ == '__main__':
    print(json.dumps(Q.P.export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
