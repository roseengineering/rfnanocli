# Nanocli

## Introduction

Nanocli is a utility for running measurement
sweeps off the original NanoVNA or the new NanoVNAv2
from the command line.
The sweep results are printed to the terminal
in touchstone format.

In addition the utility provides its own error correction.
It does not use the onboard calibrations features
of either nano.
You must calibrate your nano separately using this utility.
The calibration data is stored in a npz file on your computer.

In order to perform a measure sweep on the original nano, the
utility first turns calibration off on the device.  Once the
measurement is made, the utility will turn calibration back on.
It is recommended to use the same frequency sweep
with the original nano UI as well as with nanocli to
avoid UI interpolation issues.
For the v2 nano, since its USB connection is always uncorrected
its UI is unaffected.

## Calibration

The utility uses the 12-term error model to correct
sweep measurements.  This is the same SOLT
calibration method that you use to calibrate the nano from its UI.

To calibrate the nano using the utility, first initialize the
calibration with your frequency sweep.  This
sweep will be written to your calibration file.  If the calibration
file already exists, it will be overwritten.  By default
the name of the file is cal.npz.

The frequency sweep for a given calibration file is always fixed.  All
subsequent calibrations will use the same sweep set in the calibration
file.

## How to Install

First pip install the required python libraries using:


```
$ pip install -r requirements.txt
Requirement already satisfied: pyserial in /usr/local/lib/python3.9/dist-packages (from -r requirements.txt (line 1)) (3.5)
Requirement already satisfied: numpy in /usr/lib/python3/dist-packages (from -r requirements.txt (line 2)) (1.19.5)
```


Then run the utility using python3.

## Command Line Usage

The utility's command line usage is as follows:


```
$ python3 nanocli.py --help
usage: nanocli.py [-h] [-f FILE] [-o] [-s] [-l] [-t] [-i] [-d] [-r] [-1]
                  [--db] [--text] [-n SAMPLES] [--start START] [--stop STOP]
                  [--points POINTS]
                  [command ...]

positional arguments:
  command               command (default: None)

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  calibration file (default: cal.npz)
  -o, --open            open calibration (default: False)
  -s, --short           short calibration (default: False)
  -l, --load            load calibration (default: False)
  -t, --thru            thru calibration (default: False)
  -i, --init            initialize calibration (default: False)
  -d, --details         show calibration details (default: False)
  -r, --raw             do not apply calibration (default: False)
  -1, --one             show s1p (default: False)
  --db                  show in dB (default: False)
  --text                send output to text file (default: False)
  -n SAMPLES, --samples SAMPLES
                        samples per frequency (default: 2)
  --start START         start frequency (Hz) (default: None)
  --stop STOP           stop frequency (Hz) (default: None)
  --points POINTS       frequency points (default: None)
```


## Utility Calibration

First initialize the calibration file, setting the 
frequency sweep.


```
$ python3 nanocli.py --init --start 10e3 --stop 10e6 --points 1001
```


```
$ python3 nanocli.py --details
start:  0.01 MHz
stop:   10 MHz
points: 1001
cals:   <none>
```


Next perform SOLT calibration.

```
$ python3 nanocli.py --open
$ python3 nanocli.py --short
$ python3 nanocli.py --load
$ python3 nanocli.py --thru
$ python3 nanocli.py --details
```

Now run a sweep.  


```
$ python3 nanocli.py --points 5
# MHz S MA R 50
0.01             0.059735   -87.740        0.31423     2.343        0.31423     2.343       0.059735   -87.740
2.5075          0.0016811   117.338         1.3665    -2.531         1.3665    -2.531      0.0016811   117.338
5.005          0.00054634   -95.277        0.85531   -15.137        0.85531   -15.137     0.00054634   -95.277
7.5025          0.0018721   -63.487        0.78932   -13.616        0.78932   -13.616      0.0018721   -63.487
10              0.0035976   -69.912        0.76787   -13.945        0.76787   -13.945      0.0035976   -69.912
```


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01           -24.400   -87.701     -10.054     2.354     -10.054     2.354     -24.400   -87.701
2.5075         -55.780   132.885       2.712    -2.543       2.712    -2.543     -55.780   132.885
5.005          -68.604   -69.262      -1.361   -15.155      -1.361   -15.155     -68.604   -69.262
7.5025         -53.954   -61.698      -2.054   -13.607      -2.054   -13.607     -53.954   -61.698
10             -48.844   -69.557      -2.295   -13.944      -2.295   -13.944     -48.844   -69.557
```


```
$ python3 nanocli.py --text --points 5
10000          0.00237336-0.0590712j       0.314305+0.0130707j
2507500      -0.00105983+0.00161584j          1.3657-0.061132j
5005000      0.00014045-0.000487809j        0.825504-0.223203j
7502500       0.00096275-0.00183625j        0.767103-0.185639j
10000000      0.00136009-0.00331973j        0.745212-0.185136j
```


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01           -24.407   -87.834
2.5075         -54.816   122.399
5.005          -64.645   -78.646
7.5025         -53.510   -63.576
10             -48.933   -68.541
```


Passing the --points option above
forces an interpolation of the calibration data
to the new frequency sweep.  If the option was not given
the 1001 frequencies used for calibration would be swept.

## Interpolation of Calibration Data

By default, no interpolation is performed
on your calibration data.  The range for the
frequency sweep is taken from the calibration
file.  

However if a different frequency range is
set on the command line from the calibration
data, then the calibration data will be interpolated
to the new range.

Remember the frequency range cannot be changed
when doing calibration.  All calibration data
in a single calibration file must be for the same range.

## Measurement Report Formats

All measurement output from the utility is
written to the terminal.
By default the output will be formatted
for a s2p touchstone file.  If the --one option
is passed on the command line the output will instead be
written in s1p format.

Passing the --text option writes the output
in a format compatible with numpy's loadtxt(arr, dtype='c16')
function.


