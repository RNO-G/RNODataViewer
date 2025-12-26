import numpy as np
#from NuRadioReco.eventbrowser.app import app

from dash import html, dcc, callback
from dash import dcc
from dash.dependencies import Input, Output, State
from dash import callback_context
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import plotly.subplots
import RNODataViewer.base.error_message
import RNODataViewer.spectrogram.spectrogram_data
from NuRadioReco.utilities import units
from station_selection.station_list import channel_entries
import pandas as pd

channel_mapping = pd.DataFrame(channel_entries)
channel_mapping.set_index("value", inplace=True)

layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.Div('Average spectrogram', style={'flex': '1'}),
                html.Div([
                    html.Button('Show', id='spectrogram-avg-showhide')
                ],  style={'flex':'none', 'margin-right':'5px'}),
                html.Div([
                    html.Button([
                        html.Div('', className='icon-cw')
                    ], id='spectrogram-avg-reload-button', className='btn btn-primary')
                ], style={'flex': 'none'})
            ], className='flexi-box')
        ], className='panel panel-heading'),
        html.Div([
            dcc.RadioItems(
                id='spectrogram-avg-plot-layout',
                options=[
                    {'label':'Individual channels', 'value':'separate'},
                    {'label':'Grouped (all events)', 'value':'grouped0'},
                    {'label':'Grouped (forced triggers only)', 'value':'grouped1'},
                    ],
                value='separate'
            ),
            dcc.Graph(id='spectrogram-avg-plot')
        ], className='panel panel-body', id='spectrogram-avg-plot-container', style={'display':'none'})
    ], className='panel panel-default')
])

