from dash import html, dcc, callback, MATCH, ALL
from dash import dcc
from dash.exceptions import PreventUpdate
import pandas as pd
from dash.dependencies import Input, Output, State
import astropy.time
import numpy as np
from .run_stats import run_table
import os
import zipfile
import logging

logger = logging.getLogger()

layout = html.Div([
    html.Div([
        html.Div([
            html.Div('File Names', style={'flex': '1'}),
            html.Div([
                html.Button([
                    html.Div('', className='icon-cw')
                ], id='file-list-reload-button', className='btn btn-primary')
            ], style={'flex': 'none'})
        ], className='flexi-box')
    ], className='panel panel-heading'),
    html.Div([
        html.Div('', id='file-list-display')
    ], className='panel panel-body', style={'max-height': '100px', 'overflow': 'scroll'})
], className='panel panel-default')



@callback(
    Output('file-list-display', 'children'),
    [Input('file-list-reload-button', 'n_clicks'),
     Input('time-selector-start-date', 'date'),
     Input('time-selector-start-time', 'value'),
     Input('time-selector-end-date', 'date'),
     Input('time-selector-end-time', 'value'),
     Input('overview-station-id-dropdown', 'value'),
     Input({'type':'show_more_button', 'index':ALL}, 'n_clicks')
     ],
)
def update_file_list(n_clicks, start_date, start_time, end_date, end_time, station_ids, show_n_files_clicks):
    try:
        t_start = astropy.time.Time(start_date) + astropy.time.TimeDelta(start_time, format='sec')
        t_end = astropy.time.Time(end_date) + astropy.time.TimeDelta(end_time, format='sec')
    except ValueError: # probably someone is typing!
        raise PreventUpdate
    if t_start > t_end:
        raise PreventUpdate
    tab = run_table.get_table()
    selected = tab[(np.array(tab.loc[:,"time_start"])>t_start) & (np.array(tab.loc[:,"time_end"])<t_end)].sort_values(['station', 'time_start'])
    selected = selected.query('station in @station_ids')

    if not len(show_n_files_clicks):
        show_n_files_clicks = 1
    else:
        show_n_files_clicks = show_n_files_clicks[-1]

    download_buttons = [
        html.Div([html.Button(
            f'station{selected.loc[i].station}/run{selected.loc[i].run:.0f}',
            id={'type': 'file_download_button', 'path':selected.loc[i].filenames_root},
            n_clicks=None, title='Click to download'
        ), dcc.Download(id={'type':'file_download_trigger', 'path':selected.loc[i].filenames_root})]) for i in selected.index[:50*show_n_files_clicks]
    ]
    if len(selected) > 50*show_n_files_clicks:
        expand_list_button = html.Div([html.Button(
            'Show more...', id={'type':'show_more_button','index':show_n_files_clicks}, title='Show more files...', n_clicks=show_n_files_clicks
        )])
        download_buttons += [expand_list_button]

    return download_buttons

@callback(
   Output({"type": "file_download_trigger", 'path':MATCH}, "data"),
   [Input({"type":"file_download_button", 'path':MATCH}, 'n_clicks')],
   [State({"type":"file_download_button", 'path':MATCH}, 'id')],
   prevent_initial_call=True
)
def file_download(n_clicks, which_file):
    if n_clicks is None:
        raise PreventUpdate

    file_dir = os.path.dirname(which_file['path'])
    logger.info(f'Preparing {file_dir} for download...')
    files = os.listdir(file_dir)
    target_dir = file_dir.replace(os.environ['RNO_DATA_DIR'], '')

    def zip_folder(bytesio):
        with zipfile.ZipFile(bytesio, 'w') as zf:
            for f in files:
                zf.write(os.path.join(file_dir, f), os.path.join(target_dir, f))
        logger.info('Finished zipping, sending zipped file...')

    return dcc.send_bytes(zip_folder, filename='inbox.zip')
