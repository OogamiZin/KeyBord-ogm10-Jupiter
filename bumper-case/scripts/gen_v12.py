# ogm10-Jupiter side guard v12 (front guard also clamped by the feet)
# v11 (smooth foot joints)
# v10 (rear guard flat back, printed USB face down; foot claws follow)
# v9 (rear guard: plate jaws)
# v8 (front guard: 4 spacer snaps)
# v7 (claw covers the foot to its outer end):
# v6: 4 parts + locks
#  - foot <-> guard gap 0.05 mm
#  - front guard: snap rings that clip onto the two front-most M2 spacers (round, knurled, ~3 mm)
#  - rear guard : each foot grows a claw along its back that wraps the rear guard end (outer face, top, underside)
import sys, json, math
import numpy as np, trimesh, shapely.geometry as sg, shapely.ops as so
import gen_guard as G, gen_half2 as H

H.REAR_LIP_IN = 10.0
TOT = 2*G.X_END + G.LEN
GAP = 0.05
X0, X1 = G.FOOT_X1 + GAP, TOT - G.FOOT_X1 - GAP
NOTCH = (108.9, 121.9)
USB_X = [G.X_END + u for u in G.USB_XP]
BED = 180.0

# ---- spacer snap rings (front guard) ----
SPACER_D = 3.0                       # knurled round spacer, nominal OD
SEAT_D = SPACER_D + 0.3              # seat (knurl peaks)
SNAP_W = SPACER_D - 0.45             # opening width -> snaps over
RING_W = 1.4                         # ring wall
Z_TAB = (G.PLATE_T + 0.05, G.PLATE_T + 0.95)   # lies on the bottom-plate top, under the PCB-bottom parts (sockets end at Z 2.75)
SPACERS = [(G.X_END + (x - 7.496), G.Y_FRONT + (83.63 - y)) for x, y in ((71.496, 74.929), (171.496, 74.929), (29.246, 65.179), (216.996, 64.68))]
STEM_W = 5.0

def snap_tab(xc, yc):
    r_seat, r_out = SEAT_D/2, SEAT_D/2 + RING_W
    ring = sg.Point(xc, yc).buffer(r_out, 64)
    stem = sg.box(xc - STEM_W/2, H.Y_F_IN - 0.5, xc + STEM_W/2, yc)
    shape = ring.union(stem)
    shape = shape.difference(sg.Point(xc, yc).buffer(r_seat, 64))
    shape = shape.difference(sg.box(xc - SNAP_W/2, yc, xc + SNAP_W/2, yc + r_out + 1))         # entry (rear side)
    shape = shape.difference(sg.box(xc - 0.4, yc - r_seat - 3.0, xc + 0.4, yc))                  # flex slot
    return shape

def xy_prism(poly, z0, z1):
    t = trimesh.creation.extrude_polygon(poly, z1 - z0); t.apply_translation([0, 0, z0]); return G.to_man(t)

def front_guard():
    m = H.prism_yz(H.front_profile(), X0, X1)
    lip = H.prism_yz(H.front_pcb_lip(), X0, X1) - G.box(NOTCH[0], -5, -5, NOTCH[1], 20, 20)
    m = m + lip
    for xc, yc in SPACERS:
        m = m + xy_prism(snap_tab(xc, yc), *Z_TAB)
    return m

# v9: upper jaws on the bottom-plate top surface (plate is clamped between them and the 10mm under-lip)
REAR_JAW_X = [20.0, 60.0, 85.0, 110.0, 130.0, 205.0]     # clear of the USB-C bodies (+-8mm) and the encoder pins
REAR_JAW_W = 10.0
REAR_JAW_Z = (G.PLATE_T + 0.02, G.PLATE_T + 0.92)       # 1.62..2.52 (PCB-bottom parts end at Z 2.75)
REAR_JAW_IN = 2.5                                         # overlap onto the plate top

def rear_guard():
    m = H.prism_yz(rear_profile_flat(), X0, X1)
    for xc in REAR_JAW_X:
        m = m + G.box(xc - REAR_JAW_W/2, G.Y_REAR - REAR_JAW_IN, REAR_JAW_Z[0], xc + REAR_JAW_W/2, H.Y_R_IN + 0.3, REAR_JAW_Z[1])
    for xc in USB_X:
        m = m - G.box(xc - G.USB_W/2, H.Y_R_IN - 1.0, H.USB_Z0, xc + G.USB_W/2, H.Y_R_OUT + 2, H.USB_Z1)
    return m

# ---- v10: rear guard back face is one flat plane (printed USB face down) ----
def rear_profile_flat():
    return sg.Polygon([(H.Y_R_OUT, H.Z_TOP), (G.Y_REAR-G.LIP_IN, H.Z_TOP), (G.Y_REAR-G.LIP_IN, H.Z_LIP0), (H.Y_R_IN, H.Z_LIP0),
                       (H.Y_R_IN, 0.0), (G.Y_REAR-H.REAR_LIP_IN, 0.0), (G.Y_REAR-H.REAR_LIP_IN, H.REAR_BOT), (H.Y_R_OUT, H.REAR_BOT)])

