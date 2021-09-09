#!/usr/bin/python3

import numpy as np
import serial, os, sys
from serial.tools import list_ports
from struct import pack, unpack_from

# defaults

CALFILE = 'cal'

# configuration
 
FORMAT_TEXT = ' {:25.6g} {:25.6g}'
FORMAT_DB   = ' {:11.3f} {:9.3f}'
FORMAT_MAG  = ' {:14.5g} {:9.3f}'

# supported calibrations

CALIBRATIONS = [ 'open', 'short', 'load', 'thru' ]


def parse_args():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    # value options 
    parser.add_argument('--filename', default=CALFILE, help='calibration file')
    parser.add_argument('--start', type=float, help='start frequency (Hz)')
    parser.add_argument('--stop', type=float, help='stop frequency (Hz)')
    parser.add_argument('--points', type=int, help='frequency points in sweep')
    parser.add_argument('--segment', type=int, help='frequency points in each sweep segment')
    parser.add_argument('--samples', type=int, help='samples per frequency')
    parser.add_argument('--device', type=int, help='select device number')
    # calibration flags
    parser.add_argument('-i', '--init', action='store_true', help='initialize calibration')
    parser.add_argument('-o', '--open', action='store_true', help='open calibration')
    parser.add_argument('-s', '--short', action='store_true', help='short calibration')
    parser.add_argument('-l', '--load', action='store_true', help='load calibration')
    parser.add_argument('-t', '--thru', action='store_true', help='thru calibration')
    # other flags
    parser.add_argument('-d', '--details',  action='store_true', help='show calibration details')
    parser.add_argument('-1', '--one-port',  action='store_true', help='output in s1p format')
    parser.add_argument('--db', action='store_true', help='show in dB')
    args = parser.parse_args()
    return args


###############################

def nanovna(dev):
    FSTART = 6348 
    FSTOP = 2.7e9

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
        cmd = "scan {:d} {:d} {:d} 111".format(start, stop, points)
        text = command(ser, cmd)
        d = np.array([[ float(c) for c in ln.split() ] for ln in text.split('\n') ])
        freq = np.linspace(start, stop, points)
        assert(len(d) == points)
        assert(start == d[0,0])
        assert(stop == d[-1,0])
        return d[:,1::2] + 1j * d[:,2::2]

    def sweep(start, stop, points, samples):
        start, stop, points = int(start), int(stop), int(points)
        # points should also be <= 101, but dislord extended it to 301
        assert(points > 0)
        assert(stop >= start)
        assert(start >= FSTART and stop <= FSTOP)
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
        return data

    return sweep


def saa2(dev):
    POINTS = 255
    FSTART = 10e3 
    FSTOP = 4400e6

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
        assert(points > 0 and points <= POINTS)
        assert(stop >= start)
        assert(start >= FSTART and stop <= FSTOP)
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
      
        return data

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
    # e30 is assumed to be zero here
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


def cal_frequencies(cal):
    return np.linspace(cal['start'], cal['stop'], cal['points'])


def cal_interpolate(cal, start, stop, points):
    if ((start and start != cal['start'])
       or (stop and stop != cal['stop'])
       or (points and points != cal['points'])):
        freq = np.linspace(cal['start'], cal['stop'], cal['points'])
        cal['start'] = start or cal['start']
        cal['stop'] = stop or cal['stop'] 
        cal['points'] = points or cal['points']
        freq_new = cal_frequencies(cal=cal)
        for name in cal.keys():
            data = cal[name]
            if np.ndim(data) and data.size > 1:
                cal[name] = np.interp(freq_new, freq, data)
    return cal


def cal_init(filename, start, stop, points, segment, samples):
    FSTART = 100e3
    FSTOP = 10.1e6
    POINTS = 101
    SAMPLES = 3

    start = start or FSTART
    stop = stop or FSTOP
    samples = samples or SAMPLES
    points = points or POINTS
    segment = segment or POINTS
    assert(stop >= start)
    assert(segment > 0)
    assert(points > 0)
    np.savez(filename, start=start, stop=stop, points=points, segment=segment, samples=samples)


def cal_load(filename):
    try:
        name, ext = os.path.splitext(filename)
        npzfile = np.load('{}{}'.format(name, ext or '.npz'))
    except FileNotFoundError:
        raise RuntimeError('No calibration file, please initialize.')
    return dict(npzfile)


def measure(cal, device):
    start = cal['start']
    stop = cal['stop']
    points = cal['points']
    samples = cal['samples']
    segment = cal['segment']
    sweep = getport(device)
    freq = cal_frequencies(cal)
    ix = np.arange(segment, points, segment)
    return np.concatenate([ 
        np.median(sweep(np.round(d[0]), np.round(d[-1]), len(d), samples), axis=0) 
        for d in np.split(freq, ix) ])


def details(cal):
    print('start:   {:.6g} MHz'.format(cal['start'] / 1e6))
    print('stop:    {:.6g} MHz'.format(cal['stop'] / 1e6))
    print('points:  {:d}'.format(cal['points']))
    print('segment: {:d}'.format(cal['segment']))
    print('samples: {:d}'.format(cal['samples']))
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
        cal_init(filename=args.filename, 
                 start=args.start, stop=args.stop, points=args.points,
                 segment=args.segment, samples=args.samples)
        return

    # load calibration
    cal = cal_load(filename=args.filename)

    # show details
    if args.details:
        details(cal=cal)
        return

    # update calibration
    if args.samples: cal['samples'] = args.samples

    # save calibration
    if unit:
        data = measure(cal=cal, device=device)
        cal[unit[0]] = data[:,0] 
        if unit[0] == 'thru':
            cal['thru21'] = data[:,1]
        np.savez(args.filename, **cal)
        return

    # interpolate and measure
    cal = cal_interpolate(cal=cal, start=args.start, stop=args.stop, points=args.points)
    data = measure(cal=cal, device=args.device)
    data = cal_correct(cal=cal, data=data)
    freq = cal_frequencies(cal=cal)

    # write output
    show_touchstone(freq=freq, data=data, one_port=args.one_port, db_flag=args.db) 


####################
# public interface
####################

def sweep(start=None, stop=None, points=None, samples=None, device=None, filename=CALFILE):
    cal = cal_load(filename=filename)
    if samples: cal['samples'] = samples
    cal = cal_interpolate(cal=cal, start=start, stop=stop, points=points)
    data = measure(cal=cal, device=device)
    data = cal_correct(cal=cal, data=data)
    freq = cal_frequencies(cal=cal)
    return freq, data


if __name__ == '__main__':
    args = parse_args()
    main()


