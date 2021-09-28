import numpy as np
import os,sys
import astropy.time
import pandas as pd

class RunStats:
    summary_csv = "https://www.zeuthen.desy.de/~shallman/rnog_run_summary.csv"
    def __init__(self, top_level_dir):
        self.run_summary_from_csv(self.summary_csv, top_level_dir)
        print("found files:", len(self.run_table))
        if os.path.ismount(top_level_dir):
            print("input directory is mounted. Skipping check if all files exist")
        else:
            self.filter_available_runs()
        print("available files:", len(self.run_table))
    def run_summary_from_csv(self, csv, top_level_dir="."):
        self.run_table = pd.read_csv(csv)
        self.run_table["mjd_first_event"] = np.array(astropy.time.Time(np.array(self.run_table["time first event"]).astype("str"), format='iso').mjd)
        self.run_table["mjd_last_event"] = np.array(astropy.time.Time(np.array(self.run_table["time last event"]).astype("str"), format='iso').mjd)
        filenames_root = ["/".join([top_level_dir, path]) for path in self.run_table.path]
        self.run_table["filenames_root"] = filenames_root
    def filter_available_runs(self):
        is_there  = np.array([os.path.isfile(f) for f in self.run_table.filenames_root], dtype=bool)
        self.run_table = self.run_table[is_there]
    def get_table(self):
        return self.run_table

try:
    DATA_DIR = os.environ["RNO_DATA_DIR"]
    print("DATA DIRECTORY:", DATA_DIR)
except KeyError:
    sys.exit("Set environment variable RNO_DATA_DIR to top level path holding directories station11,station21,station22, etc.")

rs = RunStats(DATA_DIR)
RUN_TABLE = rs.get_table()
run_table = RUN_TABLE
