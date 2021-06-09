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
0.01              0.05914   -88.112        0.31511     2.457        0.31511     2.457        0.05914   -88.112
2.5075         0.00078739    97.330         1.2856    -7.033         1.2856    -7.033     0.00078739    97.330
5.005          0.00052549   -82.205        0.83989   -14.192        0.83989   -14.192     0.00052549   -82.205
7.5025          0.0021275   -63.184        0.78623   -13.120        0.78623   -13.120      0.0021275   -63.184
10              0.0036121   -70.370        0.76631   -13.674        0.76631   -13.674      0.0036121   -70.370
```


Return the results in dB.


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01           -24.615   -87.977     -10.040     2.571     -10.040     2.571     -24.615   -87.977
2.5075         -59.178   112.420       2.185    -7.027       2.185    -7.027     -59.178   112.420
5.005          -65.187   -93.010      -1.518   -14.178      -1.518   -14.178     -65.187   -93.010
7.5025         -53.285   -65.059      -2.088   -13.120      -2.088   -13.120     -53.285   -65.059
10             -48.853   -69.315      -2.313   -13.686      -2.313   -13.686     -48.853   -69.315
```


Output measurements in a format that can be read by numpy.


```
$ python3 nanocli.py --text --points 5
10000          0.00209053-0.0585386j       0.315104+0.0135266j
2507500    -0.000513284+0.000900327j         1.27609-0.157442j
5005000     8.58206e-05-0.000475248j        0.814411-0.205741j
7502500      0.000981311-0.00202344j        0.765464-0.178622j
10000000      0.00145997-0.00337398j        0.744377-0.181239j
```


Write a s1p file to stdout.


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01           -24.492   -87.936
2.5075         -58.999   120.338
5.005          -63.980   -70.492
7.5025         -53.678   -64.562
10             -48.481   -71.427
```


Passing the --points option above
forces an interpolation of the calibration data
to the range of the new frequency sweep.  If this option was not given
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
in a format compatible with numpy's loadtxt(arr, dtype='c16')
function.


