import logging
logging.basicConfig()
logger = logging.getLogger("RNODataViewer")
# logger.setLevel(logging.DEBUG)
from dash.dependencies import Input
import numpy as np
import pandas as pd
import astropy.time
import datetime

import dash
from dash import html
from dash import dcc
from dash import callback_context
from dash.exceptions import PreventUpdate

from RNODataViewer.base.app import app
import RNODataViewer.base.data_provider_root
import RNODataViewer.base.data_provider_nur

import RNODataViewer.file_list.file_list
import RNODataViewer.station_selection.station_selection
import RNODataViewer.trigger_rate.trigger_rate_uproot
import RNODataViewer.trigger_rate.trigger_active_plot
import RNODataViewer.trigger_rate.run_data_plot
from file_list.run_stats import run_table

time_options = [
    {
        'label':astropy.time.Time(j, format='mjd').iso.split(' ')[-1][:-4],
        'value':j
    } for j in np.arange(0,1,1./48)
]

#TODO replace this by something better
try:
    print(len(run_table.get_table()))
    slider_start = min(run_table.get_table()["mjd_first_event"])
except:
    slider_start = astropy.time.Time.now().mjd-365

overview_layout = html.Div([
    # selection for combined (including waveforms, only subset is transferred) or header files, station ids
    # TODO make app respond to use header-only files
    html.Div([
        dcc.Interval(id='update-dates', interval=18e5), # this doesn't actually matter, but we need an input to trigger the date updater on page load
        html.Div([
            html.Div([
                html.Div(['Selected time range:'], className='option-label'),#style={'margin-top':8, 'margin-right':5}),
                dcc.DatePickerSingle(
                    id='time-selector-start-date',
                    min_date_allowed=astropy.time.Time(slider_start, format='mjd').datetime,
                    max_date_allowed=datetime.datetime.utcnow(),
                    date=datetime.datetime.utcnow()-datetime.timedelta(days=7),
                    display_format="YYYY-MM-DD",
                    persistence=True,
                    persistence_type='memory',
                    style={'display':'inline-flex', 'font-size':14,'margin-top':4, 'margin-left':4}
                ),
                dcc.Dropdown(
                    id='time-selector-start-time',
                    options=time_options,
                    value=0,clearable=False,
                    persistence=True,
                    persistence_type='memory',
                    style={'min-width':85, 'margin-top':2}
                ),
                dcc.Markdown('''-''', style={'margin-top':12, 'margin-right':5, 'margin-left':5}),
                dcc.DatePickerSingle(
                    id='time-selector-end-date',
                    min_date_allowed=astropy.time.Time(slider_start, format='mjd').datetime,
                    max_date_allowed=datetime.datetime.utcnow(),
                    date=datetime.datetime.utcnow(),
                    display_format="YYYY-MM-DD",
                    persistence=True,
                    persistence_type='memory',
                    style={'display':'inline-flex', 'fontSize':14, 'margin-top':4}
                ),
                dcc.Dropdown(
                    id='time-selector-end-time',
                    options=time_options,
                    value=0, clearable=False,
                    persistence=True,
                    persistence_type='memory',
                    style={'min-width':85, 'margin-top':2}
                ),
            ], className='option-set', style={'display':'flex', 'max-width':'42%','min-width':550}),
            RNODataViewer.station_selection.station_selection.layout,
            ], className='input-group',
        ),
        html.Div(id='output-container-time-selector', style={'width': '40%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': "1%", 'marginRight': "1%"}),
        html.Div([
                RNODataViewer.file_list.file_list.layout
            ], style={'width': '55%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': "1%", 'marginRight': "1%"})]),

    html.Div([
        html.Div([
            RNODataViewer.trigger_rate.trigger_rate_uproot.layout
        ], className='flexi-element-1')
    ], className='flexi-box'),
    html.Div([
        html.Div([
            RNODataViewer.trigger_rate.run_data_plot.layout
        ], className='flexi-element-1')
    ], className='flexi-box'),
    html.Div([
        html.Div([
            RNODataViewer.trigger_rate.trigger_active_plot.layout
        ], className='flexi-element-1')
    ], className='flexi-box')
])

