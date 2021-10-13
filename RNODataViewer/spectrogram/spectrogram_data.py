import RNODataViewer.base.data_provider_root
import RNODataViewer.base.data_provider_nur
import numpy as np
import astropy.time
from NuRadioReco.utilities import units
import NuRadioReco.framework.base_trace
import NuRadioReco.utilities.fft


def get_spectrogram_data_py(station_id, channel_ids):
    data_provider = RNODataViewer.base.data_provider_nur.RNODataProvider(channels=channel_ids)
    first_event = data_provider.get_first_event(station_id)
    if first_event is None:
        return False, None, None, None
    channel = first_event.get_station(station_id).get_channel(channel_ids[0])
    spectra = np.empty((len(channel_ids), data_provider.get_n_events(), channel.get_number_of_samples() // 2 + 1))
    times = []
    labels = []
    gps_times = np.zeros(data_provider.get_n_events())
    d_f = channel.get_frequencies()[2] - channel.get_frequencies()[1]
    for i_event, event in enumerate(data_provider.get_event_iterator()()):
        if station_id in event.get_station_ids():
            station = event.get_station(station_id)
            times.append(station.get_station_time().fits)
            gps_times[i_event] = station.get_station_time().gps
            for i_channel, channel_id in enumerate(channel_ids):
                spectra[i_channel, i_event] = np.abs(station.get_channel(channel_id).get_frequency_spectrum())
            labels.append("Event {}".format(event))
    sort_args = np.argsort(gps_times)
    times = np.array(times)
    return True, times[sort_args[::-1]], spectra[:, sort_args[::-1]], d_f, labels


def get_spectrogram_data_root(station_id, channel_ids, filenames=None):
    print("getting spectrogram data")
    data_provider = RNODataViewer.base.data_provider_root.RNODataProviderRoot(channels=channel_ids)
    if not filenames is None:
        data_provider.set_filenames(filenames)
    #first_event = data_provider.get_first_event(station_id)
    #if first_event is None:
    #    return False, None, None, None
    #channel = first_event.get_station(station_id).get_channel(channel_ids[0])
    spectra = {}  # np.empty((len(channel_ids), data_provider.get_n_events(), channel.get_number_of_samples() // 2 + 1))
    gps_times = []
    #TODO this is for testing why it is so slow
    channel = NuRadioReco.framework.base_trace.BaseTrace()
    channel.set_trace(np.zeros(2048), sampling_rate=3.2 * units.GHz)
    d_f = channel.get_frequencies()[2] - channel.get_frequencies()[1]

    data_provider.set_iterators()
    for headers, events in zip(data_provider.uproot_iterator_header, data_provider.uproot_iterator_data):
        mask_station = headers['station_number'] == station_id
        gps_times.append(headers['readout_time'][mask_station])
        for i_channel, channel_id in enumerate(channel_ids):
            if i_channel not in spectra:
                spectra[i_channel] = []
            traces = np.array(events['radiant_data[24][2048]'][:, channel_id, :])[mask_station]

            def convert(data):
                tr = NuRadioReco.framework.base_trace.BaseTrace()
                tr.set_trace(data * units.mV, sampling_rate=3.2 * units.GHz)
                spectrum =  np.abs(tr.get_frequency_spectrum())
                # set DC to zero
                spectrum[0] = 0
                return spectrum
            if len(traces)==0:
                continue
            spec = np.apply_along_axis(convert, 1, np.array(traces))
            spectra[i_channel].append(spec)

    gps_times = np.concatenate(gps_times)
    for it in spectra:
        spectra[it] = np.concatenate(spectra[it])
    subplot_titles = []
    for channel_id in channel_ids:
        subplot_titles.append('Channel {}'.format(channel_id))
    sort_args = np.argsort(gps_times)
    times = astropy.time.Time(gps_times, format="unix", scale="utc").fits

    event_ids = data_provider.get_event_ids(station_id)
    run_numbers = data_provider.get_run_numbers(station_id)
    labels = ['Run {}, Event {}'.format(run_numbers[i], event_ids[i]) for i in range(len(event_ids))]
    #return True, times, spectra, d_f
    return True, np.arange(0, len(times)), spectra, d_f, labels

def get_spectrogram_average_root(station_id, channel_ids, filenames=None, suppress_zero_mode=False):
    data_provider = RNODataViewer.base.data_provider_root.RNODataProviderRoot(channels=channel_ids)
    if not filenames is None:
        data_provider.set_filenames(filenames)
    data_provider.set_iterators()
    n_total, n_forced = 0, 0
    tr = NuRadioReco.framework.base_trace.BaseTrace()
    sampling_rate = 3.2 * units.GHz
    tr.set_trace(np.zeros(2048), sampling_rate=sampling_rate)
    frequencies = tr.get_frequencies()
    spectra_all = np.zeros((len(channel_ids),len(frequencies)))
    spectra_force = np.zeros((len(channel_ids),len(frequencies)))
    for headers, events in zip(data_provider.uproot_iterator_header, data_provider.uproot_iterator_data):
        mask_station = headers['station_number'] == station_id
        try:
            mask_force_trigger = headers['trigger_info.force_trigger'][mask_station]
        except ValueError:
            mask_force_trigger = np.zeros(len(mask_station), dtype=bool)

        traces = np.array(events['radiant_data[24][2048]'][:, channel_ids, :])[mask_station]
        spectra = np.abs(NuRadioReco.utilities.fft.time2freq(traces, sampling_rate))
        spectra_all += np.sum(spectra, axis=0)
        spectra_force += np.sum(spectra[mask_force_trigger], axis=0)
        n_total += len(spectra)
        n_forced += np.sum(mask_force_trigger)
    print('n_events {} forced trigger {}'.format(n_total, n_forced))
    if suppress_zero_mode:
        spectra_all[:,0] = 0
        spectra_force[:,0] = 0
    return frequencies, spectra_all / np.max([n_total,1]), spectra_force / np.max([n_forced,1])