#export rnog_eventbrowser branch of NuRadioMC 
export PYTHONPATH=/Users/shallmann/software/rnog_eventbrowser:$PYTHONPATH
#export feature/monitoring branch of RNODataViewer
export PYTHONPATH=/Users/shallmann/software/RNODataViewer:$PYTHONPATH

# the monitoring takes $RNO_DATA_DIR environmental variable as top-level dir
# of the data. i.e. the directory $RNO_DATA_DIR is supposed to hold subdirs
# station11{/run???/combined.root}, station21, station22, ...
export RNO_DATA_DIR="/Users/shallmann/Desktop/rnog_field_data"

python3 monitoring.py --port 8050 --open-window
