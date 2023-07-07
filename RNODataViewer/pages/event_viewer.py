from __future__ import absolute_import, division, print_function  # , unicode_literals
from dash.dependencies import Input, Output, State
from dash import dcc, html, callback
import dash
import json
from dash.exceptions import PreventUpdate
import numpy as np
import uuid
import glob
#from NuRadioReco.eventbrowser.app import app

from RNODataViewer.apps import traces
import os
import argparse
import NuRadioReco.eventbrowser.dataprovider
# import NuRadioReco.eventbrowser.dataprovider_root
from RNODataViewer.base.data_provider_root import data_provider_event
import logging
import webbrowser
from NuRadioReco.modules.base import module
from RNODataViewer.file_list.run_stats import run_table, DATA_DIR, station_entries #, RunStats
# logger = module.setup_logger(level=logging.INFO)
logger=logging.getLogger('RNODataViewer')

dash.register_page(__name__, path='/eventViewer')

data_folder = DATA_DIR

browser_provider = NuRadioReco.eventbrowser.dataprovider.DataProvider()
browser_provider.set_filetype(True)

filename_table = run_table.get_table().loc[:, ['station', 'run', 'filenames_root']].drop_duplicates(subset=['station', 'run'])
filename_table = filename_table.set_index(['station', 'run']).sort_index()

event_viewer_layout = html.Div([
    html.Div(id='event-click-coordinator', children=json.dumps(None), style={'display': 'none'}),
    html.Div(id='event-ids', style={'display': 'none'},
             children=json.dumps([])),
    html.Div(
        dcc.Slider(id='event-counter-slider', value=0, min=0, max=0), # the plots in the eventbrowser are linked to 'event-counter-slider'
        style={'display':'none'}
    ),
    dcc.Dropdown(id='filename', value=None, style={'display':'None'}),
    html.Div([
        html.Div([
            html.Div(
                html.Div([
                    html.Button(
                        [
                            ' < '
                        ],
                        id='btn-previous-station',
                        title='Previous station',
                        style={'height':'35px'}
                        # className='btn btn-primary',
                    ),
                    dcc.Dropdown(
                        id='station-id-dropdown',
                        options=station_entries,
                        clearable=False,
                        multi=False,
                        style={'flex':1,'min-width':'120px'},
                        value=None,
                        persistence=True,
                        persistence_type='memory'
                    ),
                    html.Button(
                        [
                            ' > '
                        ],
                        id='btn-next-station',
                        title='Next station',
                        style={'height':'35px'}
                        # className='btn btn-primary',
                    ),
                    ], style={'flex':1, 'display':'inherit'}
                )
            , className='custom-table-row'),
            html.Div([
                html.Div('Run:', className='custom-table-td'),
                html.Button(
                        [
                            ' < '
                        ],
                        id='btn-previous-run',
                        title='Previous run',
                        style={'height':'35px'}
                    ),
                html.Div(
                    dcc.Dropdown(
                        value='', options=[], searchable=True, clearable=False,
                        # persistence=True, persistence_type='memory',
                        id='event-info-run', style={'flex':1}),
                    id='event-info-run-container', style={'flex':1}),
                html.Button(
                    [
                        ' > '
                    ],
                    id='btn-next-run',
                    title='Next run',
                    style={'height':'35px'}
                ),
            ], className='custom-table-row'),
            html.Div([
                html.Div('Event:', className='custom-table-td'),
                html.Button(
                        [
                            ' < '
                        ],
                        id='btn-previous-event',
                        title='Previous event',
                        style={'height':'35px'}
                    ),
                dcc.Dropdown(
                    value=None, options=[], searchable=True, clearable=False,
                    # persistence=True, persistence_type='memory',
                    id='event-info-id', style={'flex':1}),
                html.Button(
                    [
                        ' > '
                    ],
                    id='btn-next-event',
                    title='Next event',
                    style={'height':'35px'}
                ),
            ], className='custom-table-row'),
            html.Div([
                html.Div('Time:', className='custom-table-td'),
                html.Div('', className='custom-table-td-last', id='event-info-time')
            ], className='custom-table-row')
        ], style={'flex': '1', 'min-width':280, 'max-width':400}, className='event-info-table', id='event-info-table'),
        dash.dash_table.DataTable(
            columns=[{"name":i, "id":i} for i in ['Trigger', 'Value']],
            style_header=dict(fontWeight='bold',textAlign='left'),
            style_table=dict(padding='0px 25px 0px 0px'),
            style_data_conditional=[
                {
                    'if':{'filter_query':'{Value} = "True"', 'column_id':'Value'},
                    'color':'green',
                    'fontWeight':'bold'
                }
            ],
            id='trigger-info-table')
    ], style={'display': 'flex'}),
    traces.layout
])

layout = event_viewer_layout # needed for pages support

