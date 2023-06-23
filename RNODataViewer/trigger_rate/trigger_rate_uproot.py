import numpy as np
import itertools
#from NuRadioReco.eventbrowser.app import app
from RNODataViewer.base.app import app
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
from dash import callback_context
import plotly.graph_objs as go
import plotly.subplots
import RNODataViewer.base.data_provider_root
import RNODataViewer.base.error_message
from NuRadioReco.utilities import units
from astropy.time import Time, TimeDelta
from NuRadioReco.framework.base_trace import BaseTrace
import pandas as pd
import os
from file_list.run_stats import run_table
import logging
import requests
logging.basicConfig()
logger = logging.getLogger("RNODataViewer")
logger.setLevel(logging.DEBUG)

RUN_TABLE = run_table.get_table() # may have to double check this doesn't break automatic updating?
trigger_names = ['all', 'rf', 'force', 'pps', 'ext', 'radiant', 'lt', 'RF0', 'RF1', 'RF-1']

layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.Div('Event rate', style={'flex': '1'}),
                html.Div([
                    html.Button('Show', id='triggeruproot-showhide')
                ],  style={'flex':'none', 'margin-right':'5px'}),
                html.Div([
                    html.Button([
                        html.Div('', className='icon-cw')
                    ], id='triggeruproot-reload-button', className='btn btn-primary')
                ], style={'flex': 'none'})
            ], className='flexi-box')
        ], className='panel panel-heading'),
        html.Div([
            dcc.Markdown('Zoom level:', style={'margin-right':'5px', 'display':'inline-block', 'margin-top':4}),
            dcc.Dropdown(
                id='trigger-rate-zoom-level',
                clearable=False,
                options=[{'label':f'{int(i)} min', 'value':i} for i in [1, 5, 10, 30, 60]],
                value=10, style={'display':'inline-flex', 'min-width':100}),
            dcc.Markdown('Triggers:', style={'margin-left':'5px', 'margin-right':'5px', 'display':'inline-block', 'margin-top':4}),
            dcc.Dropdown(
                id='trigger-rate-which-triggers',
                clearable=True, multi=True,
                options=[{'label':i, 'value':i} for i in trigger_names],
                value=['all', 'force', 'radiant', 'lt'], style={'display':'inline-flex', 'min-width':100}),
            dcc.Graph(id='triggeruproot-plot')
        ], className='panel panel-body',id='triggeruproot-plot-container', style={'display':'none'})
    ], className='panel panel-default')
])


def get_updated_trigger_table(station_id):
    """
    Download updated trigger rate table

    Loads the trigger rate table, and checks if it is up to date using the
    run table. If not, download a (hopefully) updated copy from the Desy server.

    """
    table_path = os.path.join(
        #os.path.dirname(os.path.dirname(__file__)),
        '/tmp/RNODataViewer/',
        f'data/trigger_rates/trigger_rates_s{station_id}.hdf5'
    )
    try: # first, we check if the table is available locally
        df = pd.read_hdf(table_path)
        df["time_unix"] = df.index
        time_last_event = Time(run_table.get_table().query('station==@station_id').time_end.max()).unix
        if time_last_event - np.max(df.time_unix) > 1800:
            logger.debug(
                f'Updating trigger rate table for station {station_id}:\n'
                + f'Most recent event: {Time(time_last_event, format="unix").iso}\n'
                + f'Latest event in table: {Time(np.max(df.time_unix), format="unix").iso}')
            raise FileNotFoundError(f"Trigger rate table for station {station_id} is out of date, updating...") # this is hacky!
    except FileNotFoundError: # no file found, or update required
        if not os.path.exists(os.path.dirname(table_path)):
            os.makedirs(os.path.dirname(table_path))
        table_path_https = f"https://www.zeuthen.desy.de/~shallman/trigger_rates/trigger_rates_s{station_id}.hdf5"
        try:
            df_bytes = requests.get(table_path_https)
        except requests.exceptions.ConnectionError:
            logger.warning("Failed to update trigger rate tables, using local version instead...")
            return df
        with open(table_path, 'wb') as file:
            file.write(df_bytes.content)

        df = pd.read_hdf(table_path)
        df["time_unix"] = df.index
    return df

