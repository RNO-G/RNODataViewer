#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse

import dash
from dash.dependencies import Input, Output
from dash import html
from dash import dcc
import webbrowser
from RNODataViewer.base.app import app
app.config.suppress_callback_exceptions = True

import RNODataViewer.base.data_provider_root
import RNODataViewer.base.data_provider_nur

from tabs import rnog_overview
from tabs import run_viewer
from tabs import event_viewer

import logging
#TODO: need for updating run_table with hidden div? eg. dcc.Interval or other solution?
from file_list.run_stats import run_table
import astropy.time
import pandas as pd
import sys, os
argparser = argparse.ArgumentParser(description="View RNO Data Set")
argparser.add_argument('--open-window', const=True, default=False, action='store_const',
                         help="Open the event display in a new browser tab on startup")
argparser.add_argument('--port', default=8080, help="Specify the port the event display will run on")
argparser.add_argument('--reverse-proxy-path', default=None, help="If running behind a reverse proxy (e.g. https://example.org/monitoring is proxied to 127.0.0.1:$PORT from $REAL_HTTP_SERVER, you need to specify the path here so that the internal links work. In this case you would use /monitoring (don't include trailing /) ")
argparser.add_argument('--waitress', const=True,  default=False, action='store_const', help="Use waitress instead of development server")
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


logging.info("Starting the monitoring application")

# import the run table (which is a pandas table holding available runs / paths / start/stop times etc)
filenames_root = run_table.filenames_root
filenames_nur = []

RNODataViewer.base.data_provider_root.RNODataProviderRoot().set_filenames(filenames_root)
RNODataViewer.base.data_provider_nur.RNODataProvider().set_filenames(filenames_nur)


app.layout = html.Div([
    # header line with logo and title
    html.Div([
        html.Img(src=file_prefix+'/assets/rnog_logo_monogram_BlackTransparant.png', style={"float": "left", "width": "100px"}),
        html.H1('RNO-G Data Monitor')]),
    # three tabs, using this method, fresh pages get loaded after switching tabs
    dcc.Tabs(
            [
                dcc.Tab(label= 'Overview', value= 'overview_tab'),
                dcc.Tab(label= 'Run Browser', value= 'runbrowser_tab'),
                dcc.Tab(label= 'Event Browser', value= 'eventbrowser_tab')
            ],
            value='overview_tab', # start at general overview page by default
            id='tab-selection'
        ),
    html.Div(id='active-monitoring-tab')

    # TODO three tabs, the method below should avoid reloading tabs when switching, but callback ids need to be unique across all tabs
    #dcc.Tabs([
    #    dcc.Tab(label= 'Overview', children=index_app_layout),
    #    dcc.Tab(label= 'Run Browser', children=run_viewer.run_viewer_layout),
    #    dcc.Tab(label= 'Event Browser', children=event_viewer.event_viewer_layout)
    #])
])

@app.callback(Output('active-monitoring-tab', 'children'),
              [Input('tab-selection', 'value')])
def render_content(tab):
    if tab == 'overview_tab':
        return rnog_overview.overview_layout
    elif tab == 'runbrowser_tab':
        return run_viewer.run_viewer_layout
    elif tab == 'eventbrowser_tab':
        return event_viewer.event_viewer_layout


if __name__ == '__main__':
    if int(dash.__version__.split('.')[0]) <= 1:
        if int(dash.__version__.split('.')[1]) < 0:
            logging.warning("Dash version 0.39.0 or newer is required, you are running version %s. Please update.", dash.__version__)
    port = parsed_args.port

    #TODO if passed here, would need to pass properly to run_stats, which is imported by sub-tabs also
    #if parsed_args.rno_data_dir is not None:
    #    logging.warning("--rno_data_dir set to: %s.\
    #            Using this as data directory instead of environmental variable RNO_DATA_DIR", parsed_args.rno_data_dir)
    #    os.environ["RNO_DATA_DIR"] = parsed_args.rno_data_dir

    if parsed_args.open_window:
        webbrowser.open_new("http://localhost:{}".format(port))

    if parsed_args.waitress:
        from waitress import serve
        serve(app.server, host='0.0.0.0', port=port, channel_timeout=300)
    else:
        app.run_server(debug=True, port=port, host='0.0.0.0')
