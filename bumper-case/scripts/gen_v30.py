# ogm10-Jupiter side guard v30 = v29 rebuilt: the raised end wall is part of the foot section itself (no added block, no seams)
import sys, json
import gen_v28, gen_v26 as Z26, gen_v30_base as B
Z26.Q.P.N.V = B

if __name__ == '__main__':
    print(json.dumps(Z26.Q.P.export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
