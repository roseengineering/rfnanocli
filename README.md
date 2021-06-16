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
0.01             0.044138     0.613     4.6703e-05    11.717     4.6703e-05    11.717       0.044138     0.613
2.5075           0.044183    -0.500     9.7262e-06   160.101     9.7262e-06   160.101       0.044183    -0.500
5.005            0.044131    -0.900     4.0746e-06    26.672     4.0746e-06    26.672       0.044131    -0.900
7.5025           0.044185    -1.333     1.0284e-05    94.168     1.0284e-05    94.168       0.044185    -1.333
10               0.044133    -1.706     8.6263e-06   143.810     8.6263e-06   143.810       0.044133    -1.706
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
0.01             0.044138     0.613     4.6703e-05    11.717     4.6703e-05    11.717       0.044138     0.613
2.5075           0.044183    -0.500     9.7262e-06   160.101     9.7262e-06   160.101       0.044183    -0.500
5.005            0.044131    -0.900     4.0746e-06    26.672     4.0746e-06    26.672       0.044131    -0.900
7.5025           0.044185    -1.333     1.0284e-05    94.168     1.0284e-05    94.168       0.044185    -1.333
10               0.044133    -1.706     8.6263e-06   143.810     8.6263e-06   143.810       0.044133    -1.706
```


Return the results in dB.


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01           -27.109     0.623     -89.578    44.892     -89.578    44.892     -27.109     0.623
2.5075         -27.093    -0.537    -104.881   -26.210    -104.881   -26.210     -27.093    -0.537
5.005          -27.104    -0.894    -114.070   150.155    -114.070   150.155     -27.104    -0.894
7.5025         -27.095    -1.327    -104.457   163.831    -104.457   163.831     -27.095    -1.327
10             -27.105    -1.701    -113.038   155.510    -113.038   155.510     -27.105    -1.701
```


Write a s1p file to stdout.


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01           -27.105     0.583
2.5075         -27.092    -0.517
5.005          -27.104    -0.905
7.5025         -27.094    -1.337
10             -27.106    -1.704
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
[[ 4.4120084e-02+4.36676750e-04j  3.3317250e-05+5.46100000e-06j]
 [ 4.4178758e-02-4.12804250e-04j -3.4230000e-06-7.77625000e-06j]
 [ 4.4128226e-02-6.95219250e-04j  2.2577500e-06+1.20725000e-06j]
 [ 4.4170078e-02-1.03247375e-03j -5.3662500e-06+3.44550000e-06j]
 [ 4.4113516e-02-1.32664650e-03j -2.0900000e-06-7.23000000e-07j]]
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


