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
0.01              0.97584     1.834     0.00012113  -119.674     0.00012113  -119.674        0.97584     1.834
2.5075             1.9202   -18.077     3.3242e-05   132.125     3.3242e-05   132.125         1.9202   -18.077
5.005              1.1534   -14.490     2.3133e-05   -79.187     2.3133e-05   -79.187         1.1534   -14.490
7.5025             1.0944    -3.152     3.4886e-05   -18.699     3.4886e-05   -18.699         1.0944    -3.152
10                 1.0823    -3.435     5.5682e-05   145.872     5.5682e-05   145.872         1.0823    -3.435
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
0.01              0.97591     1.847     8.9378e-05  -127.872     8.9378e-05  -127.872        0.97591     1.847
2.5075               1.92   -18.095     5.1951e-05   -68.669     5.1951e-05   -68.669           1.92   -18.095
5.005              1.1534   -14.489     3.6782e-05  -145.827     3.6782e-05  -145.827         1.1534   -14.489
7.5025             1.0947    -3.145     4.0249e-05   -59.058     4.0249e-05   -59.058         1.0947    -3.145
10                  1.082    -3.447      2.077e-05   -31.293      2.077e-05   -31.293          1.082    -3.447
```


Return the results in dB.


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01            -0.214     1.824     -83.182  -121.150     -83.182  -121.150      -0.214     1.824
2.5075           5.664   -18.066     -95.597    -3.717     -95.597    -3.717       5.664   -18.066
5.005            1.239   -14.485     -91.385   137.163     -91.385   137.163       1.239   -14.485
7.5025           0.785    -3.166     -97.839   -91.152     -97.839   -91.152       0.785    -3.166
10               0.686    -3.441    -109.696   172.968    -109.696   172.968       0.686    -3.441
```


Write a s1p file to stdout.


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01            -0.211     1.858
2.5075           5.664   -18.069
5.005            1.240   -14.491
7.5025           0.784    -3.160
10               0.684    -3.441
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
                  [--average] [-f FILENAME] [-n SAMPLES] [--start START]
                  [--stop STOP] [--points POINTS]
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
  --average             take average of samples instead of median (default:
                        False)
  -f FILENAME, --filename FILENAME
                        calibration file (default: cal)
  -n SAMPLES, --samples SAMPLES
                        samples per frequency (default: 3)
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
[[ 9.75414472e-01+3.13345244e-02j -5.46586611e-05-9.65594406e-05j]
 [ 1.82587569e+00-5.95024906e-01j  4.21159824e-06-2.02978986e-05j]
 [ 1.11667080e+00-2.88781466e-01j  1.05476601e-05-2.25238450e-05j]
 [ 1.09297301e+00-5.99740960e-02j -1.90277844e-05-2.13004279e-05j]
 [ 1.08010888e+00-6.49891351e-02j  7.14493908e-06+2.24043530e-05j]]
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


