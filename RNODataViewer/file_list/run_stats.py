import numpy as np
import os,sys
import astropy.time
import pandas as pd
from pathlib import Path

import NuRadioReco.utilities.metaclasses
import requests
import datetime
import six
from dateutil.parser import parse as parsedate


@six.add_metaclass(NuRadioReco.utilities.metaclasses.Singleton)
class RunStats:
    summary_csv = "https://www.zeuthen.desy.de/~shallman/rnog_run_summary.csv"
    def __init__(self, top_level_dir):
        self.__data_dir = top_level_dir
        self.__last_modification_date = datetime.datetime.min
        self.update_run_table()

    def update_run_table(self):
        # check the date on the webpage and see if it is newer than what was loaded
        r = requests.head(self.summary_csv)
        url_date = parsedate(r.headers['last-modified'])
        if url_date > self.__last_modification_date:
            self.run_summary_from_csv(self.summary_csv, self.__data_dir)
            print("updating runtable. Expected files:", len(self.run_table))
            if os.path.ismount(top_level_dir):
                print("input directory is mounted. Skipping check if all files exist")
            else:
                self.filter_available_runs()
            print("available files:", len(self.run_table))

            self.__last_modification_date = url_date

    def run_summary_from_csv(self, csv, top_level_dir="."):
        self.run_table = pd.read_csv(csv)
        self.run_table["mjd_first_event"] = np.array(astropy.time.Time(np.array(self.run_table["time first event"]).astype("str"), format='iso').mjd)
        self.run_table["mjd_last_event"] = np.array(astropy.time.Time(np.array(self.run_table["time last event"]).astype("str"), format='iso').mjd)
        filenames_root = ["/".join([top_level_dir, path]) for path in self.run_table.path]
        print("will look for files like", filenames_root[0])
        self.run_table["filenames_root"] = filenames_root

    def filter_available_runs(self):
        files_found = []
        for path_to_file in self.run_table.filenames_root:
            path = Path(path_to_file)
            if path.is_file():
                files_found.append(True)
                #print(f'The file {path_to_file} exists')
            else:
                files_found.append(False)
                print(f'The file {path_to_file} does not exist')
        is_there = np.array(files_found, dtype=bool)
        #is_there  = np.array([os.path.isfile(f) for f in self.run_table.filenames_root], dtype=bool)
        self.run_table = self.run_table[is_there]

    def get_table(self):
        self.update_run_table()
        return self.run_table

try:
    DATA_DIR = os.environ["RNO_DATA_DIR"]
    print("DATA DIRECTORY:", DATA_DIR)
except KeyError:
    sys.exit("Set environment variable RNO_DATA_DIR to top level path holding directories station11,station21,station22, etc.")

run_table = RunStats(DATA_DIR)

station_entries = [
    {'label':f"Station {station_id}", 'value':station_id}
    for station_id in run_table.station.unique()
    if station_id > 0 and station_id < 999
]
