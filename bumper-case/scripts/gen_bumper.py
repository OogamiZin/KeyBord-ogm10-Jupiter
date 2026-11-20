# ogm10-Jupiter バンパーケース生成スクリプト（足 L/R・前ガード・後ガード・縦置きスタンド）
#   旧 gen_v12〜gen_v31 / gen_stand〜gen_stand24 の最終形（v31 + stand v24）を1本にまとめたもの。
#   使い方: python3 gen_bumper.py <出力フォルダ>
#
# K 座標系（組み立て状態・左端基準）:
#   X = キーボード長手方向（0 = 足の外端面）, Y = 手前(0) -> 奥, Z = 上（0 = ボトムプレート下面）
# 足の STL 印刷姿勢 p:  X = p.z, Y = p.y, Z = 24.91 - p.x（R の足は L を p.x で反転）
import sys, json, math
import numpy as np, trimesh, manifold3d as M, shapely.geometry as sg, shapely.ops as so

# ============================================================================
# 基板・プレートの積層と外形（mm）
# ============================================================================
PLATE_T = 1.6
SPACER = 3.0
PCB_T = 1.6
Z_PCB_BOT = PLATE_T + SPACER          # 4.6
Z_PCB_TOP = Z_PCB_BOT + PCB_T         # 6.2
CLR_Z = 0.25                          # PCB 上面とリップのすき間
LIP_T = 0.8                           # 上リップの厚さ
LIP_IN = 1.0                          # 上リップが PCB 上面に掛かる量
Z_LIP0 = Z_PCB_TOP + CLR_Z            # 6.45
Z_TOP = Z_LIP0 + LIP_T                # 7.25

X_END = 2.9                           # プレート / PCB の端面（足のポケット底）
Y_FRONT = 1.94                        # プレート / PCB の手前端
DEPTH = 76.2
Y_REAR = Y_FRONT + DEPTH              # 78.14
LEN = 229.2
HALF = LEN / 2
GAP_Y = 0.3
FOOT_X1 = 10.5                        # 足の長さ（X = 0..10.5）

USB_XP = [33.94, 148.24, 167.29, 186.34]   # USB-C の中心（プレート左端から）
USB_W = 13.0

PX_PLATE_BOTTOM = 24.91094            # 元のクリップ足のポケット底面（p.x）
FOOT_PX_MAX = 49.1430588
P2K = np.array([[0,0,1,0],[0,1,0,0],[-1,0,0,PX_PLATE_BOTTOM],[0,0,0,1]], float)   # p -> K
K2P = np.linalg.inv(P2K)

# 元のクリップ足から実測した断面の点（Y, Z）
A = (2.0, 0.0)                                         # 机面の線がプレート下面から離れる点
_D2 = (70.8958, PX_PLATE_BOTTOM - 48.88484)            # 机面の線上の2点目
Cc = (71.63787, PX_PLATE_BOTTOM - 49.14306)            # フィン後端・下の角（机面上）
B = (80.95733, PX_PLATE_BOTTOM - 22.36094)             # フィン後端・上の角
SLOPE_D = (_D2[1]-A[1])/(_D2[0]-A[0])                  # 机面
SLOPE_B = (B[1]-Cc[1])/(B[0]-Cc[0])                    # フィンの後ろ面
zd = lambda y: A[1] + (y-A[0])*SLOPE_D

Y_F_IN = Y_FRONT - GAP_Y              # 1.64
Y_R_IN = Y_REAR + GAP_Y               # 78.44
Y_F_OUT, Y_R_OUT = 0.0, B[0]
PCB_LIP = (Z_PCB_BOT-0.75, Z_PCB_BOT-0.05)   # 前ガード: PCB 端の下に入るリップ（3.85..4.55）
PCB_LIP_IN = 1.0
REAR_BOT = -2.2                       # 後ガード: ボトムプレート下のリップ
REAR_LIP_IN = 10.0
USB_Z0, USB_Z1 = -0.9, Z_LIP0         # USB 開口（上下に薄い帯が残る）

# ============================================================================
# 共通ヘルパー
# ============================================================================
def box(x0, y0, z0, x1, y1, z1):
    return M.Manifold.cube((x1-x0, y1-y0, z1-z0)).translate((x0, y0, z0))

def to_man(t):
    return M.Manifold(M.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))

