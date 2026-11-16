# ogm10-Jupiter side guard v16
#  * rear-guard spacer arm (v15) removed
#  * thick wedges that fill the bottom-plate <-> main-PCB gap (Z 1.62..4.55) on both guards,
#    placed only where the PCB bottom is free of parts (Choc sockets, diodes, caps, resistors, ICs, switch posts, spacers),
#    and on both sides of every USB-C port where there is room
#  * the thin v9 plate jaws on the rear guard are replaced by the wedges; feet = v14
import sys, json, math
import numpy as np, trimesh, shapely.geometry as sg
import gen_guard as G, gen_half2 as H, gen_v12 as V

V.REAR_JAW_X = []                       # thin jaws replaced by the wedges
WZ = (G.PLATE_T + 0.02, G.Z_PCB_BOT - 0.05)   # 1.62 .. 4.55
DEPTH = 5.5                             # how far the wedge reaches under the PCB (from the board edge)
CH = 0.8                                # lead-in chamfer on the inner end

# board-x ranges (mm, EasyEDA board coords) found free of bottom-side parts with 0.5mm margin (see pcb_bottom_obstacles.py)
FRONT_WEDGES = [(26.6, 30.9), (69.5, 73.7), (93.3, 97.5), (145.7, 149.9), (169.5, 178.5)]
REAR_WEDGES  = [(48.3, 51.0),                 # right of USB1 (left of USB1 is taken by C1/C2/F1)
                (62.0, 70.0), (86.0, 94.0), (110.0, 118.0), (132.8, 136.6),
                (162.7, 167.8),               # right of USB2 / left of USB3 (left of USB2 is taken by R5-R9)
                (181.7, 186.9),               # right of USB3 / left of USB4
                (200.8, 210.8)]               # right of USB4
bx = lambda x: G.X_END + (x - 7.496)          # board x -> K frame X

def wedge_xz(x0, x1, y0, y1, inner_at_y0):
    """wedge block with 45deg chamfers on the inner end (top and bottom) for an easy push-in"""
    zb, zt = WZ
    # profile in (Y,Z) then extrude along X
    if inner_at_y0:
        poly = sg.Polygon([(y0, zb+CH), (y0+CH, zb), (y1, zb), (y1, zt), (y0+CH, zt), (y0, zt-CH)])
    else:
        poly = sg.Polygon([(y0, zb), (y1-CH, zb), (y1, zb+CH), (y1, zt-CH), (y1-CH, zt), (y0, zt)])
    return H.prism_yz(poly, x0, x1)

def front_guard():
    m = V.front_guard()
    for a, b in FRONT_WEDGES:
        m = m + wedge_xz(bx(a), bx(b), H.Y_F_IN - 0.3, G.Y_FRONT + DEPTH, inner_at_y0=False)
    return m

def rear_guard():
    m = V.rear_guard()
    for a, b in REAR_WEDGES:
        m = m + wedge_xz(bx(a), bx(b), G.Y_REAR - DEPTH, H.Y_R_IN + 0.3, inner_at_y0=True)
    return m

def export(out):
    info = {}
    fg = G.to_tm(front_guard()); fg.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [1, 0, 0]))
    rg = G.to_tm(rear_guard()); rg.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/2, [1, 0, 0]))
    for name, t in (('guard-front', fg), ('guard-rear', rg)):
        t.apply_translation(-t.bounds[0]); part = np.round(t.extents, 2).tolist(); t = V.diag(t)
        t.export(f'{out}/ogm10-Jupiter-{name}.stl')
        info[name] = dict(part=part, bed=np.round(t.extents, 1).tolist(), watertight=bool(t.is_watertight), bodies=int(t.body_count))
    return info

if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
