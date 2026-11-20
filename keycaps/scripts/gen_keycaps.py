"""ogm10-Jupiter keycap set generator (MX-size 18x18 mm caps for Kailh Choc V2 / MX cross stems).

usage:  python3 gen_keycaps.py OUTDIR
writes: OUTDIR/ogm10-Jupiter-keycaps-{cream,gray,dark}-{2color,fullcolor}.3mf
        OUTDIR/ogm10-Jupiter-keycap-cross-fit-test.stl
        OUTDIR/keycaps-preview.png
deps:   pip install numpy opencv-python-headless trimesh manifold3d shapely matplotlib
"""
import os, sys, json, zipfile, numpy as np, cv2, trimesh
import manifold3d as m3
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = FontProperties(fname=os.path.join(HERE, "fonts", "Oswald-SemiBold.ttf"))          # main legends
LOGO_IMG = os.path.join(HERE, "logo.png")

SKIRT, TOP = 3.0, 1.6
H = SKIRT + TOP
WALL, R, CHAMFER, DEBOSS = 1.2, 1.6, 0.5, 0.6
THICKEN = 0.0
TAPER = 1.0        # side taper per side (mm) -> trapezoid profile
STEM_D, CROSS_L, CROSS_W = 5.5, 4.05, 1.20
HOMING = (4.0, 0.8, 0.5)  # w, d, height

# ---------------- glyph helpers ----------------
def _rings_to_geom(rings):
    g = Polygon()
    for r in rings:
        if len(r) >= 3:
            p = Polygon(r).buffer(0)
            g = g.symmetric_difference(p)
    return g

SMALL_PUNCT = set("~^\"'`*,.:;_-")
SMALL_PUNCT_SCALE = 1.4
FONT_SUB = FontProperties(fname=os.path.join(HERE, "fonts", "JetBrainsMono-ExtraBold.ttf"))  # small legends
_caph = {}
def cap_height(fp=None):
    fp = fp or FONT
    k = fp.get_file()
    if k not in _caph:
        _caph[k] = TextPath((0, 0), "H", size=1, prop=fp).vertices[:, 1].max()
    return _caph[k]

def text_geom(s, h, x, y, align="c"):
    """h = cap height (mm); (x,y) = cap-height center; align horizontal."""
    fp = FONT_SUB if h <= 3.0 else FONT     # small (green / orange) legends: JetBrains Mono ExtraBold
    size = h / cap_height(fp)
    tp = TextPath((0, 0), s, size=size, prop=fp)
    g = _rings_to_geom(tp.to_polygons())
    if fp is FONT_SUB and "0" in s and hasattr(g, "geoms"):
        # plain zero: drop the dot that sits inside the 0's counter
        parts = list(g.geoms)
        keep = [p for p in parts if not any(q is not p and p.within(Polygon(q.exterior)) for q in parts)]
        g = unary_union(keep)
    if fp is FONT_SUB and s in SMALL_PUNCT:
        c = g.centroid
        g = affinity.scale(g, SMALL_PUNCT_SCALE, SMALL_PUNCT_SCALE, origin=(c.x, c.y))
    minx, _, maxx, _ = g.bounds
    if align == "c": dx = x - (minx + maxx) / 2
    elif align == "l": dx = x - minx
    else: dx = x - maxx
    return affinity.translate(g, dx, y - h / 2)

def arrow_geom(direction, x, y, L=6.5, head=4.6, shaft=1.9):
    hl = head * 0.62
    pts = [(-L/2, -shaft/2), (L/2 - hl, -shaft/2), (L/2 - hl, -head/2), (L/2, 0),
           (L/2 - hl, head/2), (L/2 - hl, shaft/2), (-L/2, shaft/2)]
    g = Polygon(pts)
    ang = {"right": 0, "up": 90, "left": 180, "down": 270}[direction]
    g = affinity.rotate(g, ang, origin=(0, 0))
    return affinity.translate(g, x, y)

def dot_geom(x, y, d=2.2):
    return Point(x, y).buffer(d / 2, 48)

