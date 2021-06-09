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


```
$ python3 nanocli.py --details
start:  0.01 MHz
stop:   10 MHz
points: 1001
cals:   <none>
```


Perform the SOLT calibrations.

```
$ python3 nanocli.py --open
$ python3 nanocli.py --short
$ python3 nanocli.py --load
$ python3 nanocli.py --thru
$ python3 nanocli.py --details
```

Now run a sweep.  


```
$ python3 nanocli.py --points 5
# MHz S MA R 50
0.01             0.058815   -88.097        0.31499     2.523        0.31499     2.523       0.058815   -88.097
2.5075         0.00095648   105.554         1.2901    -6.751         1.2901    -6.751     0.00095648   105.554
5.005          0.00058297   -75.663        0.84085   -14.255        0.84085   -14.255     0.00058297   -75.663
7.5025          0.0021585   -62.841        0.78664   -13.163        0.78664   -13.163      0.0021585   -62.841
10              0.0036897   -69.325        0.76634   -13.698        0.76634   -13.698      0.0036897   -69.325
```


Return the results in dB.


```
$ python3 nanocli.py --db --points 5
# MHz S DB R 50
0.01           -24.538   -87.865     -10.053     2.518     -10.053     2.518     -24.538   -87.865
2.5075         -58.316   113.212       2.224    -6.743       2.224    -6.743     -58.316   113.212
5.005          -63.492   -72.534      -1.508   -14.245      -1.508   -14.245     -63.492   -72.534
7.5025         -53.164   -67.241      -2.088   -13.163      -2.088   -13.163     -53.164   -67.241
10             -48.809   -67.789      -2.310   -13.690      -2.310   -13.690     -48.809   -67.789
```


Output measurements in a format that can be read by numpy.


```
$ python3 nanocli.py --text --points 5
10000            0.0021622-0.058964j       0.313874+0.0140132j
2507500     -0.000479817+0.00114465j         1.28487-0.151421j
5005000     0.000102161-0.000539365j        0.815177-0.207144j
7502500      0.000863846-0.00198034j        0.765796-0.179227j
10000000      0.00128952-0.00351373j        0.744764-0.181457j
```


Write a s1p file to stdout.


```
$ python3 nanocli.py -1 --db --points 5
# MHz S DB R 50
0.01           -24.549   -87.876
2.5075         -59.515   108.592
5.005          -65.337   -74.803
7.5025         -53.330   -64.297
10             -48.587   -69.380
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


