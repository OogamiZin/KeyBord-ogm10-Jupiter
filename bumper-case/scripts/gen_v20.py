# ogm10-Jupiter side guard v20: feet rebuilt from clean sections (no imported clip-foot mesh -> no seam lines)
#  same function/dimensions as v19: plate pocket 1.65mm with hooks, fin truss on the 19.2deg desk plane, end wall,
#  front/rear claws around the v16 guards, rounded hand-contact edges.  Guards = v16.
import sys, json
import numpy as np, trimesh, shapely.geometry as sg, shapely.ops as so
import gen_guard as G, gen_half2 as H, gen_v12 as V12, gen_v14 as F

CLR, CLAW_T, CLAW_X1 = F.CLR, F.CLAW_T, F.CLAW_X1
R_SEC, R_END, R_HOLE = 0.8, 1.5, 1.5
Z_RIM = H.Z_TOP
Z_CLAW = H.Z_TOP + CLR + CLAW_T
Y_F_HOOK, Y_R_HOOK = G.Y_FRONT - 0.46, 78.6
XF = G.FOOT_X1                                   # 10.5
# plate pocket (from the original clip foot): Y 1.70..78.37, Z 0..1.65, end stop at X 2.9; hooks 0.9mm above it
POCKET_Y, POCKET_Z = (1.70, 78.37), 1.65
HOOK_Z = (1.65, 2.55)
HOOK_Y = [((1.70, 16.07), XF), ((61.57, 78.37), XF), ((16.07, 61.57), 6.0)]     # (Y range, X end)
HOLE = [(20.05, -3.00), (75.85, -3.00), (69.79, -20.41), (20.04, -3.10)]       # fin truss opening (Y,Z)

def pyz(poly, x0, x1):
    out = None
    for g in getattr(poly, 'geoms', [poly]):
        if g.area < 1e-6: continue
        m = H.prism_yz(g, x0, x1); out = m if out is None else out + m
    return out

def opn(p, r=R_SEC):
    return p.buffer(-r, join_style=1, resolution=16).buffer(r, join_style=1, resolution=16)

def sections():
    pf, pr = H.front_profile(), V12.rear_profile_flat()
    above_desk = sg.Polygon([(-50, H.zd(-50)), (200, H.zd(200)), (200, 100), (-50, 100)])
    keep_f = sg.box(-50, -50, Y_F_HOOK, 100).intersection(above_desk)
    ff = pf.buffer(CLR + CLAW_T, join_style=2).intersection(keep_f)
    fill_f = opn(ff).union(ff.intersection(sg.box(-50, -50, 200, 2.5)))
    fill_r = pr.buffer(CLR + CLAW_T, join_style=2).difference(sg.box(-50, 0.0, 78.44, 50)).difference(sg.box(-50, 7.25, 78.6, 50))
    fill_r = opn(fill_r)
    yo, zo = H.Y_R_OUT + CLR + CLAW_T, H.REAR_BOT - CLR - CLAW_T
    yc = (zo - H.SLOPE_B*yo - H.A[1] + H.SLOPE_D*H.A[0]) / (H.SLOPE_D - H.SLOPE_B); zc = H.zd(yc)
    fin = sg.Polygon([H.A, (H.Y_R_IN, 0.0), (yo, zo + R_SEC), (yo - R_SEC, zo), (yc, zc)])
    walls = pf.union(pr.intersection(sg.box(-50, 0.0, 200, 50)))               # front wall + top lip, rear wall + top lip
    outline = so.unary_union([fin, fill_f, fill_r, walls])
    hole = opn(sg.Polygon(HOLE), R_HOLE)
    body = outline.difference(hole)
    cavity = sg.box(POCKET_Y[0], 0.0, POCKET_Y[1], POCKET_Z).union(sg.box(H.Y_F_IN, POCKET_Z - 0.01, H.Y_R_IN, H.Z_LIP0))
    endcap = body.union(sg.Polygon([(H.Y_F_IN, H.zd(H.Y_F_IN)), (H.A[0], 0.0), (H.Y_R_IN, 0.0), (H.Y_R_IN, Z_RIM), (H.Y_F_IN, Z_RIM)]))                 # outer end: closed up to the rim
    return body, cavity, endcap, shell_sections(pf, pr, keep_f), (yo, zo)

