# RNODataViewer

## Aim of the monitoring branch
The monitoring branch is intended to provide a broad overview of the DAQ history of the detector for a selected period, and give the possibility to look deeper into a bunch runs for an individual station, or individual events of a specific data file. To this end it feaures three tabs:
* Monitoring Overview
* Run Browser
* Event Browser

## Setup guide
### Setting up NuRadioMC
NuRadioMC is needed, the I/O modules for reading in RNO-G .root files are currently still only in the ```rnog_eventbrowser``` branch, you can find install instructions https://github.com/nu-radio/NuRadioMC/wiki in the **manual_installation** section. This should agree with doing the following:

- if did not install NuRadioMC before
```
pip install numpy scipy matplotlib tinydb>=4.1.1 tinydb-serialization aenum astropy radiotools>=0.2.0 h5py pyyaml peakutils requests pymongo dash plotly sphinx
pip install cython
pip install uproot, awkward
```
- To install the rnog_eventbrowser branch of NuRadioMC to $HOME/software/NuRadioMC
```
cd $HOME/software #or any other install directory
git clone https://github.com/nu-radio/NuRadioMC.git
cd NuRadioMC
# get the rnog_eventbrowser branch
git checkout rnog_eventbrowser

# and add NuRadioMC to your PYTHONPATH
export PYTHONPATH=$HOME/software/NuRadioMC:$PYTHONPATH
```
### Setting up The RNODataViewer
```
cd $HOME/software #or any other install directory
git clone git@github.com:RNO-G/RNODataViewer.git
cd RNODataViewer
git checkout feature/monitoring
# and add the RNODataViewer to your PYTHONPATH
export PYTHONPATH=$HOME/software/RNODataViewer:$PYTHONPATH
```
## Usage
Execute the ```monitoring.py  --port 8050 --open-window``` (with a port of your choice). It requires the `RNO_DATA_DIR` variable to be set to the top level of the data containing files as `stationXX/runXXX/combined.root` (As in the data directories in WISC/DESY). You can choose if you want to copy the dataset to a local directory or just mount the remote one ad WISC/DESY). You will also need to add the NuRadioMC and RNODataViewer to your `PYTHONPATH` (see above).

Alternatively, after adapting the paths therein to your local install and data directories, you can also run:
```
bash run_monitor.sh
```
a web browser window should open automatically.

## Open points
- General
  - exchange the runtable generation from downloading a .csv (which is currently updated at desy via cron job) by a run database.
  - switch from "new page" tabs to child tabs, such that data does not be reentered each time after switching tabs
  - ensure runtable is updated (this is relevant for running web monitor on rnog_monitor.zeuthen.desy.de @ Desy) 
- Overview page
  - produce useful plots for the overview page from the table (these plots will update fast compared to the current trigger rate plots)
  - allow on the overview page to inspect also header files instead of the combined files (the latter include waveform datal
  - other suggestions?
- Run viewer
  - 2d plot to inspect trace spectra
  - 1D traces/spectra median/quantile projections
  - other suggestions?  
- Event viewer
  - remove path field (which does not speak to any callbacks anyway)
  - channel labelling
  - other suggestions?   
