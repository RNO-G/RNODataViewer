#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import logging
logging.basicConfig(format="%(levelname)s:%(asctime)s:%(name)s:%(message)s", datefmt="%H:%M:%S")
import dash
from dash.dependencies import Input, Output, State
from dash import html, dcc, callback, callback_context
from dash.exceptions import PreventUpdate
import webbrowser
import subprocess
import json
import uuid
from RNODataViewer.base.app import app
# app.config.suppress_callback_exceptions = True

import RNODataViewer.base.data_provider_root
import RNODataViewer.base.data_provider_nur
from RNODataViewer.file_list.run_stats import station_entries #, RunStats
# from tabs import rnog_overview
# from tabs import run_viewer
# from tabs import event_viewer

from file_list.run_stats import run_table
import astropy.time
import time
import pandas as pd
import sys, os

# we add a Dash handler to be able to display debug output on the online monitor
class DashLoggerHandler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.setFormatter(logging.Formatter(fmt="%(asctime)s:%(levelname)s:%(name)s:%(message)s", datefmt="%H:%M:%S"))
        self.queue = []
        self._maxLength = 6400

    def emit(self, record):
        msg = self.format(record)
        self.queue.append(msg)
        if len(self.queue) > self._maxLength:
            self.queue = self.queue[-self._maxLength:]


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
if not any([isinstance(handler, DashLoggerHandler) for handler in logger.handlers]):
    dashLoggerHandler = DashLoggerHandler()
    logger.addHandler(dashLoggerHandler)

argparser = argparse.ArgumentParser(description="View RNO Data Set")
argparser.add_argument('--open-window', const=True, default=False, action='store_const',
                         help="Open the event display in a new browser tab on startup")
argparser.add_argument('--port', default=8080, help="Specify the port the event display will run on")
argparser.add_argument('--reverse-proxy-path', default=None, help="If running behind a reverse proxy (e.g. https://example.org/monitoring is proxied to 127.0.0.1:$PORT from $REAL_HTTP_SERVER, you need to specify the path here so that the internal links work. In this case you would use /monitoring (don't include trailing /) ")
argparser.add_argument('--waitress', const=True,  default=False, action='store_const', help="Use waitress instead of development server")
# argparser.add_argument('--skip-file-check', const=True, default=False, action='store_const', help='Skip check to see which files are available')
#argparser.add_argument('--rno_data_dir', type=str, default=None, help="if set, use the passed <file_location> as top level directory where data (i.e. the stationXX directories) sit, rather than using 'RNO_DATA_DIR' environmental variable")
parsed_args = argparser.parse_args()
file_prefix = '.'

if parsed_args.reverse_proxy_path is not None:
    app.config.update({
    # as the proxy server will remove the prefix
    'routes_pathname_prefix': '/',

    # the front-end will prefix this string to the requests
    # that are made to the proxy server
    'requests_pathname_prefix': parsed_args.reverse_proxy_path + "/"
    })

    file_prefix = parsed_args.reverse_proxy_path


logger.info("Starting the monitoring application")

# import the run table (which is a pandas table holding available runs / paths / start/stop times etc)
filenames_root = run_table.get_table().filenames_root.values
filenames_nur = []

# RNODataViewer.base.data_provider_root.RNODataProviderRoot().set_filenames(filenames_root)
RNODataViewer.base.data_provider_nur.RNODataProvider().set_filenames(filenames_nur)


trigger_hover_info = (
    "Which trigger fired for this event. Options are\n"
    "LT: the low-threshold trigger on the FLOWER board (deep trigger)\n"
    "RADIANT0: radiant trigger 0 (shallow trigger, upward-facing LPDAs)\n"
    "RADIANT1: radiant trigger 1 (shallow trigger, downward-facing LPDAs)\n"
    "RADIANTX: both radiant triggers\n"
    "FORCE: the periodic (usually 0.1 Hz) 'forced' trigger\n"
    "UNKNOWN: no trigger flag present"
)

