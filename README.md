# Nanocli

## Introduction

Nanocli is a utility for running measurement
sweeps off the original NanoVNA, NanoVNA-Hx (DiSload firmware), or the new SAA2 (NanoVNAv2)
from the command line.
The sweep results are printed to the terminal
in touchstone format.

The utility provides its own error correction.
It does not use the onboard calibrations features
of either nano.
You must calibrate your nano separately to use this utility.
The calibration data is stored in a npz file on your computer.

Note, the utility will disturb your nano UI settings (but not on the SAA2).
So if you sweep a different range of frequencies using nanocli than what the UI is sweeping,
the UI will be affected.
That said, nanocli will not upset your nano UI calibrations. They remain as they were.

## How to Use

After calibration, just issue the following on the command line.



```
$ nanocli
# MHz S DB R 50
0.100000   1.82305e-02   -57.16 4.20330e-05   124.47 0.00000e+00     0.00 0.00000e+00     0.00
2.575000   1.04345e-02     6.59 1.63317e-05  -137.17 0.00000e+00     0.00 0.00000e+00     0.00
5.050000   1.15557e-02    13.33 2.60198e-05    24.49 0.00000e+00     0.00 0.00000e+00     0.00
7.525000   1.28045e-02    15.85 3.25940e-05   177.34 0.00000e+00     0.00 0.00000e+00     0.00
10.000000  1.38885e-02    17.16 5.32466e-05   135.07 0.00000e+00     0.00 0.00000e+00     0.00
```


If an error gets thrown, like not being able to find the device or ValueError, try again
or reset your device.  None of the nanos have a perfect USB interface.

## Walkthrough

First initialize the calibration file, setting the 
frequency sweep.


```
$ nanocli --init --start 100e3 --stop 10e6 --points 401
```


Print details on the calibration file.


```
$ nanocli --info
start:   0.1 MHz
stop:    10 MHz
points:  401
samples: 3
average: false
cals:    <none>
```


According to the --details option, the calibration file currently has no calibration data.
So lets perform the SOLT calibrations.

```
$ nanocli --open
$ nanocli --short
$ nanocli --load
$ nanocli --thru
```

After calibration, any change in start, stop, and points will
cause new calibration points to be interpolated from the current
calibration for the sweep.  

Now let's run a sweep.  


```
$ nanocli | head
# MHz S DB R 50
0.100000   1.86329e-02   -58.05 3.47374e-05  -119.32 0.00000e+00     0.00 0.00000e+00     0.00
0.124750   1.58401e-02   -52.33 3.75332e-05  -179.82 0.00000e+00     0.00 0.00000e+00     0.00
0.149500   1.42232e-02   -47.46 7.80899e-05  -176.16 0.00000e+00     0.00 0.00000e+00     0.00
0.174250   1.32134e-02   -42.74 8.08887e-05   169.80 0.00000e+00     0.00 0.00000e+00     0.00
0.199000   1.23884e-02   -38.60 7.48856e-05   121.35 0.00000e+00     0.00 0.00000e+00     0.00
0.223750   1.16958e-02   -35.45 1.26412e-04   -76.12 0.00000e+00     0.00 0.00000e+00     0.00
0.248500   1.13386e-02   -32.08 1.01752e-04   -88.90 0.00000e+00     0.00 0.00000e+00     0.00
0.273250   1.09931e-02   -29.77 9.79434e-05    97.15 0.00000e+00     0.00 0.00000e+00     0.00
0.298000   1.08332e-02   -27.70 2.59980e-05  -117.97 0.00000e+00     0.00 0.00000e+00     0.00
```


Write a s1p file to stdout.


```
$ nanocli --gamma | head
# MHz S DB R 50
0.100000   1.86381e-02   -58.17
0.124750   1.58179e-02   -51.97
0.149500   1.42243e-02   -47.67
0.174250   1.29826e-02   -42.74
0.199000   1.23597e-02   -38.57
0.223750   1.18137e-02   -34.82
0.248500   1.13314e-02   -32.23
0.273250   1.10162e-02   -30.01
0.298000   1.08663e-02   -27.91
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

Another option is to build an executable file of nanocli.
To do this run:


```
$ sh build.sh
python res/zip.py -s 1 -o nanocli src/* src/*/*
echo '#!/usr/bin/env python3' | cat - nanocli.zip > nanocli
rm nanocli.zip
chmod 755 nanocli
```


## Command Line Usage

The utility's command line usage is as follows:


```
$ nanocli --help
usage: nanocli [-h] [--filename FILENAME] [--start START] [--stop STOP]
               [--init] [--open] [--short] [--load] [--thru] [--points POINTS]
               [--samples SAMPLES] [--average] [--gamma] [--device DEVICE]
               [--info] [-l]

optional arguments:
  -h, --help           show this help message and exit
  --filename FILENAME  calibration file (default: cal.npz)
  --start START        start frequency (Hz) (default: None)
  --stop STOP          stop frequency (Hz) (default: None)
  --init               initialize calibration (default: False)
  --open               open calibration (default: False)
  --short              short calibration (default: False)
  --load               load calibration (default: False)
  --thru               thru calibration (default: False)
  --points POINTS      frequency points in sweep (default: None)
  --samples SAMPLES    samples per frequency (default: None)
  --average            average samples (default: False)
  --gamma              output only S11 (default: False)
  --device DEVICE      tty device name of nanovna to use (default: None)
  --info               show calibration info (default: False)
  -l, --list           list available devices (default: False)
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
for a s2p touchstone file.  If the --gamma option
is passed on the command line the output will be
formatted for a s1p touchstone file.

## Python Interface

Import this library using import nanocli.  The function
getvna is provided.  After passing it the cal file, 
the device name, the start frequency, the stop frequency, and 
the number of frequency points to measure, it returns a function which 
performs the measurement.

When called this function returns a (freq, data) tuple result.
freq is an array of frequencies points.  data is a 2xN array
of s11 and s21 calibration corrected measurements.

The interface for sweep is as follows.  Changing the range
for the frequency sweep by passing values for
start, stop or points will force an interpolation of the calibration
data.  

```python
sweep = getvna(device=None, filename='cal')
sweep(start=None, stop=None)
```

For example:


```
$ python3 -c 'from nanocli import getvna; f,d = getvna()(points=5); print(d)'
Traceback (most recent call last):
  File "<string>", line 1, in <module>
TypeError: fn() got an unexpected keyword argument 'points'
```



## Reason for This Utility

I needed the ability to perform a calibrated measurement from the terminal
or from a Jupyter Notebook, for example.  The original nano
had this ability through its (USB) serial interface and its "data" command.
However the new SAA2 does not.  It uses a special binary
protocol. Its measurements over the USB interface are also uncalibrated unlike the original nano. 
Lastly and probably, most importantly, with the SSA2 you cannot control its UI
over USB.  So no more computer remote control visual operation of the
device like I was able to do with the original nanovna.
As a result this utility is intended to unify the two nanos to satisfy my above need
and do my remote control in Jupyter instead.

## Implementation Notes

In order to perform a measurement sweep on the original nano, the
utility first turns calibration off on the device.  Once the
measurement is made, the utility will turn calibration back on.
For the SAA2 nano, since its USB connection is always uncorrected
its UI and calibration is unaffected.

## Supported Nanovna Versions

For the NanoVNA, only versions 0.7.1 and higher of the firmware are supported.

## Derivation of Calibration

See the papers on Network Analyzer Error Models and Calibration Methods
by Doug Rytting.

![](res/cal.png)