# callback to update the current / maximum allowed date
@app.callback(
    [dash.dependencies.Output('time-selector-start-date', 'date'),
     dash.dependencies.Output('time-selector-start-date', 'max_date_allowed'),
     dash.dependencies.Output('time-selector-end-date', 'date'),
     dash.dependencies.Output('time-selector-end-date', 'max_date_allowed')],
    dash.dependencies.Input('update-dates', 'n_intervals'),
    dash.dependencies.State('time-selector-end-date', 'max_date_allowed')
)
def update_current_date(n_intervals, max_date):
    current_time = astropy.time.Time.now().mjd
    max_date_allowed = astropy.time.Time(max_date).mjd // 1
    if current_time - max_date_allowed < 23/24: # we only force an update past 11 pm
        raise PreventUpdate
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=2) # add one more day past 11 pm for convenience
    start_date = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    return [start_date, now, now, now]

@app.callback(
    [dash.dependencies.Output('output-container-time-selector', 'children'),
     dash.dependencies.Output('time-selector-start-time', 'options'),
     dash.dependencies.Output('time-selector-end-time', 'options'),
    ],
    [dash.dependencies.Input('time-selector-start-date', 'date'),
     dash.dependencies.Input('time-selector-start-time', 'value'),
     dash.dependencies.Input('time-selector-end-date', 'date'),
     dash.dependencies.Input('time-selector-end-time', 'value'),
     dash.dependencies.Input('station-id-dropdown', 'value')])
def update_output(start_date, start_time, end_date, end_time, station_ids=[11,21,22]):
    t_start = astropy.time.Time(start_date).mjd // 1 + start_time
    t_end = astropy.time.Time(end_date).mjd // 1 + end_time
    if t_start > t_end:
        raise PreventUpdate
    tab = run_table.get_table()
    selected = tab[(np.array(tab["mjd_first_event"])>t_start) & (np.array(tab["mjd_last_event"])<t_end)]
    logger.info("Number of selected runs: %s (out of %s)", len(selected), len(tab))
    logger.debug(f"Current utc time: {str(end_date)}")
    RNODataViewer.base.data_provider_root.RNODataProviderRoot().set_filenames(selected.filenames_root)

    return_strings = []
    for station in station_ids:
        runs_for_station = selected[selected.station==station].run
        if len(runs_for_station) == 0:
            runrange = [np.nan, np.nan]
        else:
            runrange = [min(runs_for_station), max(runs_for_station)]
        return_strings.append('{} - {}'.format(str(runrange[0]).rjust(6),str(runrange[1]).rjust(6)))
    return_data = pd.DataFrame({"Station": station_ids, "Selected Runs": return_strings})

    # the selected time(s) need to be in the dropdown options in order to display correctly
    if t_start % 1 not in [k['value'] for k in time_options]:
        t_start_label = astropy.time.Time(t_start % 1, format='mjd').iso.split(' ')[-1][:-4]
        t_start_options = [{'label':t_start_label, 'value':t_start % 1}] + time_options
    else: # this is probably never the case due to fp precision
        t_start_options = time_options
    if t_end % 1 not in [k['value'] for k in time_options]:
        t_end_label = astropy.time.Time(t_end % 1, format='mjd').iso.split(' ')[-1][:-4]
        t_end_options = [{'label':t_end_label, 'value':t_end % 1}] + time_options
    else:
        t_end_options = time_options
    output = [
        dash.dash_table.DataTable(
            id='ddoutput-container-time-selector',
            data=return_data.to_dict("records"),
            columns=[{'id': x, 'name': x} for x in return_data.columns]
        ),
        t_start_options,
        t_end_options,
    ]

    return output
