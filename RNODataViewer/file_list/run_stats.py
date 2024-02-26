import numpy as np
import os,sys
import astropy.time
import pandas as pd
from pathlib import Path
import logging
import NuRadioReco.utilities.metaclasses
import six
from rnog_data.runtable import RunTable
import threading

logger = logging.getLogger('RNODataViewer')

@six.add_metaclass(NuRadioReco.utilities.metaclasses.Singleton)
class RunStats:
    __lock = threading.Lock()
    def __init__(self, top_level_dir):
        with self.__lock:
            self.__data_dir = top_level_dir
            self.run_table_class =  RunTable()
            run_table = self.run_table_class.get_table()
            run_table = self.add_paths_to_run_table(run_table, top_level_dir)
            self.run_table = self.filter_available_runs(run_table)
            self.last_modification_date = astropy.time.Time.now()
            self.last_full_update = astropy.time.Time.now()

    def update_run_table(self):
        with self.__lock:
            # check the date on the webpage and see if it is newer than what was loaded
            current_time = astropy.time.Time.now()
            if (current_time - self.last_modification_date).sec < 60:
                return None # no need to update more than once a minute
            elif (current_time - self.last_full_update).sec > 86400: # once per day, reload the complete table (slow)
                logger.debug("Reloading run table")
                run_table = self.run_table_class.get_table()
                run_table = self.add_paths_to_run_table(run_table, self.__data_dir)
                self.run_table = self.filter_available_runs(run_table)
                self.last_full_update = current_time
            else: # we only update the most recent 24 hours (quicker)
                logger.debug("Checking for updated run table...")
                update_table = self.run_table_class.get_table(
                    start_time=self.last_modification_date-astropy.time.TimeDelta(1, format='jd')
                )
                if len(update_table):
                    update_table = self.add_paths_to_run_table(update_table, self.__data_dir)
                    update_table = self.filter_available_runs(update_table)
                    self.run_table = pd.concat([self.run_table, update_table], ignore_index=True).drop_duplicates(['station', 'run'], keep='last')

            self.last_modification_date = astropy.time.Time.now()

    def add_paths_to_run_table(self, run_table, top_level_dir="."):
        run_table["mjd_first_event"] = np.array(astropy.time.Time(np.array(run_table["time_start"])).mjd)
        run_table["mjd_last_event"] = np.array(astropy.time.Time(np.array(run_table["time_end"])).mjd)
        filenames_root = ["/".join([top_level_dir, path]).replace("inbox/inbox", "inbox") for path in run_table.path]
        logger.info(f"will look for files like {filenames_root[0]}")
        run_table["filenames_root"] = filenames_root
        return run_table

    def filter_available_runs(self, run_table, force_check=False):
        if '/mnt' in self.__data_dir and not force_check:
            logger.info("input directory is mounted. Skipping check if all files exist")
            return run_table
        files_found = np.zeros(len(run_table.filenames_root), dtype=bool)
        for i, path_to_file in enumerate(run_table.filenames_root):
            path = Path(path_to_file)
            files_found[i] = path.exists()
        missing_files = ~files_found
        if np.any(missing_files):
            logger.debug(
                f"Missing {np.sum(missing_files)} files, displaying first 100...\n"
                + '\n'.join(run_table[missing_files].filenames_root.unique()[:100])
            )

        run_table = run_table[files_found]
        return run_table

    def get_table(self):
        self.update_run_table()
        return self.run_table

try:
    DATA_DIR = os.environ["RNO_DATA_DIR"]
    logger.info(f"DATA DIRECTORY: {DATA_DIR}")
except KeyError:
    logger.error("RNO_DATA_DIR not set, exiting...")
    sys.exit("Set environment variable RNO_DATA_DIR to top level path holding directories station11,station21,station22, etc.")

global run_table
run_table = RunStats(DATA_DIR)
# print(run_table.get_table())
station_entries = [
    {'label':f"Station {station_id}", 'value':station_id}
    for station_id in run_table.get_table().station.unique()
    if station_id > 0 and station_id < 999
]
