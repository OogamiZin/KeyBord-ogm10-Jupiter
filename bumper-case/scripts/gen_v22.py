# ogm10-Jupiter side guard v22
#  feet : v21 fit (0.15 per side / above the PCB), encoder notch in the end lip removed,
#         the top cover (claws + foot top) now reaches the top-plate edge, so seen from above it covers the guard lips
#  guards: v16 + more PCB/bottom-plate wedges on the rear guard (front has no free room left)
import sys, json, math
import numpy as np, trimesh
import gen_guard as G, gen_v22_base as B, gen_v21 as N, gen_v16 as W

N.V = B
N.FIT_Y = N.FIT_Z = 0.15
N.YF, N.YR = G.Y_FRONT - N.FIT_Y, G.Y_REAR + N.FIT_Y
N.Z_LIP0 = G.Z_PCB_TOP + N.FIT_Z

W.REAR_WEDGES = [(48.3, 51.0), (62.0, 70.0), (74.0, 82.0), (86.0, 94.0), (98.0, 106.0), (110.0, 118.0), (121.5, 129.5),
                 (132.8, 136.6), (162.7, 167.8), (181.7, 186.9), (200.8, 212.4)]

def export_feet(out):
    info = {}
    t = G.to_tm(N.foot_left())                                   # manifold output is already one closed body
    t.apply_transform(G.K2P)
    tr = t.copy(); tr.vertices[:, 0] = G.FOOT_PX_MAX - tr.vertices[:, 0]; tr.invert()
    for name, m in (('foot-L', t), ('foot-R', tr)):
        m.apply_translation(-m.bounds[0]); m.export(f'{out}/ogm10-Jupiter-{name}.stl')
        r = trimesh.load(f'{out}/ogm10-Jupiter-{name}.stl')            # clean the float32 slivers of the STL
        r.merge_vertices(digits_vertex=5); r.update_faces(r.nondegenerate_faces(height=1e-6)); r.remove_unreferenced_vertices()
        r.export(f'{out}/ogm10-Jupiter-{name}.stl'); r = trimesh.load(f'{out}/ogm10-Jupiter-{name}.stl')
        info[name] = dict(size=np.round(r.extents, 2).tolist(), watertight=bool(r.is_watertight), bodies=int(r.body_count))
    return info

def export(out):
    info = export_feet(out)
    info.update(W.export(out))
    return info

if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