def shell_sections(pf, pr, keep_f):
    keep_r = sg.box(78.6, -50, 200, 50).union(sg.box(-50, -50, 200, H.REAR_BOT - CLR))
    shell_r = opn(pr.buffer(CLR + CLAW_T, join_style=2).difference(pr.buffer(CLR, join_style=2)).intersection(keep_r))
    sf = pf.buffer(CLR + CLAW_T, join_style=2).difference(pf.buffer(CLR, join_style=2)).intersection(keep_f)
    shell_f = opn(sf).union(sf.intersection(sg.box(-50, -50, 200, 2.5)))
    return shell_r, shell_f

def foot_left():
    body, cavity, endcap, (shell_r, shell_f), (yo, zo) = sections()
    foot = pyz(endcap, 0.0, G.X_END) + pyz(body.difference(cavity), G.X_END, XF)
    for (y0, y1), xe in HOOK_Y:                                                     # hooks over the bottom plate
        foot = foot + G.box(G.X_END, y0, HOOK_Z[0], xe, y1, HOOK_Z[1])
    lip = G.box(G.X_END, H.Y_F_IN, H.Z_LIP0, G.X_END + G.LIP_IN, H.Y_R_IN, Z_RIM) \
          - G.box(G.X_END - 1, G.ENC_NOTCH_Y[0], H.Z_LIP0 - 1, G.X_END + G.LIP_IN + 1, G.ENC_NOTCH_Y[1], Z_RIM + 1)
    foot = foot + lip
    # claws (continue the section past the foot, planar tapers at the end)
    claw_r = pyz(shell_r, XF, CLAW_X1)
    claw_r = claw_r - F.chamfer_y(yo, H.Y_R_OUT + CLR, +1) - F.chamfer_z(Z_CLAW, H.Z_TOP + CLR, +1) \
                    - F.chamfer_z(H.REAR_BOT - CLR - CLAW_T, H.REAR_BOT - CLR, -1)
    claw_f = pyz(shell_f, XF, CLAW_X1)
    claw_f = claw_f - F.chamfer_y(H.Y_F_OUT - CLR - CLAW_T, H.Y_F_OUT - CLR, -1) - F.chamfer_z(Z_CLAW, H.Z_TOP + CLR, +1)
    foot = foot + claw_r + claw_f
    # outer end: round the top edges and the two vertical corners
    ymin, ymax = H.Y_F_OUT - CLR - CLAW_T, yo
    def xz_env(ztop):
        return F.xz_prism(sg.box(0, -200, 400, ztop).buffer(-R_END, join_style=1).buffer(R_END, join_style=1)
                          .union(sg.box(0, -200, 400, ztop - R_END)).union(sg.box(R_END, -200, 400, ztop + 50)), -100, 200)
    env_xy = sg.box(0, ymin, 400, ymax).buffer(-R_END, join_style=1).buffer(R_END, join_style=1).union(sg.box(R_END, ymin - 50, 400, ymax + 50))
    mid = G.box(-1, Y_F_HOOK, -100, 400, Y_R_HOOK, 100)
    foot = (foot ^ mid ^ xz_env(Z_RIM)) + ((foot - mid) ^ xz_env(Z_CLAW))
    return foot ^ F.xy_prism(env_xy, -100, 100)

def export(out):
    info = {}
    t = G.to_tm(foot_left()); t = max(t.split(only_watertight=False), key=lambda p: abs(p.volume))
    t.apply_transform(G.K2P)
    tr = t.copy(); tr.vertices[:, 0] = G.FOOT_PX_MAX - tr.vertices[:, 0]; tr.invert()
    for name, m in (('foot-L', t), ('foot-R', tr)):
        m.apply_translation(-m.bounds[0]); m.export(f'{out}/ogm10-Jupiter-{name}.stl')
        info[name] = dict(size=np.round(m.extents, 2).tolist(), watertight=bool(m.is_watertight), bodies=int(m.body_count), faces=len(m.faces))
    return info

if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
