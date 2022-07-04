import NuRadioReco.utilities.metaclasses
import six
from NuRadioReco.modules.io.rno_g.readRNOGData import readRNOGData
import uproot
import numpy as np


@six.add_metaclass(NuRadioReco.utilities.metaclasses.Singleton)
class RNODataProviderRoot:
    def __init__(self, channels=None):
        self.__filenames = None
        self.__event_io = None
        self.__channels = channels
        self.uproot_iterator_data = None
        self.uproot_iterator_header = None

    def set_filenames(self, filenames):
        if len(filenames) > 0:
            self.__filenames = filenames
            #self.__event_io = readRNOGData()
            #self.__event_io.begin(filenames)
            #self.__event_io.run(channels=self.__channels)

    def set_iterators(self, cut=None):
        self.__event_io = readRNOGData()
        self.__event_io.begin(self.__filenames)
        self.__event_io._set_iterators(cut=cut)
        self.uproot_iterator_data = self.__event_io.uproot_iterator_data

    def get_event_iterator(self):
        return self.__event_io.get_events

    def get_file_names(self):
        return self.__filenames

    def get_first_event(self, station_id=None):
        for event in self.__event_io.get_events():
            if station_id in event.get_station_ids() or station_id==None:
                return event
        return None

    def get_n_events(self):
        return self.__event_io.get_n_events()

    def get_waveforms(self, station_id, channels):
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
        station_ids = np.array([], dtype=int)
        readout_times = np.array([], dtype=float)
        for filename in self.__filenames:
            file = uproot.open(filename)
            if 'combined' in file:
                file = file['combined']
            station_ids = np.append(station_ids, file['header']['station_number'].array(library='np'))
            readout_times = np.append(readout_times, file['header']['readout_time'].array(library='np'))
        return readout_times[station_ids == station_id]

    def get_event_times_hdr(self, station_id):
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
        station_ids = np.array([], dtype=int)
        run_numbers = np.array([], dtype=int)
        for filename in self.__filenames:
            file = uproot.open(filename)
            if 'combined' in file:
                file = file['combined']
            station_ids = np.append(station_ids, file['header']['station_number'].array(library='np'))
            run_numbers = np.append(run_numbers, file['waveforms']['run_number'].array(library='np'))
        return run_numbers[station_ids == station_id]