_logo = None
def logo_geom(x, y, size):
    global _logo
    if _logo is None:
        img = cv2.imread(LOGO_IMG, cv2.IMREAD_GRAYSCALE)
        _, bw = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV)
        cnts, hier = cv2.findContours(bw, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        hier = hier[0]; polys = []
        for i, c in enumerate(cnts):
            if hier[i][3] != -1: continue
            outer = cv2.approxPolyDP(c, 1.5, True)[:, 0, :]
            holes = []; j = hier[i][2]
            while j != -1:
                hh = cv2.approxPolyDP(cnts[j], 1.5, True)[:, 0, :]
                if len(hh) >= 3 and cv2.contourArea(hh) > 30: holes.append(hh)
                j = hier[j][0]
            if len(outer) >= 3:
                p = Polygon(outer, holes).buffer(0)
                if p.area > 50: polys.append(p)
        g = unary_union(polys)
        g = affinity.scale(g, 1, -1, origin=(0, 0))
        minx, miny, maxx, maxy = g.bounds
        g = affinity.translate(g, -(minx + maxx) / 2, -(miny + maxy) / 2)
        _logo = (g, max(maxx - minx, maxy - miny))
    g, ext = _logo
    s = size / ext
    return affinity.translate(affinity.scale(g, s, s, origin=(0, 0)), x, y)

# ---------------- layout (from the reference image) ----------------
# positions are fractions of a 1u key (x right, y up), legends: (kind, text, color, fx, fy, height, align)
MAIN, MOD, SUB, LAY = 5.0, 4.0, 3.0, 2.8
TR = (0.36, 0.33)   # orange top-right (right aligned)
def alpha(ch, sub=None, side="l", lay=None, fn=None, fnside="l", homing=False):
    L = [("t", ch, "main", 0, 0.22 if side == "c" else 0.05, MAIN, "c")]
    if sub:
        fx = -0.32 if side == "l" else (0.32 if side == "r" else 0)
        ys = (0.03, -0.27) if side != "c" else (-0.08, -0.30)
        L += [("t", sub[0], "green", fx, ys[0], SUB, "c"), ("t", sub[1], "green", fx, ys[1], SUB, "c")]
    if lay: L.append(("t", lay, "orange", TR[0], TR[1], LAY, "r"))
    if fn:
        L.append(("t", fn, "green", -0.38 if fnside == "l" else 0.36, -0.29, SUB, "l" if fnside == "l" else "r"))
    return dict(L=L, homing=homing)

KEYS = []  # (row, col_u, width_u, body, legends dict)
def add(row, col, w, body, spec): KEYS.append(dict(row=row, col=col, w=w, body=body, **spec))
# row 0
r0 = [("Q",None,"F1","l"),("W",None,"F2","l"),("E",None,"F3","l"),("R",None,"F4","l"),("T",None,"F5","l"),
      ("Y","F6","F7","r"),("U",None,"F8","r"),("I","INS","F9","r"),("O",None,"F10","r"),("P","F12","F11","r")]
for i,(ch,lay,fn,fs) in enumerate(r0):
    add(0, 0.75 + i, 1, "cream", alpha(ch, lay=lay, fn=fn, fnside=fs))
# row 1
add(1, 0, 1, "gray", dict(L=[("t","Z/H","orange",-0.38,0.28,LAY,"l"),("t","TAB","main",-0.06,-0.02,MOD,"c"),
                             ("t","ESC","green",-0.38,-0.29,SUB,"l")], homing=False))
r1 = [("A","!1","l"),("S","\"2","l"),("D","#3","l"),("F","$4","l"),("G","%5","l"),
      ("H","&6","r"),("J","'7","r"),("K","(8","r"),("L",")9","r")]
for i,(ch,s,sd) in enumerate(r1):
    add(1, 1 + i, 1, "cream", alpha(ch, sub=s, side=sd, homing=ch in "FJ"))
add(1, 10, 1, "cream", dict(L=[("t","=","main",-0.06,0.18,MAIN*0.8,"c",(2.6,1.4)),("t","-","main",-0.06,-0.18,MAIN*0.8,"c",(3.2,1.6)),
                              ("t","_","orange",0.30,0.20,LAY,"c",(1.0,1.3)),("t","0","green",0.32,-0.29,SUB,"c")], homing=False))
add(1, 11, 1, "gray", dict(L=[("t","BKSP","main",0.38,-0.02,MOD,"r"),("t","DEL","green",0.38,-0.29,SUB,"r")], homing=False))
# row 2
add(2, 0, 1.5, "gray", dict(L=[("t","SHIFT","main",-0.54,-0.08,MOD,"l")], homing=False))
r2 = [("Z","~^","l"),("X","|¥","l"),("C","{[","l"),("V","}]","l"),("B","+;","l"),("N","*:","r")]
for i,(ch,s,sd) in enumerate(r2):
    add(2, 1.5 + i, 1, "cream", alpha(ch, sub=s, side=sd))
m = alpha("M", sub="?/", side="r", lay="MENU"); m["L"].append(("d", None, "green", 0.12, -0.27, 1.5, None))
add(2, 7.5, 1, "cream", m)
add(2, 8.5, 1, "cream", dict(L=[("t","<","main",-0.06,0.18,MAIN*0.75,"c",(1.8,1.8)),("t",",","main",-0.06,-0.18,MAIN*0.75,"c",(1.8,1.8)),
                               ("t",">","green",0.32,0.03,SUB,"c",(1.3,1.3)),("t",".","green",0.32,-0.27,SUB,"c",(1.4,1.4))], homing=False))
add(2, 10, 1, "gray", dict(L=[("t","PGUP","orange",TR[0],TR[1],LAY,"r"),("a","up","main",0,-0.02,None,None)], homing=False))
add(2, 11, 1, "black", dict(L=[("t","`","white",0,0.25,MAIN*0.85,"c",(1.6,1.6)),("t","@","white",0,-0.12,MAIN*1.15,"c"),
                              ("d",None,"orange",0.30,0.28,3.6,None)], homing=False))
# row 3
add(3, 0, 1, "gray", dict(L=[("t","CAPS","orange",-0.38,0.28,LAY,"l"),("t","CTRL","main",-0.38,-0.04,MOD,"l")], homing=False))
add(3, 1.25, 1, "gray", dict(L=[("l",None,"main",0,0,6.5,None)], homing=False))
add(3, 2.25, 1, "gray", dict(L=[("t","ALT","main",-0.09,-0.08,MOD,"c")], homing=False))
add(3, 3.5, 1, "black", dict(L=[("t","ASC","white",-0.04,0.02,MOD,"c"),("d",None,"green",-0.32,-0.30,3.6,None)], homing=False))
add(3, 4.5, 1.5, "gray", dict(L=[("t","SPACE","main",-0.54,-0.08,MOD,"l")], homing=False))
add(3, 6.0, 1.5, "gray", dict(L=[("t","ENTER","main",0.54,-0.08,MOD,"r")], homing=False))
add(3, 7.5, 1, "black", dict(L=[("t","JIS","white",0.04,0.02,MOD,"c"),("d",None,"green",0.32,-0.30,3.6,None)], homing=False))
for i,(lab,d) in enumerate([("HOME","left"),("PGDN","down"),("END","right")]):
    add(3, 9 + i, 1, "gray", dict(L=[("t",lab,"orange",TR[0],TR[1],LAY,"r"),("a",d,"main",0,-0.02,None,None)], homing=False))

# ---------------- geometry ----------------
def rrect(w, d, r):
    return m3.CrossSection.square((w - 2*r, d - 2*r), center=True).offset(r, m3.JoinType.Round, circular_segments=48)

def to_cs(geom):
    loops = []
    for g in (geom.geoms if hasattr(geom, "geoms") else [geom]):
        if g.is_empty: continue
        for ring in [g.exterior] + list(g.interiors):
            loops.append([tuple(p) for p in list(ring.coords)[:-1]])
    return m3.CrossSection(loops, m3.FillRule.EvenOdd)

def legend_layers(key, W1, D1):
    """returns {color: shapely geom} in key-local mm coords"""
    out = {}
    for item in key["L"]:
        kind, txt, col, fx, fy, h, al = item[:7]
        st = item[7] if len(item) > 7 else None      # optional (sx, sy) stretch for small symbols
        x, y = fx * W1, fy * D1
        if kind == "t":
            g = text_geom(txt, h, x, y, al)
            if st:
                c = g.centroid
                g = affinity.scale(g, st[0], st[1], origin=(c.x, c.y))
            if h < 2.6 and THICKEN > 0: g = g.buffer(THICKEN, join_style=2)
        elif kind == "a": g = arrow_geom(txt, x, y)
        elif kind == "d": g = dot_geom(x, y, h)
        elif kind == "l": g = logo_geom(x, y, h)
        out[col] = unary_union([out[col], g]) if col in out else g
    return out

def build_key(key, W1, D1, pitch):
    W = W1 + (key["w"] - 1) * pitch
    D = D1
    # trapezoid side profile: sides taper inward by TAPER from the bottom edge to the top
    T = TAPER
    zt = H - CHAMFER
    slope = T / zt
    Wt, Dt = W - 2*T, D - 2*T
    def slab(w, d, r, z):
        return rrect(w, d, r).extrude(0.001).translate((0, 0, z - 0.001))
    body = m3.Manifold.batch_hull([rrect(W, D, R).extrude(0.001),
                                   slab(Wt, Dt, R, zt),
                                   slab(Wt - 2*CHAMFER, Dt - 2*CHAMFER, R - CHAMFER, H)])
    ins_top = WALL + slope * SKIRT
    cavity = m3.Manifold.batch_hull([
        rrect(W - 2*(WALL - slope), D - 2*(WALL - slope), 0.5).extrude(0.001).translate((0, 0, -1)),
        slab(W - 2*ins_top, D - 2*ins_top, 0.5, SKIRT)])
    stem = m3.Manifold.cylinder(SKIRT + 0.01, STEM_D/2, STEM_D/2, 64)
    cross = (m3.CrossSection.square((CROSS_L, CROSS_W), center=True) +
             m3.CrossSection.square((CROSS_W, CROSS_L), center=True)).extrude(SKIRT + 1).translate((0, 0, -1))
    cap = (body - cavity) + (stem - cross)
    if key["homing"]:
        w, d, hh = HOMING
        bar = rrect(w, d, d/2 - 0.01).extrude(hh).translate((0, -0.29 * (D1 - 2*TAPER), H))
        cap = cap + bar
    layers = legend_layers(key, W1 - 2*TAPER, D1 - 2*TAPER)   # legend positions relative to the (smaller) top
    top_area = Polygon(box(-Wt/2 + CHAMFER + 0.3, -Dt/2 + CHAMFER + 0.3, Wt/2 - CHAMFER - 0.3, Dt/2 - CHAMFER - 0.3))
    inlays = {}
    for col, g in layers.items():
        if not g.within(top_area):
            print("WARN legend outside top:", key["L"][0][1], col)
        g = g.intersection(top_area)
        cs = to_cs(g)
        cap = cap - cs.extrude(DEBOSS + 1).translate((0, 0, H - DEBOSS))
        inlays[col] = cs.extrude(DEBOSS).translate((0, 0, H - DEBOSS))
    return cap, inlays, W, D, layers

def tm(mf):
    mesh = mf.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts))

