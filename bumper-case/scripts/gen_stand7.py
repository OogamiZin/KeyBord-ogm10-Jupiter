# ogm10-Jupiter vertical stand v7 - round puck (diameter smaller than the keyboard depth), the foot end plugs into it
# frame: u = keyboard Y (front->rear), v = keyboard Z (fin side -> keycap side), w = up
import sys, json, math
import numpy as np, trimesh, shapely.geometry as sg, shapely.ops as so
import gen_guard as G, gen_stand as S, gen_v20 as R

DIA = 64.0                 # keyboard depth is ~84mm
CENTER = (41.0, 4.0)       # under the (estimated) centre of gravity
DISC_T = 4.0               # base disc thickness (the foot end rests on its top)
CHAMFER = 1.0              # chamfer on the disc's top edge
CLR, COLLAR_T = 0.4, 3.0
KEY_H = 6.0                # locating key height (fits into the foot's fin opening)
KEY_CLR = 0.5              # locating key clearance
H_COLLAR, H_LOW, LOW_FROM_V = 8.0, 2.0, 6.0     # collar heights above the disc top (= foot end)     # collar above the disc; low on the keycap side (keycaps/knob)

def stand():
    o = S.foot_outline()
    pocket = o.buffer(CLR, join_style=1, resolution=24)
    disc = sg.Point(CENTER).buffer(DIA/2, resolution=128)
    collar = pocket.buffer(COLLAR_T, join_style=1, resolution=24).difference(pocket).intersection(disc)
    cut = sg.box(-500, -500, 500, LOW_FROM_V)
    # disc with a chamfered top edge (two stacked rings)
    m = S.ext(disc, 0, DISC_T - CHAMFER) + S.ext(sg.Point(CENTER).buffer(DIA/2 - CHAMFER*0.5, resolution=128), DISC_T - CHAMFER, DISC_T - CHAMFER*0.5) \
        + S.ext(sg.Point(CENTER).buffer(DIA/2 - CHAMFER, resolution=128), DISC_T - CHAMFER*0.5, DISC_T)
    m = m + S.ext(collar.intersection(cut), DISC_T - 0.01, DISC_T + H_COLLAR) + S.ext(collar.difference(cut), DISC_T - 0.01, DISC_T + H_LOW)
    # locating key: fills the foot's fin truss opening -> the foot cannot slide along the collar
    hole = R.opn(sg.Polygon(R.HOLE), R.R_HOLE)
    key = hole.buffer(-KEY_CLR, join_style=1, resolution=24).intersection(disc.buffer(-2.0))
    m = m + S.ext(key, DISC_T - 0.01, DISC_T + KEY_H)
    return m, o, disc, pocket

def export(out):
    m, o, disc, pocket = stand()
    t = G.to_tm(m); t.merge_vertices(digits_vertex=5); t.apply_translation(-t.bounds[0]); t.export(f'{out}/ogm10-Jupiter-stand.stl')
    return {'stand': dict(size=np.round(t.extents, 2).tolist(), watertight=bool(t.is_watertight), bodies=int(t.body_count))}

if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
