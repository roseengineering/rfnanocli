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
0.100000   1.81296e-02   -56.87 1.51673e-04   133.63 0.00000e+00     0.00 0.00000e+00     0.00
2.575000   1.05350e-02     6.97 4.01273e-05  -129.70 0.00000e+00     0.00 0.00000e+00     0.00
5.050000   1.16109e-02    12.28 3.37232e-05   -14.77 0.00000e+00     0.00 0.00000e+00     0.00
7.525000   1.28498e-02    15.76 1.86714e-05  -142.61 0.00000e+00     0.00 0.00000e+00     0.00
10.000000  1.40450e-02    17.45 1.43166e-04   -89.75 0.00000e+00     0.00 0.00000e+00     0.00
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
0.100000   1.86490e-02   -57.69 1.72704e-04   109.81 0.00000e+00     0.00 0.00000e+00     0.00
0.124750   1.56715e-02   -51.50 1.55659e-04   169.75 0.00000e+00     0.00 0.00000e+00     0.00
0.149500   1.41132e-02   -46.92 6.78835e-05   169.96 0.00000e+00     0.00 0.00000e+00     0.00
0.174250   1.29694e-02   -42.00 7.61136e-05  -160.44 0.00000e+00     0.00 0.00000e+00     0.00
0.199000   1.22575e-02   -37.97 1.72030e-05   149.76 0.00000e+00     0.00 0.00000e+00     0.00
0.223750   1.18081e-02   -35.07 8.82115e-05  -176.16 0.00000e+00     0.00 0.00000e+00     0.00
0.248500   1.13656e-02   -32.35 1.68591e-05  -108.08 0.00000e+00     0.00 0.00000e+00     0.00
0.273250   1.11271e-02   -29.73 2.68149e-05  -159.67 0.00000e+00     0.00 0.00000e+00     0.00
0.298000   1.07729e-02   -26.35 7.66936e-05   114.76 0.00000e+00     0.00 0.00000e+00     0.00
```


Write a s1p file to stdout.


```
$ nanocli --gamma | head
# MHz S DB R 50
0.100000   1.80675e-02   -56.47
0.124750   1.58397e-02   -51.83
0.149500   1.41285e-02   -47.01
0.174250   1.30293e-02   -42.46
0.199000   1.23160e-02   -38.24
0.223750   1.17124e-02   -35.11
0.248500   1.13105e-02   -32.39
0.273250   1.09172e-02   -28.92
0.298000   1.08279e-02   -26.92
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
$ python3 -c 'from nanocli import getvna; f,d = getvna()(start=3e6, stop=6e6); print(d)' | head
[[ 1.0703690e-02+1.565078e-03j -6.3440000e-05+1.142400e-05j]
 [ 1.0581026e-02+1.464269e-03j -4.9090000e-06-3.784000e-06j]
 [ 1.0590182e-02+1.483348e-03j  8.6610000e-06+1.083700e-05j]
 [ 1.0644534e-02+1.507456e-03j -5.1601000e-05+2.813800e-05j]
 [ 1.0647516e-02+1.574263e-03j  5.4448000e-05+8.637000e-06j]
 [ 1.0561992e-02+1.565354e-03j -2.9996000e-05-2.547500e-05j]
 [ 1.0592866e-02+1.469272e-03j -1.4870000e-06+2.220590e-04j]
 [ 1.0598958e-02+1.606484e-03j -3.9047000e-05-7.776700e-05j]
 [ 1.0594464e-02+1.477188e-03j -2.6555000e-05+7.411300e-05j]
 [ 1.0586636e-02+1.500278e-03j  2.9712000e-05+3.176400e-05j]
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


