#!/usr/bin/python3

import os, sys, re, shutil, serial
import urllib.request
import numpy as np
from serial.tools import list_ports
from struct import pack, unpack_from
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from http.server import BaseHTTPRequestHandler, HTTPServer

# configuration

CALIBRATIONS = [ 'open', 'short', 'load', 'thru' ]
CALFILE = 'cal.npz'

DEFAULT_FSTART = 100e3
DEFAULT_FSTOP = 10.1e6
DEFAULT_POINTS = 101
DEFAULT_SAMPLES = 3


def parse_args():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    # value options 
    parser.add_argument('--filename', default=CALFILE, help='calibration file')
    parser.add_argument('--start', type=float, help='start frequency (Hz)')
    parser.add_argument('--stop', type=float, help='stop frequency (Hz)')
    parser.add_argument('--points', type=int, help='frequency points in sweep')
    parser.add_argument('--samples', type=int, help='samples per frequency')
    parser.add_argument('--average', action='store_true', help='average samples')
    # SOLT calibration
    parser.add_argument('--init', action='store_true', help='initialize calibration')
    parser.add_argument('--open', action='store_true', help='open calibration')
    parser.add_argument('--short', action='store_true', help='short calibration')
    parser.add_argument('--load', action='store_true', help='load calibration')
    parser.add_argument('--thru', action='store_true', help='thru calibration')
    # REST server
    parser.add_argument('--server', action='store_true', help='enter REST server mode')
    parser.add_argument('--hostname', default='0.0.0.0', help='REST server host name')
    parser.add_argument('--port', default=8080, type=int, help='REST server port number')
    # other flags
    parser.add_argument('--device', help='tty device name of nanovna to use')
    parser.add_argument('--info',  action='store_true', help='show calibration info')
    parser.add_argument('--list', action='store_true', help='list available devices')
    parser.add_argument('--gamma',  action='store_true', help='output only S11')
    args = parser.parse_args()
    return args


def request(path, data=None, hostname='127.0.0.1', port=8080):
    url = f'http://{hostname}:{port}/{path}' 
    method = 'GET' if data is None else 'PUT'
    req = urllib.request.Request(url, method=method)
    if data is not None:
        data = str(data).encode('latin1')
    with urllib.request.urlopen(req, data=data) as f:
        return f.read().decode('latin1')


###############################
# touchstone routines
###############################

def db(x):
    return 20 * np.log10(abs(x))


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
    line.append('# MHz S DB R 50')
    entry = ' {:11.3f} {:9.3f}'
    for f, d in zip(freq, data):
        one = entry.format(db(d[0]), np.angle(d[0], deg=True))
        two = entry.format(db(d[1]), np.angle(d[1], deg=True))
        if gamma:
            line.append('{:<10.6f}{}'.format(f/1e6, one))
        else:
            line.append('{:<10.6f}{}{}{}{}'.format(f/1e6, one, two, two, one))
    return '\n'.join(line)


###############################
# REST server
###############################

def afloat(text):
    try:
        return float(text) 
    except ValueError:
        pass


def aint(text):
    try:
        return int(text) 
    except ValueError:
        pass


def abool(text):
    text = text.strip().lower()
    if text == 'y' or text == 'yes' or text == 'true':
        return True
    if text == 'n' or text == 'no' or text == 'false':
        return False


def tobool(val):
    return 'true' if val else 'false'


def tostr(val):
    if val is None:
        return 'null'
    return str(val)


def atoken(text):
    text = text.strip()
    if re.fullmatch(r'[\w_]+', text):
        return text

