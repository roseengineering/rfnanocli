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
You must calibrate your nano separately to use this utility.
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
calibration file with your frequency sweep.
If the calibration
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


Print details on the calibration file.


```
$ python3 nanocli.py --details
start:  0.01 MHz
stop:   10 MHz
points: 1001
cals:   <none>
```


According to the --details option, the calibration file currently has no calibration data.
So lets perform the SOLT calibrations.

```
$ python3 nanocli.py --open
$ python3 nanocli.py --short
$ python3 nanocli.py --load
$ python3 nanocli.py --thru
```

Now run a sweep.  


```
$ python3 nanocli.py --points 5
# MHz S MA R 50
0.01             0.059103   -88.109        0.31488     2.485        0.31488     2.485       0.059103   -88.109
2.5075         0.00094646    95.230         1.2795    -7.257         1.2795    -7.257     0.00094646    95.230
5.005          0.00062485   -73.699        0.83905   -14.130        0.83905   -14.130     0.00062485   -73.699
7.5025          0.0020576   -64.948        0.78604   -13.110        0.78604   -13.110      0.0020576   -64.948
10              0.0035517   -67.605        0.76611   -13.669        0.76611   -13.669      0.0035517   -67.605
```


Return the results in dB.


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01           -24.540   -87.864     -10.054     2.602     -10.054     2.602     -24.540   -87.864
2.5075         -58.996   110.807       2.151    -7.265       2.151    -7.265     -58.996   110.807
5.005          -65.195   -83.229      -1.522   -14.123      -1.522   -14.123     -65.195   -83.229
7.5025         -54.144   -62.327      -2.090   -13.106      -2.090   -13.106     -54.144   -62.327
10             -48.549   -68.870      -2.315   -13.680      -2.315   -13.680     -48.549   -68.870
```


Output measurements in a format that can be read by numpy.


```
$ python3 nanocli.py --text --points 5
10000          0.00198803-0.0593619j       0.314632+0.0137569j
2507500     -0.000535604+0.00122873j         1.27013-0.161605j
5005000     0.000109866-0.000645447j        0.813437-0.204892j
7502500      0.000995252-0.00180906j        0.765461-0.178246j
10000000      0.00131698-0.00339905j         0.744325-0.18106j
```


Write a s1p file to stdout.


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01           -24.514   -87.834
2.5075         -60.143   105.598
5.005          -66.591   -75.767
7.5025         -53.168   -61.714
10             -48.863   -68.138
```


Passing the --points option above
forces an interpolation of the calibration data
to the frequencies of the new sweep.  If this option was not given
the original 1001 frequencies used for calibration would be swept
without interpolation.

## Interpolation of Calibration Data

By default, no interpolation is performed
on your calibration data when making a measurement.  
The frequencies for the measurement sweep is taken directly from 
the calibration file.  

However if the range of the frequency sweep
is changed on the command line from that given 
in the calibration file,
the calibration data will be interpolated
to the new range.

Remember, the frequency range cannot be changed
when doing calibration.  But during a measurement it can.
All calibration data within a calibration file 
must have same frequency sweep range.

## Measurement Report Formats

All measurement output from the utility is
written to the terminal (using stdout).
By default the output will be formatted
for a s2p touchstone file.  If the --one option
is passed on the command line the output will be
formatted for a s1p touchstone file.

Passing the --text option writes the output
in a format compatible with numpy's loadtxt(fid, dtype='c16')
function.


