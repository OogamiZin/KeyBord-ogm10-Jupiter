# ogm10-Jupiter side guard: modified ogm9-Izanami clip foot (end caps) + 4 side rails
# K frame (assembled, left end): X = inward along keyboard length (0 = outer end face of the foot)
#                               Y = front(0) -> rear(80), Z = up (0 = bottom-plate bottom face)
# Foot STL print frame p:  X = p.z, Y = p.y, Z = 24.91 - p.x   (R foot = L mirrored in p.x)
import sys, json, math
import numpy as np, trimesh, manifold3d as M

U = '/root/.claude/uploads/1c4fe9a0-59e4-58ce-90ae-acc6f6804ebc/'
FOOT_L = U + 'e874d122-ogm9-Izanami-clipfoot-half-fronthigh-L.stl'
PX_PLATE_BOTTOM = 24.91094          # exact pocket-floor plane of the original foot (p.x)
FOOT_PX_MAX = 49.1430588

# ---- stack (mm, Z from bottom-plate bottom) ----
PLATE_T = 1.6
SPACER = 3.0
PCB_T = 1.6
Z_PCB_BOT = PLATE_T + SPACER          # 4.6
Z_PCB_TOP = Z_PCB_BOT + PCB_T         # 6.2
CLR_Z = 0.25                          # clearance above PCB top
LIP_T = 0.8                           # top lip thickness
LIP_IN = 1.0                          # top lip overlap onto PCB top
Z_LIP0 = Z_PCB_TOP + CLR_Z            # 6.45
Z_TOP = Z_LIP0 + LIP_T                # 7.25

# ---- board / plate outline in K frame ----
X_END = 2.9                           # plate & PCB end face (foot pocket floor)
Y_FRONT = 1.94                        # plate/PCB front edge
DEPTH = 76.2
Y_REAR = Y_FRONT + DEPTH              # 78.14
LEN = 229.2
HALF = LEN / 2                        # 114.6 (seam, from plate end)
GAP_Y = 0.3                           # side clearance
WALL_F0, WALL_F1 = 0.0, Y_FRONT - GAP_Y           # front wall Y range
WALL_R0, WALL_R1 = Y_REAR + GAP_Y, 80.0           # rear wall Y range
FOOT_X1 = 10.5                        # foot extends to X = 10.5
RAIL_GAP = 0.2
SEAM_GAP = 0.15
BOT_IN = 2.5                          # bottom lip overlap under the plate
BOT_T_FRONT, BOT_T_REAR = 0.8, 1.2

# USB-C openings (rear), centres measured from the plate left end
USB_XP = [33.94, 148.24, 167.29, 186.34]
USB_W = 13.0
USB_Z1 = 6.9                          # opening top (plug overmold up to ~7mm tall, centred at Z=2.97)
Z_REAR_TOP = 9.4                      # rear wall top (outside the top plate edge)
# ENC1 mounting-tab solder pad near the left edge (top side): keep the end lip clear
ENC_NOTCH_Y = (66.4, 71.4)

def box(x0, y0, z0, x1, y1, z1):
    return M.Manifold.cube((x1-x0, y1-y0, z1-z0)).translate((x0, y0, z0))

def to_man(t):
    return M.Manifold(M.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))

def to_tm(m):
    me = m.to_mesh(); return trimesh.Trimesh(np.array(me.vert_properties)[:, :3].astype(np.float64), np.array(me.tri_verts), process=False)

P2K = np.array([[0,0,1,0],[0,1,0,0],[-1,0,0,PX_PLATE_BOTTOM],[0,0,0,1]], float)   # p -> K
K2P = np.linalg.inv(P2K)