def serverfactory(sweep):
    kw = {}

    class Server(BaseHTTPRequestHandler):

        def text_response(self, data='OK', code=200):
            data = data.rstrip().encode() + b'\n'
            self.send_response(code)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', len(data))
            self.end_headers()
            self.wfile.write(data)

        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

        def do_POST(self):
            self.do_PUT()

        def do_PUT(self):
            length = int(self.headers.get('Content-Length', 0))
            text = self.rfile.read(length).decode().strip()
            if self.path == '/recall':
                value = atoken(text)
                if value is not None:
                    shutil.copyfile(value + '.npz', CALFILE) 
                    return self.text_response()
            elif self.path == '/save':
                value = atoken(text)
                if value is not None:
                    shutil.copyfile(CALFILE, value + '.npz') 
                    return self.text_response()
            elif self.path == '/start':
                value = afloat(text)
                if value is not None:
                    kw['start'] = value
                    return self.text_response()
            elif self.path == '/stop':
                value = afloat(text)
                if value is not None:
                    kw['stop'] = value
                    return self.text_response()
            elif self.path == '/points':
                value = aint(text)
                if value is not None:
                    kw['points'] = value
                    return self.text_response()
            elif self.path == '/samples':
                value = aint(text)
                if value is not None:
                    kw['samples'] = value
                    return self.text_response()
            elif self.path == '/average':
                value = abool(text)
                if value is not None:
                    kw['average'] = value
                    return self.text_response()
            else:
                return self.text_response('Not Found', code=404)
            self.text_response('Bad Request', code=400)

        def do_GET(self):
            nonlocal kw
            start = kw.get('start')
            stop = kw.get('stop')
            points = kw.get('points')
            samples = kw.get('samples')
            average = kw.get('average')
            if self.path == '/info':
                buf = cal_info(filename=CALFILE)
                return self.text_response(buf)
            elif self.path == '/':
                buf = do_sweep(sweep=sweep, start=start, stop=stop, 
                               points=points, samples=samples, average=average, 
                               filename=CALFILE)
                return self.text_response(buf)
            elif self.path == '/gamma':
                buf = do_sweep(sweep=sweep, start=start, stop=stop, 
                               points=points, samples=samples, average=average, 
                               gamma=True, filename=CALFILE)
                return self.text_response(buf)
            elif self.path == '/init':
                cal_init(start=start, stop=stop, points=points, samples=samples,
                         filename=CALFILE)
                return self.text_response()
            elif self.path == '/open':
                do_calibration(sweep=sweep, unit='open', average=average, filename=CALFILE)
                return self.text_response()
            elif self.path == '/short':
                do_calibration(sweep=sweep, unit='short', average=average, filename=CALFILE)
                return self.text_response()
            elif self.path == '/load':
                do_calibration(sweep=sweep, unit='load', average=average, filename=CALFILE)
                return self.text_response()
            elif self.path == '/thru':
                do_calibration(sweep=sweep, unit='thru', average=average, filename=CALFILE)
                return self.text_response()
            elif self.path == '/reset':
                kw = {}
                return self.text_response()
            elif self.path == '/start':
                return self.text_response(tostr(start))
            elif self.path == '/stop':
                return self.text_response(tostr(stop))
            elif self.path == '/points':
                return self.text_response(tostr(points))
            elif self.path == '/samples':
                return self.text_response(tostr(samples))
            elif self.path == '/average':
                return self.text_response(tobool(average))
            else:
                return self.text_response('Not Found', code=404)
            self.text_response('Bad Request', code=400)

        def handle(self):
            try:
                BaseHTTPRequestHandler.handle(self)
            except RuntimeError as e:
                self.text_response(str(e), code=500)
            except Exception as e:
                self.text_response(str(e) if str(e) else 'Internal Server Error', code=500)
                raise

    return Server


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
        freq = np.linspace(start, stop, points)
        assert(len(d) == points)
        assert(start == d[0,0])
        assert(stop == d[-1,0])
        return d[:,1::2] + 1j * d[:,2::2]

    def sweep(start, stop, points, samples):
        start, stop, points = round(start), round(stop), round(points)
        assert(stop >= start)
        assert(start >= FSTART and stop <= FSTOP)
        assert(points > 0 and points <= POINTS)
        # since Si5351 multisynth divider ratio < 2048, 6348 is the min freq:
        # 26000000 {xtal} * 32 {pll_n} / (6348 {freq} << 6 {rdiv}) = 2047.9
        clear_state(ser)
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
        start, stop, points = round(start), round(stop), round(points)
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

DEVICES = [ nanovna, saa2 ]


def probe_devices():
    data = []
    for fn in DEVICES:
        for dev in list_ports.comports(include_links=True):
            sweep = fn(dev)
            if sweep is not None:
                data.append((sweep, dev))
    return data


def list_devices(data=None):
    data = data or probe_devices()
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
    list_devices(data)
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
    if ((start and start != cal['start'])
       or (stop and stop != cal['stop'])
       or (points and points != cal['points'])):
        freq = cal_frequencies(cal=cal)
        cal['start'] = start or cal['start']
        cal['stop'] = stop or cal['stop'] 
        cal['points'] = points or cal['points']
        freq_new = cal_frequencies(cal=cal)
        for name in cal.keys():
            data = cal[name]
            if np.ndim(data) and data.size > 1:
                cal[name] = np.interp(freq_new, freq, data)