# @callback(
#     Output('content', 'children'),
#     [Input('content-selector', 'value')]
# )
# def get_page_content(selection):
#     if selection == 'traces':
#         return [traces.layout]
#     return []


# @callback(
#     Output('station-id-dropdown', 'value'),
#     [Input('btn-previous-station', 'n_clicks'),
#      Input('btn-next-station', 'n_clicks'),
#      Input('url', 'hash')],
#     [State('station-id-dropdown', 'value')]
# )
# def change_station_from_button(previous, next, hash, current_station_value):
#     context = dash.callback_context

#     # update triggered by url
#     if context.triggered[0]['prop_id'] == 'url.hash':
#         logger.debug('Triggered by URL')
#         idx = np.array([hash.find('S'), hash.find('R')])
#         if np.any(idx < 0): # hash doesn't completely specify location
#             raise PreventUpdate
#         station_id = int(hash[idx[0]+1:idx[1]])
#         if station_id not in station_entries:
#             raise PreventUpdate
#         return station_id

#     n_stations = len(station_entries)
#     station_values = [i['value'] for i in station_entries]
#     if current_station_value is None:
#         station_value = station_values[0]
#         return station_value

#     station_value = current_station_value
#     try:
#         current_station_i = station_values.index(current_station_value)
#     except ValueError:
#         raise PreventUpdate
#     if context.triggered[0]['prop_id'] == 'btn-previous-station.n_clicks':
#         if current_station_i > 0:
#             station_value = station_values[current_station_i - 1]
#     elif context.triggered[0]['prop_id'] == 'btn-next-station.n_clicks':
#         if current_station_i < n_stations - 1:
#             station_value = station_values[current_station_i + 1]
#     return station_value

# @callback(
#     Output('event-info-run-container','children'),
#     [Input('station-id-dropdown', 'value'),
#      Input('btn-previous-run', 'n_clicks'),
#      Input('btn-next-run', 'n_clicks')],
#     [State('event-info-run', 'value')]
# )
# def persistent_run_selection(station_id, click_previous, click_next, current_run):
#     context = dash.callback_context
#     if station_id == None:
#         run_numbers = []
#         run_options = []
#     else:
#         run_numbers = run_table.get_table().query('station==@station_id').run.values
#         run_options = [{'label':i, 'value':i} for i in run_numbers]

#     try:
#         current_run_idx = list(run_numbers).index(current_run)
#     except ValueError:
#         current_run_idx = 0

#     if context.triggered[0]['prop_id'] == 'btn-previous-run.n_clicks':
#         if current_run_idx > 0:
#             current_run_idx -= 1
#     elif context.triggered[0]['prop_id'] == 'btn-next-run.n_clicks':
#         if current_run_idx < len(run_numbers) - 1:
#             current_run_idx += 1

#     station_dropdown = dcc.Dropdown(
#         value=run_options[current_run_idx]['value'], options=run_options,
#         searchable=True, clearable=False,
#         persistence=station_id, persistence_type='memory',
#         id='event-info-run', style={'flex':1}),

#     return station_dropdown

# @callback(
#     [Output('filename', 'value'),
#     Output('event-info-id', 'options'),
#     Output('event-counter-slider', 'max')],
#     [Input('station-id-dropdown', 'value'),
#     Input('event-info-run', 'value'),
#     Input('url', 'hash')],
#     [State('user_id', 'children')]
# )
# def update_event_info_id_options(station_id, run_number, hash, juser_id):
#     context = dash.callback_context
    
#     # update triggered by url
#     if context.triggered[0]['prop_id'] == 'url.hash':
#         logger.debug('Triggered by URL')
#         idx = np.array([hash.find('S'), hash.find('R'), hash.find('E')])
#         if np.any(idx < 0): # hash doesn't completely specify location
#             raise PreventUpdate
#         station_id = int(hash[idx[0]+1:idx[1]])
#         run_number = int(hash[idx[1]+1:idx[2]])
#         event_id = int(hash[idx[2]+1:])

#     try:
#         filename = filename_table.loc[(station_id, run_number), 'filenames_root']
#     except KeyError:
#         return None, [], 0
#     user_id = json.loads(juser_id)
#     logger.debug(f'Getting file handler for user {user_id} and filename {filename}')
#     nurio = browser_provider.get_file_handler(user_id, filename)
#     event_ids = nurio.get_event_ids()
#     event_ids = [i[1] for i in event_ids if i[0] == run_number]
#     return filename, [{'label':i, 'value':i} for i in event_ids], len(event_ids)-1

