import numpy as np
from RNODataViewer.base.app import app
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
from dash import callback_context
import plotly
import plotly.subplots
import plotly.graph_objs as go
import RNODataViewer.base.error_message
from NuRadioReco.utilities import units
from astropy.time import Time, TimeDelta
import pandas as pd
from file_list.run_stats import run_table
idx = pd.IndexSlice
run_info_options = [
    {'label':'Number of events (Greenland)', 'value':'n_events (greenland)'},
    {'label':'Trigger rate [Hz]', 'value':'trigger rate [Hz]'},
    {'label':'Number of events (transferred)', 'value':'n_events (transferred)'},
    {'label':'Transfer subsampling', 'value':'transfer subsampling'},
    {'label':'Soft rate [Hz]', 'value':'soft_rate [Hz]'},
    {'label':'Run duration [min]', 'value':'run_length'}
]

layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.Div('Run info', style={'flex': '1'}),
                html.Div([
                    html.Button('Show', id='run-data-showhide')
                ],  style={'flex':'none', 'margin-right':'5px'}),
                html.Div([
                    html.Button([
                        html.Div('', className='icon-cw')
                    ], id='run-data-reload-button', className='btn btn-primary')
                ], style={'flex': 'none'})
            ], className='flexi-box')
        ], className='panel panel-heading'),
        html.Div([
            dcc.Dropdown(
                id='run-data-plot-choice', options=run_info_options,
                value='n_events (greenland)'
            ),
            dcc.Graph(id='run-data-plot')
        ], className='panel panel-body',id='run-data-plot-container', style={'display':'none'})
    ], className='panel panel-default')
])

@app.callback(
    Output('run-data-plot', 'figure'),
    [Input('run-data-reload-button', 'n_clicks'),
     Input('run-data-plot-choice', 'value')],
    [State('time-selector', 'value'),
     State('station-id-dropdown', 'value')]
)
def plot_run_data(n_clicks, which_plot, time_value, station_ids):
    t_start, t_end = time_value
    selected = run_table[(np.array(run_table["mjd_first_event"])>t_start) & (np.array(run_table["mjd_last_event"])<t_end)]
    if len(selected) == 0:
        return go.Figure()
    plot_colors = plotly.colors.qualitative.Plotly
    fig = go.Figure()
    for i_station, station_id in enumerate(station_ids):
        table_i = selected.query('station==@station_id')
        normal_runs = table_i.loc[table_i.comment.isna()]
        special_runs = table_i.dropna(subset=["comment"])
        if which_plot == 'run_length': 
            y_normal = (normal_runs.mjd_last_event - normal_runs.mjd_first_event) * 1440
            y_special = (special_runs.mjd_last_event - special_runs.mjd_first_event) * 1440
        else:
            y_normal = normal_runs.loc[idx[:], which_plot]
            y_special = special_runs.loc[idx[:], which_plot]
        normal_runs = table_i.loc[table_i.comment.isna()]
        special_runs = table_i.dropna(subset=["comment"])
        fig.add_trace(
            go.Scatter(
                x=Time(normal_runs.mjd_first_event, format='mjd').fits,
                y=y_normal,
                mode='markers',
                name="Station {}".format(station_id),
                marker={'symbol':100,'color':plot_colors[i_station % len(plot_colors)], 'opacity':1.0,'size':7},
                customdata=normal_runs.run,
                hovertemplate="%{y}<br>%{x}<br>Run %{customdata}",
                legendrank=i_station
            )
        )
        fig.add_trace(
            go.Scatter(
                x=Time(special_runs.mjd_first_event, format='mjd').fits,
                y=y_special,
                mode='markers',
                name="Station {} (special run)".format(station_id),
                marker={'color':plot_colors[i_station % len(plot_colors)], 'symbol':34, 'line_width':1, 'line_color':plot_colors[i_station % len(plot_colors)], 'opacity':1.0, 'size':7},
                customdata=special_runs.run,
                meta=special_runs.comment.astype('str'),
                hovertemplate="%{y}<br>%{x}<br>Run %{customdata}<br>%{meta}",
                legendrank=i_station+1000
            )
        )
    fig['layout']['yaxis']['title'] = [i for i in run_info_options if i['value']==which_plot][0]['label']
    fig['layout']['legend']['uirevision'] = n_clicks
    return fig

@app.callback(
    [Output('run-data-plot-container', 'style'),
     Output('run-data-showhide','children')],
    [Input('run-data-reload-button', 'n_clicks'),
     Input('run-data-showhide', 'n_clicks')],
    [State('run-data-showhide', 'children'),
     State('run-data-plot-container', 'style')],
     prevent_initial_call=True
)
def show_hide_plot(n_clicks1, n_clicks2, show_or_hide, style):
    trigger = callback_context.triggered[0]['prop_id'].split('.')[0]
    if trigger == 'run-data-reload-button':
        style['display'] = 'inherit'
        return style, 'Hide'
    elif trigger == 'run-data-showhide':
        if show_or_hide == 'Hide':
            style['display'] = 'none'
            return style, 'Show'
        else:
            style['display'] = 'inherit'
            return style, 'Hide'
    else:
        return style, 'Hide'