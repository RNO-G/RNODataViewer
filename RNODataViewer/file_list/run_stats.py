import numpy as np
import os, sys
import astropy.time
import pandas as pd
from pathlib import Path
import logging
import NuRadioReco.utilities.metaclasses
import six
from rnog_data.runtable import RunTable
import threading
from astropy.time import Time
import requests

logger = logging.getLogger('RNODataViewer')

@six.add_metaclass(NuRadioReco.utilities.metaclasses.Singleton)
class RunStats:
    __lock = threading.Lock()
    def __init__(self, top_level_dir, table_path="/tmp/RNODataViewer/data/runtable.hdf5"):
        with self.__lock:
            self.__data_dir = top_level_dir
            self.run_table_class = RunTable()
            self.run_table_path = table_path
            self.run_table = None
            self.last_modification_date = astropy.time.Time('1970-01-01')
            self.last_full_update = astropy.time.Time('1970-01-01')

    def update_run_table(self):
        with self.__lock:
            if self.run_table is None: # no run table yet
                if os.path.exists(self.run_table_path):
                    logger.debug(f"Loading cached run table at {self.run_table_path}")
                    self.run_table = pd.read_hdf(self.run_table_path)
                    self.last_modification_date = astropy.time.Time(os.path.getmtime(self.run_table_path), format='unix')
                    self.last_full_update = self.last_modification_date
                else:
                    logger.info(f"No run table in cache at {self.run_table_path}. Downloading complete run table...")
                    if not os.path.exists(os.path.dirname(self.run_table_path)):
                        os.makedirs(os.path.dirname(self.run_table_path))

                    # run_table = self.run_table_class.get_table()
                    # run_table = self.add_paths_to_run_table(run_table, self.__data_dir)
                    # self.run_table = self.filter_available_runs(run_table)
                    # self.last_modification_date = astropy.time.Time.now()
                    # self.last_full_update = astropy.time.Time.now()

            # check the date on the webpage and see if it is newer than what was loaded
            current_time = astropy.time.Time.now()
            if (current_time - self.last_modification_date).sec < 60:
                return None # no need to update more than once a minute
            elif (current_time - self.last_full_update).sec > 86400: # once per day, reload the complete table (slow)
                logger.debug("Reloading run table")
                run_table = self.run_table_class.get_table()
                run_table = self.add_paths_to_run_table(run_table, self.__data_dir)
                self.run_table = self.filter_available_runs(run_table)
                if self.run_table_path is not None:
                    self.run_table.to_hdf(self.run_table_path, key='df', mode='w')
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
        logger.debug(f"Checking for the existence of {len(files_found)} files...")
        for i, path_to_file in enumerate(run_table.filenames_root):
            path = Path(path_to_file)
            files_found[i] = path.exists()
        missing_files = ~files_found
        if np.any(missing_files):
            logger.debug(
                f"Missing {np.sum(missing_files)} files, displaying first 100...\n"
                + '\n'.join(run_table[missing_files].filenames_root.unique()[:100])
            )
        else:
            logger.debug("All files present.")
        run_table = run_table[files_found]
        return run_table

    def get_table(self):
        self.update_run_table()
        return self.run_table

    def get_station_entries(self):
        station_entries = [
            {'label':f"Station {station_id}", 'value':station_id}
            for station_id in self.get_table().station.unique()
            if station_id > 0 and station_id < 999
        ]
        return station_entries

