#!flask/bin/python
import os
import sys

parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)
sys.path.append(os.getcwd())

os.environ["LOCATION"] = "LOCAL"

from server import create_app

app = create_app()

app.run(host='0.0.0.0', port=9000)
