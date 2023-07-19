from __future__ import absolute_import, division, print_function  # , unicode_literals
from dash import html, dcc, callback, no_update
import NuRadioReco.eventbrowser.apps.trace_plots.channel_time_trace
import NuRadioReco.eventbrowser.apps.trace_plots.channel_spectrum
import NuRadioReco.eventbrowser.apps.trace_plots.multi_channel_plot
from dash.dependencies import State, Input, Output
# from NuRadioReco.eventbrowser.app import app
import logging

logger = logging.getLogger('traces')

layout = html.Div([
    html.Div(id='trigger-trace', style={'display': 'none'}),
    html.Div([
        html.Div([
            html.Div([
                'Channel Traces',
                html.Button('Show', id='toggle_channel_traces', n_clicks=0, style={'float':'right'})
                ], className='panel-heading'),
            html.Div(NuRadioReco.eventbrowser.apps.trace_plots.channel_time_trace.layout,
                     className='panel-body', id='channel_traces_layout')
        ], className='panel panel-default', style={'flex': '1'}),
        html.Div([
            html.Div([
                'Channel Spectrum', 
                ' (y-scale:  ',
                html.Button(
                    id='channel-spectrum-log-linear-switch', children='linear',
                ),
                ')',
                html.Button('Show', id='toggle_channel_spectrum', n_clicks=0, style={'float':'right'})
                ], className='panel-heading'),
            html.Div(NuRadioReco.eventbrowser.apps.trace_plots.channel_spectrum.layout,
                     className='panel-body', id='channel_spectrum_layout')
        ], className='panel panel-default', style={'flex': '1'})
    ], style={'display': 'flex'}),
    html.Div([
        html.Div([
            html.Div('Individual Channels', className='panel-heading'),
            html.Div(NuRadioReco.eventbrowser.apps.trace_plots.multi_channel_plot.layout, className='panel-body')
        ], className='panel panel-default', style={'flex': '1'})
    ], style={'display': 'flex'})
])

@callback(
    [Output('channel_traces_layout', 'style'),
    Output('toggle_channel_traces', 'children')],
    [Input('toggle_channel_traces', 'n_clicks')],
    State('toggle_channel_traces', 'children'),
    prevent_initial_callback=True
)
def toggle_channel_trace_plot(button_clicks, showhide):
    if showhide == 'Hide':
        return {'flex': '1', 'display': 'none'}, 'Show'
    else:
        return {'flex' : '1'}, 'Hide'

@callback(
    [Output('channel_spectrum_layout', 'style'),
    Output('toggle_channel_spectrum', 'children')],
    [Input('toggle_channel_spectrum', 'n_clicks')],
    State('toggle_channel_spectrum', 'children'),
    prevent_initial_callback=True
)
def toggle_channel_spectrum_plot(button_clicks, showhide):
    if showhide == 'Hide':
        return {'flex': '1', 'display': 'none'}, 'Show'
    else:
        return {'flex': '1'}, 'Hide'

@callback(
    [Output('channel-spectrum', 'figure', allow_duplicate=True), # this is a 'duplicate' callback - requires dash >= 2.9
     Output('time-traces', 'figure', allow_duplicate=True),
     Output('channel-spectrum-log-linear-switch', 'children')
    ],
    [Input('channel-spectrum-log-linear-switch', 'n_clicks')],
    [State('channel-spectrum-log-linear-switch', 'children'),
     State('channel-spectrum', 'figure'),
     State('time-traces', 'figure'),
    ], prevent_initial_call=True
)
def toggle_linear_log_scale(button_clicks, button_current_value, channel_spectrum, multichannel_plot):
    outputs = []
    if button_current_value == 'linear': # switch to log
        new_value = 'log'
    else:
        new_value = 'linear'
    try:
        channel_spectrum['layout']['yaxis']['type'] = new_value
        outputs.append(channel_spectrum)
    except KeyError:
        outputs.append(no_update)
    
    try:
        yaxes = [key for key in multichannel_plot['layout'].keys() if 'yaxis' in key]
        yaxes = [key for key in yaxes if len(key)>5] # omit key 'yaxis'
        yaxes_even = [key for key in yaxes if not (int(key.split('yaxis')[-1]) % 2)]
        for yaxis in yaxes_even:
            multichannel_plot['layout'][yaxis]['type'] = new_value
        outputs.append(multichannel_plot)
    except KeyError as e:
        outputs.append(no_update)
    
    outputs.append(new_value)
    return outputs

# @callback(
#     [Output('channel_traces_layout', 'children'),
#     Output('toggle_channel_traces', 'children')],
#     [Input('toggle_channel_traces', 'n_clicks')],
#     State('toggle_channel_traces', 'children'),
#     prevent_initial_call=True
# )
# def toggle_channel_trace_plot(button_clicks, showhide):
#     if showhide == 'Hide':
#         return [], 'Show'
#     else:
#         return NuRadioReco.eventbrowser.apps.trace_plots.channel_time_trace.layout, 'Hide'

# @callback(
#     [Output('channel_spectrum_layout', 'children'),
#     Output('toggle_channel_spectrum', 'children')],
#     [Input('toggle_channel_spectrum', 'n_clicks')],
#     State('toggle_channel_spectrum', 'children'),
#     prevent_initial_call=True
# )
# def toggle_channel_spectrum_plot(button_clicks, showhide):
#     if showhide == 'Hide':
#         return [], 'Show'
#     else:
#         return NuRadioReco.eventbrowser.apps.trace_plots.channel_spectrum.layout, 'Hide'
    
# @callback(

# )