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
0.01                    1    -0.005     0.00017708     1.765     0.00017708     1.765              1    -0.005
2.5075            0.99979    -0.209     5.1072e-05   158.128     5.1072e-05   158.128        0.99979    -0.209
5.005             0.99951    -0.399     4.4152e-05   -85.685     4.4152e-05   -85.685        0.99951    -0.399
7.5025            0.99944    -0.590     5.0312e-06   117.518     5.0312e-06   117.518        0.99944    -0.590
10                0.99941    -0.774     2.6698e-05   -36.176     2.6698e-05   -36.176        0.99941    -0.774
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
0.01              0.99996    -0.004     0.00012047   -28.434     0.00012047   -28.434        0.99996    -0.004
2.5075             0.9998    -0.192     5.1572e-05   -91.993     5.1572e-05   -91.993         0.9998    -0.192
5.005             0.99963    -0.403      6.231e-05  -167.956      6.231e-05  -167.956        0.99963    -0.403
7.5025            0.99963    -0.580     3.2299e-05  -157.186     3.2299e-05  -157.186        0.99963    -0.580
10                0.99934    -0.785     7.5902e-05   -79.865     7.5902e-05   -79.865        0.99934    -0.785
```


Return the results in dB.


```
$ nanocli --db --points 5
# MHz S DB R 50
0.01            -0.000     0.002     -75.539   -26.599     -75.539   -26.599      -0.000     0.002
2.5075          -0.000    -0.215    -104.084  -171.109    -104.084  -171.109      -0.000    -0.215
5.005           -0.005    -0.406     -93.385   -10.947     -93.385   -10.947      -0.005    -0.406
7.5025          -0.004    -0.593     -86.800    83.780     -86.800    83.780      -0.004    -0.593
10              -0.006    -0.760     -98.618   -16.150     -98.618   -16.150      -0.006    -0.760
```


Write a s1p file to stdout.


```
$ nanocli -1 --db --points 5
# MHz S DB R 50
0.01             0.000     0.003
2.5075          -0.003    -0.221
5.005           -0.005    -0.403
7.5025          -0.003    -0.583
10              -0.004    -0.777
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
               [--points POINTS] [--segment SEGMENT] [--samples SAMPLES]
               [--init] [--open] [--short] [--load] [--thru] [-d DEVICE] [-i]
               [-l] [-1] [--db]

optional arguments:
  -h, --help            show this help message and exit
  --filename FILENAME   calibration file (default: cal)
  --start START         start frequency (Hz) (default: None)
  --stop STOP           stop frequency (Hz) (default: None)
  --points POINTS       frequency points in sweep (default: None)
  --segment SEGMENT     frequency points in each sweep segment (default: None)
  --samples SAMPLES     samples per frequency (default: 3)
  --init                initialize calibration (default: False)
  --open                open calibration (default: False)
  --short               short calibration (default: False)
  --load                load calibration (default: False)
  --thru                thru calibration (default: False)
  -d DEVICE, --device DEVICE
                        device name (default: None)
  -i, --info            show calibration info (default: False)
  -l, --list            list devices (default: False)
  -1, --one-port        output in s1p format (default: False)
  --db                  show in dB (default: False)
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
[[ 9.99951959e-01+5.18392771e-05j  1.77253969e-04-8.00350681e-05j]
 [ 9.99956489e-01-3.53892613e-03j  6.22402877e-06-3.27453017e-06j]
 [ 9.99507785e-01-7.05986843e-03j -1.09514222e-05+1.62320212e-05j]
 [ 9.99439120e-01-1.01066474e-02j -2.29533762e-05+6.32321462e-05j]
 [ 9.99375045e-01-1.35249803e-02j  7.42822886e-06+6.88899308e-06j]]
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


