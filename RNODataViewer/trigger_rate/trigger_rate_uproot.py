import numpy as np
import itertools
#from NuRadioReco.eventbrowser.app import app

from dash import html, dcc, callback
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

trigger_names = ['ALL', 'RADIANT0','RADIANT1', 'RADIANTX', 'LT', 'FORCE', 'PPS']

# line styles for plot
trigger_line_styles = ['solid'] + 4 * ['dash', 'dot', 'dashdot', 'longdash', 'longdashdot']
trigger_line_styles = {i:j for i,j in zip(trigger_names, trigger_line_styles)}

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
                value=['ALL',], style={'display':'inline-flex', 'min-width':100}),
            dcc.Graph(id='triggeruproot-plot')
        ], className='panel panel-body',id='triggeruproot-plot-container', style={'display':'none'})
    ], className='panel panel-default')
])

class trigger_rates:

    def __init__(self, table_path='/tmp/RNODataViewer/data/trigger_rates'):
        self.table_dir_local = table_path
        if not os.path.exists(table_path):
            os.makedirs(table_path)
        self.hash_table_path_local = os.path.join(table_path, 'trigger_rate_hash_table.hdf5')
        self.hash_table_path_url = 'https://www.zeuthen.desy.de/~shallman/trigger_rates/trigger_rate_hash_table.hdf5'
        self.last_update = Time('1970-01-01')
        if os.path.exists(self.hash_table_path_local):
            self.hash_table = pd.read_hdf(self.hash_table_path_local)
        else:
            self.hash_table = None

    def get_updated_trigger_table(self, start_time, end_time):
        """
        Returns a DataFrame with the trigger rates
        """
        now = Time.now()
        if (now - self.last_update).sec > 300: # update trigger rate tables
            logger.warning("Updating trigger rate tables...")
            try:
                df_bytes = requests.get(self.hash_table_path_url)
                df_bytes.raise_for_status()
                with open(self.hash_table_path_local+'.upd', 'wb') as f:
                    f.write(df_bytes.content)
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                logger.error(msg="Failed to update trigger rate tables, will try to use local versions instead...", exc_info=e)
            
            hash_table = pd.read_hdf(self.hash_table_path_local+'.upd')
            if self.hash_table is None:
                update_tables = hash_table.index.levels[0] # update all tables
                logger.info(f'No previous hash found, updating all {len(update_tables)} trigger tables')
            else:
                update_tables = []
                for i in hash_table.index.levels[0]:
                    if i in self.hash_table.index.levels[0]:
                        n_events_new = hash_table.loc[i, 'n_events']
                        n_events_old = self.hash_table.loc[i, 'n_events']
                        if len(n_events_new) == len(n_events_old):
                            if np.all(n_events_new == n_events_old):
                                continue # table is up to date
                    update_tables.append(i)
            
            if len(update_tables):
                # times = Time([f'{month}-01' for month in update_tables])
                # mask = (times >= start_time) & (times <= end_time)
                # update_tables = np.array(update_tables)[mask]

                for table in update_tables:
                    logger.warning(f"Downloading updated trigger rate table {table}")
                    try:
                        df_bytes = requests.get(f"https://www.zeuthen.desy.de/~shallman/trigger_rates/trigger_rates_{table}.hdf5")
                        df_bytes.raise_for_status()
                        with open(os.path.join(self.table_dir_local, f"trigger_rates_{table}.hdf5"), 'wb') as f:
                            f.write(df_bytes.content)
                        # we update the hash table only AFTER the new table has been downloaded
                        # this prevents issues if the update is interrupted by the user
                        if self.hash_table is not None:
                            if table in self.hash_table.index:
                                self.hash_table.drop(table, inplace=True)
                        self.hash_table = pd.concat([self.hash_table, hash_table.loc[[table]]]).sort_index()
                        self.hash_table.to_hdf(self.hash_table_path_local, 'df', 'w')
                    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                        logger.error(msg=f"Unable to update trigger table {table}", exc_info=e)
            
            self.last_update = now
        tables = self.hash_table.index.levels[0]
        times = Time([f'{month}-01' for month in tables])
        start_month = Time(f'{Time(start_time).iso[:7]}-01') # stupid way of converting to 1st day of month
        mask = (times >= start_month) & (times <= end_time)
        tables = tables[mask]
        trigger_rate_tables = [
            pd.read_hdf(os.path.join(self.table_dir_local, f"trigger_rates_{table}.hdf5"))
            for table in tables]
        if not len(trigger_rate_tables):
            logger.warning('No trigger rate tables for selected period!')
            return None
        
        trigger_table = pd.concat(trigger_rate_tables)
        
        return trigger_table
      
