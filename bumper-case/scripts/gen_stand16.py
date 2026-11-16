# ogm10-Jupiter vertical stand v16 = v15 with key clr 0.4, keycap-side clr 0, collar 9mm; v15 = v14 with collar 11mm, key 10mm; v14 = v13 (Ø50, centre +5mm keycap side, tighter, taller collar); v12 = v11 (Ø56) with tighter / thicker keycap-side prop, longer at the encoder and Shift
# frame: u = keyboard Y (front->rear), v = keyboard Z (fin side -> keycap side), w = up (= keyboard X from the foot end)
# keyboard (K frame Z): PCB top 6.2, top plate 8.4..9.6 (from X=2.9), foot end lip top 7.25
# NOTE: the Shift extension fits the LEFT end only (right end: 1u key there, switch from X~4.9)
import sys, json
import numpy as np, shapely.geometry as sg
import gen_guard as G, gen_stand as S
import gen_stand7 as S7
S7.DIA = 50.0
S7.CENTER = (41.0, 9.0)    # shifted 5mm toward the keycap side (v13: v=4)
S7.CLR = 0.15              # foot pocket clearance (v13: 0.4)
S7.KEY_CLR = 0.4           # locating key clearance (v15: 0.2)
S7.H_COLLAR = 9.0          # fin-side collar height above the disc (v15: 11)
S7.KEY_H = 10.0            # locating key height (v14: 6)

PROP_V0 = 7.25            # thick part face on the foot end lip (7.25): 0 clearance (v15: 0.05)
PROP_T = 11.0             # thick part thickness (v11: 7.35 -> x1.5)
PROP_H = 2.4              # thick part height above the disc top
STEP_V0, STEP_T = 9.6, 2.7    # thin part on the top plate top (9.6): 0 clearance (v15: 0.05)
STEP_H = 4.6              # thin part height (1u switches from X~5.5)
ENC_U, STEP_H_ENC = (58.0, 80.0), 4.2          # encoder: v11 3.4
SHIFT_U, STEP_H_SHIFT = (22.6, 38.4), 9.0       # left 1.5u Shift row (switch housing from X~10.3)

def stand():
    m, o, disc, pocket = S7.stand()
    keep = disc.buffer(-S7.CHAMFER).difference(pocket)
    thick = keep.intersection(sg.box(-500, PROP_V0, 500, PROP_V0 + PROP_T))
    step = keep.intersection(sg.box(-500, STEP_V0, 500, STEP_V0 + STEP_T))
    enc = sg.box(ENC_U[0], -500, ENC_U[1], 500); sh = sg.box(SHIFT_U[0], -500, SHIFT_U[1], 500)
    T = S7.DISC_T
    m = m + S.ext(thick, T - 0.01, T + PROP_H)
    m = m + S.ext(step.difference(enc).difference(sh), T + PROP_H - 0.01, T + STEP_H)
    m = m + S.ext(step.intersection(enc), T + PROP_H - 0.01, T + STEP_H_ENC)
    m = m + S.ext(step.intersection(sh), T + PROP_H - 0.01, T + STEP_H_SHIFT)
    return m, o, disc, pocket

def export(out):
    m, o, disc, pocket = stand()
    t = G.to_tm(m); t.merge_vertices(digits_vertex=5); t.apply_translation(-t.bounds[0]); t.export(f'{out}/ogm10-Jupiter-stand.stl')
    return {'stand': dict(size=np.round(t.extents, 2).tolist(), watertight=bool(t.is_watertight), bodies=int(t.body_count))}

if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