def cal_init(start, stop, points, samples, filename):
    start = start or DEFAULT_FSTART
    stop = stop or DEFAULT_FSTOP
    points = points or DEFAULT_POINTS
    samples = samples or DEFAULT_SAMPLES
    assert(stop >= start)
    assert(points > 0)
    assert(samples > 0)
    np.savez(filename, start=start, stop=stop, points=points, samples=samples)


def cal_load(filename):
    try:
        ext = os.path.splitext(filename)[1]
        if ext.lower() != '.npz':
            filename += '.npz'
        npzfile = np.load(filename)
    except FileNotFoundError:
        raise RuntimeError('No calibration file, please initialize.')
    return dict(npzfile)


def cal_info(filename):
    cal = cal_load(filename)
    line = []
    line.append('start:   {:.6g} MHz'.format(cal['start'] / 1e6))
    line.append('stop:    {:.6g} MHz'.format(cal['stop'] / 1e6))
    line.append('points:  {:d}'.format(cal['points']))
    line.append('samples: {:d}'.format(cal['samples']))
    units = [ d for d in CALIBRATIONS if d in cal ]
    line.append('cals:    {}'.format(', '.join(units) if units else '<none>'))
    return '\n'.join(line)


###############################
# measurement
###############################

def measure(cal, sweep, samples, average):
    samples = samples or cal['samples']
    freq = cal_frequencies(cal=cal)
    s = sweep(start=freq[0], stop=freq[-1], points=len(freq), samples=samples)
    s = np.average(s, axis=0) if average else np.median(s, axis=0)
    return freq, s


def do_calibration(sweep, unit, filename, average):
    cal = cal_load(filename)
    freq, data = measure(cal=cal, sweep=sweep, average=average, samples=None)
    cal[unit] = data[:,0]
    if unit == 'thru':
        cal['thru21'] = data[:,1]
    np.savez(filename, **cal)


def do_sweep(sweep, start, stop, points, samples, average, filename, gamma=None):
    cal = cal_load(filename)
    cal_interpolate(cal=cal, start=start, stop=stop, points=points)
    freq, data = measure(cal=cal, sweep=sweep, samples=samples, average=average)
    data = cal_correct(cal=cal, data=data)
    text = write_touchstone(freq=freq, data=data, gamma=gamma)
    return text


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
        buf = cal_info(filename=args.filename)
        print(buf)
        return

    # open device
    sweep = getport(device=args.device)

    # operations
    if args.init:
        cal_init(start=args.start, stop=args.stop, points=args.points,
            samples=args.samples, filename=args.filename)
    elif unit:
        do_calibration(sweep=sweep, unit=unit[0], average=args.average, filename=args.filename)
    else:
        buf = do_sweep(sweep=sweep, start=args.start, stop=args.stop, 
            points=args.points, samples=args.samples, average=args.average, 
            gamma=args.gamma, filename=args.filename)
        print(buf)


def getvna(device=None, filename=CALFILE):
    cal_orig = cal_load(filename)
    def fn(start=None, stop=None, points=None, samples=None, average=None, gamma=None):
        cal = cal_orig.copy()
        cal_interpolate(cal=cal, start=start, stop=stop, points=points)
        sweep = getport(device)
        freq, data = measure(cal=cal, sweep=sweep, samples=samples, average=average)
        data = cal_correct(cal=cal, data=data)
        return freq, data[:,0] if gamma else data
    return fn


def getremote(hostname='127.0.0.1', port=8080):
    def fn(start=None, stop=None, points=None, samples=None, average=None, gamma=None):
        text = request('reset', hostname=hostname, port=port)
        if start: request('start', start, hostname=hostname, port=port)
        if stop: request('stop', stop, hostname=hostname, port=port)
        if points: request('points', points, hostname=hostname, port=port)
        if samples: request('samples', samples, hostname=hostname, port=port)
        if average: request('average', average, hostname=hostname, port=port)
        if gamma: 
            text = request('gamma', hostname=hostname, port=port)
        else:
            text = request('', hostname=hostname, port=port)
        f, s = read_touchstone(text)
        return f, s[:,0]
    return fn


def main():
    args = parse_args()
    if args.server:
        try:
            sweep = getport(args.device)
        except RuntimeError as e:
            print(str(e), file=sys.stderr)
            return
        try:
            httpserver = HTTPServer((args.hostname, args.port), serverfactory(sweep))
            httpserver.serve_forever()
        except KeyboardInterrupt:
            httpserver.server_close()
    else:
        try:
            cli(args)
        except RuntimeError as e:
            print(str(e), file=sys.stderr)