# ---------------- 3MF writer (standard core + basematerials) ----------------
def write_3mf(path, items, palette):
    """items: list of (name, [(trimesh, color_name)], (tx,ty))"""
    names = list(palette)
    mats = "".join(f'<base name="{n}" displaycolor="{palette[n]}FF"/>' for n in names)
    objs, comps_xml, build = [], [], []
    oid = 100
    for name, parts, (tx, ty) in items:
        cids = []
        for mesh, col in parts:
            oid += 1
            v = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in mesh.vertices)
            t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh.faces)
            objs.append(f'<object id="{oid}" type="model" name="{name}_{col}" pid="10" pindex="{names.index(col)}">'
                        f'<mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')
            cids.append(oid)
        oid += 1
        objs.append(f'<object id="{oid}" type="model" name="{name}"><components>' +
                    "".join(f'<component objectid="{c}"/>' for c in cids) + '</components></object>')
        build.append(f'<item objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 {tx:.3f} {ty:.3f} 0"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>'
             f'<basematerials id="10">{mats}</basematerials>' + "".join(objs) +
             '</resources><build>' + "".join(build) + '</build></model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels); z.writestr("3D/3dmodel.model", model)

FULL = {"cream": "#EDEBE3", "gray": "#C9C3C1", "black": "#262626",
        "main": "#262626", "white": "#F5F5F5", "green": "#5DBF9E", "orange": "#F08C32"}
TWO = {"body_white": "#FFFFFF", "body_black": "#000000"}
def two_color(c, body):
    if c in ("cream", "gray"): return "body_white"
    if c == "black": return "body_black"
    # legends: contrast with body
    return "body_white" if body == "black" else "body_black"

def preview(built, path, pitch=19.05):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(16, 5.5))
    def fill(g, c, bg):
        for p in (g.geoms if hasattr(g, "geoms") else [g]):
            if p.is_empty: continue
            x, y = p.exterior.xy; ax.fill(x, y, color=c, lw=0)
            for h in p.interiors: x, y = h.xy; ax.fill(x, y, color=bg, lw=0)
    for k, _, _, W, D, layers in built:
        cx = k["col"] * pitch + k["w"] * pitch / 2; cy = -k["row"] * pitch
        bg = FULL[k["body"]]
        fill(box(cx - W/2, cy - D/2, cx + W/2, cy + D/2), bg, bg)
        for c, g in layers.items(): fill(affinity.translate(g, cx, cy), FULL[c], bg)
    ax.set_aspect("equal"); ax.axis("off"); plt.tight_layout(); plt.savefig(path, dpi=110)

