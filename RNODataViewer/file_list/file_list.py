import RNODataViewer.base.data_provider_nur
import RNODataViewer.base.data_provider_root
#from NuRadioReco.eventbrowser.app import app
from RNODataViewer.base.app import app
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State

layout = html.Div([
    html.Div([
        html.Div([
            html.Div('File Names', style={'flex': '1'}),
            html.Div([
                html.Button([
                    html.Div('', className='icon-cw')
                ], id='file-list-reload-button', className='btn btn-primary')
            ], style={'flex': 'none'})
        ], className='flexi-box')
    ], className='panel panel-heading'),
    html.Div([
        html.Div('', id='file-list-display')
    ], className='panel panel-body', style={'max-height': '100px', 'overflow': 'scroll'})
], className='panel panel-default')


@app.callback(
    Output('file-list-display', 'children'),
    [Input('file-list-reload-button', 'n_clicks')],
    [State('station-id-dropdown', 'value')]
)
def update_file_list(n_clicks, station_ids):
    data_provider = RNODataViewer.base.data_provider_root.RNODataProviderRoot()
    filenames = data_provider.get_file_names()
    if filenames is None:
        return ''
    children = []
    for filename in filenames:
        stn = int(filename.split("/")[-3].replace("station",""))
        run = int(filename.split("/")[-2].replace("run", ""))
        if type(station_ids) == int:
            station_ids = [station_ids]
        if stn in station_ids:
            children.append(
                    html.Div([html.Button('{}'.format(filename), id="btn_image", name='{}'.format(filename)), dcc.Download(id="download_file")])
            )
    return children


@app.callback(
    Output("download_file", "data"),
    Input("btn_image", "n_clicks"),
    Input("btn_image", "name"),
    prevent_initial_call=True,
)
def file_download(n_clicks, the_file):
    return dcc.send_file(the_file, filename=the_file.split("/")[-1])