def to_tm(m):
    me = m.to_mesh(); return trimesh.Trimesh(np.array(me.vert_properties)[:, :3].astype(np.float64), np.array(me.tri_verts), process=False)

def prism_yz(poly, x0, x1):
    """(Y,Z) の断面を X 方向に x0..x1 で押し出し"""
    t = trimesh.creation.extrude_polygon(poly, x1-x0)
    t.apply_transform(np.array([[0,0,1,x0],[1,0,0,0],[0,1,0,0],[0,0,0,1]], float))
    return to_man(t)

def xz_prism(poly, y0, y1):
    """(X,Z) の断面を Y 方向に y0..y1 で押し出し"""
    t = trimesh.creation.extrude_polygon(poly, y1 - y0)
    t.apply_transform(np.array([[1,0,0,0],[0,0,-1,0],[0,1,0,0],[0,0,0,1]], float))   # (a,b,t)->(a,-t,b)
    t.apply_translation([0, y1, 0])
    return to_man(t)

def xy_prism(poly, z0, z1):
    t = trimesh.creation.extrude_polygon(poly, z1 - z0); t.apply_translation([0, 0, z0]); return to_man(t)

def pyz(poly, x0, x1):
    out = None
    for g in getattr(poly, 'geoms', [poly]):
        if g.area < 1e-6: continue
        m = prism_yz(g, x0, x1); out = m if out is None else out + m
    return out

def ext(poly, z0, z1):
    out = None
    for g in getattr(poly, 'geoms', [poly]):
        if g.area < 1e-6: continue
        t = trimesh.creation.extrude_polygon(g, z1 - z0); t.apply_translation([0, 0, z0]); m = to_man(t)
        out = m if out is None else out + m
    return out

# ============================================================================
# ガードの断面
# ============================================================================
def front_profile():
    return sg.Polygon([(Y_F_OUT, zd(Y_F_OUT)), (Y_F_OUT, Z_TOP), (Y_FRONT+LIP_IN, Z_TOP), (Y_FRONT+LIP_IN, Z_LIP0),
                       (Y_F_IN, Z_LIP0), (Y_F_IN, zd(Y_F_IN))])

def front_pcb_lip():
    return sg.box(Y_F_IN-0.3, PCB_LIP[0], Y_FRONT+PCB_LIP_IN, PCB_LIP[1])

def rear_profile_flat():
    """後ガード: 背面は1枚の平面（USB 面を下にして印刷）"""
    return sg.Polygon([(Y_R_OUT, Z_TOP), (Y_REAR-LIP_IN, Z_TOP), (Y_REAR-LIP_IN, Z_LIP0), (Y_R_IN, Z_LIP0),
                       (Y_R_IN, 0.0), (Y_REAR-REAR_LIP_IN, 0.0), (Y_REAR-REAR_LIP_IN, REAR_BOT), (Y_R_OUT, REAR_BOT)])

# ============================================================================
# 足（L/R）
# ============================================================================
CLR = 0.1                 # 爪とガードのすき間
CLAW_T = 1.6              # 爪の厚さ
CLAW_X1 = 28.5            # 爪の先端（最初の USB 開口 X 30.3 より手前）
TAPER = 4.0               # 爪先端の面取り長さ
XT = CLAW_X1 - TAPER
R_SEC, R_END, R_HOLE = 0.8, 1.5, 1.5
X_RAISE = X_END - 0.15    # 外端の壁を爪の高さまで上げる範囲
DROP = (CLR + CLAW_T) / math.cos(math.atan(abs(SLOPE_D)))     # 机面を下げる量（前ガード下の爪の帯厚）
Z_RIM = Z_TOP
Z_CLAW = Z_TOP + CLR + CLAW_T
Y_F_HOOK, Y_R_HOOK = Y_FRONT - 0.15, Y_REAR + 0.15     # 上面カバーがトッププレート端まで来る位置
Y_F_SIDE, Y_R_SIDE = Y_FRONT - 0.46, 78.6
XF = FOOT_X1
# プレートのポケット: Y 1.70..78.37, Z 0..1.65, X 2.9 で突き当て。その上 0.9mm にフック
POCKET_Y, POCKET_Z = (1.70, 78.37), 1.65
HOOK_Z = (1.65, 2.55)
HOOK_Y = [((1.70, 16.07), XF), ((61.57, 78.37), XF), ((16.07, 61.57), 6.0)]     # (Y 範囲, X 端)
HOLE = [(20.05, -3.00), (75.85, -3.00), (69.79, -20.41), (20.04, -3.10)]       # フィンの肉抜き穴（Y,Z）
# 基板・プレートへのはめあい（片側すき間 / PCB 上面とのすき間）
FIT_Y = FIT_Z = 0.15
FIT_YF, FIT_YR = Y_FRONT - FIT_Y, Y_REAR + FIT_Y
FIT_Z_LIP0 = Z_PCB_TOP + FIT_Z