def end_cap_left():
    foot = trimesh.load(FOOT_L); foot.apply_transform(P2K)
    m = to_man(foot)
    add = M.Manifold()
    # end wall over the full depth, up to the top lip
    add += box(0, WALL_F0, 0, X_END, WALL_R1, Z_TOP)
    # side walls along the foot length
    add += box(0, WALL_F0, 0, FOOT_X1, WALL_F1, Z_TOP)
    add += box(0, WALL_R0, 0, FOOT_X1, WALL_R1, Z_TOP)
    # top lips (sit on the PCB top surface)
    end_lip = box(X_END-0.01, WALL_F1, Z_LIP0, X_END+LIP_IN, WALL_R0, Z_TOP) - box(X_END-1, ENC_NOTCH_Y[0], Z_LIP0-1, X_END+LIP_IN+1, ENC_NOTCH_Y[1], Z_TOP+1)
    add += end_lip
    add += box(0, WALL_F1-0.01, Z_LIP0, FOOT_X1, Y_FRONT+LIP_IN, Z_TOP)
    add += box(0, Y_REAR-LIP_IN, Z_LIP0, FOOT_X1, WALL_R0+0.01, Z_TOP)
    # keep the board volume itself free
    cav = box(X_END, Y_FRONT-0.05, -0.0, 200, Y_REAR+0.05, Z_LIP0)
    return m + (add - cav)

def rail(front, x0, x1, usb_local=()):
    """C-channel along X from x0 to x1 (K frame)."""
    L = x1 - x0
    if front:
        bt = BOT_T_FRONT
        r = box(0, WALL_F0, -bt, L, WALL_F1, Z_TOP)                       # wall
        r += box(0, WALL_F1-0.01, -bt, L, Y_FRONT+BOT_IN, 0.0)            # bottom lip (under plate)
        r += box(0, WALL_F1-0.01, Z_LIP0, L, Y_FRONT+LIP_IN, Z_TOP)       # top lip (on PCB)
    else:
        bt = BOT_T_REAR
        r = box(0, WALL_R0, -bt, L, WALL_R1, Z_REAR_TOP)          # taller rear wall bridges the USB openings
        r += box(0, Y_REAR-BOT_IN, -bt, L, WALL_R0+0.01, 0.0)
        r += box(0, Y_REAR-LIP_IN, Z_LIP0, L, WALL_R0+0.01, Z_TOP)
    for u in usb_local:
        r -= box(u-USB_W/2, WALL_R0-BOT_IN-5, -5, u+USB_W/2, WALL_R1+5, USB_Z1)
    return r.translate((x0, 0, 0))

def build():
    parts = {}
    capL = end_cap_left()
    # rails (left half in K frame; right-half rails built in the mirrored frame then mirrored back)
    rx0 = FOOT_X1 + RAIL_GAP
    rx1 = X_END + HALF - SEAM_GAP
    fl = rail(True, rx0, rx1)
    rl = rail(False, rx0, rx1, [X_END + u - rx0 for u in USB_XP if u < HALF])
    # right half: work in mirrored coordinates X' measured from the right outer end
    rr = rail(False, rx0, rx1, [X_END + (LEN - u) - rx0 for u in USB_XP if u > HALF])
    parts['assembly_left'] = (capL, fl, rl)
    parts['rear_right_mirrored'] = rr
    return capL, fl, rl, rr

def export(out):
    capL, fl, rl, rr = build()
    info = {}
    # end caps in the original foot print orientation
    tL = to_tm(capL); tL.apply_transform(K2P)
    tR = tL.copy(); tR.vertices[:, 0] = FOOT_PX_MAX - tR.vertices[:, 0]; tR.invert()
    for name, t in (('endcap-L', tL), ('endcap-R', tR)):
        t.apply_translation(-t.bounds[0]); t.export(f'{out}/ogm10-Jupiter-guard-{name}.stl')
        info[name] = dict(size=np.round(t.extents, 2).tolist(), watertight=bool(t.is_watertight), bodies=int(t.body_count))
    # rails: lay on the outer wall face (no overhangs)
    def lay(m, front):
        t = to_tm(m)
        ang = math.pi/2 if front else -math.pi/2
        t.apply_transform(trimesh.transformations.rotation_matrix(ang, [1, 0, 0]))
        t.apply_translation(-t.bounds[0]); return t
    # right-half rails are mirror images (X) of the built ones
    def mirror_x(m):
        t = to_tm(m); t.vertices[:, 0] *= -1; t.invert(); return to_man(t)
    rails = {'rail-front-x2': (fl, True), 'rail-rear-L': (rl, False), 'rail-rear-R': (mirror_x(rr), False)}
    for name, (m, fr) in rails.items():
        t = lay(m, fr); t.export(f'{out}/ogm10-Jupiter-guard-{name}.stl')
        info[name] = dict(size=np.round(t.extents, 2).tolist(), watertight=bool(t.is_watertight), bodies=int(t.body_count))
    return info

if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
