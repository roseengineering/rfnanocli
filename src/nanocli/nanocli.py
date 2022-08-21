#!/usr/bin/python3

import os, sys, re, serial, argparse
import numpy as np
from serial.tools import list_ports
from struct import pack, unpack_from

# configuration

CALFILE = 'cal.npz'
CALIBRATIONS = [ 'open', 'short', 'load', 'thru' ]

DEFAULT_FSTART = 100e3
DEFAULT_FSTOP = 10.1e6
DEFAULT_POINTS = 101
DEFAULT_SAMPLES = 3


def parse_args():
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=formatter_class)
    # value options 
    parser.add_argument('--calfile', default=CALFILE, help='calibration file')
    parser.add_argument('--start', type=float, help='start frequency (Hz)')
    parser.add_argument('--stop', type=float, help='stop frequency (Hz)')
    parser.add_argument('--points', type=int, help='frequency points in sweep')
    # SOLT calibration
    parser.add_argument('--init', action='store_true', help='initialize calibration')
    parser.add_argument('--open', action='store_true', help='open calibration')
    parser.add_argument('--short', action='store_true', help='short calibration')
    parser.add_argument('--load', action='store_true', help='load calibration')
    parser.add_argument('--thru', action='store_true', help='thru calibration')
    parser.add_argument('--samples', type=int, help='samples per frequency')
    parser.add_argument('--average', action='store_true', help='average samples')
    # other flags
    parser.add_argument('--gamma',  action='store_true', help='output only S11')
    parser.add_argument('--device', help='tty device name of nanovna to use')
    parser.add_argument('-i', '--info',  action='store_true', help='show calibration info')
    parser.add_argument('-l', '--list', action='store_true', help='list available devices')
    args = parser.parse_args()
    return args


def tobool(val):
    return 'true' if val else 'false'


###############################
# touchstone routines
###############################

def rect(x, y, dtype):
    if dtype == 'db' or dtype =='ma':
        x = 10**(x / 20) if dtype == 'db' else x
        value = x * np.exp(1j * np.deg2rad(y))
    elif dtype == 'ri':
        value = x + 1j * y
    else:
        raise ValueError
    return value


def prefix(unit):
    if unit == 'hz':
        return 1
    elif unit == 'khz':
        return 1e3
    elif unit == 'mhz':
        return 1e6
    elif unit == 'ghz':
        return 1e9
    else:
        raise ValueError


def read_touchstone(text):
    freq = []
    data = []
    dtype = None
    buf = ''
    f = iter(text.splitlines())
    while True:
        ln = next(f, None)
        if ln is not None:
            ln = ln.rstrip()
            if not ln or ln[0] == '!':
                continue
            # handle header line
            if ln[0] == '#':
                d = ln[1:].lower().split()
                if d[1] != 's' or d[3] != 'r' or float(d[4]) != 50:
                    raise ValueError
                scale = prefix(d[0])
                dtype = d[2]
                continue
            # handle line continuation
            if ln[0] == ' ':
                buf += ln
                continue
        if buf:
            d = [ float(d) for d in buf.split() ]
            freq.append(d[0] * scale)
            d = [ rect(d[i], d[i+1], dtype=dtype) for i in range(1, len(d), 2) ]
            n = int(np.sqrt(len(d)))
            d = np.array(d).reshape(n, n)
            data.append(d.T if d.size == 4 else d)
        if ln is None:
            break
        buf = ln
    freq = np.array(freq)
    data = np.array(data)
    return freq, data


def write_touchstone(freq, data, gamma):
    line = []
    line.append('# MHz S MA R 50')
    entry = ' {:11.5e} {:8.2f}'
    for f, d in zip(freq, data):
        one = entry.format(abs(d[0]), np.angle(d[0], deg=True))
        two = entry.format(abs(d[1]), np.angle(d[1], deg=True))
        zero = entry.format(0, 0)
        if gamma:
            line.append('{:<12.6f}{}'.format(f/1e6, one))
        else:
            line.append('{:<12.6f}{}{}{}{}'.format(f/1e6, one, two, zero, zero))
    return '\n'.join(line)


###############################
# drivers
###############################

