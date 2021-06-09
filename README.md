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
and do my remote control in Jupyter.

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
0.01             0.059563   -87.919        0.31412     2.345        0.31412     2.345       0.059563   -87.919
2.5075          0.0012087   119.948         1.3416    -3.936         1.3416    -3.936      0.0012087   119.948
5.005          0.00052141   -77.125        0.85057   -14.879        0.85057   -14.879     0.00052141   -77.125
7.5025          0.0020102   -63.101        0.78812   -13.479        0.78812   -13.479      0.0020102   -63.101
10               0.003653   -69.778        0.76721   -13.906        0.76721   -13.906       0.003653   -69.778
```


Return the results in dB.


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01           -24.529   -87.861     -10.057     2.483     -10.057     2.483     -24.529   -87.861
2.5075         -58.049   115.132       2.568    -3.931       2.568    -3.931     -58.049   115.132
5.005          -65.202   -76.546      -1.405   -14.878      -1.405   -14.878     -65.202   -76.546
7.5025         -53.863   -63.355      -2.065   -13.491      -2.065   -13.491     -53.863   -63.355
10             -48.916   -70.156      -2.302   -13.888      -2.302   -13.888     -48.916   -70.156
```


Output measurements in a format that can be read by numpy.


```
$ python3 nanocli.py --text --points 5
10000          0.00186252-0.0586606j       0.314745+0.0133235j
2507500     -0.000547051+0.00121898j        1.34073-0.0924701j
5005000     0.000234655-0.000582708j        0.821918-0.218422j
7502500      0.000886088-0.00172663j        0.766492-0.183885j
10000000      0.00123678-0.00345777j        0.744874-0.184215j
```


Write a s1p file to stdout.


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01           -24.617   -88.102
2.5075         -57.440   109.686
5.005          -64.339   -77.957
7.5025         -53.946   -59.154
10             -48.969   -66.259
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