@callback(
    Output('spectrogram-avg-plot', 'figure'),
    [Input('spectrogram-avg-reload-button', 'n_clicks'),
     Input('spectrogram-avg-plot-layout', 'value')],
    [State('station-id-dropdown-single', 'value'),
     State('channel-id-dropdown', 'value'),
     State('file-name-dropdown-2', 'value'),
     State('spectrogram-avg-plot', 'figure')],
    background=True,
    # running=[
    #     (Output('spectrogram-avg-reload-button', 'disabled'), True, False)
    # ],
    # cancel=[
    #     Input('station-id-dropdown-single', 'value'),
    #     Input('channel-id-dropdown', 'value'),
    #     Input('file-name-dropdown-2', 'value'),
    #     Input('tab-selection', 'value')
    # ]
)
def update_spectrogram_plot(n_clicks, plot_layout, station_id, channel_ids, file_names, current_fig):
    if len(file_names) == 0:
        return RNODataViewer.base.error_message.get_error_message('No File chosen')
    if station_id is None:
        return RNODataViewer.base.error_message.get_error_message('No Station selected')
    if len(channel_ids) == 0:
        return RNODataViewer.base.error_message.get_error_message('No Channels selected')
    if callback_context.triggered[0]['prop_id'].split('.')[0]=='spectrogram-avg-plot-layout':
        traces = current_fig['data']
        if len(traces) == 0:
            raise PreventUpdate
        channel_ids = np.sort(np.unique([int(trace['uid'].split('_')[-1]) for trace in traces]))
    else:
        frequencies, spectra_all, spectra_forced = RNODataViewer.spectrogram.spectrogram_data.get_spectrogram_average_root(
            station_id, channel_ids, file_names, suppress_zero_mode=True)
        traces = []
        for i_channel, channel_id in enumerate(channel_ids):
            traces.append(
                go.Scatter(
                    x=frequencies / units.MHz,
                    y=spectra_forced[i_channel],
                    # name='Forced trigger only',
                    uid='avg_spectrum_forced_{}'.format(channel_id),
                    # legendgroup='Forced trigger only',
                    # showlegend=not bool(i_channel),
                    # line={'dash':'solid', 'color':'black'}
                )
            )
            traces.append(
                go.Scatter(
                    x=frequencies / units.MHz,
                    y=spectra_all[i_channel],
                    # name='All events',
                    uid='avg_spectrum_all_{}'.format(channel_id),
                    # legendgroup='All events',
                    # showlegend=not bool(i_channel),
                    # line={'color':'blue','dash':'dot'}
                )
            )
    if plot_layout == 'separate':
        subplot_titles = [channel_mapping.label[channel_id] for channel_id in channel_ids]
        n_rows = (len(channel_ids) - 1) // 4 + 1
        fig = plotly.subplots.make_subplots(
            cols=4,
            rows=n_rows,
            subplot_titles=subplot_titles,
            x_title='f [MHz]',
            y_title='Amplitude [mV / MHz]',
            shared_xaxes='all',
            shared_yaxes='all',
            vertical_spacing=.2 / n_rows,
            horizontal_spacing=3e-3
        )
        for i_channel, channel_id in enumerate(channel_ids):
            forced_trace = [trace for trace in traces if trace['uid'] == 'avg_spectrum_forced_{}'.format(channel_id)][0]
            all_trace = [trace for trace in traces if trace['uid'] == 'avg_spectrum_all_{}'.format(channel_id)][0]
            forced_trace['visible'] = True
            forced_trace['name'] = 'Forced trigger only'
            forced_trace['legendgroup'] = 'Forced trigger'
            forced_trace['showlegend'] = not bool(i_channel)
            forced_trace['line'] ={'color':'black', 'dash':'solid'}
            all_trace['visible'] = True
            all_trace['name'] = 'All events'
            all_trace['legendgroup'] = 'All events'
            all_trace['showlegend'] = not bool(i_channel)
            all_trace['line'] ={'color':'blue', 'dash':'dot'}

            fig.add_trace(
                forced_trace, row=i_channel // 4 + 1, col=i_channel % 4 + 1
            )
            fig.add_trace(
                all_trace, row=i_channel // 4 + 1, col=i_channel % 4 + 1
            )
            fig['layout']['xaxis{}'.format(i_channel + 1)].update(showticklabels=True)
        fig.update_layout({'height': 300 * n_rows})
        return fig
    elif (plot_layout == 'grouped0') or (plot_layout == 'grouped1'):
        if plot_layout == 'grouped0':
            uid_mask = 'avg_spectrum_all_{}', 'avg_spectrum_forced_{}'
        else:
            uid_mask = 'avg_spectrum_forced_{}', 'avg_spectrum_all_{}'
        channel_groups = [
            [i for i in channel_ids if 'PA' in channel_mapping.label[i]],
            [i for i in channel_ids if 'Vpol' in channel_mapping.label[i]],
            [i for i in channel_ids if 'Hpol' in channel_mapping.label[i]],
            [i for i in channel_ids if 'Surf' in channel_mapping.label[i]],
        ]
        subplot_titles = ['Phased Array', 'VPol', 'HPol', 'Surface']
        fig = plotly.subplots.make_subplots(
            cols=4, rows=1,
            subplot_titles=subplot_titles,
            x_title='f [MHz]',
            y_title='Amplitude [mV / MHz]',
            shared_xaxes='all',
            shared_yaxes='all',
            horizontal_spacing=3e-3
        )
        for i_channel, channel_id in enumerate(channel_ids):
            i_col = [j for j in range(4) if channel_id in channel_groups[j]][0] + 1
            trace = [trace for trace in traces if trace['uid'] == uid_mask[0].format(channel_id)][0]
            trace['name'] = channel_mapping.label[channel_id]
            trace['legendgroup'] = ""
            trace['visible'] = True
            trace['showlegend'] = True
            trace['legendrank'] = i_col
            trace['line'] = {'dash':'solid'}
            fig.add_trace(
                trace, row=1, col=i_col
            )
            hidden_trace = [trace for trace in traces if trace['uid'] == uid_mask[1].format(channel_id)][0]
            hidden_trace['visible'] = False
            fig.add_trace(
                hidden_trace, row=1, col=i_col
            )
        fig.update_layout(height = 500)
        return fig


    # if not station_found:
    #     return RNODataViewer.base.error_message.get_error_message('Station {} not found in events'.format(station_id))
    subplot_titles = []
    for channel_id in channel_ids:
        subplot_titles.append(channel_mapping.label[channel_id])
    n_rows = (len(channel_ids) - 1) // 4 + 1
    fig = plotly.subplots.make_subplots(
        cols=4,
        rows=n_rows,
        subplot_titles=subplot_titles,
        x_title='f [MHz]',
        y_title='Amplitude [mV / MHz]',
        shared_xaxes='all',
        shared_yaxes='all',
        vertical_spacing=.2 / n_rows,
        horizontal_spacing=3e-3
    )

    for i_channel, channel_id in enumerate(channel_ids):
        fig.add_trace(
            go.Scatter(
                x=frequencies / units.MHz,
                y=spectra_forced[i_channel],
                name='Forced trigger only',
                uid='avg_spectrum_forced_{}'.format(channel_id),
                legendgroup='Forced trigger only',
                showlegend=not bool(i_channel),
                line={'dash':'solid', 'color':'black'}
            ), row=i_channel // 4 + 1, col=i_channel % 4 + 1
        )
        fig.add_trace(
            go.Scatter(
                x=frequencies / units.MHz,
                y=spectra_all[i_channel],
                name='All events',
                uid='avg_spectrum_all_{}'.format(channel_id),
                legendgroup='All events',
                showlegend=not bool(i_channel),
                line={'color':'blue','dash':'dot'}
            ), row=i_channel // 4 + 1, col=i_channel % 4 + 1
        )

        fig['layout']['xaxis{}'.format(i_channel + 1)].update(showticklabels=True)
    fig.update_layout({'height': 300 * n_rows})
    return fig

@callback(
    [Output('spectrogram-avg-plot-container', 'style'),
     Output('spectrogram-avg-showhide','children')],
    [Input('spectrogram-avg-reload-button', 'n_clicks'),
     Input('spectrogram-avg-showhide', 'n_clicks')],
    [State('spectrogram-avg-showhide', 'children'),
     State('spectrogram-avg-plot-container', 'style')],
     prevent_initial_call=True
)
def show_hide_plot(n_clicks1, n_clicks2, show_or_hide, style):
    trigger = callback_context.triggered[0]['prop_id'].split('.')[0]
    if trigger == 'spectrogram-avg-reload-button':
        style['display'] = 'inherit'
        return style, 'Hide'
    elif trigger == 'spectrogram-avg-showhide':
        if show_or_hide == 'Hide':
            style['display'] = 'none'
            return style, 'Show'
        else:
            style['display'] = 'inherit'
            return style, 'Hide'
    else:
        return style, 'Hide'