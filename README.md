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
$ nanocli
# MHz S MA R 50
0.01                    1    -0.001     0.00016205   -29.709     0.00016205   -29.709              1    -0.001
2.5075             0.9997    -0.195     4.6446e-05    26.198     4.6446e-05    26.198         0.9997    -0.195
5.005             0.99957    -0.387     4.0401e-05  -101.379     4.0401e-05  -101.379        0.99957    -0.387
7.5025            0.99941    -0.579      2.237e-05  -175.846      2.237e-05  -175.846        0.99941    -0.579
10                0.99957    -0.770     4.4616e-05  -130.526     4.4616e-05  -130.526        0.99957    -0.770
```


If an error gets thrown, like not being able to find the device or ValueError, try again
or reset your device.  None of the nanos have a perfect USB interface.

## Walkthrough

First initialize the calibration file, setting the 
frequency sweep.


```
$ nanocli --init --start 10e3 --stop 10e6 --points 101
```


Print details on the calibration file.


```
$ nanocli --info
start:   0.01 MHz
stop:    10 MHz
points:  101
segment: 101
samples: 3
average: False
log:     False
cals:   <none>
```


According to the --details option, the calibration file currently has no calibration data.
So lets perform the SOLT calibrations.

```
$ nanocli --open
$ nanocli --short
$ nanocli --load
$ nanocli --thru
```

Now run a sweep.  


```
$ nanocli --points 5
# MHz S MA R 50
0.01                    1     0.001     0.00017226   -27.352     0.00017226   -27.352              1     0.001
2.5075            0.99978    -0.210     6.8268e-05   -75.971     6.8268e-05   -75.971        0.99978    -0.210
5.005             0.99938    -0.393     4.1963e-05   -98.998     4.1963e-05   -98.998        0.99938    -0.393
7.5025            0.99942    -0.595     4.5497e-05   -70.027     4.5497e-05   -70.027        0.99942    -0.595
10                0.99956    -0.755     8.7168e-05   125.094     8.7168e-05   125.094        0.99956    -0.755
```


Write a s1p file to stdout.


```
$ nanocli -1 --points 5
# MHz S MA R 50
0.01               1.0001     0.003
2.5075            0.99973    -0.205
5.005             0.99958    -0.401
7.5025            0.99934    -0.588
10                0.99955    -0.763
```


Passing the --points option above
forces an interpolation of the calibration data
to the frequencies of the new sweep.  If this option was not given
the original 101 frequencies used for calibration would be swept
and without any interpolation of the calibration data.

## How to Install

First pip install the required python libraries by going into
the top directory of the repo and running:

```
$ pip install .
```


## Command Line Usage

The utility's command line usage is as follows:


```
$ nanocli --help
usage: nanocli [-h] [--filename FILENAME] [--start START] [--stop STOP]
               [--points POINTS] [--samples SAMPLES] [--init] [--open]
               [--short] [--load] [--thru] [--average] [--log]
               [--segment SEGMENT] [-d DEVICE] [-i] [-l] [-1]

optional arguments:
  -h, --help            show this help message and exit
  --filename FILENAME   calibration file (default: cal)
  --start START         start frequency (Hz) (default: None)
  --stop STOP           stop frequency (Hz) (default: None)
  --points POINTS       frequency points in sweep (default: None)
  --samples SAMPLES     samples per frequency (default: None)
  --init                initialize calibration (default: False)
  --open                open calibration (default: False)
  --short               short calibration (default: False)
  --load                load calibration (default: False)
  --thru                thru calibration (default: False)
  --average             average samples rather than median (default: False)
  --log                 use log frequency spacing (default: False)
  --segment SEGMENT     frequency points in each sweep segment (default: None)
  -d DEVICE, --device DEVICE
                        device name (default: None)
  -i, --info            show calibration info (default: False)
  -l, --list            list devices (default: False)
  -1, --one-port        output in s1p format (default: False)
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

Import this library using import nanocli.  The function
getvna is provided.  After passing it the cal file, 
the device name, the start frequency, the stop frequency, and 
the number of frequency points to measure, it returns a function which 
performs the measurement returning a (freq, data) tuple result.
freq is an array of frequencies points.  data is a 2xN array
of s11 and s21 calibration corrected measurements.

The interface for sweep is as follows.  Changing the range
for the frequency sweep by passing values for
start, stop or points will force an interpolation of the calibration
data.

```python
fn = getvna(start=None, stop=None, points=None, device=None, filename='cal')
freq, gamma = sweep(samples=3)
```

For example:


```
$ python3 -c 'from nanocli import getvna; f,d = getvna(points=5)(); print(d)'
[[ 1.00004053e+00+1.09104440e-05j  1.34607777e-04-1.03579834e-04j]
 [ 9.99947548e-01-3.66589241e-03j  4.82592732e-05+1.26874074e-05j]
 [ 9.99438643e-01-6.82144705e-03j  1.65728852e-05-7.53719360e-06j]
 [ 9.99459743e-01-9.98111162e-03j -3.32333148e-05+2.57370993e-05j]
 [ 9.99396026e-01-1.35567850e-02j -6.63278624e-05-1.43684447e-05j]]
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