app.title = "RNO-G Data Monitor"

app.layout = html.Div([
    # header line with logo and title
    html.Div([
        html.Img(src=file_prefix+'/assets/rnog_logo_monogram_BlackTransparant.png', style={"float": "left", "width": "100px"}),
        html.H1('RNO-G Data Monitor'),
        ]),
    # three tabs, using this method, fresh pages get loaded after switching tabs
    dcc.Tabs(
            [
                dcc.Tab(label= 'Overview', value= '/', id='overview_tab_button'),
                dcc.Tab(label= 'Run Browser', value= '/runViewer', id='runbrowser_tab_button'),
                dcc.Tab(label= 'Event Browser', value= '/eventViewer'),
                # dcc.Tab(label='?!', value='debug_menu', style={'maxwidth':'20px'}),
            ],
            value='overview_tab', # start at general overview page by default
            id='tab-selection'
        ),
       html.Div([
            html.Div(id='event-click-coordinator', children=json.dumps(None), style={'display': 'none'}),
            html.Div(id='event-ids', style={'display': 'none'},
                children=json.dumps([])),
            html.Div(
                dcc.Slider(id='event-counter-slider', value=0, min=0, max=0), # the plots in the eventbrowser are linked to 'event-counter-slider'
                style={'display':'none'}
            ),
            dcc.Dropdown(id='filename', value=None, style={'display':'None'}),
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
                            id='btn-next-run',
                            title='Previous run',
                            style={'height':'35px'}
                        ),
                    html.Div(
                        dcc.Dropdown(
                            value=None, options=[], searchable=True, clearable=False,
                            # persistence=True, persistence_type='memory',
                            id='event-info-run', style={'flex':1}),
                        id='event-info-run-container', style={'flex':1}),
                    html.Button(
                        [
                            ' > '
                        ],
                        id='btn-previous-run',
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
                    html.Div('', className='custom-table-td-last', id='event-info-time',style={'height':'35px'})
                ], className='custom-table-row'),
                html.Div([
                    html.Div('Trigger:', className='custom-table-td', title=trigger_hover_info),
                    html.Div('', className='custom-table-td-last', id='event-info-trigger', style={'fontWeight':'bold', 'height':'35px'}, title=trigger_hover_info)
                ], className='custom-table-row')
            ], style={'flex': '1', 'min-width':280, 'max-width':400}, className='event-info-table', id='event-info-table'),
            dash.dash_table.DataTable(
                columns=[{"name":i, "id":i} for i in ['Run Info', '']],
                style_header=dict(fontWeight='bold',textAlign='left'),
                style_table=dict(padding='0px 25px 0px 0px'),
                style_cell=dict(textAlign='left'),
                style_data_conditional=[
                    {
                        'if':{'filter_query':'{Value} = "True"', 'column_id':'Value'},
                        'color':'green',
                        'fontWeight':'bold'
                    }
                ],
                id='eventviewer-run-info-table'),
    ], style={'display': 'none'}, id='eventViewer-inputs'),
    # html.Div(id='active-monitoring-tab'),
    # ### use hidden links to make the tab buttons work with pages - hacky?
    # dcc.Link(id='link-home', href='/', style={'display':'none'}),
    # dcc.Link(id='link-run', href='/runViewer', style={'display':'none'}),
    # dcc.Link(id='link-event', href='/eventViewer', style={'display':'none'}),
    dash.page_container,
    dcc.Location(id='url', refresh='callback-nav'),
    html.Div(id='user_id', style={'display': 'none'}, children=json.dumps(None)), # is this needed to allow multiple users/instances?
    dcc.Interval(id='self-updater', interval=300000), # to update the run table
    dcc.Interval(id='debug-log-updater', interval=3600000), # not used by default
    html.Div([
        html.Div(
            id='version-info',
            children=[''],
            # style={'float':'right', 'font-size':'smaller','margin-top':'-5px', 'margin-right':'5px'}
        ),
        # html.Br(),
        html.Button('Debug', id='show-debug-output',
        # style={'float':'right'}
        ),
    ], style={'float':'right', 'font-size':'smaller', 'margin-right':'5px'}
    ),
    html.Div(id='debug-output',
        children=[
            html.Iframe(id='logger-output', srcDoc='',
            style={'width':'100%', 'height':350}),
            dcc.Input(id='debug-input', debounce=True),
            html.Div(id='mem-usage', children='')
            ],
        style={'display':'none', 'margin-left':'5px','margin-right':'5px'})
    # dcc.Tooltip("This is the overview tab", targ)
    # TODO three tabs, the method below should avoid reloading tabs when switching, but callback ids need to be unique across all tabs
    #dcc.Tabs([
    #    dcc.Tab(label= 'Overview', children=index_app_layout),
    #    dcc.Tab(label= 'Run Browser', children=run_viewer.run_viewer_layout),
    #    dcc.Tab(label= 'Event Browser', children=event_viewer.event_viewer_layout)
    #])
])

