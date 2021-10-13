import numpy as np
from RNODataViewer.base.app import app
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
import plotly
import plotly.subplots
import plotly.graph_objs as go
import RNODataViewer.base.error_message
from NuRadioReco.utilities import units
from astropy.time import Time, TimeDelta
import pandas as pd
from file_list.run_stats import run_table

layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.Div('Active Triggers', style={'flex': '1'}),
                html.Div([
                    html.Button([
                        html.Div('', className='icon-cw')
                    ], id='active-triggers-reload-button', className='btn btn-primary')
                ], style={'flex': 'none'})
            ], className='flexi-box')
        ], className='panel panel-heading'),
        html.Div([
            dcc.Graph(id='active-triggers-plot')
        ], className='panel panel-body')
    ], className='panel panel-default')
])

@app.callback(
    Output('active-triggers-plot', 'figure'),
    Input('active-triggers-reload-button', 'n_clicks'),
    [State('time-selector', 'value'),
     State('station-id-dropdown', 'value')]
)
def plot_active_triggers(n_clicks, time_value, station_ids):
    t_start, t_end = time_value
    trigger_cols = [
        'has_rf0 (surface)', 'has_rf1 (deep)', 'has_ext (low threshold)', 
        'has_pps (PPS signal)', 'has_soft (forced)'
    ]
    trigger_names = [
        'surface trigger', 'deep trigger', 'low threshold',
         'pulse-per-second (pps)', 'forced trigger'
    ]
    trigger_colors = ['blue', 'red', 'green', 'purple', 'orange']
    selected = run_table[(np.array(run_table["mjd_first_event"])>t_start) & (np.array(run_table["mjd_last_event"])<t_end)]
    if len(selected) == 0:
        return go.Figure()
    n_rows = len(station_ids)
    # subplot_titles = ["Station {}".format(i) for i in station_ids]
    fig = plotly.subplots.make_subplots(
        cols=1, rows=n_rows, shared_xaxes='all', shared_yaxes='all',
        vertical_spacing=.2 / n_rows,
        specs=[[{'secondary_y':True},],]*n_rows)
    for i_station, station_id in enumerate(station_ids):
        table_i = selected.query('station==@station_id')
        x_times = Time(np.sort(np.concatenate([
            table_i["mjd_first_event"], table_i["mjd_first_event"], 
            table_i["mjd_last_event"], table_i["mjd_last_event"]
        ])), format='mjd').fits
        trigger_active = np.zeros((len(x_times), len(trigger_cols)))
        data_labels = np.concatenate([
            ['Run {} (start)'.format(run)]*2 + ['Run {} (end)'.format(run)]*2 
            for run in table_i.run
        ])
        for i_trigger, trigger in enumerate(trigger_cols):
            mask = 4 * np.where(table_i[trigger])[0]
            trigger_active[mask + 1, i_trigger] = 1
            trigger_active[mask + 2, i_trigger] = 1
        
            fig.add_trace(
                go.Scatter(
                    x=x_times,
                    #y=trigger_names,
                    y=trigger_active[:, i_trigger] + 1.5 * i_trigger,
                    legendgroup=trigger_names[i_trigger],
                    showlegend=not bool(i_station),
                    name=trigger_names[i_trigger],
                    text=data_labels,
                    line={'color':trigger_colors[i_trigger]}
                    ),
                    #type='heatmap'),                    
                secondary_y=False,
                row=i_station+1,
                col=1
            )
        fig.update_layout({
            'yaxis{}'.format(2*i_station+1):{
                'tickmode':'array', 'tickvals':np.arange(len(trigger_cols)) * 1.5 + .5,
                'fixedrange':True,
                'ticktext':trigger_names, 'side':'left', 'title':'<b>Station {}</b>'.format(station_id)}})
        fig.update_layout({
            'yaxis{}'.format(2 * i_station + 2):{
                'tickmode':'array', 'tickvals':np.unique(trigger_active), 
                'ticktext':['Off','On'] * (len(np.unique(trigger_active)) // 2), 'showticklabels':True}
        })
        
    return fig
