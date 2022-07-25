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

data_provider_run = RNODataViewer.base.data_provider_root.RNODataProviderRoot()


##app.title = 'RNO Data Browser'
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
            html.Button('open file', id='btn-open-file', className='btn btn-default')
            ], className='input-group-btn', style={'vertical-align':'bottom'}),
        ], className='input-group',style={'width':'90%'}),
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