@callback(Output('user_id', 'children'),
              [Input('url', 'id')], # this should never trigger, we just want to do this whenever a new connection is opened (?)
              [State('user_id', 'children')])
def set_uuid(pathname, juser_id):
    user_id = json.loads(juser_id)
    if user_id is None:
        logger.debug("Generating new unique user id...")
        user_id = uuid.uuid4().hex
    return json.dumps(user_id)


@callback(
        [Output('url', 'pathname'),
         Output('tab-selection', 'value'), Output('eventViewer-inputs', 'style')],
        [Input('tab-selection', 'value'), Input('url', 'pathname')],
        prevent_initial_call=True
)
def tab_selection(tab, pathname):
    triggering_component = callback_context.triggered[0]['prop_id'].split('.')[0]
    logger.debug(f'current tab: {tab} / current pathname: {pathname} / trigger: {triggering_component}')

    if triggering_component == 'url':
        page = pathname # set from url
    else:
        page = tab

    if page == '/eventViewer':
        displaystyle = {'display':'flex'}
    else:
        displaystyle = {'display':'none'}

    return page, page, displaystyle


@callback(Output('version-info', 'children'),
              [Input('self-updater', 'n_intervals')])
def update_version_info(n_intervals):
    # get current versions:
    dataviewer_version = subprocess.check_output(['git', '-C', os.path.dirname(__file__), 'rev-parse', '--short', 'HEAD']).decode()
    # # check for updated version on remote
    # subprocess.call(['git', '-C', os.path.dirname(__file__), 'fetch', 'origin', '+refs/heads/feature/monitoring:refs/remotes/origin/feature/monitoring']) #TODO - change this to 'master'
    # dataviewer_current_version = subprocess.check_output(['git', '-C', os.path.dirname(__file__), 'rev-parse', '--short', 'origin/feature/monitoring']).decode()

    from NuRadioMC import __path__ as nuradiomc_path
    nuradiomc_version = subprocess.check_output(['git', '-C', os.path.dirname(nuradiomc_path[0]), 'rev-parse', '--short', 'HEAD']).decode()
    subprocess.call(['git', '-C', nuradiomc_path[0], 'fetch', 'origin', '+refs/heads/rnog_eventbrowser:refs/remotes/origin/rnog_eventbrowser'])
    nuradiomc_current_version = subprocess.check_output(['git', '-C', os.path.dirname(nuradiomc_path[0]), 'rev-parse', '--short', 'origin/rnog_eventbrowser']).decode()
    run_table_last_update = run_table.last_modification_date
    time_since_update = astropy.time.Time(time.time(), format='unix') - run_table_last_update
    if time_since_update.sec > 600:
        run_table.update_run_table()
        run_table_last_update = run_table.last_modification_date

    # if dataviewer_version == dataviewer_current_version:
    #     dataviewer_string = 'Up to date'
    # else:
    #     dataviewer_string = f'latest: {dataviewer_current_version}'
    if nuradiomc_version == nuradiomc_current_version:
        nuradiomc_string = 'Up to date'
    else:
        nuradiomc_string = f'latest: {nuradiomc_current_version}'

    version_info_table = [
        f'Deployed: {DEPLOYMENT_DATE} (UTC) (version {dataviewer_version})',
        html.Br(),
        f'NuRadioMC version: {nuradiomc_version} ({nuradiomc_string})',
        html.Br(),
        f'Last run table update: {run_table_last_update.iso[:16]} (UTC)'
    ]
    return version_info_table

