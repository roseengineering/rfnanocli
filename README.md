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
0.01             0.044126     0.561     3.4598e-05    -0.059     3.4598e-05    -0.059       0.044126     0.561
2.5075           0.044192    -0.508     9.5339e-06  -109.040     9.5339e-06  -109.040       0.044192    -0.508
5.005            0.044143    -0.898     8.2403e-06   130.601     8.2403e-06   130.601       0.044143    -0.898
7.5025           0.044195    -1.325       2.71e-06    74.702       2.71e-06    74.702       0.044195    -1.325
10               0.044137    -1.710     1.1795e-05   143.730     1.1795e-05   143.730       0.044137    -1.710
```


If an error gets thrown, like not being able to find the device or ValueError, try again
or reset your device.  None of the nanos have a perfect USB interface.

## Walkthrough

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
0.01             0.044114     0.549     2.6742e-05     4.648     2.6742e-05     4.648       0.044114     0.549
2.5075           0.044202    -0.510     6.9481e-06   179.697     6.9481e-06   179.697       0.044202    -0.510
5.005            0.044143    -0.902     4.7993e-06    73.008     4.7993e-06    73.008       0.044143    -0.902
7.5025           0.044196    -1.339     4.3726e-06  -132.574     4.3726e-06  -132.574       0.044196    -1.339
10               0.044132    -1.724     4.5905e-06    25.306     4.5905e-06    25.306       0.044132    -1.724
```


Return the results in dB.


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01           -27.100     0.593     -86.701    21.194     -86.701    21.194     -27.100     0.593
2.5075         -27.094    -0.494     -96.692   103.063     -96.692   103.063     -27.094    -0.494
5.005          -27.103    -0.893     -99.970    95.950     -99.970    95.950     -27.103    -0.893
7.5025         -27.095    -1.333    -106.747    30.071    -106.747    30.071     -27.095    -1.333
10             -27.105    -1.717    -109.812   -23.606    -109.812   -23.606     -27.105    -1.717
```


Write a s1p file to stdout.


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01           -27.105     0.606
2.5075         -27.090    -0.513
5.005          -27.104    -0.903
7.5025         -27.095    -1.340
10             -27.105    -1.713
```


Passing the --points option above
forces an interpolation of the calibration data
to the frequencies of the new sweep.  If this option was not given
the original 1001 frequencies used for calibration would be swept
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
                  [-f FILENAME] [-n SAMPLES] [--start START] [--stop STOP]
                  [--points POINTS]
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
  -1, --one             show s1p (default: False)
  --db                  show in dB (default: False)
  -f FILENAME, --filename FILENAME
                        calibration file (default: cal)
  -n SAMPLES, --samples SAMPLES
                        samples per frequency (default: 2)
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
sweep(start=None, stop=None, points=None, filename='cal.npz', samples=2)
```

For example:


```
$ python3 -c 'from nanocli import sweep; f,d = sweep(points=5); print(d)'
[[ 4.4122792e-02+4.4093325e-04j  2.5598750e-05+8.2660000e-06j]
 [ 4.4195800e-02-3.9940700e-04j  1.2575000e-07-3.6657500e-06j]
 [ 4.4135130e-02-6.9608475e-04j -5.4232500e-06+3.9350000e-07j]
 [ 4.4189484e-02-1.0305405e-03j  4.7625000e-07-1.9440000e-06j]
 [ 4.4107688e-02-1.3323305e-03j  2.5290000e-06+4.9197500e-06j]]
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

## Derivation of Calibration

See the papers on Network Analyzer Error Models and Calibration Methods
by Doug Rytting.

![](cal.png)