def opn(p, r=R_SEC):
    return p.buffer(-r, join_style=1, resolution=16).buffer(r, join_style=1, resolution=16)

def chamfer_y(y_full, y_zero, outward_sign):
    """XT で y_full、CLAW_X1 で y_zero になる面より外側を削る"""
    big = 200 * outward_sign
    poly = sg.Polygon([(XT, y_full), (CLAW_X1 + 1, y_zero + (y_zero - y_full)/TAPER), (CLAW_X1 + 1, big), (XT, big)])
    return xy_prism(poly.buffer(0), -100, 100)

def chamfer_z(z_full, z_zero, outward_sign):
    big = 200 * outward_sign
    poly = sg.Polygon([(XT, z_full), (CLAW_X1 + 1, z_zero + (z_zero - z_full)/TAPER), (CLAW_X1 + 1, big), (XT, big)])
    return xz_prism(poly.buffer(0), -100, 200)

def foot_sections():
    pf, pr = front_profile(), rear_profile_flat()
    above_desk = sg.Polygon([(-50, zd(-50) - DROP), (200, zd(200) - DROP), (200, 100), (-50, 100)])
    below_old = sg.Polygon([(-50, zd(-50)), (200, zd(200)), (200, -100), (-50, -100)])
    keep_f = sg.box(-50, -50, Y_F_SIDE, 100).union(sg.box(-50, Z_TOP, Y_F_HOOK, 100)) \
               .union(sg.box(-50, -100, Y_FRONT - 0.25, 100).intersection(below_old)).intersection(above_desk)
    ff = pf.buffer(CLR + CLAW_T, join_style=2).intersection(keep_f)
    fill_f = opn(ff).union(ff.intersection(sg.box(-50, -50, 200, 2.5)))
    fill_r = pr.buffer(CLR + CLAW_T, join_style=2).difference(sg.box(-50, 0.0, 78.44, Z_TOP)).difference(sg.box(-50, Z_TOP, Y_R_HOOK, 50)).difference(sg.box(-50, 0.0, Y_R_SIDE, Z_TOP))
    fill_r = opn(fill_r)
    yo, zo = Y_R_OUT + CLR + CLAW_T, REAR_BOT - CLR - CLAW_T
    yc = (zo - SLOPE_B*yo - A[1] + SLOPE_D*A[0]) / (SLOPE_D - SLOPE_B); zc = zd(yc)
    fin = sg.Polygon([A, (Y_R_IN, 0.0), (yo, zo + R_SEC), (yo - R_SEC, zo), (yc, zc)])
    # 底面: 机面全体を DROP だけ下げる（傾き 19.2° のまま）。後ろ面の線を延長
    zl = lambda y: zd(y) - DROP
    sd = SLOPE_D; yc2 = (zc - SLOPE_B*yc - (A[1] - sd*A[0] - DROP)) / (sd - SLOPE_B)
    sole = sg.Polygon([(-0.01, zd(-0.01)), (yc, zc), (yc2, zl(yc2)), (-0.01, zl(-0.01))])
    fin = fin.union(sole)
    walls = pf.union(pr.intersection(sg.box(-50, 0.0, 200, 50)))
    outline = so.unary_union([fin, fill_f, fill_r, walls])
    hole = opn(sg.Polygon(HOLE), R_HOLE)
    body = outline.difference(hole)
    cavity = sg.box(POCKET_Y[0], 0.0, POCKET_Y[1], POCKET_Z).union(sg.box(Y_F_IN, POCKET_Z - 0.01, Y_R_IN, Z_LIP0))
    endcap = body.union(sg.Polygon([(Y_F_IN, zd(Y_F_IN)), (A[0], 0.0), (Y_R_IN, 0.0), (Y_R_IN, Z_RIM), (Y_F_IN, Z_RIM)]))
    endcap_hi = endcap.union(sg.box(Y_F_IN - 1.0, Z_RIM - 0.5, Y_R_IN + 1.0, Z_CLAW))   # 外端の壁は爪の高さまで
    return body, cavity, (endcap, endcap_hi), claw_sections(pf, pr, keep_f), (yo, zo)