# @callback(
#     [Output('event-counter-slider', 'value'),
#      Output('event-info-id', 'value'),
#      Output('url', 'hash')
#      ],
#     [Input('btn-next-event', 'n_clicks_timestamp'),
#      Input('btn-previous-event', 'n_clicks_timestamp'),
#      Input('event-info-run', 'value'),
#      Input('event-info-id', 'value'),
#      Input('url', 'hash')
#      ],
#     [State('user_id', 'children'),
#      State('filename', 'value'),
#      State('station-id-dropdown', 'value')],
# )
# def set_event_number(next_evt_click_timestamp, prev_evt_click_timestamp, run_number, event_id, hash, juser_id, filename, station_id):
#     context = dash.callback_context
    
#     # update triggered by url
#     if context.triggered[0]['prop_id'] == 'url.hash':
#         logger.debug('Triggered by URL')
#         idx = np.array([hash.find('S'), hash.find('R'), hash.find('E')])
#         if np.any(idx < 0): # hash doesn't completely specify location
#             raise PreventUpdate
#         station_id = int(hash[idx[0]+1:idx[1]])
#         run_number = int(hash[idx[1]+1:idx[2]])
#         event_id = int(hash[idx[2]+1:])
#         filename = filename_table.loc[(station_id, run_number), 'filenames_root']
    
#     if (filename is None) or (run_number is None):
#         raise PreventUpdate
#     user_id = json.loads(juser_id)
#     number_of_events = browser_provider.get_file_handler(user_id, filename).get_n_events()
#     event_ids = browser_provider.get_file_handler(user_id, filename).get_event_ids()
#     # number_of_events = browser_provider.get_n_events()
#     # event_ids = browser_provider.get_event_ids()

#     mask = event_ids == (run_number, event_id)
#     mask = mask[:,0] * mask[:,1]
#     if not np.sum(mask):
#         return 0, event_ids[0][1],  f'#S{station_id}R{run_number}E{event_ids[0][1]}' # if not set, we initialize to the first event in run
#     else:
#         event_i = np.where(mask)[0][0]
#     if context.triggered[0]['prop_id'] == 'event-info-id.value':
#         pass
#     elif context.triggered[0]['prop_id'] == 'event-info-run.value': # set to first event in run - #TODO: add persistence?
#         event_i = 0
#     elif context.triggered[0]['prop_id'] == 'btn-previous-event.n_clicks_timestamp':
#         if event_i > 0:
#             event_i -= 1
#     elif context.triggered[0]['prop_id'] == 'btn-next-event.n_clicks_timestamp':
#         if event_i + 1 != number_of_events:
#             event_i += 1
#     logger.info(f"Loading event S{station_id}:R{run_number}:E{event_ids[event_i][1]} from {filename}...")

#     outputs = event_i, event_ids[event_i][1], f'#S{station_id}R{run_number}E{event_ids[event_i][1]}'

#     return outputs





@callback(
    Output('trigger-info-table', 'data'),
    [Input('filename', 'value'),
     Input('station-id-dropdown', 'value'),
     Input('event-counter-slider', 'value')],
    [State('user_id', 'children')]
)
def fill_trigger_info_table(filename, station_id, event_i, juser_id):
    if filename is None:
        raise PreventUpdate
    user_id = json.loads(juser_id)
    nurio = browser_provider.get_file_handler(user_id, filename)
    event = nurio.get_event_i(event_i)
    station = event.get_station(station_id)
    trigger_names = []
    trigger_bools = []
    for trigger_key in station.get_triggers():
        trigger = station.get_trigger(trigger_key)
        trigger_names.append(trigger.get_name())
        trigger_bools.append(str(trigger.has_triggered()))
    data_list = [
        {'Trigger':trigger_names[i],'Value':trigger_bools[i]}
        for i in range(len(trigger_names))]
    return data_list


# @callback(
#     Output('event-info-run', 'options'),
#     Input('station-id-dropdown', 'value'),
# )
# def update_event_info_run_options(station_id):
#     if station_id == None:
#         return []
#     run_numbers = run_table.get_table().query('station==@station_id').run.values
#     return [{'label':i, 'value':i} for i in run_numbers]


@callback(
    Output('event-info-time', 'children'),
    [Input('event-info-id', 'value'),
     Input('filename', 'value'),
     Input('station-id-dropdown', 'value')],
    [State('event-info-run', 'value'),
     State('user_id', 'children')])
def update_event_info_time(event_id, filename, station_id, run_number, juser_id):
    if (filename is None) or (station_id is None):
        return ""
    user_id = json.loads(juser_id)
    nurio = browser_provider.get_file_handler(user_id, filename)
    evt = nurio.get_event((run_number, event_id))
    if evt.get_station(station_id).get_station_time() is None:
        return ''
    return '{:%d. %b %Y, %H:%M:%S}'.format(evt.get_station(station_id).get_station_time().datetime)

