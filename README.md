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
0.01             0.093974     1.675     7.5289e-06    54.116     7.5289e-06    54.116       0.093974     1.675
2.5075            0.09413    -0.016     3.4944e-05    84.075     3.4944e-05    84.075        0.09413    -0.016
5.005            0.094092    -0.469     2.6199e-05    65.891     2.6199e-05    65.891       0.094092    -0.469
7.5025           0.094064    -0.899      4.349e-05  -146.059      4.349e-05  -146.059       0.094064    -0.899
10               0.094043    -1.384     2.7174e-05   117.076     2.7174e-05   117.076       0.094043    -1.384
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
start:  0.01 MHz
stop:   10 MHz
points: 101
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
0.01             0.093972     1.667     1.9348e-05    30.642     1.9348e-05    30.642       0.093972     1.667
2.5075           0.094143    -0.000      3.842e-05  -129.195      3.842e-05  -129.195       0.094143    -0.000
5.005            0.094085    -0.461     3.3425e-05   146.259     3.3425e-05   146.259       0.094085    -0.461
7.5025           0.094068    -0.911      1.362e-05   175.827      1.362e-05   175.827       0.094068    -0.911
10               0.094029    -1.357     2.2766e-05    88.815     2.2766e-05    88.815       0.094029    -1.357
```


Return the results in dB.


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01           -20.539     1.677     -88.685   125.798     -88.685   125.798     -20.539     1.677
2.5075         -20.526     0.011     -89.053    75.524     -89.053    75.524     -20.526     0.011
5.005          -20.527    -0.466     -91.642  -108.304     -91.642  -108.304     -20.527    -0.466
7.5025         -20.533    -0.918     -91.736   139.076     -91.736   139.076     -20.533    -0.918
10             -20.535    -1.374     -94.096    69.628     -94.096    69.628     -20.535    -1.374
```


Write a s1p file to stdout.


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01           -20.541     1.669
2.5075         -20.526    -0.001
5.005          -20.530    -0.466
7.5025         -20.531    -0.896
10             -20.534    -1.381
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
usage: nanocli.py [-h] [-i] [-o] [-s] [-l] [-t] [-d] [-r] [-1] [--db]
                  [--average] [-f FILENAME] [-n SAMPLES] [--device DEVICE]
                  [--start START] [--stop STOP] [--points POINTS]
                  [command ...]

positional arguments:
  command               command (default: None)

optional arguments:
  -h, --help            show this help message and exit
  -i, --init            initialize calibration (default: False)
  -o, --open            open calibration (default: False)
  -s, --short           short calibration (default: False)
  -l, --load            load calibration (default: False)
  -t, --thru            thru calibration (default: False)
  -d, --details         show calibration details (default: False)
  -r, --raw             do not apply calibration (default: False)
  -1, --one-port        output in s1p format (default: False)
  --db                  show in dB (default: False)
  --average             take average of samples, not median (default: False)
  -f FILENAME, --filename FILENAME
                        calibration file (default: cal)
  -n SAMPLES, --samples SAMPLES
                        samples per frequency (default: 3)
  --device DEVICE       select device number (default: None)
  --start START         start frequency (Hz) (default: None)
  --stop STOP           stop frequency (Hz) (default: None)
  --points POINTS       frequency points (default: None)
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

Import this library using import nanocli.  There is only one function
provided called sweep.  It returns a (freq, data) tuple for the result.
freq is an array of frequencies points and data is a 2xN array
of s11 and s21 calibration corrected measurements.

The interface for sweep is as follows.  Changing the range
for the frequency sweep by passing values for
start, stop or points will force an interpolation of the calibration
data.

```python
sweep(start=None, stop=None, points=None, filename='cal', samples=3, average=False, device=None)
```

For example:


```
$ python3 -c 'from nanocli import sweep; f,d = sweep(points=5); print(d)'
[[ 9.3944936e-02+2.749016e-03j  1.6728000e-05-4.386000e-06j]
 [ 9.4144752e-02-1.526400e-05j -8.0720000e-06+3.125800e-05j]
 [ 9.4082416e-02-7.480370e-04j  1.4800000e-06+1.526800e-05j]
 [ 9.4072736e-02-1.502874e-03j -1.9288000e-05+3.392600e-05j]
 [ 9.4001656e-02-2.262796e-03j  7.4610000e-06-5.669000e-06j]]
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


