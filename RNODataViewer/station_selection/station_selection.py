#from NuRadioReco.eventbrowser.app import app
from RNODataViewer.base.app import app
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
from RNODataViewer.station_selection.station_list import station_entries, channel_entries

layout = html.Div([
    html.Div([
            html.Div('File Type', className='option-label'),
            html.Div([
                dcc.Dropdown(
                    id='file-type-dropdown',
                    options=[
                        {'label': 'waveforms', 'value': 'combined'},
                        {'label': 'headers', 'value': 'headers'}
                    ],
                    value='combined'
                )
            ], className='option-select')
        ], className='option-set'),
    html.Div([
        html.Div('Station ID', className='option-label'),
        html.Div([
            dcc.Dropdown(
                id='station-id-dropdown',
                options=station_entries,
                value=[11,21,22],
                multi=True
            )
        ], className='option-select')
    ], className='option-set')#,
], className='input-group')

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
                  multi=False
              )
          ], className='option-select')
          ], className='option-set', style={"flex":"1", 'display': 'inline-block', 'width':'16%'}),
      html.Div([
          html.Div('Channel IDs', className='option-label'),
          html.Div([
              dcc.Dropdown(
                  id='channel-id-dropdown',
                  options=channel_entries,
                  value=[0],
                  multi=True
              )
          ], className='option-select')
          ], className='option-set', style={'display': 'inline-block', 'width':'82%'})
      ], className='input-group', style={'flex': '1','display': 'inline-block', 'width':'100%'})