def claw_sections(pf, pr, keep_f):
    """爪の断面 = 足自身の外側断面からガード + すき間を引いたもの（足と段差なくつながる）"""
    keep_r = sg.box(Y_R_SIDE, -50, 200, 50).union(sg.box(Y_R_HOOK, Z_TOP, 200, 50)).union(sg.box(-50, -50, 200, REAR_BOT - CLR))
    ff = pf.buffer(CLR + CLAW_T, join_style=2).intersection(keep_f)
    fill_f = opn(ff).union(ff.intersection(sg.box(-50, -50, 200, 2.5)))
    fill_r = pr.buffer(CLR + CLAW_T, join_style=2).difference(sg.box(-50, 0.0, 78.44, Z_TOP)).difference(sg.box(-50, Z_TOP, Y_R_HOOK, 50)).difference(sg.box(-50, 0.0, Y_R_SIDE, Z_TOP))
    fill_r = opn(fill_r)
    shell_f = fill_f.difference(pf.buffer(CLR, join_style=2))
    shell_r = fill_r.intersection(keep_r).difference(pr.buffer(CLR, join_style=2))
    big = lambda p: max(getattr(p, 'geoms', [p]), key=lambda g: g.area)
    return big(shell_r), big(shell_f)

def foot_base():
    body, cavity, (endcap, endcap_hi), (shell_r, shell_f), (yo, zo) = foot_sections()
    foot = pyz(endcap_hi, 0.0, X_RAISE) + pyz(endcap, 0.0, X_END) + pyz(body.difference(cavity), X_END, XF)
    for (y0, y1), xe in HOOK_Y:                                         # ボトムプレートに掛かるフック
        foot = foot + box(X_END, y0, HOOK_Z[0], xe, y1, HOOK_Z[1])
    foot = foot + box(X_END, Y_F_IN, Z_LIP0, X_END + LIP_IN, Y_R_IN, Z_RIM)    # 端のリップ
    # 爪（足の断面を延長し、先端を平面で面取り）
    claw_r = pyz(shell_r, XF, CLAW_X1)
    claw_r = claw_r - chamfer_y(yo, Y_R_OUT + CLR, +1) - chamfer_z(Z_CLAW, Z_TOP + CLR, +1) \
                    - chamfer_z(REAR_BOT - CLR - CLAW_T, REAR_BOT - CLR, -1)
    claw_f = pyz(shell_f, XF, CLAW_X1)
    claw_f = claw_f - chamfer_y(Y_F_OUT - CLR - CLAW_T, Y_F_OUT - CLR, -1) - chamfer_z(Z_CLAW, Z_TOP + CLR, +1)
    foot = foot + claw_r + claw_f
    # 外端: 上の稜線と縦の角2か所を丸める
    ymin, ymax = Y_F_OUT - CLR - CLAW_T, yo
    def xz_env(ztop):
        return xz_prism(sg.box(0, -200, 400, ztop).buffer(-R_END, join_style=1).buffer(R_END, join_style=1)
                        .union(sg.box(0, -200, 400, ztop - R_END)).union(sg.box(R_END, -200, 400, ztop + 50)), -100, 200)
    env_xy = sg.box(0, ymin, 400, ymax).buffer(-R_END, join_style=1).buffer(R_END, join_style=1).union(sg.box(R_END, ymin - 50, 400, ymax + 50))
    # 爪の間: X < X_RAISE は Z_CLAW、基板の上は Z_RIM。内側の上の稜線を薄い段（0.05mm）の積み重ねで R_SEC に丸める
    r, n = R_SEC, 16
    low = sg.box(X_RAISE, Y_F_HOOK - 0.03, 400, Y_R_HOOK + 0.03)
    cut = xy_prism(low, Z_RIM, Z_CLAW - r + 1e-3)
    z0 = Z_CLAW - r
    for k in range(n):
        za, zb = z0 + r*k/n, z0 + r*(k + 1)/n
        zm = (za + zb) / 2 - z0
        d = r - math.sqrt(max(r*r - zm*zm, 0.0))
        cut = cut + xy_prism(low.buffer(d, join_style=1, resolution=32) if d > 0.02 else low, za, zb + 1e-3)
    cut = cut + xy_prism(low.buffer(r, join_style=1, resolution=32), Z_CLAW, Z_CLAW + 5)
    foot = (foot ^ xz_env(Z_CLAW)) - cut
    return foot ^ xy_prism(env_xy, -100, 100)

