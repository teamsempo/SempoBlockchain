#!flask/bin/python
import os

os.environ["LOCATION"] = "LOCAL"

from server import create_app

app = create_app()
app.run(debug=True, threaded=True, host='0.0.0.0', port=9000)