@six.add_metaclass(NuRadioReco.utilities.metaclasses.Singleton)
class trigger_rates:
    __lock = threading.Lock()
    def __init__(self, table_path='/tmp/RNODataViewer/data/trigger_rates'):
        with self.__lock:
            self.table_dir_local = table_path
            if not os.path.exists(table_path):
                os.makedirs(table_path)
            self.hash_table_path_local = os.path.join(table_path, 'trigger_rate_hash_table.hdf5')
            self.hash_table_path_url = 'https://www.zeuthen.desy.de/~shallman/trigger_rates/trigger_rate_hash_table.hdf5'
            self.last_update = Time('1970-01-01')
            if os.path.exists(self.hash_table_path_local):
                self.hash_table = pd.read_hdf(self.hash_table_path_local)
            else:
                self.hash_table = None

    def get_updated_trigger_table(self, start_time, end_time):
        """
        Returns a DataFrame with the trigger rates
        """
        with self.__lock:
            now = Time.now()
            if (now - self.last_update).sec > 300: # update trigger rate tables
                logger.warning("Updating trigger rate tables...")
                try:
                    df_bytes = requests.get(self.hash_table_path_url)
                    df_bytes.raise_for_status()
                    with open(self.hash_table_path_local+'.upd', 'wb') as f:
                        f.write(df_bytes.content)
                except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                    logger.error(msg="Failed to update trigger rate tables, will try to use local versions instead...", exc_info=e)

                hash_table = pd.read_hdf(self.hash_table_path_local+'.upd')
                if self.hash_table is None:
                    update_tables = hash_table.index.levels[0] # update all tables
                    logger.info(f'No previous hash found, updating all {len(update_tables)} trigger tables')
                else:
                    update_tables = []
                    for i in hash_table.index.levels[0]:
                        if i in self.hash_table.index.levels[0]:
                            n_events_new = hash_table.loc[i, 'n_events']
                            n_events_old = self.hash_table.loc[i, 'n_events']
                            if len(n_events_new) == len(n_events_old):
                                if np.all(n_events_new == n_events_old):
                                    continue # table is up to date
                        update_tables.append(i)

                if len(update_tables):
                    # times = Time([f'{month}-01' for month in update_tables])
                    # mask = (times >= start_time) & (times <= end_time)
                    # update_tables = np.array(update_tables)[mask]

                    for table in update_tables:
                        logger.warning(f"Downloading updated trigger rate table {table}")
                        try:
                            df_bytes = requests.get(f"https://www.zeuthen.desy.de/~shallman/trigger_rates/trigger_rates_{table}.hdf5")
                            df_bytes.raise_for_status()
                            with open(os.path.join(self.table_dir_local, f"trigger_rates_{table}.hdf5"), 'wb') as f:
                                f.write(df_bytes.content)
                            # we update the hash table only AFTER the new table has been downloaded
                            # this prevents issues if the update is interrupted by the user
                            if self.hash_table is not None:
                                if table in self.hash_table.index:
                                    self.hash_table.drop(table, inplace=True)
                            self.hash_table = pd.concat([self.hash_table, hash_table.loc[[table]]]).sort_index()
                            self.hash_table.to_hdf(self.hash_table_path_local, key='df', mode='w')
                        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                            logger.error(msg=f"Unable to update trigger table {table}", exc_info=e)

                self.last_update = now

        tables = self.hash_table.index.levels[0]
        times = Time([f'{month}-01' for month in tables])
        start_month = Time(f'{Time(start_time).iso[:7]}-01') # stupid way of converting to 1st day of month
        mask = (times >= start_month) & (times <= end_time)
        tables = tables[mask]
        trigger_rate_tables = [
            pd.read_hdf(os.path.join(self.table_dir_local, f"trigger_rates_{table}.hdf5"))
            for table in tables]
        if not len(trigger_rate_tables):
            logger.warning('No trigger rate tables for selected period!')
            return None

        trigger_table = pd.concat(trigger_rate_tables)

        return trigger_table

try:
    DATA_DIR = os.environ["RNO_DATA_DIR"]
    logger.info(f"DATA DIRECTORY: {DATA_DIR}")
except KeyError:
    logger.error("RNO_DATA_DIR not set, exiting...")
    sys.exit("Set environment variable RNO_DATA_DIR to top level path holding directories station11,station21,station22, etc.")

global RUN_TABLE
RUN_TABLE = RunStats(DATA_DIR)
global TRIGGER_RATE_TABLE
TRIGGER_RATE_TABLE = trigger_rates()

# print(run_table.get_table())