def foot_left():
    """foot_base をはめあい寸法（FIT_Y / FIT_Z）に詰めたもの。外側の形は変えない"""
    f = foot_base()
    X0, X1 = X_END - 0.01, FOOT_X1 + 0.01
    d = 0.4      # 内側の前後面を基板側へ伸ばす（壁自身の形をコピー）
    f = f + (f.translate((0, d, 0)) ^ box(X0, 1.5, 0.0, X1, FIT_YF, Z_TOP)) \
          + (f.translate((0, -d, 0)) ^ box(X0, FIT_YR, 0.0, X1, 78.6, Z_TOP))
    dz = Z_LIP0 - FIT_Z_LIP0    # PCB 上面に乗るリップを下げる
    f = f + (f.translate((0, 0, -dz - 0.01)) ^ box(X0, FIT_YF - 0.01, FIT_Z_LIP0, X1, FIT_YR + 0.01, Z_LIP0 + 0.01))
    return f

# ============================================================================
# 前ガード・後ガード
# ============================================================================
GAP = 0.05                                       # 足とガードのすき間
G_X0, G_X1 = FOOT_X1 + GAP, (2*X_END + LEN) - FOOT_X1 - GAP
NOTCH = (108.9, 121.9)                           # 前ガードの PCB リップを U3 / R15 の下で切り欠く
USB_X = [X_END + u for u in USB_XP]
BED = 180.0

WZ = (PLATE_T + 0.02, Z_PCB_BOT - 0.05)          # ボトムプレートと PCB の間を埋めるくさび（1.62..4.55）
WEDGE_DEPTH = 5.5                                # PCB の下に入る深さ（基板端から）
SHORT_DEPTH = 2.6                                # 短いくさびの深さ
CH = 0.8                                         # 差し込み側の面取り
# 基板 x 範囲（EasyEDA 座標）。PCB 裏の部品を 0.5mm 避けた空き（pcb_bottom_obstacles.py 参照）
FRONT_WEDGES = [(26.6, 30.9), (69.5, 73.7), (93.3, 97.5), (145.7, 149.9), (169.5, 178.5)]
FRONT_SHORT = [(22.7, 38.5), (46.5, 57.5), (65.5, 81.3), (89.3, 105.1), (127.6, 133.7), (141.7, 157.5),
               (165.5, 186.1), (194.1, 205.2), (213.2, 224.2)]
REAR_WEDGES = [(62.0, 129.5), (132.8, 136.6)]    # USB-C 横のくさびは無し（基板は USB 付近を樹脂で固定）
bx = lambda x: X_END + (x - 7.496)               # 基板 x -> K 座標 X

# 後ガード: ボトムプレートの USB 切り欠きに入るキー（USB-C 本体の左右に1つずつ）
PLATE_NOTCH_X = [(34.94, 47.94), (149.24, 162.24), (168.29, 181.29), (187.34, 200.34)]
NOTCH_DEPTH = 9.5           # 切り欠きの深さ（後端から）
KEY_CLR_WALL = 0.10
USB_BODY_HALF = 4.47        # USB-C レセプタクルのシェル半幅
KEY_CLR_USB = 0.40
KEY_TOP = PLATE_T - 0.1     # 1.5

def wedge_xz(x0, x1, y0, y1, inner_at_y0):
    """差し込み側（上下）に 45° 面取りの付いたくさび"""
    zb, zt = WZ
    if inner_at_y0:
        poly = sg.Polygon([(y0, zb+CH), (y0+CH, zb), (y1, zb), (y1, zt), (y0+CH, zt), (y0, zt-CH)])
    else:
        poly = sg.Polygon([(y0, zb), (y1-CH, zb), (y1, zb+CH), (y1, zt-CH), (y1-CH, zt), (y0, zt)])
    return prism_yz(poly, x0, x1)

