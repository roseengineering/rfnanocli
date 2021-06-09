
import subprocess 


def run(command, language=""):
    proc = subprocess.Popen("PYTHONPATH=. " + command, shell=True, stdout=subprocess.PIPE)
    buf = proc.stdout.read().decode()
    proc.wait()
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
sweeps off the original NanoVNA or the new NanoVNAv2
from the command line.
The sweep results are printed to the terminal
in touchstone format.

In addition the utility provides its own error correction.
It does not use the onboard calibrations features
of either nano.
You must calibrate your nano separately using this utility.
The calibration data is stored in a npz file on your computer.

In order to perform a measure sweep on the original nano, the
utility first turns calibration off on the device.  Once the
measurement is made, the utility will turn calibration back on.
It is recommended to use the same frequency sweep
with the original nano UI as well as with nanocli to
avoid UI interpolation issues.
For the v2 nano, since its USB connection is always uncorrected
its UI is unaffected.

## Calibration

The utility uses the 12-term error model to correct
sweep measurements.  This is the same SOLT
calibration method that you use to calibrate the nano from its UI.

To calibrate the nano using the utility, first initialize the
calibration with your frequency sweep.  This
sweep will be written to your calibration file.  If the calibration
file already exists, it will be overwritten.  By default
the name of the file is cal.npz.

The frequency sweep for a given calibration file is always fixed.  All
subsequent calibrations will use the same sweep set in the calibration
file.

## How to Install

First pip install the required python libraries using:

{run("pip install -r requirements.txt")}

Then run the utility using python3.

## Command Line Usage

The utility's command line usage is as follows:

{run("python3 nanocli.py --help")}

## Utility Calibration

First initialize the calibration file, setting the 
frequency sweep.

{run("python3 nanocli.py --init --start 10e3 --stop 10e6 --points 1001")}
{run("python3 nanocli.py --details")}

Next perform SOLT calibration.

```
$ python3 nanocli.py --open
$ python3 nanocli.py --short
$ python3 nanocli.py --load
$ python3 nanocli.py --thru
$ python3 nanocli.py --details
```

Now run a sweep.  

{run("python3 nanocli.py --points 5")}
{run("python3 nanocli.py --db --points 5")}
{run("python3 nanocli.py --text --points 5")}
{run("python3 nanocli.py -1 --db --points 5")}

Passing the --points option above
forces an interpolation of the calibration data
to the new frequency sweep.  If the option was not given
the 1001 frequencies used for calibration would be swept.

## Interpolation of Calibration Data

By default, no interpolation is performed
on your calibration data.  The range for the
frequency sweep is taken from the calibration
file.  

However if a different frequency range is
set on the command line from the calibration
data, then the calibration data will be interpolated
to the new range.

Remember the frequency range cannot be changed
when doing calibration.  All calibration data
in a single calibration file must be for the same range.

## Measurement Report Formats

All measurement output from the utility is
written to the terminal.
By default the output will be formatted
for a s2p touchstone file.  If the --one option
is passed on the command line the output will instead be
written in s1p format.

Passing the --text option writes the output
in a format compatible with numpy's loadtxt(arr, dtype='c16')
function.

""")



