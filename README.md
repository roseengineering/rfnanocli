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
0.01                    1    -0.000     0.00016717   -30.503     0.00016717   -30.503              1    -0.000
2.5075            0.99991    -0.215     1.7345e-05   -52.448     1.7345e-05   -52.448        0.99991    -0.215
5.005             0.99949    -0.380     1.7454e-05   103.846     1.7454e-05   103.846        0.99949    -0.380
7.5025            0.99938    -0.566     2.8688e-05   100.728     2.8688e-05   100.728        0.99938    -0.566
10                0.99941    -0.755     6.2399e-05    38.568     6.2399e-05    38.568        0.99941    -0.755
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
0.01                    1     0.000     0.00019456   -16.549     0.00019456   -16.549              1     0.000
2.5075             0.9997    -0.207     4.0955e-06   134.972     4.0955e-06   134.972         0.9997    -0.207
5.005              0.9995    -0.384     3.5709e-05  -132.236     3.5709e-05  -132.236         0.9995    -0.384
7.5025            0.99929    -0.573     2.7137e-05   -44.612     2.7137e-05   -44.612        0.99929    -0.573
10                0.99928    -0.767     2.2279e-05  -122.023     2.2279e-05  -122.023        0.99928    -0.767
```


Return the results in dB.


```
$ nanocli --db --points 5
# MHz S DB R 50
0.01             0.000     0.003     -74.530   -28.956     -74.530   -28.956       0.000     0.003
2.5075          -0.001    -0.205     -88.021    89.882     -88.021    89.882      -0.001    -0.205
5.005           -0.004    -0.377     -92.967  -137.741     -92.967  -137.741      -0.004    -0.377
7.5025          -0.005    -0.571     -88.338    90.442     -88.338    90.442      -0.005    -0.571
10              -0.006    -0.759    -113.257    11.093    -113.257    11.093      -0.006    -0.759
```


Write a s1p file to stdout.


```
$ nanocli -1 --db --points 5
# MHz S DB R 50
0.01            -0.000     0.001
2.5075          -0.000    -0.203
5.005           -0.004    -0.387
7.5025          -0.005    -0.573
10              -0.006    -0.747
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
               [--segment SEGMENT] [-d DEVICE] [-i] [-l] [-1] [--db]

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
[[ 9.99969065e-01+5.38062304e-05j  1.38835981e-04-7.12992623e-05j]
 [ 9.99864340e-01-3.35255917e-03j  1.78981572e-05-3.61735001e-05j]
 [ 9.99521136e-01-6.71732426e-03j  1.35255978e-05+2.68453732e-05j]
 [ 9.99423683e-01-9.88406688e-03j -4.32124361e-05+2.27922574e-05j]
 [ 9.99168038e-01-1.29039697e-02j -2.87871808e-06-3.46153975e-05j]]
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


