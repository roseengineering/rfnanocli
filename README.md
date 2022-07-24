# Nanocli

## Introduction

Nanocli is a utility for running measurement
sweeps off the original NanoVNA, NanoVNA-Hx (DiSload firmware), or the new SAA2 (NanoVNAv2)
from the command line.
The sweep results are printed to the terminal
in touchstone format.

The utility provides its own error correction.
It does not use the onboard calibrations features
of either nano.
You must calibrate your nano separately to use this utility.
The calibration data is stored in a npz file on your computer.

Note, the utility will disturb your nano UI settings (but not on the SAA2).
So if you sweep a different range of frequencies using nanocli than what the UI is sweeping,
the UI will be affected.
That said, nanocli will not upset your nano UI calibrations. They remain as they were.

## How to Use

After calibration, just issue the following on the command line.



```
$ nanocli
# MHz S DB R 50
0.010000   6.37082e-01     0.78 1.16755e-04  -176.23 0.00000e+00     0.00 0.00000e+00     0.00
2.507500   6.40304e-01    -0.64 8.56011e-05   100.21 0.00000e+00     0.00 0.00000e+00     0.00
5.005000   6.40406e-01    -1.01 7.13514e-05   124.75 0.00000e+00     0.00 0.00000e+00     0.00
7.502500   6.40326e-01    -1.43 8.98970e-05   166.18 0.00000e+00     0.00 0.00000e+00     0.00
10.000000  6.40227e-01    -1.82 1.28297e-04   146.16 0.00000e+00     0.00 0.00000e+00     0.00
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
samples: 3
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

After calibration, any change in start, stop, and points will
cause new calibration points to be interpolated from the current
calibration for the sweep.  

Now let's run a sweep.  


```
$ nanocli --points 5
# MHz S DB R 50
0.010000   6.37023e-01     0.79 8.05478e-05  -168.82 0.00000e+00     0.00 0.00000e+00     0.00
2.507500   6.40386e-01    -0.64 7.64227e-05   129.30 0.00000e+00     0.00 0.00000e+00     0.00
5.005000   6.40361e-01    -1.03 2.10763e-04   149.06 0.00000e+00     0.00 0.00000e+00     0.00
7.502500   6.40220e-01    -1.41 1.05194e-04    98.22 0.00000e+00     0.00 0.00000e+00     0.00
10.000000  6.40273e-01    -1.81 1.39570e-04   116.61 0.00000e+00     0.00 0.00000e+00     0.00
```


Write a s1p file to stdout.


```
$ nanocli --gamma --points 5
# MHz S DB R 50
0.010000   6.37070e-01     0.78
2.507500   6.40362e-01    -0.65
5.005000   6.40413e-01    -1.01
7.502500   6.40350e-01    -1.40
10.000000  6.40260e-01    -1.82
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

Another option is to build an executable file of nanocli.
To do this run:


```
$ sh build.sh
python res/zip.py -s 1 -o nanocli src/* src/*/*
echo '#!/usr/bin/env python3' | cat - nanocli.zip > nanocli
rm nanocli.zip
chmod 755 nanocli
```


## Command Line Usage

The utility's command line usage is as follows:


