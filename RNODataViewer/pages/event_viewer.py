from __future__ import absolute_import, division, print_function  # , unicode_literals
from dash.dependencies import Input, Output, State
from dash import dcc, html, callback
import dash
import json
from dash.exceptions import PreventUpdate
import numpy as np

from RNODataViewer.apps import traces

from RNODataViewer.base.data_provider_root import data_provider_event
import logging
from RNODataViewer.file_list.run_stats import RUN_TABLE, DATA_DIR #, RunStats

logger=logging.getLogger('RNODataViewer')

dash.register_page(__name__, path='/eventViewer')

data_folder = DATA_DIR

browser_provider = data_provider_event

event_viewer_layout = html.Div([
    traces.layout
])

layout = event_viewer_layout # needed for pages support



@callback(
    Output('eventviewer-run-info-table', 'data'),
    [Input('station-id-dropdown', 'value'),
     Input('event-info-run', 'value'),
     ],
    [State('user_id', 'children')]
)
def fill_run_info_table(station_id, run_number, juser_id):
    if (station_id is None) or (run_number is None):
        raise PreventUpdate
    table = RUN_TABLE.get_table().query('station==@station_id&run==@run_number').iloc[0]
    keys = ['time_start', 'time_end', 'n_events_recorded',
       'n_events_transferred', 'trigger_rf0_enabled', 'trigger_rf1_enabled',
       'trigger_ext_enabled', 'trigger_pps_enabled', 'trigger_soft_enabled',
       'daq_config_comment', 'firmware_version','run_type']
    data_dict = {}
    data_dict['start time'] = table.loc['time_start'].strftime('%Y-%m-%d %H:%M:%S')
    data_dict['end time'] = table.loc['time_end'].strftime('%Y-%m-%d %H:%M:%S')
    # data_dict['time'] = '{} - {}'.format(*[table.loc[key].strftime('%Y-%m-%d %H:%M:%S') for key in ['time_start', 'time_end']])
    data_dict['n_events (transferred / total)'] = '{} / {}'.format(*table.loc[['n_events_transferred', 'n_events_recorded']])
    data_dict['active triggers'] = ', '.join([k for k in ['rf0', 'rf1', 'ext', 'pps', 'soft'] if table.loc[f'trigger_{k}_enabled']])
    for key in ['daq_config_comment', 'firmware_version', 'run_type']:
        data_dict[key.replace('_', ' ')] = table.loc[key]

    data_list = [
        {'Run Info':key, '':value}
        for key,value in data_dict.items()
    ]
    return data_list

## callback to update event time and trigger type
@callback(
    [Output('event-info-time', 'children'),
     Output('event-info-trigger', 'children')],
    [Input('event-info-id', 'value'),
     Input('filename', 'value'),
     Input('station-id-dropdown', 'value')],
    [State('event-info-run', 'value'),
     State('user_id', 'children')])
def update_event_info_time(event_id, filename, station_id, run_number, juser_id):
    if (filename is None) or (station_id is None):
        return "", ""
    user_id = json.loads(juser_id)
    nurio = browser_provider.get_file_handler(user_id, filename)
    evt = nurio.get_event((run_number, event_id))
    station = evt.get_station(station_id)
    if station.get_station_time() is None:
        return '', ''
    station_time = '{:%d. %b %Y, %H:%M:%S}'.format(evt.get_station(station_id).get_station_time().datetime)
    trigger_type = ', '.join([trigger for trigger in station.get_triggers()])

    return station_time, trigger_type

## complicated callback that updates the selected event
## as well as all possible inputs that affect the selected event
## in order to keep them synchronised and consistent
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
        Input('btn-previous-event', 'n_clicks'),
        Input('btn-next-event', 'n_clicks'),
        Input('station-id-dropdown', 'value'),
        Input('event-info-run', 'value'),
        Input('event-info-id', 'value'),
        Input('url', 'hash'),
        Input('url', 'pathname'),
        Input('tab-selection', 'value'),
    ],
    [State('user_id', 'children')],
    prevent_initial_call=True
)
def update_everything(
        btn1, btn2, btn3, btn4, btn5, btn6,
        station_id, run_number, event_id, hash, url_path, tab_selection, juser_id
):
    user_id = json.loads(juser_id)
    if tab_selection != '/eventViewer':
        raise PreventUpdate
    context = dash.callback_context
    logger.info(f"Updating event viewer from {context.triggered[0]['prop_id']}")
    # if 'btn' in context.triggered[0]['prop_id']: # triggered by a button:
    #     if np.all(np.array([btn1,btn2,btn3,btn4,btn5,btn6]) == None):
    #         raise PreventUpdate # we just loaded the tab, so we shouldn't trigger on the buttons
    # logger.info(f'Buttons were clicked {np.array([btn1,btn2,btn3,btn4,btn5,btn6])} times')
    # update from URL or tab selection
    if context.triggered[0]['prop_id'] in ['url.hash', 'url.pathname', 'tab-selection.value']:
        logger.debug('Triggered by URL / tab-selection')
        idx = np.array([hash.find('S'), hash.find('R'), hash.find('E')])
        if np.any(idx < 0): # hash doesn't completely specify location
            raise PreventUpdate
        station_id = int(hash[idx[0]+1:idx[1]])
        run_number = int(hash[idx[1]+1:idx[2]])
        event_id = int(hash[idx[2]+1:])
        logger.debug(f'Requested S{station_id}R{run_number}E{event_id} from URL...')

    ### update station
    station_entries = RUN_TABLE.get_station_entries()
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
    table_for_station = RUN_TABLE.get_table().query('station==@station_id').sort_values(
        by='mjd_last_event', ascending=False)
    run_numbers = table_for_station.run.values.astype(int)
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
    filename = table_for_station.query('run==@run_number').iloc[0].loc['filenames_root']
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
    elif context.triggered[0]['prop_id'] == 'btn-previous-event.n_clicks':
        if event_i > 0:
            event_i -= 1
    elif context.triggered[0]['prop_id'] == 'btn-next-event.n_clicks':
        if event_i + 1 != number_of_events:
            event_i += 1
    logger.info(f"Loading event S{station_id}:R{run_number}:E{event_ids[event_i][1]} from {filename}...")
    event_id = event_ids[event_i][1]
    hash = f'#S{station_id}R{run_number}E{event_ids[event_i][1]}'

    outputs = [
        filename, station_id, run_dropdown, event_id, event_id_options, event_i, len(event_ids)-1, hash
    ]
    return outputs