@callback(
    [Output('show-debug-output', 'children'),
     Output('debug-output', 'style'),
     Output('debug-log-updater', 'interval')],
    [Input('show-debug-output', 'n_clicks')],
    [State('debug-output', 'style'),
     State('show-debug-output', 'children')],
    prevent_initial_call=True)
def show_debug_output(n_clicks, debug_style, current_value):
    if current_value == 'Debug':
        debug_style['display'] = 'inherit'
        button_label = 'Close'
        log_update_interval = 5000
    elif current_value == 'Close':
        debug_style['display'] = 'none'
        button_label = 'Debug'
        log_update_interval = 3600000

    return [button_label, debug_style, log_update_interval]

@callback(
        [Output('logger-output', 'srcDoc'),
         Output('mem-usage', 'children')],
        [Input('debug-log-updater', 'n_intervals'),
         Input('show-debug-output', 'children')]
)
def update_debug_logger_output(n_updates, current_value):
    if current_value == 'Debug':
        raise PreventUpdate
    else:
        dashlogger = None
        for handler in logger.handlers:
            if isinstance(handler, DashLoggerHandler):
                dashlogger = handler
        if dashlogger is None: # this should never happen?
            raise PreventUpdate

        log_output = ('\n'.join(dashlogger.queue[::-1])).replace('\n', '<BR>')
        try: # try to also show memory usage - probably only works on Linux platforms
            with open('/proc/meminfo') as f:
                meminfo = f.readlines()
            meminfo = ' / '.join([k.strip() for k in meminfo if 'MemAvailable' in k] + [k.strip() for k in meminfo if 'MemTotal' in k])
        except IOError:
            meminfo = ''
        # mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e3 # should convert KB to MB on Linux and probably is wrong on iOS
        return log_output, meminfo #f' (MEM: {mem_usage:.0f} MB)'


if __name__ == '__main__':
    global DEPLOYMENT_DATE # for debugging
    DEPLOYMENT_DATE = time.strftime('%Y-%m-%d %H:%M', time.gmtime(time.time()))
    dash_version = [int(i) for i in dash.__version__.split('.')]
    if dash_version[0] <= 2:
        if (dash_version[1] < 9) or (dash_version[0] < 2):
            logging.warning("Dash version 2.9.2 or newer is required, you are running version %s. Please update.", dash.__version__)
    port = parsed_args.port

    #TODO if passed here, would need to pass properly to run_stats, which is imported by sub-tabs also
    #if parsed_args.rno_data_dir is not None:
    #    logging.warning("--rno_data_dir set to: %s.\
    #            Using this as data directory instead of environmental variable RNO_DATA_DIR", parsed_args.rno_data_dir)
    #    os.environ["RNO_DATA_DIR"] = parsed_args.rno_data_dir
    pip_output = subprocess.check_output(['python3', '-m', 'pip', 'list']).decode()
    logger.debug(f"Installed python modules:\n{pip_output}")

    if parsed_args.open_window:
        webbrowser.open_new("http://localhost:{}".format(port))

    if parsed_args.waitress:
        from waitress import serve
        serve(app.server, host='0.0.0.0', port=port, channel_timeout=300)
    else:
        app.run_server(debug=True, port=port, host='0.0.0.0')
