# Nanocli

## Introduction

Nanocli is a utility for running measurement
sweeps off the original NanoVNA or the new SAA2 (NanoVNAv2)
from the command line.
The sweep results are printed to the terminal
in touchstone format.

The utility provides its own error correction.
It does not use the onboard calibrations features
of either nano.
You must calibrate your nano separately to use this utility.
The calibration data is stored in a npz file on your computer.

Lastly, the utility takes steps not to disturb your nano UI settings.
So you can sweep a different range of frequencies using nanocli than what the UI is sweeping,
and the nano UI will be unaffected.
Nanocli will neither upset your nano UI calibrations nor your UI frequency sweep
settings.

## How to Use

After calibration, just issue the following on the command line.



```
$ python3 nanocli.py
# MHz S MA R 50
0.01             0.089135     0.476     3.9155e-06    58.994     3.9155e-06    58.994       0.089135     0.476
2.5075            0.08893    -0.607     1.3271e-05   131.710     1.3271e-05   131.710        0.08893    -0.607
5.005            0.088876    -1.012      1.278e-05    53.047      1.278e-05    53.047       0.088876    -1.012
7.5025            0.08882    -1.434     2.4322e-05   100.367     2.4322e-05   100.367        0.08882    -1.434
10               0.088929    -2.007     6.6082e-06   -71.453     6.6082e-06   -71.453       0.088929    -2.007
```


If an error gets thrown, like not being able to find the device or ValueError, try again
or reset your device.  None of the nanos have a perfect USB interface.

## Walkthrough

First initialize the calibration file, setting the 
frequency sweep.


```
$ python3 nanocli.py --init --start 10e3 --stop 10e6 --points 101
```


Print details on the calibration file.


```
$ python3 nanocli.py --details
start:   0.01 MHz
stop:    10 MHz
points:  101
segment: 101
samples: 3
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
0.01             0.089125     0.467     1.5611e-05    27.222     1.5611e-05    27.222       0.089125     0.467
2.5075           0.088912    -0.588     5.6956e-06   150.334     5.6956e-06   150.334       0.088912    -0.588
5.005            0.088862    -1.011     1.5714e-05    59.061     1.5714e-05    59.061       0.088862    -1.011
7.5025           0.088835    -1.427      1.118e-05    95.214      1.118e-05    95.214       0.088835    -1.427
10               0.088934    -2.029     8.2497e-06   -69.122     8.2497e-06   -69.122       0.088934    -2.029
```


Return the results in dB.


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01           -21.001     0.466     -96.890    72.624     -96.890    72.624     -21.001     0.466
2.5075         -21.020    -0.586     -94.625   123.432     -94.625   123.432     -21.020    -0.586
5.005          -21.024    -1.020     -95.747   100.558     -95.747   100.558     -21.024    -1.020
7.5025         -21.030    -1.415     -99.224  -127.610     -99.224  -127.610     -21.030    -1.415
10             -21.017    -2.031    -107.803   167.261    -107.803   167.261     -21.017    -2.031
```


Write a s1p file to stdout.


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01           -21.000     0.467
2.5075         -21.021    -0.599
5.005          -21.026    -1.014
7.5025         -21.032    -1.448
10             -21.019    -2.005
```


Passing the --points option above
forces an interpolation of the calibration data
to the frequencies of the new sweep.  If this option was not given
the original 101 frequencies used for calibration would be swept
and without any interpolation of the calibration data.

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
usage: nanocli.py [-h] [--filename FILENAME] [--start START] [--stop STOP]
                  [--points POINTS] [--segment SEGMENT] [--samples SAMPLES]
                  [--device DEVICE] [-i] [-o] [-s] [-l] [-t] [-d] [-1] [--db]

