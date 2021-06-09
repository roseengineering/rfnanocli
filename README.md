# Nanocli

## Introduction

Nanocli is a utility for running measurement
sweeps off the original NanoVNA or the new NanoVNAv2
from the command line.
The sweep results are printed to the terminal
in touchstone format.

In addition the utility provides its own error correction.
It does not use the onboard calibrations features
of either nano.
You must calibrate your nano separately to use this utility.
The calibration data is stored in a npz file on your computer.

In order to perform a measurement sweep on the original nano, the
utility first turns calibration off on the device.  Once the
measurement is made, the utility will turn calibration back on.
It is recommended to use the same frequency sweep
with the original nano UI as well as with nanocli to
avoid UI interpolation issues.
For the v2 nano, since its USB connection is always uncorrected
its UI is unaffected.

## Reason for This Utility

I needed the ability to perform a calibrated measurement from the terminal
or from a Jupyter Notebook, for example.  The original nano
had this ability through its (usb) serial interface and its "data" command.
However the new NanoVNAv2 does not.  It uses a special binary
protocol. Its measurements over the usb interface are uncalibrated. 
Lastly and probably most importantly you cannot control its UI
over usb.  So no more computer remote control visual operation of the
device like I was able to do with the original nano.
As a result this utility is intended to unify the two nanos to satisfy my above need
and do my remote control in Jupyter instead.

## To Do

Add a python interface so the utility can be called programmaticaly say in
a ipython notebook.

## Calibration

The utility uses the 12-term error model to correct
sweep measurements.  This is the same SOLT
calibration method that you use to calibrate the nano from its UI.

To calibrate the nano using the utility, first initialize the
calibration file with your frequency sweep.
If the calibration
file already exists, it will be overwritten.  By default
the name of the file is cal.npz.

The frequency sweep for a given calibration file is always fixed.  All
subsequent calibrations will use the same sweep set in the calibration
file.  All calibration data within each calibration file
must have same frequency sweep range.

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
usage: nanocli.py [-h] [-f FILE] [-o] [-s] [-l] [-t] [-i] [-d] [-r] [-1]
                  [--db] [--text] [-n SAMPLES] [--start START] [--stop STOP]
                  [--points POINTS]
                  [command ...]

positional arguments:
  command               command (default: None)

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  calibration file (default: cal.npz)
  -o, --open            open calibration (default: False)
  -s, --short           short calibration (default: False)
  -l, --load            load calibration (default: False)
  -t, --thru            thru calibration (default: False)
  -i, --init            initialize calibration (default: False)
  -d, --details         show calibration details (default: False)
  -r, --raw             do not apply calibration (default: False)
  -1, --one             show s1p (default: False)
  --db                  show in dB (default: False)
  --text                send output to text file (default: False)
  -n SAMPLES, --samples SAMPLES
                        samples per frequency (default: 2)
  --start START         start frequency (Hz) (default: None)
  --stop STOP           stop frequency (Hz) (default: None)
  --points POINTS       frequency points (default: None)
```


## Utility Calibration

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
0.01             0.059216   -88.019        0.31498     2.376        0.31498     2.376       0.059216   -88.019
2.5075          0.0010958   115.851         1.3355    -4.410         1.3355    -4.410      0.0010958   115.851
5.005          0.00062724   -63.083        0.84892   -14.786        0.84892   -14.786     0.00062724   -63.083
7.5025          0.0019552   -62.061        0.78793   -13.430        0.78793   -13.430      0.0019552   -62.061
10              0.0036207   -67.964        0.76682   -13.872        0.76682   -13.872      0.0036207   -67.964
```


Return the results in dB.


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01           -24.625   -88.136     -10.030     2.358     -10.030     2.358     -24.625   -88.136
2.5075         -57.813   108.587       2.525    -4.371       2.525    -4.371     -57.813   108.587
5.005          -65.273   -71.330      -1.424   -14.798      -1.424   -14.798     -65.273   -71.330
7.5025         -53.467   -62.116      -2.069   -13.436      -2.069   -13.436     -53.467   -62.116
10             -48.685   -67.441      -2.303   -13.872      -2.303   -13.872     -48.685   -67.441
```


Output measurements in a format that can be read by numpy.


```
$ python3 nanocli.py --text --points 5
10000           0.00216908-0.059639j       0.314088+0.0130817j
2507500      -0.000237048+0.0017135j         1.33329-0.102145j
5005000     6.49465e-05-0.000546617j         0.820766-0.21667j
7502500       0.000868469-0.0019541j        0.766272-0.183291j
10000000      0.00126921-0.00329147j        0.744795-0.183795j
```


Write a s1p file to stdout.


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01           -24.550   -88.000
2.5075         -56.419   105.708
5.005          -63.831   -57.838
7.5025         -53.363   -62.882
10             -49.151   -69.363
```


Passing the --points option above
forces an interpolation of the calibration data
to the frequencies of the new sweep.  If this option was not given
the original 1001 frequencies used for calibration would be swept
and without any interpolation of the calibration data.

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

Passing the --text option writes the output
in a format compatible with numpy's loadtxt(fid, dtype='c16')
function.