TriggerRateTable = trigger_rates()


@callback(
    Output('triggeruproot-plot', 'figure'),
    [Input('triggeruproot-reload-button', 'n_clicks'),
     Input('trigger-rate-zoom-level', 'value'),],
    [State('time-selector-start-date', 'date'),
     State('time-selector-start-time', 'value'),
     State('time-selector-end-date', 'date'),
     State('time-selector-end-time', 'value'),
     State('overview-station-id-dropdown', 'value'),
     State('trigger-rate-which-triggers', 'value')],
    prevent_initial_call=True
)
def update_triggeruproot_plot(n_clicks, binwidth_min, start_date, start_time, end_date, end_time, station_ids, trigger_keys):
    t_start = (Time(start_date) + TimeDelta(start_time, format='sec')).datetime
    t_end = (Time(end_date) + TimeDelta(end_time, format='sec')).datetime
    t_start_unix = Time(t_start).unix // 60 * 60
    t_end_unix = (Time(t_end).unix // 60 + 1) * 60

    binwidth_sec = binwidth_min * 60

    if station_ids is None:
        return RNODataViewer.base.error_message.get_error_message('No Station selected')

    plots = []

    # trigger_line_styles = {
    #         'rf_trigger': 'dash',
    #         'force_trigger': 'longdash',
    #         'pps_trigger': 'longdash',
    #         'ext_trigger': 'longdashdot',
    #         'radiant_trigger': 'dashdot',
    #         'RF0_trigger': 'dashdot',
    #         'RF1_trigger': 'dashdot',
    #         'RF-1_trigger': 'dashdot',
    #         'lt_trigger': 'dot',
    #         'all': 'solid'
    #         }

    df = TriggerRateTable.get_updated_trigger_table(t_start, t_end)
    if df is None: # no trigger rate tables found
        return RNODataViewer.base.error_message.get_error_message("No trigger rate tables found")
    df = df.query('time_unix>@t_start_unix&time_unix<@t_end_unix')
    bins = np.arange(t_start_unix, t_end_unix + binwidth_sec + 1, binwidth_sec)
    runtable = run_table.get_table().query("time_end>@t_start&time_start<@t_end")
    for station_id in station_ids:
        if station_id not in df.index.get_level_values(0).unique(): # index.levels doesn't update after the .query above
            logger.info(f"No trigger rates for station {station_id} in current time selection, skipping...")
            continue
        logger.debug(f"Getting trigger table for station {station_id}...")
        run_table_cut = runtable.query('station==@station_id')
        runs = np.array((len(bins)-1) * ['',], dtype=object)
        run_start_times = Time(run_table_cut.time_start).unix
        run_end_times = Time(run_table_cut.time_end).unix
        run_values = run_table_cut.run.values
        mask = (bins[None, :-1] < run_end_times[:, None]) & (bins[None, 1:] > run_start_times[:,None])
        for i in range(len(run_values)):
            runs[mask[i]] += f'{int(run_values[i])},'
        runs[np.where(runs=='')] = 'None'
        # np.save(f'{station_id}_runs', runs) # debugging
        # np.save(f'{station_id}_times', bins)
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
        trigger_df = df.loc[station_id]
        for key in trigger_keys:
            if key=="ALL":
                visible = True
                line_dict = dict(width=2)
                mode = 'lines+markers'
            else:
                visible= True #'legendonly'
                line_dict = dict(dash=trigger_line_styles[key])
                mode = 'lines'
            counts, _ = np.histogram(trigger_df.index.get_level_values(1), bins=bins, weights=trigger_df.loc[:,key])
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
                    args=[{'yaxis.type': 'log'}],
                    label="Log",
                    method="relayout"
                ),
                dict(
                    args=[{'yaxis.type': 'linear'}],
                    label="Linear",
                    method="relayout"
                ),
            ])
        ),
    ]
    fig.update_layout(
          xaxis={'title': 'date'},
          yaxis={'title': 'Rate [Hz]','type':'log'},
          updatemenus=updatemenus,
          uirevision=True
      )
    fig.update_yaxes(rangemode='tozero')
    return fig

@callback(
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