optional arguments:
  -h, --help           show this help message and exit
  --filename FILENAME  calibration file (default: cal)
  --start START        start frequency (Hz) (default: None)
  --stop STOP          stop frequency (Hz) (default: None)
  --points POINTS      frequency points in sweep (default: None)
  --segment SEGMENT    frequency points in each sweep segment (default: None)
  --samples SAMPLES    samples per frequency (default: None)
  --device DEVICE      select device number (default: None)
  -i, --init           initialize calibration (default: False)
  -o, --open           open calibration (default: False)
  -s, --short          short calibration (default: False)
  -l, --load           load calibration (default: False)
  -t, --thru           thru calibration (default: False)
  -d, --details        show calibration details (default: False)
  -1, --one-port       output in s1p format (default: False)
  --db                 show in dB (default: False)
```



## On Calibration

The utility uses the (incomplete, one path) 12-term error model to correct
sweep measurements.  This is the same SOLT
calibration method that you use to calibrate the nano from its UI.

To calibrate the nano using the utility, first initialize the
calibration file with your frequency sweep.
If the calibration
file already exists, it will be overwritten.  By default
the name of the file is cal.npz.

Once intialized the frequency sweep for a given calibration file is fixed.
All calibrations will use the same sweep range set in the calibration
file.  This is because all calibration data within a single calibration file
must have measurements for the same set of frequencies.

## Interpolation of Calibration Data

By default, no interpolation is performed
on your calibration data when making a measurement.  
The frequencies for the measurement sweep are taken directly from 
the calibration file.  

If the range of the frequency sweep
is changed on the command line from that given 
in the calibration file,
the calibration data will be interpolated
to the new range.

Remember, the frequency range cannot be changed
when doing calibration.  But when making a measurement
sweep it can.

## Measurement Report Formats

All measurement output from the utility is
written to the terminal (using stdout).
By default the output will be formatted
for a s2p touchstone file.  If the --one option
is passed on the command line the output will be
formatted for a s1p touchstone file.

## Python Interface

Import this library using import nanocli.  The most important function
provided is called sweep.  It returns a (freq, data) tuple for the result.
freq is an array of frequencies points and data is a 2xN array
of s11 and s21 calibration corrected measurements.

The interface for sweep is as follows.  Changing the range
for the frequency sweep by passing values for
start, stop or points will force an interpolation of the calibration
data.

```python
frequencies, gammas = sweep(start=None, stop=None, points=None, filename='cal', samples=3, average=False, device=None)
```

For example:


```
$ python3 -c 'from nanocli import sweep; f,d = sweep(points=5); print(d)'
[[ 8.9124440e-02+7.088520e-04j  3.8100000e-06+1.867800e-05j]
 [ 8.8913552e-02-9.213630e-04j -9.2170000e-06+1.464600e-05j]
 [ 8.8833968e-02-1.579035e-03j  3.7710000e-06+1.145900e-05j]
 [ 8.8786024e-02-2.257115e-03j  9.2100000e-07+7.508000e-06j]
 [ 8.8881536e-02-3.125639e-03j  5.9300000e-06+8.244000e-06j]]
```

## Reason for This Utility

I needed the ability to perform a calibrated measurement from the terminal
or from a Jupyter Notebook, for example.  The original nano
had this ability through its (USB) serial interface and its "data" command.
However the new SAA2 does not.  It uses a special binary
protocol. Its measurements over the USB interface are also uncalibrated unlike the original nano. 
Lastly and probably, most importantly, you cannot control its UI
over USB.  So no more computer remote control visual operation of the
device like I was able to do with the original nano.
As a result this utility is intended to unify the two nanos to satisfy my above need
and do my remote control in Jupyter instead.

## Implementation Notes

In order to perform a measurement sweep on the original nano, the
utility first turns calibration off on the device.  Once the
measurement is made, the utility will turn calibration back on.
For the SAA2 nano, since its USB connection is always uncorrected
its UI is unaffected.

## Supported Nanovna Versions

For the NanoVNA, only versions 0.7.1 and higher of the firmware are supported.

## Derivation of Calibration

See the papers on Network Analyzer Error Models and Calibration Methods
by Doug Rytting.

![](cal.png)


