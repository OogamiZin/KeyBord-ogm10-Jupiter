import sys, itertools, warnings; warnings.filterwarnings("ignore")
import gen_keycaps as K   # usage: python3 check_layout.py mx
from shapely.geometry import box
v=sys.argv[1]
W1,D1,pitch=(18,18,19.05) if v=="mx" else (17.5,16.5,18)
bad=0
for k in K.KEYS:
    W=W1+(k["w"]-1)*pitch-2*K.TAPER; Dt=D1-2*K.TAPER
    area=box(-W/2+K.CHAMFER+0.3,-Dt/2+K.CHAMFER+0.3,W/2-K.CHAMFER-0.3,Dt/2-K.CHAMFER-0.3)
    items=[]
    for it in k["L"]:
        kk=dict(k); kk["L"]=[it]
        g=list(K.legend_layers(kk,W1-2*K.TAPER,D1-2*K.TAPER).values())[0]
        items.append((it[1] or it[0],g))
        if not g.within(area): print("OUT",k["L"][0][1],it[1]); bad+=1
    for (a,ga),(b,gb) in itertools.combinations(items,2):
        d=ga.distance(gb)
        if d<0.5: print("CLOSE",k["L"][0][1],repr(a),repr(b),round(d,2)); bad+=1
print(v,"issues",bad)
