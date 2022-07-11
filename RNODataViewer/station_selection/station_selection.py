#from NuRadioReco.eventbrowser.app import app
from RNODataViewer.base.app import app
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
from dash import callback_context
from RNODataViewer.station_selection.station_list import station_entries, channel_entries

layout = html.Div([
    # html.Div([
    #         html.Div('File Type', className='option-label'),
    #         html.Div([
    #             dcc.Dropdown(
    #                 id='file-type-dropdown',
    #                 options=[
    #                     {'label': 'waveforms', 'value': 'combined'},
    #                     {'label': 'headers', 'value': 'headers'}
    #                 ],
    #                 value='combined'
    #             )
    #         ], className='option-select')
    #     ], className='option-set'),
    # html.Div([
        html.Div('Station ID', className='option-label'),
        html.Div([
            dcc.Dropdown(
                id='station-id-dropdown',
                options=station_entries,
                value=[11,21,22],
                persistence=True,
                persistence_type='memory',
                multi=True
            )
        ], className='option-select')
    ], className='option-set')#,
# ], className='input-group')

layout_run_browser = html.Div([
      #html.Div([
              #html.Div('File Type', className='option-label'),
              #html.Div([
              #    dcc.Dropdown(
              #        id='file-type-dropdown',
              #        options=[
              #            {'label': 'ROOT', 'value': 'combined'},
              #            {'label': 'headers', 'value': 'headers'}
              #        #    {'label': '.nur', 'value': 'nur'}
              #        ],
              #        value='combined'
              #    )
              #], className='option-select')
      #    ], className='option-set', style={'width': '20%', 'display': 'inline-block'}),
      html.Div([
          html.Div('Station ID', className='option-label'),
          html.Div([
              dcc.Dropdown(
                  id='station-id-dropdown-single',
                  options=station_entries,
                  multi=False,
                  persistence=True,
                  persistence_type='memory',
                  style={'display':'inline-block','width':'100%'}
              )
          ], className='option-select')
          ], className='option-set', style={"flex":"1", 'display': 'inline-block', 'width':'16%'}),
      html.Div([
          html.Div('Channel IDs', className='option-label'),
          html.Div([
              html.Div([
              dcc.Dropdown(
                  id='channel-id-dropdown',
                  options=channel_entries,
                  value=[0],
                  multi=True,
                  persistence=True, #TODO - this doesn't work because of the circular callback with 'select-all'
                  persistence_type='memory',
                  style={'width':'100%'}
              ),],style={'display':'inline-block', 'width':'95%'}),
            #   html.Div([
              dcc.Checklist(
                  id='channel-id-select-all', options=[{'label':'All', 'value':'select_all'}],
                  style={'display':'inline-block', 'margin-bottom':0, 'width':'4%','margin-left':'5px'}
                  )
            #   ], style={'display':'inline-block', 'width':'5%'})
          ], className='option-select')
          ], className='option-set', style={'display': 'inline-block', 'width':'82%'})
      ], className='input-group', style={'flex': '1','display': 'inline-block', 'width':'100%'})

@app.callback(
    [Output('channel-id-dropdown', 'value'),
     Output('channel-id-select-all', 'value')],
    [Input('channel-id-dropdown', 'value'),
     Input('channel-id-select-all', 'value')],
    [State('channel-id-dropdown', 'options')],
    prevent_initial_call=True
)
def select_all_channels(channel_ids, select_all, channel_options):
    trigger = callback_context.triggered[0]['prop_id'].split('.')[0]
    all_channels = sorted([k['value'] for k in channel_options])
    if trigger == 'channel-id-dropdown':
        if sorted(channel_ids) == all_channels:
            return channel_ids, ['select_all']
        else:
            return channel_ids, []
    elif trigger == 'channel-id-select-all':
        if 'select_all' in select_all:
            return all_channels, ['select_all']
        else:
            return [], []
