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
# MHz S MA R 50
0.100000     6.36445e-01    -0.67 2.32551e-05   136.98 0.00000e+00     0.00 0.00000e+00     0.00
2.575000     6.39618e-01   -16.72 5.06521e-05   113.48 0.00000e+00     0.00 0.00000e+00     0.00
5.050000     6.48363e-01   -32.95 3.84420e-05   139.69 0.00000e+00     0.00 0.00000e+00     0.00
7.525000     6.62878e-01   -49.68 3.35834e-05    99.99 0.00000e+00     0.00 0.00000e+00     0.00
10.000000    6.82772e-01   -67.19 4.12503e-05    78.01 0.00000e+00     0.00 0.00000e+00     0.00
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
# MHz S MA R 50
0.100000     6.36109e-01    -0.66 6.35929e-05   136.29 0.00000e+00     0.00 0.00000e+00     0.00
0.124750     6.36282e-01    -0.85 8.50108e-05   150.64 0.00000e+00     0.00 0.00000e+00     0.00
0.149500     6.36318e-01    -1.02 3.74528e-05   175.00 0.00000e+00     0.00 0.00000e+00     0.00
0.174250     6.36327e-01    -1.19 9.57142e-05   122.16 0.00000e+00     0.00 0.00000e+00     0.00
0.199000     6.36398e-01    -1.36 6.56578e-05   168.31 0.00000e+00     0.00 0.00000e+00     0.00
0.223750     6.36308e-01    -1.52 6.65813e-05   122.33 0.00000e+00     0.00 0.00000e+00     0.00
0.248500     6.36368e-01    -1.68 4.90364e-05   115.12 0.00000e+00     0.00 0.00000e+00     0.00
0.273250     6.36432e-01    -1.84 6.34475e-05  -160.78 0.00000e+00     0.00 0.00000e+00     0.00
0.298000     6.36343e-01    -2.01 4.00861e-05   105.09 0.00000e+00     0.00 0.00000e+00     0.00
```


Write a s1p file to stdout.


```
$ nanocli --gamma | head
# MHz S MA R 50
0.100000     6.36373e-01    -0.67
0.124750     6.36306e-01    -0.84
0.149500     6.36289e-01    -1.02
0.174250     6.36340e-01    -1.18
0.199000     6.36342e-01    -1.35
0.223750     6.36377e-01    -1.51
0.248500     6.36322e-01    -1.68
0.273250     6.36355e-01    -1.84
0.298000     6.36358e-01    -2.00
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
usage: nanocli [-h] [--calfile CALFILE] [--start START] [--stop STOP]
               [--points POINTS] [--init] [--open] [--short] [--load] [--thru]
               [--samples SAMPLES] [--average] [--gamma] [--device DEVICE]
               [-i] [-l]

optional arguments:
  -h, --help         show this help message and exit
  --calfile CALFILE  calibration file (default: cal.npz)
  --start START      start frequency (Hz) (default: None)
  --stop STOP        stop frequency (Hz) (default: None)
  --points POINTS    frequency points in sweep (default: None)
  --init             initialize calibration (default: False)
  --open             open calibration (default: False)
  --short            short calibration (default: False)
  --load             load calibration (default: False)
  --thru             thru calibration (default: False)
  --samples SAMPLES  samples per frequency (default: None)
  --average          average samples (default: False)
  --gamma            output only S11 (default: False)
  --device DEVICE    tty device name of nanovna to use (default: None)
  -i, --info         show calibration info (default: False)
  -l, --list         list available devices (default: False)
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

Setting the filename option will save the results to this file.
The function will then return the name of this file.  The file
extension must be either 's1p' or 's2p'.

```python
sweep = getvna(device=None, calname='cal')
sweep(start=None, stop=None, points=None, filename=None)
```

For example:


```
$ python3 -c 'from nanocli import getvna; f,d = getvna()(start=3e6, stop=6e6); print(d)' | head
[[ 6.03945344e-01-2.13709216e-01j -4.64940000e-05+7.38160000e-05j]
 [ 6.03728192e-01-2.14155776e-01j -3.82350000e-05+3.75260000e-05j]
 [ 6.03539712e-01-2.14678176e-01j  9.33400000e-06+6.19160000e-05j]
 [ 6.03384448e-01-2.15204416e-01j -1.79890000e-05+3.35190000e-05j]
 [ 6.03226368e-01-2.15712160e-01j -2.77610000e-05+5.45100000e-05j]
 [ 6.03012032e-01-2.16203120e-01j -2.74510000e-05+4.38000000e-05j]
 [ 6.02889792e-01-2.16796880e-01j  2.18270000e-05+4.54730000e-05j]
 [ 6.02720576e-01-2.17342912e-01j  3.94900000e-06+7.72860000e-05j]
 [ 6.02566464e-01-2.17785216e-01j -1.45040000e-05+4.35450000e-05j]
 [ 6.02368448e-01-2.18366880e-01j -1.37610000e-05+5.90930000e-05j]
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


