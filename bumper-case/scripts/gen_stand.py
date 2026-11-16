# ogm10-Jupiter vertical stand: the keyboard stands on the outer end of either foot (L or R) in a fitted pocket
# stand frame: u = keyboard Y (front->rear), v = keyboard Z (fin side -> keycap side), w = keyboard X (up)
import sys, json, math
import numpy as np, trimesh, manifold3d as M, shapely.geometry as sg, shapely.ops as so
import gen_guard as G, gen_v20 as R

POCKET_D = 10.0      # how deep the foot sits (foot is 10.5 long)
CLR = 0.4            # pocket clearance
RIM_T = 3.0          # rim wall thickness
LOW_RIM = 2.0        # rim height on the keycap side (keycaps / knob come down to X~2.7)
LOW_FROM_V = 6.0     # rim is low where v > this (keycap side)
FLOOR = 3.0
BASE_MARGIN = 4.0    # base plate around the rim
KEY_SIDE = 26.0      # base reaches this far on the keycap side (v) -> keeps the centre of gravity well inside
BASE_R = 6.0

def foot_outline():
    f = R.foot_left() ^ G.box(-1, -50, -50, POCKET_D, 150, 50)
    cs = f.transform([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]]).project()
    polys = [sg.Polygon(p) for p in cs.to_polygons()]
    u = so.unary_union([p for p in polys if p.area > 0])
    return sg.Polygon(u.exterior) if u.geom_type == 'Polygon' else sg.Polygon(max(u.geoms, key=lambda g: g.area).exterior)

def ext(poly, z0, z1):
    out = None
    for g in getattr(poly, 'geoms', [poly]):
        if g.area < 1e-6: continue
        t = trimesh.creation.extrude_polygon(g, z1 - z0); t.apply_translation([0, 0, z0]); m = G.to_man(t)
        out = m if out is None else out + m
    return out

def stand():
    o = foot_outline()
    pocket = o.buffer(CLR, join_style=1, resolution=16)
    ring = pocket.buffer(RIM_T, join_style=1, resolution=16).difference(pocket)
    hi = ring.intersection(sg.box(-500, -500, 500, LOW_FROM_V))
    lo = ring.difference(sg.box(-500, -500, 500, LOW_FROM_V))
    hull = pocket.buffer(RIM_T + BASE_MARGIN, join_style=1).convex_hull
    u0, v0, u1, v1 = hull.bounds
    base = hull.union(sg.box(u0 + BASE_R, v0, u1 - BASE_R, KEY_SIDE)).convex_hull
    base = base.buffer(-BASE_R, join_style=1).buffer(BASE_R, join_style=1, resolution=24)
    m = ext(base, -FLOOR, 0.0)
    m = m + ext(hi.buffer(0.3).buffer(-0.3), 0.0, POCKET_D) + ext(lo, 0.0, LOW_RIM)
    # 0.6mm chamfer on the base top edge for looks / no sharp edge
    return m, o

def export(out):
    m, o = stand()
    t = G.to_tm(m); t.apply_translation(-t.bounds[0])
    t.export(f'{out}/ogm10-Jupiter-stand.stl')
    return {'stand': dict(size=np.round(t.extents, 2).tolist(), watertight=bool(t.is_watertight), bodies=int(t.body_count))}

if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
