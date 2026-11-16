# ogm10-Jupiter side guard v14 = v12 design, feet cleaned up
#  * all added surfaces use the exact planes of the original clip foot (desk edge, fin rear face, pocket floor)
#    -> no hair-line slivers where the added walls meet the original model
#  * claw tapers are single planar chamfers (no 16-step staircase), no epsilon overlaps / 0.01mm buffers
#  * guards are unchanged from v12 (front guard v8, rear guard v10)
import sys, json, math
import numpy as np, trimesh, manifold3d as M, shapely.geometry as sg
import gen_guard as G, gen_half2 as H
import gen_v12 as V12                       # v12 parameters / guard geometry (rear_profile_flat, CLAW_*)

TOT = V12.TOT
CLAW_T, CLR = V12.CLAW_T, V12.CLAW_CLR
CLAW_X1 = V12.CLAW_X1                       # 28.5
TAPER = 4.0
XT = CLAW_X1 - TAPER                        # taper starts here

def xz_prism(poly, y0, y1):
    """polygon in (X,Z) extruded along Y from y0 to y1"""
    t = trimesh.creation.extrude_polygon(poly, y1 - y0)
    t.apply_transform(np.array([[1,0,0,0],[0,0,-1,0],[0,1,0,0],[0,0,0,1]], float))   # (a,b,t)->(a,-t,b)
    t.apply_translation([0, y1, 0])
    return G.to_man(t)

def xy_prism(poly, z0, z1):
    t = trimesh.creation.extrude_polygon(poly, z1 - z0); t.apply_translation([0, 0, z0]); return G.to_man(t)

def chamfer_y(y_full, y_zero, outward_sign):
    """remove material beyond a plane that moves from y_full (at XT) to y_zero (at CLAW_X1)"""
    big = 200 * outward_sign
    poly = sg.Polygon([(XT, y_full), (CLAW_X1 + 1, y_zero + (y_zero - y_full)/TAPER), (CLAW_X1 + 1, big), (XT, big)])
    return xy_prism(poly.buffer(0), -100, 100)

def chamfer_z(z_full, z_zero, outward_sign):
    big = 200 * outward_sign
    poly = sg.Polygon([(XT, z_full), (CLAW_X1 + 1, z_zero + (z_zero - z_full)/TAPER), (CLAW_X1 + 1, big), (XT, big)])
    return xz_prism(poly.buffer(0), -100, 200)

def foot_left():
    h = H.half([G.X_END + u for u in G.USB_XP if u < G.HALF])
    f = h ^ G.box(-50, -50, -50, G.FOOT_X1, 150, 50)

    # ---------------- rear ----------------
    pr = V12.rear_profile_flat()
    keep_r = sg.box(78.6, -50, 200, 50).union(sg.box(-50, -50, 200, H.REAR_BOT - CLR))
    shell_r = pr.buffer(CLR + CLAW_T, join_style=2).difference(pr.buffer(CLR, join_style=2)).intersection(keep_r)
    claw_r = H.prism_yz(shell_r, G.FOOT_X1 - 0.5, CLAW_X1)
    y_out, y_in = H.Y_R_OUT + CLR + CLAW_T, H.Y_R_OUT + CLR
    claw_r = claw_r - chamfer_y(y_out, y_in, +1)                                   # back face
    claw_r = claw_r - chamfer_z(H.Z_TOP + CLR + CLAW_T, H.Z_TOP + CLR, +1)         # top
    claw_r = claw_r - chamfer_z(H.REAR_BOT - CLR - CLAW_T, H.REAR_BOT - CLR, -1)    # bottom
    fill_r = pr.buffer(CLR + CLAW_T, join_style=2)
    fill_r = fill_r.difference(sg.box(-50, 0.0, 78.44, 50)).difference(sg.box(-50, 7.25, 78.6, 50))
    # fin rear face moved out so it runs straight into the claw's outer-bottom corner (exact fin planes)
    yo, zo = y_out, H.REAR_BOT - CLR - CLAW_T
    yc = (zo - H.SLOPE_B*yo - H.A[1] + H.SLOPE_D*H.A[0]) / (H.SLOPE_D - H.SLOPE_B); zc = H.zd(yc)
    n = np.array([-(H.B[1]-H.Cc[1]), (H.B[0]-H.Cc[0])]); n = n/np.linalg.norm(n)       # inward normal of the fin rear face
    if np.dot(n, np.array(H.A) - np.array(H.Cc)) < 0: n = -n
    Bi, Ci = tuple(np.array(H.B) + 1.0*n), tuple(np.array(H.Cc) + 1.0*n)
    band = sg.Polygon([Bi, H.B, (yo, zo), (yc, zc), H.Cc, Ci])
    rear = H.prism_yz(fill_r, 0.0, G.FOOT_X1) + H.prism_yz(band.buffer(0), 0.0, G.FOOT_X1)

    # ---------------- front ----------------
    pf = H.front_profile()
    above_desk = sg.Polygon([(-50, H.zd(-50)), (200, H.zd(200)), (200, 100), (-50, 100)])
    keep_f = sg.box(-50, -50, G.Y_FRONT - 0.46, 100).intersection(above_desk)
    shell_f = pf.buffer(CLR + CLAW_T, join_style=2).difference(pf.buffer(CLR, join_style=2)).intersection(keep_f)
    claw_f = H.prism_yz(shell_f, 0.0, CLAW_X1)
    claw_f = claw_f - chamfer_y(H.Y_F_OUT - CLR - CLAW_T, H.Y_F_OUT - CLR, -1)      # front face
    claw_f = claw_f - chamfer_z(H.Z_TOP + CLR + CLAW_T, H.Z_TOP + CLR, +1)         # top
    fill_f = H.prism_yz(pf.buffer(CLR + CLAW_T, join_style=2).intersection(keep_f), 0.0, G.FOOT_X1)

    return f + rear + claw_r + fill_f + claw_f

def export(out):
    info = {}
    fl = G.to_tm(foot_left()); fl.apply_transform(G.K2P)
    fr = fl.copy(); fr.vertices[:, 0] = G.FOOT_PX_MAX - fr.vertices[:, 0]; fr.invert()
    for name, t in (('foot-L', fl), ('foot-R', fr)):
        t.apply_translation(-t.bounds[0])
        t.export(f'{out}/ogm10-Jupiter-{name}.stl')
        info[name] = dict(size=np.round(t.extents, 2).tolist(), watertight=bool(t.is_watertight), bodies=int(t.body_count), faces=len(t.faces))
    return info

if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
