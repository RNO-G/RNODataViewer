from __future__ import absolute_import, division, print_function  # , unicode_literals
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
import dash
import json
import numpy as np
import uuid
import glob
#from NuRadioReco.eventbrowser.app import app
from RNODataViewer.base.app import app
from RNODataViewer.apps import traces
import os
import argparse
import NuRadioReco.eventbrowser.dataprovider
import NuRadioReco.eventbrowser.dataprovider_root
import logging
import webbrowser
from NuRadioReco.modules.base import module
from file_list.run_stats import RUN_TABLE, DATA_DIR #, RunStats
logger = module.setup_logger(level=logging.INFO)

#data_folder = DATA_DIR
#if os.path.isfile(data_folder):
#    starting_filename = data_folder
#else:
#    starting_filename = None

data_folder = DATA_DIR

browser_provider = NuRadioReco.eventbrowser.dataprovider.DataProvider()
browser_provider.set_filetype(True)


event_viewer_layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='event-click-coordinator', children=json.dumps(None), style={'display': 'none'}),
    html.Div(id='user_id', style={'display': 'none'},
             children=json.dumps(None)),
    html.Div(id='event-ids', style={'display': 'none'},
             children=json.dumps([])),
    html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Div('File location:', className='input-group-text')
                    ], className='input-group-addon', style={'width':'200px'}),
                dcc.Input(id='datafolder', placeholder='filename', type='text', value=data_folder,
                          className='form-control')
            ], className='input-group', style={"width":"99%"}),
            html.Div([
                dcc.Dropdown(id='filename',
                             options=[],
                             multi=False,
                             #value=starting_filename,
                             className='custom-dropdown',style={'width':'100%'}),
                html.Div([
                    html.Button('open file', id='btn-open-file', className='btn btn-default')
                ], className='input-group-btn'),
                ], className='input-group', style={"width":"75%"}),
            html.Div(
                [
                    html.Div(
                        [
                            html.Button(
                                [
                                    html.Div(className='icon-arrow-left')
                                ],
                                id='btn-previous-event',
                                className='btn btn-primary',
                                n_clicks_timestamp=0
                            ),
                            html.Button(
                                id='event-number-display',
                                children='''''',
                                className='btn btn-primary'
                            ),
                            html.Button(
                                [
                                    html.Div(className='icon-arrow-right')
                                ],
                                id='btn-next-event',
                                className='btn btn-primary',
                                n_clicks_timestamp=0
                            )
                        ],
                        className='btn-group',
                        style={'margin': '10px'}
                    ),
                    html.Div(
                        [
                            dcc.Slider(
                                id='event-counter-slider',
                                step=1,
                                value=0,
                                marks={}
                            ),
                        ],
                        style={
                            'padding': '10px 30px 20px',
                            'overflow': 'hidden',
                            'flex': '1'
                        }
                    ),
                    html.Div([
                        dcc.Dropdown(
                            id='station-id-dropdown',
                            options=[],
                            multi=False
                        )
                    ],
                        style={'flex': 'none', 'padding': '10px', 'min-width': '200px'})
                ],
                style={
                    'display': 'flex'
                }
            )
        ], style={'flex': '7'}),
        html.Div([
            html.Div([
                html.Div('Run:', className='custom-table-td'),
                dcc.Dropdown(
                    value='', options=[], searchable=True, clearable=False,
                    id='event-info-run', style={'flex':1})
            ], className='custom-table-row'),
            html.Div([
                html.Div('Event:', className='custom-table-td'),
                dcc.Dropdown(
                    value='', options=[], searchable=True, clearable=False,
                    id='event-info-id', style={'flex':1})
            ], className='custom-table-row'),
            html.Div([
                html.Div('Time:', className='custom-table-td'),
                html.Div('', className='custom-table-td-last', id='event-info-time')
            ], className='custom-table-row')
        ], style={'flex': '1'}, className='event-info-table')
    ], style={'display': 'flex'}),
    traces.layout #'', id='content')
])


@app.callback(
    Output('content', 'children'),
    [Input('content-selector', 'value')]
)
def get_page_content(selection):
    if selection == 'traces':
        return [traces.layout]
    return []


