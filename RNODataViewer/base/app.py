import dash
from flask import Flask
import os
import diskcache

cache = diskcache.Cache("/tmp/RNODataViewer/cache")
background_callback_manager = dash.DiskcacheManager(cache=cache)

os.environ["FLASK_APP_DIR"] = "RNODataViewer.base.app"
server = Flask(os.getenv("FLASK_APP_DIR") or __name__, static_folder='static')
#print(server)
# from NuRadioReco.eventbrowser.app import *

#app._favicon = ("./favicon.ico")
#app = NuRadioReco.eventbrowser.app
app = dash.Dash(
    server=server, use_pages=True,
    pages_folder='../', suppress_callback_exceptions=True,
    background_callback_manager=background_callback_manager
)
#app.config.suppress_callback_exceptions = True
