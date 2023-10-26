import NuRadioReco.utilities.metaclasses
import six
# from NuRadioReco.modules.io.RNO_G.readRNOGDataMattak import readRNOGData
from NuRadioReco.eventbrowser import dataprovider
import uproot
import numpy as np
import os
import time
import logging


logger = logging.getLogger('RNODataViewer')
trigger_names = ["RADIANT0", "RADIANT1", "RADIANTX", "LT", "FORCE", "PPS", "UNKNOWN"]

# @six.add_metaclass(NuRadioReco.utilities.metaclasses.Singleton)
class RNODataProviderRoot(dataprovider.DataProvider):
    def __init__(self, channels=None, ):
        super().__init__(use_root=True)
        self.__filenames = None

    def set_filenames(self, filenames):
        if isinstance(filenames, str):
            filenames = [filenames]
        if len(filenames) > 0:
            if filenames is not self.__filenames:
                logger.info(f'Opening new file(s): {filenames}')
                self.__filenames = filenames
                self.get_file_handler('runviewer', filenames)

    def get_event_iterator(self):
        return self.get_file_handler('runviewer', self.__filenames).run

    def get_file_names(self):
        return self.__filenames

    def get_event_ids(self, station_id):
        filehandler = self.get_file_handler('runviewer', self.__filenames)
        einfo = filehandler.get_events_information(['station', 'eventNumber', 'run', 'triggerTime', 'triggerType'])
        return [i['eventNumber'] for i in einfo.values() if i['station'] == station_id]

    def get_run_numbers(self, station_id):
        filehandler = self.get_file_handler('runviewer', self.__filenames)
        einfo = filehandler.get_events_information(['station', 'eventNumber', 'run', 'triggerTime', 'triggerType'])
        return [i['run'] for i in einfo.values() if i['station'] == station_id]

    def get_trigger_types(self, station_id):
        filehandler = self.get_file_handler('runviewer', self.__filenames)
        einfo = filehandler.get_events_information(['station', 'eventNumber', 'run', 'triggerTime', 'triggerType'])
        return [i['triggerType'] for i in einfo.values() if i['station'] == station_id]

    def get_event_times(self, station_id):
        filehandler = self.get_file_handler('runviewer', self.__filenames)
        einfo = filehandler.get_events_information(['station', 'eventNumber', 'run', 'triggerTime', 'triggerType'])
        return [i['triggerTime'] for i in einfo.values() if i['station'] == station_id] #einfo['triggerTime'][einfo['station'] == station_id]

    def get_first_event(self, station_id=None):
        filehandler = self.get_file_handler('runviewer', self.__filenames)
        for event in filehandler.run():
            if station_id in event.get_station_ids() or station_id==None:
                return event
        return None

    def get_n_events(self):
        filehandler = self.get_file_handler('runviewer', self.__filenames)
        return filehandler.get_n_events()

    def get_event(self, id):
        filehandler = self.get_file_handler('runviewer', self.__filenames)
        return filehandler.get_event(id[0], id[1])

    def get_event_i(self, i):
        filehandler = self.get_file_handler('runviewer', self.__filenames)
        return filehandler.get_event_by_index(i)

data_provider = RNODataProviderRoot() # not sure that this is used
data_provider_run = RNODataProviderRoot()
data_provider_event = dataprovider.DataProvider(use_root=True, create_new=True)