def nanovna(dev):
    FSTART = 6348  # si5351 limit
    FSTOP = 2.7e9
    POINTS = 401   # f303 based nanovna
    VID = 0x0483
    PID = 0x5740

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
        text = read(ser)
        return text

    def clear_state(ser):
        for i in range(2): 
            text = command(ser, "help")
            if text[:9] == 'Commands:': break
            text = read(ser)
            if text[:9] == 'Commands:': break

    def scan(ser, start, stop, points):
        cmd = "scan {:d} {:d} {:d} 111".format(start, stop, points)
        text = command(ser, cmd)
        d = np.array([[ float(c) for c in ln.split() ] for ln in text.split('\n') ])
        assert(len(d) == points)
        assert(start == d[0,0])
        assert(stop == d[-1,0])
        return d[:,1::2] + 1j * d[:,2::2]

    def sweep(start, stop, points, samples):
        start, stop, points = round(start), round(stop), int(points)
        assert(stop >= start)
        assert(start >= FSTART and stop <= FSTOP)
        assert(points > 0 and points <= POINTS)
        # since Si5351 multisynth divider ratio < 2048, 6348 is the min freq:
        # 26000000 {xtal} * 32 {pll_n} / (6348 {freq} << 6 {rdiv}) = 2047.9
        clear_state(ser)
        # alter ui
        command(ser, f'sweep {start} {stop} {points}')
        command(ser, "cal off")
        data = []
        for i in range(samples):
            d = scan(ser, start=start, stop=stop, points=points)
            data.append(d)
        data = np.array(data)
        command(ser, "cal on")
        command(ser, "resume")  # resume 
        return data

    if dev.vid == VID and dev.pid == PID:
        ser = serial.Serial(dev.device)
        return sweep


def saa2(dev):
    FSTART = 10e3 
    FSTOP = 4400e6
    POINTS = 255
    VID = 0x04b4
    PID = 0x0008

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

    def clear_fifo(ser):
        cmd = pack("<BBB", CMD_WRITE, ADDR_VALUES_FIFO, 0)
        send(ser, cmd)

    def set_sweep(ser, start, stop, points, samples):
        step = (stop - start) / (points - 1)
        cmd = pack("<BBQ", CMD_WRITE8, ADDR_SWEEP_START, int(start))
        cmd += pack("<BBQ", CMD_WRITE8, ADDR_SWEEP_STEP, int(step))
        cmd += pack("<BBH", CMD_WRITE2, ADDR_SWEEP_POINTS, int(points))
        cmd += pack("<BBH", CMD_WRITE2, ADDR_SWEEP_VALS_PER_FREQ, int(samples))
        send(ser, cmd)

    def read_fifo(ser, n):
        cmd = pack("<BBB", CMD_READFIFO, ADDR_VALUES_FIFO, n)
        send(ser, cmd)
        return ser.read(32 * n)

    def exit_usbmode(ser):
        cmd = pack("<BBB", CMD_WRITE, ADDR_RAW_SAMPLES_MODE, 2)
        send(ser, cmd)

    def sweep(start, stop, points, samples):
        start, stop, points = round(start), round(stop), int(points)
        assert(stop >= start)
        assert(start >= FSTART and stop <= FSTOP)
        assert(points > 0 and points <= POINTS)
        data = []
        try:
            for n in range(samples):
                set_sweep(ser, start, stop, points, 1)
                clear_fifo(ser)  # ensures the first point is 0
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
        return data

    if dev.vid == VID and dev.pid == PID:
        ser = serial.Serial(dev.device)
        return sweep


def probe_devices():
    data = []
    for fn in [ nanovna, saa2 ]:
        for dev in list_ports.comports(include_links=True):
            sweep = fn(dev)
            if sweep is not None:
                data.append((sweep, dev))
    return data


def list_devices():
    data = probe_devices()
    for i in range(len(data)):
        fn, dev = data[i]
        m = re.match(r'<function (\w+)', str(fn))
        print("{}: {}".format(m.group(1), dev.device), file=sys.stderr)


def getport(device):
    data = probe_devices()
    if len(data) == 0:
        raise RuntimeError("No NanoVNA device found.")
    for fn, dev in data:
        if device is None or device == dev.device:
            return fn
    print("Use --device to select the NanoVNA to use:", file=sys.stderr)
    raise RuntimeError("No NanoVNA device found")


###############################
# calibration
###############################

def calibrate(cal):
    # see Rytting, "Network analyzer error models and calibration methods"
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
    start = cal['start']
    stop = cal['stop']
    points = cal['points']
    freq = np.linspace(start, stop, points)
    return freq


