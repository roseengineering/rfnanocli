#!/usr/bin/python3

import numpy as np
import serial, os, sys
from serial.tools import list_ports
from struct import pack, unpack_from

# defaults

FSTART = 100e3
FSTOP = 10.1e6
POINTS = 101
SAMPLES = 3
CALFILE = 'cal'
 
FORMAT_TEXT = ' {:25.6g} {:25.6g}'
FORMAT_DB   = ' {:11.3f} {:9.3f}'
FORMAT_MAG  = ' {:14.5g} {:9.3f}'

# supported calibrations

CALIBRATIONS = [ 'open', 'short', 'load', 'thru' ]


def parse_args():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('command', metavar='command', nargs='*', help='command')
    # calibration flags
    parser.add_argument('-i', '--init', action='store_true', help='initialize calibration')
    parser.add_argument('-o', '--open', action='store_true', help='open calibration')
    parser.add_argument('-s', '--short', action='store_true', help='short calibration')
    parser.add_argument('-l', '--load', action='store_true', help='load calibration')
    parser.add_argument('-t', '--thru', action='store_true', help='thru calibration')
    # other flags
    parser.add_argument('-d', '--details',  action='store_true', help='show calibration details')
    parser.add_argument('-r', '--raw', action='store_true', help='do not apply calibration')
    parser.add_argument('-1', '--one-port',  action='store_true', help='output in s1p format')
    parser.add_argument('--db', action='store_true', help='show in dB')
    parser.add_argument('--average', action='store_true', help='take average of samples, not median')
    # value options 
    parser.add_argument('-f', '--filename', default=CALFILE, help='calibration file')
    parser.add_argument('-n', '--samples', default=SAMPLES, type=int, help='samples per frequency')
    parser.add_argument('--device', type=int, help='select device number')
    parser.add_argument('--start', type=float, help='start frequency (Hz)')
    parser.add_argument('--stop', type=float, help='stop frequency (Hz)')
    parser.add_argument('--points', type=int, help='frequency points')
    args = parser.parse_args()
    return args


###############################

def nanovna(dev):
    def send(ser, cmd):
        cmd += '\r'
        ser.write(cmd.encode())
        ser.readline()

    def read(ser):
        result = ''
        line = ''
        while True:
            c = ser.read().decode('utf-8')
            if c == chr(13):
                next
            line += c
            if c == chr(10):
                result += line
                line = ''
                next
            if line.endswith('ch>'):
                break
        return result.strip()

    def command(ser, buf):
        send(ser, buf)
        return read(ser)

    def clear_state(ser):
        text = command(ser, "help")
        if text[:9] != 'Commands:': 
            text = read(ser)

    def scan(ser, start, stop, points):
        freq = np.linspace(start, stop, points)
        cmd = "scan {:d} {:d} {:d} 111".format(start, stop, points)
        text = command(ser, cmd)
        d = np.array([[ float(c) for c in ln.split() ] for ln in text.split('\n') ])
        assert(np.all(freq == d[:,0]))
        return d[:,1::2] + 1j * d[:,2::2]


    def sweep(start, stop, points, samples):
        start, stop, points = int(start), int(stop), int(points)
        assert(stop > start)
        assert(points > 1)
        # points should also be <= 101, but dislord extended it to 301
        assert(start >= 6348 and stop <= 2.7e9)
        # since Si5351 multisynth divider ratio < 2048, 6348 is the min freq:
        # 26000000 {xtal} * 32 {pll_n} / (6348 {freq} << 6 {rdiv}) = 2047.9
        freq = np.linspace(start, stop, points)
        data = []
        ser = serial.Serial(dev)
        clear_state(ser)
        command(ser, "cal off")
        for i in range(samples):
            d = scan(ser, start=start, stop=stop, points=points)
            data.append(d)
        command(ser, "resume")  # resume and update sweep frequencies without calibration
        command(ser, "cal on")
        ser.close()
        return freq, data

    return sweep


