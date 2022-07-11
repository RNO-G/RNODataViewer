import dash
from flask import Flask
import os


os.environ["FLASK_APP_DIR"] = "RNODataViewer.base.app"
server = Flask(os.getenv("FLASK_APP_DIR") or __name__, static_folder='static')
#print(server)
from NuRadioReco.eventbrowser.app import *

#app._favicon = ("./favicon.ico")
#app = NuRadioReco.eventbrowser.app
#app = dash.Dash(server=server)
#app.config.suppress_callback_exceptions = True