# event selector - couples slider, next/previous button and dropdown input
@app.callback(
    [Output('event-counter-slider', 'value'),
     Output('event-info-run', 'value'),
     Output('event-info-id', 'value')],
    [Input('btn-next-event', 'n_clicks_timestamp'),
     Input('btn-previous-event', 'n_clicks_timestamp'),
     Input('event-info-id', 'value'),
     Input('event-click-coordinator', 'children'),
     Input('filename', 'value'),
     Input('event-counter-slider', 'value')],
    [State('event-info-run', 'value'),
     State('user_id', 'children')]
)
def set_event_number(next_evt_click_timestamp, prev_evt_click_timestamp, event_id, j_plot_click_info, filename, 
                     i_event, run_number, juser_id):
    context = dash.callback_context
    if filename is None:
        return 0, None, None
    user_id = json.loads(juser_id)
    number_of_events = browser_provider.get_arianna_io(user_id, filename).get_n_events()
    event_ids = browser_provider.get_arianna_io(user_id, filename).get_event_ids()
    if context.triggered[0]['prop_id'] == 'filename.value':
        return 0, event_ids[0][0], event_ids[0][1]
    if context.triggered[0]['prop_id'] == 'event-click-coordinator.children':
        if context.triggered[0]['value'] is None:
            return 0, event_ids[0][0], event_ids[0][1]
        event_i = json.loads(context.triggered[0]['value'])['event_i']
        return event_i, event_ids[event_i][0], event_ids[event_i][1]
    if context.triggered[0]['prop_id'] == 'event-counter-slider.value':
        return i_event, event_ids[i_event][0], event_ids[i_event][1]
    else:
        if context.triggered[0]['prop_id'] == 'event-info-id.value':
            mask = event_ids == (run_number, event_id)
            event_i = np.where(mask[:,0] * mask[:,1])[0][0]
            return event_i, run_number, event_id
        if context.triggered[0]['prop_id'] != 'btn-next-event.n_clicks_timestamp' and context.triggered[0]['prop_id'] != 'btn-previous-event.n_clicks_timestamp':
            return 0, event_ids[0][0], event_ids[0][1]
        if context.triggered[0]['prop_id'] == 'btn-previous-event.n_clicks_timestamp':
            if i_event == 0:
                event_i = 0
            else:
                event_i = i_event - 1
        if context.triggered[0]['prop_id'] == 'btn-next-event.n_clicks_timestamp':
            # user_id = json.loads(juser_id)

            # number_of_events = provider.get_arianna_io(user_id, filename).get_n_events()
            if number_of_events == i_event + 1:
                event_i =  number_of_events - 1
            else:
                event_i = i_event + 1
        return event_i, event_ids[event_i][0], event_ids[event_i][1]


@app.callback(
    Output('event-number-display', 'children'),
    [Input('filename', 'value'),
     Input('event-counter-slider', 'value')]
)
def set_event_number_display(filename, event_number):
    if filename is None:
        return 'No file selected'
    return 'Event {}'.format(event_number)


@app.callback(
    Output('event-counter-slider', 'max'),
    [Input('filename', 'value')],
    [State('user_id', 'children')])
def update_slider_options(filename, juser_id):
    if filename is None:
        return 0
    user_id = json.loads(juser_id)
    ariio = browser_provider.get_arianna_io(user_id, filename)
    number_of_events = ariio.get_n_events()
    return number_of_events - 1


@app.callback(
    Output('event-counter-slider', 'marks'),
    [Input('filename', 'value')],
    [State('user_id', 'children')]
)
def update_slider_marks(filename, juser_id):
    if filename is None:
        return {}
    user_id = json.loads(juser_id)
    ariio = browser_provider.get_arianna_io(user_id, filename)
    n_events = ariio.get_n_events()
    step_size = int(np.power(10., int(np.log10(n_events))))
    marks = {}
    for i in range(0, n_events, step_size):
        marks[i] = str(i)
    if n_events % step_size != 0:
        marks[n_events] = str(n_events)
    return marks


@app.callback(Output('user_id', 'children'),
              [Input('url', 'pathname')],
              [State('user_id', 'children')])
def set_uuid(pathname, juser_id):
    user_id = json.loads(juser_id)
    if user_id is None:
        user_id = uuid.uuid4().hex
    return json.dumps(user_id)


@app.callback(Output('filename', 'options'), [Input('datafolder', 'value')])
def set_filename_dropdown(folder):
    #if parsed_args.rnog_file:
        #rs = RunStats(folder)
        run_table = RUN_TABLE #rs.get_table()
        filtered_names = list(run_table.filenames_root)
        rrr =  [{'label': "Station {}, Run {}".format(row.station, row.run), 'value': row.filenames_root} for index, row in run_table.iterrows()]
        return rrr
    #return [{'label': ll.split('/')[-1], 'value': ll} for ll in sorted(glob.glob(os.path.join(folder, '*.root*')))]
    #else:
    #    return [{'label': ll.split('/')[-1], 'value': ll} for ll in sorted(glob.glob(os.path.join(folder, '*.nur*')))]


@app.callback(
    Output('station-id-dropdown', 'options'),
    [Input('filename', 'value'),
     Input('event-counter-slider', 'value')],
    [State('user_id', 'children')])
