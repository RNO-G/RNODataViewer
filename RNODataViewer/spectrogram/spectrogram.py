import numpy as np
#from NuRadioReco.eventbrowser.app import app
from RNODataViewer.base.app import app
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
from dash import callback_context
import plotly.graph_objs as go
import plotly.subplots
import RNODataViewer.base.data_provider_nur
import RNODataViewer.base.error_message
import RNODataViewer.spectrogram.spectrogram_data
from NuRadioReco.utilities import units
from station_selection.station_list import channel_entries
import pandas as pd

layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.Div('Spectrogram', style={'flex': '1'}),
                html.Div([
                    html.Button('Show', id='spectrogram-showhide')
                ],  style={'flex':'none', 'margin-right':'5px'}),
                html.Div([
                    html.Button([
                        html.Div('', className='icon-cw')
                    ], id='spectrogram-reload-button', className='btn btn-primary')
                ], style={'flex': 'none'})
            ], className='flexi-box')
        ], className='panel panel-heading'),
        html.Div([
            dcc.Graph(id='spectrogram-plot')
        ], className='panel panel-body', id='spectrogram-plot-container', style={'display':'none'})
    ], className='panel panel-default')
])


channel_mapping = pd.DataFrame(channel_entries)
channel_mapping.set_index("value", inplace=True)


@app.callback(
    Output('spectrogram-plot', 'figure'),
    [Input('spectrogram-reload-button', 'n_clicks')],
    [State('station-id-dropdown-single', 'value'),
     State('channel-id-dropdown', 'value'),
     State('file-name-dropdown-2', 'value')]
)
def update_spectrogram_plot(n_clicks, station_id, channel_ids, file_names):
    if len(file_names) == 0:
        return RNODataViewer.base.error_message.get_error_message('No File chosen')
    if station_id is None:
        return RNODataViewer.base.error_message.get_error_message('No Station selected')
    if len(channel_ids) == 0:
        return RNODataViewer.base.error_message.get_error_message('No Channels selected')
    station_found, times, spectra, d_f, labels = RNODataViewer.spectrogram.spectrogram_data.get_spectrogram_data_root(station_id, channel_ids, file_names)
    if not station_found:
        return RNODataViewer.base.error_message.get_error_message('Station {} not found in events'.format(station_id))
    subplot_titles = []
    for channel_id in channel_ids:
        subplot_titles.append(channel_mapping.label[channel_id])
    n_rows = (len(channel_ids)-1) // 4 + 1
    n_cols = int(np.min([len(channel_ids), 4]))
    fig = plotly.subplots.make_subplots(
        cols=n_cols,
        rows=n_rows,
        subplot_titles=subplot_titles,
        x_title='Event count',
        y_title='f [MHz]',
        shared_xaxes='all',
        shared_yaxes='all',
        vertical_spacing=0.2 / n_rows
    )

    xtitles = np.repeat(labels, len(spectra[0][0])).reshape(len(labels),len(spectra[0][0])).T
    for i_channel, channel_id in enumerate(channel_ids):
        i_row = i_channel // 4 + 1
        i_col = i_channel % 4 + 1
        fig.add_trace(
            go.Heatmap(
                z=np.abs(spectra[i_channel].T) / units.mV,
                x=times,
                y0=0.0,
                dy=d_f / units.MHz,
                customdata=xtitles,
                coloraxis='coloraxis',
                meta=xtitles,
                hovertemplate='%{customdata}<br>%{y}<br>amplitude [mV/Hz]: %{z}<extra></extra>'
                #name='Ch.{}'.format(channel_id)
            ), i_row, i_col
        )
        fig['layout']['xaxis{}'.format(i_channel+1)].update(showticklabels=True)
    fig.update_layout(coloraxis_colorbar={'title': 'U [mV]'}, height=300 * n_rows)
    fig.update_layout({"coloraxis_cmin": 0,
                       "coloraxis_cmax": 1e3})
    return fig

@app.callback(
    [Output('spectrogram-plot-container', 'style'),
     Output('spectrogram-showhide','children')],
    [Input('spectrogram-reload-button', 'n_clicks'),
     Input('spectrogram-showhide', 'n_clicks')],
    [State('spectrogram-showhide', 'children'),
     State('spectrogram-plot-container', 'style')],
     prevent_initial_call=True
)
def show_hide_plot(n_clicks1, n_clicks2, show_or_hide, style):
    trigger = callback_context.triggered[0]['prop_id'].split('.')[0]
    if trigger == 'spectrogram-reload-button':
        style['display'] = 'inherit'
        return style, 'Hide'
    elif trigger == 'spectrogram-showhide':
        if show_or_hide == 'Hide':
            style['display'] = 'none'
            return style, 'Show'
        else:
            style['display'] = 'inherit'
            return style, 'Hide'
    else:
        return style, 'Hide'