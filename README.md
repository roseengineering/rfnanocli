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
calibration file with your frequency sweep.
If the calibration
file already exists, it will be overwritten.  By default
the name of the file is cal.npz.

The frequency sweep for a given calibration file is always fixed.  All
subsequent calibrations will use the same sweep set in the calibration
file.

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


The calibration file has no calibration data.
Next perform the SOLT calibrations.

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
0.01             0.059075   -88.107        0.31488     2.582        0.31488     2.582       0.059075   -88.107
2.5075          0.0010822   114.880         1.2871    -6.924         1.2871    -6.924      0.0010822   114.880
5.005          0.00064035   -86.056        0.84017   -14.186        0.84017   -14.186     0.00064035   -86.056
7.5025          0.0021083   -65.407         0.7863   -13.140         0.7863   -13.140      0.0021083   -65.407
10              0.0036591   -69.949        0.76639   -13.684        0.76639   -13.684      0.0036591   -69.949
```


Return the results in dB.


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01           -24.487   -87.805     -10.055     2.492     -10.055     2.492     -24.487   -87.805
2.5075         -59.926    94.702       2.204    -6.940       2.204    -6.940     -59.926    94.702
5.005          -64.434   -83.055      -1.513   -14.213      -1.513   -14.213     -64.434   -83.055
7.5025         -53.299   -64.752      -2.088   -13.155      -2.088   -13.155     -53.299   -64.752
10             -48.427   -70.208      -2.310   -13.688      -2.310   -13.688     -48.427   -70.208
```


Output measurements in a format that can be read by numpy.


```
$ python3 nanocli.py --text --points 5
10000          0.00202506-0.0586622j       0.314701+0.0138618j
2507500    -0.000292003+0.000749571j         1.28059-0.155384j
5005000     0.000159319-0.000605672j        0.814351-0.206161j
7502500      0.000897456-0.00197351j         0.765621-0.17866j
10000000      0.00128996-0.00341322j        0.744529-0.181269j
```


Write a s1p file to stdout.


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01           -24.615   -88.046
2.5075         -61.087    91.905
5.005          -63.493   -88.143
7.5025         -53.529   -64.783
10             -48.665   -71.569
```


Passing the --points option above
forces an interpolation of the calibration data
to the range of the new frequency sweep.  If this option was not given
the original 1001 frequencies used for calibration would be swept
without interpolation.

## Interpolation of Calibration Data

By default, no interpolation is performed
on your calibration data mean making a measurement.  
The frequencies for the sweep is taken directly from 
the calibration file.  

However if the range of the frequency sweep
is changed on the command line from that given 
in the calibration file,
the calibration data will be interpolated
to the new range.

Remember, the frequency range cannot be changed
when doing calibration.  But during a measurement it can.
All calibration data within a calibration file 
must have same frequency sweep range.

## Measurement Report Formats

All measurement output from the utility is
written to the terminal (using stdout).
By default the output will be formatted
for a s2p touchstone file.  If the --one option
is passed on the command line the output will be
formatted for a s1p touchstone file.

Passing the --text option writes the output
in a format compatible with numpy's loadtxt(arr, dtype='c16')
function.