@app.callback(
    Output('triggeruproot-plot', 'figure'),
    [Input('triggeruproot-reload-button', 'n_clicks'),
     Input('trigger-rate-zoom-level', 'value'),],
    [State('time-selector-start-date', 'date'),
     State('time-selector-start-time', 'value'),
     State('time-selector-end-date', 'date'),
     State('time-selector-end-time', 'value'),
     State('station-id-dropdown', 'value'),
     State('trigger-rate-which-triggers', 'value')],
    prevent_initial_call=True
)
def update_triggeruproot_plot(n_clicks, binwidth_min, start_date, start_time, end_date, end_time, station_ids, trigger_keys):
    t_start = (Time(start_date) + TimeDelta(start_time, format='sec')).datetime
    t_end = (Time(end_date) + TimeDelta(end_time, format='sec')).datetime
    t_start_unix = Time(t_start).unix
    t_end_unix = Time(t_end).unix

    binwidth_sec = binwidth_min * 60

    if station_ids is None:
        return RNODataViewer.base.error_message.get_error_message('No Station selected')

    plots = []

    trigger_line_styles = {
            'rf_trigger': 'dash',
            'force_trigger': 'longdash',
            'pps_trigger': 'longdash',
            'ext_trigger': 'longdashdot',
            'radiant_trigger': 'dashdot',
            'RF0_trigger': 'dashdot',
            'RF1_trigger': 'dashdot',
            'RF-1_trigger': 'dashdot',
            'lt_trigger': 'dot',
            'all': 'solid'
            }

    for station_id in station_ids:
        logger.debug(f"Getting trigger table for station {station_id}...")
        df = get_updated_trigger_table(station_id)
        df = df.query('time_unix>@t_start_unix&time_unix<@t_end_unix')
        run_table_cut = RUN_TABLE.query(
            'station==@station_id&time_end>@t_start&time_start<@t_end'
        ).sort_values(by='time_start')
        if len(run_table_cut) == 0:
            continue
        logger.debug("Making bins...")
        bins = np.arange(Time(run_table_cut.time_start.min()).unix, Time(run_table_cut.time_end.max()).unix + binwidth_sec, binwidth_sec)
        runs = np.array((len(bins)-1) * ['',], dtype=object)
        run_start_times = Time(run_table_cut.time_start).unix
        run_end_times = Time(run_table_cut.time_end).unix
        run_values = run_table_cut.run.values
        mask = (bins[None, :-1] < run_end_times[:, None]) & (bins[None, 1:] > run_start_times[:,None])
        for i in range(len(run_values)):
            runs[mask[i]] += f'{int(run_values[i])},'
        runs[np.where(runs=='')] = 'None'
        np.save(f'{station_id}_runs', runs)
        np.save(f'{station_id}_times', bins)
        # bins = []
        # runs = []
        # for i in run_table_cut.index:
        #     run, t_run_start, t_run_end = run_table_cut.loc[i, ['run', 'time_start', 'time_end']]
        #     t_run_start = Time(t_run_start).unix
        #     t_run_end = Time(t_run_end).unix
        #     t_start_i = np.max([t_run_start, t_start_unix])
        #     t_end_i = np.min([t_run_end, t_end_unix])
        #     bins_i =  np.arange(
        #         int(t_start_i) - 1, # -1 to prevent off-by-one errors due to timing precision in run table
        #         int(t_end_i) + binwidth_sec,
        #         binwidth_sec
        #     )

        #     bins_i[-1] = np.min([bins_i[-1], t_run_end + 1])
        #     # if the last bin is much smaller than the requested bin size,
        #     # we combine it with the penultimate bin:
        #     if (len(bins_i) > 2):
        #         if (t_run_end - bins_i[-2] < binwidth_sec / 3):
        #             bins_i[-2] = t_run_end + 1
        #             bins_i = bins_i[:-1]
        #     if bins: # this makes sure the bins of the previous run don't overlap
        #         bins[-1][-1] = np.min([bins[-1][-1], bins_i[0]-1])
        #     bins.append(bins_i)
        #     runs.append(run * np.ones_like(bins_i, dtype=int))
        # if not bins: # no runs available for this station - skip
        #     continue
        # bins = np.concatenate(bins)
        # runs = np.concatenate(runs)
        bin_widths = bins[1:] - bins[:-1]

        logger.debug("Binning trigger rates...")
        for key in trigger_keys:
            if key=="all":
                visible = True
                line_dict = dict(width=2)
                mode = 'lines+markers'
            else:
                visible= True #'legendonly'
                line_dict = dict(dash=trigger_line_styles[f'{key}_trigger'])
                mode = 'lines'
            counts, _ = np.histogram(df.index.values, bins=bins, weights=df.loc[:,key])
            y = counts / bin_widths
            assert len(runs) == len(y)
            # mask = np.ones_like(y).astype(bool)
            # y[bin_widths > 1.5 * binwidth_sec] = np.nan # don't connect runs with large time gaps
            # mask = np.where(~(
            #     ((bin_widths < binwidth_sec - 1e-4)
            #     | (bin_widths > 1.4 * binwidth_sec))
            #     & (y < 1e-6)
            # )) # exclude empty bins between runs
            plots.append(go.Scattergl(
                x = Time((bins[:-1]+bin_widths/2), format='unix').fits, #Time(df.time_unix, format='unix').fits,
                y = y, #df.loc[:, key] / 60,
                mode=mode,
                name='Station: {}, Trigger: {}'.format(station_id, key),
                customdata=runs,
                visible=visible,
                line=line_dict,
                hovertemplate=f"Station {station_id}, run %{{customdata}} trigger: {key}<br>%{{y}}<br>%{{x}}"
            ))
    logger.debug("Making plot...")
    fig = go.Figure(plots)
    ### add a button to switch between linear / log plot:
    updatemenus = [
        dict(
            type="buttons",
            direction="left",
            buttons=list([
                dict(
                    args=[{'yaxis.type': 'linear'}],
                    label="Linear",
                    method="relayout"
                ),
                dict(
                    args=[{'yaxis.type': 'log'}],
                    label="Log",
                    method="relayout"
                )
            ])
        ),
    ]
    fig.update_layout(
          xaxis={'title': 'date'},
          yaxis={'title': 'Rate [Hz]'},
          updatemenus=updatemenus,
          uirevision=True
      )
    fig.update_yaxes(rangemode='tozero')
    return fig

@app.callback(
    [Output('triggeruproot-plot-container', 'style'),
     Output('triggeruproot-showhide','children')],
    [Input('triggeruproot-reload-button', 'n_clicks'),
     Input('triggeruproot-showhide', 'n_clicks')],
    [State('triggeruproot-showhide', 'children'),
     State('triggeruproot-plot-container', 'style')],
     prevent_initial_call=True
)
def show_hide_plot(n_clicks1, n_clicks2, show_or_hide, style):
    trigger = callback_context.triggered[0]['prop_id'].split('.')[0]
    if trigger == 'triggeruproot-reload-button':
        style['display'] = 'inherit'
        return style, 'Hide'
    elif trigger == 'triggeruproot-showhide':
        if show_or_hide == 'Hide':
            style['display'] = 'none'
            return style, 'Show'
        else:
            style['display'] = 'inherit'
            return style, 'Hide'
    else:
        return style, 'Hide'
