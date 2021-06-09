
import numpy as np
import serial
from serial.tools import list_ports
from struct import pack, unpack_from
from time import sleep

FSTART = 10e3
FSTOP = 10e6
POINTS = 101
SAMPLES = 2
 
FORMAT_TEXT = ' {:25.6g} {:25.6g}'
FORMAT_DB   = ' {:11.3f} {:9.3f}'
FORMAT_MAG  = ' {:14.5g} {:9.3f}'

calibrations = [ 'open', 'short', 'load', 'thru' ]


def parse_args():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('command', metavar='command', nargs='*', help='command')
    parser.add_argument('-f', '--file', default='cal.npz', help='calibration file')
    parser.add_argument('-o', '--open', action='store_true', help='open calibration')
    parser.add_argument('-s', '--short', action='store_true', help='short calibration')
    parser.add_argument('-l', '--load', action='store_true', help='load calibration')
    parser.add_argument('-t', '--thru', action='store_true', help='thru calibration')
    parser.add_argument('-i', '--init', action='store_true', help='initialize calibration')
    parser.add_argument('-d', '--details',  action='store_true', help='show calibration details')
    parser.add_argument('-r', '--raw', action='store_true', help='do not apply calibration')
    # output flags
    parser.add_argument('-1', '--one',  action='store_true', help='show s1p')
    parser.add_argument('--db', action='store_true', help='show in dB')
    parser.add_argument('--text', action='store_true', help='send output to text file')
    # value options
    parser.add_argument('-n', '--samples', default=SAMPLES, type=int, help='samples per frequency')
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

    def scan(start, stop, points, samples):
        assert(points > 1 and points <= 101)
        freq = np.linspace(start, stop, points)
        data = np.zeros((points, 4))
        try:
            ser = serial.Serial(dev)
            send(ser, "")
            read(ser)
            send(ser, "cal off")
            read(ser)
            for i in range(samples):
                send(ser, "scan {} {} {} 110".format(start, stop, points))
                text = read(ser)
                data += np.array([[ float(d) for d in ln.split() ] for ln in text.split('\n') ])
        finally:
            send(ser, "cal on")
            read(ser)
            ser.close()
        data = data / samples
        data = data[:,0::2] + 1j * data[:,1::2]
        return freq, data / samples

    return scan