def cross_fit_test(W1, D1, pitch):
    """five blank caps, cross width 1.10-1.30 mm, numbered 1-5 on the top"""
    global CROSS_W, CROSS_L
    keep = (CROSS_W, CROSS_L); meshes = []; x = 0
    for i, w in enumerate([1.10, 1.15, 1.20, 1.25, 1.30]):
        CROSS_W, CROSS_L = w, 4.0 + (w - 1.15)
        key = dict(row=0, col=0, w=1, body="cream", homing=False,
                   L=[("t", str(i + 1), "main", 0, 0.12, 5.0, "c"), ("t", f"{w:.2f}", "main", 0, -0.27, 3.0, "c")])
        cap, _, W, _, _ = build_key(key, W1, D1, pitch)
        m = tm(cap); m.apply_translation([x + W/2, 0, 0]); x += W + 4; meshes.append(m)
    CROSS_W, CROSS_L = keep
    return trimesh.util.concatenate(meshes)

if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    W1, D1, pitch = 18.0, 18.0, 19.05
    built = []
    for i, k in enumerate(KEYS):
        cap, inlays, W, D, layers = build_key(k, W1, D1, pitch)
        built.append((k, tm(cap), {c: tm(m) for c, m in inlays.items()}, W, D, layers))
        assert built[-1][1].is_watertight
    # one plate per body colour, centred for a 180 mm bed (A1 mini / P1S)
    def pack(sel):
        pos, x, y, rowh, gap = [], 0, 0, 0, 3.0
        for b in sel:
            W, D = b[3], b[4]
            if x + W > 170: x, y = 0, y + rowh + gap; rowh = 0
            pos.append((x + W/2, y + D/2)); x += W + gap; rowh = max(rowh, D)
        maxx = max(p[0] + b[3]/2 for p, b in zip(pos, sel)); maxy = max(p[1] + b[4]/2 for p, b in zip(pos, sel))
        return [(px + 90 - maxx/2, py + 90 - maxy/2) for px, py in pos], maxx, maxy
    for plate, sel in [("cream", [b for b in built if b[0]["body"] == "cream"]),
                       ("gray", [b for b in built if b[0]["body"] == "gray"]),
                       ("dark", [b for b in built if b[0]["body"] == "black"])]:
        pos, mx_, my_ = pack(sel)
        print(plate, len(sel), "keys, footprint", round(mx_, 1), "x", round(my_, 1))
        for mode, pal in [("2color", TWO), ("fullcolor", FULL)]:
            items = []
            for (k, capm, inl, W, D, _), p in zip(sel, pos):
                bcol = k["body"] if mode == "fullcolor" else two_color(k["body"], k["body"])
                parts = [(capm, bcol)]
                merged = {}
                for c, mm in inl.items():
                    cc = c if mode == "fullcolor" else two_color(c, k["body"])
                    merged.setdefault(cc, []).append(mm)
                for cc, ms in merged.items():
                    parts.append((trimesh.util.concatenate(ms), cc))
                name = "".join(ch for ch in (k["L"][0][1] or "logo") if ch.isalnum()) or "key"
                items.append((name, parts, p))
            used = {c for _, parts, _ in items for _, c in parts}
            write_3mf(f"{outdir}/ogm10-Jupiter-keycaps-{plate}-{mode}.3mf", items, {c: pal[c] for c in pal if c in used})
    cross_fit_test(W1, D1, pitch).export(f"{outdir}/ogm10-Jupiter-keycap-cross-fit-test.stl")
    preview(built, f"{outdir}/keycaps-preview.png")
