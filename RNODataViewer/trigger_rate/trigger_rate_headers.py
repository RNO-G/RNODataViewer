import numpy as np
import itertools

from dash import html, dcc, callback
from dash import dcc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.subplots
import RNODataViewer.base.data_provider_root
import RNODataViewer.base.error_message
from NuRadioReco.utilities import units
from astropy.time import Time, TimeDelta
from NuRadioReco.framework.base_trace import BaseTrace
layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.Div('Event rate from headers.root', style={'flex': '1'}),
                html.Div([
                    html.Button([
                        html.Div('', className='icon-cw')
                    ], id='triggeruproot-reload-button', className='btn btn-primary')
                ], style={'flex': 'none'})
            ], className='flexi-box')
        ], className='panel panel-heading'),
        html.Div([
            dcc.Graph(id='triggeruproot-plot')
        ], className='panel panel-body')
    ], className='panel panel-default')
])

@callback(
    Output('triggeruproot-plot', 'figure'),
    [Input('triggeruproot-reload-button', 'n_clicks')],
    [State('station-id-dropdown', 'value')]
)
def update_trigger_header_plot(n_clicks, station_id):
    if station_id is None:
        return RNODataViewer.base.error_message.get_error_message('No Station selected')
    data_provider = RNODataViewer.base.data_provider_root.RNODataProviderHeaders()
    first_event = data_provider.get_first_event(station_id)
    if first_event is None:
        return RNODataViewer.base.error_message.get_error_message('Station {} not found in events'.format(station_id))
    times = []
    gps_times = []

    trigger_masks = {'rf_trigger' : [],
            'force_trigger': [],
            'pps_trigger': [],
            'ext_trigger': [],
            'radiant_trigger': [],
            'lt_trigger': [],
            'surface_trigger': []}

    data_provider.set_iterators()

    for headers in data_provider.uproot_iterator_header:
        mask_station = headers['station_number'] == station_id
        gps_times.append(headers['readout_time'][mask_station])
        for trigger_key in trigger_masks:
            trigger_masks[trigger_key].append(np.array(headers['trigger_info.'+trigger_key][mask_station]))
    gps_times = np.concatenate(gps_times)

    for k in trigger_masks:
        trigger_masks[k] = np.concatenate(trigger_masks[k])
    trigger_masks["all"] = np.ones_like(trigger_masks['rf_trigger'])

    bins = np.arange(min(gps_times), max(gps_times)+60*5, 60*5)#min(Time(gps_times, format="unix", scale="utc")), max(Time(gps_times, format="unix", scale="utc"))+dt, dt)
    bins_fits = Time(bins, format="unix", scale="utc").fits

    contents, bins = np.histogram(np.array(gps_times), bins)

    subplot_titles = []

    subplot_titles.append('Station {}'.format(station_id))
    sort_args = np.argsort(gps_times)
    times = Time(gps_times, format="unix", scale="utc").fits
    bincenters = Time((bins[1:]+bins[:-1])/2., format="unix", scale="utc").fits

    plots = []
    for key in reversed(trigger_masks):
        contents, b = np.histogram(np.array(gps_times)[trigger_masks[key]], bins)
        plots.append(go.Scatter(
              x = bincenters,
              y = contents/(60.*5),
              mode='lines+markers',
              name='Trigger: {}'.format(key)#,
              #text=point_labels
        ))
    fig = go.Figure(plots)
    fig.update_layout(
          xaxis={'title': 'time'},
          yaxis={'title': 'Rate [Hz]'}
      )
    fig.update_yaxes(rangemode="tozero")
    return fig
