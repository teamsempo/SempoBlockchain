from server import create_app
from werkzeug.contrib.fixers import ProxyFix

app = ProxyFix(create_app(), num_proxies=1)
