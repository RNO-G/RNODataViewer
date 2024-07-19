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
from io import StringIO

logger = logging.getLogger('RNODataViewer')

@six.add_metaclass(NuRadioReco.utilities.metaclasses.Singleton)
class RunStats:
    __lock = threading.Lock()
    run_table = None
    last_modification_date = None
    last_full_update = None

    def __init__(self, top_level_dir):
        with self.__lock:
            self.__data_dir = top_level_dir
            self.run_table_class = RunTable()

    def update_run_table(self, delta_t=None):
        """
        update run table

        Parameters
        ----------
        delta_t: float | None
            Number of days (before current time) to update. If None, reload entire
            run table.
        """
        with self.__lock:

            current_time = astropy.time.Time.now()
            if self.run_table is None or delta_t is None: # full update
                logger.debug(f"Reloading run table ({['run_table', 'delta_t'][delta_t is None]} is None)")
                run_table = self.run_table_class.get_table()
                run_table.drop('_id', axis=1, inplace=True)
                run_table = self.add_paths_to_run_table(run_table, self.__data_dir)
                self.run_table = self.filter_available_runs(run_table)
                self.last_full_update = current_time
            else:
                logger.debug(f"Updating run table (checking last {delta_t:.1f} days...)")
                update_table = self.run_table_class.get_table(
                    start_time=current_time-astropy.time.TimeDelta(delta_t, format='jd')
                )
                if len(update_table):
                    update_table.drop('_id', axis=1, inplace=True)
                    update_table = self.add_paths_to_run_table(update_table, self.__data_dir)
                    update_table = self.filter_available_runs(update_table)
                    self.run_table = pd.concat([self.run_table, update_table], ignore_index=True).drop_duplicates(['station', 'run'], keep='last')

            self.last_modification_date = current_time

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

    def export_table(self):
        if self.run_table is None:
            self.update_run_table(None)
        return self.run_table.to_json(date_format='iso')

    def import_table(self, json_table):
        # when loading from json, we need to reconvert the timestamps back into timestamps
        run_table = pd.read_json(
            StringIO(json_table), convert_dates=['time_start', 'time_end'])
        self.run_table = run_table


    def get_table(self):
        if self.run_table is None: # we force an update only if the table is currently empty
            self.update_run_table(delta_t=None)
        return self.run_table

try:
    DATA_DIR = os.environ["RNO_DATA_DIR"]
    logger.info(f"DATA DIRECTORY: {DATA_DIR}")
except KeyError:
    logger.error("RNO_DATA_DIR not set, exiting...")
    sys.exit("Set environment variable RNO_DATA_DIR to top level path holding directories station11,station21,station22, etc.")

run_table = RunStats(DATA_DIR)

def get_station_entries():
    table = run_table.get_table()
    if table is None:
        return []

    station_entries = [
        {'label':f"Station {station_id}", 'value':station_id}
        for station_id in run_table.get_table().station.unique()
        if station_id > 0 and station_id < 999
    ]
    return station_entries
