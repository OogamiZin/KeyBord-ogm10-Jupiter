# ogm10-Jupiter vertical stand v23 = v22 with every raised part kept inside the disc's flat top
#   v22 clipped the collar / rails / key at the disc outline (on the chamfer), leaving ragged ends.
#   Now: all raised parts are clipped EDGE mm inside the outer edge and their ends rounded (R_END) -> clean, smooth ends.
import sys, json, types
import numpy as np, shapely.geometry as sg
import gen_v30, gen_v21 as N, gen_stand as S
S.R = types.SimpleNamespace(foot_left=N.foot_left)
import gen_stand16 as S16, gen_stand7 as S7, gen_guard as G, gen_v20 as R
S7.DIA = 68.0
EDGE = 2.0                  # raised parts stop this far inside the disc edge (chamfer is 1.0)
R_END = 1.0                 # rounding of the raised parts' ends / corners

def rnd(p, r=R_END):
    q = p.buffer(-r, join_style=1, resolution=24).buffer(r, join_style=1, resolution=24)
    return q

def stand():
    o = S.foot_outline()
    pocket = o.buffer(S7.CLR, join_style=1, resolution=24)
    disc = sg.Point(S7.CENTER).buffer(S7.DIA/2, resolution=192)
    inner = disc.buffer(-EDGE, resolution=192)
    T, C = S7.DISC_T, S7.CHAMFER
    m = S.ext(disc, 0, T - C) + S.ext(sg.Point(S7.CENTER).buffer(S7.DIA/2 - C*0.5, resolution=192), T - C, T - C*0.5) \
        + S.ext(sg.Point(S7.CENTER).buffer(S7.DIA/2 - C, resolution=192), T - C*0.5, T)
    # fin-side collar (keycap side has none since v22)
    collar = pocket.buffer(S7.COLLAR_T, join_style=1, resolution=24).difference(pocket)
    collar = rnd(collar.intersection(sg.box(-500, -500, 500, S7.LOW_FROM_V)).intersection(inner))
    m = m + S.ext(collar, T - 0.01, T + S7.H_COLLAR)
    # locating key in the fin opening
    hole = R.opn(sg.Polygon(R.HOLE), R.R_HOLE)
    key = rnd(hole.buffer(-S7.KEY_CLR, join_style=1, resolution=24).intersection(inner))
    m = m + S.ext(key, T - 0.01, T + S7.KEY_H)
    # keycap-side rail (rests on the top plate), stepped heights at the encoder / Shift
    rail = sg.box(-500, S16.STEP_V0, 500, S16.STEP_V0 + S16.STEP_T).intersection(inner).difference(pocket)
    enc = sg.box(S16.ENC_U[0], -500, S16.ENC_U[1], 500); sh = sg.box(S16.SHIFT_U[0], -500, S16.SHIFT_U[1], 500)
    base = rnd(rail)
    m = m + S.ext(base, T - 0.01, T + S16.STEP_H_ENC)                                  # lowest of the three heights everywhere
    m = m + S.ext(rnd(rail.difference(enc).difference(sh)), T + S16.STEP_H_ENC - 0.01, T + S16.STEP_H)
    m = m + S.ext(rnd(rail.intersection(sh)), T + S16.STEP_H_ENC - 0.01, T + S16.STEP_H_SHIFT)
    return m, o, disc, pocket

def export(out):
    m, o, disc, pocket = stand()
    t = G.to_tm(m); t.merge_vertices(digits_vertex=5); t.apply_translation(-t.bounds[0]); t.export(f'{out}/ogm10-Jupiter-stand.stl')
    return {'stand': dict(size=np.round(t.extents, 2).tolist(), watertight=bool(t.is_watertight), bodies=int(t.body_count))}

if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
