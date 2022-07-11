import NuRadioReco.modules.io.NuRadioRecoio
import NuRadioReco.utilities.metaclasses
import six


@six.add_metaclass(NuRadioReco.utilities.metaclasses.Singleton)
class RNODataProvider():
    def __init__(self, channels=None):
        self.__filenames = None
        self.__event_io = None
        self.__channels = channels

    def set_filenames(self, filenames):
        if len(filenames)>0:
            self.__filenames = filenames
            self.__event_io = NuRadioReco.modules.io.NuRadioRecoio.NuRadioRecoio(filenames)

    def get_event_iterator(self):
        return self.__event_io.get_events

    def get_file_names(self):
        return self.__filenames

    def get_first_event(self, station_id):
        for event in self.__event_io.get_events():
            if station_id in event.get_station_ids():
                return event
        return None

    def get_n_events(self):
        return self.__event_io.get_n_events()