```
$ nanocli --help
usage: nanocli [-h] [--filename FILENAME] [--start START] [--stop STOP]
               [--points POINTS] [--samples SAMPLES] [--init] [--open]
               [--short] [--load] [--thru] [--server] [--hostname HOSTNAME]
               [--port PORT] [--save SAVE] [--recall RECALL] [--average]
               [--gamma] [--device DEVICE] [--info] [-l]

optional arguments:
  -h, --help           show this help message and exit
  --filename FILENAME  calibration file (default: cal.npz)
  --start START        start frequency (Hz) (default: None)
  --stop STOP          stop frequency (Hz) (default: None)
  --points POINTS      frequency points in sweep (default: None)
  --samples SAMPLES    samples per frequency (default: None)
  --init               initialize calibration (default: False)
  --open               open calibration (default: False)
  --short              short calibration (default: False)
  --load               load calibration (default: False)
  --thru               thru calibration (default: False)
  --server             enter REST server mode (default: False)
  --hostname HOSTNAME  REST server host name (default: 0.0.0.0)
  --port PORT          REST server port number (default: 8080)
  --save SAVE          save calibration file (default: None)
  --recall RECALL      load calibration file (default: None)
  --average            average samples (default: False)
  --gamma              output only S11 (default: False)
  --device DEVICE      tty device name of nanovna to use (default: None)
  --info               show calibration info (default: False)
  -l, --list           list available devices (default: False)
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
for a s2p touchstone file.  If the --gamma option
is passed on the command line the output will be
formatted for a s1p touchstone file.

## REST Server

Passing the --server option starts the REST server for
remote control of your NanoVNAs.

The following REST commands display or update the current
value of the corresponding command line setting.  For PUT
(or POST), pass the value of the option to set in the body 
of your request as a text string.  To reset all the options
back to their defaults use the /reset REST command

```
GET or PUT /start
GET or PUT /stop
GET or PUT /points
GET or PUT /samples
GET or PUT /average
GET /reset
```

To create, get details about, load or save a calibration file use the 
following REST commands.  To save the current calibration to a file or 
to load (ie. recall) a file as the current calibration, 
pass its name as a text string in the request body.

```
GET /init
GET /info
PUT /save
PUT /recall
```

The following REST commands will perform a sweep on a NanoVNA and then
either save the results to the current calibration or return the results
in the response body using the touchstone file format.

```
GET /
GET /gamma
GET /open
GET /short
GET /load
GET /thru
```

For example to create a current calibration from 7.000Mhz to 7.060 MHz, use:

```
$ curl -d 7.00e6 http://localhost:8080/start
$ curl -d 7.06e6 http://localhost:8080/stop
$ curl -d 5 http://localhost:8080/samples
$ curl http://localhost:8080/init
$ curl http://localhost:8080/open
$ curl http://localhost:8080/short
$ curl http://localhost:8080/load
$ curl http://localhost:8080/thru
$ curl -d crystal http://localhost:8080/save
$ curl -d crystal http://localhost:8080/recall
$ curl http://localhost:8080/
```

## Python Interface

Import this library using import nanocli.  The function
getvna is provided.  After passing it the cal file, 
the device name, the start frequency, the stop frequency, and 
the number of frequency points to measure, it returns a function which 
performs the measurement.  (To access the nanovna over REST use getremote i
nstead of getvna.)

When called this function returns a (freq, data) tuple result.
freq is an array of frequencies points.  data is a 2xN array
of s11 and s21 calibration corrected measurements.

The interface for sweep is as follows.  Changing the range
for the frequency sweep by passing values for
start, stop or points will force an interpolation of the calibration
data.  

```python
sweep = getremote(hostname='127.0.0.1', port=8080)
sweep = getvna(device=None, filename='cal')
sweep(start=None, stop=None, points=None, samples=None, average=None, gamma=None)
```

For example:


```
$ python3 -c 'from nanocli import getvna; f,d = getvna()(points=5); print(d)'
[[ 6.36909376e-01+8.7103100e-03j -4.34980000e-05-1.2667600e-04j]
 [ 6.40288576e-01-7.1707060e-03j -6.31060000e-05-1.9919000e-05j]
 [ 6.40350016e-01-1.1563366e-02j -1.17534000e-04+1.1852800e-04j]
 [ 6.40137856e-01-1.5716456e-02j -1.05928000e-04-1.9051000e-05j]
 [ 6.39925696e-01-2.0305866e-02j -1.32174000e-04+9.9447000e-05j]]
```



## Reason for This Utility

I needed the ability to perform a calibrated measurement from the terminal
or from a Jupyter Notebook, for example.  The original nano
had this ability through its (USB) serial interface and its "data" command.
However the new SAA2 does not.  It uses a special binary
protocol. Its measurements over the USB interface are also uncalibrated unlike the original nano. 
Lastly and probably, most importantly, with the SSA2 you cannot control its UI
over USB.  So no more computer remote control visual operation of the
device like I was able to do with the original nanovna.
As a result this utility is intended to unify the two nanos to satisfy my above need
and do my remote control in Jupyter instead.

## Implementation Notes

In order to perform a measurement sweep on the original nano, the
utility first turns calibration off on the device.  Once the
measurement is made, the utility will turn calibration back on.
For the SAA2 nano, since its USB connection is always uncorrected
its UI and calibration is unaffected.

## Supported Nanovna Versions

For the NanoVNA, only versions 0.7.1 and higher of the firmware are supported.

## Derivation of Calibration

See the papers on Network Analyzer Error Models and Calibration Methods
by Doug Rytting.

![](res/cal.png)