def get_station_dropdown_options(filename, i_event, juser_id):
    if filename is None:
        return []
    user_id = json.loads(juser_id)
    ariio = browser_provider.get_arianna_io(user_id, filename)
    event = ariio.get_event_i(i_event)
    dropdown_options = []
    for station in event.get_stations():
        dropdown_options.append({
            'label': 'Station {}'.format(station.get_id()),
            'value': station.get_id()
        })
    return dropdown_options


@app.callback(
    Output('station-id-dropdown', 'value'),
    [Input('filename', 'value'),
     Input('event-counter-slider', 'value')],
    [State('user_id', 'children')])
def set_to_first_station_in_event(filename, event_i, juser_id):
    if filename is None:
        return None
    user_id = json.loads(juser_id)
    ariio = browser_provider.get_arianna_io(user_id, filename)
    event = ariio.get_event_i(event_i)
    for station in event.get_stations():
        return station.get_id()


# update event ids list from plot selection
@app.callback(Output('event-ids', 'children'),
              [Input('cr-skyplot', 'selectedData'),
               Input('cr-xcorrelation', 'selectedData'),
               Input('cr-xcorrelation-amplitude', 'selectedData'),
               Input('skyplot-xcorr', 'selectedData'),
               Input('cr-polarization-zenith', 'selectedData')],
              [State('event-ids', 'children')])
def set_event_selection(selectedData1, selectedData2, selectedData3, selectedData4, selectedData5, jcurrent_selection):
    current_selection = json.loads(jcurrent_selection)
    tcurrent_selection = []
    for i, selection in enumerate([selectedData1, selectedData2, selectedData3, selectedData4,
                                   selectedData5]):  # check which selection has fired the callback
        if selection is not None:
            event_ids = []
            for x in selection['points']:
                t = x['customdata']
                if t not in event_ids:
                    event_ids.append(t)
            if not np.array_equal(np.array(event_ids), current_selection):  # this selection has fired the callback
                tcurrent_selection = event_ids
    return json.dumps(tcurrent_selection)


def add_click_info(json_object, event_number_array, times_array):
    loaded_object = json.loads(json_object)
    if loaded_object is not None:
        event_number_array.append(loaded_object['event_i'])
        times_array.append(loaded_object['time'])


# finds out which one of the plots was clicked last (i.e. which one triggered the event update)
@app.callback(
    Output('event-click-coordinator', 'children'),
    [Input('cr-polarization-zenith', 'clickData'),
     Input('cr-skyplot', 'clickData'),
     Input('cr-xcorrelation', 'clickData'),
     Input('cr-xcorrelation-amplitude', 'clickData')])
def coordinate_event_click(cr_polarization_zenith_click, cr_skyplot_click, cr_xcorrelation_click,
                           cr_xcorrelation_amplitude_click):
    context = dash.callback_context
    if context.triggered[0]['value'] is None:
        return None
    return json.dumps({
        'event_i': context.triggered[0]['value']['points'][0]['customdata'],
    })


@app.callback(
    Output('event-info-run', 'options'),
    Input('filename', 'value'),
    State('user_id', 'children')
)
def update_event_info_run_options(filename, juser_id):
    if filename == None:
        return []
    user_id = json.loads(juser_id)
    ariio = browser_provider.get_arianna_io(user_id, filename)
    run_numbers = np.unique([i[0] for i in ariio.get_event_ids()])
    return [{'label':i, 'value':i} for i in run_numbers]

@app.callback(
    Output('event-info-id', 'options'),
    Input('event-info-run', 'value'),
    [State('filename', 'value'),
     State('user_id', 'children')]
)
def update_event_info_id_options(run_number, filename, juser_id):
    if filename == None:
        return []
    user_id = json.loads(juser_id)
    ariio = browser_provider.get_arianna_io(user_id, filename)
    event_ids = [i[1] for i in ariio.get_event_ids() if i[0] == run_number]
    return [{'label':i, 'value':i} for i in event_ids]



@app.callback(
    Output('event-info-time', 'children'),
    [Input('event-counter-slider', 'value'),
     Input('filename', 'value'),
     Input('station-id-dropdown', 'value')],
    [State('user_id', 'children')])
def update_event_info_time(event_i, filename, station_id, juser_id):
    if filename is None or station_id is None:
        return ""
    user_id = json.loads(juser_id)
    ariio = browser_provider.get_arianna_io(user_id, filename)
    evt = ariio.get_event_i(event_i)
    if evt.get_station(station_id).get_station_time() is None:
        return ''
    return '{:%d. %b %Y, %H:%M:%S}'.format(evt.get_station(station_id).get_station_time().datetime)