# ---- rear claw on the foot ----
CLAW_T = 1.6
CLAW_CLR = 0.1
CLAW_X1 = 28.5                      # stays clear of the first USB opening (starts at X 30.3)
def claw_profile():
    p = rear_profile_flat()
    shell = p.buffer(CLAW_CLR + CLAW_T, join_style=2).difference(p.buffer(CLAW_CLR, join_style=2))
    keep = sg.box(78.6, -50, 200, 50).union(sg.box(-50, -50, 200, H.REAR_BOT - CLAW_CLR + 0.001))   # outside the top plate / below the guard
    return shell.intersection(keep)

def foot_left():
    h = H.half([G.X_END + u for u in G.USB_XP if u < G.HALF])
    f = h ^ G.box(-50, -50, -50, G.FOOT_X1, 150, 50)
    # v11: claw tapers to the guard surface over its last TAPER mm (no step where the claw ends)
    TAPER, NSTEP = 4.0, 16
    claw = H.prism_yz(claw_profile(), G.FOOT_X1 - 0.5, CLAW_X1 - TAPER)
    p0 = rear_profile_flat()
    keep = sg.box(78.6, -50, 200, 50).union(sg.box(-50, -50, 200, H.REAR_BOT - CLAW_CLR + 0.001))
    for k in range(NSTEP):
        xa = CLAW_X1 - TAPER + k*TAPER/NSTEP; xb = xa + TAPER/NSTEP
        t = CLAW_T * (1 - (k + 0.5)/NSTEP)
        sh = p0.buffer(CLAW_CLR + t, join_style=2).difference(p0.buffer(CLAW_CLR, join_style=2)).intersection(keep)
        claw = claw + H.prism_yz(sh, xa - 0.001, xb + 0.001)
    # v7: the claw's outer shape continues over the foot itself, right to the outer end face (X=0)
    p = rear_profile_flat()
    fill = p.buffer(CLAW_CLR + CLAW_T, join_style=2)
    fill = fill.difference(sg.box(-50, 0.0, 78.44, 50))          # keep the plate / PCB / top-plate area free (Y < 78.44, Z >= 0)
    fill = fill.difference(sg.box(-50, 7.25, 78.6, 50))          # top-plate edge clearance
    endcap = H.prism_yz(fill, 0.0, G.FOOT_X1)
    # v11: thicken the fin's rear member so its slanted rear face runs straight up into the claw's outer corner
    yo, zo = H.Y_R_OUT + CLAW_CLR + CLAW_T, H.REAR_BOT - CLAW_CLR - CLAW_T     # claw outer-bottom corner
    s_bc = H.SLOPE_B
    # intersection of the shifted rear face with the desk plane
    yc = (zo - s_bc*yo - H.A[1] + H.SLOPE_D*H.A[0]) / (H.SLOPE_D - s_bc); zc = H.zd(yc)
    band = sg.Polygon([H.Cc, (yc, zc), (yo, zo), (H.yb(zo), zo)])
    fin_ext = H.prism_yz(band.buffer(0.01), 0.0, G.FOOT_X1)
    # v12: front claw (outer face + top hook) wrapping the front guard end; bottom follows the desk plane
    pf = H.front_profile()
    above_desk = sg.Polygon([(-50, H.zd(-50)), (200, H.zd(200)), (200, 100), (-50, 100)])
    keep_f = sg.box(-50, -50, G.Y_FRONT - 0.46, 100).intersection(above_desk)     # stay outside the top-plate edge
    def fshell(t):
        return pf.buffer(CLAW_CLR + t, join_style=2).difference(pf.buffer(CLAW_CLR, join_style=2)).intersection(keep_f)
    fclaw = H.prism_yz(fshell(CLAW_T), 0.0, CLAW_X1 - TAPER)
    for k in range(NSTEP):
        xa = CLAW_X1 - TAPER + k*TAPER/NSTEP; xb = xa + TAPER/NSTEP
        fclaw = fclaw + H.prism_yz(fshell(CLAW_T * (1 - (k + 0.5)/NSTEP)), xa - 0.001, xb + 0.001)
    ffill = H.prism_yz(pf.buffer(CLAW_CLR + CLAW_T, join_style=2).intersection(keep_f), 0.0, G.FOOT_X1)   # solid inside the foot -> one body
    return f + claw + endcap + fin_ext + fclaw + ffill

def diag(t):
    t = t.copy(); t.apply_transform(trimesh.transformations.rotation_matrix(math.pi/4, [0, 0, 1]))
    t.apply_translation(-t.bounds[0]); e = t.extents
    t.apply_translation([(BED - e[0])/2, (BED - e[1])/2, 0]); return t

def export(out):
    info = {}
    fl = G.to_tm(foot_left()); fl.apply_transform(G.K2P)
    fr = fl.copy(); fr.vertices[:, 0] = G.FOOT_PX_MAX - fr.vertices[:, 0]; fr.invert()
    fg = G.to_tm(front_guard()); fg.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [1, 0, 0]))
    rg = G.to_tm(rear_guard()); rg.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/2, [1, 0, 0]))   # USB face down
    for name, t, d in (('foot-L', fl, False), ('foot-R', fr, False), ('guard-front', fg, True), ('guard-rear', rg, True)):
        t.apply_translation(-t.bounds[0]); straight = np.round(t.extents, 2).tolist()
        if d: t = diag(t)
        t.export(f'{out}/ogm10-Jupiter-{name}.stl')
        info[name] = dict(part=straight, bed=np.round(t.extents, 1).tolist(), fits=bool(t.extents[0] <= BED and t.extents[1] <= BED and t.extents[2] <= BED),
                          watertight=bool(t.is_watertight), bodies=int(t.body_count))
    return info

if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