def cal_interpolate(cal, start, stop, points):
    if start != cal['start'] or stop != cal['stop'] or points != cal['points']:
        freq = cal_frequencies(cal=cal)
        cal['start'] = start or cal['start']
        cal['stop'] = stop or cal['stop'] 
        cal['points'] = points or cal['points'] 
        freq_new = cal_frequencies(cal=cal)
        for name in cal.keys():
            data = cal[name]
            if np.ndim(data) and data.size > 1:
                cal[name] = np.interp(freq_new, freq, data)


def cal_init(start, stop, points, samples, average, calfile):
    start = DEFAULT_FSTART if start is None else start
    stop = DEFAULT_FSTOP if stop is None else stop
    points = DEFAULT_POINTS if points is None else points
    samples = DEFAULT_SAMPLES if samples is None else samples
    average = bool(average)
    points = int(points)
    samples = int(samples)
    assert(start > 0)
    assert(stop > 0)
    assert(stop > start)
    assert(points > 0)
    assert(samples > 0)
    np.savez(calfile, start=start, stop=stop, points=points, 
             average=average, samples=samples)


def cal_load(calfile):
    try:
        ext = os.path.splitext(calfile)[1]
        if ext.lower() != '.npz':
            calfile += '.npz'
        npzfile = np.load(calfile)
    except FileNotFoundError:
        raise RuntimeError('No calibration file, please initialize.')
    return dict(npzfile)


def cal_info(calfile, calibrations):
    cal = cal_load(calfile)
    line = []
    line.append('start:   {:.6g} MHz'.format(cal['start'] / 1e6))
    line.append('stop:    {:.6g} MHz'.format(cal['stop'] / 1e6))
    line.append('points:  {:d}'.format(cal['points']))
    line.append('samples: {:d}'.format(cal['samples']))
    line.append('average: {}'.format(tobool(cal['average'])))
    units = [ d for d in calibrations if d in cal ]
    line.append('cals:    {}'.format(', '.join(units) if units else '<none>'))
    return '\n'.join(line)


###############################
# measurement
###############################

def measure(cal, sweep):
    samples = cal['samples']
    average = cal['average']
    freq = cal_frequencies(cal=cal)
    data = sweep(start=freq[0], stop=freq[-1], points=len(freq), samples=samples)
    data = np.average(data, axis=0) if average else np.median(data, axis=0)
    return freq, data


def do_calibration(sweep, unit, calfile):
    cal = cal_load(calfile)
    freq, data = measure(cal=cal, sweep=sweep)
    cal[unit] = data[:,0]
    if unit == 'thru':
        cal['thru21'] = data[:,1]
    np.savez(calfile, **cal)


def do_sweep(cal, start, stop, points, sweep):
    cal_interpolate(cal=cal, start=start, stop=stop, points=points)
    freq, data = measure(cal=cal, sweep=sweep)
    data = cal_correct(cal=cal, data=data)
    return freq, data


def cli(args):
    if args.list:
        list_devices()
        return

    # which calibration to run
    unit = [ d for d in CALIBRATIONS if args.__dict__.get(d) ]
    if len(unit) > 1:
        raise RuntimeError('Cannot do more than one calibration at a time.')
    if unit and args.init:
        raise RuntimeError('Cannot initialize and calibrate as the same time.')

    # show details
    if args.info:
        text = cal_info(args.calfile, calibrations=CALIBRATIONS)
        print(text)
        return

    # open device
    sweep = getport(args.device)

    # operations
    if args.init:
        cal_init(start=args.start, stop=args.stop, points=args.points,
                 samples=args.samples, average=args.average, 
                 calfile=args.calfile)
    elif unit:
        do_calibration(sweep=sweep, unit=unit[0], calfile=args.calfile)
    else:
        cal = cal_load(args.calfile)
        freq, data = do_sweep(cal=cal, start=args.start, stop=args.stop, 
                              points=args.points, sweep=sweep)
        text = write_touchstone(freq=freq, data=data, gamma=args.gamma)
        print(text)


def getvna(device=None, calfile=CALFILE):
    cal_orig = cal_load(calfile)
    def fn(start=None, stop=None, points=None, filename=None):
        if filename is not None:
            ext = os.path.splitext(filename)[1]
            if ext != '.s1p' and ext != '.s2p':
                raise ValueError
        cal = cal_orig.copy()
        sweep = getport(device)
        freq, data = do_sweep(cal=cal, start=start, stop=stop,
                              points=points, sweep=sweep)
        if filename is not None:
            text = write_touchstone(freq=freq, data=data, gamma=ext=='.s1p')
            with open(filename, 'w') as f: 
                f.write(text)
        return freq, data
    return fn


def main():
    args = parse_args()
    try:
        cli(args)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)

