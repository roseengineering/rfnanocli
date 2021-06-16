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
0.01             0.044165     0.605     1.9327e-05    15.877     1.9327e-05    15.877       0.044165     0.605
2.5075            0.04429    -0.515     2.9628e-06   -69.770     2.9628e-06   -69.770        0.04429    -0.515
5.005            0.044238    -0.903     1.0115e-05   141.117     1.0115e-05   141.117       0.044238    -0.903
7.5025           0.044286    -1.334     8.0525e-06    84.888     8.0525e-06    84.888       0.044286    -1.334
10               0.044225    -1.710     5.2198e-06   146.021     5.2198e-06   146.021       0.044225    -1.710
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
0.01             0.044195     0.616      2.992e-05    23.416      2.992e-05    23.416       0.044195     0.616
2.5075           0.044287    -0.511     9.9768e-06    70.444     9.9768e-06    70.444       0.044287    -0.511
5.005            0.044227    -0.894     7.5341e-06   109.686     7.5341e-06   109.686       0.044227    -0.894
7.5025           0.044277    -1.331     4.6032e-06   157.120     4.6032e-06   157.120       0.044277    -1.331
10               0.044232    -1.724     7.5435e-06   127.026     7.5435e-06   127.026       0.044232    -1.724
```


Return the results in dB.


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01           -27.092     0.621     -91.177    22.824     -91.177    22.824     -27.092     0.621
2.5075         -27.078    -0.508     -99.375   162.148     -99.375   162.148     -27.078    -0.508
5.005          -27.086    -0.888    -102.014    90.372    -102.014    90.372     -27.086    -0.888
7.5025         -27.075    -1.317    -109.702   146.238    -109.702   146.238     -27.075    -1.317
10             -27.087    -1.718    -101.636   114.733    -101.636   114.733     -27.087    -1.718
```


Write a s1p file to stdout.


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01           -27.094     0.602
2.5075         -27.072    -0.492
5.005          -27.086    -0.899
7.5025         -27.076    -1.311
10             -27.087    -1.702
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
[[ 4.4228162e-02+4.8912650e-04j  4.1508500e-05+1.1447000e-05j]
 [ 4.4264304e-02-3.9982975e-04j -9.5267500e-06+2.1297500e-06j]
 [ 4.4232590e-02-7.0093125e-04j  8.5805000e-06+4.4662500e-06j]
 [ 4.4277692e-02-1.0167055e-03j -5.6517500e-06+1.6457500e-06j]
 [ 4.4204814e-02-1.3300330e-03j -2.0990000e-06+9.5432500e-06j]]
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