def nanovnav2(dev):
    WRITE_SLEEP = 0.05

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
        cmd += pack("<BBH", CMD_WRITE2, ADDR_SWEEP_POINTS, points)
        cmd += pack("<BBH", CMD_WRITE2, ADDR_SWEEP_VALS_PER_FREQ, samples)
        send(ser, cmd)
        sleep(WRITE_SLEEP)

    def clear_state(ser):
        cmd = pack("<Q", 0)
        send(ser, cmd)
        sleep(WRITE_SLEEP)

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

    def scan(start, stop, points, samples):
        assert(points > 1 and points <= 1024)
        freq = np.linspace(start, stop, points)
        data = np.zeros((points, 2), dtype=complex)
        remaining = samples * points
        count = 0
        try:
            ser = serial.Serial(dev)
            clear_state(ser)
            set_sweep(ser, start, stop, points, samples)        
            clear_state(ser)  # required
            clear_fifo(ser)
            while remaining > 0:
                n = min(255, remaining)
                fifo = read_fifo(ser, n)
                for i in range(n):
                    d = unpack_from("<iiiiiihxxxxxx", fifo, i * 32)
                    fwd = complex(d[0], d[1])
                    refl = complex(d[2], d[3])
                    thru = complex(d[4], d[5])
                    index = d[6]
                    assert(index == count // samples)
                    data[index,0] += refl / fwd
                    data[index,1] += thru / fwd
                    count += 1
                remaining -= n
        finally:
            exit_usbmode(ser)
            ser.close()
        data = data / samples
        return freq, data

    return scan


###############################


DEVICES = {
    nanovna: [(0x0483, 0x5740)],
    nanovnav2: [(0x04b4, 0x0008)],
};


def getport():
    device_list = list_ports.comports()
    for device in device_list:
        for fn, address in DEVICES.items():
            if (device.vid, device.pid) in address:
                return fn(device.device)
    raise RuntimeError("NanoVNA device not found.")


def calibrate(cal):
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


def cal_init(filename, start, stop, points):
    start = start or FSTART
    stop = stop or FSTOP
    points = points or POINTS
    np.savez(filename, start=start, stop=stop, points=points)


def cal_load(filename):
    try:
        npzfile = np.load(filename)
    except FileNotFoundError:
        raise RuntimeError('No calibration file, please initialize.')
    return dict(npzfile)


def cal_correct(cal, data):
    d = calibrate(cal)
    S11M = data[:,0]
    S21M = data[:,1]
    S11 = (S11M - d['e00']) / (S11M * d['e11'] - d['de'])
    S21 = S21M / d['e10e32'] * d['e10e01'] / (d['e11'] * S11M - d['de'])
    return np.array([ S11, S21 ]).T


def measure(cal, samples):
    start = cal['start']
    stop = cal['stop']
    points = cal['points']
    scan = getport()
    freq, data = scan(start, stop, points, samples)
    return freq, data


def details(cal):
    print('start:  {:.6g} MHz'.format(cal['start'] / 1e6))
    print('stop:   {:.6g} MHz'.format(cal['stop'] / 1e6))
    print('points: {:d}'.format(cal['points']))
    units = ', '.join([ d for d in calibrations if d in cal ])
    print('cals:   {}'.format(units if units else '<none>'))


def show_text(freq, data):
    for f, d in zip(freq, data):
        print('{:<10.0f}'.format(f), end='')
        print(FORMAT_TEXT.format(d[0], d[1]))


def show_touchstone(freq, data):
    print('# MHz S {} R 50'.format('DB' if args.db else 'MA'))
    db = lambda x: 20 * np.log10(abs(x))
    for f, d in zip(freq, data):
        if args.db:
            one = FORMAT_DB.format(db(d[0]), np.angle(d[0], deg=True))
            two = FORMAT_DB.format(db(d[1]), np.angle(d[1], deg=True))
        else:
            one = FORMAT_MAG.format(abs(d[0]), np.angle(d[0], deg=True))
            two = FORMAT_MAG.format(abs(d[1]), np.angle(d[1], deg=True))
        print('{:<10.6g}'.format(f/1e6), end='')
        if args.one:
            print('{}'.format(one))
        else:
            print('{}{}{}{}'.format(one, two, two, one))


def main():
    # which calibration to run
    unit = [ d for d in calibrations if args.__dict__.get(d) ]
    if args.init and unit:
        raise RuntimeError('Cannot both intialize and calibrate.')
    if len(unit) > 1:
        raise RuntimeError('Cannot do more than one calibration at a time.')

    # initialize calibration
    if args.init:
        cal_init(args.file, args.start, args.stop, args.points)
        return

    # load calibration file
    cal = cal_load(args.file)

    # show details
    if args.details:
        details(cal)
        return

    # interpolate
    if args.start or args.stop or args.points:
        if unit:
            raise RuntimeError('Cannot both interpolate and calibrate.')
        cal_interpolate(cal, args.start, args.stop, args.points)

    # measure
    freq, data = measure(cal, args.samples)

    # calibrate
    if unit:
        cal[unit[0]] = data[:,0] 
        if unit[0] == 'thru':
            cal['thru21'] = data[:,1]
        np.savez(args.file, **cal)
        return

    # measure and apply correction
    if not args.raw: 
        data = cal_correct(cal, data)

    # write output
    if args.text:
        show_text(freq, data)
    else:
        show_touchstone(freq, data) 


if __name__ == '__main__':
    args = parse_args()
    main()


