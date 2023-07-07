import NuRadioReco.utilities.metaclasses
import six
from NuRadioReco.modules.io.RNO_G.readRNOGDataMattak import readRNOGData
import uproot
import numpy as np
import os
import time
import logging


logger = logging.getLogger('RNODataViewer')
trigger_names = ["RADIANT0", "RADIANT1", "RADIANTX", "LT", "FORCE", "PPS", "UNKNOWN"]

@six.add_metaclass(NuRadioReco.utilities.metaclasses.Singleton)
class RNODataProviderRoot:
    def __init__(self, channels=None):
        self.__filenames = None
        self.__event_io = readRNOGData()
        self.__channels = channels
        self.uproot_iterator_data = None
        self.uproot_iterator_header = None

    def set_filenames(self, filenames):
        if isinstance(filenames, str):
            filenames = [filenames]
        if len(filenames) > 0:
            if filenames is not self.__filenames:
                logger.info(f'Opening new file(s): {filenames}')
                self.__filenames = filenames
                # self.__event_io = readRNOGData()
                # mattak for now can only read directories
                self.__event_io.begin([os.path.dirname(f) for f in filenames])
                #self.__event_io.run(channels=self.__channels)

    def set_iterators(self, cut=None):
        self.__event_io.begin(self.__filenames)
        self.__event_io._set_iterators(cut=cut)
        self.uproot_iterator_data = self.__event_io.uproot_iterator_data

    def get_event_iterator(self):
        return self.__event_io.run

    def get_file_names(self):
        return self.__filenames

    def get_first_event(self, station_id=None):
        for event in self.__event_io.get_events():
            if station_id in event.get_station_ids() or station_id==None:
                return event
        return None

    def get_n_events(self):
        return self.__event_io._n_events_total#get_n_events()
    
    def get_event(self, id):
        return self.__event_io.get_event(id[0], id[1])
    
    def get_event_i(self, i):
        return self.__event_io.get_event_by_index(i)

    def get_waveforms(self, station_id, channels): ### DEPRECATED
        # for evt in self.__event_io.run():
        #     evt.get_station(station_id)
        waveform_array = []
        for filename in self.__filenames:
            file = uproot.open(filename)
            if 'combined' in file:
                file = file['combined']
            waveforms = file['waveforms']['radiant_data[24][2048]'].array(library='np')
            station_ids = file['header']['station_number'].array(library='np')
            waveform_array.append(waveforms[(station_ids == station_id), :, :][:, channels])
        return np.concatenate(waveform_array)

    def get_event_times(self, station_id):
        einfo = self.__event_io.get_events_information(['station', 'triggerTime'])
        return [i['triggerTime'] for i in einfo.values() if i['station'] == station_id] #einfo['triggerTime'][einfo['station'] == station_id]
        station_ids = np.array([], dtype=int)
        readout_times = np.array([], dtype=float)
        for filename in self.__filenames:
            file = uproot.open(filename)
            if 'combined' in file:
                file = file['combined']
            station_ids = np.append(station_ids, file['header']['station_number'].array(library='np'))
            readout_times = np.append(readout_times, file['header']['readout_time'].array(library='np'))
        return readout_times[station_ids == station_id]

    def get_event_times_hdr(self, station_id): ### DEPRECATED
        station_ids = np.array([], dtype=int)
        readout_times = np.array([], dtype=float)
        for filename in self.__filenames:
            file = uproot.open(filename.replace("combined", "headers"))
            if 'hdr' in file:
                file = file['hdr']
            station_ids = np.append(station_ids, file['hdr']['station_number'].array(library='np'))
            readout_times = np.append(readout_times, file['hdr']['readout_time'].array(library='np'))
        return readout_times[station_ids == station_id]

    def get_event_ids(self, station_id):
        einfo = self.__event_io.get_events_information(['station', 'eventNumber'])
        return [i['eventNumber'] for i in einfo.values() if i['station'] == station_id]
        station_ids = np.array([], dtype=int)
        event_ids = np.array([], dtype=int)
        for filename in self.__filenames:
            file = uproot.open(filename)
            if 'combined' in file:
                file = file['combined']
            station_ids = np.append(station_ids, file['header']['station_number'].array(library='np'))
            event_ids = np.append(event_ids, file['waveforms']['event_number'].array(library='np'))
        return event_ids[station_ids == station_id]

    def get_run_numbers(self, station_id):
        einfo = self.__event_io.get_events_information(['station', 'run'])
        return [i['run'] for i in einfo.values() if i['station'] == station_id]
        station_ids = np.array([], dtype=int)
        run_numbers = np.array([], dtype=int)
        for filename in self.__filenames:
            file = uproot.open(filename)
            if 'combined' in file:
                file = file['combined']
            station_ids = np.append(station_ids, file['header']['station_number'].array(library='np'))
            run_numbers = np.append(run_numbers, file['waveforms']['run_number'].array(library='np'))
        return run_numbers[station_ids == station_id]
    
    def get_trigger_types(self, station_id):
        einfo = self.__event_io.get_events_information(['station', 'triggerType'])
        return [i['triggerType'] for i in einfo.values() if i['station'] == station_id]

### we create a separate datareader for each tab and each user
@six.add_metaclass(NuRadioReco.utilities.metaclasses.Singleton)
class DataProvider:

    def __init__(self):
        self.__user_instances = {}
    
    def get_file_handler(self, user_id, filenames, channels=None):
        if user_id not in self.__user_instances.keys(): # create new instance
            
            
            data_provider = RNODataProviderRoot(create_new=True)
            
            self.__user_instances[user_id] = dict(
                data_provider=data_provider, last_access=None
            )
        else:
            data_provider = self.__user_instances[user_id]['data_provider']
        data_provider.set_filenames(filenames)
        
        self.__user_instances[user_id]['last_access'] = time.time()
        return data_provider
    
data_provider = RNODataProviderRoot()
data_provider_run = RNODataProviderRoot(create_new=True)
data_provider_event = DataProvider() #RNODataProviderRoot(create_new=True)