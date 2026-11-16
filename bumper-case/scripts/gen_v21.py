# ogm10-Jupiter side guard v21: v20 feet with a tighter fit on the PCB / bottom-plate stack
#   side gap (Y)   : 0.30 (PCB section) / 0.24 (plate pocket) -> FIT_Y per side
#   gap above PCB  : 0.25 (end lip / front & rear lips on the PCB top) -> FIT_Z
#   the outside of the foot (and so the v16 guards / claws) is unchanged
import sys, json
import numpy as np, trimesh
import gen_guard as G, gen_half2 as H, gen_v20 as V

FIT_Y = 0.10
FIT_Z = 0.10
YF, YR = G.Y_FRONT - FIT_Y, G.Y_REAR + FIT_Y          # new inner faces (1.84 / 78.24)
Z_LIP0 = G.Z_PCB_TOP + FIT_Z                           # 6.30 (was 6.45)

def foot_left():
    f = V.foot_left()
    X0, X1 = G.X_END - 0.01, G.FOOT_X1 + 0.01
    # side faces: grow the inner front/rear faces toward the board (material copied from the wall itself)
    d = 0.4
    f = f + (f.translate((0, d, 0)) ^ G.box(X0, 1.5, 0.0, X1, YF, G.Z_TOP)) \
          + (f.translate((0, -d, 0)) ^ G.box(X0, YR, 0.0, X1, 78.6, G.Z_TOP))
    # top: lower every lip that sits on the PCB top (end lip, front/rear lips)
    dz = G.Z_LIP0 - Z_LIP0
    f = f + (f.translate((0, 0, -dz - 0.01)) ^ G.box(X0, YF - 0.01, Z_LIP0, X1, YR + 0.01, G.Z_LIP0 + 0.01))
    return f

def export(out):
    info = {}
    t = G.to_tm(foot_left()); t = max(t.split(only_watertight=False), key=lambda p: abs(p.volume))
    t.apply_transform(G.K2P)
    tr = t.copy(); tr.vertices[:, 0] = G.FOOT_PX_MAX - tr.vertices[:, 0]; tr.invert()
    for name, m in (('foot-L', t), ('foot-R', tr)):
        m.apply_translation(-m.bounds[0]); m.export(f'{out}/ogm10-Jupiter-{name}.stl')
        info[name] = dict(size=np.round(m.extents, 2).tolist(), watertight=bool(m.is_watertight), bodies=int(m.body_count))
    return info

if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