def saa2(dev):

    # most of this saa2 code was taken from nanovna-saver
    # the si5351 is used up to 140Mhz

    CMD_READFIFO = 0x18
    CMD_WRITE = 0x20
    CMD_WRITE2 = 0x21
    CMD_WRITE8 = 0x23
    CMD_WRITEFIFO = 0x28

    ADDR_SWEEP_START = 0x00
    ADDR_SWEEP_STEP = 0x10
    ADDR_SWEEP_POINTS = 0x20
    ADDR_SWEEP_VALS_PER_FREQ = 0x22
    ADDR_RAW_SAMPLES_MODE = 0x26
    ADDR_VALUES_FIFO = 0x30

    def send(ser, cmd):
        ser.write(cmd)

    def set_sweep(ser, start, stop, points, samples):
        step = (stop - start) / (points - 1)
        cmd = pack("<BBQ", CMD_WRITE8, ADDR_SWEEP_START, int(start))
        cmd += pack("<BBQ", CMD_WRITE8, ADDR_SWEEP_STEP, int(step))
        cmd += pack("<BBH", CMD_WRITE2, ADDR_SWEEP_POINTS, int(points))
        cmd += pack("<BBH", CMD_WRITE2, ADDR_SWEEP_VALS_PER_FREQ, int(samples))
        send(ser, cmd)

    def clear_state(ser):
        cmd = pack("<Q", 0)
        send(ser, cmd)

    def clear_fifo(ser):
        cmd = pack("<BBB", CMD_WRITE, ADDR_VALUES_FIFO, 0)
        send(ser, cmd)

    def read_fifo(ser, n):
        cmd = pack("<BBB", CMD_READFIFO, ADDR_VALUES_FIFO, n)
        send(ser, cmd)
        return ser.read(32 * n)

    def exit_usbmode(ser):
        cmd = pack("<BBB", CMD_WRITE, ADDR_RAW_SAMPLES_MODE, 2)
        send(ser, cmd)

    def sweep(start, stop, points, samples):
        start, stop, points = int(start), int(stop), int(points)
        assert(stop > start)
        assert(start >= 10e3 and stop <= 4400e6)
        assert(points > 1 and points <= 255)
        freq = np.linspace(start, stop, points)
        data = []
        ser = serial.Serial(dev)
        try:
            for n in range(samples):
                clear_state(ser)
                set_sweep(ser, start, stop, points, 1)        
                clear_fifo(ser)
                fifo = read_fifo(ser, points)
                for i in range(points):
                    d = unpack_from("<iiiiiihxxxxxx", fifo, i * 32)
                    fwd = complex(d[0], d[1])
                    refl = complex(d[2], d[3])
                    thru = complex(d[4], d[5])
                    index = d[6]
                    assert(index == i)
                    data.append([ refl / fwd, thru / fwd ])
            data = np.reshape(data, (samples, points, 2))
        finally:
            exit_usbmode(ser)
            ser.close()
      
        return freq, data

    return sweep


###############################

DEVICES = {
    nanovna: [(0x0483, 0x5740)],
    saa2: [(0x04b4, 0x0008)]
};


def getport(devnum):
    device_list = list_ports.comports()
    d = []
    for device in device_list:
        for fn, address in DEVICES.items():
            if (device.vid, device.pid) in address:
                d.append((fn, device.device))
    if len(d) == 0:
        raise RuntimeError("NanoVNA device not found.")
    if len(d) > 1 and (devnum is None or devnum < 1 or devnum > len(d)):
        print("Which NanoVNA?  Use --device to select.", file=sys.stderr)
        for i in range(len(d)):
            print("{}. {}".format(i+1, d[i][1]), file=sys.stderr)
        sys.exit(1)
    fn, device = d[0 if devnum is None else devnum-1]
    return fn(device)


def calibrate(cal):
    # see Rytting, "Network analyzer error models and calibration methods", HP 1998
    # e30 assumed to be zero
    gms = cal.get("short", -1)
    gmo = cal.get("open", 1)
    gml = cal.get("load", 0)
    gmu = cal.get("thru", 0)
    gmu21 = cal.get("thru21", 1) # 0 causes nan results
    d = {}
    d['e00'] = gml
    d['e11'] = (gmo + gms - 2 * gml) / (gmo - gms)
    d['de'] = (2 * gmo * gms - gml * gms - gml * gmo) / (gmo - gms) 
    d['e10e01'] = d['e00'] * d['e11'] - d['de']
    d['e22'] = ((gmu - gml) / (gmu * d['e11'] - d['de']))
    d['e10e32'] = gmu21 * (1 - d['e11'] * d['e22'])
    return d


def cal_correct(cal, data):
    d = calibrate(cal)
    S11M = data[:,0]
    S21M = data[:,1]
    S11 = (S11M - d['e00']) / (S11M * d['e11'] - d['de'])
    S21 = S21M / d['e10e32'] * d['e10e01'] / (d['e11'] * S11M - d['de'])
    return np.array([ S11, S21 ]).T


