from RNODataViewer.base.data_provider_root import data_provider, trigger_names #trigger names are hardcoded for now
import RNODataViewer.base.data_provider_nur
import numpy as np
import astropy.time
from NuRadioReco.utilities import units
import NuRadioReco.framework.base_trace
import NuRadioReco.utilities.fft
import time
import logging
logging.basicConfig()
logger = logging.getLogger("RNODataViewer")

### unused?
def get_spectrogram_data_py(station_id, channel_ids, filenames=None):
    data_provider = RNODataViewer.base.data_provider_nur.RNODataProvider(channels=channel_ids)
    first_event = data_provider.get_first_event(station_id)
    if first_event is None:
        return False, None, None, None
    channel = first_event.get_station(station_id).get_channel(channel_ids[0])
    spectra = np.empty((len(channel_ids), data_provider.get_n_events(), channel.get_number_of_samples() // 2 + 1))
    times = []
    labels = []
    triggers = None
    gps_times = np.zeros(data_provider.get_n_events())
    d_f = channel.get_frequencies()[2] - channel.get_frequencies()[1]
    for i_event, event in enumerate(data_provider.get_event_iterator()()):
        if station_id in event.get_station_ids():
            station = event.get_station(station_id)
            if triggers is None:
                triggers = list(station.get_triggers().keys())
                triggers = {trigger_key: [] for trigger_key in triggers}

            times.append(station.get_station_time().fits)
            for trigger in triggers.keys():
                triggers[trigger].append(station.get_trigger(trigger).has_triggered())
            gps_times[i_event] = station.get_station_time().gps
            for i_channel, channel_id in enumerate(channel_ids):
                spectra[i_channel, i_event] = np.abs(station.get_channel(channel_id).get_frequency_spectrum())
            labels.append("Event {}".format(event))
    sort_args = np.argsort(gps_times)
    times = np.array(times)
    return True, times[sort_args[::-1]], spectra[:, sort_args[::-1]], d_f, labels, triggers

# @lru_cache(maxsize=1)
def get_spectrogram_data_root(station_id, channel_ids, filenames=None):
    logger.debug("getting spectrogram data...")
    t0 = time.time()
    if not filenames is None:
        data_provider.set_filenames(filenames)

    spectra = {i:[] for i in channel_ids}
    gps_times = []
    labels = []
    iterator = data_provider.get_event_iterator()

    for event in iterator():
        station = event.get_station(station_id)
        for channel_id in channel_ids:
            channel = station.get_channel(channel_id)
            spectra[channel_id].append(channel.get_frequency_spectrum())

    spectra = {i:np.array(j) for i,j in spectra.items()} # convert to numpy arrays for convenience
    d_f = channel.get_frequencies()[1] - channel.get_frequencies()[0]
    event_ids = data_provider.get_event_ids(station_id)
    run_numbers = data_provider.get_run_numbers(station_id)
    gps_times = data_provider.get_event_times(station_id)
    trigger_types = data_provider.get_trigger_types(station_id)
    times = astropy.time.Time(gps_times, format='unix', scale='utc').fits
    labels = np.array(['Run {}, Event {}, Trigger {}'.format(run_numbers[i], event_ids[i], trigger_types[i]) for i in range(len(event_ids))])
    logger.debug(f'... obtained spectra for {len(labels)} events in {time.time()-t0:.0f} s. Making plot...')
    return True, times, spectra, d_f, labels, None

def get_spectrogram_average_root(station_id, channel_ids, filenames=None, suppress_zero_mode=False):
    logger.debug("getting spectrogram data...")
    t0 = time.time()
    if not filenames is None:
        data_provider.set_filenames(filenames)

    spectra = np.zeros((len(channel_ids), 1025))
    spectra_forced = np.zeros_like(spectra)
    trigger_types = data_provider.get_trigger_types(station_id)
    iterator = data_provider.get_event_iterator()
    n_total = 0
    n_forced = 0

    for i, event in enumerate(iterator()):
        trigger_type = trigger_types[i]
        station = event.get_station(station_id)
        n_total += 1
        n_forced += (trigger_type == 'FORCE')
        for j, channel_id in enumerate(channel_ids):
            channel = station.get_channel(channel_id)
            spectra[j] += np.abs(channel.get_frequency_spectrum())
            if trigger_type == 'FORCE':
                spectra_forced[j] += np.abs(channel.get_frequency_spectrum())

    frequencies = channel.get_frequencies()
    logger.debug('n_events {} forced trigger {}'.format(n_total, n_forced))

    return frequencies, spectra / np.max([n_total,1]), spectra_forced / np.max([n_forced, 1])