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
0.01              0.99999     0.000     0.00016946   -29.786     0.00016946   -29.786        0.99999     0.000
2.5075            0.99968    -0.157     0.00090342    80.356     0.00090342    80.356        0.99968    -0.157
5.005             0.99993    -0.348      0.0007697   -95.687      0.0007697   -95.687        0.99993    -0.348
7.5025            0.99973    -0.560     0.00023922    89.016     0.00023922    89.016        0.99973    -0.560
10                0.99932    -0.816     0.00031214    51.657     0.00031214    51.657        0.99932    -0.816
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
average: false
log:     false
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

Now run a sweep.  


```
$ nanocli --points 5
# MHz S MA R 50
0.01                    1     0.001     0.00018589   -32.255     0.00018589   -32.255              1     0.001
2.5075             0.9999    -0.263     0.00022359  -155.273     0.00022359  -155.273         0.9999    -0.263
5.005             0.99886    -0.319     0.00050646    66.798     0.00050646    66.798        0.99886    -0.319
7.5025            0.99901    -0.565     3.6397e-05   -10.997     3.6397e-05   -10.997        0.99901    -0.565
10                0.99964    -0.758     9.9414e-05  -153.155     9.9414e-05  -153.155        0.99964    -0.758
```


Write a s1p file to stdout.


```
$ nanocli -1 --points 5
# MHz S MA R 50
0.01              0.99998    -0.002
2.5075            0.99923    -0.250
5.005              1.0001    -0.411
7.5025            0.99947    -0.547
10                0.99966    -0.741
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
               [--points POINTS] [--samples SAMPLES] [--init]
               [--segment SEGMENT] [--average] [--log] [--open] [--short]
               [--load] [--thru] [--server] [--host HOST] [--port PORT]
               [-d DEVICE] [-i] [-l] [-1]

optional arguments:
  -h, --help            show this help message and exit
  --filename FILENAME   calibration file (default: cal.npz)
  --start START         start frequency (Hz) (default: None)
  --stop STOP           stop frequency (Hz) (default: None)
  --points POINTS       frequency points in sweep (default: None)
  --samples SAMPLES     samples per frequency (default: None)
  --init                initialize calibration (default: False)
  --segment SEGMENT     frequency points in each sweep segment (default: None)
  --average             average samples rather than median (default: False)
  --log                 use log frequency spacing (default: False)
  --open                open calibration (default: False)
  --short               short calibration (default: False)
  --load                load calibration (default: False)
  --thru                thru calibration (default: False)
  --server              enter REST server mode (default: False)
  --host HOST           REST server host name (default: 0.0.0.0)
  --port PORT           REST server port number (default: 8080)
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
[[ 9.99969363e-01-3.41171399e-05j  2.04826705e-04-1.61565840e-05j]
 [ 9.99873877e-01-2.22244672e-03j -1.10466965e-04-1.25451013e-04j]
 [ 1.00001419e+00-5.81184775e-03j -3.05408612e-04+6.03068620e-05j]
 [ 1.00000989e+00-1.02572078e-02j  1.34262256e-04+1.35331415e-04j]
 [ 9.99870121e-01-1.33099873e-02j -2.13925727e-04+5.97222708e-04j]]
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

![](res/cal.png)