def front_guard():
    m = prism_yz(front_profile(), G_X0, G_X1)
    m = m + (prism_yz(front_pcb_lip(), G_X0, G_X1) - box(NOTCH[0], -5, -5, NOTCH[1], 20, 20))
    for a, b in FRONT_WEDGES:
        m = m + wedge_xz(bx(a), bx(b), Y_F_IN - 0.3, Y_FRONT + WEDGE_DEPTH, inner_at_y0=False)
    for a, b in FRONT_SHORT:
        m = m + wedge_xz(bx(a), bx(b), Y_F_IN - 0.3, Y_FRONT + SHORT_DEPTH, inner_at_y0=False)
    # PCB リップをボトムプレートまで下ろす（中央の切り欠きは残す）
    lip = prism_yz(front_pcb_lip().union(sg.box(Y_F_IN - 0.3, WZ[0], Y_FRONT + 1.0, PCB_LIP[1])), G_X0, G_X1)
    lip = lip - box(NOTCH[0], -5, -5, NOTCH[1], 20, 20)
    return m + lip

def rear_guard():
    m = prism_yz(rear_profile_flat(), G_X0, G_X1)
    for xc in USB_X:
        m = m - box(xc - USB_W/2, Y_R_IN - 1.0, USB_Z0, xc + USB_W/2, Y_R_OUT + 2, USB_Z1)
    for a, b in REAR_WEDGES:
        m = m + wedge_xz(bx(a), bx(b), Y_REAR - WEDGE_DEPTH, Y_R_IN + 0.3, inner_at_y0=True)
    y0, y1 = Y_REAR - NOTCH_DEPTH + KEY_CLR_WALL, Y_REAR - 0.05
    for a, b in PLATE_NOTCH_X:
        xa, xb = bx(a), bx(b); xc = (xa + xb) / 2
        for k0, k1 in ((xa + KEY_CLR_WALL, xc - USB_BODY_HALF - KEY_CLR_USB), (xc + USB_BODY_HALF + KEY_CLR_USB, xb - KEY_CLR_WALL)):
            m = m + box(k0, y0, USB_Z0 - 0.05, k1, y1, KEY_TOP)
    return m

def diag(t):
    """ベッドに斜め 45° で置く"""
    t = t.copy(); t.apply_transform(trimesh.transformations.rotation_matrix(math.pi/4, [0, 0, 1]))
    t.apply_translation(-t.bounds[0]); e = t.extents
    t.apply_translation([(BED - e[0])/2, (BED - e[1])/2, 0]); return t

# ============================================================================
# 縦置きスタンド（左端専用）
#   座標: u = キーボード Y（手前 -> 奥）, v = キーボード Z（フィン側 -> キー側）, w = 上（= 足の端からのキーボード X）
# ============================================================================
ST_POCKET_D = 10.0         # 足を差し込む深さ（足の長さは 10.5）
ST_DIA = 74.0              # 台座の直径
ST_CENTER = (41.0, 9.0)    # 台座の中心
ST_DISC_T = 4.0            # 台座の厚さ（足の端がこの上面に乗る）
ST_CHAMFER = 1.0           # 台座上面の面取り
ST_CLR = 0.15              # 足のポケットのすき間
ST_COLLAR_T = 3.0          # フィン側の壁の厚さ
ST_H_COLLAR = 9.0          # フィン側の壁の高さ
ST_LOW_FROM_V = 6.0        # v がこれより大きい側（キー側）には壁なし
ST_KEY_CLR = 0.4           # 位置決め突起のすき間
ST_KEY_H = 10.0            # 位置決め突起の高さ（足の肉抜き穴に入る）
ST_EDGE = 2.0              # 立ち上がり部分は台座の縁からこれだけ内側で止める
ST_R_END = 1.0             # 立ち上がり部分の端の丸め
STEP_V0, STEP_T = 9.6, 2.7                       # キー側の段（トッププレート上面 9.6 に当たる）
STEP_H = 4.6                                     # 段の高さ（1u スイッチは X~5.5 から）
ENC_U, STEP_H_ENC = (58.0, 80.0), 4.2            # エンコーダー部
SHIFT_U, STEP_H_SHIFT = (22.6, 38.4), 9.0        # 左の 1.5u Shift 列（スイッチは X~10.3 から）

def foot_outline():
    f = foot_left() ^ box(-1, -50, -50, ST_POCKET_D, 150, 50)
    cs = f.transform([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]]).project()
    polys = [sg.Polygon(p) for p in cs.to_polygons()]
    u = so.unary_union([p for p in polys if p.area > 0])
    return sg.Polygon(u.exterior) if u.geom_type == 'Polygon' else sg.Polygon(max(u.geoms, key=lambda g: g.area).exterior)

