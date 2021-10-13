import numpy as np
#from NuRadioReco.eventbrowser.app import app
from RNODataViewer.base.app import app
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
from dash import callback_context
import plotly.graph_objs as go
import RNODataViewer.base.data_provider_nur
import RNODataViewer.base.error_message
from NuRadioReco.utilities import units
from NuRadioReco.framework.parameters import channelParameters as chp
import RNODataViewer.noise_rms.noise_rms_data
import webbrowser

layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.Div('Noise RMS', style={'flex': '1'}),
                html.Div([
                    html.Button('Show', id='noise-rms-showhide')
                ],  style={'flex':'none', 'margin-right':'5px'}),
                html.Div([
                    html.Button([
                        html.Div('', className='icon-cw')
                    ], id='noise-rms-reload-button', className='btn btn-primary')
                ], style={'flex': 'none'})
            ], className='flexi-box')
        ], className='panel panel-heading'),
        html.Div([
            dcc.Graph(id='noise-rms-plot')
        ], id='noise-rms-plot-container', className='panel panel-body', style={'display':'none'})
    ], className='panel panel-default')
])

def do_click(trace, points, state):
    if points.point_inds:
        ind = points.point_inds[0]
    url = "https://www.zeuthen.desy.de/~shallman/rnog_run_summary.html"
    webbrowser.open_new_tab(url)
    print("click")

@app.callback(
    Output('noise-rms-plot', 'figure'),
    [Input('noise-rms-reload-button', 'n_clicks')],
    [State('station-id-dropdown-single', 'value'),
     State('channel-id-dropdown', 'value'),
     State('file-name-dropdown-2', 'value'),]
)
def update_noise_rms_plot(n_clicks, station_id, channel_ids, file_names):
    print("updating noise rms plot")
    if len(file_names) == 0:
        return RNODataViewer.base.error_message.get_error_message('No File chosen')
    if station_id is None:
        return RNODataViewer.base.error_message.get_error_message('No Station selected')
    if len(channel_ids) == 0:
        return RNODataViewer.base.error_message.get_error_message('No Channels selected')
    has_station, times, noise_rms, point_labels = RNODataViewer.noise_rms.noise_rms_data.get_noise_rms_data_root(station_id, channel_ids, file_names)
    if not has_station:
        return RNODataViewer.base.error_message.get_error_message('Station {} not found in events'.format(station_id))
    plots = []
    for i_channel, channel_id in enumerate(channel_ids):
        scatter = go.Scatter(
            x=times,
            y=noise_rms[i_channel] / units.mV,
            mode='markers',
            name='Channel {}'.format(channel_id),
            text=point_labels
        )
        scatter.on_click(do_click)
        plots.append(scatter)
    fig = go.Figure(plots)
    fig.data[0].on_click(do_click)
    fig.update_layout(
        xaxis={'title': 'time'},
        yaxis={'title': 'noise RMS [mV]'}
    )
    fig.update_layout(
        xaxis_tickformatstops=[
            dict(dtickrange=[None, 1000], value="%H:%M:%S.%L"),
            dict(dtickrange=[1000, 60000], value="%H:%M:%S"),
            dict(dtickrange=[60000, 3600000], value="%H:%M"),
            dict(dtickrange=[3600000, 86400000], value="%H:%M %e.%B"),
            dict(dtickrange=[86400000, 604800000], value="%e. %b %y"),
            dict(dtickrange=[604800000, "M1"], value="%e. %b '%y"),
            dict(dtickrange=["M1", "M12"], value="%b '%y M"),
            dict(dtickrange=["M12", None], value="%Y")
    ]
    )
    fig.update_xaxes(nticks=10)
    return fig

@app.callback(
    [Output('noise-rms-plot-container', 'style'),
     Output('noise-rms-showhide','children')],
    [Input('noise-rms-reload-button', 'n_clicks'),
     Input('noise-rms-showhide', 'n_clicks')],
    [State('noise-rms-showhide', 'children'),
     State('noise-rms-plot-container', 'style')],
     prevent_initial_call=True
)
def show_hide_rms_plot(n_clicks1, n_clicks2, show_or_hide, style):
    trigger = callback_context.triggered[0]['prop_id'].split('.')[0]
    if trigger == 'noise-rms-reload-button':
        style['display'] = 'inherit'
        return style, 'Hide'
    elif trigger == 'noise-rms-showhide':
        if show_or_hide == 'Hide':
            style['display'] = 'none'
            return style, 'Show'
        else:
            style['display'] = 'inherit'
            return style, 'Hide'
    else:
        return style, 'Hide'