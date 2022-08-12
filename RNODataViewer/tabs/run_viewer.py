from dash import html
import os
import dash
from dash import dcc
from dash.dependencies import Input, Output, State
from RNODataViewer.base.app import app
import webbrowser
import RNODataViewer.base.data_provider_root
import RNODataViewer.base.data_provider_nur
import RNODataViewer.file_list.file_list
import RNODataViewer.station_selection.station_selection
import RNODataViewer.spectrogram.spectrogram
import RNODataViewer.spectrogram.spectrogram_average_plot
import RNODataViewer.noise_rms.noise_rms
from file_list.run_stats import run_table
import numpy as np
from dash import callback_context
from dash.exceptions import PreventUpdate


data_provider_run = RNODataViewer.base.data_provider_root.RNODataProviderRoot()


run_viewer_layout = html.Div([
        RNODataViewer.station_selection.station_selection.layout_run_browser,
        html.Div([html.Div([
            html.Div('Selected runs', className='option-label'),
            dcc.Dropdown(id='file-name-dropdown-2',
                options=[],
                value=[],
                multi=True,
                className='custom-dropdown')],style={'width':'100%'}),
        html.Div([
            html.Div([
            html.Button('Most recent run', id='select-last-run', style={'display':'block', 'minWidth':'150px','margin-top':2,'margin-bottom':2}),
            html.Button('Most recent 24 hours', id='select-last-24h', style={'display':'block','minWidth':'150px', 'margin-top':2,'margin-bottom':2}),
            ], style={'vertical-align':'bottom'}),], className='flexi-element-1')
        ], className='flexi-box',style={'width':'100%'}),
    html.Div([
        html.Div([
            RNODataViewer.noise_rms.noise_rms.layout
        ], className='flexi-element-4')

    ], className='flexi-box'),
    html.Div([
        html.Div([
            RNODataViewer.spectrogram.spectrogram.layout
        ], className='flexi-element-1')
    ], className='flexi-box'),
    html.Div([
        html.Div([
            RNODataViewer.spectrogram.spectrogram_average_plot.layout
        ], className='flexi-element-1')
    ], className='flexi-box')
])

@app.callback(
    Output('file-name-dropdown-2', 'value'),
    [Input('select-last-run', 'n_clicks'),
     Input('select-last-24h', 'n_clicks'),
    ],
    State('station-id-dropdown-single', 'value'),
    prevent_initial_call=True

)
def select_runs_button(last_run, last_24h, stations, run_table=run_table):
    trigger = callback_context.triggered[0]['prop_id'].split('.')[0]
    tab = run_table.get_table()
    station_mask = np.array([np.isin(s, stations) for s in tab.station], dtype=bool)
    tab_selected = tab[station_mask]
    tab_selected_sort = tab_selected.sort_values(by='mjd_last_event')
    if trigger == 'select-last-run':
        return [tab_selected_sort.iloc[-1].loc['filenames_root']]
    elif trigger == 'select-last-24h':
        last_mjd = tab_selected_sort.iloc[-1].loc['mjd_last_event']
        tab_last_24h = tab_selected_sort.query('mjd_last_event>@last_mjd-1')
        return tab_last_24h.filenames_root
    else:
        raise PreventUpdate

@app.callback(Output('file-name-dropdown-2', 'options'),
              [Input('station-id-dropdown-single', 'value')])
def set_filename_dropdown(stations , run_table=run_table):
        tab = run_table.get_table()
        station_mask = np.array([np.isin(s, stations) for s in tab.station], dtype=bool)
        tab_selected = tab[station_mask]
        filtered_names = list(tab_selected.filenames_root)
        data_provider_run.set_filenames([])
        rrr =  [{'label': "Station {}, Run {}".format(row.station, row.run), 'value': row.filenames_root} for index, row in tab_selected.iterrows()]
        return rrr
