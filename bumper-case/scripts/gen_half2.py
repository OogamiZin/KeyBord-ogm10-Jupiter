# ogm10-Jupiter slide-on side guards v2 (L/R) - outer surfaces continue the foot's own faces
#   front face  : flush with the foot front face (Y=0), bottom edge on the desk plane (same line as the fin's front-bottom edge)
#   rear face   : flush with the foot's rear corner (Y=80.96), lower face continues the fin's rear face (BC plane)
#   top         : one height all around (Z=7.25)
import sys, json, math
import numpy as np, trimesh, manifold3d as M, shapely.geometry as sg
import gen_guard as G

# exact values measured from the original clip-foot STL (mid-thickness section)
_PX0 = 24.91094
A = (2.0, 0.0)                                  # desk edge leaves the plate bottom here
_D2 = (70.8958, _PX0-48.88484)                  # second point on the desk edge
Cc = (71.63787, _PX0-49.14306)                  # fin rear-bottom corner (on the desk)
B = (80.95733, _PX0-22.36094)                   # fin rear-top corner
SLOPE_D = (_D2[1]-A[1])/(_D2[0]-A[0])           # desk plane
SLOPE_B = (B[1]-Cc[1])/(B[0]-Cc[0])            # rear face of the fin
zd = lambda y: A[1] + (y-A[0])*SLOPE_D
zb = lambda y: B[1] + (y-B[0])*SLOPE_B
yb = lambda z: B[0] + (z-B[1])/SLOPE_B

Z_TOP = G.Z_TOP                 # 7.25
Z_LIP0 = G.Z_LIP0               # 6.45  (top lip, on PCB top)
Y_F_IN = G.Y_FRONT - G.GAP_Y    # 1.64
Y_R_IN = G.Y_REAR + G.GAP_Y     # 78.44
Y_F_OUT, Y_R_OUT = 0.0, B[0]
PCB_LIP = (G.Z_PCB_BOT-0.75, G.Z_PCB_BOT-0.05)   # front: lip under the PCB edge (3.85..4.55)
PCB_LIP_IN = 1.0
REAR_BOT = -2.2                 # rear lip under the bottom plate
REAR_LIP_IN = 2.5
USB_Z0, USB_Z1 = -0.9, Z_LIP0   # USB opening; thin strips stay above and below (print bridge)
NOTCH_X = (108.9, 121.9)        # front PCB lip removed under U3 / R15 (K-frame X, both halves)
X_SEAM = G.X_END + G.HALF - G.SEAM_GAP

def prism_yz(poly, x0, x1):
    t = trimesh.creation.extrude_polygon(poly, x1-x0)
    t.apply_transform(np.array([[0,0,1,x0],[1,0,0,0],[0,1,0,0],[0,0,0,1]], float))
    return G.to_man(t)

def front_profile():
    return sg.Polygon([(Y_F_OUT, zd(Y_F_OUT)), (Y_F_OUT, Z_TOP), (G.Y_FRONT+G.LIP_IN, Z_TOP), (G.Y_FRONT+G.LIP_IN, Z_LIP0),
                       (Y_F_IN, Z_LIP0), (Y_F_IN, zd(Y_F_IN))])

def front_pcb_lip():
    return sg.box(Y_F_IN-0.3, PCB_LIP[0], G.Y_FRONT+PCB_LIP_IN, PCB_LIP[1])

def rear_profile(with_lip=True):
    pts = [(Y_R_OUT, Z_TOP), (G.Y_REAR-G.LIP_IN, Z_TOP), (G.Y_REAR-G.LIP_IN, Z_LIP0), (Y_R_IN, Z_LIP0)]
    if with_lip:
        pts += [(Y_R_IN, 0.0), (G.Y_REAR-REAR_LIP_IN, 0.0), (G.Y_REAR-REAR_LIP_IN, REAR_BOT), (yb(REAR_BOT), REAR_BOT)]
    else:
        pts += [(Y_R_IN, zb(Y_R_IN))]
    pts += [(Y_R_OUT, B[1])]
    return sg.Polygon(pts)

def half(usb_x):
    foot = trimesh.load(G.FOOT_L); foot.apply_transform(G.P2K); m = G.to_man(foot)
    L = X_SEAM
    add = prism_yz(front_profile(), 0, L)
    lip = prism_yz(front_pcb_lip(), G.X_END, L)
    lip = lip - G.box(NOTCH_X[0], -5, -5, NOTCH_X[1], 20, 20)
    add += lip
    add += prism_yz(rear_profile(False), 0, G.FOOT_X1+0.01)      # inside the foot: follow the fin's rear face
    add += prism_yz(rear_profile(True), G.FOOT_X1, L)
    # end wall (outer end of the plate/PCB) + top lip with the ENC1 tab notch
    end = sg.Polygon([(Y_F_OUT, zd(Y_F_OUT)), (Y_F_OUT, Z_TOP), (Y_R_OUT, Z_TOP), (Y_R_OUT, B[1]), (Y_R_IN, 0), (G.Y_FRONT, max(0.0, zd(G.Y_FRONT)))])
    add += prism_yz(end, 0, G.X_END)
    add += G.box(G.X_END-0.01, Y_F_IN, Z_LIP0, G.X_END+G.LIP_IN, Y_R_IN, Z_TOP) - G.box(G.X_END-1, G.ENC_NOTCH_Y[0], Z_LIP0-1, G.X_END+G.LIP_IN+1, G.ENC_NOTCH_Y[1], Z_TOP+1)
    cav = G.box(G.X_END, G.Y_FRONT-0.05, 0.0, 400, G.Y_REAR+0.05, Z_LIP0)
    cav = cav - G.box(G.X_END, G.Y_FRONT-0.06, PCB_LIP[0], 400, G.Y_FRONT+PCB_LIP_IN, PCB_LIP[1])   # keep the PCB lip
    m = m + (add - cav)
    for xc in usb_x:
        m = m - G.box(xc-G.USB_W/2, G.Y_REAR-REAR_LIP_IN-1, USB_Z0, xc+G.USB_W/2, Y_R_OUT+2, USB_Z1)
    return m

def export(out):
    info = {}
    usb_L = [G.X_END + u for u in G.USB_XP if u < G.HALF]
    usb_R = [G.X_END + (G.LEN - u) for u in G.USB_XP if u > G.HALF]
    for name, ux, mirror in (('L', usb_L, False), ('R', usb_R, True)):
        t = G.to_tm(half(ux)); t.apply_transform(G.K2P)
        if mirror:
            t.vertices[:, 0] = G.FOOT_PX_MAX - t.vertices[:, 0]; t.invert()
        t.apply_translation(-t.bounds[0])
        t.export(f'{out}/ogm10-Jupiter-sideguard-{name}.stl')
        info[name] = dict(size=np.round(t.extents, 2).tolist(), watertight=bool(t.is_watertight), bodies=int(t.body_count), vol=round(t.volume, 1))
    return info

if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
