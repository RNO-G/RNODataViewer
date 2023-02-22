import RNODataViewer.base.data_provider_nur
import RNODataViewer.base.data_provider_root
#from NuRadioReco.eventbrowser.app import app
from RNODataViewer.base.app import app
from dash import html
from dash import dcc
import pandas as pd
from dash.dependencies import Input, Output, State
# from dash import dash_table

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
                    html.Div([html.Button('{}'.format(filename), id="btn_image", name='{}'.format(filename))])#,
                              #html.Button('headers.root', id="btn_image", name='{}'.format(filename.replace("combined.root", "headers.root"))),
                              #html.Button('daqstatus.root', id="btn_image", name='{}'.format(filename.replace("combined.root", "daqstatus.root"))),
                              #dcc.Download(id="download_file")])
            )
    #df = pd.DataFrame({"File names": filenames})
    #children.append(dash_table.DataTable(df.to_dict('records'),[{"name": i, "id": i} for i in df.columns], id='selected_run_tbl'))
    #children.append(dcc.Download(id="download_file"))
    return children


#@app.callback(
#    Output("download_file", "data"),
#    Input("btn_image", "n_clicks"),
#    State("btn_image", "name"),
#    prevent_initial_call=True,
#)
#def file_download(n_clicks, the_file):
#    return dcc.send_file(the_file, filename="_".join(the_file.split("/")[-3:]))

#@app.callback(
#    Output('download_file', 'data'),
#    Input('selected_run_tbl', 'active_cell'),
#    prevent_initial_call=True
#)
#def update_download_selection(active_cell):
#    data_provider = RNODataViewer.base.data_provider_root.RNODataProviderRoot()
#    the_file = data_provider.get_file_names()[active_cell['row']]
#    return dcc.send_file(the_file, filename="_".join(the_file.split("/")[-3:]))