def rnd(p, r=ST_R_END):
    return p.buffer(-r, join_style=1, resolution=24).buffer(r, join_style=1, resolution=24)

def stand():
    o = foot_outline()
    pocket = o.buffer(ST_CLR, join_style=1, resolution=24)
    disc = sg.Point(ST_CENTER).buffer(ST_DIA/2, resolution=192)
    inner = disc.buffer(-ST_EDGE, resolution=192)
    T, C = ST_DISC_T, ST_CHAMFER
    m = ext(disc, 0, T - C) + ext(sg.Point(ST_CENTER).buffer(ST_DIA/2 - C*0.5, resolution=192), T - C, T - C*0.5) \
        + ext(sg.Point(ST_CENTER).buffer(ST_DIA/2 - C, resolution=192), T - C*0.5, T)
    # フィン側の壁
    collar = pocket.buffer(ST_COLLAR_T, join_style=1, resolution=24).difference(pocket)
    collar = rnd(collar.intersection(sg.box(-500, -500, 500, ST_LOW_FROM_V)).intersection(inner))
    m = m + ext(collar, T - 0.01, T + ST_H_COLLAR)
    # 肉抜き穴に入る位置決め突起
    hole = opn(sg.Polygon(HOLE), R_HOLE)
    key = rnd(hole.buffer(-ST_KEY_CLR, join_style=1, resolution=24).intersection(inner))
    m = m + ext(key, T - 0.01, T + ST_KEY_H)
    # キー側の段（エンコーダー / Shift の位置で高さを変える）
    rail = sg.box(-500, STEP_V0, 500, STEP_V0 + STEP_T).intersection(inner).difference(pocket)
    enc = sg.box(ENC_U[0], -500, ENC_U[1], 500); sh = sg.box(SHIFT_U[0], -500, SHIFT_U[1], 500)
    m = m + ext(rnd(rail), T - 0.01, T + STEP_H_ENC)
    m = m + ext(rnd(rail.difference(enc).difference(sh)), T + STEP_H_ENC - 0.01, T + STEP_H)
    m = m + ext(rnd(rail.intersection(sh)), T + STEP_H_ENC - 0.01, T + STEP_H_SHIFT)
    return m

# ============================================================================
# 書き出し
# ============================================================================
def export_feet(out):
    info = {}
    t = to_tm(foot_left())
    t.apply_transform(K2P)
    tr = t.copy(); tr.vertices[:, 0] = FOOT_PX_MAX - tr.vertices[:, 0]; tr.invert()
    for name, m in (('foot-L', t), ('foot-R', tr)):
        m.apply_translation(-m.bounds[0]); m.export(f'{out}/ogm10-Jupiter-{name}.stl')
        r = trimesh.load(f'{out}/ogm10-Jupiter-{name}.stl')            # STL の float32 化で出る細い三角形を掃除
        r.merge_vertices(digits_vertex=5); r.update_faces(r.nondegenerate_faces(height=1e-6)); r.remove_unreferenced_vertices()
        r.export(f'{out}/ogm10-Jupiter-{name}.stl'); r = trimesh.load(f'{out}/ogm10-Jupiter-{name}.stl')
        info[name] = dict(size=np.round(r.extents, 2).tolist(), watertight=bool(r.is_watertight), bodies=int(r.body_count))
    return info

def export_guards(out):
    info = {}
    fg = to_tm(front_guard()); fg.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [1, 0, 0]))
    rg = to_tm(rear_guard()); rg.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/2, [1, 0, 0]))   # USB 面を下
    for name, t in (('guard-front', fg), ('guard-rear', rg)):
        t.apply_translation(-t.bounds[0]); part = np.round(t.extents, 2).tolist(); t = diag(t)
        t.export(f'{out}/ogm10-Jupiter-{name}.stl')
        info[name] = dict(part=part, bed=np.round(t.extents, 1).tolist(), watertight=bool(t.is_watertight), bodies=int(t.body_count))
    return info

def export_stand(out):
    t = to_tm(stand()); t.merge_vertices(digits_vertex=5); t.apply_translation(-t.bounds[0]); t.export(f'{out}/ogm10-Jupiter-stand.stl')
    return {'stand': dict(size=np.round(t.extents, 2).tolist(), watertight=bool(t.is_watertight), bodies=int(t.body_count))}

def export(out):
    info = export_feet(out)
    info.update(export_guards(out))
    info.update(export_stand(out))
    return info

if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
