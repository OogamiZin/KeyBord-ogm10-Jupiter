# ogm10-Jupiter side guard v28 = v27 with the front-guard spacer snaps removed
#  the short wedges (2.6mm) now also run through the places the snaps used to take
import sys, json
import gen_v27 as Z27, gen_v26 as Z26, gen_v12 as V12

V12.SPACERS = []                                  # no spacer snap rings on the front guard
Z26.FRONT_SHORT = [(22.7, 38.5), (46.5, 57.5), (65.5, 81.3), (89.3, 105.1), (127.6, 133.7), (141.7, 157.5),
                   (165.5, 186.1), (194.1, 205.2), (213.2, 224.2)]

if __name__ == '__main__':
    print(json.dumps(Z26.Q.P.export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