def cal_interpolate(cal, start, stop, points):
    freq = np.linspace(cal['start'], cal['stop'], cal['points'])
    cal['start'] = start or cal['start']
    cal['stop'] = stop or cal['stop'] 
    cal['points'] = points or cal['points']
    freq_new = np.linspace(cal['start'], cal['stop'], cal['points'])
    for name in cal.keys():
        data = cal[name]
        if np.ndim(data) and data.size > 1:
            cal[name] = np.interp(freq_new, freq, data)
    return cal


def cal_init(filename, start, stop, points):
    start = start or FSTART
    stop = stop or FSTOP
    points = points or POINTS
    np.savez(filename, start=start, stop=stop, points=points)


def cal_load(filename):
    try:
        name, ext = os.path.splitext(filename)
        npzfile = np.load('{}{}'.format(name, ext or '.npz'))
    except FileNotFoundError:
        raise RuntimeError('No calibration file, please initialize.')
    return dict(npzfile)


def measure(cal, samples, average, device):
    start = cal['start']
    stop = cal['stop']
    points = cal['points']
    sweep = getport(device)
    freq, data = sweep(start, stop, points, samples)
    if average:
        data = np.average(data, axis=0)
    else:
        data = np.median(data, axis=0)
    return freq, data


def details(cal):
    print('start:  {:.6g} MHz'.format(cal['start'] / 1e6))
    print('stop:   {:.6g} MHz'.format(cal['stop'] / 1e6))
    print('points: {:d}'.format(cal['points']))
    units = [ d for d in CALIBRATIONS if d in cal ]
    print('cals:   {}'.format(', '.join(units) if units else '<none>'))


def show_touchstone(freq, data, one_port, db_flag):
    print('# MHz S {} R 50'.format('DB' if db_flag else 'MA'))
    db = lambda x: 20 * np.log10(abs(x))
    for f, d in zip(freq, data):
        if db_flag:
            one = FORMAT_DB.format(db(d[0]), np.angle(d[0], deg=True))
            two = FORMAT_DB.format(db(d[1]), np.angle(d[1], deg=True))
        else:
            one = FORMAT_MAG.format(abs(d[0]), np.angle(d[0], deg=True))
            two = FORMAT_MAG.format(abs(d[1]), np.angle(d[1], deg=True))
        print('{:<10.6g}'.format(f/1e6), end='')
        if one_port:
            print('{}'.format(one))
        else:
            print('{}{}{}{}'.format(one, two, two, one))


# public interface

def sweep(start=None, stop=None, points=None, filename=CALFILE, samples=SAMPLES, average=False, device=None):
    cal = cal_load(filename=filename)
    if start or stop or points:
        cal_interpolate(cal=cal, start=start, stop=stop, points=points)
    freq, data = measure(cal=cal, samples=samples, average=average, device=device)
    data = cal_correct(cal=cal, data=data)
    return freq, data


def main():
    # which calibration to run
    unit = [ d for d in CALIBRATIONS if args.__dict__.get(d) ]

    # error check
    if len(unit) > 1:
        raise RuntimeError('Cannot do more than one calibration at a time.')
    if unit and args.init:
        raise RuntimeError('Cannot both intialize and calibrate.')

    # initialize calibration
    if args.init:
        cal_init(filename=args.filename, start=args.start, stop=args.stop, points=args.points)
        return

    # load calibration file
    cal = cal_load(filename=args.filename)

    # show details
    if args.details:
        details(cal=cal)
        return

    # interpolate
    if not unit and (args.start or args.stop or args.points):
        cal = cal_interpolate(cal=cal, start=args.start, stop=args.stop, points=args.points)

    # measure
    freq, data = measure(cal=cal, samples=args.samples, average=args.average, device=args.device)

    # calibrate
    if unit:
        cal[unit[0]] = data[:,0] 
        if unit[0] == 'thru':
            cal['thru21'] = data[:,1]
        np.savez(args.filename, **cal)
        return

    # apply correction
    if not args.raw: 
        data = cal_correct(cal=cal, data=data)

    # write output
    show_touchstone(freq=freq, data=data, one_port=args.one_port, db_flag=args.db) 


if __name__ == '__main__':
    args = parse_args()
    main()


