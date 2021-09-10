import numpy as np
import itertools
#from NuRadioReco.eventbrowser.app import app
from RNODataViewer.base.app import app
import dash_html_components as html
import dash_core_components as dcc
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
                html.Div('Event rate', style={'flex': '1'}),
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

@app.callback(
    Output('triggeruproot-plot', 'figure'),
    [Input('triggeruproot-reload-button', 'n_clicks')],
    [State('station-id-dropdown', 'value')]
)
def update_triggeruproot_plot(n_clicks, station_ids):
    BINWIDTH_SEC = 10*60 #define how fine we want the binning
    if station_ids is None:
        return RNODataViewer.base.error_message.get_error_message('No Station selected')
    data_provider = RNODataViewer.base.data_provider_root.RNODataProviderRoot()
    
    plots = []
    subplot_titles = []

    # get the needed data:
    station_numbers = np.array([],dtype=int)
    trigger_times = np.array([])

    trigger_masks = {
            'rf_trigger' : np.array([],dtype=bool),
            'force_trigger': np.array([],dtype=bool),
            'pps_trigger': np.array([],dtype=bool),
            'ext_trigger': np.array([],dtype=bool),
            'radiant_trigger': np.array([],dtype=bool),
            'lt_trigger': np.array([],dtype=bool)
            }
    trigger_line_styles = {
            'rf_trigger': 'dash',
            'force_trigger': 'longdash',
            'pps_trigger': 'dashdot',
            'ext_trigger': 'longdashdot',
            'radiant_trigger': '5px 10px 2px 2px',
            'lt_trigger': 'dot',
            'total': 'solid'
            }

    data_provider.set_iterators()
    for headers in data_provider.uproot_iterator_header:
        station_numbers = np.append(station_numbers, np.array(headers['station_number']))
        trigger_times = np.append(trigger_times, np.array(headers['readout_time']))
        for trigger_key in trigger_masks:
            trigger_masks[trigger_key] = np.append(trigger_masks[trigger_key], np.array(headers['trigger_info.'+trigger_key]))
    trigger_masks['total'] = np.ones_like(station_numbers, dtype=bool)

    for station_id in station_ids:        
        mask_station = station_numbers == station_id

        bins = np.arange(min(trigger_times), max(trigger_times)+BINWIDTH_SEC, BINWIDTH_SEC)
        bins_fits = Time(bins, format="unix", scale="utc").fits

        subplot_titles.append('Station {}'.format(station_id))
        bincenters = Time((bins[1:]+bins[:-1])/2., format="unix", scale="utc").fits

        for key in trigger_masks:# ["total"]: #trigger_masks
            contents, b = np.histogram(trigger_times[trigger_masks[key]&mask_station], bins)
            point_labels = None #contents
            if key=="total":
                visible = True
                line_dict = dict(width=4)
                mode = 'lines+markers'
            else:
                visible='legendonly'
                line_dict = dict(dash=trigger_line_styles[key])
                mode = 'lines'
            
            plots.append(go.Scatter(
                x = bincenters,
                y = contents/(BINWIDTH_SEC),
                mode=mode,
                name='Station: {}, Trigger: {}'.format(station_id, key.replace("_trigger","")),
                visible=visible,
                line=line_dict,
                text=point_labels
            ))
    fig = go.Figure(plots)
    fig.update_layout(
          xaxis={'title': 'date'},
          yaxis={'title': 'Rate [Hz]'}
      )
    fig.update_yaxes(rangemode='tozero')
    return fig
