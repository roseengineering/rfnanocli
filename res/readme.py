
import subprocess 


def spawn(command):
    proc = subprocess.Popen('PYTHONPATH=src PATH=".:$PATH" ' + command, shell=True, stdout=subprocess.PIPE)
    proc.wait()
    return ''

def run(command, language=""):
    proc = subprocess.Popen('2>&1 PYTHONPATH=src PATH=".:$PATH" ' + command, shell=True, stdout=subprocess.PIPE)
    proc.wait()
    buf = proc.stdout.read().decode()
    return f"""
```{language}
$ {command}
{buf}\
```
"""


print(f"""\
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

The utility however does disturb your nano UI settings.
So if you sweep a different range of frequencies using nanocli than what the UI is sweeping,
the nano UI sweep will be affected (but not on the SAA2).
However nanocli will not upset your nano UI calibrations.

## How to Use

After calibration, just issue the following on the command line.

{spawn("nanocli --init --start 10e3 --stop 10e6 --points 5")}
{run("nanocli")}

If an error gets thrown, like not being able to find the device or ValueError, try again
or reset your device.  None of the nanos have a perfect USB interface.

## Walkthrough

First initialize the calibration file, setting the 
frequency sweep.

{run("nanocli --init --start 10e3 --stop 10e6 --points 101")}

Print details on the calibration file.

{run("nanocli --info")}

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

{run("nanocli --points 5")}

Write a s1p file to stdout.

{run("nanocli --gamma --points 5")}

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

{run("sh build.sh")}

## Command Line Usage

The utility's command line usage is as follows:

{run("nanocli --help")}


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
performs the measurement returning a (freq, data) tuple result.
freq is an array of frequencies points.  data is a 2xN array
of s11 and s21 calibration corrected measurements.

The interface for sweep is as follows.  Changing the range
for the frequency sweep by passing values for
start, stop or points will force an interpolation of the calibration
data.

```python
sweep = getvna(device=None, filename='cal')
sweep(start=None, stop=None, points=None, gamma=False, samples=None)
```

For example:

{run("python3 -c 'from nanocli import getvna; f,d = getvna()(points=5); print(d)'")}


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

""")



