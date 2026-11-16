# ogm10-Jupiter side guard v31 = v30 with the rear-guard PCB/bottom-plate wedges beside the USB-C ports removed
#   (the board is now fixed with resin near the ports; those wedges could stop the guard from going on)
#   the USB-notch keys (v27) and the wedges away from the ports stay
import sys, json
import gen_v30, gen_v27 as Z27, gen_v26 as Z26

W = Z27.W
USB_X = [41.44, 155.74, 174.79, 193.84]                       # USB-C centres (board x)
# v23 list: (48.3,51.0) right of USB1, (162.7,167.8) USB2|USB3, (181.7,186.9) USB3|USB4, (200.8,212.4) right of USB4 -> removed
W.REAR_WEDGES = [(62.0, 129.5), (132.8, 136.6)]

if __name__ == '__main__':
    print(json.dumps(Z26.Q.P.export(sys.argv[1] if len(sys.argv) > 1 else '.'), indent=1))
