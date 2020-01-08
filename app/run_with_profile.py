#!flask/bin/python
import os
import sys
from werkzeug.middleware.profiler import ProfilerMiddleware

parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)
sys.path.append(os.getcwd())

os.environ["LOCATION"] = "LOCAL"

from server import create_app

app = create_app()
app.config['PROFILE'] = True
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
app.run(debug=True, threaded=True, host='0.0.0.0', port=9000)