@callback(
    [
        Output('filename', 'value'),
        Output('station-id-dropdown', 'value'),
        Output('event-info-run-container','children'),
        Output('event-info-id', 'value'),
        Output('event-info-id', 'options'),
        Output('event-counter-slider', 'value'),
        Output('event-counter-slider', 'max'),
        Output('url', 'hash'),
    ],
    [
        Input('btn-previous-station', 'n_clicks'),
        Input('btn-next-station', 'n_clicks'),
        Input('btn-previous-run', 'n_clicks'),
        Input('btn-next-run', 'n_clicks'),
        Input('btn-previous-event', 'n_clicks_timestamp'),
        Input('btn-next-event', 'n_clicks_timestamp'),
        Input('station-id-dropdown', 'value'),
        Input('event-info-run', 'value'),
        Input('event-info-id', 'value'),
        Input('url', 'hash'),
        Input('url', 'pathname'),
        Input('tab-selection', 'value'),
    ],
    [State('user_id', 'children')],
)
def update_everything(
        btn1, btn2, btn3, btn4, btn5, btn6,
        station_id, run_number, event_id, hash, url_path, tab_selection, juser_id
):
    user_id = json.loads(juser_id)
    context = dash.callback_context

    # update from URL or tab selection
    if context.triggered[0]['prop_id'] in ['url.hash', 'url.pathname', 'tab-selection.value']:
        logger.debug('Triggered by URL / tab-selection')
        idx = np.array([hash.find('S'), hash.find('R'), hash.find('E')])
        if np.any(idx < 0): # hash doesn't completely specify location
            raise PreventUpdate
        station_id = int(hash[idx[0]+1:idx[1]])
        run_number = int(hash[idx[1]+1:idx[2]])
        event_id = int(hash[idx[2]+1:])

    ### update station
    n_stations = len(station_entries)
    station_values = [i['value'] for i in station_entries]
    if context.triggered[0]['prop_id'] == 'station-id-dropdown.value':
        pass # station_id from dropdown

    if station_id is None:
        station_id = station_values[0] # default to first station?
    try:
        current_station_i = station_values.index(station_id)
    except ValueError:
        raise PreventUpdate
    if context.triggered[0]['prop_id'] == 'btn-previous-station.n_clicks':
        if current_station_i > 0:
            station_id = station_values[current_station_i - 1]
    elif context.triggered[0]['prop_id'] == 'btn-next-station.n_clicks':
        if current_station_i < n_stations - 1:
            station_id = station_values[current_station_i + 1]

    ### update run & run options
    run_numbers = run_table.get_table().query('station==@station_id').run.values.astype(int)
    run_options = [{'label':i, 'value':i} for i in run_numbers]

    try:
        current_run_idx = list(run_numbers).index(run_number)
    except ValueError:
        current_run_idx = 0

    if context.triggered[0]['prop_id'] == 'btn-previous-run.n_clicks':
        if current_run_idx > 0:
            current_run_idx -= 1
    elif context.triggered[0]['prop_id'] == 'btn-next-run.n_clicks':
        if current_run_idx < len(run_numbers) - 1:
            current_run_idx += 1
    run_number = run_options[current_run_idx]['value']
    run_dropdown = dcc.Dropdown(
        value=run_options[current_run_idx]['value'], options=run_options,
        searchable=True, clearable=False,
        persistence=station_id, persistence_type='memory',
        id='event-info-run', style={'flex':1}),

    ### update event & event options
    filename = filename_table.loc[(station_id, run_number), 'filenames_root']
    number_of_events = browser_provider.get_file_handler(user_id, filename).get_n_events()
    event_ids = browser_provider.get_file_handler(user_id, filename).get_event_ids()
    event_id_options = [{'label':i[1], 'value':i[1]} for i in event_ids]

    mask = event_ids == (run_number, event_id)
    mask = mask[:,0] * mask[:,1]
    if not np.sum(mask):
        event_i = 0 # if not set, we initialize to the first event in run
    else:
        event_i = np.where(mask)[0][0]
    if context.triggered[0]['prop_id'] == 'event-info-id.value':
        pass
    elif context.triggered[0]['prop_id'] == 'event-info-run.value': # set to first event in run - #TODO: add persistence?
        event_i = 0
    elif context.triggered[0]['prop_id'] == 'btn-previous-event.n_clicks_timestamp':
        if event_i > 0:
            event_i -= 1
    elif context.triggered[0]['prop_id'] == 'btn-next-event.n_clicks_timestamp':
        if event_i + 1 != number_of_events:
            event_i += 1
    logger.info(f"Loading event S{station_id}:R{run_number}:E{event_ids[event_i][1]} from {filename}...")
    event_id = event_ids[event_i][1]
    hash = f'#S{station_id}R{run_number}E{event_ids[event_i][1]}'

    outputs = [
        filename, station_id, run_dropdown, event_id, event_id_options, event_i, len(event_ids)-1, hash
    ]
    # logger.debug(f"outputs:{outputs}")
    return outputs