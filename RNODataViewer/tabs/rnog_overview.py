import logging
import numpy as np
import pandas as pd
import astropy.time

import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc

from RNODataViewer.base.app import app
import RNODataViewer.base.data_provider_root
import RNODataViewer.base.data_provider_nur

import RNODataViewer.file_list.file_list
import RNODataViewer.station_selection.station_selection
import RNODataViewer.trigger_rate.trigger_rate_uproot
from file_list.run_stats import run_table

def get_slider_marks(ymin=2021, ymax=None, months = np.arange(1,13)):
    # use now if no maximum time defined
    if ymax==None:
        ymax=astropy.time.Time.now().ymdhms[0]
    slider_mark_dict = {}
    for y in range(ymin,ymax+1):
        for m in months:
            for d in range(32):
                # one mark for every day (TODO: may get impractical to use a full range slider once time range gets too large)
                try:
                    slider_mark_dict[int(astropy.time.Time("{}-{}-{}".format(str(y).zfill(4), str(m).zfill(2), str(d).zfill(2)), format="iso").mjd)] = ""
                except:
                    # skip non-existent days
                    continue
            for d in [1,15]:
                # mark with label for beginning and mid of a month
                iso_string = "{}-{}-{}".format(str(y).zfill(4), str(m).zfill(2), str(d).zfill(2))
                slider_mark_dict[int(astropy.time.Time(iso_string, format="iso").mjd)] = iso_string
    return slider_mark_dict
slider_marks = get_slider_marks()

#TODO replace this by something better
try:
    print(len(run_table))
    slider_start = min(run_table["mjd_first_event"])
except:
    slider_start = astropy.time.Time.now().mjd-365

overview_layout = html.Div([
    # selection for combined (including waveforms, only subset is transferred) or header files, station ids
    # TODO make app respond to use header-only files
    RNODataViewer.station_selection.station_selection.layout,
    # a slider to select time
    html.Div([html.Div('Time selector', style={'flex': '1'}),
                  dcc.RangeSlider(
                      id='time-selector',
                      min=slider_start,
                      max=astropy.time.Time.now().mjd+1,
                      marks = slider_marks,
                      # by default select the last day
                      value=[astropy.time.Time.now().mjd - 1,
                          astropy.time.Time.now().mjd,
                      ],
                      step=0.01,
                      included=True
                  ),
                  ],style={'marginTop':"1%", "margin":"1%"}),
    html.Div([
        html.Div(id='output-container-time-selector', style={'width': '40%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': "1%", 'marginRight': "1%"}),
        html.Div([
                RNODataViewer.file_list.file_list.layout
            ], style={'width': '55%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': "1%", 'marginRight': "1%"})]),

    html.Div([
        html.Div([
            RNODataViewer.trigger_rate.trigger_rate_uproot.layout
        ], className='flexi-element-1')
    ], className='flexi-box')
])



@app.callback(
    dash.dependencies.Output('output-container-time-selector', 'children'),
    [dash.dependencies.Input('time-selector', 'value'),
     dash.dependencies.Input('station-id-dropdown', 'value')])
def update_output(value, station_ids=[11,21,22]):
    # use start and end time from slider, slider is in units of MJD
    t_start = value[0]
    t_end = value[1]
    selected = run_table[(np.array(run_table["mjd_first_event"])>t_start) & (np.array(run_table["mjd_last_event"])<t_end)]
    logging.info("Number of selected runs: %s (out of %s)", len(selected), len(run_table))

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

    t_start_iso = astropy.time.Time(t_start, format="mjd").iso
    t_end_iso = astropy.time.Time(t_end, format="mjd").iso

    return  ["Selected time range: {} -> {}".format(t_start_iso.split(".")[0], t_end_iso.split(".")[0]),
            dash_table.DataTable(
                            id='ddoutput-container-time-selector',
                            data=return_data.to_dict("records"),
                            columns=[{'id': x, 'name': x} for x in return_data.columns]
                )]
