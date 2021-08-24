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
0.01             0.089266     0.496     1.7928e-05    18.599     1.7928e-05    18.599       0.089266     0.496
2.5075           0.089081    -0.588     1.2726e-05   134.516     1.2726e-05   134.516       0.089081    -0.588
5.005            0.089032    -1.005     1.3804e-05  -173.106     1.3804e-05  -173.106       0.089032    -1.005
7.5025           0.088987    -1.448     1.2941e-05    81.902     1.2941e-05    81.902       0.088987    -1.448
10               0.089092    -2.038     1.4707e-05   -91.418     1.4707e-05   -91.418       0.089092    -2.038
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
0.01             0.089271     0.487     2.5191e-05    44.620     2.5191e-05    44.620       0.089271     0.487
2.5075           0.089098    -0.585     8.0465e-06   158.722     8.0465e-06   158.722       0.089098    -0.585
5.005            0.089003    -1.007     8.1686e-06    65.481     8.1686e-06    65.481       0.089003    -1.007
7.5025           0.088994    -1.443     1.8634e-05   119.377     1.8634e-05   119.377       0.088994    -1.443
10               0.089086    -2.046     1.4256e-05  -103.703     1.4256e-05  -103.703       0.089086    -2.046
```


Return the results in dB.


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01           -20.985     0.518     -90.031    52.289     -90.031    52.289     -20.985     0.518
2.5075         -21.003    -0.582    -100.514    99.897    -100.514    99.897     -21.003    -0.582
5.005          -21.012    -1.024    -100.893  -139.045    -100.893  -139.045     -21.012    -1.024
7.5025         -21.015    -1.443    -100.055   130.609    -100.055   130.609     -21.015    -1.443
10             -21.004    -2.053    -103.857  -127.022    -103.857  -127.022     -21.004    -2.053
```


Write a s1p file to stdout.


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01           -20.986     0.501
2.5075         -21.003    -0.588
5.005          -21.012    -1.029
7.5025         -21.016    -1.448
10             -21.004    -2.058
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

Import this library using import nanocli.  The most important function
provided is called sweep.  It returns a (freq, data) tuple for the result.
freq is an array of frequencies points and data is a 2xN array
of s11 and s21 calibration corrected measurements.

The interface for sweep is as follows.  Changing the range
for the frequency sweep by passing values for
start, stop or points will force an interpolation of the calibration
data.

```python
frequencies, gammas = sweep(start=None, stop=None, points=None, filename='cal', samples=3, average=False, device=None)
```

For example:


```
$ python3 -c 'from nanocli import sweep; f,d = sweep(points=5); print(d)'
[[ 8.9254208e-02+7.586870e-04j  5.0490000e-06+1.374700e-05j]
 [ 8.9055744e-02-9.216820e-04j -4.2050000e-06+1.666500e-05j]
 [ 8.9008856e-02-1.558015e-03j  1.6700000e-06+9.516000e-06j]
 [ 8.8942384e-02-2.253689e-03j -3.9160000e-06+4.923000e-06j]
 [ 8.9029880e-02-3.184959e-03j  6.5470000e-06+1.693000e-06j]]
```


The other two public functions provided are:

```python
freq_start, freq_stop = range_timedomain(freq_center, time_span, points)
times, magnitude_db = timedomain(frequencies, gammas)
```

Use these functions to convert the S11 frequency measurements of
a bandpass filter into the time domain.  

Specifically the function range\_timedomain() returns the
start and stop frequencies which will create
a time domain result with the specified time span for the given 
number of frequency points.
The function timedomain() does the actual IFFT transform 
on the frequency domain data into the time domain.

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


